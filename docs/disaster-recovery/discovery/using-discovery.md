---
title: "Using Discovery"
description: "Run discovery, read the graph and candidates of a site, review a bundle, approve it through a pull request or in the Control Center, and roll it back."
weight: 10282
---

Discovery is used from the Control Center (**Disaster Recovery → Discovery** and **Disaster Recovery → Proposals**)
or with `kubectl` on the hub. Graphs are cluster-scoped. Bundles live in the Ramen operations namespace
(`ramen-ops`), next to the ProtectedApplications they propose.

## Running Discovery

With `autoRules` enabled, dr-hub rebuilds a site's graph whenever the site's report changes and writes bundles
without a request. A DiscoveryRun forces a pass, for a whole site or a few namespaces:

```yaml title="A discovery run for one namespace"
apiVersion: dr.simplyblock.io/v1alpha1
kind: DiscoveryRun
metadata:
  name: site-a-shop
  namespace: ramen-ops
spec:
  mode: Rules
  scope:
    site: site-a
    namespaces: [shop]
```

The run's status shows its phase (`Pending`, `Running`, `Succeeded`, `Failed`), its progress and the bundles it
produced. A run scoped to namespaces never marks bundles of other namespaces as stale. Runs are started in the
Control Center with **Run discovery**. The mode `AI` is planned and not implemented yet.

## Reading the Graph

```bash title="Listing the discovery graphs"
kubectl get discoverygraphs
```

```plain title="Example output of the graph listing"
NAME     NODES   EDGES   CANDIDATES   BUILT
site-a   212     540     6            2m
```

The DiscoveryGraph of a site lists its application candidates in `status.candidates`: members, namespaces, a score
and, when an existing ProtectedApplication already covers most of the candidate's PVCs, the adopted application.
Connections between candidates are listed in `status.interApp`. The full graph (nodes, edges, and evidence) is stored
in compressed ConfigMap shards in the namespace of dr-hub.

In the Control Center, the site page shows the candidates and a graph view of one candidate or namespace. Edges can
be filtered by type: ownership, volume mounts, Service selection, configuration references, observed connections and
network attachments. Selecting a node or an edge shows its evidence.

## Reviewing a Bundle

```bash title="Listing the bundles"
kubectl -n ramen-ops get drproposals
```

```plain title="Example output of the bundle listing"
NAME                  SCOPE         SITE     SOURCE   PHASE      AGE
shop-7f3c1a           Application   site-a   rules    PROpened   5m
rp-site-a-to-site-b   RecoveryPlan  site-a   rules    Proposed   5m
```

A bundle shows:

- **Summary and confidence:** What the bundle proposes and how sure the proposer is (0 to 1000, shown as a percentage).
- **Objects:** The proposed ProtectedApplication, RecoveryPlan, SiteProfile, DHCPServer, or DRPath, each with the
  evidence and confidence of every field.
- **Diff:** The difference to the live objects. A bundle for an adopted application only contains what changes.
- **Labels:** The labels to set on PVCs, VMs, and workloads, with their effect. A consistency-group label on a PVC that
  is already bound is listed as a late join. Such volumes are listed under migrations and join the group only once
  consistency groups can be formed after volume creation. A bundle never migrates a volume.
- **Questions:** What the proposer could not decide, with the options to choose from. Blocking questions must be
  answered before the bundle can be approved.
- **Dry run:** The readiness checks evaluated against the proposed objects and labels. Checks that need live state
  report `NotApplicable`. A blocking failure prevents approval.

## Approval Through a Pull Request

When a GitOps target is configured, dr-hub opens a pull request for every valid bundle. The bundle's phase becomes
`PROpened`, and `status.gitOps` holds the branch and the pull request link.

- **Branch and files:** The branch is `dr/<site>/<bundle>`. The files are written below the configured path, one
  directory per application (`applications/<key>/`) or per site (`sites/<site>/`), with a `BUNDLE.md` and a generated
  `kustomization.yaml`.
- **Answering questions:** Questions appear as a task list in the pull request description. A question is answered by
  checking exactly one of its options. dr-hub reads the answers back into `status.answers`. Checking two options of one
  question is reported as a conflict.
- **Review changes:** Reviewers may edit the generated files on the branch. A later revision of the bundle becomes a
  new commit on the same branch, never a force-push.
- **Merging:** Merging approves the bundle. The merging user is recorded as the approver, and the phase becomes
  `Merged`. Once the hub's GitOps tool has applied the objects, the phase becomes `Applied`. If the merged objects do
  not appear within 30 minutes, the condition `SyncPending` is set.
- **Rejecting:** Closing the pull request without a merge, or rejecting the bundle in the Control Center with a reason,
  sets the phase `Rejected`.
- **Rolling back:** Reverting the merge commit removes the objects. dr-hub detects this and sets the phase
  `RolledBack`.

## Approval Without GitOps

Without a GitOps target, the Control Center offers **Approve** and **Roll back** to users with the `dr-admin` role.

- **Approve:** Allowed for a valid bundle whose blocking questions are answered and whose dry run has no blocking
  failure. dr-hub applies the objects with server-side apply and keeps the previous state in the ConfigMap
  `dr-bundle-<name>-previous`.
- **Answers:** Questions are answered in the Control Center.
- **Roll back:** Restores the previous state of the objects.

## Labels and Their Rollback

The labels of a bundle are applied on the site by dr-agent through LabelRequests, named `bundle-<bundle>-<site>`.
Only the allow-listed label keys can be set (see [Reference](reference.md#label-keys)). The LabelRequests of a bundle
are kept. Deleting one restores the previous label values and removes labels that did not exist before.

Single labels are also set with **Label for DR** in the Kubernetes section of the Control Center.

## Recovery Plans

A RecoveryPlan bundle orders the applications of one DR path in priority lanes, with dependencies first. It names the
application bundles it depends on. After its merge, it waits in the phase `WaitingForApplications` until all of them
are `Applied`, and is then applied itself. Cyclic dependencies become a question.

## Changes Over Time

- **Superseded:** When a site changes, the rule engine writes a new bundle. The new bundle supersedes the open one,
  and the old pull request is closed unless the new bundle takes over its branch.
- **Stale:** A bundle whose candidate disappears from the graph becomes `Stale`.
- **No change:** No bundle is written when the live objects already match.
