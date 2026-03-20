---
title: "Replication"
weight: 30800
---

Simplyblock supports snapshot-based replication between clusters for multi-site disaster recovery and data
availability. Replication ensures that snapshots of volumes on a source cluster are continuously transferred to a
remote target cluster, enabling recovery from site-level failures with automatic failover detection and controlled
failback.

## Snapshot Replication

Snapshot replication periodically transfers volume snapshots from a source cluster to a target cluster. Each replication
cycle creates a new snapshot on the source and transfers it to the target, building an incremental snapshot chain on
both sides.

Key characteristics:

- **Snapshot-Based:** Replication transfers volume snapshots at configurable intervals (minimum 60 seconds, default 300
  seconds).
- **Incremental:** Snapshots are chained on the target. Each replicated snapshot references its predecessor, enabling
  efficient copy-on-write storage.
- **Pool or Volume Scope:** Replication can be enabled for specific volumes. All volumes with replication enabled in a
  cluster are managed by a single replication relationship.
- **Per-Volume Tracking:** The operator tracks replication status per volume, including last replicated snapshot,
  replication count, and timestamps.
- **Automatic Task Management:** Each replication cycle creates a background task that handles the data transfer
  asynchronously. The operator waits for the previous task to complete before triggering the next cycle.

Snapshot replication is suitable for disaster recovery scenarios where a recovery point objective (RPO) of minutes is
acceptable. It can also be used for local and global CDN-like data distribution processes or for the site migration of
clusters.

## Replication Architecture

The replication system involves three components:

1. **Simplyblock Operator** ([simplyblock-manager](https://github.com/simplyblock/simplyblock-manager)): A Kubernetes
   operator that watches the `SimplyBlockSnapshotReplication` CRD and orchestrates replication cycles. It detects
   failover conditions and manages the failback process.

2. **Control Plane** (sbcli): The simplyblock management API handles the actual snapshot creation, data transfer via
   NVMe-oF connections, and snapshot chain management on both source and target clusters.

3. **Data Plane** (SPDK): The storage nodes perform block-level data transfer using `bdev_lvol_transfer` RPC calls
   over NVMe-oF connections between clusters.

## Failover

Failover is triggered **automatically** when the operator detects that the source cluster is in a failure state:

- The source cluster status is `suspended`, **and**
- All storage nodes in the source cluster are `unreachable`.

When both conditions are met, the operator initiates a one-time volume replication (`replicate_lvol`) for each
replicated volume, effectively migrating the full volume to the target cluster. The target volumes become primary and
begin serving I/O.

No manual action is required to trigger failover -- the operator detects the conditions and acts automatically.

!!! warning
    After failover, any data written to the source cluster since the last successful snapshot replication will not be
    available on the target. The data gap equals the replication interval plus any time the replication was behind
    schedule.

## Failback

Failback is triggered **manually** by setting `action: failback` on the `SimplyBlockSnapshotReplication` CRD after the
source cluster has been restored.

The failback process for each volume:

1. **Trigger replication on target:** Create a snapshot on the target and replicate it back to the source to capture
   changes made during failover.
2. **Wait for completion:** Poll until the replication task finishes.
3. **Suspend target volume:** Freeze I/O on the target to prevent further changes.
4. **Trigger final replication:** Capture and transfer the last delta since the previous replication.
5. **Wait for completion:** Ensure all data is synchronized.
6. **Delete target volume:** Remove the failover copy from the target cluster.
7. **Resume on source:** Notify the source cluster to resume serving the volume.

The failback process supports filtering volumes using `includeVolumeIDs` and `excludeVolumeIDs` for selective failback.

!!! note
    The two-phase replication (steps 1 and 4) minimizes the I/O freeze window. The first replication transfers the bulk
    of changes while the target is still active. The second replication only needs to transfer the small delta
    accumulated during the first transfer.

## Kubernetes Integration

In Kubernetes environments, replication is managed through the `SimplyBlockSnapshotReplication` CRD. For the full CRD
specification and examples, see
[Kubernetes CRD Reference](../../reference/kubernetes/crds.md#simplyblocksnapshotreplication).

For operational procedures, see [Replication Operations](../../maintenance-operations/replication.md).
