#!/usr/bin/env python3
"""Look for lists that are missing their Oxford comma.

The documentation separates the last item of a list with a comma as well:
"storage nodes, volumes, and snapshots", not "storage nodes, volumes and
snapshots". The same holds for the other conjunctions that end a series, "or"
and "nor".

The comma belongs to a series of three or more items, and only there. A comma in
front of an "and" that joins two sentences ("the cluster is created, and the pool
is added") is ordinary punctuation and no concern of this check.

Unlike the other gates, this one cannot be sure. Whether "A, B and C" is a list
of three items or a sentence that happens to contain a comma and an "and" is a
question of grammar, not of spelling:

    Missing:  "Read, Write and ReadWrite limits"         -> three list items
    Correct:  "reboots, graceful and ungraceful shutdowns" -> two items, the
                                                              second one paired
    Correct:  "Therefore, the average or the median"       -> no list at all

Telling those apart reliably needs to parse the sentence. This check instead
looks for the shape a list of short, parallel items has, and reports what it
finds as a **warning**: every finding is a candidate for a human to confirm, and
none of them fails the build. The rules below are deliberately narrow, so that
the few candidates reported are worth reading. Longer or less regular lists are
missed on purpose; a check that reported every comma followed by an "and" would
report a few hundred of them, almost all correct.

For the same reason there is no "--fix": inserting a comma into a sentence that
turns out not to be a list changes its meaning.

By default all Markdown files below "docs/" and "snippets/" are scanned.
Generated files are skipped, since they have to be corrected at their source.

Usage:
    python3 scripts/check-oxford-comma.py [PATH ...]
"""

import argparse
import re
import sys

from markdown_common import (
    DEFAULT_TARGET_DIRS,
    SEVERITY_WARNING,
    Violation,
    collect_files,
    drop_generated,
    get_line_excerpt,
    iter_prose_lines,
    read_lines,
    relative_path,
    report_violations,
)

CHECK_NAME = "oxford-comma"

# The conjunctions that can end a series, and that the Oxford comma is placed
# in front of.
CONJUNCTIONS = r"and|or|nor"

# A list item runs up to the next punctuation that ends it. A dash is included,
# since it separates parts of a sentence rather than items of a list.
ITEM = r"[^,;:.!?()\[\]—–]{1,45}"
CANDIDATE_PATTERN = re.compile(
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

REASON = (
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


def is_candidate(match):
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


def scan_file(file_path):
    lines = read_lines(file_path)
    rel = relative_path(file_path)
    violations = []

    for prose in iter_prose_lines(lines):
        for match in CANDIDATE_PATTERN.finditer(prose.masked):
            if not is_candidate(match):
                continue

            violations.append(
                Violation(
                    file=rel,
                    line=prose.number,
                    column=match.start() + 1,
                    check=CHECK_NAME,
                    reason=REASON.format(
                        conjunction=match.group("conjunction").lower(),
                        candidate=match.group(0).strip(),
                    ),
                    excerpt=get_line_excerpt(prose.text, match.start()),
                    severity=SEVERITY_WARNING,
                )
            )

    return violations


def report_generated(generated):
    print(f"Skipped {len(generated)} generated file(s), fix those at their source:")
    for file in generated:
        print(f"  • {relative_path(file)}")


def main():
    parser = argparse.ArgumentParser(
        description="Look for lists that are missing their Oxford comma."
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

    violations = [v for file in files for v in scan_file(file)]

    sys.exit(
        report_violations(
            violations,
            "Oxford comma check",
            files,
            "Reviewed {files} file(s), {warnings} candidate(s) for a missing Oxford comma.",
            group_warnings=False,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as error:  # noqa: BLE001
        print("Failed to run Oxford comma check.", file=sys.stderr)
        print(error, file=sys.stderr)
        sys.exit(1)
