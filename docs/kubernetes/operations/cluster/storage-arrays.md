---
title: "Operating on Storage Arrays"
description: "Operate a simplyblock cluster on storage array LUNs: capacity on two thin-provisioning levels, adding capacity, LUN resizing, failures, and data protection."
weight: 10165
---

{{ experimental }}

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
    end is lost, and simplyblock refuses to take a smaller size.

### Growing the LUNs

A storage device keeps the placement weight it was given when it joined the cluster, because changing a weight would
re-place a large part of the data. Data is therefore spread over the devices in proportion to their original sizes.
The added capacity is only fully usable once all data LUNs of the cluster have grown by the same factor, for
example, all of them from 2 TiB to 4 TiB.

1. Grow every data LUN on the array by the same factor. The journal LUNs do not need to grow.
2. Let every storage device take its new size with a `StorageClusterOps` with the action `GrowDevices`.

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

The host of each storage node rescans the device, and the device takes its new size without interrupting I/O. Its
pending I/O is drained and held for a moment while it switches over. Devices whose LUN has not grown are left as they
are. `status.deviceGrowth` counts the devices that grew, that were unchanged, and that could not be grown, with the
reason for each. `uniform` is `false`, with a `DeviceGrowthUneven` event, when the data devices have not all grown by
the same factor.

A single device is grown with a `StorageDeviceOps` with the action `Grow`, for example, after one LUN was grown on
its own. Its outcome is recorded in `status.growth` (see
[Growing a Storage Device](../storage-nodes/storage-node-actions.md#growing-a-storage-device)).

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
