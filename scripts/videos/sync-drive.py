#!/usr/bin/env python3
"""Sync the video catalog (docs/tutorials/videos.yml) with the Google Drive folder.

The Drive folder named in the catalog (`drive.folder`) holds one subfolder per
category (`categories[].drive_folder`). Every video file in a subfolder becomes
one catalog entry. The folder only has to be shared "anyone with the link";
no Google credentials are needed, the public folder view is read.

File names follow "<Category> <NN> - <Title>.mp4", for example
"Core 04 - Ultra-fast copy-on-write.mp4". The number makes the stable id
(<category>-<NN>, used in deep links), so a re-uploaded video keeps its tile.
When several files carry the same number, the most recently modified one wins.

What the sync changes:
  * new numbers         -> new entry, title taken from the file name
  * known numbers       -> drive_id updated; title, teaser, description kept
  * gone from the Drive -> entry removed (only entries with a drive_id;
                           YouTube and local entries are never touched)

Usage:
  python3 scripts/videos/sync-drive.py            # rewrite the catalog
  python3 scripts/videos/sync-drive.py --check    # exit 1 if out of sync
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "docs" / "tutorials" / "videos.yml"
FOLDER_VIEW = "https://drive.google.com/embeddedfolderview?id={}"
VIDEO_EXT = (".mp4", ".mov", ".m4v", ".webm")

ENTRY_RE = re.compile(
    r'<div class="flip-entry" id="entry-(?P<id>[\w-]+)".*?'
    r'<a href="(?P<href>[^"]+)".*?'
    r'<div class="flip-entry-title">(?P<title>.*?)</div>.*?'
    r'<div class="flip-entry-last-modified"><div>(?P<modified>.*?)</div>',
    re.S,
)
# "DR 01 - Policy-based backup.mp4", "dr-01-policy-based-backup (2).mp4"
NAME_RE = re.compile(
    r"^(?P<prefix>.*?)[\s_-]*(?P<num>\d{1,3})\s*[-_.:\u2013\u2014 ]\s*(?P<title>.+?)"
    r"(?:\s*\(\d+\))?\.[A-Za-z0-9]+$"
)


def fetch(folder_id: str) -> list[dict]:
    req = urllib.request.Request(FOLDER_VIEW.format(folder_id), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        page = resp.read().decode("utf-8")
    entries = []
    for m in ENTRY_RE.finditer(page):
        entries.append(
            {
                "id": m["id"],
                "name": html.unescape(m["title"]).strip(),
                "folder": "/folders/" in m["href"],
                "modified": parse_modified(html.unescape(m["modified"]).strip()),
            }
        )
    return entries


def parse_modified(text: str) -> dt.date:
    """The folder view shows a time for today, "Oct 31" for this year, else a date."""
    today = dt.date.today()
    if re.search(r"\d:\d\d", text):
        return today
    for fmt in ("%b %d", "%d %b"):
        try:
            d = dt.datetime.strptime(f"{text} {today.year}", fmt + " %Y").date()
            return d if d <= today else d.replace(year=today.year - 1)
        except ValueError:
            pass
    for fmt in ("%m/%d/%y", "%m/%d/%Y", "%d/%m/%y", "%d.%m.%y", "%b %d, %Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return dt.date.min


def title_from(raw: str) -> str:
    if " " not in raw.strip():
        raw = raw.replace("-", " ").replace("_", " ")
    raw = raw.strip()
    return raw[:1].upper() + raw[1:]


def scalar(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value)
    if re.fullmatch(r"[A-Za-z0-9_][\w./-]*", text) and text.lower() not in ("true", "false", "null", "yes", "no", "on", "off"):
        return text
    return json.dumps(text, ensure_ascii=False)


FIELD_ORDER = ("id", "category", "title", "teaser", "description", "drive_id", "youtube", "src", "poster", "page", "pick")


def dump_videos(videos: list[dict]) -> str:
    out = ["videos:"]
    for v in videos:
        keys = [k for k in FIELD_ORDER if k in v] + sorted(k for k in v if k not in FIELD_ORDER)
        for i, k in enumerate(keys):
            value = v[k]
            if k == "title" and not isinstance(value, bool):
                value = json.dumps(str(value), ensure_ascii=False)
            else:
                value = scalar(value)
            out.append(f"  {'- ' if i == 0 else '  '}{k}: {value}")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="report only, exit 1 if the catalog is out of sync")
    args = ap.parse_args()

    text = CATALOG.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    head = text[: text.index("\nvideos:") + 1]
    categories = data["categories"]
    by_folder = {c["drive_folder"]: c["id"] for c in categories if c.get("drive_folder")}
    order = {c["id"]: i for i, c in enumerate(categories)}

    found: dict[str, dict] = {}
    root = fetch(data["drive"]["folder"])
    for sub in (e for e in root if e["folder"]):
        category = by_folder.get(sub["name"])
        if not category:
            print(f"note: Drive folder {sub['name']!r} is not mapped to a category, skipped")
            continue
        for f in fetch(sub["id"]):
            if f["folder"] or not f["name"].lower().endswith(VIDEO_EXT):
                continue
            m = NAME_RE.match(f["name"])
            if not m:
                print(f"note: {sub['name']}/{f['name']}: no '<NN> - <Title>' in the name, skipped")
                continue
            vid = f"{category}-{int(m['num']):02d}"
            cand = {"drive_id": f["id"], "name": f["name"], "modified": f["modified"],
                    "category": category, "title": title_from(m["title"])}
            prev = found.get(vid)
            if prev:
                newer = cand if cand["modified"] > prev["modified"] else prev
                print(f"note: {vid}: several files ({prev['name']!r}, {cand['name']!r}), using {newer['name']!r}")
                cand = newer
            found[vid] = cand

    videos = data.get("videos") or []
    changes = []
    result = []
    for v in videos:
        if "drive_id" not in v:
            result.append(v)
            continue
        f = found.pop(v["id"], None)
        if f is None:
            changes.append(f"removed {v['id']} ({v.get('title')})")
            continue
        if f["drive_id"] != v["drive_id"]:
            changes.append(f"updated {v['id']}: {f['name']}")
            v = {**v, "drive_id": f["drive_id"]}
        result.append(v)
    for vid, f in found.items():
        changes.append(f"added {vid}: {f['name']}")
        result.append({"id": vid, "category": f["category"], "title": f["title"], "drive_id": f["drive_id"]})

    def sort_key(v):
        m = re.search(r"(\d+)$", v["id"])
        return (order.get(v.get("category"), 99), int(m.group(1)) if m else 999, v["id"])

    result.sort(key=sort_key)
    new_text = head + dump_videos(result)

    for c in changes:
        print(c)
    if new_text == text:
        print("catalog is in sync")
        return 0
    if args.check:
        print("catalog is out of sync, run scripts/videos/sync-drive.py")
        return 1
    CATALOG.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"wrote {CATALOG.relative_to(ROOT)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
