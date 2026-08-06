#!/usr/bin/env python3
"""Check (and optionally fix) the casing of the "simplyblock" brand name in Markdown files.

The brand is written in lowercase ("simplyblock"), except in a few contexts where
regular capitalization rules win (headings, sentence starts, link text, ...).

The brand keeps its capital as part of a product name ("Simplyblock Operator") and
in release references ("Simplyblock 25.10.2").

By default all Markdown files below "docs/" and "snippets/" are scanned. Generated
files are skipped, since they have to be corrected at their source.

Usage:
    python3 scripts/check-simplyblock-spelling.py [--fix] [PATH ...]
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass

DEFAULT_TARGET_DIRS = ["docs", "snippets"]

SCANNED_EXTENSIONS = {".md"}

BRAND_PATTERN = re.compile(r"\bsimplyblock\b", re.IGNORECASE)

HEADING_PATTERN = re.compile(r"^\s*#{1,6}\s+")
CODE_FENCE_PATTERN = re.compile(r"^\s*```")
# Regions that are not prose: inline code spans (a run of backticks closed by a
# run of the same length) and mkdocs-macros template expressions. The latter cover
# both placeholders declared under "extra" in mkdocs.yml ({{ cliname }}) and
# statements such as snippet includes ({% include 'file.md' %}).
CODE_SPAN_PATTERN = re.compile(r"(`+)(?:.+?)\1")
TEMPLATE_PATTERN = re.compile(r"\{\{.*?\}\}|\{%.*?%\}")

# `[^\w\s]|_` is the Python equivalent of `[^\p{L}\p{N}\s]`, since `\w` also covers
# the underscore, which is neither a letter nor a number.
PARAGRAPH_START_PATTERN = re.compile(
    r"^\s*(?:>+\s*)?(?:[-*+]\s+|\d+\.\s+)?(?:(?:[^\w\s]|_)+\s*)*(?:[*_`(\[]+\s*)*$"
)

METADATA_LINE_PATTERN = re.compile(r"^\s*(title|description)\s*:")
IMAGE_LINE_PATTERN = re.compile(r"^\s*!\[.*\]\(.*\)\s*$")
CAPTION_LINE_PATTERN = re.compile(r"^\s*(Image|Figure|Table)\s+\d+\s*:")

# Material grid cards: an HTML wrapper around Markdown card definitions.
GRID_CARDS_OPEN_PATTERN = re.compile(r"<(?:div|ul)[^>]*class=\"[^\"]*\bgrid\b", re.IGNORECASE)
GRID_CARDS_CLOSE_PATTERN = re.compile(r"</(?:div|ul)>", re.IGNORECASE)
# A card title is the top-level list item of a grid card, for example:
# "-   :material-cog-refresh:{ .lg .middle } **Operate Simplyblock**".
CARD_TITLE_PATTERN = re.compile(r"^ {0,3}[-*+]\s+")
CARD_DIVIDER = "---"

# Admonition ("!!! note \"Title\"") and content tab ("=== \"Title\"") titles.
ADMONITION_TITLE_PATTERN = re.compile(r"^\s*(?:!!!|\?\?\?\+?)(?:\s|$)")
TAB_TITLE_PATTERN = re.compile(r"^\s*===\+?\s")

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

# Block-level markers keep their paragraph-start exemption even on a card body
# continuation line, because they open a new block instead of wrapping a sentence.
BLOCK_MARKER_PATTERN = re.compile(r"^\s*(?:>+\s*|[-*+]\s+|\d+\.\s+)")

# Product names: here the brand is part of a proper name and keeps its capital,
# as in "the Simplyblock Operator". Generic nouns ("simplyblock cluster",
# "simplyblock control plane", "simplyblock backend") are deliberately absent.
PRODUCT_NAME_PATTERN = re.compile(
    r"\s+(?:(?:Kubernetes\s+)?Operator|CSI|CLI|Management\s+API)\b"
)

# Release references name a product version, as in "Simplyblock 25.10.2".
VERSION_REFERENCE_PATTERN = re.compile(r"\s+v?\d+(?:\.\d+)*\b")

# Terms that share their casing with the brand: "Simplyblock Documentation" and
# "simplyblock documentation" are both correct, a mix of the two is not.
CASE_MATCHED_TERMS = {"documentation"}

# Renamed products. The old term is reported but never rewritten automatically,
# because the surrounding sentence usually has to be reworded as well.
DEPRECATED_TERMS = {"manager": ("Simplyblock Manager", "Simplyblock Operator")}

FOLLOWING_WORD_PATTERN = re.compile(r"\s+([A-Za-z][\w-]*)")

# Generated files are corrected at their source, so they are not checked here.
GENERATED_MARKER_PATTERN = re.compile(
    r"this file is generated|do not edit (?:it )?by hand|code generated .*do not edit",
    re.IGNORECASE,
)
GENERATED_MARKER_LINES = 15

# Characters after which a new text block begins. Besides sentence punctuation
# this covers the pipe, which starts a new cell in a markdown table.
SENTENCE_END_CHARS = {".", ":", "?", "!", ";", "+", "|", "。", "：", "？", "！", "；", "؟"}
IGNORABLE_FORMATTING_CHARS = {"*", "_", "`", "(", "[", '"', "'"}

CASING_REASON = "Non-standard casing (only 'simplyblock' or contextual 'Simplyblock' allowed)"
MIXED_CASE_REASON = (
    "Brand and term must share the same casing "
    "('Simplyblock Documentation' or 'simplyblock documentation', never a mix)"
)
CONTEXT_REASON = (
    "Expected lowercase 'simplyblock' here (exception rules: heading, card or admonition "
    "title, paragraph start, sentence start after '.', ':', '?', '!', or ';')"
)


@dataclass
class Violation:
    file: str
    line: int
    column: int
    found: str
    reason: str
    excerpt: str


@dataclass
class CandidatePattern:
    punct: str
    file: str
    line: int
    excerpt: str


@dataclass
class FileFix:
    line: int
    column: int
    length: int
    replacement: str


@dataclass
class ScanResult:
    violations: list
    candidates: list
    fixes: list


def walk(directory):
    files = []
    for root, dirnames, filenames in os.walk(directory):
        dirnames.sort()
        for name in sorted(filenames):
            if os.path.splitext(name)[1].lower() in SCANNED_EXTENSIONS:
                files.append(os.path.join(root, name))
    return files


def is_heading_line(line):
    return bool(HEADING_PATTERN.match(line))


def indentation_of(line):
    return len(line) - len(line.lstrip())


def non_prose_ranges(line):
    """Return the (start, end) ranges of all non-prose regions in a line."""
    ranges = [match.span() for match in CODE_SPAN_PATTERN.finditer(line)]
    ranges.extend(match.span() for match in TEMPLATE_PATTERN.finditer(line))
    return ranges


def is_inside_range(ranges, index):
    return any(start <= index < end for start, end in ranges)


def mask_ranges(line, ranges):
    """Blank out non-prose regions so they do not affect the prefix analysis."""
    if not ranges:
        return line
    chars = list(line)
    for start, end in ranges:
        for index in range(start, min(end, len(chars))):
            chars[index] = " "
    return "".join(chars)


def is_likely_paragraph_start(prefix):
    return bool(PARAGRAPH_START_PATTERN.match(prefix))


def previous_non_whitespace_char(prefix):
    for ch in reversed(prefix):
        if not ch.isspace() and ch not in IGNORABLE_FORMATTING_CHARS:
            return ch
    return None


def get_line_excerpt(line, col):
    start = max(0, col - 30)
    end = min(len(line), col + 45)
    return line[start:end].strip()


def is_inside_markdown_link_text(line, index):
    left = line.rfind("[", 0, index)
    if left == -1:
        return False
    prior_close = line.rfind("]", 0, index)
    if prior_close > left:
        return False
    right = line.find("]", index)
    if right == -1:
        return False
    return line[right + 1:].lstrip().startswith("(")


def read_lines(file_path):
    with open(file_path, "r", encoding="utf-8") as handle:
        content = handle.read()
    if content.startswith("﻿"):
        content = content[1:]
    return re.split(r"\r?\n", content)


def is_generated(file_path):
    """Detect the "do not edit by hand" marker that generators write out."""
    head = read_lines(file_path)[:GENERATED_MARKER_LINES]
    return any(GENERATED_MARKER_PATTERN.search(line) for line in head)


def scan_file(file_path):
    lines = read_lines(file_path)
    rel = os.path.relpath(file_path, os.getcwd())
    if rel.startswith(".."):
        rel = file_path

    violations = []
    candidates = []
    fixes = []

    def check_line(line, index, is_title_line, on_continuation=False, previous_tail=None):
        """Report every non-compliant brand occurrence on a single line."""
        ranges = non_prose_ranges(line)
        masked = mask_ranges(line, ranges)
        for match in BRAND_PATTERN.finditer(line):
            found = match.group(0)
            col = match.start()
            prefix = masked[:col]
            following = line[match.end():]

            # Code spans are literals (commands, identifiers, values) and template
            # expressions are resolved by mkdocs, so neither is subject to the
            # brand style rules.
            if is_inside_range(ranges, col):
                continue

            word_match = FOLLOWING_WORD_PATTERN.match(following)
            next_word = word_match.group(1) if word_match else ""
            term = next_word.lower()

            if found in ("simplyblock", "Simplyblock") and term in DEPRECATED_TERMS:
                # Link text may legitimately name the old product, for example
                # when linking to a repository that still carries that name.
                if not is_inside_markdown_link_text(line, col):
                    old_term, new_term = DEPRECATED_TERMS[term]
                    violations.append(
                        Violation(
                            file=rel,
                            line=index + 1,
                            column=col + 1,
                            found=f"{found} {next_word}",
                            reason=f"Outdated term: '{old_term}' is now called '{new_term}'",
                            excerpt=get_line_excerpt(line, col),
                        )
                    )
                continue

            if found in ("simplyblock", "Simplyblock") and term in CASE_MATCHED_TERMS:
                if next_word[:1].isupper() == found[:1].isupper():
                    continue
                violations.append(
                    Violation(
                        file=rel,
                        line=index + 1,
                        column=col + 1,
                        found=f"{found} {next_word}",
                        reason=MIXED_CASE_REASON,
                        excerpt=get_line_excerpt(line, col),
                    )
                )
                if found[:1].isupper():
                    # Lowercasing the brand yields the valid all-lowercase form.
                    fixes.append(
                        FileFix(
                            line=index + 1,
                            column=col + 1,
                            length=len(found),
                            replacement="simplyblock",
                        )
                    )
                continue

            if found == "simplyblock":
                continue

            if found != "Simplyblock":
                violations.append(
                    Violation(
                        file=rel,
                        line=index + 1,
                        column=col + 1,
                        found=found,
                        reason=CASING_REASON,
                        excerpt=get_line_excerpt(line, col),
                    )
                )
                fixes.append(
                    FileFix(
                        line=index + 1,
                        column=col + 1,
                        length=len(found),
                        replacement="simplyblock",
                    )
                )
                continue

            # Part of a product name or a release reference, where the brand
            # keeps its capital.
            if PRODUCT_NAME_PATTERN.match(following) or VERSION_REFERENCE_PATTERN.match(following):
                continue

            if is_title_line:
                continue

            if is_inside_markdown_link_text(line, col):
                continue

            if is_likely_paragraph_start(prefix):
                # On a wrapped body line of an indented block, indentation alone
                # does not start a sentence; only a real block marker (list,
                # quote) does.
                if not on_continuation or BLOCK_MARKER_PATTERN.match(prefix):
                    continue

            prev_char = previous_non_whitespace_char(prefix)
            if prev_char is None and on_continuation:
                # The text continues from the line above, so that is where the
                # preceding sentence ends.
                prev_char = previous_tail
            if prev_char in SENTENCE_END_CHARS:
                continue

            # Candidate contexts to review/approve later.
            if prev_char in (")", "]"):
                candidates.append(
                    CandidatePattern(
                        punct=prev_char,
                        file=rel,
                        line=index + 1,
                        excerpt=get_line_excerpt(line, col),
                    )
                )

            violations.append(
                Violation(
                    file=rel,
                    line=index + 1,
                    column=col + 1,
                    found=found,
                    reason=CONTEXT_REASON,
                    excerpt=get_line_excerpt(line, col),
                )
            )
            fixes.append(
                FileFix(
                    line=index + 1,
                    column=col + 1,
                    length=len(found),
                    replacement="simplyblock",
                )
            )

    in_frontmatter = False
    frontmatter_fence_count = 0
    in_code_fence = False
    html_skip_tag = None
    html_skip_depth = 0
    in_grid_cards = False
    card_paragraph_start = True
    # Indentation levels of the admonition / content tab blocks currently open.
    body_indents = []
    body_paragraph_start = True

    for i, line in enumerate(lines):
        trimmed = line.strip()
        is_card_title = False
        on_continuation = False
        previous_tail = previous_non_whitespace_char(lines[i - 1]) if i > 0 else None

        if i == 0 and trimmed == "---":
            in_frontmatter = True
            frontmatter_fence_count = 1
            continue

        # Fallback: allow leading blank lines before frontmatter fence.
        if i <= 3 and frontmatter_fence_count == 0 and trimmed == "---":
            in_frontmatter = True
            frontmatter_fence_count = 1
            continue

        if in_frontmatter:
            if trimmed == "---":
                frontmatter_fence_count += 1
                if frontmatter_fence_count >= 2:
                    in_frontmatter = False
            continue

        if CODE_FENCE_PATTERN.match(line):
            in_code_fence = not in_code_fence
            # An opening fence may carry a title attribute
            # (```bash title="Deploy simplyblock"), which follows regular title
            # capitalization just like a heading.
            check_line(line, i, is_title_line=True)
            continue
        if in_code_fence:
            continue

        # Material grid cards: the wrapper is HTML, but the cards themselves are
        # Markdown, so they have to be handled before raw HTML lines are skipped.
        if GRID_CARDS_OPEN_PATTERN.search(line):
            in_grid_cards = True
            card_paragraph_start = True
            continue
        if in_grid_cards:
            if GRID_CARDS_CLOSE_PATTERN.search(line):
                in_grid_cards = False
                continue
            # Blank lines and the "---" divider end the current card paragraph.
            if not trimmed or trimmed == CARD_DIVIDER:
                card_paragraph_start = True
                continue
            if CARD_TITLE_PATTERN.match(line):
                # Card titles are title-cased like headings, and the body below
                # them starts a fresh paragraph.
                is_card_title = True
                card_paragraph_start = True
            else:
                # Everything else is card body prose. Only the first line of a
                # paragraph starts a sentence; wrapped lines are continuations.
                on_continuation = not card_paragraph_start
                card_paragraph_start = False
        else:
            # Admonition and content tab bodies are indented below their title and
            # behave like card bodies: only the first line of a paragraph starts a
            # sentence, wrapped lines continue the line above.
            block_title = ADMONITION_TITLE_PATTERN.match(line) or TAB_TITLE_PATTERN.match(line)
            if block_title:
                body_indents.append(indentation_of(line))
                body_paragraph_start = True
            elif body_indents:
                if not trimmed:
                    body_paragraph_start = True
                else:
                    indent = indentation_of(line)
                    while body_indents and indent <= body_indents[-1]:
                        body_indents.pop()
                    if body_indents:
                        on_continuation = not body_paragraph_start
                        body_paragraph_start = False

        # Raw HTML blocks (e.g., <table>, <script>, figcaption contexts) are exempt,
        # unless they carry the md_in_html "markdown" attribute. With that attribute
        # set, mkdocs renders the block content as Markdown, so it is checked like
        # any other prose. Inline HTML in a prose line does not open a block.
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

        # Safety: never enforce brand casing in metadata-ish lines.
        if METADATA_LINE_PATTERN.match(trimmed):
            continue

        # Image markdown lines and plain caption lines are exempt.
        if IMAGE_LINE_PATTERN.match(trimmed):
            continue
        if CAPTION_LINE_PATTERN.match(trimmed):
            continue

        # Headings, card titles, admonition titles, and content tab titles all
        # follow regular title capitalization.
        is_title_line = (
            is_heading_line(line)
            or is_card_title
            or bool(ADMONITION_TITLE_PATTERN.match(line))
            or bool(TAB_TITLE_PATTERN.match(line))
        )

        check_line(line, i, is_title_line, on_continuation, previous_tail)

    return ScanResult(violations=violations, candidates=candidates, fixes=fixes)


def apply_fixes_to_file(file_path, fixes):
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

    # read_lines() keeps a trailing empty element for a final newline, so joining
    # restores the file exactly as it was, including whether it ended with one.
    with open(file_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    return applied


def main():
    parser = argparse.ArgumentParser(
        description="Check the casing of the 'simplyblock' brand name in Markdown files."
    )
    parser.add_argument(
        "-f",
        "--fix",
        action="store_true",
        help="rewrite non-compliant occurrences to lowercase 'simplyblock'",
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

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # The defaults are anchored to the repository root, so the check can be run
    # from anywhere; explicitly passed paths stay relative to the current directory.
    if args.paths:
        targets = [os.path.abspath(path) for path in args.paths]
    else:
        targets = [os.path.join(repo_root, name) for name in DEFAULT_TARGET_DIRS]


    files = []
    for target in targets:
        if os.path.isdir(target):
            files.extend(walk(target))
        elif os.path.isfile(target):
            files.append(target)
        else:
            print(f"Skipping missing path: {target}", file=sys.stderr)

    generated = [file for file in files if is_generated(file)]
    if generated:
        files = [file for file in files if file not in set(generated)]
        print(f"Skipped {len(generated)} generated file(s), fix those at their source:")
        for file in generated:
            print(f"  • {os.path.relpath(file, os.getcwd())}")

    scans = [scan_file(file) for file in files]
    violations = [v for scan in scans for v in scan.violations]
    candidates = [c for scan in scans for c in scan.candidates]

    if args.fix and violations:
        files_changed = 0
        replacements_applied = 0

        for file, scan in zip(files, scans):
            applied = apply_fixes_to_file(file, scan.fixes)
            if applied > 0:
                files_changed += 1
                replacements_applied += applied

        print(
            f"Auto-fix mode: updated {replacements_applied} occurrence(s) "
            f"across {files_changed} file(s)."
        )

        scans = [scan_file(file) for file in files]
        violations = [v for scan in scans for v in scan.violations]
        candidates = [c for scan in scans for c in scan.candidates]

    if not violations:
        print(f"No simplyblock spelling/casing violations found in {len(files)} file(s).")
    else:
        print(
            "simplyblock spelling/casing check failed. Found non-compliant occurrences:",
            file=sys.stderr,
        )
        for v in violations:
            print(
                f"- {v.file}:{v.line}:{v.column} | {v.found} | {v.reason}\n  {v.excerpt}",
                file=sys.stderr,
            )

    if candidates:
        print("")
        print("Potential additional exception patterns for approval:")
        grouped = {}
        for c in candidates:
            grouped.setdefault(f"'{c.punct}' before Simplyblock", []).append(c)
        for key, group in grouped.items():
            print(f"- {key}: {len(group)} occurrence(s)")
            for sample in group[:3]:
                print(f"  • {sample.file}:{sample.line} -> {sample.excerpt}")

    if violations:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as error:  # noqa: BLE001
        print("Failed to run simplyblock spelling/casing check.", file=sys.stderr)
        print(error, file=sys.stderr)
        sys.exit(1)
