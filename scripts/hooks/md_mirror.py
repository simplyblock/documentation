"""Ship a Markdown twin of every page next to the built HTML.

AI agents that read the documentation pay for the Material theme on every
request: navigation, search index, and scripts dwarf the prose. The mirrors
written here carry the same content at a fraction of the size, so an agent can
read a page (or the whole corpus) instead of truncating it.

Each page is mirrored at its source path inside the built site::

    docs/kubernetes/installation.md  ->  site/kubernetes/installation.md
    docs/kubernetes/index.md         ->  site/kubernetes/index.md

That layout is deliberate. The HTML for ``docs/kubernetes/installation.md``
lives at ``/kubernetes/installation/``, so the mirror answers the usual
``<url>.md`` convention, and every relative link in the source (all of which
point at sibling ``.md`` files) keeps resolving between mirrors without any
rewriting.

The hook runs on ``on_page_markdown``, which fires after the macros plugin.
The mirrors therefore contain ``sbctl`` rather than ``{{ cliname }}`` and carry
the snippets from ``snippets/`` inlined, exactly as the HTML does.

Two index files are written alongside the mirrors:

``llms.txt``
    An index of every page in navigation order, following https://llmstxt.org/.
``llms-full.txt``
    The entire documentation concatenated into a single file.

Kill switches, for a build that needs to skip any of this::

    MD_MIRROR=0             no mirrors, no index files
    MD_MIRROR_LLMS_TXT=0    no llms.txt
    MD_MIRROR_LLMS_FULL=0   no llms-full.txt

Nothing in here is allowed to break a documentation build: every failure is
logged and swallowed. A missing mirror is a nuisance, a failed release is not.
"""

from __future__ import annotations

import json
import logging
import os

log = logging.getLogger("mkdocs.hooks.md_mirror")

ENABLED = os.environ.get("MD_MIRROR", "1") != "0"
WRITE_LLMS_TXT = os.environ.get("MD_MIRROR_LLMS_TXT", "1") != "0"
WRITE_LLMS_FULL = os.environ.get("MD_MIRROR_LLMS_FULL", "1") != "0"

LLMS_TXT = "llms.txt"
LLMS_FULL_TXT = "llms-full.txt"

# Blockquote summary at the top of llms.txt and llms-full.txt. Used unless
# site_description is set in mkdocs.yml.
SUMMARY = (
    "Simplyblock is a cloud-native, software-defined storage platform that provides "
    "NVMe-over-TCP block storage for Kubernetes and Linux, with erasure coding, "
    "snapshots, clones, and multi-tenancy."
)

# Pages that render to a JavaScript widget rather than to prose. Their mirror
# carries a pointer to the machine-readable source instead of the widget markup.
STUBS = {
    "reference/api/reference.md": (
        "The interactive API reference is rendered in the browser from an OpenAPI "
        "specification and has no meaningful Markdown representation.\n\n"
        "Read the specification directly: {base}reference/api/openapi.json\n"
    ),
}

# Collected during the build, consumed in on_post_build.
_pages: list = []
_nav = None


# --------------------------------------------------------------------------
# events
# --------------------------------------------------------------------------

def on_pre_build(*, config) -> None:
    # mkdocs serve rebuilds in-process, so never accumulate across builds.
    global _nav
    _pages.clear()
    _nav = None


def on_nav(nav, *, config, files):
    global _nav
    _nav = nav
    return nav


def on_page_markdown(markdown: str, *, page, config, files) -> None:
    """Capture the page Markdown after every other plugin has transformed it."""
    if ENABLED and page.file.src_uri.endswith(".md"):
        _pages.append((page, markdown))
    return None


def on_post_build(*, config) -> None:
    if not ENABLED:
        return

    base = _canonical_base(config)
    written = 0
    for page, markdown in _pages:
        try:
            _write(
                os.path.join(config.site_dir, page.file.src_uri),
                _mirror(page, markdown, base),
            )
            written += 1
        except Exception as error:  # never fail the build over a mirror
            log.warning("md_mirror: %s: %s", page.file.src_uri, error)
    log.info("md_mirror: wrote %d Markdown mirrors", written)

    ordered = _in_nav_order()

    if WRITE_LLMS_TXT:
        try:
            _write(os.path.join(config.site_dir, LLMS_TXT), _llms_txt(config, ordered, base))
            log.info("md_mirror: wrote %s (%d entries)", LLMS_TXT, len(ordered))
        except Exception as error:
            log.warning("md_mirror: %s: %s", LLMS_TXT, error)

    if WRITE_LLMS_FULL:
        try:
            _write(os.path.join(config.site_dir, LLMS_FULL_TXT), _llms_full(config, ordered, base))
            log.info("md_mirror: wrote %s", LLMS_FULL_TXT)
        except Exception as error:
            log.warning("md_mirror: %s: %s", LLMS_FULL_TXT, error)


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------

def _mirror(page, markdown: str, base: str) -> str:
    """Front matter plus body for a single mirrored page."""
    title = _title(page)
    body = STUBS[page.file.src_uri].format(base=base) if page.file.src_uri in STUBS else markdown

    front = [f"title: {_yaml(title)}"]
    description = page.meta.get("description")
    if description:
        front.append(f"description: {_yaml(description)}")
    front.append(f"source: {_yaml(_page_url(page, base))}")

    return "---\n" + "\n".join(front) + "\n---\n\n" + _with_heading(body, title)


def _llms_txt(config, ordered, base: str) -> str:
    lines = [
        f"# {config.site_name}",
        "",
        f"> {config.site_description or SUMMARY}",
        "",
        "Every page of this documentation is available as Markdown: append `.md` to any "
        "page URL, or request the page with an `Accept: text/markdown` header. The "
        f"complete documentation as a single file: {base}{LLMS_FULL_TXT}",
    ]

    for section, entries in _sections(ordered):
        lines += ["", f"## {section}", ""]
        for label, page in entries:
            entry = f"- [{label}]({base}{page.file.src_uri})"
            description = page.meta.get("description")
            if description:
                entry += f": {' '.join(str(description).split())}"
            lines.append(entry)

    return "\n".join(lines) + "\n"


def _llms_full(config, ordered, base: str) -> str:
    parts = [
        f"# {config.site_name}",
        "",
        f"> {config.site_description or SUMMARY}",
        "",
        f"The complete documentation, one page after another, in navigation order. "
        f"The rendered pages live at {base}",
    ]

    for _, page in ordered:
        markdown = _markdown_of(page)
        if markdown is None:
            continue
        title = _title(page)
        body = STUBS[page.file.src_uri].format(base=base) if page.file.src_uri in STUBS else markdown
        parts += [
            "",
            "---",
            "",
            f"<!-- source: {_page_url(page, base)} -->",
            "",
            _with_heading(body, title).rstrip(),
        ]

    return "\n".join(parts) + "\n"


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def _canonical_base(config) -> str:
    """Absolute base for every URL the mirrors point at.

    Follows the canonical strategy of templates/base.html: all versions
    consolidate onto the /latest/ alias, so mirrors of an older build still
    attribute back to the page a reader is meant to land on.
    """
    base = config.extra.get("canonical_base") or config.site_url or ""
    return base if base.endswith("/") else base + "/"


def _page_url(page, base: str) -> str:
    """Absolute URL of the rendered HTML page a mirror belongs to."""
    return base + page.url.lstrip("/")


def _title(page) -> str:
    return str(page.meta.get("title") or page.title or page.file.src_uri)


def _with_heading(body: str, title: str) -> str:
    """Give the mirror a level-one heading.

    Pages carry their title in front matter and the theme renders it, so almost
    no source file starts with one. A standalone Markdown document needs it.
    """
    body = body.strip()
    for line in body.splitlines():
        if line.strip():
            return body + "\n" if line.startswith("# ") else f"# {title}\n\n{body}\n"
    return f"# {title}\n"


def _yaml(value) -> str:
    """Quote a scalar for YAML front matter (JSON is valid YAML)."""
    return json.dumps(str(value), ensure_ascii=False)


def _markdown_of(page):
    for candidate, markdown in _pages:
        if candidate is page:
            return markdown
    return None


def _in_nav_order() -> list:
    """All mirrored pages in navigation order, each with its section trail."""
    ordered = []
    seen = set()

    def walk(items, trail):
        for item in items:
            if item.is_page and item.file.src_uri.endswith(".md"):
                ordered.append((trail, item))
                seen.add(item.file.src_uri)
            elif item.is_section:
                walk(item.children, trail + [item.title])

    if _nav is not None:
        walk(_nav.items, [])

    # Pages outside the navigation still get an entry, in build order.
    ordered += [([], page) for page, _ in _pages if page.file.src_uri not in seen]
    return ordered


def _sections(ordered) -> list:
    """Group pages into the level-two sections of llms.txt.

    The top level of the navigation becomes the section headings. Deeper
    nesting is kept in the entry label, so the structure survives the flat
    format llms.txt asks for.
    """
    sections: dict[str, list] = {}
    for trail, page in ordered:
        section = trail[0] if trail else "Overview"
        nested = trail[1:]
        title = _title(page)
        # The index page of a subsection carries the section title itself.
        parts = nested if nested and nested[-1] == title else nested + [title]
        sections.setdefault(section, []).append((" / ".join(parts), page))
    return list(sections.items())


def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as target:
        target.write(content)
