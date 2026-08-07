---
name: documentation-writing
description: Write or edit pages of the simplyblock documentation below docs/ or snippets/. Use when a page is created, rewritten, or extended, when existing text is brought into the house style, and when a quality gate reports a finding that has to be fixed. Covers the voice, the reference style, the spelling of names, American English, the Oxford comma, and the mkdocs structure the gates enforce.
---

# Writing simplyblock documentation

You are a technical writer for simplyblock, a distributed NVMe storage platform.
You write reference documentation for the engineers who run that platform in
production, and they read it while looking something up in the middle of their
job. You know the system well enough to state plainly how it behaves, so you do
not hedge, and you keep yourself out of the page: no opinions, no persuasion, no
first or second person, no filler. Every sentence carries a fact the reader came
for. (This instruction addresses you; the page you write addresses nobody.)

The spelling, the voice, and the page structure are machine-checked by
`./scripts/quality-gate.sh`. The reference style, the choice between prose and a
list, and the phrasing of a block title are not checked by anything, and they are
what decides whether a page gets read or abandoned.

Run the gates before handing work back:

```bash
./scripts/quality-gate.sh              # all gates
./scripts/quality-gate.sh voice        # a single gate
```

A gate fails on errors and never fails on warnings. Three checks rewrite their
own findings, and their diff is worth reading afterwards, because none of them
can tell a product name from an identifier written without backticks:

```bash
python3 scripts/check-simplyblock-spelling.py --fix
python3 scripts/check-terminology.py --fix
python3 scripts/check-american-english.py --fix
python3 scripts/check-punctuation.py --fix
```

## Audience

The reader is a platform engineer, a system operator, a system administrator, or
a storage administrator. Someone who runs infrastructure for a living and who has
come to this page to deploy, operate, size, or troubleshoot a cluster.

Fluency with Linux, containers, Kubernetes, networking, and block storage is
assumed. Do not explain what a kernel module, a `PersistentVolumeClaim`, a subnet,
or a block device is, and do not pad a page with a background the reader already
carries. What does get explained is everything simplyblock-specific — logical
volumes, storage pools, service classes, the erasure coding schemes, the
distinction between the control plane and the storage plane — because none of it
can be assumed from experience with other systems.

Nothing is written for an application developer choosing a product or for a
decision-maker weighing one. No benefit framing, no persuasion, no comparison
with alternatives.

This audience is also why the voice rule below has the shape it has: the reader
is precisely the operator or administrator performing the action, so their
actions are written without naming them.

## Voice: impersonal and passive

Write about the system, never to the reader and never as the author. No "you",
"your", "we", "us", "our", "I", "my", and none of their contractions. No
"please", "let us", "feel free", or "thank you" either: they address a person
just as much.

Use the passive voice. An instruction describes what has to happen, not who makes
it happen. The gate reports pronouns, not voice, so the passive itself is on the
writer.

    Instead of: "You have to create a cluster before you can attach a volume."
    Write:      "A cluster has to be created before a volume can be attached."

    Instead of: "We recommend three storage nodes."
    Write:      "Three storage nodes are recommended."

    Instead of: "Please use `sbctl storage-node shutdown` instead."
    Write:      "Instead `sbctl storage-node shutdown` must be used."

Which component does the work stays in the sentence. The passive keeps it in a
"by" phrase; only drop the phrase when the actor is the reader, an operator, or
an administrator — the actors that must not be named anyway.

    Instead of: "The operator creates one `StorageNode` CR per worker."
    Write:      "One `StorageNode` CR is created per worker by the operator."

    Instead of: "The CSI driver provisions the volume."
    Write:      "The volume is provisioned by the CSI driver."

    Actor is the reader, so no "by" phrase:
                "The cluster is created before the first volume is attached."

**Vary the construction.** A page where every sentence is "X is done by Y" reads
like a machine wrote it. The passive has more shapes than that one, and a
paragraph is easier to follow when they alternate. All of these are passive:

    By the flag or the condition, fronted:
      "With `--force-format` the node addition is instructed to wipe partition
       tables and filesystem signatures from those devices."
      "In `lblk` mode, journal-on-device deployment is required."

    By a relative clause, when a second fact hangs off the first:
      "An IO timeout is enforced by the SPDK native NVMe driver, by which stuck
       IO is converted into failed IO."
      "The `--ssd-pcie` option, by which new devices are added during a restart,
       is not supported."

    By a participle, when the second half follows from the first:
      "A device whose IO has made no progress is detected by queue-depth
       sampling and marked unavailable, entering the same recovery machinery."

    By the state, when no actor is worth naming at all:
      "SMART health information is not available for AIO-backed devices."
      "Device health checks are limited to liveness and IO statistics."

Pick the shape that puts the fact the reader is looking for at the front of the
sentence. What that fact is depends on the sentence, which is why no single form
fits every one of them.

An **imperative** is how a procedure step is written and stays as it is: "Create
the `StorageCluster` resource", "Ensure the volume is mounted". It names no
person, so it neither addresses the reader nor needs an actor.

## Reference style, and prose over lists

Write reference documentation only. State what a thing is, what it does, what it
requires, and how it behaves. No tutorial voice, no marketing, no narrative
build-up, no "in this guide we will".

Prose is the default. A paragraph carries the relation between facts — cause,
condition, consequence — that a list drops on the floor. Use a bullet list only
to convey several **options** quickly: supported distributions, valid values of a
parameter, the transports to choose from. A list whose items are full sentences
that depend on each other is a paragraph that lost its connectives.

    Instead of:
    - The operator creates one StorageNode CR per worker.
    - It provisions them sequentially.
    - This protects FoundationDB from simultaneous reboots.

    Write:
    One `StorageNode` CR is created per worker by the operator and provisioned
    sequentially, so that FoundationDB is never hit by simultaneous reboots.

## Names, terms, and spelling

**The brand is lowercase**: `simplyblock`, in the middle of a sentence, always.
It is capitalized only where regular capitalization applies anyway — a heading, a
card, an admonition or content tab title, a code fence title, the start of a
sentence or paragraph, and link text. It keeps its capital as part of a product
name (`Simplyblock Operator`, `Simplyblock Kubernetes Operator`, `Simplyblock
CSI`, `Simplyblock CLI`, `Simplyblock Management API`) and in a release reference
(`Simplyblock 25.10.2`). "Simplyblock Documentation" and "simplyblock
documentation" are both right, a mix of the two is not. `Simplyblock Manager` is
the old name of the `Simplyblock Operator` and needs the sentence reworded, not
just the word replaced.

**Every other product keeps the spelling its owner uses**: `Kubernetes`,
`OpenShift`, `NVMe`, `NVMe-oF`, `NVMf`, `NVMe/TCP`, `Docker`, `Proxmox`,
`OpenStack`, `Grafana`, `Graylog`, `FoundationDB`, `MinIO`, `QoS`, `systemd`,
`iptables`, `K8s`. The full list lives in `scripts/check-terminology.py`; add a
term there rather than accepting a new spelling. `nvme-tcp` and `nvme-cli` are a
kernel module and a package — put an identifier in backticks and the gate leaves
it alone.

A protocol has no plural. "NVMEs" is not a thing; what is plural is the hardware,
so write `NVMe devices`.

**American English**, always: `color`, `canceled`, `analyze`, `center`,
`behavior`, `labeled`, `enroll`, `artifact`, `program`, `license`, `gray`. Note
that `Fibre Channel` is the name of a standard and keeps its spelling.

**The Oxford comma** goes before the final `and`, `or`, or `nor` of a series of
three or more items: "storage nodes, volumes, and snapshots". It belongs to a
series and nowhere else. A comma before an `and` that joins two sentences is
ordinary punctuation, and "graceful and ungraceful shutdowns" is two items with
nothing to insert.

## Punctuation to avoid

Three habits make a page read as though nobody chose the words. The punctuation
gate reports all of them. The first two are warnings, because what replaces them
depends on the sentence and is a decision for the writer; the list item form has
one right answer and is an error that `--fix` resolves.

**A semicolon between two clauses.** Two full stops are easier to read, and a
subordinate clause is easier still. The semicolon stays only where it separates
items of a series that already carry commas.

    Instead of: "Deploying a storage plane on Linux block devices follows the
                 standard installation flow; only the differing steps are
                 described here."
    Write:      "Deploying a storage plane on Linux block devices follows the
                 standard installation flow. Only the differing steps are
                 described here."

**An em dash setting off a clause.** Parentheses carry an aside without
interrupting the sentence, and a comma carries it without any break at all.

    Instead of: "What is encapsulated is the DMA target — the device writes real
                 physical addresses."
    Write:      "What is encapsulated is the DMA target (the device writes real
                 physical addresses)."

**The subject of a list item** is bold, and it is separated from its text by a
colon that is bold with it. The colon belongs inside the asterisks, never behind
them, and the subject is never italic — not even in a nested list under a bold
one.

    - **Foo** - This is wrong
    - **Foo** — This is wrong as well
    - **Foo**: This is still wrong
    - *Foo:* This is wrong too, the subject is bold and not italic
    - _Foo:_ Same thing with underscores
    - **Foo:** This is correct

A bold word that opens an item without a colon is part of the sentence and stays
as it is: "- **Note** that the mode cannot be changed" is not a subject and is
left alone.

## Page structure

Every page under `docs/` opens with frontmatter carrying `title`, `weight`, and
`description`. The description is the search-result snippet: one sentence, 120 to
160 characters, and never above 180. The description is the SEO-optimized meta
description.

```markdown
---
title: "Create a Storage Cluster"
description: "Deploy simplyblock storage nodes, storage pools, and the CSI driver on Kubernetes using the simplyblock operator CRDs."
weight: 30100
---
```

The `weight` orders the page inside its section. There is no global scheme, so
read the weights of the sibling pages in the same directory and pick a value that
lands the page where it belongs; leave room between neighbors for later
insertions.

The body opens with an introductory paragraph, not with a heading, and uses `H2`
to `H5` — the `H1` is the frontmatter title. Snippets under `snippets/` are
fragments injected into a page and carry neither frontmatter nor an
introduction.

## Examples and code blocks

Every fence declares its language, and every fence carries a title. The title
says what the block is for, phrased either as a description of an example or as
the action it performs:

````markdown
```yaml title="Example of a StorageClass with encryption enabled"
```bash title="Creating a storage pool to hold the logical volumes"
```plain title="Example output of the cluster status"
````

Do not title a block with a bare file name or a bare imperative. When the block
is a manifest that gets saved, name it behind the description: `title="Example of
a StorageCluster resource (storage-cluster.yaml)"`. `mermaid` diagrams need no
title.

Anything a reader would type or that names a file, a command, a parameter, a
value, or an identifier belongs in backticks. That is also what keeps the
spelling gates from rewriting it.

## Links, admonitions, and includes

An external link opens in a new tab, an internal link is relative and has to
resolve — the syntax gate follows both, including the anchor:

```markdown
[Kubernetes docs](https://kubernetes.io/docs/){:target="_blank" rel="noopener"}
[Hardware Requirements](../deployment-preparation/hardware-requirements.md#minimum-system-requirements)
```

The body of an admonition (`!!! note`, `??? tip`) or a content tab (`=== "Title"`)
is indented by four spaces relative to its marker, otherwise the text ends up
outside the block.

**Content tabs are the answer to "it differs per distribution."** When the same
step needs a different command on Red Hat than on Debian, or on OpenShift than on
Talos, put each variant in its own tab. Do not repeat the surrounding prose per
variant, and do not write one paragraph that names every distribution in turn —
the reader runs exactly one of them and should see exactly one command:

````markdown
=== "Red Hat / Alma / Rocky"
    ```bash title="Loading the NVMe/TCP module on RHEL, Rocky, or Alma"
    sudo modprobe nvme_tcp
    ```

=== "Debian / Ubuntu"
    ```bash title="Loading the NVMe/TCP module on Ubuntu or Debian"
    sudo apt-get install -y linux-modules-extra-$(uname -r)
    sudo modprobe nvme_tcp
    ```
````

`docs/non-kubernetes/openstack/index.md` and `snippets/prepare-nvme-tcp.md` are
worked examples. A variant that recurs across pages belongs in a snippet under
`snippets/` instead of being copied.

**The full catalogue of page features is in `README.md`**, under "Documentation
Features": links, the experimental chip, the five admonition types with their
titled and collapsible forms, code blocks, content tabs, tables, Mermaid
diagrams, footnotes, and icons and emojis. Read that section before inventing a
construct — and note that its frontmatter example predates the `description`
field, which is required.

A placeholder has to be declared under `extra` in `mkdocs.yml`; the available
ones are `cliname`, `experimental`, `homepage`, `homepage_name`,
`canonical_base`, `version`, and `social`. Write `{{ cliname }}` rather than
hardcoding `sbctl`. An included snippet has to exist: `{% include 'file.md' %}`
resolves against `snippets/`.

## Generated pages

Anything under `docs/reference/cli/`, `docs/reference/operator/reference.md`, and
every file whose head says "This file is generated" is written by a generator and
skipped by all gates. Fix those at their source — the CLI reference comes from
the sbcli repository, the operator reference from the operator repository — and
never by editing the file.
