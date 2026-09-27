---
title: "Volume Migration"
description: "How the Simplyblock Operator migrates the backing logical volume of a volume between storage nodes, manually or automatically when a node is drained."
weight: 10410
---

The Simplyblock Operator can move a volume's backing logical volume from one storage node to another
while the volume stays online (live migration). A migration relocates a logical volume (and its snapshots). It
does not move the storage node itself. This is different from
[Migrating a Storage Node](../storage-nodes/migrating-a-storage-node.md), which relocates an entire storage node identity to a
new host.

A volume migration moves only the logical volume itself, not the actual data. Since data remains distributed in the back
storage, volume migrations is an online live migration and nearly instant. If node affinity is turned on for a cluster,
back storage data realignment happens via rebalancing as an asynchronous task after one or more the volume migration(s)
finished.

Volume migration is used in three ways:

- **Manual migration:** requests a specific volume to move to a specific target node.
- **Drain / removal migration:** the operator automatically evacuates a node's volumes before it is removed.
- **Auto-rebalancing:** the operator continuously moves volumes off overloaded nodes.

All three paths share the same backend migration mechanism and the same post-migration
[data realignment](#data-realignment).

## Volume Migration Settings

Volume migration cannot be turned off: a drain, a rebalance, and a device replacement are all performed by moving
volumes. What is configurable is the post-migration realignment and the image the path-validation Job runs.

```yaml title="Volume migration settings"
spec:
  disableDataRealignment: false         # default: false, realignment is on
  volumeMigrationSettings:
    dataRealignment:
      interval: 10m                     # default: 10m
      minMoves: 1
```

| Field                                                   | Default | Description                                                               |
|---------------------------------------------------------|---------|---------------------------------------------------------------------------|
| `spec.disableDataRealignment`                           | `false` | Turns off automatic post-migration [data realignment](#data-realignment). |
| `spec.volumeMigrationSettings.dataRealignment.interval` | `10m`   | How often the operator checks whether a realignment is pending.           |
| `spec.volumeMigrationSettings.dataRealignment.minMoves` | —       | The number of moves below which a realignment is not worth running.       |
| `spec.volumeMigrationSettings.rebalancerImage`          | —       | The image the migration path-validation Job runs.                         |

`disableDataRealignment` is a field of the cluster spec rather than of the block it governs, because
`volumeMigrationSettings.dataRealignment.disableDataRealignment` says the same word twice.

## Manual Volume Migration

A manual migration is triggered by creating a `PersistentVolumeOps` resource (short name `pvops`) that names the
`PersistentVolume` to move and the `StorageNode` to move it to.

`PersistentVolumeOps` is cluster-scoped, because its target is: a `PersistentVolume` is a cluster-scoped object, and
it is the one operations kind in the group whose target is a core Kubernetes type rather than one this group
defines.

```bash title="Migrate a single volume to a target node"
kubectl apply -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha2
kind: PersistentVolumeOps
metadata:
  name: migrate-pvc-968cff4f
spec:
  persistentVolumeName: pvc-968cff4f-a199-4964-88f0-7cfccb5251d9
  action: Migrate
  migrate:
    targetNodeRef:
      namespace: simplyblock
      name: simplyblock-node-o6x20i
EOF
```

`spec.persistentVolumeName`, `spec.action`, and `spec.migrate.targetNodeRef` are immutable. To migrate the same
volume again, or to a different target, create a new `PersistentVolumeOps` resource.

The referenced PV must be provisioned by the Simplyblock CSI driver. The operator resolves the PV to its
logical volume UUID, submits the migration to the storage API, validates the new NVMe-oF paths, and then
tracks progress to completion.

### Finding the Target Node

`targetNodeRef` names a `StorageNode` object rather than a backend UUID, so a migration can be written by hand
without looking one up.

```bash title="Listing the storage node CRs"
kubectl get storagenodes -n simplyblock
```

The backend UUID of each node is in its status, and the operation records both ends of the move in
`status.migration` once it has resolved them.

```bash title="Listing the storage nodes with their backend UUIDs"
kubectl get storagenodes -n simplyblock \
    -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.uuid}{"\n"}{end}'
```

### Monitoring a Migration

The resource exposes the current phase and step directly in its printer columns.

```bash title="Watch migration progress"
kubectl get persistentvolumeops -w
```

```bash title="Inspect full migration status"
kubectl get persistentvolumeops migrate-pvc-968cff4f -o jsonpath='{.status}' | jq .
```

Each migration progresses through the phases below, tracked in `status.phase`:

| Phase       | Description                                                          |
|-------------|----------------------------------------------------------------------|
| `Pending`   | The operation has been accepted and is waiting to start.             |
| `Running`   | In progress. `status.step.state` says where.                         |
| `Succeeded` | The volume now resides on the target node.                           |
| `Failed`    | The migration could not complete. `status.message` holds the reason. |
| `Aborted`   | The migration was canceled via `spec.abort`, and did not go wrong.   |

While it is `Running`, the step says what it is doing:

| Step         | Description                                                                               |
|--------------|-------------------------------------------------------------------------------------------|
| `Validating` | The new target-side NVMe-oF paths are being established and verified by a validation Job. |
| `Migrating`  | The backend is copying data and snapshots.                                                |
| `Verifying`  | The move is confirmed before the operation completes.                                     |

`status.migration` records the resolved `sourceNodeUUID`, `targetNodeUUID`, `volumeUUID`, `poolUUID`,
`clusterUUID`, the backend `migrationUUID`, the NVMe-oF `connections`, and the `validationJobs` that checked them.
`status.startedAt` and `status.completedAt` bracket the run.

### Aborting a Migration

An in-progress migration can be canceled by setting `spec.abort` to `true`. The phase transitions to
`Aborted` once the backend confirms the cancellation.

!!! important
    Whether an abort is expressible from the current step is declared by the action's state machine. A migration
    that is already copying data has to be able to complete to ensure data consistency, so an abort arriving then is
    reported as an illegal transition and the operation runs on.

```bash title="Abort an in-progress migration"
kubectl patch persistentvolumeops migrate-pvc-968cff4f \
  --type merge -p '{"spec":{"abort":true}}'
```

### Migrating by Pinning a PVC

There are also automated processes that create a `PersistentVolumeOps` resource, for example, setting the
`simplyblock.io/selected-storage-node` annotation on an already-bound PVC. This will effectively migrate the pinned
volume to a new storage node. The operator creates the operation on the user's behalf, as part of moving the volume
to that node. This is the same annotation that [pins a volume](#pinned-volumes) against auto-rebalancing and
node removal.

```bash title="Pin a bound PVC to a new node to trigger a migration"
kubectl annotate pvc <pvc-name> -n <namespace> \
  simplyblock.io/selected-storage-node=<target-storage-node-uuid> --overwrite
```

The annotation value must be a known storage node UUID. Any other value is rejected by a validating webhook.
If the value is not a valid node, the operator records it and emits an `InvalidPinTarget` event.

An operation created this way names the object that created it in `spec.creatorRef`, so a fan-out of migrations can
be traced back to the drain or rebalance that asked for them.

## Auto-Rebalancing

{{ experimental }}

When enabled, the operator continuously evaluates the per-node load and automatically migrates volumes off
overloaded ("hot") nodes onto less-loaded ("cold") nodes. Under the hood it creates the same
`PersistentVolumeOps` resources as a manual migration, so all migrations remain observable through `pvops`.

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

!!! note
    Setting `latencyBenchmarkEnabled: true` also activates load-aware placement for newly created volumes,
    independent of `migrationEnabled` (which only controls the continuous rebalancer above). See
    [Automatic Volume Placement](../../usage/volume-placement.md).

## Volume Migration During Node Draining and Removal

When a storage node is removed, the operator evacuates its volumes onto the remaining nodes before the node
leaves the cluster. Removal is triggered by a `StorageNodeOps` resource with `action: Remove`, and the full workflow
is described in [Removing a Storage Node](../storage-nodes/removing-a-storage-node.md).

```bash title="Remove a storage node (drains its volumes first)"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageNodeOps
metadata:
  name: drain-worker-1
  namespace: simplyblock
spec:
  nodeRef: simplyblock-node-mejue8
  action: Remove
EOF
```

While `status.phase` is `Running`, the removal advances through the drain steps tracked in
`StorageNodeOps.status.step.state`:

| Step               | Description                                                                                                     |
|--------------------|-----------------------------------------------------------------------------------------------------------------|
| `Validating`       | Preconditions are checked and the node's volumes are classified.                                                |
| `Suspending`       | The node is suspended so no new volumes are placed on it.                                                       |
| `MigratingVolumes` | Volumes are migrated off the node. `status.drain.volumesMigrated` / `status.drain.volumesTotal` track progress. |
| `Verifying`        | Migrations are confirmed and system volumes are cleaned up.                                                     |
| `Removing`         | The now-empty node is removed from the cluster.                                                                 |

System volumes are excluded from migration and deleted inline during `Verifying`. The set of system volumes
is matched by `spec.remove.systemVolumeFilterRegex` (default `^sb-fio-baseline-.*` which matches the auto-rebalancer
volumes used to measure the system latency).

```bash title="Watch a node removal drain its volumes"
kubectl get storagenodeops drain-worker-1 -n simplyblock \
  -o jsonpath='{.status.step.state} migrated={.status.drain.volumesMigrated}/{.status.drain.volumesTotal}{"\n"}' -w
```

For how removal coordinates with Kubernetes node cordon/drain and `maxFaultTolerance`, see
[Draining Coordination of a Kubernetes Worker Node](../storage-nodes/node-drain-coordination.md).

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

| Annotation value                                                  | Removal behavior                                               |
|-------------------------------------------------------------------|----------------------------------------------------------------|
| A valid storage node UUID (different from the node being removed) | Volume is migrated to that node, removal proceeds.             |
| Empty / absent                                                    | Volume is not pinned, a target is picked by the operator.      |
| A non-UUID value                                                  | Removal is blocked. An `InvalidPinTarget` event is emitted.    |
| The UUID of the node being removed                                | Removal is blocked. A `PinnedVolumeBlocking` event is emitted. |

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
`volumeMigrationSettings.dataRealignment` (see [Volume Migration Settings](#volume-migration-settings)).

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

| Reason                      | Meaning                                                           |
|-----------------------------|-------------------------------------------------------------------|
| `MigrationRequested`        | A `PersistentVolumeOps` was accepted and submitted.               |
| `MigrationStarted`          | The backend migration is running.                                 |
| `MigrationCompleted`        | The volume finished migrating to the target node.                 |
| `MigrationFailed`           | The migration failed. See the event message and `status.message`. |
| `MigrationAborted`          | The migration was canceled via `spec.abort`.                      |
| `MigrationStuck`            | A migration has not progressed within the expected time.          |
| `VolumeRebalancingStarted`  | Auto-rebalancing began moving a volume.                           |
| `VolumeRebalancingComplete` | An auto-rebalancing migration finished.                           |
| `VolumeRebalancingDeferred` | A rebalancing move was skipped this cycle (e.g., cool-down).      |
| `PinnedVolumeBlocking`      | A pinned volume is blocking a node removal.                       |
| `UnmanagedVolumeBlocking`   | A volume without a PV is blocking a node removal.                 |
| `InvalidPinTarget`          | A pin annotation value is not a known storage node UUID.          |
| `DataRealignmentTriggered`  | A post-migration data realignment was started.                    |

```bash title="Stream migration-related events"
kubectl get events -n simplyblock --watch \
  --field-selector reason=MigrationCompleted
```
