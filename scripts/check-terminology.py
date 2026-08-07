#!/usr/bin/env python3
"""Check that product names, projects and acronyms are spelled the way their owners spell them.

"Kubernetes" is never "kubernetes", "OpenShift" is never "Openshift" and NVMe is
never "nvme". Every term below is matched regardless of its casing, and reported
when it is not written in its canonical form. A trailing plural "s" is part of
the match, so "CRDs" is checked as well.

The casing of the "simplyblock" brand follows its own rules and is checked by
scripts/check-simplyblock-spelling.py instead.

A misspelling in prose fails the check. Inline code, mkdocs-macros expressions,
link targets and raw HTML are literals and are not looked at, and neither is a
term that is part of a larger token: "nvme-cli", "linux-headers" and "docker.io"
name a package, a command or a host, not a product.

Inside a code block only the comments are checked, and they are reported as a
warning: the commands, values and program output around them are literals, and a
comment is easily missed but never breaks anything when it is wrong.

By default all Markdown files below "docs/" and "snippets/" are scanned.
Generated files are skipped, since they have to be corrected at their source.

Usage:
    python3 scripts/check-terminology.py [--fix] [PATH ...]

"--fix" rewrites the prose occurrences only, never the inside of a code block.
"""

import argparse
import re
import sys
from dataclasses import dataclass, field

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
    is_part_of_identifier,
    iter_prose_lines,
    read_lines,
    relative_path,
    report_violations,
)

CHECK_NAME = "terminology"


@dataclass
class Term:
    """A term, and the other names that mean the same thing.

    "canonical" is how the term is written. An "alias" is a second name that is
    just as correct ("NVMe over Fabrics" next to "NVMe-oF"); it is checked for its
    own spelling and never rewritten to the canonical one.

    Casing and separators are never listed: every name is matched regardless of
    its case, and its separators match each other, so "NVMEoF", "nvme-of" and
    "NVMe oF" all resolve to "NVMe-oF".

    "plural" is how the term reads in the plural, for a term that has none of its
    own. NVMe is a protocol, so there is no such thing as "NVMEs": what is plural
    is the thing that speaks it, and the sentence has to name it ("NVMe devices").
    """

    canonical: str
    aliases: tuple = field(default_factory=tuple)
    plural: str = ""
    wrong: tuple = field(default_factory=tuple)


def terms(*entries):
    return [
        entry if isinstance(entry, Term) else Term(entry) if isinstance(entry, str)
        else Term(*entry)
        for entry in entries
    ]


def term(canonical, aliases=(), plural="", wrong=()):
    return Term(canonical, tuple(aliases), plural, tuple(wrong))


# Terms that are deliberately absent, because their lowercase spelling is an
# English word or a command, and reporting it would be wrong more often than
# right: "Go" (the verb), "Git" (the command), "Kind" (the adjective), "REST"
# ("encryption at rest"), "Windows" ("maintenance windows"), "Flux", "Swift",
# "Glance" and "Bash".
#
# Architectures are listed as the separate names they are. "x86-64", "x86_64",
# "x64" and "AMD64" name the same architecture but are not spellings of each
# other, and neither are "ARM64" and "AArch64", so none of them is rewritten
# into another.
TERMS = terms(
    # Operating systems and distributions.
    "Linux",
    "macOS",
    "Unix",
    "FreeBSD",
    "Ubuntu",
    "Debian",
    "CentOS",
    "Fedora",
    "RHEL",
    "Red Hat",
    "Red Hat Enterprise Linux",
    "Rocky Linux",
    "AlmaLinux",
    "Amazon Linux",
    "openSUSE",
    "SUSE",
    "Oracle Linux",
    "Alpine Linux",
    "systemd",
    "udev",
    "GRUB",
    "iptables",
    "nftables",
    # Kubernetes and the container ecosystem.
    "Kubernetes",
    "K8s",
    "K3s",
    "OpenShift",
    "Rancher",
    "Talos",
    "Docker",
    "Docker Swarm",
    "Podman",
    "containerd",
    "CRI-O",
    "Helm",
    "kubectl",
    "kubeadm",
    "minikube",
    "Kustomize",
    "Karpenter",
    "Istio",
    "Argo CD",
    "Prometheus",
    "Grafana",
    "Graylog",
    "OpenSearch",
    "Elasticsearch",
    "MongoDB",
    "Thanos",
    "Loki",
    # Virtualization, clouds and their services.
    "OpenStack",
    "Proxmox",
    "VMware",
    "vSphere",
    "ESXi",
    "KVM",
    "QEMU",
    "libvirt",
    "LXC",
    "Hyper-V",
    "AWS",
    "Amazon Web Services",
    "Azure",
    "GCP",
    "Google Cloud",
    "EC2",
    "EBS",
    "EKS",
    "AKS",
    "GKE",
    "IAM",
    "Terraform",
    "Ansible",
    "Cinder",
    "Nova",
    "Keystone",
    "DevStack",
    # Databases and languages.
    "FoundationDB",
    "PostgreSQL",
    "MySQL",
    "Redis",
    "Kafka",
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "Node.js",
    "Rust",
    "Markdown",
    "MkDocs",
    "GitHub",
    "GitLab",
    "Slack",
    "Jira",
    # Storage and networking.
    term("NVMe", ("NVM Express",), plural="NVMe devices"),
    term("NVMe-oF", ("NVMe over Fabrics", "NVMf"), plural="NVMe-oF connections"),
    term("NVMe/TCP", plural="NVMe/TCP connections"),
    term("NVMe/RDMA", plural="NVMe/RDMA connections"),
    "SPDK",
    "DPDK",
    "iSCSI",
    "SCSI",
    "RDMA",
    "RoCE",
    "InfiniBand",
    "Fibre Channel",
    "SATA",
    "SAS",
    "PCIe",
    "SSD",
    "HDD",
    "JBOD",
    "HBA",
    "LUN",
    "NUMA",
    "RAID",
    "LVM",
    "ZFS",
    "XFS",
    "ext4",
    "Btrfs",
    "Ceph",
    "MinIO",
    "S3",
    "QoS",
    "IOPS",
    term("I/O", wrong=("IO",)),
    "TCP",
    "UDP",
    "IP",
    "TCP/IP",
    "IPv4",
    "IPv6",
    "DNS",
    "DHCP",
    "VLAN",
    "VPC",
    "MTU",
    "NIC",
    "CIDR",
    # Protocols, formats and interfaces.
    "TLS",
    "mTLS",
    "SSL",
    "SSH",
    "HTTP",
    "HTTPS",
    "gRPC",
    "JSON",
    "YAML",
    "TOML",
    "XML",
    "CSV",
    "API",
    "CLI",
    "SDK",
    "UUID",
    "URL",
    "URI",
    "JWT",
    "RBAC",
    "OIDC",
    "LDAP",
    "SAML",
    "CSI",
    "CNI",
    "CRD",
    "PVC",
    # Hardware.
    "CPU",
    "GPU",
    "RAM",
    "NVIDIA",
    "Intel",
    "AMD",
    "ARM",
    "ARM64",
    "AArch64",
    "x86",
)

# The separators a term may be written with, and that are ignored when a match is
# looked up: "NVMe-oF", "NVMe oF" and "NVMeoF" all name the same term.
SEPARATOR_PATTERN = re.compile(r"([\s\-/._]+)")

# What each separator of a term accepts. A space and a hyphen stand in for each
# other and may be left out, but a slash is written as a slash: "nvme-tcp" is the
# kernel module, not a spelling of "NVMe/TCP".
SEPARATOR_CLASSES = {
    " ": r"[\s\-]?",
    "-": r"[\s\-]?",
    "_": r"[\s\-_]?",
    ".": r"\.?",
    "/": r"/",
}

REASON = "'{found}' is written '{expected}'"
PLURAL_REASON = "'{found}' has no plural, name what there is more than one of: '{expected}'"


def lookup_key(text):
    return SEPARATOR_PATTERN.sub("", text).lower()


def spelling_pattern(spelling):
    """Turn a spelling into the pattern that matches the way it is written."""
    parts = SEPARATOR_PATTERN.split(spelling)
    return "".join(
        # re.split() returns the separators it captured at the odd positions.
        SEPARATOR_CLASSES.get(part[0], re.escape(part)) if index % 2 else re.escape(part)
        for index, part in enumerate(parts)
        if part
    )


def spellings_of(term):
    """The spellings that resolve to a name of their own."""
    return (term.canonical,) + tuple(term.aliases)


def matched_spellings_of(term):
    """Everything the pattern looks for, including the spellings to correct.

    A "wrong" spelling is matched but never indexed: stripped of its separators
    it has the same key as the canonical one, so the index already resolves it.
    """
    return spellings_of(term) + tuple(term.wrong)


def build_index():
    """Map every name to the spelling it has to be written in.

    A canonical name and an alias each map to themselves, so an alias keeps its
    own spelling instead of being turned into the canonical one.
    """
    index = {}
    for term in TERMS:
        for spelling in spellings_of(term):
            key = lookup_key(spelling)
            if key in index and index[key] != spelling:
                raise ValueError(
                    f"'{spelling}' cannot be told apart from '{index[key]}'"
                )
            index[key] = spelling
    return index


TERM_INDEX = build_index()

# The plural wordings, by the canonical name they belong to.
PLURAL_INDEX = {
    lookup_key(term.canonical): term.plural for term in TERMS if term.plural
}


def build_pattern():
    """Build the alternation that matches every spelling of every term.

    The spellings are sorted by length, so that the longest one wins:
    "NVMe/TCP" is one term and not the term "NVMe" followed by the term "TCP".
    A trailing plural "s" is part of the match, so that "CRDs" is checked too.
    """
    spellings = [spelling for term in TERMS for spelling in matched_spellings_of(term)]
    alternatives = [
        spelling_pattern(spelling)
        for spelling in sorted(spellings, key=len, reverse=True)
    ]
    return re.compile(r"\b(?:" + "|".join(alternatives) + r")s?\b", re.IGNORECASE)


TERM_PATTERN = build_pattern()


def expected_spelling(found):
    """Return how a match has to be written and why, or (None, None).

    The reason differs for a plural the term does not have: there the whole
    wording changes, not just the casing of a word.
    """
    spelling = TERM_INDEX.get(lookup_key(found))
    if spelling is not None:
        return spelling, REASON

    # The match carries a plural "s" that the term itself does not.
    if found[-1:] in ("s", "S"):
        key = lookup_key(found[:-1])
        spelling = TERM_INDEX.get(key)
        if spelling is not None:
            plural = PLURAL_INDEX.get(key)
            if plural:
                return plural, PLURAL_REASON
            return spelling + "s", REASON

    return None, None


def scan_file(file_path):
    lines = read_lines(file_path)
    rel = relative_path(file_path)
    violations = []
    fixes = []

    for prose in iter_prose_lines(lines, include_code=True):
        for match in TERM_PATTERN.finditer(prose.masked):
            found = match.group(0)
            expected, reason = expected_spelling(found)
            if expected is None or found == expected:
                continue

            if is_part_of_identifier(prose.text, match.start(), match.end()):
                continue

            in_code = prose.context == CONTEXT_CODE
            violations.append(
                Violation(
                    file=rel,
                    line=prose.number,
                    column=match.start() + 1,
                    check=CHECK_NAME,
                    reason=reason.format(found=found, expected=expected),
                    excerpt=get_line_excerpt(prose.text, match.start()),
                    severity=SEVERITY_WARNING if in_code else SEVERITY_ERROR,
                )
            )
            # A code block holds commands and values. Rewriting one changes what
            # it does, so only the prose is fixed automatically.
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
        description="Check the spelling of product names, projects and acronyms."
    )
    parser.add_argument(
        "-f",
        "--fix",
        action="store_true",
        help="rewrite every reported term to its canonical spelling",
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
            "terminology check",
            files,
            f"No misspelled terms found in {{files}} file(s) ({len(TERMS)} term(s) checked).",
        )
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as error:  # noqa: BLE001
        print("Failed to run terminology check.", file=sys.stderr)
        print(error, file=sys.stderr)
        sys.exit(1)
