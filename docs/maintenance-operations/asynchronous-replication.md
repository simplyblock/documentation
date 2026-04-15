---
title: "Asynchronous Replication"
description: "Configure and operate simplyblock snapshot-based asynchronous replication across clusters with automatic failover and manual failback."
weight: 10650
---

Simplyblock provides a snapshot-based asynchronous replication mechanism that replicates volumes at regular intervals.
For each interval, simplyblock takes a copy-on-write snapshot on the source and replicates it to a volume in a storage
pool on the target storage cluster.

For the architecture background, see [Replication Concepts](../architecture/concepts/replication.md).

## Scope and Prerequisites

- Asynchronous replication with automatic failover and controlled failback is a Kubernetes-only feature.
- It is managed by the Simplyblock Manager (Kubernetes operator) using the `SnapshotReplication` CRD.
- Source and target storage clusters must be attached to the same simplyblock control plane.
- The two simplyblock clusters (source and target) must have network interconnectivity.
- Both clusters must be activated and have storage nodes online.

!!! note
    For multi-site setups (for example, DR / offsite failover), using a distributed control plane is highly recommended.
    A typical setup is 2 management nodes on the main site and 3 management nodes on the failover site, so quorum /
    consensus can be maintained during a site failure.

## Enabling Replication on Volumes

Replication participation is controlled on volumes by setting `replicate: true`.

```yaml title="Example enabling replication via a storage class"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: encrypted-volumes
provisioner: csi.simplyblock.io
parameters:
  replicate: true
  ... other parameters
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

## Configuring Source and Target

Replication also requires a source/target cluster and target storage pool configuration via `SnapshotReplication`.

```yaml title="Example enabling asynchronous replication"
apiVersion: storage.simplyblock.io/v1alpha1
kind: SnapshotReplication
metadata:
  name: simplyblock-snapshot-replication
  namespace: simplyblock
spec:
  sourceCluster: <SOURCE_SIMPLYBLOCK_CLUSTER>
  targetCluster: <TARGET_SIMPLYBLOCK_CLUSTER>
  targetPool: <TARGET_CLUSTER2_STORAGE_POOL>
  interval: <REPLICATION_INTERVAL>
```

### SnapshotReplication Spec Fields

| Field              | Type       | Description                                                                               |
|--------------------|------------|-------------------------------------------------------------------------------------------|
| `sourceCluster`    | string     | Source simplyblock cluster name. Required.                                                |
| `targetCluster`    | string     | Target simplyblock cluster name. Required.                                                |
| `targetPool`       | string     | Target storage pool for replicated volumes. Required.                                     |
| `interval`         | int/string | Interval for creating new replication snapshots. Required.                                |
| `timeout`          | int/string | Per-task replication timeout. Optional. Defaults to `60` seconds (control plane default). |
| `action`           | string     | Lifecycle action. Use `failback` to trigger failback after source recovery.               |
| `sourcePool`       | string     | Source storage pool, required for failback workflows.                                     |
| `includeVolumeIDs` | []string   | Optional list of volumes to include in replication/failback.                              |
| `excludeVolumeIDs` | []string   | Optional list of volumes to exclude from replication/failback.                            |

## Replication Cycle and Queue Behavior

At each configured interval:

1. A copy-on-write snapshot is taken for the logical volume.
2. A replication task is created and added to the replication queue.
3. Queue tasks are processed one-by-one.

`SnapshotReplication.spec.interval` defines how often new snapshots are scheduled.

`SnapshotReplication.spec.timeout` limits the maximum runtime of a replication task. By default, the control plane
uses `60` seconds if not explicitly configured.

To avoid queue exhaustion from stacked tasks (for example when replication is slower than snapshot creation, or the
target cluster is unreachable), set `timeout` lower than or up to a maximum of approximately `1.5x` the `interval`.

## Monitoring Replication Status

The operator tracks replication progress per volume in the `SnapshotReplication` status.

```bash
kubectl get snapshotreplication \
  simplyblock-snapshot-replication \
  -n simplyblock -o yaml
```

Status includes per-volume replication details such as the last replicated snapshot, counters, and timestamps.

## Failover

Failover to the target cluster happens automatically when the source cluster becomes unhealthy or unavailable.

- The source cluster status is `suspended`, or
- All storage nodes in the source cluster are `unreachable`.

When these conditions are met, replicated volumes are switched to the target cluster and begin serving I/O
automatically.

!!! warning
    Data written on the source after the last successful replication snapshot is not available on the target.
    The data gap is at least the configured replication interval, plus any replication lag.

## Failback

Failback is exclusively user-initiated. It is an active/manual process that must be triggered by the user through a
`SnapshotReplication` CRD with `action: failback`.

!!! important
    Failback requires a minimal downtime window during the final synchronization/cutback phase. For production
    workloads, plan and schedule a maintenance window whenever needed.

The failback process:

1. Create a snapshot on the target and replicate it back to the source.
2. Wait for replication completion.
3. Suspend target I/O to freeze the final delta.
4. Replicate the remaining delta to the source.
5. Remove the failover copy on the target.
6. Resume serving I/O from the source.

```yaml title="Example of failback"
apiVersion: storage.simplyblock.io/v1alpha1
kind: SnapshotReplication
metadata:
  name: simplyblock-snap-replication-failback
  namespace: simplyblock
spec:
  sourceCluster: simplyblock-cluster
  targetCluster: simplyblock-cluster2
  targetPool: simplyblock-pool2
  sourcePool: simplyblock-pool
  action: failback
```

!!! note
    The two-phase failback replication minimizes the I/O freeze window by transferring most data before the final
    short delta synchronization step.
