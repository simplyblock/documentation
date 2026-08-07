"""Shared helpers for the documentation quality gates.

The gates all walk the same set of Markdown files and all have to tell prose
apart from the parts of a page that are not prose: code blocks, inline code,
mkdocs-macros expressions, link targets and raw HTML.

Two levels are offered:

* The primitives (walk, read_lines, is_generated, non_prose_ranges, ...), for a
  gate that runs its own line analysis.
* iter_prose_lines(), for a gate that only wants the prose of a page. It yields
  one entry per line that carries prose, with every non-prose region blanked out,
  so a match position still refers to the original line.
"""

import os
import re
import sys
from dataclasses import dataclass

DEFAULT_TARGET_DIRS = ["docs", "snippets"]

SCANNED_EXTENSIONS = {".md"}

CODE_FENCE_PATTERN = re.compile(r"^\s*```")
# The info string of an opening fence, e.g. 'bash title="Create a cluster"'.
CODE_FENCE_TITLE_PATTERN = re.compile(r"title\s*=\s*\"([^\"]*)\"")

# Regions that are not prose: inline code spans (a run of backticks closed by a
# run of the same length) and mkdocs-macros template expressions. The latter cover
# both placeholders declared under "extra" in mkdocs.yml ({{ cliname }}) and
# statements such as snippet includes ({% include 'file.md' %}).
CODE_SPAN_PATTERN = re.compile(r"(`+)(?:.+?)\1")
TEMPLATE_PATTERN = re.compile(r"\{\{.*?\}\}|\{%.*?%\}")

# Regions that carry no prose either, but that only the higher level checks mask:
# link and image targets, reference definitions, bare urls, attribute lists
# ({:target="_blank"}, {#anchor}) and inline html tags.
LINK_TARGET_PATTERN = re.compile(r"(?<=\])\([^)]*\)")
REFERENCE_TARGET_PATTERN = re.compile(r"^(\s*\[[^\]]+\]:).*$")
URL_PATTERN = re.compile(r"<?\b(?:https?|ftp)://\S+>?")
ATTRIBUTE_LIST_PATTERN = re.compile(r"\{[^{}]*\}")
HTML_TAG_PATTERN = re.compile(r"</?[a-zA-Z][^<>]*>")

# The comment of a code block line. A comment is written by the author of the
# page, the code around it is not. The space behind the marker keeps a shebang
# ("#!/bin/bash"), a url and a json pointer ("#/definitions") out. Only "#" and
# "//" are markers: ";" and "--" open a comment in some languages, but separate
# a command from its arguments in the shell.
CODE_COMMENT_PATTERN = re.compile(r"(?:^|\s)(?:#|//)\s")

# Raw HTML blocks start with a tag on their own line. Their content is only
# Markdown if the block carries the md_in_html "markdown" attribute.
HTML_BLOCK_OPEN_PATTERN = re.compile(r"^\s*<([a-zA-Z][\w:-]*)((?:\"[^\"]*\"|'[^']*'|[^>\"'])*)>")
MD_IN_HTML_ATTR_PATTERN = re.compile(
    r"(?:^|\s)markdown(?:\s*=\s*(?:\"[^\"]*\"|'[^']*'|\S+))?(?=\s|/|$)"
)
VOID_HTML_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

# Frontmatter fields that hold prose. The remaining fields are configuration
# (weight, redirects, ...) and are not written for a reader.
FRONTMATTER_FENCE = "---"
FRONTMATTER_PROSE_FIELDS = ("title", "description")
FRONTMATTER_FIELD_PATTERN = re.compile(r"^([A-Za-z_][\w-]*)\s*:\s*")

# Generated files are corrected at their source, so they are not checked.
GENERATED_MARKER_PATTERN = re.compile(
    r"this file is generated|do not edit (?:it )?by hand|code generated .*do not edit",
    re.IGNORECASE,
)
GENERATED_MARKER_LINES = 15

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"

# Every reported line opens with its severity, so that a finding stands out while
# the gates scroll past, and so that quality-gate.sh can collect the errors of all
# gates into one list at the end of a run.
ERROR_PREFIX = "ERROR  "
WARNING_PREFIX = "WARN   "


CONTEXT_PROSE = "prose"
CONTEXT_CODE = "code"


@dataclass
class ProseLine:
    """A single line of page text.

    "text" is the line as written, "masked" is the same line with every region
    that carries no text replaced by spaces. Both have the same length, so a
    column found in "masked" points at the same character in "text".

    "context" is CONTEXT_PROSE for the prose of a page, and CONTEXT_CODE for the
    body of a code block, which a check only sees when it asks for it.
    """

    number: int
    text: str
    masked: str
    context: str = CONTEXT_PROSE


@dataclass
class Violation:
    file: str
    line: int
    column: int
    check: str
    reason: str
    excerpt: str
    severity: str = SEVERITY_ERROR


@dataclass
class FileFix:
    """A replacement of "length" characters at a 1-based line and column."""

    line: int
    column: int
    length: int
    replacement: str


def repository_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def walk(directory):
    files = []
    for root, dirnames, filenames in os.walk(directory):
        dirnames.sort()
        for name in sorted(filenames):
            if os.path.splitext(name)[1].lower() in SCANNED_EXTENSIONS:
                files.append(os.path.join(root, name))
    return files


def read_lines(file_path):
    with open(file_path, "r", encoding="utf-8") as handle:
        content = handle.read()
    if content.startswith("﻿"):
        content = content[1:]
    return re.split(r"\r?\n", content)


def write_lines(file_path, lines):
    # read_lines() keeps a trailing empty element for a final newline, so joining
    # restores the file exactly as it was, including whether it ended with one.
    with open(file_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def is_generated(file_path):
    """Detect the "do not edit by hand" marker that generators write out."""
    head = read_lines(file_path)[:GENERATED_MARKER_LINES]
    return any(GENERATED_MARKER_PATTERN.search(line) for line in head)


def indentation_of(line):
    return len(line) - len(line.lstrip())


def get_line_excerpt(line, col):
    start = max(0, col - 30)
    end = min(len(line), col + 45)
    return line[start:end].strip()


def collect_files(paths, default_dirs=DEFAULT_TARGET_DIRS, on_missing=None):
    """Resolve the paths to scan into a sorted list of Markdown files.

    The defaults are anchored to the repository root, so a check can be run from
    anywhere; explicitly passed paths stay relative to the current directory.
    """
    if paths:
        targets = [os.path.abspath(path) for path in paths]
    else:
        targets = [os.path.join(repository_root(), name) for name in default_dirs]

    files = []
    for target in targets:
        if os.path.isdir(target):
            files.extend(walk(target))
        elif os.path.isfile(target):
            files.append(target)
        elif on_missing is not None:
            on_missing(target)
    return files


def drop_generated(files, report=None):
    """Remove the generated files, reporting them through "report" if given."""
    generated = [file for file in files if is_generated(file)]
    if not generated:
        return files
    if report is not None:
        report(generated)
    skipped = set(generated)
    return [file for file in files if file not in skipped]


def relative_path(file_path):
    rel = os.path.relpath(file_path, os.getcwd())
    return file_path if rel.startswith("..") else rel


# Characters that join words into an identifier, a path, a package name or a
# host: "my-cluster", "docs/kubernetes", "nvme-cli", "docker.io".
IDENTIFIER_CHARS = set("-_./\\:@=+$~")


def is_part_of_identifier(line, start, end):
    """Tell whether the match at (start, end) is part of a longer token.

    A separator only joins when a word continues behind it: "docker.io" is a
    host, "on Kubernetes." is the end of a sentence, and "(NVMe-oF)" is a word in
    brackets.
    """
    if start > 0 and line[start - 1] in IDENTIFIER_CHARS:
        # Nothing before the separator means the token starts with it, as a path
        # ("/etc/nvme") or an option ("--nvme") does.
        if start < 2 or line[start - 2].isalnum() or line[start - 2] == "_":
            return True

    if end < len(line) and line[end] in IDENTIFIER_CHARS:
        following = line[end + 1] if end + 1 < len(line) else ""
        if following.isalnum() or following == "_":
            return True

    return False


def template_ranges(line):
    return [match.span() for match in TEMPLATE_PATTERN.finditer(line)]


def non_prose_ranges(line):
    """Return the (start, end) ranges of the inline code and template regions."""
    ranges = [match.span() for match in CODE_SPAN_PATTERN.finditer(line)]
    ranges.extend(match.span() for match in TEMPLATE_PATTERN.finditer(line))
    return ranges


def is_inside_range(ranges, index):
    return any(start <= index < end for start, end in ranges)


def mask_ranges(line, ranges):
    """Blank out the given regions, keeping the length of the line."""
    if not ranges:
        return line
    chars = list(line)
    for start, end in ranges:
        for index in range(start, min(end, len(chars))):
            chars[index] = " "
    return "".join(chars)


def mask_non_prose(line):
    """Blank out every region of a line that is not prose.

    Next to inline code and template expressions this covers link and image
    targets, bare urls, attribute lists and inline html tags. The link text
    itself is prose and stays, as does the alt text of an image.
    """
    ranges = non_prose_ranges(line)
    masked = mask_ranges(line, ranges)

    for pattern in (
        URL_PATTERN,
        LINK_TARGET_PATTERN,
        ATTRIBUTE_LIST_PATTERN,
        HTML_TAG_PATTERN,
    ):
        ranges.extend(match.span() for match in pattern.finditer(masked))
        masked = mask_ranges(line, ranges)

    reference = REFERENCE_TARGET_PATTERN.match(masked)
    if reference:
        ranges.append((len(reference.group(1)), len(line)))
        masked = mask_ranges(line, ranges)

    return masked


def frontmatter_value_span(line):
    """Return the (start, end) span of a frontmatter value, without its quotes."""
    match = FRONTMATTER_FIELD_PATTERN.match(line)
    if not match:
        return None
    start, end = match.end(), len(line.rstrip())
    if end - start >= 2 and line[start] in "\"'" and line[end - 1] == line[start]:
        start, end = start + 1, end - 1
    return start, end


def iter_prose_lines(lines, frontmatter_fields=FRONTMATTER_PROSE_FIELDS, include_code=False):
    """Yield a ProseLine for every line of a page that carries prose.

    Skipped are the code blocks, the raw HTML blocks without an md_in_html
    "markdown" attribute, and the frontmatter fields that are not prose. Of an
    opening code fence only its title attribute is prose, of a frontmatter field
    only its value.

    With "include_code" the body of a code block is yielded as well, marked as
    CONTEXT_CODE. A check that looks at it has to treat it more leniently: a code
    block holds commands, values and identifiers, not sentences.
    """
    in_frontmatter = False
    frontmatter_fence_count = 0
    in_code_fence = False
    html_skip_tag = None
    html_skip_depth = 0

    for index, line in enumerate(lines):
        trimmed = line.strip()

        # Leading blank lines before the frontmatter fence are tolerated.
        if frontmatter_fence_count == 0 and index <= 3 and trimmed == FRONTMATTER_FENCE:
            in_frontmatter = True
            frontmatter_fence_count = 1
            continue

        if in_frontmatter:
            if trimmed == FRONTMATTER_FENCE:
                frontmatter_fence_count += 1
                if frontmatter_fence_count >= 2:
                    in_frontmatter = False
                continue
            field = FRONTMATTER_FIELD_PATTERN.match(line)
            if not field or field.group(1) not in frontmatter_fields:
                continue
            start, end = frontmatter_value_span(line)
            masked = mask_ranges(line, [(0, start), (end, len(line))])
            yield ProseLine(number=index + 1, text=line, masked=mask_non_prose(masked))
            continue

        if CODE_FENCE_PATTERN.match(line):
            in_code_fence = not in_code_fence
            # An opening fence may carry a title attribute
            # (```bash title="Deploy a cluster"), which is prose.
            title = CODE_FENCE_TITLE_PATTERN.search(line) if in_code_fence else None
            if title:
                masked = mask_ranges(
                    line, [(0, title.start(1)), (title.end(1), len(line))]
                )
                yield ProseLine(number=index + 1, text=line, masked=masked)
            continue
        if in_code_fence:
            comment = CODE_COMMENT_PATTERN.search(line) if include_code else None
            if comment:
                # Commands, values and program output are literals. Only the
                # comment next to them is written as text.
                masked = mask_ranges(line, [(0, comment.end()), *template_ranges(line)])
                yield ProseLine(
                    number=index + 1, text=line, masked=masked, context=CONTEXT_CODE
                )
            continue

        # Raw HTML blocks are exempt, unless they carry the md_in_html "markdown"
        # attribute. With that attribute set, mkdocs renders the block content as
        # Markdown, so it is prose like any other. Inline HTML in a prose line
        # does not open a block.
        if html_skip_tag is None:
            open_match = HTML_BLOCK_OPEN_PATTERN.match(line)
            if open_match and not MD_IN_HTML_ATTR_PATTERN.search(open_match.group(2)):
                tag = open_match.group(1).lower()
                if tag in VOID_HTML_TAGS or open_match.group(2).rstrip().endswith("/"):
                    # Self-contained element, no block to skip over.
                    continue
                html_skip_tag = tag
                html_skip_depth = 0
        if html_skip_tag is not None:
            html_skip_depth += len(
                re.findall(rf"<{re.escape(html_skip_tag)}\b", line, re.IGNORECASE)
            )
            html_skip_depth -= len(
                re.findall(rf"</{re.escape(html_skip_tag)}\s*>", line, re.IGNORECASE)
            )
            if html_skip_depth <= 0:
                html_skip_tag = None
            continue

        if not trimmed:
            continue

        yield ProseLine(number=index + 1, text=line, masked=mask_non_prose(line))


def apply_fixes_to_file(file_path, fixes):
    """Apply the replacements to a file and return how many were written."""
    if not fixes:
        return 0

    lines = read_lines(file_path)

    grouped = {}
    for fix in fixes:
        grouped.setdefault(fix.line, []).append(fix)

    applied = 0
    for line_number, line_fixes in grouped.items():
        line_index = line_number - 1
        if line_index >= len(lines):
            continue
        updated = lines[line_index]
        for fix in sorted(line_fixes, key=lambda f: f.column, reverse=True):
            start = fix.column - 1
            end = start + fix.length
            updated = f"{updated[:start]}{fix.replacement}{updated[end:]}"
            applied += 1
        lines[line_index] = updated

    write_lines(file_path, lines)
    return applied


def report_violations(violations, check_name, files, success_message, group_warnings=True):
    """Print the report of a gate and return its exit code.

    Warnings are grouped per file by default: they are numerous and only their
    line numbers are needed to find them. A gate whose warnings are candidates to
    read rather than places to visit passes group_warnings=False, so that every
    one is printed with its reason and its excerpt.
    """
    errors = [v for v in violations if v.severity == SEVERITY_ERROR]
    warnings = [v for v in violations if v.severity == SEVERITY_WARNING]

    if errors:
        print(f"{check_name} failed with {len(errors)} error(s):", file=sys.stderr)
        for v in errors:
            # The "ERROR" token opens the line, so that a finding is obvious while
            # the gates scroll past and can be collected again afterwards.
            print(
                f"{ERROR_PREFIX} {v.file}:{v.line}:{v.column} | {v.check} | {v.reason}\n"
                f"{' ' * (len(ERROR_PREFIX) + 1)}{v.excerpt}",
                file=sys.stderr,
            )
        sys.stderr.flush()

    if warnings:
        print(f"\n{len(warnings)} warning(s), these do not fail the check yet:")
        if group_warnings:
            grouped = {}
            for v in warnings:
                grouped.setdefault((v.file, v.check), []).append(v.line)
            for (file, check), numbers in grouped.items():
                print(
                    f"{WARNING_PREFIX} {file} | {check} | "
                    f"line(s) {', '.join(str(n) for n in numbers)}"
                )
        else:
            for v in warnings:
                print(
                    f"{WARNING_PREFIX} {v.file}:{v.line}:{v.column} | {v.reason}\n"
                    f"{' ' * (len(WARNING_PREFIX) + 1)}{v.excerpt}"
                )
        sys.stdout.flush()

    if errors:
        return 1

    print(success_message.format(files=len(files), warnings=len(warnings)))
    return 0
