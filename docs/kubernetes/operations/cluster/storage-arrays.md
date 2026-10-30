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

Capacity is added in one of three ways:

- **Within the existing LUNs:** Thin LUNs that were created large from the start only need more physical capacity in
  the array's pool. Simplyblock is not involved.
- **By growing the LUNs:** The data LUNs of all workers are grown on the array by the same factor, and the storage
  devices then take the new size online (see [Growing the LUNs](#growing-the-luns)).
- **With new storage nodes:** New workers with their own journal and data LUNs are added to the cluster with a
  growth deployment document (see [Expanding a Storage Cluster](../scaling/expanding-storage-cluster.md)). The data
  is rebalanced onto the new LUNs.

!!! warning
    Adding a LUN to a running storage node is not supported yet. A LUN must never be shrunk: the data beyond its new
    end is lost. Simplyblock refuses to take a smaller size and raises a `device_shrunk` alert.

### Growing the LUNs

Data is spread over the storage devices in proportion to their placement weights, which are fixed when a device
enters the cluster and never change afterward. A growth therefore never moves data, and it is always uniform: every
data device of the cluster grows by the same factor, the smallest growth of any of the data LUNs.

- **Same factor (recommended):** For example, every data LUN grows from 2 TiB to 3 TiB. Every device grows by 1.5,
  and the whole added capacity is usable.
- **Different factors:** For example, three LUNs grow by 1.5 and three by 2.0. Every device grows by 1.5. The rest of
  the larger LUNs stays unused and is reported as unused capacity. It becomes usable once the other LUNs have grown
  as far.
- **A LUN that has not grown:** Nothing grows, because the smallest factor is 1.
- **A smaller LUN:** Shrinking is not supported. The growth is refused for the whole cluster, the control plane raises
  a `device_shrunk` alert, and the LUN must be restored to at least its previous size.

1. Grow every data LUN on the array by the same factor and wait until the array has finished. The journal LUNs do
   not need to grow.
2. Let the storage devices take their new size with a `StorageClusterOps` with the action `GrowDevices`, once for all
   LUNs.

```yaml title="Growing every device of a cluster (grow-devices.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageClusterOps
metadata:
  name: grow-devices
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  action: GrowDevices
```

```bash title="Starting and following the growth"
kubectl apply -f grow-devices.yaml
kubectl get storageclusterops grow-devices -n simplyblock \
    -o jsonpath='{.status.deviceGrowth}' | jq .
```

The host of each storage node rescans its data LUNs. Every storage device then takes its new size without
interrupting I/O: its pending I/O is drained and held for a moment while it switches over. All data devices and their
storage nodes must be online; otherwise nothing grows.

`status.deviceGrowth` records the outcome:

| Field         | Meaning                                                                                         |
|---------------|-------------------------------------------------------------------------------------------------|
| `grown`       | Whether the devices grew.                                                                       |
| `factor`      | The factor every data device grew by, or `1` when nothing grew.                                 |
| `reason`      | Why nothing grew, for example, because a LUN has not grown yet.                                 |
| `devices`     | Every data device with its new `size` and the `unusedBytes` of its LUN beyond that size.        |
| `unusedBytes` | The unused capacity of all LUNs together.                                                       |
| `errors`      | The devices that stopped the growth, with the reason, for example, a device that is not online. |
| `shrunk`      | The devices whose LUN is smaller than the device.                                               |

A growth emits a `DevicesGrown` event with the factor and the unused capacity. When no LUN has grown, or not all of
them have, the operation succeeds with a `DevicesNotGrown` event. A shrunk LUN or a device that stopped the growth
fails the operation, and a shrunk LUN also emits a `DeviceShrunk` warning. Running `GrowDevices` again is safe: without
new growth on the array, nothing changes.

A storage node that is added after a growth gets weights on the same scale as the grown devices, so it receives its
share of the data in proportion to its real size.

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
