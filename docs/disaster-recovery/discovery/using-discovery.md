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

```yaml title="Example of a discovery run for one namespace"
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

The run's status shows its phase (`Pending`, `Running`, `Succeeded`, `Failed`), its progress, and the bundles it
produced. A run scoped to namespaces never marks bundles of other namespaces as stale. Runs are started in the
Control Center with **Run discovery**. The mode `AI` is planned and not implemented yet.

A run fails, with the reason in its condition `Completed`, when discovery is disabled (`DiscoveryDisabled`), when the
site's dr-agent has not reported yet (`NotReported`), or when building the graph or the bundles fails (`BuildFailed`,
`ProposeFailed`). While the site's report is incomplete, the run waits in `Running`.

## Reading the Graph

```bash title="Listing the discovery graphs"
kubectl get discoverygraphs
```

```plain title="Example output of the graph listing"
NAME     NODES   EDGES   CANDIDATES   BUILT
site-a   212     540     6            2m
```

The DiscoveryGraph of a site lists its application candidates in `status.candidates`: members, namespaces, a score,
and, when an existing ProtectedApplication already covers most of the candidate's PVCs, the adopted application.
Connections between candidates are listed in `status.interApp`. The full graph (nodes, edges, and evidence) is stored
in compressed ConfigMap shards `dr-graph-<site>-<n>` in the namespace of dr-hub.

Groups of objects without a PVC or VM are not proposed on their own, because there is nothing to replicate. When
their namespace holds exactly one candidate, they join it, for example, a tools Deployment next to a database.
Otherwise, they stay in the graph as services that other candidates use.

In the Control Center, the site page shows the candidates and a graph view of one candidate or namespace. Edges can
be filtered by type: ownership, volume mounts, Service selection, configuration references, observed connections, and
network attachments. Selecting a node or an edge shows its evidence.

## How the Rule Engine Builds a Bundle

The rule engine is deterministic: the same graph and DR objects give the same bundles, names included.

- **Plan and target:** The ProtectionPlan whose sites include the candidate's site, and the `to` site of the DR path
  that starts there. Several plans or several paths become a blocking question. A site without a plan or without a
  path gets no bundle.
- **PVC selector:** An `app` label that every member PVC already carries and no other PVC of the namespaces has.
  Otherwise, the PVCs get the label `app=<application>`. An adopted application keeps its own selector and every
  field the rules do not derive.
- **Consistency group:** When the plan has `consistencyGroups: Enabled` and the application has two or more PVCs, the
  bound PVCs are listed under migrations. A bundle never labels or migrates them (see
  [Reviewing a Bundle](#reviewing-a-bundle)).
- **Tiers:** A `config` tier first, then a `tools` tier when the application has a tools pod, then one tier per layer
  of the dependency graph, named after the dominant role (`db`, `queue`, `cache`, `app`, or `web`, otherwise
  `tier-<n>`), and a last tier `rest` for everything no tier selects. A workload comes after everything it uses.
  Without any dependency evidence, data services come first. Workloads that depend on each other share a tier, and
  the bundle asks about them.
- **Tier labels:** The members of a tier get the label `dr.simplyblock.io/tier=<tier>`. Workloads outside the label
  allow-list, such as DaemonSets and pods without a controller, are restored in the last tier, and the bundle asks.
- **Ready gates:** `vmRunning`, `deploymentsReady`, or `statefulSetsReady`, by the kinds in the tier. For every
  Service of a tier that a later tier uses, an `exec` gate runs `nc -z -w 3 <service> <port>` in the tools pod, with a
  timeout of 900 seconds for databases and queues and 300 seconds otherwise.
- **Health probes:** HTTP on the Services of the front tier with a web port (named `http*`, or 80, 443, 3000, 8000,
  8080, or 8443), TCP on its other Services.
- **Site mappings:** Networks that the site's VMs use and no SiteProfile role binds become a SiteMapping bundle per
  site: a role per network, the counterpart network on the plan's other sites, the guest subnet, reserved host IDs,
  and the DHCP server. A DHCP server on a test network is never proposed. VMs without a pinned MAC address are a
  blocking question.

A tools pod is a Deployment without volumes that no Service selects and no member uses, that names no endpoint in its
environment, arguments, or ConfigMaps, and that either only waits (for example, `sleep infinity`) or runs a toolbox
image (such as busybox, alpine, or netshoot) without steady traffic of its own. A workload of that shape that
references an endpoint or has steady traffic is an application worker and is restored after what it uses. When
neither is clear, the workload stays with the application and the bundle asks (`helper-or-worker-<n>`). Without a
tools pod, the bundle has no TCP gates and asks whether to add one (`tools-pod`).

The bundle's confidence is 0.4 times the candidate's score plus 0.6 times the mean confidence of its fields, minus
0.1 per blocking question.

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
- **Diff:** The difference from the live objects. A bundle for an adopted application only contains what changes.
- **Labels:** The labels to set on PVCs, VMs, and workloads, with their effect.
- **Migrations:** The bound PVCs that would join the application's consistency group. A consistency group is fixed
  when a volume is created, so these volumes join only once consistency groups can be formed after volume creation.
  The list is informational. A bundle never migrates a volume.
- **Questions:** What the proposer could not decide, with the options to choose from. Blocking questions must be
  answered before the bundle can be approved in the Control Center.
- **Dry run:** The readiness checks evaluated against the proposed objects and labels. The checks that need live
  state (`protection-bound`, `move-settled`, `ramen-healthy`, `storage-replicating`, `test-recent`, and
  `artifacts-current`) report `NotApplicable` with the reason `DryRun`. A blocking failure sets the condition
  `Valid=False` and prevents approval.

An answer is recorded in `status.answers`. It does not change the proposed objects. A different choice is made by
editing the generated files on the pull request's branch, or by changing the object after it is applied.

## Approval Through a Pull Request

When a GitOps target is configured, dr-hub opens a pull request for every valid bundle. The bundle's phase becomes
`PROpened`, and `status.gitOps` holds the branch and the pull request link. For a bundle that is not valid, a pull
request is opened on request (**Open pull request** in the Control Center, or the request `open-pr`), so that
reviewers can fix it on the branch.

- **Branch and files:** The branch is `dr/<site>/<application>`, `dr/<site>/sitemap`, or
  `dr/<site>/<recovery plan>`. The files are written below the configured path: `applications/<application>/`
  (`protectedapplication.yaml`, `labels-<site>.yaml`), `sites/<site>/` (`siteprofile.yaml`, `dhcpservers/`),
  `paths/<path>.yaml`, and `recoveryplans/<plan>.yaml`. Each bundle directory gets a `BUNDLE.md` with the pull request
  description, and the path a generated `kustomization.yaml` that lists every generated file.
- **Generated files:** Every file dr-hub writes starts with `# generated by dr-hub bundle <name>`. Files without that
  header are never overwritten. A file in the way, or a generated file a reviewer edited, blocks the push and sets the
  condition `Conflict`.
- **Pull request:** The title is `[DR] <application> on <site>: <summary>`. The description lists the summary, the
  questions, the proposed values with their confidence and evidence, the labels, the migrations, the bundles a
  recovery plan waits for, and the dry run. The commit carries the trailers `DR-Bundle`, `DR-Source`, and
  `DR-Confidence`.
- **Answering questions:** Questions appear as a task list in the pull request description. A question is answered by
  checking exactly one of its options. dr-hub reads the answers back into `status.answers`. Checking two options of
  one question sets the condition `Answers=False` and leaves the question unanswered.
- **Review changes:** Reviewers may edit the generated files on the branch. A later revision of the bundle becomes a
  new commit on the same branch, never a force-push.
- **Merging:** Merging approves the bundle. The merging user is recorded as the approver, and the phase becomes
  `Merged`. Once the hub's GitOps tool has applied the objects, the phase becomes `Applied`. If the merged objects do
  not appear within 30 minutes, the condition `SyncPending` is set. dr-hub does not block a merge with open blocking
  questions or a failed dry run. Branch protection and the review do.
- **Rejecting:** Closing the pull request without a merge, or rejecting the bundle in the Control Center with a reason,
  sets the phase `Rejected`.
- **Rolling back:** Reverting the merge commit removes the objects. dr-hub detects this and sets the phase
  `RolledBack`.
- **Provider errors:** A failing Git provider, for example, a missing token, sets the condition `GitOpsError`.
  dr-hub retries every five minutes.

## Approval Without GitOps

Without a GitOps target, the Control Center offers **Approve** and **Roll back** to users with the `dr-admin` role.

- **Approve:** Allowed for a `Proposed` bundle whose blocking questions are answered and whose dry run has no blocking
  failure. dr-hub applies the objects with server-side apply and keeps the previous state in the ConfigMap
  `dr-bundle-<name>-previous`.
- **Answers:** The Control Center shows the questions but does not answer them. They are answered with the annotation
  `dr.simplyblock.io/answers`, a JSON object from question ID to the index of the chosen option (starting at 0).
- **Roll back:** Restores the previous state of the objects. Objects the bundle created are deleted.

```bash title="Answering the questions of a bundle without GitOps"
kubectl -n ramen-ops annotate drproposal shop-7f3c1a \
  dr.simplyblock.io/answers='{"plan": 0, "tools-pod": 1}' --overwrite
```

The Control Center's buttons set the request annotation `dr.simplyblock.io/request` on the bundle. The same requests
can be set with `kubectl` (see [Reference](reference.md#annotations)).

## Labels and Their Rollback

The labels of a bundle are applied on the site by dr-agent through LabelRequests, named `bundle-<bundle>-<site>`.
Only the allow-listed label keys can be set (see [Reference](reference.md#label-keys)). The LabelRequests of a bundle
carry the annotation `dr.simplyblock.io/keep: "true"` and are kept. Deleting one restores the previous label values
and removes labels that did not exist before.

Single labels are also set with **Label for DR** in the Kubernetes section of the Control Center.

## Recovery Plans

A RecoveryPlan bundle orders the applications of one DR path in priority lanes, with dependencies first. It names the
application bundles it depends on. After its merge, or its approval without GitOps, it waits in the phase
`WaitingForApplications` until all of them are `Applied`, and is then applied itself. Applications that use each
other get the same priority, and the bundle asks.

## Changes Over Time

- **Superseded:** When a site changes, the rule engine writes a new bundle. The new bundle supersedes the open one,
  and the old pull request is closed unless the new bundle takes over its branch. A newer applied bundle that takes
  over the objects of an applied one also supersedes it.
- **Stale:** A bundle whose candidate disappears from the graph, or whose application already matches the live
  objects, becomes `Stale`.
- **No change:** No bundle is written when the live objects already match.
