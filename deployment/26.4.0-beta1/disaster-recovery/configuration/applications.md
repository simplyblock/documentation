---
title: "Protected Applications"
description: "Protect discovered and GitOps-managed applications with a ProtectedApplication: namespaces, PVC selection, source, target, method, and probes."
source: "https://docs.simplyblock.io/latest/disaster-recovery/configuration/applications/"
---

# Protected Applications

A ProtectedApplication binds one application to a protection plan. It names the site the application runs on, the one
site it recovers to, and the replication method. It also defines how the application is selected, how its recovery is
confirmed, and in which order it starts on the target. Protected applications are written by the `dr-operator` role.

Applications can be containers, KubeVirt virtual machines, or both. The concepts are explained in
[Protected Applications](../../architecture/concepts/dr-applications.md).

## Discovered and Managed Applications

Applications come in two kinds, set by `spec.kind`:

|                                | `discovered`                                                 | `managed`                                                                   |
|--------------------------------|--------------------------------------------------------------|-----------------------------------------------------------------------------|
| Delivery                       | Objects already on the source cluster, deployed by any means | Delivered by GitOps (OCM subscriptions or Argo CD) through an OCM Placement |
| Recovery of objects            | Captured on the source and restored on the target            | The GitOps tool deploys the objects on the target once the Placement moves  |
| ProtectedApplication namespace | `ramen-ops`                                                  | The application's own namespace, next to its Placement                      |
| Placement                      | Not required                                                 | Provided by the user, scheduling disabled                                   |
| Boot order                     | Tiers or a hand-written Recipe                               | GitOps sync order (tiers are not executed)                                  |
| Test failover                  | Supported                                                    | Not supported                                                               |

### Discovered Applications

A discovered application must be declared in the operations namespace `ramen-ops`. Declared anywhere else, it
reports `NotInRamenOpsNamespace`. Deleting the ProtectedApplication stops the protection.

### Managed Applications

A managed application is declared in the application's own namespace, next to the OCM Placement that places it:

- **Placement requirements:** The Placement must already have scheduling disabled (annotation
  `cluster.open-cluster-management.io/experimental-scheduling-disable: "true"`) and select exactly one cluster
  (`numberOfClusters: 1`). Otherwise, the application reports `PlacementNotRamenScheduled`.
- **Source site:** `spec.source` can be omitted. It is taken from the Placement's current decision.
- **PVCs:** An empty `pvcSelector` protects all PVCs in the namespace.
- **Delivery:** The GitOps tooling (for example, Argo CD or ACM) is provided by the user and must deploy to the
  cluster the Placement selects.

!!! info "Coming soon"
    For managed applications, tiers are not executed and not yet validated against Argo CD sync waves. The admission
    webhook warns when tiers are set on a managed application.

## Specification

| Field                                   | Required   | Description                                                                                                    |
|-----------------------------------------|------------|----------------------------------------------------------------------------------------------------------------|
| `spec.planRef`                          | Yes        | Name of the ProtectionPlan. Immutable.                                                                         |
| `spec.source`                           | Discovered | Site the application runs on when protected. Defaulted from the Placement for managed applications.            |
| `spec.target`                           | Yes        | The one site the application recovers to. A DR path from source to target must exist. Immutable.               |
| `spec.method`                           | If several | Method of the plan. Required when the plan has more than one method.                                           |
| `spec.kind`                             | Yes        | `discovered` or `managed`. Immutable.                                                                          |
| `spec.discovered.protectedNamespaces[]` | Discovered | Namespaces whose objects are protected (at least one).                                                         |
| `spec.discovered.pvcSelector`           | No         | Label selector for the replicated PVCs.                                                                        |
| `spec.discovered.recipeRef`             | No         | Hand-written Ramen Recipe (`name`, optional `namespace`). Exclusive with `tiers`.                              |
| `spec.managed.placementRef.name`        | Managed    | OCM Placement in the same namespace.                                                                           |
| `spec.managed.pvcSelector`              | No         | Label selector for the replicated PVCs. Empty means all PVCs in the namespace.                                 |
| `spec.health.probes[]`                  | No         | Up to 32 probes that confirm the application serves after a recovery.                                          |
| `spec.tiers[]`                          | No         | Up to 16 tiers defining the boot order. See [Workflows and Recipes](workflows-and-recipes.md).                 |
| `spec.externalHooks`                    | No         | `preSource` and `postTargetReady` hooks. See [Workflows and Recipes](workflows-and-recipes.md#external-hooks). |
| `spec.dependsOn[]`                      | No         | Applications in the same namespace that must be healthy first, in recovery plans and tests.                    |

Changing the target or the method requires a new ProtectedApplication, which starts with a full initial sync.

## Selecting the Data

The objects and volumes of a discovered application are selected by namespace and label:

- **Namespaces:** All objects in `protectedNamespaces` are captured, except where tiers restrict the selection.
- **PVCs:** The `pvcSelector` picks the PVCs to replicate. The PVCs must use a StorageClass selected by the plan.
- **Labels:** A common label on all PVCs, for example, `app: orders`, keeps the selection stable when PVCs are added.

```bash title="Labeling the PVCs of an application"
kubectl --context site-a -n orders label pvc --all app=orders
```

!!! note
    The PVC selector cannot be changed once the application is protected. A different selection requires a new
    ProtectedApplication.

## Health Probes

Health probes confirm that the application serves after a recovery. They run on the site where the application
currently runs. A recovery action waits up to 15 minutes for all probes to pass. The recovery
time (RTO) of an action is measured from its creation until all probes pass.

| Type         | Field                          | Checks                                                        |
|--------------|--------------------------------|---------------------------------------------------------------|
| `tcp`        | `target` (`host:port`)         | A TCP connection can be opened.                               |
| `http`       | `target` (URL), `expectStatus` | The URL answers, with the expected status if set.             |
| `vmRunning`  | `selector`                     | The selected VirtualMachines are running.                     |
| `guestAgent` | `selector`                     | The guest agent of the selected VirtualMachines is connected. |

Each probe has a `timeout` (default `5s`) and an optional `name`.

!!! info "Coming soon"
    The probe type `objectExists` is accepted by the API but not yet implemented.

## Drift

The replication method, the placement, and the PVC selection of a protected application are fixed once it is protected.
If they no longer match the ProtectedApplication, it reports `DRPCDrift`. The application must then be protected under
a new ProtectedApplication.

## Status

```bash title="Listing the protected applications"
kubectl get protectedapplications -A
```

```plain title="Example output of the protected application listing"
NAMESPACE   NAME     PLAN      SOURCE   TARGET   KIND         CURRENT   PROTECTED
ramen-ops   orders   aws-fra   site-a   site-b   discovered   site-a    True
```

The status reports:

- **Current site:** The cluster the application currently runs on.
- **Readiness per path:** For every DR path the application can take, the allowed actions and a readiness verdict
  (`Ready`, `Degraded`, `NotReady`, or `Unknown`) with the individual checks. See [Monitoring](../operations/monitoring.md).
- **Recipe:** The Recipe in effect and whether it was generated.
- **Suggested tiers:** A boot order suggested from the objects found, never applied automatically.
- **Backups:** Per `snapshot-s3` method, the running and the last successful backup.
- **Conditions:** `Bound` (the protection exists and matches the specification) and `Protected` (the application is
  protected).

```bash title="Showing the readiness of an application per path"
kubectl -n ramen-ops get protectedapplication orders \
  -o jsonpath='{range .status.paths[*]}{.name}: {.readiness.verdict}{"\n"}{end}'
```

## Examples

### Discovered Application With Tiers

```yaml title="Discovered multi-tier application (papp-orders.yaml)"
apiVersion: dr.simplyblock.io/v1alpha1
kind: ProtectedApplication
metadata:
  name: orders
  namespace: ramen-ops
spec:
  planRef: aws-fra
  source: site-a
  target: site-b
  method: async-5m
  kind: discovered
  discovered:
    protectedNamespaces:
      - orders
    pvcSelector:
      matchLabels:
        app: orders
  tiers:
    - name: config
      selector:
        matchLabels:
          dr.simplyblock.io/tier: config
    - name: middleware
      selector:
        matchLabels:
          dr.simplyblock.io/tier: middleware
      ready:
        - type: deploymentsReady
    - name: app
      selector:
        matchLabels:
          dr.simplyblock.io/tier: app
      ready:
        - type: deploymentsReady
    - name: web
      selector:
        matchLabels:
          dr.simplyblock.io/tier: web
      ready:
        - type: deploymentsReady
  health:
    probes:
      - name: web
        type: http
        target: http://web.orders.svc:8080/healthz
```

### Virtual Machines

```yaml title="Discovered KubeVirt application with VM probes (papp-erp.yaml)"
apiVersion: dr.simplyblock.io/v1alpha1
kind: ProtectedApplication
metadata:
  name: erp
  namespace: ramen-ops
spec:
  planRef: fra
  source: fra-a
  target: fra-b
  kind: discovered
  discovered:
    protectedNamespaces:
      - erp
    pvcSelector:
      matchLabels:
        app: erp
  health:
    probes:
      - name: erp-vms
        type: vmRunning
        selector:
          matchLabels:
            app: erp
      - name: erp-web
        type: tcp
        target: erp-web.erp.svc:443
```

Without tiers, the default boot order restores configuration objects first and all workloads afterward (see
[Workflows and Recipes](workflows-and-recipes.md#default-order)).

### Managed Application

```yaml title="GitOps-managed application (papp-portal.yaml)"
apiVersion: dr.simplyblock.io/v1alpha1
kind: ProtectedApplication
metadata:
  name: portal
  namespace: portal
spec:
  planRef: fra
  target: fra-b
  kind: managed
  managed:
    placementRef:
      name: portal-placement
```

### Application Dependencies

`dependsOn` names applications in the same namespace that must be healthy first. Recovery plans and tests respect the
order:

```yaml title="Application that depends on its database (papp-billing.yaml)"
apiVersion: dr.simplyblock.io/v1alpha1
kind: ProtectedApplication
metadata:
  name: billing
  namespace: ramen-ops
spec:
  planRef: aws-fra
  source: site-a
  target: site-b
  kind: discovered
  discovered:
    protectedNamespaces:
      - billing
  dependsOn:
    - billing-db
```

For several applications that move together, see [Recovery Plans](../operations/recovery-plans.md).
