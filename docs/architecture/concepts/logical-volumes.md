---
title: "Logical Volumes"
description: "Logical volumes in simplyblock are thin-provisioned virtual NVMe devices, carved from a storage pool and spread across all devices of a storage cluster."
weight: 30100
---

A logical volume (LV) is a virtual NVMe device that simplyblock carves out of a storage pool. To a host, it looks
like a local NVMe drive. Its data, however, is spread across all devices of all storage nodes in the cluster, and it
is reached over NVMe-oF (NVMe/TCP or NVMe/RoCE).

Key characteristics of logical volumes include:

- **Thin provisioning:** Capacity is allocated only when data is written. A volume can be larger than the free
  capacity of the cluster at the time it is created.
- **Dynamic sizing:** Volumes are created, resized, and deleted on demand, without touching the underlying
  hardware.
- **Performance:** Every volume uses the performance of the whole cluster, and caps and service classes control its
  share (see [Performance and QoS](../storage-performance-and-qos.md#quality-of-service)).
- **Fault tolerance:** Data is protected with erasure coding, and in a highly available cluster, every volume has a
  failover path on at least one other node.
- **Data services:** Volumes can be snapshotted, cloned, encrypted, backed up to S3, and replicated to another
  cluster.

A volume is not tied to the capacity of a single node, but its size and the number of objects that depend on it are
bounded: a volume can be up to 70 TiB in size and have up to 100 snapshots, and each snapshot up to 500 clones. A
storage node serves up to 6,000 volumes, snapshots, and clones as primary. See [Limits](../../reference/limits.md)
for all limits.

## Subsystems and Namespaces

Each volume is exposed as an NVMe namespace inside an NVMe-oF subsystem. By default, every volume gets a subsystem of
its own. Volumes can also share a subsystem, up to 50 namespaces per subsystem, which is set through the storage
pool or the StorageClass.

A subsystem comes with its own set of network connections, one per queue pair. The number of queue pairs a host uses
is limited by its CPU cores: a host with 10 vCPUs connects with at most 10 queue pairs, even if the subsystem offers
more. Every subsystem also costs memory and connections on the storage node, so the number of subsystems per node is
limited.

As a rule of thumb:

- **A few high-performance volumes:** One volume per subsystem gives each volume its own connections.
- **Many small volumes:** Sharing subsystems, for example, 16 or 32 namespaces per subsystem, keeps the number of
  subsystems and connections manageable.

See [NVMe Namespaces and Subsystems](nvme-namespaces-and-subsystems.md) for details.
