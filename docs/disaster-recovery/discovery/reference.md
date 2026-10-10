---
title: "Reference"
description: "Reference of discovery: DRProposal phases and fields, DRConfig discovery settings, DiscoveryRun fields, request annotations, and the label keys a bundle may set."
weight: 10283
---

All kinds are in the API group `dr.simplyblock.io/v1alpha1` on the hub.

| Kind           | Scope      | Short name | Purpose                                         |
|----------------|------------|------------|-------------------------------------------------|
| DiscoveryGraph | Cluster    | `dgraph`   | The dependency graph and candidates of one site |
| DRProposal     | Namespaced | `drprop`   | One bundle                                      |
| DiscoveryRun   | Namespaced | `drun`     | One discovery pass                              |

## DRProposal

The spec of a bundle is immutable. A revision is a new DRProposal.

| Field                  | Content                                                                                             |
|------------------------|-----------------------------------------------------------------------------------------------------|
| `spec.scope`           | `Application`, `RecoveryPlan` or `SiteMapping`                                                      |
| `spec.site`            | The managed cluster the candidate runs on                                                           |
| `spec.candidate`       | The candidate ID in the site's DiscoveryGraph                                                       |
| `spec.source`          | `rules`, or `ai:<discoveryrun>` for a bundle of an AI run                                           |
| `spec.objects`         | The proposed objects (1 to 50), each with `operation` (`create` or `update`), `spec` and `fields`  |
| `spec.labels`          | Label changes on site objects (up to 500), each with cluster, change, reason, evidence and effect   |
| `spec.migrations`      | Bound PVCs that would join a consistency group only after a migration. Informational                |
| `spec.dependsOn`       | The application bundles a RecoveryPlan bundle waits for                                             |
| `spec.questions`       | Open questions (up to 50), each with ID, text, options and whether it is blocking                   |
| `spec.summary`         | A description, also used at the top of the pull request                                             |
| `spec.confidence`      | The bundle's confidence, 0 to 1000                                                                  |
| `status.phase`         | See the phases below                                                                                |
| `status.dryRun`        | The readiness checks evaluated against the proposed objects                                         |
| `status.diff`          | A unified diff against the live objects (up to 64 KiB)                                              |
| `status.gitOps`        | Branch, pull request, head and merge commit, and the pull request state                             |
| `status.answers`       | The answers to the questions, with who answered                                                     |
| `status.approvedBy`    | The user who approved the bundle                                                                    |
| `status.labelRequests` | The LabelRequests that applied the bundle's labels                                                  |

### Phases

| Phase                    | Meaning                                                                            |
|--------------------------|------------------------------------------------------------------------------------|
| `Proposed`               | Written and validated, not yet in a pull request                                   |
| `PROpened`               | The pull request is open                                                           |
| `Merged`                 | The pull request is merged, the objects are not yet on the hub                     |
| `WaitingForApplications` | A merged RecoveryPlan bundle waits for its application bundles                     |
| `Applied`                | The objects are on the hub                                                         |
| `Rejected`               | The pull request was closed without a merge, or the bundle was rejected            |
| `Superseded`             | A newer bundle replaces this one                                                   |
| `Stale`                  | The candidate disappeared from the graph                                           |
| `RolledBack`             | The merge was reverted, or the bundle was rolled back in the Control Center        |

### Conditions

| Condition     | Meaning                                                                               |
|---------------|---------------------------------------------------------------------------------------|
| `Valid`       | The bundle passed validation and its dry run has no blocking failure                  |
| `Request`     | The outcome of the last request from the Control Center                               |
| `Conflict`    | Files on the branch block a push, for example files edited by a reviewer              |
| `SyncPending` | The bundle was merged, but its objects have not appeared on the hub for 30 minutes    |

## DRConfig Discovery Settings

| Field                                    | Default  | Content                                                                  |
|------------------------------------------|----------|--------------------------------------------------------------------------|
| `spec.discovery.enabled`                 | `false`  | Turns discovery on                                                       |
| `spec.discovery.autoRules`               | `true`   | Writes bundles on every graph change                                     |
| `spec.discovery.rebuild`                 | `2m`     | Debounce of graph rebuilds                                               |
| `spec.discovery.flows.optOut`            | empty    | Managed clusters without the flow collector                              |
| `spec.discovery.flows.retention`         | `168h`   | How long flow aggregates are kept                                        |
| `spec.discovery.flows.udp`               | `false`  | Adds sampled UDP flows                                                   |
| `spec.discovery.flows.legacyKernels`     | `false`  | Starts the collector with `CAP_SYS_ADMIN` on kernels older than 5.8      |
| `spec.discovery.gitOps.provider`         |          | `github` or `gitea`                                                      |
| `spec.discovery.gitOps.url`              |          | The repository, starting with `https://`                                 |
| `spec.discovery.gitOps.baseBranch`       | `main`   | The branch pull requests target                                          |
| `spec.discovery.gitOps.path`             | `dr/`    | The directory of the bundles                                             |
| `spec.discovery.gitOps.credentialsSecretRef` |      | A Secret with the key `token`, in the namespace of dr-hub                |
| `spec.discovery.gitOps.reviewers`        | empty    | Reviewers requested on every pull request                                |
| `spec.discovery.gitOps.labels`           | empty    | Labels set on every pull request                                         |
| `spec.discovery.gitOps.syncDetection`    | `objects`| How a merge is detected as live: by the bundle annotation on the objects |

`spec.discovery.providers` and `spec.discovery.defaultProvider` configure model providers for the planned AI mode.

## DiscoveryRun

The spec of a run is immutable.

| Field                   | Content                                                                   |
|-------------------------|---------------------------------------------------------------------------|
| `spec.mode`             | `Rules`. The mode `AI` is planned and fails with `NotImplemented`         |
| `spec.scope.site`       | The managed cluster                                                       |
| `spec.scope.namespaces` | Narrows the run to these namespaces. Empty is the whole site              |
| `status.phase`          | `Pending`, `Running`, `Succeeded`, `Failed`, `BudgetExceeded` or `Cancelled` |
| `status.progress`       | A short description of the current step                                   |
| `status.proposals`      | The bundles the run produced                                              |

## Annotations

| Annotation                          | On                    | Content                                                                    |
|-------------------------------------|-----------------------|----------------------------------------------------------------------------|
| `dr.simplyblock.io/request`         | DRProposal            | A request from the Control Center: `open-pr`, `reject`, `approve`, `rollback` |
| `dr.simplyblock.io/request-reason`  | DRProposal            | The reason of a request                                                    |
| `dr.simplyblock.io/request-by`      | DRProposal            | Set by the admission webhook to the requesting user                        |
| `dr.simplyblock.io/answers`         | DRProposal            | Answers without GitOps, as JSON from question ID to option index           |
| `dr.simplyblock.io/bundle`          | Applied objects       | The bundle that wrote the object                                           |
| `dr.simplyblock.io/bundle-hash`     | Applied objects       | The content hash of that bundle                                            |

dr-hub carries out a request, removes the annotation and records the outcome in the condition `Request`.

## Label Keys

A bundle and a LabelRequest may only set or remove these labels. Anything else is refused by dr-hub and by dr-agent.

| Object                                | Label keys                                                                   |
|---------------------------------------|------------------------------------------------------------------------------|
| StorageClass                          | `simplyblock.io/replicated`, `simplyblock.io/dr`, `simplyblock.io/stretch`   |
| Node                                  | `topology.kubernetes.io/zone`, `topology.kubernetes.io/region`               |
| PersistentVolumeClaim                 | `app`, `storage.simplyblock.io/consistency-group`                            |
| VirtualMachine, Deployment, StatefulSet | `app`, `dr.simplyblock.io/tier` (on the object and its pod template)       |
