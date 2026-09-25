---
title: "Volume Migration"
description: "Move the backing logical volume of a PersistentVolume between storage nodes with PersistentVolumeOps, by hand, on a pin change, or when a node is drained."
weight: 10410
---

The Simplyblock Operator can move a volume's backing logical volume from one storage node to another while the volume
stays online (live migration). A migration relocates a logical volume (and its snapshots). It does not move the
storage node itself. This is different from [Migrating a Storage Node](../storage-nodes/migrating-a-storage-node.md),
which relocates an entire storage node identity to a new host.

A volume migration moves only the logical volume itself, not the actual data. Since data remains distributed in the
back storage, a volume migration is an online live migration and nearly instant. If node affinity is turned on for a
cluster, the back storage data is realigned asynchronously after one or more volume migrations have finished (see
[Data Realignment](#data-realignment)).

Every migration is carried out by a `PersistentVolumeOps` operation (short name `pvops`) with `action: Migrate`. Four
sources create one:

- **Manual migration:** an administrator creates the `PersistentVolumeOps` object directly.
- **Pin change:** the `storage.simplyblock.io/selected-storage-node` annotation of a bound claim is changed to another
  storage node.
- **Drain and removal:** a `StorageNodeOps` operation with `action: Remove` evacuates the volumes of the node.
- **Auto-rebalancing:** the operator moves volumes off overloaded storage nodes.

All four share the same backend migration mechanism and the same post-migration data realignment. Volume migration
cannot be turned off, because a drain, a rebalance, and a device replacement are all performed by moving volumes.

## Manual Volume Migration

`PersistentVolumeOps` is a cluster-scoped kind, since a `PersistentVolume` is cluster-scoped. It names the
`PersistentVolume` to move and the target `StorageNode` object, not a backend UUID. The target is given with its
namespace, which is the namespace of the owning `StorageCluster`. The target has to belong to the same cluster as the
volume.

```yaml title="Example of a PersistentVolumeOps moving one volume (migrate-pvc.yaml)"
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
      name: production-9c21de
```

```bash title="Starting the migration"
kubectl apply -f migrate-pvc.yaml
```

`spec.persistentVolumeName`, `spec.action`, and `spec.migrate.targetNodeRef` are immutable. To migrate the same volume
again, or to a different target, a new `PersistentVolumeOps` object is created. Only one operation acts on a volume at
a time. The volume's lock is the annotation `storage.simplyblock.io/active-ops` on the `PersistentVolume`, and a second
operation waits in `Pending` with an `OperationQueued` event until the first one has finished.

The referenced `PersistentVolume` has to be provisioned by the simplyblock CSI driver. The cluster, pool, and volume
UUIDs are read from its volume handle, so the operation names no cluster.

### Finding Target Storage Nodes

The `StorageNode` objects of a cluster live in the namespace of the `StorageCluster`. The `-o wide` output adds the
backend UUID of each node.

```bash title="Listing the storage nodes of a cluster"
kubectl get storagenodes -n simplyblock -o wide
```

### Monitoring a Migration

```bash title="Watching all volume operations"
kubectl get persistentvolumeops -w
```

```bash title="Reading the full status of one operation"
kubectl get pvops migrate-pvc-968cff4f -o jsonpath='{.status}' | jq .
```

`status.phase` is one of `Pending`, `Running`, `Succeeded`, `Failed`, or `Aborted`, the same five phases every
operation kind reports. While the phase is `Running`, `status.step.state` names the current step.

| Step         | Description                                                                                                                |
|--------------|----------------------------------------------------------------------------------------------------------------------------|
| `Validating` | The backend migration is created, and a Job on every node consuming the subsystem checks that the new target paths answer. |
| `Migrating`  | The migration is continued on the backend, which starts the data copy.                                                     |
| `Verifying`  | The validation Jobs are deleted, and no leftover path is allowed to stay connected.                                        |

`status.migration` records the resolved `sourceNodeUUID`, `targetNodeUUID`, `volumeUUID`, `poolUUID`, `clusterUUID`,
the backend `migrationUUID`, the published `connections`, and the `validationJobs`. `status.message` carries the
latest human-readable progress, and `status.startedAt` and `status.completedAt` the timestamps.

### Aborting a Migration

A running migration is stopped by setting `spec.abort` to `true`. The operation unwinds and ends in `Aborted`.

!!! warning
    A migration can be aborted in the `Validating` and the `Migrating` steps only. Once `Verifying` is reached, the
    copy has finished and the volume has moved, so there is nothing to undo.

```bash title="Aborting a running migration"
kubectl patch pvops migrate-pvc-968cff4f --type merge -p '{"spec":{"abort":true}}'
```

### Migrating by Pinning a PVC

Setting the `storage.simplyblock.io/selected-storage-node` annotation of an already-bound PVC to another storage node
moves the volume there. The operator creates the `PersistentVolumeOps` on behalf of the user, and it records the pin it
acted on in `storage.simplyblock.io/selected-storage-node-applied`. This is the same annotation that
[pins a volume](#pinned-volumes) against auto-rebalancing and node removal.

```bash title="Pinning a bound PVC to a new node to trigger a migration"
kubectl annotate pvc <pvc-name> -n <namespace> \
  storage.simplyblock.io/selected-storage-node=<target-storage-node-uuid> --overwrite
```

The value is the backend UUID of a storage node of the volume's cluster (the `UUID` column of `kubectl get sn -o wide`).
An unknown UUID is rejected by the PVC webhook. A value that cannot be resolved later is reported with an
`InvalidPinTarget` event on the claim, and a successful request with a `MigrationRequested` event. The older spelling
`simplyblock.io/selected-storage-node` is still read.

## Auto-Rebalancing

{{ experimental }}

When enabled, the operator continuously evaluates the per-node load and migrates volumes off overloaded ("hot") nodes
onto less-loaded ("cold") nodes. It creates the same `PersistentVolumeOps` objects as a manual migration, so every
move stays observable through `kubectl get pvops`.

Auto-rebalancing is switched on by `StorageCluster.spec.enableVolumeAutoPlacement` and tuned under
`StorageCluster.spec.volumeAutoPlacement`. It is disabled by default.

```yaml title="Example of latency-driven auto-rebalancing on a StorageCluster"
spec:
  enableVolumeAutoPlacement: true
  volumeAutoPlacement:
    metricsBackend: Prometheus
    prometheusURL: http://prometheus.simplyblock.svc:9090
    enableLatencyBenchmark: true
    evaluationInterval: 60s
    imbalanceThreshold: 80
    maxVolumeMigrationsPerCycle: 10
```

!!! warning
    Automatic rebalancing is considered an experimental feature. Its algorithm is subject to change and is not optimal.
    It is not yet recommended for any production environment.

| Field                         | Default         | Description                                                                                                  |
|-------------------------------|-----------------|--------------------------------------------------------------------------------------------------------------|
| `disableMigration`            | `false`         | When `true`, every cycle runs but its migrations are discarded instead of created (dry run).                 |
| `evaluationInterval`          | `60s`           | How often the rebalancer evaluates load.                                                                     |
| `imbalanceThreshold`          | `80`            | Latency deviation from baseline (percent) a node has to exceed before it is considered a rebalancing source. |
| `minHotColdDifferencePct`     | `20`            | How far below the source (percentage points of deviation) a target has to be before a volume is moved.       |
| `maxVolumeMigrationsPerCycle` | `10`            | Maximum number of volumes moved per cycle.                                                                   |
| `storageNodeCandidateCount`   | `3`             | Number of most loaded nodes evaluated each cycle to pick the migration source.                               |
| `defaultCoolDownSeconds`      | `600`           | Time a volume is left alone after it has been migrated.                                                      |
| `metricsBackend`              | `Prometheus`    | Source of I/O metrics: `Prometheus`, `ControlPlane`, or `Uniform`. `Uniform` disables IOPS-based scoring.    |
| `prometheusURL`               | none            | Required when `metricsBackend` is `Prometheus`.                                                              |
| `enableLatencyBenchmark`      | `false`         | Enables `fio`-based NVMe-oF latency measurement through Kubernetes Jobs.                                     |
| `latencyBenchmarkInterval`    | `5m`            | How often the benchmark Jobs run against each storage node.                                                  |
| `baselineStrategy`            | `RollingWindow` | How the per-node latency baseline is derived: `RollingWindow` or `Benchmark` (one-shot measurement).         |
| `baselineWindow`              | `6h`            | Look-back window of the `RollingWindow` strategy.                                                            |
| `baselineColdStart`           | `PartialWindow` | Handling of an under-sampled node: `PartialWindow` uses the samples there are, `Defer` leaves the node out.  |
| `baselineMinSamples`          | `6`             | Sample count below which a node counts as under-sampled.                                                     |
| `baselineOutlierK`            | `3.0`           | Outlier rejection threshold of the baseline estimator. A lower value rejects more samples.                   |
| `iopsWeight`                  | `1.0`           | Weight of per-volume IOPS in the volume I/O score.                                                           |
| `throughputWeight`            | `0.1`           | Weight of per-volume throughput (MB/s) in the volume I/O score.                                              |

The results of every cycle are written to `StorageCluster.status.rebalancingMetrics`, including the hottest and the
coolest node, the imbalance, and the per-node deviation.

!!! tip
    Start with `disableMigration: true` (dry run). The rebalancer still evaluates load, computes deviations, selects
    candidates, and emits metrics and events, but does not move any data. Once the selected candidates look correct,
    remove the field or set it to `false`.

!!! note
    Volumes that are pinned to a specific storage node (see [Pinned Volumes](#pinned-volumes)) are not subject to
    auto-rebalancing. A one-shot placement hint from initial provisioning does not pin a volume, so such volumes
    remain eligible for rebalancing.

!!! note
    Setting `enableLatencyBenchmark: true` also activates load-aware placement for newly created volumes, independent
    of `enableVolumeAutoPlacement`. See [Automatic Volume Placement](../../usage/volume-placement.md).

## Volume Migration Settings

`StorageCluster.spec.volumeMigrationSettings` controls how migrations and the post-migration realignment behave, not
whether they happen.

```yaml title="Example of volume migration settings on a StorageCluster"
spec:
  enableDataRealignment: true
  volumeMigrationSettings:
    rebalancerImage: quay.io/simplyblock-io/simplyblock-rebalancer:latest
    dataRealignment:
      interval: 10m
      minMoves: 1
```

| Field                      | Default | Description                                                                                                                             |
|----------------------------|---------|-----------------------------------------------------------------------------------------------------------------------------------------|
| `rebalancerImage`          | none    | Image of the path-validation Jobs and of the rebalancer's latency Jobs. It has to carry `nvme-cli`, and for rebalancing `fio` and `jq`. |
| `dataRealignment.interval` | `10m`   | Minimum spacing between two realignment requests.                                                                                       |
| `dataRealignment.minMoves` | `1`     | Number of volume moves that accumulate before a realignment is requested. A higher value batches realignments.                          |

## Volume Migration During Node Draining and Removal

When a storage node is removed, the operator evacuates its volumes onto the remaining nodes before the node leaves the
cluster. Removal is triggered by a `StorageNodeOps` operation with `action: Remove`, and each PersistentVolume-backed
volume of the node gets its own `PersistentVolumeOps`. The full workflow is described in
[Removing a Storage Node](../storage-nodes/removing-a-storage-node.md).

```yaml title="Example of a node removal that drains its volumes first"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageNodeOps
metadata:
  name: remove-7f3a9c
  namespace: simplyblock
spec:
  nodeRef: production-7f3a9c
  action: Remove
```

The operations a drain created carry the label `storage.simplyblock.io/managed-by` and name the draining
`StorageNodeOps` in `spec.creatorRef`. Progress is reported in `StorageNodeOps.status.drain.volumesTotal` and
`status.drain.volumesMigrated`.

```bash title="Watching a node removal drain its volumes"
kubectl get storagenodeops remove-7f3a9c -n simplyblock \
  -o jsonpath='{.status.step.state} {.status.drain.volumesMigrated}/{.status.drain.volumesTotal}{"\n"}' -w
```

System volumes are not migrated. They are matched by `spec.remove.systemVolumeFilterRegex` (default
`^sb-fio-baseline-.*`, which matches the rebalancer's own benchmark volumes) and deleted during the `Verifying` step.

### Pinned Volumes

A volume is *pinned* when its PVC carries the `storage.simplyblock.io/selected-storage-node` annotation. A pinned
volume is never moved by auto-rebalancing, and a pinned volume on a node **blocks** the removal of that node. The
operator does not remove the annotation on behalf of the user, because a pin is a deliberate placement decision.

A blocked removal is resolved in one of two ways:

- **Re-pin the volume:** set the annotation to the UUID of another storage node. The volume is migrated there, as
  described in [Migrating by Pinning a PVC](#migrating-by-pinning-a-pvc), and no longer sits on the node being
  removed.
- **Unpin the volume:** remove the annotation. The drain then picks a target for it.

Volumes whose backing logical volume has no corresponding PersistentVolume (for example, a volume created outside
Kubernetes) also block the removal, until they are removed by hand. In both cases the `StorageNodeOps` stays in its
`Validating` step, and a `DrainBlocked` event names the blocking volumes.

```bash title="Checking for blocking volumes during a stalled removal"
kubectl get events -n simplyblock --field-selector reason=DrainBlocked
```

For how removal coordinates with a Kubernetes node cordon and drain, see
[Draining Coordination of a Kubernetes Worker Node](../storage-nodes/node-drain-coordination.md).

## Data Realignment

After volumes have moved, whether by manual migration, a pin change, auto-rebalancing, or a drain, the operator can
realign the cluster's internal data structures to the new placement, so that fault-tolerance (FTT) and node-affinity
guarantees are preserved. Realignment is switched on by `StorageCluster.spec.enableDataRealignment` and is off unless
the field is set. It is tuned under `volumeMigrationSettings.dataRealignment` (see
[Volume Migration Settings](#volume-migration-settings)).

A realignment is requested once at least `minMoves` volumes have moved since the last successful realignment, at least
`interval` has passed, and no volume is currently moving. Progress is visible in `StorageCluster.status`:
`volumeMoveGeneration` counts the moves, `realignedGeneration` the moves covered by the last realignment, and
`lastDataRealignmentAt` holds its time.

A realignment can also be requested immediately by annotating the `StorageCluster`, which bypasses the spacing rules.
Realignment has to be enabled for the annotation to take effect.

```bash title="Triggering a data realignment immediately"
kubectl annotate storagecluster production -n simplyblock \
  simplyblock.io/trigger-realignment="$(date +%s)" --overwrite
```

## Legacy VolumeMigration

The `VolumeMigration` kind (`storage.simplyblock.io/v1alpha1`, short name `vmig`) is the predecessor of
`PersistentVolumeOps`. Its controller only runs when the Helm value `volumeMigration.legacy` is `true`, which is meant
for an upgrade, for as long as migrations already raised against the old kind take to finish. With the default of
`false`, every migration is raised as a `PersistentVolumeOps`.

| VolumeMigration field or phase | PersistentVolumeOps equivalent |
|--------------------------------|--------------------------------|
| `spec.pvName`                  | `spec.persistentVolumeName`    |
| `spec.targetNodeUUID`          | `spec.migrate.targetNodeRef`   |
| phase `Completed`              | phase `Succeeded`              |

## Events

The operator emits Kubernetes events on the affected objects throughout a migration. Useful reasons to filter on:

| Reason                      | Emitted on              | Meaning                                                               |
|-----------------------------|-------------------------|-----------------------------------------------------------------------|
| `OperationQueued`           | `PersistentVolumeOps`   | The operation waits for another operation on the same volume.         |
| `OperationStarted`          | `PersistentVolumeOps`   | The operation took the volume's lock and started.                     |
| `MigrationCreated`          | `PersistentVolumeOps`   | The backend migration was created.                                    |
| `MigrationStarted`          | `PersistentVolumeOps`   | The data copy was started.                                            |
| `TargetNodeNotReady`        | `PersistentVolumeOps`   | The target storage node is not ready to receive the volume.           |
| `TargetNodeIsSource`        | `PersistentVolumeOps`   | The target is the node the volume already lives on.                   |
| `StepDeadlineExceeded`      | `PersistentVolumeOps`   | A step has not finished within its deadline.                          |
| `OperationSucceeded`        | `PersistentVolumeOps`   | The volume now resides on the target node.                            |
| `OperationFailed`           | `PersistentVolumeOps`   | The migration failed. See the event message and `status.message`.     |
| `OperationAborted`          | `PersistentVolumeOps`   | The migration was stopped through `spec.abort`.                       |
| `MigrationRequested`        | `PersistentVolumeClaim` | A pin change raised a migration.                                      |
| `InvalidPinTarget`          | `PersistentVolumeClaim` | A pin annotation value is not a known storage node UUID.              |
| `VolumeRebalancingStarted`  | `StorageCluster`        | Auto-rebalancing began moving a volume.                               |
| `VolumeRebalancingComplete` | `StorageCluster`        | An auto-rebalancing migration finished.                               |
| `VolumeRebalancingDeferred` | `StorageCluster`        | A rebalancing move was skipped this cycle, for example, by cool-down. |
| `DataRealignmentTriggered`  | `StorageCluster`        | A post-migration data realignment was requested.                      |
| `DrainBlocked`              | `StorageNodeOps`        | A pinned or an unmanaged volume is blocking a node removal.           |

```bash title="Streaming completed migrations"
kubectl get events -A --watch --field-selector reason=OperationSucceeded,involvedObject.kind=PersistentVolumeOps
```
