#!/usr/bin/env python3
"""Look for punctuation that the house style avoids.

Four habits are reported. For three of them the replacement depends on the
sentence, so they are **warnings**: candidates for a human to look at, never a
failed build. The fourth has exactly one right answer and is an **error** that
"--fix" resolves.

* A **missing Oxford comma**. The last item of a series is separated by a comma
  as well: "storage nodes, volumes, and snapshots".
* A **semicolon** joining two sentences. Two full stops are easier to read, and a
  subordinate clause is easier still.
* An **em dash** setting off a clause. A pair of parentheses or a comma carries
  the same aside without the interruption.
* A **list item** whose subject is not written as "- **Foo:** bar": separated by
  a dash instead of a colon, carrying its colon outside the bold, or emphasized
  in italic rather than bold.

Whether "A, B and C" is a list of three items or a sentence that happens to
contain a comma and an "and" is a question of grammar, not of spelling, and the
same holds for a semicolon between two clauses and a semicolon between two list
items. The rules below therefore look for the shape of the habit rather than for
its meaning, and are deliberately narrow, so that the few candidates reported are
worth reading.

By default all Markdown files below "docs/" and "snippets/" are scanned.
Generated files are skipped, since they have to be corrected at their source.

Usage:
    python3 scripts/check-punctuation.py [--fix] [PATH ...]

"--fix" rewrites the subject of a list item and nothing else. A semicolon, an em
dash, and a missing Oxford comma are left alone: each of them is rewritten by
choosing different words, which is a decision for the writer.
"""

import argparse
import re
import sys
from dataclasses import dataclass

from markdown_common import (
    CODE_FENCE_PATTERN,
    DEFAULT_TARGET_DIRS,
    SEVERITY_ERROR,
    SEVERITY_WARNING,
    FileFix,
    Violation,
    apply_fixes_to_file,
    collect_files,
    drop_generated,
    get_line_excerpt,
    iter_prose_lines,
    read_lines,
    relative_path,
    report_violations,
)

@dataclass
class Finding:
    """One reported spot. "replacement" is set when the rule can fix itself."""

    column: int
    check: str
    reason: str
    severity: str = SEVERITY_WARNING
    length: int = 0
    replacement: str = ""


# ---------------------------------------------------------------------------
# The Oxford comma
# ---------------------------------------------------------------------------

# The conjunctions that can end a series, and that the Oxford comma is placed
# in front of.
CONJUNCTIONS = r"and|or|nor"

# A list item runs up to the next punctuation that ends it. A dash is included,
# since it separates parts of a sentence rather than items of a list.
ITEM = r"[^,;:.!?()\[\]—–]{1,45}"
SERIES_PATTERN = re.compile(
    rf"(?P<first>{ITEM}),\s+(?P<second>{ITEM}?)\s+(?P<conjunction>{CONJUNCTIONS})\s+"
    rf"(?P<third>{ITEM}?)(?=[.,;:!?)\]—–]|$)",
    re.IGNORECASE,
)

# A serial comma that is already there: then the list is written correctly, and
# the conjunction that was matched belongs to one of its items.
SERIAL_COMMA_PATTERN = re.compile(rf",\s*(?:{CONJUNCTIONS})\b", re.IGNORECASE)

# Words that make a chunk a clause instead of a list item. A list item is a name,
# not a statement, so a finite verb rules it out.
FINITE_VERBS = {
    "is", "are", "was", "were", "be", "been", "being", "has", "have", "had",
    "can", "could", "will", "would", "shall", "should", "may", "might", "must",
    "do", "does", "did", "provides", "allows", "requires", "means", "ensures",
    "enables", "uses", "supports", "runs", "becomes", "remains", "offers",
    "includes", "contains",
}

# Words that open a clause, never a list item.
CLAUSE_OPENERS = {
    "it", "this", "these", "they", "there", "which", "that", "if", "when",
    "while", "because", "then", "so",
}

# Wordings whose comma introduces an explanation, not a list.
INTRODUCTION_PATTERN = re.compile(
    r"(?:for example|for instance|e\.g\.|i\.e\.|that is|such as|in addition|"
    r"however|therefore|hence|meaning|instead)\s*$",
    re.IGNORECASE,
)

# The items have to be short: the shorter and the more alike they are, the more
# certain it is that they are items at all.
MAX_ITEM_WORDS = 2

OXFORD_REASON = (
    "Possible missing Oxford comma before '{conjunction}' in "
    "'{candidate}' (add one if these are three list items)"
)


def words_of(chunk):
    return [word for word in re.split(r"\s+", chunk.strip()) if word]


def is_list_item(chunk):
    words = words_of(chunk)
    if not words or len(words) > MAX_ITEM_WORDS:
        return False
    return not any(word.strip("*_`\"'").lower() in FINITE_VERBS for word in words)


def opens_clause(chunk):
    words = words_of(chunk)
    return bool(words) and words[0].lower() in CLAUSE_OPENERS


def is_series(match):
    """Tell whether a match has the shape of a list that lost its last comma."""
    if SERIAL_COMMA_PATTERN.search(match.group(0)):
        return False

    first, second, third = match.group("first"), match.group("second"), match.group("third")
    # Of the text before the comma, only the last words are the first list item.
    # What sits in front of them opens the sentence and often carries its verb,
    # as in "the mode supports neither Kubernetes, Proxmox nor OpenStack".
    lead = words_of(first.split(",")[-1])
    if not is_list_item(" ".join(lead[-MAX_ITEM_WORDS:])):
        return False
    if not (is_list_item(second) and is_list_item(third)):
        return False

    # A comma right after the first word or two of a sentence introduces it
    # ("Therefore, ..."), it does not separate items.
    if match.start("first") == 0 and len(words_of(first)) <= 2:
        return False
    if INTRODUCTION_PATTERN.search(first):
        return False

    return not (opens_clause(second) or opens_clause(third))


def check_oxford_comma(prose):
    for match in SERIES_PATTERN.finditer(prose.masked):
        if not is_series(match):
            continue
        yield Finding(
            column=match.start(),
            check="oxford-comma",
            reason=OXFORD_REASON.format(
                conjunction=match.group("conjunction").lower(),
                candidate=match.group(0).strip(),
            ),
        )


# ---------------------------------------------------------------------------
# The semicolon and the em dash
# ---------------------------------------------------------------------------

# An html entity ends in a semicolon that is not punctuation.
ENTITY_PATTERN = re.compile(r"&(?:[A-Za-z][A-Za-z0-9]*|#\d+|#x[0-9A-Fa-f]+);")

SEMICOLON_REASON = (
    "Semicolon between clauses, prefer two sentences or a subordinate clause"
)
EM_DASH_REASON = (
    "Em dash setting off a clause, prefer parentheses or a comma"
)

# "--" between words is a typed em dash and reads the same way. A "--" that opens
# a command line option is code, and the code spans are masked out already.
DOUBLE_HYPHEN_PATTERN = re.compile(r"(?<=\s)--(?=\s)")
DOUBLE_HYPHEN_REASON = (
    "Double hyphen used as a dash, prefer parentheses, a comma, or two sentences"
)

# An item of a list starts as the sentence above it left off: upper case after a
# full stop, a colon, or a heading, lower case when the sentence is still open.
LIST_BODY_PATTERN = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(?P<body>.*)$")
LIST_LEAD_SKIP_PATTERN = re.compile(r"^\s*(?:\||>|!!!|\?\?\?|===|<)")
LIST_BODY_PREFIX_PATTERN = re.compile(r"^(?:\*\*|_|\*|\[)+")
CASE_UPPER_REASON = (
    "List item starts lower case although the sentence above it is finished"
)
CASE_LOWER_REASON = (
    "List item starts upper case although it continues the sentence above it"
)


def check_semicolon(prose):
    entities = [match.span() for match in ENTITY_PATTERN.finditer(prose.masked)]
    for index, char in enumerate(prose.masked):
        if char != ";":
            continue
        if any(start <= index < end for start, end in entities):
            continue
        yield Finding(column=index, check="semicolon", reason=SEMICOLON_REASON)


# A table cell holding nothing but a dash is a value ("no default"), not an aside.
EMPTY_CELL_PATTERN = re.compile(r"\|\s*[—–]\s*(?=\|)")


def check_double_hyphen(prose):
    for match in DOUBLE_HYPHEN_PATTERN.finditer(prose.masked):
        yield Finding(
            column=match.start(), check="double-hyphen", reason=DOUBLE_HYPHEN_REASON
        )


def check_em_dash(prose):
    cells = [match.span() for match in EMPTY_CELL_PATTERN.finditer(prose.masked)]
    for index, char in enumerate(prose.masked):
        if char != "—":
            continue
        if any(start <= index < end for start, end in cells):
            continue
        yield Finding(column=index, check="em-dash", reason=EM_DASH_REASON)


# ---------------------------------------------------------------------------
# The punctuation of a list item
# ---------------------------------------------------------------------------

# The subject of a list item is bold and carries its colon inside the bold:
# "- **Foo:** bar". Everything else is one of the three ways to get it wrong: a
# colon behind the emphasis ("- **Foo**: bar"), a dash instead of a colon
# ("- **Foo** - bar"), or italic instead of bold ("- *Foo:* bar").
#
# One pattern per emphasis marker, since the closing marker has to match the
# opening one and the subject may contain the other marker. The separator is part
# of the replaced span, so that the whole of it becomes the colon. A numbered item
# carries a subject exactly like a bulleted one.
MARKER = r"^\s*(?:[-*+]|\d+[.)])\s+"
SEPARATOR = r"(?P<separator>\s*:|\s+[-–—](?=\s))?"
SUBJECT_PATTERNS = (
    ("**", re.compile(
        rf"{MARKER}(?P<replace>\*\*(?P<subject>[^*]+?)\*\*{SEPARATOR})")),
    ("*", re.compile(
        rf"{MARKER}(?P<replace>(?<!\*)\*(?P<subject>[^*]+?)\*(?!\*){SEPARATOR})")),
    ("_", re.compile(
        rf"{MARKER}(?P<replace>_(?P<subject>[^_]+?)_{SEPARATOR})")),
)

EMPHASIS_REASON = (
    "Italic subject of a list item, the subject is bold: write '**{subject}:**'"
)
COLON_REASON = (
    "Colon outside the bold subject of a list item, write '**{subject}:**'"
)
DASH_REASON = (
    "List item subject separated by a dash, write '**{subject}:**' with a colon"
)


def check_list_punctuation(prose):
    """The subject of a list item, which has exactly one spelling.

    Unlike the rules above, nothing here depends on the sentence, so these are
    errors that "--fix" resolves.
    """
    for marker, pattern in SUBJECT_PATTERNS:
        match = pattern.match(prose.text)
        if not match:
            continue

        subject = match.group("subject").rstrip()
        separator = match.group("separator") or ""
        carries_colon = subject.endswith(":")

        # A bold word that opens an item without a colon and without a separator
        # is part of the sentence, not a subject.
        if not carries_colon and not separator:
            return
        if marker == "**" and carries_colon and not separator:
            return

        if marker != "**":
            check, reason = "list-item-emphasis", EMPHASIS_REASON
        elif separator.lstrip().startswith(":"):
            check, reason = "list-item-colon", COLON_REASON
        else:
            check, reason = "list-item-dash", DASH_REASON

        subject = subject.rstrip(":").rstrip()
        yield Finding(
            column=match.start("replace"),
            check=check,
            reason=reason.format(subject=subject),
            severity=SEVERITY_ERROR,
            length=len(match.group("replace")),
            replacement=f"**{subject}:**",
        )
        return


RULES = (
    check_oxford_comma,
    check_semicolon,
    check_em_dash,
    check_double_hyphen,
    check_list_punctuation,
)


def check_list_item_case(lines):
    """Yield (line number, check, reason) for a list item that starts wrong.

    An item continues from whatever came above the list. After a heading, a full
    stop, or a colon the sentence is finished and the item opens a new one in
    upper case. After a line that just runs on, the item is the rest of that
    sentence and stays lower case.
    """
    in_code_fence = False
    lead = None

    for index, line in enumerate(lines):
        if CODE_FENCE_PATTERN.match(line):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue

        match = LIST_BODY_PATTERN.match(line)
        if not match:
            stripped = line.strip()
            if stripped and not LIST_LEAD_SKIP_PATTERN.match(stripped):
                lead = stripped
            continue

        body = match.group("body").strip()
        # A value or an identifier is written the way it is spelled.
        if lead is None or not body or body.startswith("`"):
            continue
        first = LIST_BODY_PREFIX_PATTERN.sub("", body)
        if not first or not first[0].isalpha():
            continue

        finished = lead.startswith("#") or lead.endswith((":", ".", "!", "?"))
        if finished and first[0].islower():
            yield index + 1, "list-item-case", CASE_UPPER_REASON
        elif not finished and first[0].isupper():
            yield index + 1, "list-item-case", CASE_LOWER_REASON


def scan_file(file_path):
    lines = read_lines(file_path)
    rel = relative_path(file_path)
    violations = []
    fixes = []

    for number, check, reason in check_list_item_case(lines):
        violations.append(
            Violation(
                file=rel,
                line=number,
                column=1,
                check=check,
                reason=reason,
                excerpt=lines[number - 1].strip()[:90],
                severity=SEVERITY_WARNING,
            )
        )

    for prose in iter_prose_lines(lines):
        findings = [finding for rule in RULES for finding in rule(prose)]
        for finding in sorted(findings, key=lambda f: f.column):
            violations.append(
                Violation(
                    file=rel,
                    line=prose.number,
                    column=finding.column + 1,
                    check=finding.check,
                    reason=finding.reason,
                    excerpt=get_line_excerpt(prose.text, finding.column),
                    severity=finding.severity,
                )
            )
            if finding.replacement:
                fixes.append(
                    FileFix(
                        line=prose.number,
                        column=finding.column + 1,
                        length=finding.length,
                        replacement=finding.replacement,
                    )
                )

    return violations, fixes


def report_generated(generated):
    print(f"Skipped {len(generated)} generated file(s), fix those at their source:")
    for file in generated:
        print(f"  • {relative_path(file)}")


def main():
    parser = argparse.ArgumentParser(
        description="Look for punctuation that the house style avoids."
    )
    parser.add_argument(
        "-f",
        "--fix",
        action="store_true",
        help="rewrite the list item subjects, the only rule that has one answer",
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

    files = collect_files(
        args.paths,
        on_missing=lambda target: print(f"Skipping missing path: {target}", file=sys.stderr),
    )
    files = drop_generated(files, report=report_generated)

    scans = {file: scan_file(file) for file in files}

    if args.fix:
        files_changed = 0
        applied = 0
        for file, (_, fixes) in scans.items():
            written = apply_fixes_to_file(file, fixes)
            if written:
                files_changed += 1
                applied += written
        if applied:
            print(
                f"Auto-fix mode: updated {applied} list item(s) "
                f"across {files_changed} file(s)."
            )
        scans = {file: scan_file(file) for file in files}

    violations = [v for violations, _ in scans.values() for v in violations]

    sys.exit(
        report_violations(
            violations,
            "punctuation check",
            files,
            "Reviewed {files} file(s), {warnings} punctuation candidate(s).",
            group_warnings=False,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as error:  # noqa: BLE001
        print("Failed to run punctuation check.", file=sys.stderr)
        print(error, file=sys.stderr)
        sys.exit(1)
