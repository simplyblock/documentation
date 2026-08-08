#!/usr/bin/env python3
"""Check the words themselves: misspellings, repeated words, and the comma of an abbreviation.

Three mistakes that a reader trips over and a writer reads straight past, because
the eye supplies what the text is missing:

* A **misspelling** from the list below. It holds the words that are typed wrong
  often, not every word that exists, so a word absent from it is not thereby
  correct. British spellings live in scripts/check-american-english.py.
* A **repeated word**, as in "the volume is is migrated".
* An **abbreviation or an introduction without its comma**: American usage writes
  "e.g.," and "i.e.," and "for example," with the comma.

All three have exactly one right answer, so all three are errors that "--fix"
resolves.

By default all Markdown files below "docs/" and "snippets/" are scanned.
Generated files are skipped, since they have to be corrected at their source.

Usage:
    python3 scripts/check-prose.py [--fix] [PATH ...]
"""

import argparse
import re
import sys

from markdown_common import (
    CODE_SPAN_PATTERN,
    DEFAULT_TARGET_DIRS,
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

# Words that are typed wrong often enough to be worth naming. Every entry is
# wrong in both British and American English.
MISSPELLINGS = {
    "accomodate": "accommodate", "accross": "across", "acheive": "achieve",
    "adress": "address", "alot": "a lot", "auxilary": "auxiliary",
    "avaliable": "available", "bandwith": "bandwidth", "begining": "beginning",
    "calender": "calendar", "capcity": "capacity", "choosen": "chosen", "comitted": "committed",
    "comming": "coming", "compatability": "compatibility", "completly": "completely", "contigous": "contiguous",
    "concurent": "concurrent", "consistant": "consistent", "controll": "control",
    "curently": "currently", "defualt": "default", "definately": "definitely",
    "dependancy": "dependency", "developement": "development", "diferent": "different",
    "directroy": "directory", "efficent": "efficient", "enviroment": "environment",
    "environement": "environment", "excecute": "execute", "exisiting": "existing",
    "existance": "existence", "explicitely": "explicitly", "extention": "extension",
    "filesytem": "filesystem", "finaly": "finally", "folowing": "following",
    "formating": "formatting", "fucntion": "function", "hierachy": "hierarchy", "identifer": "identifier",
    "implementaion": "implementation", "independant": "independent",
    "informations": "information", "initalize": "initialize", "instace": "instance",
    "intergration": "integration", "interupt": "interrupt", "labled": "labeled",
    "lenght": "length", "libary": "library", "maintainance": "maintenance",
    "managment": "management", "mesage": "message", "minumum": "minimum",
    "moounted": "mounted",
    "mutliple": "multiple", "neccesary": "necessary", "neccessary": "necessary",
    "occassion": "occasion", "occurance": "occurrence", "occured": "occurred",
    "occurence": "occurrence", "operatior": "operator", "orginal": "original", "paramaters": "parameters",
    "paramter": "parameter", "paramters": "parameters", "parrallel": "parallel",
    "particulary": "particularly", "perfomance": "performance",
    "performence": "performance", "permision": "permission", "persistant": "persistent",
    "posible": "possible", "prefered": "preferred", "priviledge": "privilege",
    "proccess": "process", "publically": "publicly", "recieve": "receive",
    "recieved": "received", "recomend": "recommend", "recomended": "recommended",
    "refered": "referred", "refering": "referring", "releated": "related",
    "requiered": "required", "resposne": "response", "retreive": "retrieve",
    "runing": "running", "seperate": "separate", "seperately": "separately",
    "seperation": "separation", "seperator": "separator", "similiar": "similar",
    "specifiy": "specify", "staticly": "statically", "sucess": "success", "sucessful": "successful",
    "sucessfully": "successfully", "successfull": "successful",
    "successfuly": "successfully", "supress": "suppress",
    "synchronzation": "synchronization", "temprary": "temporary",
    "thier": "their", "threshhold": "threshold", "tolerence": "tolerance",
    "transfered": "transferred", "typicaly": "typically", "unkown": "unknown",
    "usally": "usually", "usefull": "useful", "verison": "version",
    "volimes": "volumes",
    "wether": "whether", "wich": "which", "writting": "writing",
    # The two deployment topologies. One is hyphenated and the other is not, so
    # both are written the wrong way about equally often.
    "hyperconverged": "hyper-converged", "hyper converged": "hyper-converged",
    "hyperconvergence": "hyper-convergence",
    "hyper convergence": "hyper-convergence",
    "dis-aggregated": "disaggregated", "dis aggregated": "disaggregated",
    "disagregated": "disaggregated", "dissagregated": "disaggregated",
    "dissaggregated": "disaggregated",
    "dis-aggregation": "disaggregation", "dissaggregation": "disaggregation",
    # Multipathing is one word, in the NVMe specification as well as in the
    # "dm-multipath" and "nvme multipath" spellings it is written next to.
    "multi-pathing": "multipathing", "multi pathing": "multipathing",
    "multi-path": "multipath", "multi path": "multipath",
    # Misspelled names. The casing of each of these is held by
    # check-terminology.py and check-simplyblock-spelling.py, but a missing or a
    # swapped letter makes a different word, which only this check rewrites.
    # Graylog is spelled the American way by its owner, and "Greylog" is a
    # different word rather than a casing of it, so the terminology gate cannot
    # see it and check-american-english.py cannot either: its "grey" carries a
    # word boundary, which "Greylog" does not have.
    "greylog": "Graylog",
    "graphana": "Grafana", "grafanna": "Grafana",
    "promethius": "Prometheus", "prometeus": "Prometheus",
    "kubernets": "Kubernetes", "kubenetes": "Kubernetes",
    "kuberenetes": "Kubernetes", "openshfit": "OpenShift",
    "kinux": "Linux", "kockless": "lockless", "hashcorp": "HashiCorp",
    "relabalcing": "rebalancing", "relabalancing": "rebalancing",
    "simyplyblock": "simplyblock", "simpylblock": "simplyblock",
    "simplyblok": "simplyblock", "simplybock": "simplyblock",
    "simpyblock": "simplyblock", "simplybloc": "simplyblock",
    # The fault-tolerance level is written "FTT 1" or "FTT=1", never glued or
    # hyphenated. "FTT+1" is left alone: it means the level plus one node, not a
    # level of its own.
    "ftt1": "FTT 1", "ftt2": "FTT 2",
    "ftt-1": "FTT 1", "ftt-2": "FTT 2",
    "ftt_1": "FTT 1", "ftt_2": "FTT 2",
}
MISSPELLING_PATTERN = re.compile(
    r"\b(?:"
    + "|".join(re.escape(word) for word in sorted(MISSPELLINGS, key=len, reverse=True))
    + r")\b",
    re.IGNORECASE,
)

# "the volume is is migrated". The second word may not run on into a hyphenated
# compound, so that "based on on-time thresholds" is left alone.
REPEATED_WORD_PATTERN = re.compile(r"\b(\w+)([ \t]+)(\1)\b(?![-\w])", re.IGNORECASE)

# An abbreviation and an introduction both take a comma before the example they
# introduce. "that is" is deliberately absent: it is a relative clause far more
# often than an introduction ("a disk that is not the root disk").
COMMA_PATTERN = re.compile(
    r"\b(?P<phrase>e\.g\.|i\.e\.|for example|for instance|in other words|namely)"
    r"(?![,:.])(?=\s)",
    re.IGNORECASE,
)

# Two spaces between words are a typing artifact. Table columns and the wide
# markers of a grid card are lined up on purpose, so those lines are left out.
DOUBLE_SPACE_PATTERN = re.compile(r"(?<=[A-Za-z,.;:)\]`])( {2,})(?=[A-Za-z(\[`])")
ALIGNED_LINE_PATTERN = re.compile(r"^\s*(?:\||[-*+]\s{2,})")

# A compound in front of a noun is hyphenated ("a high-availability cluster"),
# the same words standing alone as a noun are not ("it provides high
# availability"). The words below follow the compound without being the noun it
# describes, so they mark the cases to leave alone. A comma behind the compound
# ends it, so only a directly following word counts.
NOT_A_NOUN = {
    "and", "or", "but", "by", "with", "without", "for", "to", "in", "of", "on",
    "at", "from", "is", "are", "was", "were", "has", "have", "had", "can",
    "could", "will", "would", "may", "might", "must", "across", "between",
    "during", "through", "as", "that", "which", "when", "while",
}
COMPOUNDS = ("high availability", "large scale", "low latency", "real time")
COMPOUND_PATTERN = re.compile(
    r"\b(?P<compound>" + "|".join(COMPOUNDS) + r")[ \t]+(?P<next>[A-Za-z][\w-]*)",
    re.IGNORECASE,
)

# An adverb ending in "ly" is never hyphenated to the adjective behind it.
ADVERB_HYPHEN_PATTERN = re.compile(r"\b(\w+ly)-(\w+)\b")

MISSPELLING_REASON = "Misspelling of '{expected}'"
REPEATED_REASON = "The word '{word}' is repeated"
COMMA_REASON = "'{phrase}' introduces an example and takes a comma"
DOUBLE_SPACE_REASON = "Two spaces between words"
COMPOUND_REASON = "'{compound}' describes '{next}' here, so it is hyphenated: '{expected}'"
ADVERB_REASON = "An adverb is not hyphenated to its adjective: '{expected}'"


def scan_file(file_path):
    lines = read_lines(file_path)
    rel = relative_path(file_path)
    violations = []
    fixes = []

    def report(number, column, check, reason, text, length=0, replacement=""):
        violations.append(
            Violation(
                file=rel,
                line=number,
                column=column + 1,
                check=check,
                reason=reason,
                excerpt=get_line_excerpt(text, column),
            )
        )
        if replacement:
            fixes.append(
                FileFix(
                    line=number,
                    column=column + 1,
                    length=length,
                    replacement=replacement,
                )
            )

    for prose in iter_prose_lines(lines):
        for match in MISSPELLING_PATTERN.finditer(prose.masked):
            found = match.group(0)
            expected = MISSPELLINGS[found.lower()]
            if found[0].isupper():
                expected = expected[0].upper() + expected[1:]
            report(
                prose.number, match.start(), "misspelling",
                MISSPELLING_REASON.format(expected=expected),
                prose.text, len(found), expected,
            )

        # A code span is removed rather than blanked, so that the words on either
        # side of it are never read as neighbours.
        without_code = CODE_SPAN_PATTERN.sub("\x00", prose.text)
        for match in REPEATED_WORD_PATTERN.finditer(without_code):
            report(
                prose.number, match.start(), "repeated-word",
                REPEATED_REASON.format(word=match.group(1)),
                prose.text,
                len(match.group(0)), match.group(1),
            )

        if not ALIGNED_LINE_PATTERN.match(prose.text):
            for match in DOUBLE_SPACE_PATTERN.finditer(prose.text):
                report(
                    prose.number, match.start(1), "double-space", DOUBLE_SPACE_REASON,
                    prose.text, len(match.group(1)), " ",
                )

        for match in COMPOUND_PATTERN.finditer(prose.masked):
            if match.group("next").lower() in NOT_A_NOUN:
                continue
            compound = match.group("compound")
            expected = compound.replace(" ", "-")
            report(
                prose.number, match.start("compound"), "compound-hyphen",
                COMPOUND_REASON.format(
                    compound=compound, next=match.group("next"), expected=expected
                ),
                prose.text, len(compound), expected,
            )

        for match in ADVERB_HYPHEN_PATTERN.finditer(prose.masked):
            expected = f"{match.group(1)} {match.group(2)}"
            report(
                prose.number, match.start(), "adverb-hyphen",
                ADVERB_REASON.format(expected=expected),
                prose.text, len(match.group(0)), expected,
            )

        for match in COMMA_PATTERN.finditer(prose.masked):
            phrase = match.group("phrase")
            report(
                prose.number, match.start(), "missing-comma",
                COMMA_REASON.format(phrase=phrase),
                prose.text, len(phrase), phrase + ",",
            )

    return violations, fixes


def report_generated(generated):
    print(f"Skipped {len(generated)} generated file(s), fix those at their source:")
    for file in generated:
        print(f"  • {relative_path(file)}")


def main():
    parser = argparse.ArgumentParser(
        description="Check misspellings, repeated words, and the comma of an abbreviation."
    )
    parser.add_argument(
        "-f",
        "--fix",
        action="store_true",
        help="rewrite every reported word, repetition, and missing comma",
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
                f"Auto-fix mode: updated {applied} occurrence(s) "
                f"across {files_changed} file(s)."
            )
        scans = {file: scan_file(file) for file in files}

    violations = [v for violations, _ in scans.values() for v in violations]

    sys.exit(
        report_violations(
            violations,
            "prose check",
            files,
            f"No misspellings, repetitions, or missing commas found in {{files}} file(s) "
            f"({len(MISSPELLINGS)} misspelling(s) checked).",
        )
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as error:  # noqa: BLE001
        print("Failed to run prose check.", file=sys.stderr)
        print(error, file=sys.stderr)
        sys.exit(1)
