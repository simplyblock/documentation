---
title: "Operating on Storage Arrays"
description: "Operate a simplyblock cluster on storage array LUNs: capacity on two thin-provisioning levels, adding capacity, LUN resizing, failures, and data protection."
weight: 10165
---

A storage cluster on the LUNs of a [storage array](../../../architecture/concepts/storage-arrays.md) is operated like
any other simplyblock cluster. This page covers what is different: capacity on two levels, the growth of the
cluster, and the tasks that stay with simplyblock instead of the array.

## Monitoring Capacity

Capacity is thin-provisioned twice, and both levels are monitored:

| Level       | What is watched                                                      | Where                                                                                                           |
|-------------|----------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| Simplyblock | Used and provisioned capacity of the cluster, its pools, and volumes | [Cluster Health](../monitoring/cluster-health.md) and [Prometheus Metrics](../monitoring/prometheus-metrics.md) |
| Array       | Used capacity of the thin pool that holds the LUNs                   | The monitoring of the array                                                                                     |

Simplyblock does not return freed capacity to the array, so the array's allocation of the LUNs only grows. It
roughly equals the raw capacity simplyblock has used at its peak, including parity. An alert on the array's thin
pool must fire well before it is full: a full pool fails the writes of all LUNs at once and takes the cluster
offline.

## Adding Capacity

Capacity is added with new LUNs, not by growing existing ones:

- **Within the existing LUNs:** Thin LUNs that were created large from the start only need more physical capacity in
  the array's pool. Simplyblock is not involved.
- **With new storage nodes:** New workers with their own LUNs are added to the cluster with a growth deployment
  document (see [Expanding a Storage Cluster](../scaling/expanding-storage-cluster.md)). The data is rebalanced onto
  the new LUNs.

!!! warning
    Adding a LUN to a running storage node is not supported yet, and a LUN must not be resized while a storage node
    uses it. A resized LUN is not picked up, and shrinking a LUN destroys data.

## The Journal

The journal of a storage node lives on a partition of the LUN it was carved from when the node was configured, or on
the dedicated journal LUN. It stays there for the life of the node: LUNs that reach the node later, for example,
when the node is added again with more LUNs, store data but receive no share of the journal.

On a storage array, this is acceptable. The array's RAID protects the journal LUN like every other LUN, and every
write is journaled on other storage nodes as well, so the loss of a host or of its LUN does not lose the journal.

## Snapshots, Clones, and Disaster Recovery

Snapshots, clones, replication, backups, and disaster recovery are done in simplyblock only:

- [Snapshotting](../../usage/snapshotting.md) and [Cloning](../../usage/cloning.md) for point-in-time copies.
- [Backup and Recovery](../data-protection/backup-recovery.md) for copies on S3.
- [Asynchronous Replication](../data-protection/asynchronous-replication.md) and
  [Disaster Recovery](../../../disaster-recovery/index.md) for copies on another cluster.

Array snapshots and array replication are not used for simplyblock LUNs. They are not consistent across the LUNs of
all workers, and a simplyblock cluster cannot be restored from them.

## Failures and Maintenance

- **Drive failures** are handled by the array's RAID. Simplyblock does not see them.
- **LUN or path failures** of a worker are handled by simplyblock like a device failure. A LUN that returns after a
  short outage is re-admitted automatically. A LUN that is lost for good is failed and its data rebuilt onto the
  other LUNs (see [Failing a Storage Device](../storage-nodes/storage-node-actions.md#failing-a-storage-device)).
- **Slow LUNs** are detected by the performance monitoring of simplyblock. SMART checks are not available for LUNs,
  so the health of the drives is monitored by the array (see [Device Health](../monitoring/device-health.md)).
- **Array maintenance** that interrupts the I/O of all LUNs, such as a disruptive firmware update, requires the
  storage cluster to be shut down first (see [Shutting Down a Storage Cluster](shutting-down-a-cluster.md)).
  Non-disruptive array maintenance needs no action in simplyblock.
