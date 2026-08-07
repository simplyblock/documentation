#!/usr/bin/env python3
"""Check mkdocs specific syntax in the documentation markdown files.

These rules fail the check:

* An admonition ("!!! note", "??? tip", "???+ info") and a content tab
  ('=== "Title"') must be followed by a body that is indented by at least four
  spaces. Without it the text ends up outside of the block. Indentation is
  measured relative to the marker and behind any blockquote prefix, so nested
  blocks are checked against their own position.
* A code block must declare a language ("```yaml", "```bash", "```plain"), and
  not an alias of one: "sh", "shell", "zsh", "console", "text", "txt", "yml".
* A heading carries a space behind its hashes ("## Title").
* A section is separated by a heading, not by a horizontal rule.
* A line carries no trailing whitespace, and a file ends with exactly one newline
  behind its last line of text.
* A list has a blank line above it, a link carries no space between its text and
  its target, and a table carries its separator row. Each of these renders as a
  plain paragraph when it is missing, without any warning.
* A nested list item is indented by four spaces per level. python-markdown reads
  one to three spaces as a sibling and eight or more as text of the item above,
  both without a warning.
* A placeholder ("{{ cliname }}") must resolve against the "extra" section of
  mkdocs.yml. The macros plugin runs with "on_undefined: strict", so an unknown
  placeholder breaks the build.
* A page declares its title and its navigation weight in the frontmatter.
* An external link opens in a new tab ('{:target="_blank" rel="noopener"}').
* An internal link points at a file that exists. Absolute links resolve against
  the docs directory, matching "absolute_links: relative_to_docs".
* An included snippet ("{% include 'file.md' %}") exists.

These rules are reported as a warning and do not fail the check yet:

* A code block carries a title attribute.
* A page starts with an introduction text instead of a heading.
* A page uses H2 to H5 only, since H1 is the frontmatter title.

Snippets are fragments injected into a page, so the frontmatter and introduction
rules do not apply to them.

By default all Markdown files below "docs/" and "snippets/" are scanned.
Generated files are skipped, since they have to be corrected at their source.

Usage:
    python3 scripts/check-mkdocs-syntax.py [PATH ...]
"""

import argparse
import os
import re
import sys
import unicodedata

from markdown_common import (
    CODE_FENCE_PATTERN,
    CODE_SPAN_PATTERN,
    DEFAULT_TARGET_DIRS,
    SCANNED_EXTENSIONS,
    SEVERITY_WARNING,
    Violation,
    collect_files,
    drop_generated,
    indentation_of,
    read_lines,
    relative_path,
    report_violations,
    repository_root,
)

MKDOCS_CONFIG_NAME = "mkdocs.yml"

# The info string of an opening fence, e.g. 'bash title="Create a cluster"'.
CODE_FENCE_INFO_PATTERN = re.compile(r"^\s*```(.*)$")
# Diagrams carry no title attribute.
UNTITLED_FENCE_LANGUAGES = {"mermaid"}

# One thing is spelled one way. Each of these is a valid highlighter alias, and
# each has a spelling the documentation uses instead.
LANGUAGE_ALIASES = {
    "sh": "bash",
    "shell": "bash",
    "zsh": "bash",
    "console": "plain",
    "text": "plain",
    "txt": "plain",
    "yml": "yaml",
}

# Blocks whose body has to be indented below their marker line. Admonitions use
# "!!!" (always open), "???" (collapsed) and "???+" (expanded); content tabs use
# "===" and "===+". A bare "===" without a title is a setext heading underline,
# hence the required whitespace.
INDENTED_BLOCKS = (
    ("Admonition", re.compile(r"^(?:!!!|\?\?\?\+?)(?:\s|$)")),
    ("Content tab", re.compile(r"^===\+?\s")),
)
BLOCK_BODY_INDENT = 4

# A blockquote prefix, so that a marker inside a quote is measured against the
# quote instead of the start of the line.
QUOTE_PREFIX_PATTERN = re.compile(r"^((?:\s*>\s?)*)")

# Placeholders are rendered before markdown, so they also apply inside code
# blocks. Only the leading name is of interest: "{{ version.provider | upper }}"
# resolves through the "version" key.
PLACEHOLDER_PATTERN = re.compile(r"\{\{(.*?)\}\}")
PLACEHOLDER_NAME_PATTERN = re.compile(r"^\s*([A-Za-z_][\w-]*)")

# Variables the macros plugin provides on its own, next to the "extra" section.
MACROS_BUILTINS = {"config", "page", "environment", "git", "navigation", "macros_info"}

EXTRA_SECTION_PATTERN = re.compile(r"^extra\s*:")
EXTRA_KEY_PATTERN = re.compile(r"^\s+([A-Za-z_][\w-]*)\s*:")
INCLUDE_DIR_PATTERN = re.compile(r"^\s+include_dir\s*:\s*(\S+)")
DEFAULT_INCLUDE_DIR = "snippets"

# Frontmatter fields every documentation page carries.
FRONTMATTER_FENCE = "---"
REQUIRED_FRONTMATTER_FIELDS = ("title", "weight", "description")
FRONTMATTER_FIELD_PATTERN = re.compile(r"^([A-Za-z_][\w-]*)\s*:")

# Generated references carry no description, they are written by their generator.
DESCRIPTION_EXEMPT_PATHS = (
    os.path.join("reference", "cli"),
    os.path.join("reference", "operator", "reference.md"),
)

# A description longer than this is cut off in search results, the narrower band
# is the length it should aim for.
DESCRIPTION_MAX_LENGTH = 180
DESCRIPTION_PREFERRED_MIN = 120
DESCRIPTION_PREFERRED_MAX = 160

# Pages use H2 to H5, the H1 is provided by the frontmatter title.
H1_PATTERN = re.compile(r"^#\s")
HEADING_PATTERN = re.compile(r"^#{1,6}\s")

# Links, with the optional attribute list mkdocs supports:
# [text](https://example.org){:target="_blank" rel="noopener"}
LINK_PATTERN = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)(\{[^}]*\})?")
EXTERNAL_LINK_SCHEMES = ("http://", "https://")
IGNORED_LINK_SCHEMES = ("mailto:", "tel:", "data:")
EXTERNAL_LINK_ATTRIBUTE = "target="

# Heading ids, as generated by the toc extension: an explicit "{#id}" from
# attr_list wins, otherwise the heading text is slugified. HTML blocks can carry
# their own ids as well.
HEADING_TEXT_PATTERN = re.compile(r"^#{1,6}\s+(.*)$")
EXPLICIT_ID_PATTERN = re.compile(r"\{[^}]*#([A-Za-z][\w:.-]*)[^}]*\}")
HTML_ID_PATTERN = re.compile(r"\bid=[\"']([^\"']+)[\"']")
MARKDOWN_LINK_TEXT_PATTERN = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
ATTRIBUTE_LIST_PATTERN = re.compile(r"\{[^}]*\}")
EMPHASIS_PATTERN = re.compile(r"[`*_~]")

INCLUDE_PATTERN = re.compile(r"\{%\s*include\s+['\"]([^'\"]+)['\"]")

# python-markdown nests a list item only when it is indented by four spaces
# relative to the item above it. One to three spaces render it as a sibling, and
# eight or more make it part of the text of the item above. Both fail silently,
# so the indentation is checked rather than trusted.
LIST_ITEM_PATTERN = re.compile(r"^(?P<indent>[ ]*)(?:[-*+]|\d+[.)])\s")
# A marker without its space is not a list item at all, it is literal text.
UNSPACED_MARKER_PATTERN = re.compile(r"^[ ]*[-*+][A-Za-z`\[]")
LIST_INDENT_STEP = 4

# A list needs a blank line above it. Without one, python-markdown reads its items
# as more text of the paragraph and prints them as one run-on line.
LIST_PREV_EXEMPT_PATTERN = re.compile(r"^\s*(?:!!!|\?\?\?\+?|===|>|\||#|\{%|<|```|:)")

# "[text] (target)" with a space between the two halves is not a link, it is the
# literal text of both.
SPACED_LINK_PATTERN = re.compile(r"\]\s+\(")

# A table needs its separator row, otherwise every row runs together as one
# paragraph.
TABLE_ROW_PATTERN = re.compile(r"^\s*\|")
TABLE_SEPARATOR_PATTERN = re.compile(r"^\s*\|[\s:|-]+\|\s*$")

# "##Heading" happens to render in python-markdown, but not in the preview of a
# pull request, and a heading is written one way like everything else.
# Up to three spaces, since four or more make the line an indented code block and
# a "#" there is a comment, not a heading.
UNSPACED_HEADING_PATTERN = re.compile(r"^ {0,3}#{1,6}[^#\s]")

# "<POOL_ID>" outside a code span is passed through as raw html, and the browser
# drops it as an unknown tag, so the reader never sees it.
ANGLE_TOKEN_PATTERN = re.compile(r"<(/?)([A-Za-z_][\w.:-]*)\s*/?>")
HTML_TAG_NAMES = {
    "a", "b", "blockquote", "br", "code", "details", "div", "em", "figcaption",
    "figure", "form", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "iframe",
    "img", "input", "label", "li", "ol", "p", "pre", "script", "small", "span",
    "strong", "style", "sub", "summary", "sup", "table", "td", "th", "tr", "u",
    "ul",
}

# A line of "===" or "---" under text is a setext heading, not a rule and not a
# content tab. A single "-" is a list marker, so two are required here.
SETEXT_PATTERN = re.compile(r"^\s*(?:=+|-{2,})\s*$")

# A horizontal rule is not used to separate sections, a heading does that. The
# same three characters divide the title of a Material grid card from its body,
# and there they are indented, so only a rule at the margin is reported.
HORIZONTAL_RULE_PATTERN = re.compile(r"^ {0,3}(?:-{3,}|\*{3,}|_{3,})\s*$")

# A marker with nothing behind it renders as an empty bullet.
EMPTY_LIST_ITEM_PATTERN = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s*$")

# A url that is not inside a link is printed as text, python-markdown does not
# turn it into a link on its own.
BARE_URL_PATTERN = re.compile(r"(?<![(\[<\w])https?://")

# Two spaces at the end of a line insert a line break into the middle of a
# paragraph. The rest of the trailing whitespace changes nothing at all, which is
# the reason to remove it: it is invisible, it lands in every diff, and it is the
# only kind of change that can never be reviewed.
TRAILING_BREAK_SPACES = 2


def load_placeholder_names(config_path):
    """Collect the placeholder names declared below "extra:" in mkdocs.yml.

    Only the keys are of interest, so the section is read directly instead of
    through a YAML parser: mkdocs.yml carries custom python tags that a plain
    parser rejects, and the check stays free of third-party dependencies. Nested
    keys are not resolved, so "{{ version.provider }}" is validated through its
    leading "version" name.
    """
    try:
        lines = read_lines(config_path)
    except OSError:
        return None

    names = set()
    key_indent = None
    in_extra = False
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if EXTRA_SECTION_PATTERN.match(line):
            in_extra = True
            continue
        if not in_extra:
            continue
        if indentation_of(line) == 0:
            break
        match = EXTRA_KEY_PATTERN.match(line)
        if not match:
            continue
        if key_indent is None:
            key_indent = indentation_of(line)
        if indentation_of(line) == key_indent:
            names.add(match.group(1))
    return names


def split_quote_prefix(line):
    """Split a line into its blockquote depth and the content behind the quote."""
    match = QUOTE_PREFIX_PATTERN.match(line)
    return match.group(1).count(">"), line[match.end():]


def block_marker(content):
    """Return the name of the indented block a line opens, if it opens one."""
    for name, pattern in INDENTED_BLOCKS:
        if pattern.match(content.lstrip()):
            return name
    return None


def check_block_indentation(lines, rel):
    """Admonitions and content tabs need a body indented below their marker.

    Indentation is measured behind any blockquote prefix and relative to the
    marker itself, so blocks nested in quotes, lists or other blocks are checked
    against their own position instead of the start of the line.
    """
    violations = []
    in_code_fence = False

    for index, line in enumerate(lines):
        if CODE_FENCE_PATTERN.match(line):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue

        quote_depth, content = split_quote_prefix(line)
        name = block_marker(content)
        if not name:
            continue

        marker_indent = indentation_of(content)
        required_indent = marker_indent + BLOCK_BODY_INDENT

        # Blank lines between the marker and its body are allowed.
        body_index = index + 1
        while body_index < len(lines):
            _, body_content = split_quote_prefix(lines[body_index])
            if body_content.strip():
                break
            body_index += 1

        if body_index >= len(lines):
            reason = f"{name} has no body"
        else:
            body_depth, body_content = split_quote_prefix(lines[body_index])
            body_indent = indentation_of(body_content)
            if body_depth != quote_depth:
                reason = (
                    f"{name} has no body, the next content is at blockquote "
                    f"level {body_depth} instead of {quote_depth}"
                )
            elif body_indent < required_indent:
                reason = (
                    f"{name} body must be indented by {BLOCK_BODY_INDENT} spaces "
                    f"(expected indent {required_indent}, found {body_indent} "
                    f"on line {body_index + 1})"
                )
            else:
                continue

        violations.append(
            Violation(
                file=rel,
                line=index + 1,
                column=len(line) - len(content.lstrip()) + 1,
                check="block-indentation",
                reason=reason,
                excerpt=line.strip(),
            )
        )

    return violations


def is_snippet(file_path, include_dir):
    return os.path.abspath(file_path).startswith(os.path.abspath(include_dir) + os.sep)


def load_include_dir(config_path, repo_root):
    """Read the snippet directory the macros plugin includes from."""
    try:
        lines = read_lines(config_path)
    except OSError:
        return os.path.join(repo_root, DEFAULT_INCLUDE_DIR)

    for line in lines:
        match = INCLUDE_DIR_PATTERN.match(line)
        if match:
            return os.path.normpath(os.path.join(repo_root, match.group(1)))
    return os.path.join(repo_root, DEFAULT_INCLUDE_DIR)


def frontmatter_bounds(lines):
    """Return the frontmatter fields and the index the page body starts at."""
    if not lines or lines[0].strip() != FRONTMATTER_FENCE:
        return None, 0

    fields = {}
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == FRONTMATTER_FENCE:
            return fields, index + 1
        match = FRONTMATTER_FIELD_PATTERN.match(line)
        if match:
            fields[match.group(1)] = line
    return fields, len(lines)


def requires_description(file_path, docs_root):
    """Generated references are exempt from the description field."""
    relative = os.path.relpath(os.path.abspath(file_path), docs_root)
    return not any(
        relative == exempt or relative.startswith(exempt + os.sep)
        for exempt in DESCRIPTION_EXEMPT_PATHS
    )


def check_frontmatter(lines, rel, file_path, docs_root):
    """Every page declares its title, description and navigation position."""
    fields, _ = frontmatter_bounds(lines)

    required = [
        field
        for field in REQUIRED_FRONTMATTER_FIELDS
        if field != "description" or requires_description(file_path, docs_root)
    ]

    if fields is None:
        return [
            Violation(
                file=rel,
                line=1,
                column=1,
                check="frontmatter-fields",
                reason="Page has no frontmatter block",
                excerpt=lines[0].strip() if lines else "",
            )
        ]

    violations = []

    missing = [field for field in required if field not in fields]
    if missing:
        violations.append(
            Violation(
                file=rel,
                line=1,
                column=1,
                check="frontmatter-fields",
                reason=f"Frontmatter is missing: {', '.join(missing)}",
                excerpt=FRONTMATTER_FENCE,
            )
        )

    if "description" in fields:
        violations.extend(check_description_length(fields["description"], rel, lines))

    return violations


def frontmatter_value(line):
    """Return the value of a frontmatter field, without its quotes."""
    value = line.split(":", 1)[1].strip()
    if len(value) >= 2 and value[0] in "\"'" and value[-1] == value[0]:
        value = value[1:-1]
    return value


def check_description_length(description_line, rel, lines):
    """The description has to fit into a search result snippet."""
    value = frontmatter_value(description_line)
    length = len(value)
    line_number = lines.index(description_line) + 1

    if length > DESCRIPTION_MAX_LENGTH:
        return [
            Violation(
                file=rel,
                line=line_number,
                column=1,
                check="description-length",
                reason=(
                    f"Description is {length} characters, "
                    f"the maximum is {DESCRIPTION_MAX_LENGTH}"
                ),
                excerpt=value[:60] + "...",
            )
        ]

    if DESCRIPTION_PREFERRED_MIN <= length <= DESCRIPTION_PREFERRED_MAX:
        return []

    return [
        Violation(
            file=rel,
            line=line_number,
            column=1,
            check="description-length",
            reason=(
                f"Description is {length} characters, it should be between "
                f"{DESCRIPTION_PREFERRED_MIN} and {DESCRIPTION_PREFERRED_MAX}"
            ),
            excerpt=value[:60] + "...",
            severity=SEVERITY_WARNING,
        )
    ]


def check_headings(lines, rel):
    """Pages open with an introduction and use H2 to H5 for their sections."""
    violations = []
    _, body_start = frontmatter_bounds(lines)

    first_index = body_start
    while first_index < len(lines) and not lines[first_index].strip():
        first_index += 1

    if first_index < len(lines) and HEADING_PATTERN.match(lines[first_index].lstrip()):
        violations.append(
            Violation(
                file=rel,
                line=first_index + 1,
                column=1,
                check="page-introduction",
                reason="Page starts with a heading instead of an introduction text",
                excerpt=lines[first_index].strip(),
                severity=SEVERITY_WARNING,
            )
        )

    in_code_fence = False
    for index in range(body_start, len(lines)):
        line = lines[index]
        if CODE_FENCE_PATTERN.match(line):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        if H1_PATTERN.match(line):
            violations.append(
                Violation(
                    file=rel,
                    line=index + 1,
                    column=1,
                    check="heading-level",
                    reason="H1 is reserved for the frontmatter title, use H2 to H5",
                    excerpt=line.strip(),
                    severity=SEVERITY_WARNING,
                )
            )

    return violations


def slugify_heading(text):
    """Reproduce the heading id the toc extension generates."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)


def heading_text_of(heading):
    """Reduce a heading to the text the id is generated from."""
    text = MARKDOWN_LINK_TEXT_PATTERN.sub(r"\1", heading)
    text = ATTRIBUTE_LIST_PATTERN.sub("", text)
    return EMPHASIS_PATTERN.sub("", text).strip()


def anchors_of(file_path, cache):
    """Collect the anchors a page offers: heading ids and explicit html ids."""
    if file_path in cache:
        return cache[file_path]

    try:
        lines = read_lines(file_path)
    except OSError:
        lines = []

    anchors = set()
    used = set()
    in_code_fence = False
    for line in lines:
        if CODE_FENCE_PATTERN.match(line):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue

        anchors.update(HTML_ID_PATTERN.findall(line))

        match = HEADING_TEXT_PATTERN.match(line)
        if not match:
            continue

        explicit = EXPLICIT_ID_PATTERN.search(match.group(1))
        if explicit:
            anchors.add(explicit.group(1))
            continue

        # Repeated headings are numbered, exactly like the toc extension does.
        base = slugify_heading(heading_text_of(match.group(1)))
        candidate = base
        counter = 0
        while candidate in used or not candidate:
            counter += 1
            candidate = f"{base}_{counter}"
        used.add(candidate)
        anchors.add(candidate)

    cache[file_path] = anchors
    return anchors


def mask_code_spans(line):
    """Blank out inline code, so that samples of links are not treated as links."""
    return CODE_SPAN_PATTERN.sub(lambda match: " " * len(match.group(0)), line)


def check_links(lines, rel, file_path, docs_root, anchor_cache):
    """External links open in a new tab, internal links point at existing files."""
    violations = []
    in_code_fence = False
    directory = os.path.dirname(os.path.abspath(file_path))

    for index, line in enumerate(lines):
        if CODE_FENCE_PATTERN.match(line):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue

        for match in LINK_PATTERN.finditer(mask_code_spans(line)):
            is_image, target, attributes = match.group(1), match.group(3), match.group(4)

            if target.startswith(EXTERNAL_LINK_SCHEMES):
                # Images are embedded, they are never navigated to.
                if is_image or (attributes and EXTERNAL_LINK_ATTRIBUTE in attributes):
                    continue
                violations.append(
                    Violation(
                        file=rel,
                        line=index + 1,
                        column=match.start() + 1,
                        check="external-link-attributes",
                        reason=(
                            "External link must open in a new tab "
                            '({:target="_blank" rel="noopener"})'
                        ),
                        excerpt=target,
                    )
                )
                continue

            if target.startswith(IGNORED_LINK_SCHEMES):
                continue

            path, _, anchor = target.partition("#")

            if not path:
                # An anchor on the page itself.
                resolved = os.path.abspath(file_path)
            elif path.startswith("/"):
                # mkdocs resolves absolute links against the docs directory
                # (validation.links.absolute_links: relative_to_docs).
                resolved = os.path.normpath(os.path.join(docs_root, path.lstrip("/")))
            else:
                resolved = os.path.normpath(os.path.join(directory, path))

            if not os.path.exists(resolved):
                violations.append(
                    Violation(
                        file=rel,
                        line=index + 1,
                        column=match.start() + 1,
                        check="internal-link-target",
                        reason=f"Link target does not exist: {path}",
                        excerpt=target,
                    )
                )
                continue

            if not anchor or os.path.splitext(resolved)[1].lower() not in SCANNED_EXTENSIONS:
                continue

            if anchor in anchors_of(resolved, anchor_cache):
                continue

            violations.append(
                Violation(
                    file=rel,
                    line=index + 1,
                    column=match.start() + 1,
                    check="internal-link-anchor",
                    reason=f"Link target has no anchor '{anchor}'",
                    excerpt=target,
                )
            )

    return violations


def check_includes(lines, rel, include_dir):
    """Every included snippet has to exist."""
    violations = []

    for index, line in enumerate(lines):
        for match in INCLUDE_PATTERN.finditer(line):
            snippet = match.group(1)
            if os.path.exists(os.path.join(include_dir, snippet)):
                continue
            violations.append(
                Violation(
                    file=rel,
                    line=index + 1,
                    column=match.start() + 1,
                    check="include-target",
                    reason=f"Included snippet does not exist: {snippet}",
                    excerpt=line.strip(),
                )
            )

    return violations


def check_placeholders(lines, rel, placeholders):
    """Every placeholder has to resolve against mkdocs.yml."""
    violations = []

    for index, line in enumerate(lines):
        for match in PLACEHOLDER_PATTERN.finditer(line):
            expression = match.group(1)
            name_match = PLACEHOLDER_NAME_PATTERN.match(expression)
            if not name_match:
                reason = f"Placeholder '{{{{{expression}}}}}' has no variable name"
            elif name_match.group(1) in placeholders or name_match.group(1) in MACROS_BUILTINS:
                continue
            else:
                reason = (
                    f"Unknown placeholder '{name_match.group(1)}', "
                    f"it is not declared below 'extra' in {MKDOCS_CONFIG_NAME}"
                )

            violations.append(
                Violation(
                    file=rel,
                    line=index + 1,
                    column=match.start() + 1,
                    check="placeholder-defined",
                    reason=reason,
                    excerpt=line.strip(),
                )
            )

    return violations


def check_list_indentation(lines, rel):
    """A nested list item is indented by exactly one step of four spaces.

    Only the step matters to the parser, and only up to seven spaces, but a step
    of four is the one that stays readable and survives another level below it.
    """
    violations = []
    in_code_fence = False
    previous_indent = None

    for index, line in enumerate(lines):
        if CODE_FENCE_PATTERN.match(line):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue

        if UNSPACED_MARKER_PATTERN.match(line):
            violations.append(
                Violation(
                    file=rel,
                    line=index + 1,
                    column=1,
                    check="list-item-marker",
                    reason="List marker without a space behind it, this is not a list item",
                    excerpt=line.strip(),
                )
            )
            continue

        match = LIST_ITEM_PATTERN.match(line)
        if not match:
            # A blank line keeps a list open, body text at the margin ends it.
            if line.strip() and indentation_of(line) == 0:
                previous_indent = None
            continue

        indent = len(match.group("indent"))

        if indent % LIST_INDENT_STEP:
            violations.append(
                Violation(
                    file=rel,
                    line=index + 1,
                    column=1,
                    check="list-item-indent",
                    reason=(
                        f"List item is indented by {indent} spaces, which is not a "
                        f"multiple of {LIST_INDENT_STEP}"
                    ),
                    excerpt=line.strip(),
                )
            )
        elif previous_indent is not None and indent > previous_indent + LIST_INDENT_STEP:
            violations.append(
                Violation(
                    file=rel,
                    line=index + 1,
                    column=1,
                    check="list-item-indent",
                    reason=(
                        f"List item is indented by {indent} spaces below an item at "
                        f"{previous_indent}, so it is read as text of that item"
                    ),
                    excerpt=line.strip(),
                )
            )

        previous_indent = indent

    return violations


def check_file_ending(lines, rel):
    """A file ends with exactly one newline behind its last line of text.

    read_lines() keeps the text behind the last newline as its final element, so
    a file that ends correctly has exactly one empty element there. No element
    means the last line carries text and no newline follows it, and more than one
    means the file ends in blank lines.
    """
    if not lines:
        return []

    trailing_blanks = 0
    for line in reversed(lines):
        if line.strip():
            break
        trailing_blanks += 1

    if trailing_blanks == 1:
        return []

    if trailing_blanks == 0:
        reason = "File does not end with a newline"
    else:
        reason = f"File ends with {trailing_blanks - 1} blank line(s) behind its last line"

    return [
        Violation(
            file=rel,
            line=len(lines),
            column=1,
            check="file-ending",
            reason=reason,
            excerpt=lines[-1].strip() or "(end of file)",
        )
    ]


def check_trailing_whitespace(lines, rel):
    """Trailing whitespace, wherever it sits.

    Two spaces at the end of a line of prose insert a line break. The rest
    changes nothing, which is exactly why it is reported: it is invisible in the
    page, it is invisible in review, and it turns up in every later diff. Code
    blocks and the frontmatter are checked as well, since a trailing space is
    copied along with the snippet it sits in.
    """
    violations = []

    for index, line in enumerate(lines):
        if line == line.rstrip():
            continue
        stripped = line.strip()
        breaks_line = (
            stripped
            and len(line) - len(line.rstrip()) >= TRAILING_BREAK_SPACES
            and index + 1 < len(lines)
            and lines[index + 1].strip()
        )
        violations.append(
            Violation(
                file=rel,
                line=index + 1,
                column=len(line.rstrip()) + 1,
                check="trailing-spaces",
                reason=(
                    "Trailing spaces insert a line break into the paragraph"
                    if breaks_line
                    else "Trailing whitespace"
                ),
                excerpt=stripped or "(whitespace only)",
            )
        )

    return violations


def check_markdown_traps(lines, rel):
    """Constructs that render as something other than what they look like.

    Each of these is silent: the page builds, and the text simply comes out as a
    paragraph, or as literal characters, instead of the list, link, or table that
    was written.
    """
    violations = []
    in_code_fence = False
    _, body_start = frontmatter_bounds(lines)

    for index, line in enumerate(lines):
        if CODE_FENCE_PATTERN.match(line):
            if not in_code_fence and index > 0:
                above = lines[index - 1]
                if above.strip() and not LIST_PREV_EXEMPT_PATTERN.match(above.strip()) \
                        and not LIST_ITEM_PATTERN.match(above):
                    violations.append(
                        Violation(
                            file=rel,
                            line=index + 1,
                            column=1,
                            check="fence-blank-line",
                            reason=(
                                "Code block opens directly below a paragraph, which nests "
                                "it inside that paragraph. A blank line is needed"
                            ),
                            excerpt=line.strip(),
                        )
                    )
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue

        if index < body_start:
            continue

        stripped = line.strip()

        if UNSPACED_HEADING_PATTERN.match(line):
            violations.append(
                Violation(
                    file=rel,
                    line=index + 1,
                    column=1,
                    check="heading-marker",
                    reason="Heading without a space behind its hashes",
                    excerpt=stripped,
                )
            )

        if SPACED_LINK_PATTERN.search(CODE_SPAN_PATTERN.sub("", line)):
            violations.append(
                Violation(
                    file=rel,
                    line=index + 1,
                    column=1,
                    check="link-spacing",
                    reason="Space between the text and the target of a link, so it is not a link",
                    excerpt=stripped,
                )
            )

        if LIST_ITEM_PATTERN.match(line) and index > 0:
            previous = lines[index - 1]
            if (
                previous.strip()
                and not LIST_ITEM_PATTERN.match(previous)
                and not LIST_PREV_EXEMPT_PATTERN.match(previous.strip())
                and indentation_of(previous) <= indentation_of(line)
            ):
                violations.append(
                    Violation(
                        file=rel,
                        line=index + 1,
                        column=1,
                        check="list-blank-line",
                        reason=(
                            "List opens directly below a paragraph, so its items are "
                            "read as more of that paragraph. A blank line is needed"
                        ),
                        excerpt=stripped,
                    )
                )

        for match in ANGLE_TOKEN_PATTERN.finditer(CODE_SPAN_PATTERN.sub("", line)):
            if match.group(2).lower() in HTML_TAG_NAMES:
                continue
            violations.append(
                Violation(
                    file=rel,
                    line=index + 1,
                    column=1,
                    check="raw-angle-token",
                    reason=(
                        f"'{match.group(0)}' outside a code span is passed through as "
                        f"html and disappears in the browser, wrap it in backticks"
                    ),
                    excerpt=stripped,
                )
            )

        if HORIZONTAL_RULE_PATTERN.match(line):
            violations.append(
                Violation(
                    file=rel,
                    line=index + 1,
                    column=1,
                    check="horizontal-rule",
                    reason=(
                        "Horizontal rule, the documentation separates sections with a "
                        "heading instead"
                    ),
                    excerpt=stripped,
                )
            )

        if EMPTY_LIST_ITEM_PATTERN.match(line):
            violations.append(
                Violation(
                    file=rel,
                    line=index + 1,
                    column=1,
                    check="empty-list-item",
                    reason="List item with no content, this renders as an empty bullet",
                    excerpt=stripped or repr(line),
                )
            )

        if index > body_start and SETEXT_PATTERN.match(line) and lines[index - 1].strip():
            violations.append(
                Violation(
                    file=rel,
                    line=index + 1,
                    column=1,
                    check="setext-heading",
                    reason=(
                        "A line of '=' or '-' under text turns that text into a heading, "
                        "leave a blank line above it"
                    ),
                    excerpt=stripped,
                )
            )

        if BARE_URL_PATTERN.search(CODE_SPAN_PATTERN.sub("", line)):
            violations.append(
                Violation(
                    file=rel,
                    line=index + 1,
                    column=1,
                    check="bare-url",
                    reason="Url outside a link is printed as text, write it as a markdown link",
                    excerpt=stripped,
                    severity=SEVERITY_WARNING,
                )
            )

        if TABLE_ROW_PATTERN.match(line) and index + 1 < len(lines):
            previous = lines[index - 1] if index else ""
            if not TABLE_ROW_PATTERN.match(previous) and not TABLE_SEPARATOR_PATTERN.match(
                lines[index + 1]
            ):
                violations.append(
                    Violation(
                        file=rel,
                        line=index + 1,
                        column=1,
                        check="table-separator",
                        reason="Table without a separator row below its header",
                        excerpt=stripped,
                    )
                )

    return violations


def check_code_blocks(lines, rel):
    """Code blocks need a language, and are expected to carry a title."""
    violations = []
    in_code_fence = False

    for index, line in enumerate(lines):
        match = CODE_FENCE_INFO_PATTERN.match(line)
        if not match:
            continue
        if in_code_fence:
            in_code_fence = False
            continue

        in_code_fence = True
        info = match.group(1).strip()
        first_token = info.split()[0] if info else ""
        # An attribute is not a language, as in '```title="..."'.
        language = "" if "=" in first_token else first_token

        if language in LANGUAGE_ALIASES:
            violations.append(
                Violation(
                    file=rel,
                    line=index + 1,
                    column=indentation_of(line) + 1,
                    check="code-block-language-alias",
                    reason=(
                        f"Code block language '{language}' is an alias, "
                        f"write '{LANGUAGE_ALIASES[language]}'"
                    ),
                    excerpt=line.strip(),
                )
            )

        if not language:
            violations.append(
                Violation(
                    file=rel,
                    line=index + 1,
                    column=indentation_of(line) + 1,
                    check="code-block-language",
                    reason="Code block has no language (```bash, ```yaml, ```plain, ...)",
                    excerpt=line.strip(),
                )
            )

        if "title=" not in info and language not in UNTITLED_FENCE_LANGUAGES:
            violations.append(
                Violation(
                    file=rel,
                    line=index + 1,
                    column=indentation_of(line) + 1,
                    check="code-block-title",
                    reason='Code block has no title attribute (```bash title="...")',
                    excerpt=line.strip(),
                    severity=SEVERITY_WARNING,
                )
            )

    return violations


def scan_file(file_path, placeholders, docs_root, include_dir, anchor_cache):
    lines = read_lines(file_path)
    rel = relative_path(file_path)

    violations = (
        check_block_indentation(lines, rel)
        + check_placeholders(lines, rel, placeholders)
        + check_code_blocks(lines, rel)
        + check_list_indentation(lines, rel)
        + check_markdown_traps(lines, rel)
        + check_trailing_whitespace(lines, rel)
        + check_file_ending(lines, rel)
        + check_links(lines, rel, file_path, docs_root, anchor_cache)
        + check_includes(lines, rel, include_dir)
    )

    # Snippets are fragments injected into a page, so they carry neither
    # frontmatter nor an introduction of their own.
    if not is_snippet(file_path, include_dir):
        violations += check_frontmatter(lines, rel, file_path, docs_root) + check_headings(lines, rel)

    return violations


def report_generated(generated):
    print(f"Skipped {len(generated)} generated file(s), fix those at their source:")
    for file in generated:
        print(f"  • {relative_path(file)}")


def main():
    parser = argparse.ArgumentParser(
        description="Check mkdocs specific syntax in the documentation markdown files."
    )
    parser.add_argument(
        "--config",
        help=f"path to {MKDOCS_CONFIG_NAME} (default: the one in the repository root)",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help=(
            "directories or files to scan, recursively "
            f"(default: {', '.join(DEFAULT_TARGET_DIRS)} in the repository root)"
        ),
    )
    args = parser.parse_args()

    repo_root = repository_root()

    config_path = args.config or os.path.join(repo_root, MKDOCS_CONFIG_NAME)
    docs_root = os.path.join(repo_root, "docs")
    include_dir = load_include_dir(config_path, repo_root)
    placeholders = load_placeholder_names(config_path)
    if placeholders is None:
        print(f"Could not read {config_path}, placeholders cannot be verified.", file=sys.stderr)
        sys.exit(1)

    files = collect_files(
        args.paths,
        on_missing=lambda target: print(f"Skipping missing path: {target}", file=sys.stderr),
    )
    files = drop_generated(files, report=report_generated)

    anchor_cache = {}
    violations = [
        v
        for file in files
        for v in scan_file(file, placeholders, docs_root, include_dir, anchor_cache)
    ]

    sys.exit(
        report_violations(
            violations,
            "mkdocs syntax check",
            files,
            "No mkdocs syntax errors found in {files} file(s) "
            f"({len(placeholders)} placeholder(s) declared, "
            "{warnings} warning(s)).",
        )
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as error:  # noqa: BLE001
        print("Failed to run mkdocs syntax check.", file=sys.stderr)
        print(error, file=sys.stderr)
        sys.exit(1)
