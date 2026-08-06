#!/usr/bin/env python3
"""Check that the documentation is written without addressing a person.

The documentation describes a system, not a conversation: it neither addresses
the reader ("you", "your") nor speaks as the author ("we", "our", "I"). A
sentence that needs one of those pronouns is rewritten impersonally.

    Before: "You have to create your cluster before you can attach a volume."
    After:  "A cluster has to be created before a volume can be attached."

    Before: "We recommend three storage nodes."
    After:  "Three storage nodes are recommended."

Next to the pronouns, a few wordings address the reader without naming a person
("please", "let us", "feel free"). They are reported for the same reason.

Only prose is checked. Code blocks, inline code, mkdocs-macros expressions, link
targets and raw HTML carry no prose, and a pronoun that is part of an identifier
("my-cluster", "us-east-1", "your-namespace") is a value, not an address.

By default all Markdown files below "docs/" and "snippets/" are scanned.
Generated files are skipped, since they have to be corrected at their source.

Usage:
    python3 scripts/check-voice.py [PATH ...]
"""

import argparse
import re
import sys

from markdown_common import (
    DEFAULT_TARGET_DIRS,
    Violation,
    collect_files,
    drop_generated,
    get_line_excerpt,
    is_part_of_identifier,
    iter_prose_lines,
    read_lines,
    relative_path,
    report_violations,
)

CHECK_NAME = "voice"

# The wordings the check reports, grouped by what they do to a sentence. The
# contractions are listed next to their pronoun, since the apostrophe is not a
# word character and a plain word boundary would only match their first half.
SECOND_PERSON = [
    "you", "your", "yours", "yourself", "yourselves",
    "you're", "you've", "you'll", "you'd",
    # Archaic, but they address a reader just as much.
    "thou", "thee", "thy", "thine", "thyself", "ye",
]
FIRST_PERSON = [
    "we", "we're", "we've", "we'll", "we'd",
    "us", "our", "ours", "ourselves",
    "me", "my", "mine", "myself",
    "i'm", "i've", "i'll", "i'd",
    "let's",
]
# "I" is matched case-sensitively: a lowercase "i" is an index or an option
# ("-i"), never a pronoun.
FIRST_PERSON_CASED = ["I"]
# Wordings that address the reader without naming a person. Google's developer
# documentation style guide rejects them for the same reason: they turn a
# description into a conversation.
DIRECT_ADDRESS = [
    "please", "kindly", "let us", "feel free",
    "thank you", "thanks for", "thanks to you",
]

CATEGORY_OF = {}
for phrase in SECOND_PERSON:
    CATEGORY_OF[phrase] = "Second person pronoun"
for phrase in FIRST_PERSON + FIRST_PERSON_CASED:
    CATEGORY_OF[phrase.lower()] = "First person pronoun"
for phrase in DIRECT_ADDRESS:
    CATEGORY_OF[phrase] = "Direct address"

# The apostrophe may be typed straight or as a typographic quote.
APOSTROPHE = "['‘’ʼ]"


def normalize(found):
    """Reduce a match to the form the phrase lists are written in."""
    return re.sub(r"\s+", " ", re.sub(APOSTROPHE, "'", found.lower()))


def phrase_pattern(phrases):
    """Build the alternation that matches the given phrases as whole words.

    The words of a phrase are joined by "\\s+", so that it is still found when
    more than one space separates them.
    """
    # Longest first, so that "you're" wins over "you" and "let us" over "us".
    alternatives = [
        r"\s+".join(re.escape(word).replace("'", APOSTROPHE) for word in phrase.split())
        for phrase in sorted(phrases, key=len, reverse=True)
    ]
    return r"\b(?:" + "|".join(alternatives) + r")\b"


PHRASE_PATTERN = re.compile(
    phrase_pattern(SECOND_PERSON + FIRST_PERSON + DIRECT_ADDRESS), re.IGNORECASE
)
CASED_PHRASE_PATTERN = re.compile(phrase_pattern(FIRST_PERSON_CASED))

REASON = (
    "{category} '{found}', the documentation describes the system impersonally "
    "(rewrite without addressing a person)"
)


def scan_file(file_path):
    lines = read_lines(file_path)
    rel = relative_path(file_path)
    violations = []

    for prose in iter_prose_lines(lines):
        matches = list(PHRASE_PATTERN.finditer(prose.masked))
        covered = {index for match in matches for index in range(*match.span())}
        # "I" is matched separately, and its own match is already covered when it
        # opens a contraction ("I'm").
        matches += [
            match
            for match in CASED_PHRASE_PATTERN.finditer(prose.masked)
            if match.start() not in covered
        ]

        for match in sorted(matches, key=lambda m: m.start()):
            found = match.group(0)
            if is_part_of_identifier(prose.text, match.start(), match.end()):
                continue

            violations.append(
                Violation(
                    file=rel,
                    line=prose.number,
                    column=match.start() + 1,
                    check=CHECK_NAME,
                    reason=REASON.format(
                        category=CATEGORY_OF[normalize(found)], found=found
                    ),
                    excerpt=get_line_excerpt(prose.text, match.start()),
                )
            )

    return violations


def main():
    parser = argparse.ArgumentParser(
        description="Check that the documentation neither addresses the reader nor the author."
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
            "voice check",
            files,
            "No first or second person pronouns found in {files} file(s).",
        )
    )


def report_generated(generated):
    print(f"Skipped {len(generated)} generated file(s), fix those at their source:")
    for file in generated:
        print(f"  • {relative_path(file)}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as error:  # noqa: BLE001
        print("Failed to run voice check.", file=sys.stderr)
        print(error, file=sys.stderr)
        sys.exit(1)
