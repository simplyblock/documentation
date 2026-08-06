---
title: "Volume Migration"
description: "How the Simplyblock operator migrates a volume's backing logical volume between storage nodes — manually, through experimental auto-rebalancing, and automatically during node draining or removal."
weight: 10770
---

The Simplyblock Operator can move a volume's backing logical volume from one storage node to another
while the volume stays online (live migration). A migration relocates a logical volume (and its snapshots). It
does not move the storage node itself. This is different from
[Migrating a Storage Node](../../non-kubernetes/operations/migrating-storage-node.md), which relocates an entire storage node identity to a
new host.

Volume migration is used in three ways:

- **Manual migration:** requests a specific volume to move to a specific target node.
- **Drain / removal migration:** the operator automatically evacuates a node's volumes before it is removed.
- **Auto-rebalancing:** the operator continuously moves volumes off overloaded nodes.

All three paths share the same backend migration mechanism and the same post-migration
[data realignment](#data-realignment).

## Enabling Volume Migration

Volume migration is controlled per cluster by `StorageCluster.spec.volumeMigrationSettings`.

```yaml title="Volume migration settings"
spec:
  volumeMigrationSettings:
    enabled: true                       # default: true
    dataRealignment:
      enabled: true                     # default: true
      interval: 10m                     # default: 10m
```

| Field                      | Default | Description                                                                                                                      |
|----------------------------|---------|----------------------------------------------------------------------------------------------------------------------------------|
| `enabled`                  | `true`  | When `false`, the operator does not act on `VolumeMigration` resources for this cluster.                                         |
| `dataRealignment.enabled`  | `true`  | Enables automatic post-migration [data realignment](#data-realignment).                                                          |
| `dataRealignment.interval` | `10m`   | How often the operator checks whether a realignment is pending.                                                                  |

## Manual Volume Migration

A manual migration is triggered by creating a [`VolumeMigration`](../../reference/operator/reference.md#volumemigration)
resource (short name `vmig`) that names the `PersistentVolume` to move and the UUID of the destination storage node.

```bash title="Migrate a single volume to a target node"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha1
kind: VolumeMigration
metadata:
  name: migrate-pvc-968cff4f
  namespace: simplyblock
spec:
  pvName: pvc-968cff4f-a199-4964-88f0-7cfccb5251d9
  targetNodeUUID: 4e53efdd-86c9-424f-940c-e437eb6a2e95
EOF
```

Both `spec.pvName` and `spec.targetNodeUUID` are immutable. To migrate the same volume again, or to a
different target, create a new `VolumeMigration` resource.

The referenced PV must be provisioned by the Simplyblock CSI driver. The operator resolves the PV to its
logical volume UUID, submits the migration to the storage API, validates the new NVMe-oF paths, and then
tracks progress to completion.

### Finding Target Node UUIDs

The `targetNodeUUID` is the backend storage node UUID, not the Kubernetes worker name.

```bash title="Listing the storage node UUIDs"
kubectl get storagenodeset simplyblock-node -n simplyblock \
  -o jsonpath='{.status.nodes[*].uuid}' | tr ' ' '\n'
```

Alternatively, the storage node CRs can be listed to find the storage node UUID:

```bash title="Listing the storage node CRs"
kubectl get storagenodes -n simplyblock
```

### Monitoring a Migration

The resource exposes the current phase and snapshot progress directly in its printer columns.

```bash title="Watch migration progress"
kubectl get volumemigration -n simplyblock -w
```

```bash title="Inspect full migration status"
kubectl get volumemigration migrate-pvc-968cff4f \
  -n simplyblock -o jsonpath='{.status}' | jq .
```

Each migration progresses through the following phases, tracked in `VolumeMigration.status.phase`:

| Phase        | Description                                                                                             |
|--------------|---------------------------------------------------------------------------------------------------------|
| `Pending`    | The migration has been accepted. The operator is resolving the PV and submitting it.                    |
| `Validating` | The new target-side NVMe-oF paths are being established and verified by a validation Job.               |
| `Running`    | The backend is copying data and snapshots. `status.snapsMigrated` / `status.snapsTotal` track progress. |
| `Completed`  | The volume now resides on the target node.                                                              |
| `Failed`     | The migration could not complete. `status.errorMessage` holds the reason.                               |
| `Aborted`    | The migration was cancelled via `spec.abort`.                                                           |

The status also records the resolved `sourceNodeUUID`, `volumeUUID`, `poolUUID`, `clusterUUID`, the backend
`migrationUUID`, and `startedAt` / `completedAt` timestamps.

### Aborting a Migration

An in-progress migration can be canceled by setting `spec.abort` to `true`. The phase transitions to
`Aborted` once the backend confirms the cancellation.

!!! important
    A volume migration can only be aborted while in the `Pending` or `Validating` phases. A running migration must be
    able to complete to ensure data consistency. Hence, it cannot be aborted once running.  

```bash title="Abort an in-progress migration"
kubectl patch volumemigration migrate-pvc-968cff4f -n simplyblock \
  --type merge -p '{"spec":{"abort":true}}'
```

### Migrating by Pinning a PVC

There are also automated processes that create a `VolumeMigration` resource, for example, setting the
`simplyblock.io/selected-storage-node` annotation on an already-bound PVC. This will effectively migrate the pinned
volume to a new storage node UUID. The operator create a `VolumeMigration` on the user's behalf, as part of moving the
volume to that node. This is the same annotation that [pins a volume](#pinned-volumes) against auto-rebalancing and
node removal.

```bash title="Pin a bound PVC to a new node to trigger a migration"
kubectl annotate pvc <pvc-name> -n <namespace> \
  simplyblock.io/selected-storage-node=<target-storage-node-uuid> --overwrite
```

The annotation value must be a known storage node UUID; a validating webhook rejects the change otherwise.
If the value is not a valid node, the operator records it and emits an `InvalidPinTarget` event.

## Auto-Rebalancing

{{ experimental }}

When enabled, the operator continuously evaluates the per-node load and automatically migrates volumes off
overloaded ("hot") nodes onto less-loaded ("cold") nodes. Under the hood it creates the same
`VolumeMigration` resources as a manual migration, so all migrations remain observable through `vmig`.

Auto-rebalancing is configured by `StorageCluster.spec.volumeAutoPlacement` and is disabled by default.

```yaml title="Enable latency-driven auto-rebalancing"
spec:
  volumeAutoPlacement:
    enabled: true
    metricsBackend: prometheus
    prometheusURL: http://prometheus.simplyblock.svc:9090
    latencyBenchmarkEnabled: true
    evaluationInterval: 60s
    imbalanceThreshold: 80
    maxVolumeMigrationsPerCycle: 10
```

!!! important
    Automatic rebalancing is considered an experimental feature. Its algorithm is subject to change and is not optimal.
    It is not yet recommended for any production environment.

| Field                         | Default      | Description                                                                                                   |
|-------------------------------|--------------|---------------------------------------------------------------------------------------------------------------|
| `enabled`                     | `false`      | Activates automatic rebalancing for the cluster.                                                              |
| `migrationEnabled`            | `true`       | When `false`, the rebalancer runs every cycle but discards the migrations instead of creating them (dry-run). |
| `evaluationInterval`          | `60s`        | How often the rebalancer evaluates load.                                                                      |
| `imbalanceThreshold`          | `80`         | Minimum latency deviation from baseline (percent) before a node is considered a rebalancing source.           |
| `minHotColdDifferencePct`     | `20`         | Minimum latency-deviation gap a target must be below the source before a migration is performed.              |
| `maxVolumeMigrationsPerCycle` | `10`         | Maximum number of volumes moved per cycle.                                                                    |
| `storageNodeCandidateCount`   | `3`          | Number of top-loaded nodes evaluated each cycle to pick the migration source.                                 |
| `defaultCoolDownSeconds`      | `600`        | Cool-down applied to a volume after it has been migrated, preventing it from moving again immediately.        |
| `metricsBackend`              | `prometheus` | Source of I/O metrics: `prometheus`, `controlplane`, or `uniform`.                                            |
| `prometheusURL`               | —            | Required when `metricsBackend` is `prometheus`.                                                               |
| `latencyBenchmarkEnabled`     | `false`      | Enables `fio`-based NVMe-oF latency measurement via Kubernetes Jobs.                                          |
| `latencyBenchmarkInterval`    | `5m`         | How often benchmark Jobs run against each storage node.                                                       |
| `iopsWeight`                  | `1.0`        | Weight applied to per-volume IOPS in the volume I/O score.                                                    |
| `throughputWeight`            | `0.1`        | Weight applied to per-volume throughput (MB/s) in the volume I/O score.                                       |

!!! tip
    Start with `migrationEnabled: false` (dry-run). The rebalancer still evaluates load, computes deviations,
    selects candidates, and emits metrics and events, but does not move any data. Once the selected candidates
    look correct, set `migrationEnabled: true`.

!!! note
    Volumes that are pinned to a specific storage node (see [Pinned Volumes](#pinned-volumes)) are not subject to
    auto-rebalancing. A one-shot placement hint from initial provisioning does not pin a volume. Such volumes
    remain eligible for rebalancing.

## Volume Migration During Node Draining and Removal

When a storage node is removed, the operator evacuates its volumes onto the remaining nodes before the node
leaves the cluster. Removal is triggered by a `StorageNodeOps` resource with `action: remove`.

```bash title="Remove a storage node (drains its volumes first)"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeOps
metadata:
  name: drain-worker-1
  namespace: simplyblock
spec:
  storageNodeRef: simplyblock-node-worker-1.example.com-s0-n0
  action: remove
EOF
```

While `status.phase` is `Running`, the removal advances through the drain sub-phases tracked in
`StorageNodeOps.status.subPhase`:

| Sub-phase    | Description                                                                                           |
|--------------|-------------------------------------------------------------------------------------------------------|
| `Validating` | Preconditions are checked and the node's volumes are classified.                                      |
| `Suspending` | The node is suspended so no new volumes are placed on it.                                             |
| `Migrating`  | Volumes are migrated off the node. `status.volumesMigrated` / `status.volumesPending` track progress. |
| `Verifying`  | Migrations are confirmed and system volumes are cleaned up.                                           |
| `Removing`   | The now-empty node is removed from the cluster.                                                       |

System volumes are excluded from migration and deleted inline during `Verifying`. The set of system volumes
is matched by `spec.drain.systemVolumeFilterRegex` (default `^sb-fio-baseline-.*` which matches the auto-rebalancer
volumes used to measure the system latency).

```bash title="Watch a node removal drain its volumes"
kubectl get storagenodeops drain-worker-1 -n simplyblock \
  -o jsonpath='{.status.subPhase} migrated={.status.volumesMigrated} pending={.status.volumesPending}{"\n"}' -w
```

For how removal coordinates with Kubernetes node cordon/drain and `maxFaultTolerance`, see
[Draining Coordination of a Kubernetes Worker Node](node-drain-coordination.md).

### Pinned Volumes

A volume is *pinned* when its PVC carries the `simplyblock.io/selected-storage-node` annotation. A pinned
volume is never moved by auto-rebalancing. By default, a pinned volume **blocks** a node removal. Pinned volumes need
to be explicitly directed to a target node before removal.

To allow a pinned volume to migrate during removal, set the annotation value to the UUID of the target node
it should move *to*:

```bash title="Direct a pinned volume to a specific target node before removal"
kubectl annotate pvc <pvc-name> -n <namespace> \
  simplyblock.io/selected-storage-node=<target-storage-node-uuid> --overwrite
```

| Annotation value                                                  | Removal behaviour                                                |
|-------------------------------------------------------------------|------------------------------------------------------------------|
| A valid storage node UUID (different from the node being removed) | Volume is migrated to that node; removal proceeds.               |
| Empty / absent                                                    | Volume is not pinned; the operator picks a target automatically. |
| A non-UUID value                                                  | Removal is blocked. An `InvalidPinTarget` event is emitted.      |
| The UUID of the node being removed                                | Removal is blocked. A `PinnedVolumeBlocking` event is emitted.   |

Volumes whose backing logical volume has no corresponding PV (for example, a volume created outside 
Kubernetes) also block removal, with an `UnmanagedVolumeBlocking` event, until they are resolved.

```bash title="Check for blocking events during a stalled removal"
kubectl get events -n simplyblock \
  --field-selector reason=PinnedVolumeBlocking
kubectl get events -n simplyblock \
  --field-selector reason=UnmanagedVolumeBlocking
```

## Data Realignment

After volumes move, whether by manual migration, auto-rebalancing, or drain/removal, the operator automatically
periodically re-aligns the cluster's internal data structures to the new placement so that fault-tolerance
(FTT) and node-affinity guarantees are preserved. This is enabled by default and configured under
`volumeMigrationSettings.dataRealignment` (see [Enabling Volume Migration](#enabling-volume-migration)).

The operator triggers a realignment on its own schedule whenever at least one volume has moved since the last
successful realignment. However, a realignment can also be trigger immediately by annotating the
`StorageCluster`:

```bash title="Trigger a data realignment immediately"
kubectl annotate storagecluster simplyblock-cluster -n simplyblock \
  simplyblock.io/trigger-realignment="$(date +%s)" --overwrite
```

## Events

The operator emits Kubernetes events on the affected resources throughout a migration. Useful reasons to
filter on:

| Reason                      | Meaning                                                                |
|-----------------------------|------------------------------------------------------------------------|
| `MigrationRequested`        | A `VolumeMigration` was accepted and submitted.                        |
| `MigrationStarted`          | The backend migration is running.                                      |
| `MigrationCompleted`        | The volume finished migrating to the target node.                      |
| `MigrationFailed`           | The migration failed; see the event message and `status.errorMessage`. |
| `MigrationAborted`          | The migration was cancelled via `spec.abort`.                          |
| `MigrationStuck`            | A migration has not progressed within the expected time.               |
| `VolumeRebalancingStarted`  | Auto-rebalancing began moving a volume.                                |
| `VolumeRebalancingComplete` | An auto-rebalancing migration finished.                                |
| `VolumeRebalancingDeferred` | A rebalancing move was skipped this cycle (e.g. cool-down).            |
| `PinnedVolumeBlocking`      | A pinned volume is blocking a node removal.                            |
| `UnmanagedVolumeBlocking`   | A volume without a PV is blocking a node removal.                      |
| `InvalidPinTarget`          | A pin annotation value is not a known storage node UUID.               |
| `DataRealignmentTriggered`  | A post-migration data realignment was started.                         |

```bash title="Stream migration-related events"
kubectl get events -n simplyblock --watch \
  --field-selector reason=MigrationCompleted
```
