---
name: release-notes
description: Write, extend, or correct a release notes page under docs/release-notes/. Use when a new simplyblock release is prepared, when the entries of a release note are collected from the source repositories, or when an existing release note is brought into the house style. Covers the split into Simplyblock (Control Plane, Storage Plane) and Kubernetes (Operator, CSI Driver), the wording of a feature, a fix, and an important change, the harvest from a git range, and the quality gates the page has to pass.
---

# Writing simplyblock release notes

A release notes page answers three questions for an operator who is deciding
whether and how to upgrade: what changed, which component it changed in, and
what has to be done about it. It is scanned, not read, and it is scanned under
time pressure. Every entry is therefore one self-contained sentence or two, and
it names the resource, the field, or the command the reader will search for.

Everything about voice, spelling, punctuation, American English, and page
structure comes from the `documentation-writing` skill. **Load that skill first**
and follow it. This skill adds only what is specific to a release note: the two
component sections, the wording of an entry, the harvest from the source
repositories, and the gate run against the generated file.

## Ask before writing

Five inputs cannot be guessed, and a wrong guess produces a page full of
plausible entries that belong to another release. They are collected with
`AskUserQuestion` before any git command is run, in two rounds, because one call
carries at most four questions.

The first round settles what the page is:

1. **Version.** The version as it is written on the page, including a suffix such
   as `-PRE`. It decides the file name, the `title`, and the `weight`. Offer the
   version that follows the newest existing page and the newest tag of the
   source repositories as options, and take a typed answer verbatim. Before
   continuing, check whether `docs/release-notes/` already carries the page for
   that version. If it does, the page is extended, and nothing already on it is
   rewritten without saying so.
2. **Section.** `Simplyblock` (Control Plane and Storage Plane), `Kubernetes`
   (Operator and CSI Driver), or both. Only the requested section is filled in.
   The other one keeps its headings and carries a placeholder entry.

The second round settles where the entries come from, once the section is known:

3. **Source location.** The path of the checkout the entries are harvested from,
   one per component in scope. It is never assumed and never guessed from a
   previous session: the answer is typed, and the pinned checkouts of the
   documentation repository are offered only as a fallback, with the caveat
   below. A supplied path is confirmed to be the expected repository before it
   is used.
4. **Previous reference.** The tag or the branch the previous release was cut
   from. This is the lower end of the git range.
5. **Current reference.** The tag or the branch this release is cut from,
   usually the release branch of the version being written. This is the upper
   end.

Echo the resolved range back before harvesting, as `<previous>..<current>` per
repository, together with the commit count. A range that returns thousands of
commits or none at all is the wrong range, and the answer to that is another
question, not a guess.

### Where the code lives

| Component     | Repository                | Path within the repository                                              |
|---------------|---------------------------|-------------------------------------------------------------------------|
| Control Plane | `sbcli`                   | `simplyblock_core/`, `simplyblock_web/`, `simplyblock_cli/` for the CLI |
| Storage Plane | The simplyblock SPDK fork | The whole repository                                                    |
| Operator      | `simplyblock-operator`    | `operator/`, `helm-charts/`                                             |
| CSI Driver    | `simplyblock-operator`    | `csi-driver/`, `atlas-lib/`, `shared/`                                  |

**Where those repositories are checked out is never assumed.** It differs per
machine, so the path is asked for, one per component in scope, and the answer is
verified before it is used:

```bash title="Confirming that a supplied path is the expected repository"
git -C <path> remote -v
git -C <path> rev-parse --abbrev-ref HEAD
```

The documentation repository does keep its own checkouts, at `scripts/sbcli-repo`
and `scripts/operator-repo`, created and updated by
`./doc-builder update-repositories` and pinned through `scripts/sbcli.lock` and
`scripts/operator.lock`. They can be offered as a fallback when no path is
supplied, but they exist to generate the CLI and the operator reference, and
**without a lock file they sit on `main`**. That makes them the wrong source for
a release note and for verifying a page, since `main` carries the work of the
*next* release. Run `git fetch --tags` before a range is resolved against them.

No checkout of the SPDK fork is managed by the documentation repository, so its
path always has to be supplied.

**The release branch is the source of truth.** A release is cut on a branch, and
what is on `main` may never reach it. The two diverge in both directions, so
neither `git log` nor a field lookup on `main` proves anything about the release.

**The two repositories name that branch differently**, and neither convention
carries over to the other:

| Repository                          | Branch                                | Example          |
|-------------------------------------|---------------------------------------|------------------|
| `simplyblock-operator` (and the CSI driver) | `release/<major>.<minor>.<patch>` | `release/26.3.0` |
| `sbcli`                             | `R<major>.<minor>`                    | `R26.3`          |

An `sbcli` branch also takes a suffix or a patch level of its own, as in
`R26.2-PRE` and `R25.10-Hotfix`, so the branch is listed rather than constructed
from the version. Resolve it per repository, then verify every claim against it:

```bash title="Listing the release branches of a repository"
git -C <repo> branch -a | grep -iE 'release/|/R[0-9]+\.'
```

```bash title="Measuring how far the release branch and main have diverged"
git -C <repo> rev-list --count <release-branch>..main   # on main only
git -C <repo> rev-list --count main..<release-branch>   # on the branch only
```

## The page

The file name is the version with every separator turned into a hyphen:
`26-3.md` for 26.3, `25-10-5.md` for 25.10.5. The `title` is the version exactly
as it is written elsewhere, including a suffix such as `26.2-PRE`. The suffix
stays out of the file name, which is why `26-2.md` carries the title
`26.2-PRE`.

The `weight` values of the section descend, so the newest page carries the
lowest number. Take the current minimum and subtract one:

```bash title="Finding the weight for a new release notes page"
grep -h "^weight:" docs/release-notes/[0-9]*.md | awk '{print $2}' | sort -n | head -1
```

The order of the headings is fixed, and a heading is never dropped because it
has no content:

```markdown title="Skeleton of a release notes page"
---
title: "26.3"
description: "One sentence, 120 to 160 characters, naming the release and the components it covers."
weight: 999987
---

Simplyblock is happy to release Simplyblock 26.3. ...

## Simplyblock

### New Features

### Fixes

## Kubernetes

### New Features

### Fixes

## Important Changes

## Upgrade Considerations

## Known Issues

## Features to Expect with Next Major Release
```

The subsections are named `New Features` and `Fixes`, not `Features` and
`Bugfixes`, because every existing page in the section uses those two names. An
empty subsection carries one entry instead of nothing: `No major fixes.` or `No
changes in this release.`

While entries are still being collected, the page opens with a draft warning
directly under the introduction, so that an unfinished page cannot ship
unnoticed:

```markdown title="Marking a release note that is still being collected"
!!! warning "Draft"
    This page is a work in progress. The control plane and storage plane
    entries, the upgrade path, and the known issues are not final yet.
```

The placeholder of a section that is not in scope names the source it still has
to be harvested from, so the next writer does not have to reconstruct it:

```markdown title="Placeholder for a section that is not in scope yet"
- **Control Plane:** TODO, to be collected from the `sbcli` changes since 26.2.
```

## The two sections and their component prefixes

The top-level split follows the release boundary, not the feature area.
`## Simplyblock` carries everything that ships with the control plane and the
storage plane and therefore applies to every deployment. `## Kubernetes` carries
everything that ships with the Simplyblock Operator and Simplyblock CSI and
therefore applies to a Kubernetes-based deployment only. Each section opens with
one sentence stating that scope.

Every entry starts with its component as a bold subject, the colon inside the
asterisks:

| Section     | Prefix                         | Used for                                       |
|-------------|--------------------------------|------------------------------------------------|
| Simplyblock | `**Control Plane:**`           | The control plane, its API, and the CLI        |
| Simplyblock | `**Storage Plane:**`           | SPDK, the data path, and the journal           |
| Simplyblock | `**General:**`                 | Both planes, the images, or the base OS        |
| Kubernetes  | `**Operator:**`                | The operator, its resources, and the charts    |
| Kubernetes  | `**CSI Driver:**`              | Provisioning, attaching, and mounting a volume |
| Kubernetes  | `**Operator and CSI Driver:**` | A change that lands in both                    |

A change that spans both sections is written once per section, from the angle of
that section, and not copied verbatim.

## Wording of an entry

An entry opens with what happened to the product, in the past tense for a
delivered change and in the present tense for a statement of the new behavior.
It never opens with the version, the ticket, or the team.

**A feature** opens with `Added`, or states the new behavior directly:

    - **Operator:** Added support for failure domains. The mode is enabled
      through `spec.enableFailureDomains` on the `StorageCluster`, and workers
      are assigned to a domain through the `StorageNodeSet`.
    - **Operator:** Added the `StorageClusterOps` resource, by which cluster
      operations are decoupled from the `StorageCluster` reconciler.
    - **Control Plane:** The command `{{ cliname }} storage-node add-node` now
      supports the `--nvme-names` flag to specify the NVMe device names.
    - **CSI Driver:** The presence of a device is registered when the volume is
      connected, instead of only by polling.

The first sentence carries the feature. Whatever a reader needs in order to use
it, the field, the resource, or the flag, follows in the next one or two
sentences. Past three sentences, the entry belongs on a documentation page and
the entry links to it instead.

**A fix** opens with `Fixed`, or with `Improved` when nothing was broken and the
behavior became more reliable:

    - **CSI Driver:** Fixed the connection of a volume in a cluster with more
      than one storage pool.
    - **Control Plane:** Fixed an issue where failed devices could not be added
      back to the cluster.
    - **Storage Plane:** Improved the reliability of the graceful startup and
      shutdown of the storage plane.

A fix is written as the symptom the operator saw, not as the code that changed.
`Fixed an issue where ...` is the form for a symptom that needs a condition to
be stated. Where the symptom fits into a noun phrase, `Fixed the ...` is
shorter and preferred.

**A dependency or image change** opens with `Updated`:

    - **Operator and CSI Driver:** Updated the container base images and the Go
      dependencies to resolve open CVEs.

**An important change** goes under `## Important Changes` and is written in the
present tense as a statement of the new state, with no component prefix, because
the whole entry is about a name or a contract:

    - The `Pool` resource is renamed to `StoragePool`.
    - The field `maxLogicalVolumeCount` is renamed to `maxSubsystemCount`, and
      the field `corePercentage` is removed.
    - The field `unpinBeforeDrain` is removed. A pinned volume has to be
      unpinned manually before its storage node is drained.

Anything that breaks an existing manifest, script, or habit belongs here: a
renamed or removed resource, field, flag, or annotation, a changed default, and
a deprecation. An entry that requires an action states that action in its second
sentence. The same change is not repeated under `New Features`.

`## Upgrade Considerations` names the releases an upgrade is supported from, and
nothing else. `## Known Issues` carries an issue only after it has been
confirmed to still apply. `## Features to Expect with Next Major Release` is
carried over from the previous page with every delivered item removed.

**What never appears in an entry:** a commit hash, a pull request number, a
branch name, a file path in the source, an internal type or function name, a
contributor, a date, or a benchmark number. A commit subject is a lead, never a
sentence to paste.

## Harvesting the entries

The harvest turns a git range into topics, not into a bullet per commit. Several
commits on one feature are one entry, and a feature is worth one entry no matter
how long it took to land.

```bash title="Listing the candidate commits of a release range"
git -C <repo> log --format='%s' <previous>..<current> \
    | sed -E 's/ \(#[0-9]+\)$//' \
    | grep -iE '^(feat|fix)' \
    | sort -u
```

Drop everything with no effect a reader can observe: `chore`, `lint`, `test`,
`ci`, `docs`, a refactor with no behavior change, a dependency bump with no CVE
behind it, and a fix to a change that never shipped. What remains is grouped by
topic, and each group is turned into one entry.

Four traps are worth a deliberate check on every release:

- **A range is reachability, not time.** `git log A..B` lists a commit that was
  authored long before `A` but merged after it. An author date is no evidence
  that a change belongs to this release.
- **A patch release may already carry the feature.** Check it before deciding:
  `git merge-base --is-ancestor <commit> <patch-tag>` succeeds when the change
  already shipped in that tag. Whether such a change is listed again in the next
  major release note is an editorial decision, so state which boundary was drawn
  and why.
- **A commit subject is not the user-facing name.** Verify the name in the
  source, and read it *at the release branch* with
  `git show <release-branch>:<path>` rather than from the working tree, which may
  sit on another branch. For a resource or a field, read
  `operator/api/v1alpha1/*_types.go`; for a command or a flag, read
  `simplyblock_cli/`; for an annotation, read the constants it is declared in. A
  field removed from a spec often survives in the status, which changes the
  wording of the entry.
- **A new, renamed, or removed resource is visible in the tree.** Diff the type
  files of the two references, which is faster and more reliable than reading
  subjects:

```bash title="Finding the resources added, renamed, or removed in a range"
git -C <repo> ls-tree -r --name-only <previous> | grep '_types.go$' | sed 's|.*/||' | sort > /tmp/before.txt
git -C <repo> ls-tree -r --name-only <current>  | grep '_types.go$' | sed 's|.*/||' | sort > /tmp/after.txt
diff /tmp/before.txt /tmp/after.txt
```

Finally, read the previous release notes page end to end. Nothing it already
lists is repeated, its `Features to Expect with Next Major Release` list is the
shortlist of headline entries for this page, and its `Known Issues` are re-checked
rather than copied.

## Testing the generated page

The page is not finished until all seven gates run clean **on the new file**,
with no warnings, not only with no errors. The gates are `spelling`,
`terminology`, `american`, `prose`, `voice`, `punctuation`, and `syntax`, and the
script runs all of them by default:

```bash title="Running the quality gates against the new release notes page"
./scripts/quality-gate.sh 2>&1 | grep -E '26-3|^All'
```

The filter is what makes the run a test of this page. The section carries pages
that predate the gates, so an unfiltered run ends in warnings that belong to
other files, and the new page hides in them. A single gate is run by name while
a finding is worked on:

```bash title="Running a single gate while a finding is worked on"
./scripts/quality-gate.sh voice
```

The rewriting checks are run first, and their diff is read afterward, because
none of them can tell a product name from an identifier written without
backticks:

```bash title="Letting the checks fix their own findings"
python3 scripts/check-simplyblock-spelling.py --fix
python3 scripts/check-terminology.py --fix
python3 scripts/check-american-english.py --fix
python3 scripts/check-punctuation.py --fix
python3 scripts/check-prose.py --fix
python3 scripts/check-mkdocs-syntax.py --fix
```

Four findings are specific to a release note and are worth checking by hand:

- **A wrapped product name.** A line break inside `Simplyblock Operator` or
  `Simplyblock CSI` leaves `Simplyblock` alone at the end of a line, and the
  spelling gate reports it as a brand that should be lowercase. Reflow the
  paragraph instead of lowercasing the word.
- **An untitled code fence.** The example of a workaround under `Known Issues`
  needs a language and a title like every other fence.
- **The description length.** One sentence between 120 and 160 characters,
  naming the release and the components the page covers.
- **The bold subject.** The colon sits inside the asterisks: `**Operator:**`,
  never `**Operator**:`.

The opening word of every entry is checked separately, since no gate knows about
it. The command below prints every entry of `New Features` and `Fixes` that does
not open the house way. It matches on the bold prefix, so the entries of
`Important Changes` and `Known Issues`, which carry none, are left out:

```bash title="Listing the feature and fix entries that do not open the house way"
grep -nE '^- \*\*' docs/release-notes/26-3.md \
    | grep -vE ':- \*\*[A-Za-z ]+:\*\* (Added|Fixed|Improved|Updated|The|TODO)'
```

An entry it reports is either rewritten to open with one of those words or, when
it states a new behavior, reworded to start with `The`.

## The last pass

Read the finished page once, from the introduction to the last entry, as an
operator who has to decide whether to upgrade tonight. Three questions decide
whether the page is any good, and none of them is machine-checkable:

1. Does every entry name the thing the reader would search for, in backticks?
2. Does every breaking change say what has to be done, and is it under
   `Important Changes` rather than buried in a feature entry?
3. Is anything on the page unverified? An unverified entry is either verified in
   the source or moved into the draft warning. It is never softened into a vague
   sentence and left in place.
