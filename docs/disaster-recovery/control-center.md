---
title: "Control Center"
description: "Deploy the simplyblock Control Center with the operator or the DR hub chart and manage plans, paths, applications, site mappings, actions, and tests in the browser."
weight: 10500
---

The simplyblock Control Center is the web console of simplyblock. Its *Disaster recovery* section is a client of the
DR resources on the hub: everything that is declared as a custom resource in this documentation can also be created
and watched in the console, and the console never holds state of its own. Reading the resource pages of this section
is still worthwhile, because the console writes exactly those fields.

## Deploying the Console

The console runs on the hub cluster, next to dr-hub, in one of two modes:

- **Full mode:** The storage console with the Disaster recovery section. It is deployed by the Simplyblock Operator
  Helm chart on a hub that also runs the simplyblock control plane, with `controlCenter.enabled=true`. The chart
  creates the console's ServiceAccount, its ClusterRole (storage reads, the DR writes, and the site mapper's DHCP
  servers), a Service, and optionally an Ingress.
- **DR-only mode:** Nothing but the Disaster recovery section, for a hub without a simplyblock control plane. It is
  deployed by the DR hub chart with `console.enabled=true`. `console.role` (`viewer`, `operator`, or `admin`) is
  the DR role the console's ServiceAccount holds.

```bash title="Enabling the DR-only console on the hub"
helm upgrade dr-simplyblock-hub simplyblock/dr-simplyblock-hub -n dr-simplyblock --reuse-values \
  --set console.enabled=true --set console.role=admin \
  --set console.ingress.enabled=true --set console.ingress.host=dr.example.com
```

```bash title="Enabling the full console with the Simplyblock Operator chart"
helm upgrade simplyblock-operator simplyblock/simplyblock-operator -n simplyblock --reuse-values \
  --set controlCenter.enabled=true --set controlCenter.mode=full \
  --set controlCenter.ingress.enabled=true --set controlCenter.ingress.host=console.example.com
```

| Value (operator chart `controlCenter.*`, hub chart `console.*`) | Description                                                                                                                                             |
|-----------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| `enabled`                                                       | Deploys the console. Off by default.                                                                                                                    |
| `mode` (operator chart only)                                    | `full` or `dr`.                                                                                                                                         |
| `role` (hub chart only)                                         | The DR role of the console in service-account mode: `viewer`, `operator`, or `admin`.                                                                   |
| `authMode`                                                      | `serviceaccount`: the pod attaches its own token to every request. `passthrough`: the browser's bearer token is forwarded and each user's RBAC applies. |
| `image.registry`, `image.repository`, `image.tag`               | The console image.                                                                                                                                      |
| `replicas`                                                      | Stateless, so two replicas keep the console up through a node loss.                                                                                     |
| `service.type`, `service.port`, `service.nodePort`              | The Service. A NodePort is pinned with `service.nodePort` (operator chart).                                                                             |
| `ingress.enabled`, `ingress.host`, `ingress.annotations`        | The Ingress. In service-account mode, authentication belongs in front of it.                                                                            |
| `drNamespace` (operator chart only)                             | Ramen's operations namespace, where discovered applications live (default `ramen-ops`).                                                                 |
| `prometheusUrl`                                                 | A Prometheus that scrapes dr-hub's metrics, for history views. Empty shows the resource status only.                                                    |

!!! warning
    In service-account mode, everyone who reaches the Service acts with the console's ClusterRole. The console does
    not authenticate users itself. An authenticating proxy or the Ingress annotations provide the login, or
    `authMode: passthrough` passes on each user's own token.

## What the Console Does

The Disaster recovery home shows the plans, paths, protected applications with their readiness per path, the running
actions and tests, and the resolution inbox of the site mapper.

| Screen                       | Creates and edits                                                                                                                                                                                                           | Resources                                      |
|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------|
| New plan, Edit S3 stores     | Sites, storage class selector, methods with their intervals, one S3 store per site, Velero namespace.                                                                                                                       | `ProtectionPlan`                               |
| Declare path                 | Direction, allowed actions, test settings (isolated NAD, clone capacity, test-recent window).                                                                                                                               | `DRPath`                                       |
| Protect application          | Kind, namespaces, PVC selector, source and target, tiers with their ready conditions, health probes. *Edit tiers & probes* changes them later.                                                                              | `ProtectedApplication`                         |
| Register DHCP server         | Site, type, ConfigMap, and binding as the site's DHCP server.                                                                                                                                                               | `DHCPServer`, `SiteProfile`                    |
| Site profiles, Edit bindings | Logical networks per role, guest networks with subnet and reserved host IDs, the DHCP server per role.                                                                                                                      | `SiteProfile`                                  |
| Application, Site mapping    | The findings, guest reservations, and renderings of an application (read-only).                                                                                                                                             | `ProtectedApplication` status                  |
| Relocate, Failover, Test     | A recovery action or test along a path, with the override reason when the path is `NotReady` (`dr-admin` only). The action's phase strip, journal, and report follow in place.                                              | `RecoveryAction`, `TestBubble`                 |
| Recovery plans, Schedules    | Ordered plans of several applications, cron schedules of tests.                                                                                                                                                             | `RecoveryPlan`, `TestSchedule`                 |
| Restore                      | A restore of an application awaiting restore after a total loss.                                                                                                                                                            | `RestoreAction`                                |
| Discovery, Proposals         | The site graphs, the bundles with their evidence, questions, and dry run, runs of the rule engine, and the approval and rollback of bundles without a GitOps repository. See [Discovery and Proposals](discovery/index.md). | `DiscoveryGraph`, `DRProposal`, `DiscoveryRun` |
| Clusters, Logical volumes    | Full mode only: the storage side, for example, the landing copies and replicated snapshots on the target cluster, and the clone under the PVC's name after a fail-over.                                                     | Storage resources                              |

The replicated StorageClass of a site is created by dr-hub from the plan, see
[Protection Plans](configuration/protection-plans.md#provisioning-the-storageclass). The deployment of a managed site's
storage cluster (discovery, draft, approval) is not in the console yet.

!!! info "Coming soon"
    - **Deploying a site's storage from the hub:** A `StorageSiteDeployment` resource on the hub, reconciled through
      Open Cluster Management, lets the console discover a managed site's nodes, size the draft, and approve the
      deployment of its storage cluster.
