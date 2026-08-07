#!/usr/bin/env python3
"""Check that the documentation is written in American English.

The documentation uses American spelling throughout: "color" and not "colour",
"canceled" and not "cancelled", "analyze" and not "analyse", "center" and not
"centre". Every British spelling below is matched regardless of its casing and
reported with the American one, keeping the casing it was written in.

The word list is explicit on purpose. A rule such as "-ise becomes -ize" would
rewrite "advertise", "comprise" and "supervise", which are spelled the same on
both sides of the Atlantic, so only the words that really differ are listed.

Some proper names carry a British spelling and keep it: "Fibre Channel" is the
name of a standard, not a spelling of "fiber".

A British spelling in prose fails the check. Inside a code block only the
comments are checked, and they are reported as a warning: identifiers and
commands are literals, and a variable named "colour" has to keep its name.

By default all Markdown files below "docs/" and "snippets/" are scanned.
Generated files are skipped, since they have to be corrected at their source.

Usage:
    python3 scripts/check-american-english.py [--fix] [PATH ...]

"--fix" rewrites the prose occurrences only, never the inside of a code block.
"""

import argparse
import re
import sys

from markdown_common import (
    CONTEXT_CODE,
    DEFAULT_TARGET_DIRS,
    SEVERITY_ERROR,
    SEVERITY_WARNING,
    FileFix,
    Violation,
    apply_fixes_to_file,
    collect_files,
    drop_generated,
    get_line_excerpt,
    is_inside_range,
    is_part_of_identifier,
    iter_prose_lines,
    read_lines,
    relative_path,
    report_violations,
)

CHECK_NAME = "american-english"


def ise_verbs(*bases):
    """Map the "-ise" verbs to "-ize", together with the forms built on them.

    The difference sits inside the word, so British and American take the same
    endings: "organis|e" and "organiz|e" both become "-es", "-ed", "-ing" and
    "-ation".
    """
    suffixes = ("e", "es", "ed", "ing", "er", "ers", "ation", "ations", "able")
    pairs = {}
    for base in bases:
        british, american = base[:-1], base[:-2] + "z"
        for suffix in suffixes:
            pairs[british + suffix] = american + suffix
    return pairs


def yse_verbs(*bases):
    """Map the "-yse" verbs to "-yze".

    The "-es" form is left out: "analyses" is also the plural of "analysis",
    which is spelled that way in American English too.
    """
    pairs = {}
    for base in bases:
        british, american = base[:-1], base[:-2] + "z"
        for suffix in ("e", "ed", "ing"):
            pairs[british + suffix] = american + suffix
    return pairs


def our_nouns(*bases):
    """Map the "-our" words to "-or", together with the forms built on them."""
    suffixes = (
        "", "s", "ed", "ing", "ful", "fully", "less", "able", "ably",
        "al", "ally", "ite", "ites", "hood", "hoods",
    )
    pairs = {}
    for base in bases:
        british, american = base, base[:-2] + "r"
        for suffix in suffixes:
            pairs[british + suffix] = american + suffix
    return pairs


def re_nouns(*bases):
    """Map the "-re" words to "-er", together with the forms built on them."""
    pairs = {}
    for base in bases:
        stem = base[:-2]
        for british, american in (("re", "er"), ("res", "ers"), ("red", "ered"), ("ring", "ering")):
            pairs[stem + british] = stem + american
    return pairs


def explicit(*pairs):
    """Take the British and American spellings as they are written."""
    return dict(pairs)


SPELLINGS = {}
SPELLINGS.update(ise_verbs(
    "apologise", "authorise", "capitalise", "categorise", "centralise",
    "characterise", "colonise", "commercialise", "computerise", "containerise",
    "criticise", "customise", "decentralise", "deserialise", "digitise",
    "emphasise", "equalise", "familiarise", "finalise", "formalise",
    "generalise", "harmonise", "humanise", "hybridise", "idealise",
    "incentivise", "industrialise", "initialise", "internalise", "itemise",
    "legalise", "legitimise", "localise", "marginalise", "materialise",
    "maximise", "memorise", "minimise", "mobilise", "modernise", "modularise",
    "monetise", "nationalise", "neutralise", "normalise", "optimise",
    "organise", "oxidise", "parallelise", "parameterise", "penalise",
    "personalise", "polarise", "popularise", "pressurise", "prioritise",
    "privatise", "publicise", "quantise", "randomise", "rationalise",
    "realise", "recognise", "regularise", "revolutionise", "sanitise",
    "scrutinise", "sensitise", "serialise", "socialise", "specialise",
    "stabilise", "standardise", "sterilise", "stigmatise", "subsidise",
    "summarise", "symbolise", "sympathise", "synchronise", "synthesise",
    "systematise", "theorise", "tokenise", "unionise", "urbanise", "utilise",
    "vaporise", "verbalise", "virtualise", "visualise", "weaponise",
))
SPELLINGS.update(yse_verbs(
    "analyse", "catalyse", "dialyse", "electrolyse", "hydrolyse", "paralyse",
))
SPELLINGS.update(our_nouns(
    "ardour", "armour", "behaviour", "candour", "clamour", "colour",
    "demeanour", "endeavour", "favour", "fervour", "flavour", "harbour",
    "honour", "humour", "labour", "misdemeanour", "neighbour", "odour",
    "parlour", "rancour", "rigour", "rumour", "savour", "saviour", "splendour",
    "tumour", "valour", "vapour", "vigour",
))
SPELLINGS.update(re_nouns(
    "calibre", "centimetre", "centre", "datacentre", "fibre", "goitre",
    "kilometre", "litre", "lustre", "meagre", "metre", "millimetre", "mitre",
    "sabre", "sceptre", "sombre", "spectre", "theatre", "titre",
))

# The doubled "l": British doubles it before a suffix ("cancelled"), American
# does not, and the other way around at the end of a word ("fulfil"). Only the
# words that really differ are listed: "cancellation" and "controlled" are
# spelled the same on both sides.
SPELLINGS.update(explicit(
    ("cancelled", "canceled"), ("cancelling", "canceling"),
    ("channelled", "channeled"), ("channelling", "channeling"),
    ("counselled", "counseled"), ("counselling", "counseling"),
    ("counsellor", "counselor"), ("counsellors", "counselors"),
    ("dialled", "dialed"), ("dialling", "dialing"),
    ("equalled", "equaled"), ("equalling", "equaling"),
    ("fuelled", "fueled"), ("fuelling", "fueling"),
    ("labelled", "labeled"), ("labelling", "labeling"),
    ("levelled", "leveled"), ("levelling", "leveling"),
    ("marvelled", "marveled"),
    ("modelled", "modeled"), ("modelling", "modeling"),
    ("modeller", "modeler"), ("modellers", "modelers"),
    ("signalled", "signaled"), ("signalling", "signaling"),
    ("spiralled", "spiraled"), ("spiralling", "spiraling"),
    ("totalled", "totaled"), ("totalling", "totaling"),
    ("travelled", "traveled"), ("travelling", "traveling"),
    ("traveller", "traveler"), ("travellers", "travelers"),
    ("appal", "appall"), ("appals", "appalls"),
    ("distil", "distill"), ("distils", "distills"),
    ("enrol", "enroll"), ("enrols", "enrolls"),
    ("enrolment", "enrollment"), ("enrolments", "enrollments"),
    ("enthral", "enthrall"),
    ("fulfil", "fulfill"), ("fulfils", "fulfills"),
    ("fulfilment", "fulfillment"), ("fulfilments", "fulfillments"),
    ("instalment", "installment"), ("instalments", "installments"),
    ("instil", "instill"), ("instils", "instills"),
    ("skilful", "skillful"), ("skilfully", "skillfully"),
    ("wilful", "willful"), ("wilfully", "willfully"),
))

# Nouns written with a "c" in British English and with an "s" in American
# English, and the verb "practise", which American English does not know.
SPELLINGS.update(explicit(
    ("defence", "defense"), ("defences", "defenses"),
    ("licence", "license"), ("licences", "licenses"), ("licenced", "licensed"),
    ("offence", "offense"), ("offences", "offenses"),
    ("pretence", "pretense"),
    ("practise", "practice"), ("practises", "practices"),
    ("practised", "practiced"), ("practising", "practicing"),
))

# Ligatures and everything that follows no rule at all.
SPELLINGS.update(explicit(
    ("aeroplane", "airplane"), ("aeroplanes", "airplanes"),
    ("ageing", "aging"),
    # American English drops the "s" of the directional adverbs. "sideways" is
    # not one of them: it has no "sideway" form on either side.
    ("afterwards", "afterward"), ("backwards", "backward"),
    # A hyphenated compound would otherwise be read as an identifier and skipped.
    ("backwards-compatible", "backward-compatible"),
    ("downwards", "downward"), ("forwards", "forward"),
    ("inwards", "inward"), ("onwards", "onward"),
    ("outwards", "outward"), ("towards", "toward"),
    ("upwards", "upward"),
    ("aluminium", "aluminum"),
    ("amidst", "amid"), ("amongst", "among"), ("whilst", "while"),
    ("analogue", "analog"), ("analogues", "analogs"),
    ("artefact", "artifact"), ("artefacts", "artifacts"),
    ("catalogue", "catalog"), ("catalogues", "catalogs"),
    ("catalogued", "cataloged"), ("cataloguing", "cataloging"),
    ("cheque", "check"), ("cheques", "checks"),
    ("dialogue", "dialog"), ("dialogues", "dialogs"),
    ("draught", "draft"), ("draughts", "drafts"),
    ("encyclopaedia", "encyclopedia"),
    ("enquiry", "inquiry"), ("enquiries", "inquiries"),
    ("grey", "gray"), ("greys", "grays"), ("greyed", "grayed"),
    ("greyish", "grayish"), ("greyscale", "grayscale"),
    ("judgement", "judgment"), ("judgements", "judgments"),
    ("acknowledgement", "acknowledgment"),
    ("acknowledgements", "acknowledgments"),
    ("kerb", "curb"), ("kerbs", "curbs"),
    ("learnt", "learned"), ("spelt", "spelled"), ("dreamt", "dreamed"),
    ("manoeuvre", "maneuver"), ("manoeuvres", "maneuvers"),
    ("manoeuvred", "maneuvered"), ("manoeuvring", "maneuvering"),
    ("mould", "mold"), ("moulds", "molds"), ("moulded", "molded"),
    ("moulding", "molding"), ("smoulder", "smolder"),
    ("moustache", "mustache"),
    ("plough", "plow"), ("ploughs", "plows"),
    ("programme", "program"), ("programmes", "programs"),
    ("pyjamas", "pajamas"),
    ("sceptic", "skeptic"), ("sceptical", "skeptical"),
    ("scepticism", "skepticism"),
    ("speciality", "specialty"), ("specialities", "specialties"),
    ("storey", "story"), ("storeys", "stories"),
    ("sulphur", "sulfur"), ("sulphate", "sulfate"), ("sulphide", "sulfide"),
    ("sulphuric", "sulfuric"),
    ("tyre", "tire"), ("tyres", "tires"),
))

# Proper names that carry a British spelling. "Fibre Channel" is the name of the
# standard, in American English as well.
EXEMPT_NAMES = [re.compile(r"\bFibre\s+Channel\b", re.IGNORECASE)]

REASON = "British spelling '{found}', the documentation is written in American English: '{expected}'"


def build_pattern():
    """Build the alternation that matches every listed British spelling."""
    # Longest first, so that "colourless" wins over "colour".
    alternatives = [re.escape(word) for word in sorted(SPELLINGS, key=len, reverse=True)]
    return re.compile(r"\b(?:" + "|".join(alternatives) + r")\b", re.IGNORECASE)


SPELLING_PATTERN = build_pattern()


def matching_case(found, replacement):
    """Write the replacement the way the match was written."""
    if found.isupper() and len(found) > 1:
        return replacement.upper()
    if found[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


def exempt_ranges(line):
    return [match.span() for pattern in EXEMPT_NAMES for match in pattern.finditer(line)]


def scan_file(file_path):
    lines = read_lines(file_path)
    rel = relative_path(file_path)
    violations = []
    fixes = []

    for prose in iter_prose_lines(lines, include_code=True):
        exempt = exempt_ranges(prose.masked)

        for match in SPELLING_PATTERN.finditer(prose.masked):
            found = match.group(0)
            if is_inside_range(exempt, match.start()):
                continue
            if is_part_of_identifier(prose.text, match.start(), match.end()):
                continue

            expected = matching_case(found, SPELLINGS[found.lower()])
            in_code = prose.context == CONTEXT_CODE
            violations.append(
                Violation(
                    file=rel,
                    line=prose.number,
                    column=match.start() + 1,
                    check=CHECK_NAME,
                    reason=REASON.format(found=found, expected=expected),
                    excerpt=get_line_excerpt(prose.text, match.start()),
                    severity=SEVERITY_WARNING if in_code else SEVERITY_ERROR,
                )
            )
            # A comment may sit next to an identifier that carries the same
            # spelling, so a code block is never rewritten automatically.
            if not in_code:
                fixes.append(
                    FileFix(
                        line=prose.number,
                        column=match.start() + 1,
                        length=len(found),
                        replacement=expected,
                    )
                )

    return violations, fixes


def report_generated(generated):
    print(f"Skipped {len(generated)} generated file(s), fix those at their source:")
    for file in generated:
        print(f"  • {relative_path(file)}")


def main():
    parser = argparse.ArgumentParser(
        description="Check that the documentation is written in American English."
    )
    parser.add_argument(
        "-f",
        "--fix",
        action="store_true",
        help="rewrite every reported word to its American spelling",
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
            "American English check",
            files,
            f"No British spellings found in {{files}} file(s) "
            f"({len(SPELLINGS)} spelling(s) checked).",
        )
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as error:  # noqa: BLE001
        print("Failed to run American English check.", file=sys.stderr)
        print(error, file=sys.stderr)
        sys.exit(1)
