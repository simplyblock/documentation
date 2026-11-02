"""Render the video catalog of the Tutorials section.

The catalog lives in ``docs/tutorials/videos.yml`` (see the header of that file
for its fields). This hook

* loads and validates it in ``on_config`` and exposes the normalized list as
  ``config.extra.sb_videos``, which ``templates/main.html`` turns into the
  "Video pick of the day" bar on top of every page, and
* replaces the marker ``<!-- sb:video-gallery -->`` in a page with the
  filterable tile gallery (``docs/assets/javascripts/videos.js`` adds the
  filter buttons' behavior, the player dialog, and deep links).

The gallery is plain HTML with one link per video, so it stays usable without
JavaScript and reads well in the Markdown mirror written by ``md_mirror.py``.
For that, this hook has to be listed before ``md_mirror.py`` in ``mkdocs.yml``.

A broken catalog entry is logged and skipped; it never fails the build.
"""

from __future__ import annotations

import html
import logging
import re
from pathlib import Path

import yaml
from mkdocs.utils import get_relative_url

log = logging.getLogger("mkdocs.hooks.videos")

CATALOG = "tutorials/videos.yml"
GALLERY_MARKER = "<!-- sb:video-gallery -->"
SOURCES = ("drive_id", "youtube", "src")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

_categories: list[dict] = []
_icons: dict[str, str] = {}
_videos: list[dict] = []


def _is_url(value: str) -> bool:
    return value.startswith(("http://", "https://"))


def _icon_svg(name: str) -> str:
    """Inline SVG of a theme icon such as material/server, or "" if unknown."""
    if not name:
        return ""
    try:
        import material

        path = Path(material.__file__).parent / "templates" / ".icons" / f"{name}.svg"
        return path.read_text(encoding="utf-8").strip()
    except Exception:  # noqa: BLE001
        log.warning("%s: icon %r not found", CATALOG, name)
        return ""


def _normalize(raw: dict, labels: dict[str, str], seen: set[str]) -> dict | None:
    vid = str(raw.get("id", ""))
    problem = None
    if not ID_RE.match(vid):
        problem = "id must be lowercase letters, digits and dashes"
    elif vid in seen:
        problem = "duplicate id"
    elif raw.get("category") not in labels:
        problem = f"unknown category {raw.get('category')!r}"
    elif not raw.get("title"):
        problem = "title missing"
    elif sum(1 for s in SOURCES if raw.get(s)) != 1:
        problem = "exactly one of drive_id, youtube, src required"
    if problem:
        log.error("%s: video %r skipped: %s", CATALOG, vid or raw, problem)
        return None
    seen.add(vid)

    video = {
        "id": vid,
        "category": raw["category"],
        "category_label": labels[raw["category"]],
        "title": str(raw["title"]),
        "teaser": str(raw.get("teaser") or ""),
        "description": str(raw.get("description") or ""),
        "page": raw.get("page") or "",
        "pick": raw.get("pick", True) is not False,
        # Paths below docs/ are kept site-relative here and made page-relative
        # when rendered; URLs pass through.
        "src": "",
        "poster": str(raw.get("poster") or ""),
    }
    if raw.get("drive_id"):
        did = str(raw["drive_id"])
        video["kind"] = "drive"
        video["embed"] = f"https://drive.google.com/file/d/{did}/preview"
        video["watch"] = f"https://drive.google.com/file/d/{did}/view"
    elif raw.get("youtube"):
        yid = str(raw["youtube"])
        video["kind"] = "youtube"
        video["embed"] = f"https://www.youtube-nocookie.com/embed/{yid}?autoplay=1&rel=0"
        video["watch"] = f"https://www.youtube.com/watch?v={yid}"
    else:
        video["kind"] = "file"
        video["src"] = str(raw["src"])
        video["embed"] = ""
        video["watch"] = video["src"]
    return video


def on_config(config, **kwargs):
    global _categories, _videos, _icons
    _categories, _videos, _icons = [], [], {}
    path = Path(config["docs_dir"]) / CATALOG
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except FileNotFoundError:
        log.warning("%s not found, no video gallery", CATALOG)
        data = {}
    except Exception as exc:  # noqa: BLE001 - never break the build
        log.error("%s could not be read: %s", CATALOG, exc)
        data = {}

    _categories = [
        {"id": str(c["id"]), "label": str(c["label"])}
        for c in data.get("categories") or []
        if c.get("id") and c.get("label")
    ]
    labels = {c["id"]: c["label"] for c in _categories}
    for c in data.get("categories") or []:
        if c.get("id"):
            _icons[str(c["id"])] = _icon_svg(str(c.get("icon") or ""))
    seen: set[str] = set()
    for raw in data.get("videos") or []:
        video = _normalize(raw or {}, labels, seen)
        if video:
            _videos.append(video)

    config["extra"]["sb_videos"] = [
        {k: v[k] for k in ("id", "title", "teaser", "category_label", "pick")}
        for v in _videos
    ]
    return config


def _site_path(value: str, page_url: str) -> str:
    """A path below docs/ (or a URL) as seen from the page at page_url."""
    if not value or _is_url(value):
        return value
    target = value
    if target.endswith(".md"):
        target = target[:-3]
        target = target[: -len("index")] if target.endswith("index") else target + "/"
    return get_relative_url(target, page_url)


def _tile(video: dict, page_url: str) -> str:
    e = lambda s: html.escape(s, quote=True)  # noqa: E731
    src = _site_path(video["src"], page_url)
    watch = src if video["kind"] == "file" else video["watch"]
    poster = _site_path(video["poster"], page_url)
    attrs = {
        "class": "sb-video__link",
        "href": watch,
        "data-sb-kind": video["kind"],
        "data-sb-embed": video["embed"],
        "data-sb-src": src,
        "data-sb-poster": poster,
        "data-sb-title": video["title"],
        "data-sb-page": _site_path(video["page"], page_url),
    }
    attr_html = " ".join(f'{k}="{e(v)}"' for k, v in attrs.items() if v)
    # Every tile is drawn from the same parts (category color and icon, the
    # number of the id, the title), not from a frame of the video.
    number = re.search(r"(\d+)$", video["id"])
    icon = _icons.get(video["category"], "")
    parts = [
        f'<li class="sb-video" id="video-{e(video["id"])}" data-sb-video="{e(video["id"])}" '
        f'data-sb-category="{e(video["category"])}">',
        f"<a {attr_html}>",
        '<span class="sb-video__art">',
        f'<span class="sb-video__icon" aria-hidden="true">{icon}</span>' if icon else "",
        '<span class="sb-video__meta">',
        f'<span class="sb-video__category">{e(video["category_label"])}</span>',
        f'<span class="sb-video__number">{int(number.group(1)):02d}</span>' if number else "",
        "</span>",
        f'<span class="sb-video__title">{e(video["title"])}</span>',
        '<span class="sb-video__play" aria-hidden="true"></span>',
        "</span>",
        f'<span class="sb-video__description">{e(video["description"])}</span>' if video["description"] else "",
        "</a>",
        "</li>",
    ]
    return "".join(p for p in parts if p)


def _gallery(page_url: str) -> str:
    counts = {c["id"]: 0 for c in _categories}
    for v in _videos:
        counts[v["category"]] += 1
    buttons = [
        '<button type="button" class="sb-videos__filter" data-sb-filter="all" aria-pressed="true">'
        f'All<span class="sb-videos__count">{len(_videos)}</span></button>'
    ]
    for c in _categories:
        if counts[c["id"]]:
            buttons.append(
                f'<button type="button" class="sb-videos__filter" data-sb-filter="{html.escape(c["id"])}" '
                f'aria-pressed="false">{html.escape(c["label"])}'
                f'<span class="sb-videos__count">{counts[c["id"]]}</span></button>'
            )
    # One block of raw HTML without blank lines, so Markdown leaves it alone.
    lines = [
        '<div class="sb-videos" data-sb-videos>',
        '<div class="sb-videos__filters" role="group" aria-label="Filter videos by category">',
        *buttons,
        "</div>",
        '<ul class="sb-videos__grid">',
        *(_tile(v, page_url) for v in _videos),
        "</ul>",
        "</div>",
    ]
    return "\n".join(lines)


def on_page_markdown(markdown, page, config, files, **kwargs):
    if GALLERY_MARKER not in markdown:
        return markdown
    if not _videos:
        return markdown.replace(GALLERY_MARKER, "")
    return markdown.replace(GALLERY_MARKER, "\n" + _gallery(page.url) + "\n")

