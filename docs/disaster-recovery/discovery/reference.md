---
title: "Reference"
description: "Reference of discovery: graphs, bundles with their phases, DR configuration settings, discovery runs, request annotations, and the allowed label keys."
weight: 10283
---

All kinds are in the API group `dr.simplyblock.io/v1alpha1` on the hub.

| Kind               | Scope      | Short name  | Purpose                                                       |
|--------------------|------------|-------------|---------------------------------------------------------------|
| DiscoveryGraph     | Cluster    | `dgraph`    | The dependency graph and candidates of one site               |
| DRProposal         | Namespaced | `drprop`    | One bundle                                                    |
| DiscoveryRun       | Namespaced | `drun`      | One discovery pass                                            |
| DRBlueprint        | Namespaced | `drbp`      | Approved applications in environment-neutral form (blueprint) |
| BlueprintExport    | Namespaced | `bpexport`  | A one-shot export of applied bundles into a blueprint         |
| EnvironmentMapping | Namespaced | `envmap`    | A blueprint matched against one site                          |
| SRMImport          | Namespaced | `srmimport` | A one-shot import of a VMware Live Site Recovery export       |

The blueprint kinds are described in [Environment Promotion](blueprints.md) and
[Migration From VMware Live Site Recovery](srm-import.md).

## DiscoveryGraph

A DiscoveryGraph is named after its managed cluster and written only by dr-hub.

| Field                   | Content                                                                                              |
|-------------------------|------------------------------------------------------------------------------------------------------|
| `status.observedReport` | The generation of the site's discovery report the graph was built from                               |
| `status.built`          | When the graph was built                                                                             |
| `status.shards`         | The ConfigMaps `dr-graph-<site>-<n>` in the namespace of dr-hub that hold nodes, edges, and evidence |
| `status.counts`         | Nodes, edges, evidence, candidates, and the collectors whose budget truncated the report             |
| `status.candidates`     | The application candidates: ID, name, namespaces, members, score (0 to 1000), adopted application    |
| `status.interApp`       | Edges between candidates, from caller to callee, for recovery-plan priorities                        |

| Element         | Values                                                                                |
|-----------------|---------------------------------------------------------------------------------------|
| Node kinds      | `Workload`, `VirtualMachine`, `Pod`, `PVC`, `Service`, `NAD`, `Namespace`, `External` |
| Edge kinds      | `owns`, `mounts`, `selects`, `references`, `connects`, `attaches`, `packagedWith`     |
| Evidence source | `inventory`, `configScan`, `packaging`, `fingerprint`, `flows`, `guestAgent`          |

Every edge has a weight from 0 to 1000 and the IDs of its evidence. An evidence item names the object and field it was
read from and a redacted excerpt of at most 120 characters. Evidence IDs stay the same across rebuilds, so bundles can
cite them.

## DRProposal

The spec of a bundle is immutable. A revision is a new DRProposal.

| Field                  | Content                                                                                                     |
|------------------------|-------------------------------------------------------------------------------------------------------------|
| `spec.scope`           | `Application`, `RecoveryPlan` or `SiteMapping`                                                              |
| `spec.site`            | The managed cluster the candidate runs on                                                                   |
| `spec.candidate`       | The candidate ID in the site's DiscoveryGraph                                                               |
| `spec.source`          | `rules`, `ai:<discoveryrun>`, `blueprint:<blueprint>@<version>`, or `srm:<blueprint>@<version>`             |
| `spec.baseline`        | The rules bundle that an AI or blueprint bundle revises                                                     |
| `spec.objects`         | The proposed objects (1 to 50), each with `operation` (`create` or `update`), `spec` and `fields`           |
| `spec.labels`          | Label changes on site objects (up to 500), each with cluster, change, reason, evidence, and effect          |
| `spec.migrations`      | Bound PVCs that would join a consistency group only after a migration. Informational                        |
| `spec.dependsOn`       | The application bundles a RecoveryPlan bundle waits for                                                     |
| `spec.questions`       | Open questions (up to 50), each with ID, text, up to 8 options, the field it decides, and whether it blocks |
| `spec.summary`         | A description, also used at the top of the pull request                                                     |
| `spec.confidence`      | The bundle's confidence, 0 to 1000                                                                          |
| `status.phase`         | See the phases below                                                                                        |
| `status.dryRun`        | The readiness checks evaluated against the proposed objects                                                 |
| `status.diff`          | A unified diff against the live objects (up to 64 KiB)                                                      |
| `status.baselineDiff`  | A unified diff against the baseline bundle (up to 64 KiB)                                                   |
| `status.gitOps`        | Branch, pull request, head commit, and merge commit, and the pull request state                             |
| `status.answers`       | The answers to the questions, with who answered                                                             |
| `status.approvedBy`    | The user who approved the bundle                                                                            |
| `status.appliedAt`     | When the objects were applied                                                                               |
| `status.supersededBy`  | The bundle that replaced this one                                                                           |
| `status.labelRequests` | The LabelRequests that applied the bundle's labels                                                          |

### Phases

| Phase                    | Meaning                                                                     |
|--------------------------|-----------------------------------------------------------------------------|
| `Proposed`               | Written and validated, not yet in a pull request                            |
| `PROpened`               | The pull request is open                                                    |
| `Merged`                 | The pull request is merged, the objects are not yet on the hub              |
| `WaitingForApplications` | A merged or approved RecoveryPlan bundle waits for its application bundles  |
| `Applied`                | The objects are on the hub                                                  |
| `Rejected`               | The pull request was closed without a merge, or the bundle was rejected     |
| `Superseded`             | A newer bundle replaces this one                                            |
| `Stale`                  | The candidate disappeared from the graph, or the live objects already match |
| `RolledBack`             | The merge was reverted, or the bundle was rolled back in the Control Center |

`Rejected`, `Superseded`, `Stale`, and `RolledBack` are final. An `Applied` bundle can still be rolled back or
superseded.

### Conditions

| Condition     | Meaning                                                                            |
|---------------|------------------------------------------------------------------------------------|
| `Valid`       | The bundle passed validation and its dry run has no blocking failure               |
| `Request`     | The outcome of the last request from the Control Center                            |
| `Conflict`    | Files on the branch block a push, for example, files edited by a reviewer          |
| `Answers`     | A question in the pull request has more than one option checked                    |
| `GitOpsError` | The Git provider failed, for example, because of a missing token                   |
| `SyncPending` | The bundle was merged, but its objects have not appeared on the hub for 30 minutes |

Every phase change also sets a condition of the phase's name, with the reason and the user involved, and records an
event on the bundle.

## DRConfig Discovery Settings

| Field                                        | Default   | Content                                                                                                                         |
|----------------------------------------------|-----------|---------------------------------------------------------------------------------------------------------------------------------|
| `spec.discovery.enabled`                     | `false`   | Turns discovery on                                                                                                              |
| `spec.discovery.autoRules`                   | `true`    | Writes bundles on every graph change                                                                                            |
| `spec.discovery.rebuild`                     | `2m`      | Debounce of graph rebuilds                                                                                                      |
| `spec.discovery.flows.optOut`                | empty     | Managed clusters without the flow collector                                                                                     |
| `spec.discovery.flows.retention`             | `168h`    | How long flow aggregates are kept                                                                                               |
| `spec.discovery.flows.udp`                   | `false`   | Reserved for sampled UDP flows. The collector records TCP only                                                                  |
| `spec.discovery.flows.legacyKernels`         | `false`   | Reserved for kernels older than 5.8. The collector does not start on them                                                       |
| `spec.discovery.gitOps.provider`             |           | `github` or `gitea`. `gitlab` is accepted but not implemented                                                                   |
| `spec.discovery.gitOps.url`                  |           | The repository, `https://<host>/<owner>/<name>`                                                                                 |
| `spec.discovery.gitOps.baseBranch`           | `main`    | The branch pull requests target                                                                                                 |
| `spec.discovery.gitOps.path`                 | `dr/`     | The directory of the bundles                                                                                                    |
| `spec.discovery.gitOps.credentialsSecretRef` |           | A Secret with the key `token`, in the namespace of dr-hub                                                                       |
| `spec.discovery.gitOps.reviewers`            | empty     | Reviewers requested on every pull request                                                                                       |
| `spec.discovery.gitOps.labels`               | empty     | Labels set on every pull request                                                                                                |
| `spec.discovery.gitOps.syncDetection`        | `objects` | How a merge is detected as live: by the bundle annotations on the objects. `argocd` and `flux` are accepted but not implemented |
| `spec.discovery.gitOps.syncRef`              | empty     | Reserved for `argocd` and `flux`                                                                                                |

`spec.discovery.providers` (each with `name`, `type`, `model`, `region`, `endpoint`, `credentialsSecretRef`, and
`egress`) and `spec.discovery.defaultProvider` configure model providers for the planned AI mode. The types are
`anthropic`, `bedrock`, `vertex`, and `openaiCompatible`. They have no effect in rules mode.

## DiscoveryRun

The spec of a run is immutable.

| Field                   | Content                                                                      |
|-------------------------|------------------------------------------------------------------------------|
| `spec.mode`             | `Rules`. The mode `AI` is planned and fails with `NotImplemented`            |
| `spec.scope.site`       | The managed cluster                                                          |
| `spec.scope.namespaces` | Narrows the run to these namespaces. Empty is the whole site                 |
| `status.phase`          | `Pending`, `Running`, `Succeeded`, `Failed`, `BudgetExceeded` or `Cancelled` |
| `status.progress`       | A short description of the current step                                      |
| `status.started`        | When the run started                                                         |
| `status.completed`      | When the run finished                                                        |
| `status.proposals`      | The bundles the run produced                                                 |

The condition `Completed` records the outcome: `Proposed` on success, or `DiscoveryDisabled`, `NotReported`,
`BuildFailed`, `ProposeFailed`, or `NotImplemented` on failure. The fields `spec.provider`, `spec.budget`,
`spec.instructions`, `spec.playbooks`, and `spec.scope.proposal`, and the status fields `usage`, `toolLog`, and
`rejected` belong to the planned AI mode.

## Annotations

| Annotation                         | On              | Content                                                                       |
|------------------------------------|-----------------|-------------------------------------------------------------------------------|
| `dr.simplyblock.io/request`        | DRProposal      | A request from the Control Center: `open-pr`, `reject`, `approve`, `rollback` |
| `dr.simplyblock.io/request-reason` | DRProposal      | The reason of a request                                                       |
| `dr.simplyblock.io/request-by`     | DRProposal      | Set by the admission webhook to the requesting user                           |
| `dr.simplyblock.io/answers`        | DRProposal      | Answers without GitOps, as JSON from question ID to option index              |
| `dr.simplyblock.io/bundle`         | Applied objects | The bundle that wrote the object                                              |
| `dr.simplyblock.io/bundle-hash`    | Applied objects | The content hash of that bundle                                               |
| `dr.simplyblock.io/keep`           | LabelRequest    | `"true"` keeps a bundle's LabelRequest, deleting it restores the labels       |

dr-hub carries out a request, removes the annotation and records the outcome in the condition `Request`. The requests
`approve` and `rollback` need the verbs of the same name on `drproposals`, and are refused while a GitOps target is
configured. `open-pr` is refused without a GitOps target, and `reject` applies only to an open bundle.

## Label Keys

A bundle and a LabelRequest may only set or remove these labels. Anything else is refused by dr-hub and by dr-agent.

| Object                                  | Label keys                                                                 |
|-----------------------------------------|----------------------------------------------------------------------------|
| StorageClass                            | `simplyblock.io/replicated`, `simplyblock.io/dr`, `simplyblock.io/stretch` |
| Node                                    | `topology.kubernetes.io/zone`, `topology.kubernetes.io/region`             |
| PersistentVolumeClaim                   | `app`, `storage.simplyblock.io/consistency-group`                          |
| VirtualMachine, Deployment, StatefulSet | `app`, `dr.simplyblock.io/tier` (on the object and its pod template)       |
