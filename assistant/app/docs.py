"""The documentation corpus the assistant answers from.

Every published version of the docs carries ``llms-full.txt``: all pages as
Markdown, one after another, each introduced by ``<!-- source: URL -->`` (see
scripts/hooks/md_mirror.py). One download per version gives the whole corpus,
which is split into pages and sections and searched with BM25.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
import re
import time
import unicodedata
import urllib.request
from collections import Counter
from dataclasses import dataclass, field

from .config import settings

SOURCE_RE = re.compile(r"^<!-- source: (?P<url>\S+) -->\s*$", re.M)
HEADING_RE = re.compile(r"^(#{1,4})\s+(.+?)\s*#*\s*$", re.M)
FENCE_RE = re.compile(r"^(```|~~~)", re.M)
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_.-]*[a-z0-9]|[a-z0-9]")
PAGE_CHUNK = 30_000  # characters returned per read_page call


def tokens(text: str) -> list[str]:
    out = []
    for t in TOKEN_RE.findall(text.lower()):
        out.append(t)
        if "-" in t or "." in t or "_" in t:
            out.extend(p for p in re.split(r"[-._]", t) if p)
    return out


def slugify(heading: str) -> str:
    """Same ids as Python-Markdown's toc extension, which MkDocs uses."""
    text = re.sub(r"\{.*?\}", "", heading)  # attribute lists like {#id}
    text = re.sub(r"[`*_\[\]()]", "", text)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)


def command_lines(text: str) -> list[str]:
    """Logical lines of a command block, whitespace- and continuation-insensitive.

    Used to verify that a command in an answer is copied from the docs: every
    line of it has to appear as a whole line in the page.
    """
    text = re.sub(r"\\[ \t]*\n", " ", text)
    lines = (re.sub(r"\s+", " ", line).strip() for line in text.splitlines())
    return [line for line in lines if line]


@dataclass
class Section:
    page: str
    title: str  # page title
    heading: str  # section heading ("" for the page intro)
    anchor: str
    text: str
    terms: Counter = field(default_factory=Counter)
    length: int = 0


@dataclass
class Page:
    path: str  # "kubernetes/installation/openshift/"
    title: str
    text: str
    headings: dict[str, str]  # anchor -> heading
    lines: frozenset = frozenset()
    digest: str = ""  # changes when the page text changes; cached answers depend on it


class Corpus:
    def __init__(self, version: str, pages: dict[str, Page], sections: list[Section]):
        self.version = version
        self.pages = pages
        self.sections = sections
        self.loaded = time.time()
        n = len(sections) or 1
        self.avgdl = sum(s.length for s in sections) / n
        df: Counter = Counter()
        for s in sections:
            df.update(s.terms.keys())
        self.idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}

    # -- tools -------------------------------------------------------------
    def search(self, query: str, limit: int = 8) -> list[dict]:
        q = tokens(query)
        if not q:
            return []
        k1, b = 1.4, 0.6
        scored = []
        for s in self.sections:
            score = 0.0
            for t in q:
                f = s.terms.get(t)
                if not f:
                    continue
                score += self.idf.get(t, 0) * f * (k1 + 1) / (f + k1 * (1 - b + b * s.length / self.avgdl))
            if score:
                # A match in the page title or heading counts extra.
                head = tokens(f"{s.title} {s.heading}")
                score *= 1 + 0.3 * sum(1 for t in set(q) if t in head)
                scored.append((score, s))
        scored.sort(key=lambda x: -x[0])
        results, per_page = [], Counter()
        for score, s in scored:
            if per_page[s.page] >= 2:
                continue
            per_page[s.page] += 1
            snippet = re.sub(r"\s+", " ", s.text)[:300]
            results.append(
                {"page": s.page, "page_title": s.title, "section": s.heading, "snippet": snippet}
            )
            if len(results) >= limit:
                break
        return results

    def read(self, path: str, offset: int = 0) -> dict:
        page = self.find(path)
        if not page:
            return {"error": f"no page {path!r}; use a path returned by search_docs or list_pages"}
        chunk = page.text[offset : offset + PAGE_CHUNK]
        more = offset + PAGE_CHUNK < len(page.text)
        return {
            "page": page.path,
            "title": page.title,
            "content": chunk,
            "next_offset": offset + PAGE_CHUNK if more else None,
        }

    def list_pages(self, prefix: str = "") -> list[dict]:
        prefix = prefix.strip("/")
        return [
            {"page": p.path, "title": p.title}
            for p in self.pages.values()
            if p.path.startswith(prefix)
        ]

    def find(self, path: str) -> Page | None:
        path = path.strip()
        path = re.sub(r"^https?://[^/]+/[^/]+/", "", path)  # full URL -> path
        path = re.sub(r"(index)?\.md$", "", path).split("#")[0].strip("/")
        return self.pages.get(f"{path}/" if path else "")

    def page_url(self, path: str) -> str:
        return f"{settings.docs_base}/{self.version}/{path}"


def _parse(text: str, version: str) -> Corpus:
    pages: dict[str, Page] = {}
    sections: list[Section] = []
    parts = SOURCE_RE.split(text)
    # parts = [preamble, url1, body1, url2, body2, ...]
    for url, body in zip(parts[1::2], parts[2::2]):
        path = re.sub(r"^https?://[^/]+/[^/]+/", "", url)
        body = re.sub(r"\n---\s*$", "", body.strip()).strip()
        m = HEADING_RE.search(body)
        title = m.group(2) if m and m.group(1) == "#" else path
        headings = {}
        # Split into sections at ## / ### headings outside code fences.
        current_heading, current_lines, in_fence = "", [], False
        chunks = []
        for line in body.splitlines():
            if FENCE_RE.match(line):
                in_fence = not in_fence
            hm = None if in_fence else HEADING_RE.match(line)
            if hm and len(hm.group(1)) in (2, 3):
                chunks.append((current_heading, "\n".join(current_lines)))
                current_heading, current_lines = hm.group(2), [line]
                headings[slugify(hm.group(2))] = hm.group(2)
            else:
                current_lines.append(line)
        chunks.append((current_heading, "\n".join(current_lines)))
        page = Page(path=path, title=title, text=body, headings=headings,
                    lines=frozenset(command_lines(body)),
                    digest=hashlib.sha256(body.encode()).hexdigest()[:16])
        pages[path] = page
        for heading, chunk in chunks:
            if not chunk.strip():
                continue
            terms = Counter(tokens(f"{title} {heading} {chunk}"))
            sections.append(Section(page=path, title=title, heading=heading,
                                    anchor=slugify(heading) if heading else "",
                                    text=chunk, terms=terms, length=sum(terms.values())))
    return Corpus(version, pages, sections)


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "simplyblock-docs-assistant"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


class Library:
    """Corpus per docs version, loaded on first use and refreshed periodically."""

    def __init__(self) -> None:
        self._corpora: dict[str, Corpus] = {}
        self._versions: tuple[float, dict[str, str]] = (0.0, {})
        self._lock = asyncio.Lock()

    async def versions(self) -> dict[str, str]:
        """Name or alias -> version directory, from versions.json."""
        stamp, known = self._versions
        if time.time() - stamp < settings.refresh_seconds and known:
            return known
        try:
            data = json.loads(await asyncio.to_thread(_get, f"{settings.docs_base}/versions.json"))
            known = {}
            for v in data:
                known[v["version"]] = v["version"]
                for alias in v.get("aliases", []):
                    known[alias] = v["version"]
            known.setdefault("dev", "dev")
            self._versions = (time.time(), known)
        except Exception:
            if not known:
                known = {"latest": "latest", "dev": "dev"}
        return known

    async def resolve(self, version: str | None) -> str:
        known = await self.versions()
        return known.get((version or "").strip("/"), known.get("latest", "latest"))

    async def corpus(self, version: str) -> Corpus:
        c = self._corpora.get(version)
        if c and time.time() - c.loaded < settings.refresh_seconds:
            return c
        async with self._lock:
            c = self._corpora.get(version)
            if c and time.time() - c.loaded < settings.refresh_seconds:
                return c
            try:
                raw = await asyncio.to_thread(_get, f"{settings.docs_base}/{version}/llms-full.txt")
            except Exception:
                if c:  # keep serving the old copy when a refresh fails
                    c.loaded = time.time()
                    return c
                raise LookupError(f"documentation version {version!r} has no llms-full.txt")
            c = await asyncio.to_thread(_parse, raw.decode("utf-8"), version)
            self._corpora[version] = c
            return c


library = Library()
