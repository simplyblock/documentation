---
title: "Performance and QoS"
description: "How simplyblock keeps storage latency low and predictable, from its user-space NVMe data path to data placement, and how caps and service classes isolate I/O."
weight: 20100
---

Simplyblock is built for low and, above all, predictable latency. This page explains how storage performance is
measured, which design decisions keep it consistent, and how quality of service (QoS) keeps workloads from
interfering with each other.

## Measuring Storage Performance

Storage performance is described by three indicators:

- **Latency:** The time an I/O request takes from the host to the storage and back.
- **IOPS:** The number of random I/O operations per second, usually measured with 4 KiB requests.
- **Throughput:** The amount of sequential data transferred per second, usually measured with 128 KiB requests or
  larger.

All three depend on the I/O type (read, write, unmap), the I/O size, and the load on the system. Under heavy load,
queues build up and latency rises, so latency results are only comparable at the same load. IOPS and throughput are
best compared relative to capacity, for example, IOPS per TB.

!!! important
    For latency, consistency matters more than the average. Outliers in the tail slow down applications, so the 99th
    percentile latency is often more meaningful than the mean or the median.

Software-defined and hyper-converged storage often struggle with exactly this consistency. Load spreads unevenly
across nodes, the operating system schedules storage threads next to application threads, and mixed workloads
compete for the same devices and links. The sections below describe how simplyblock avoids these effects.

## How Simplyblock Keeps Latency Low

### NVMe From End to End

Every hop of the data path uses NVMe: the local devices of a storage node, the connection from a host to the
cluster, and the traffic between storage nodes. Hosts connect over NVMe/TCP or NVMe/RoCE (RDMA over Converged
Ethernet, RoCEv2). NVMe is asynchronous and highly parallel, so it avoids the bottlenecks that protocols such as
iSCSI show under mixed I/O. RoCEv2 further lowers the latency and, in particular, the tail latency compared with TCP,
and it is routable over standard IP networks.

### User-Space, Zero-Copy Data Plane

The data plane of a storage node is built on [SPDK](https://spdk.io/){:target="_blank" rel="noopener"}. It takes
the devices away from the Linux kernel and processes all I/O in user space, without copying data, without locks,
and without interrupts. This removes context switches and thread synchronization from the data path, which lowers
the baseline latency and makes it far more predictable.

### Dedicated Cores and NUMA Awareness

A storage node runs on CPU cores that are isolated from the operating system, including interrupt handling, and
its threads are pinned to those cores. On servers with several CPU sockets, one storage node is deployed per socket
and uses only that socket's memory, network interfaces, and NVMe devices. No scheduling delays and no cross-socket
memory access slow down the storage processing.

### Balanced, Distributed Data Placement

Data is split into small chunks and spread across all devices of all storage nodes, relative to their capacity. As a
result, every device, node, and network link carries a similar share of the load, and no single node becomes a
hotspot. Adding nodes or devices increases performance almost linearly.

After failures, expansions, or node removals, the cluster rebalances in the background (see
[Automatic Rebalancing](concepts/automatic-rebalancing.md)). Rebalancing moves large contiguous segments, which is
far cheaper than many small random writes, and it runs in an internal service class, so client I/O always keeps
the larger share of the cluster's performance.

### Data Locality

Simplyblock separates the layer that clients connect to (the front storage, which holds the NVMe-oF volumes) from
the layer that stores the data (the back storage, which consists of the NVMe devices). Every front storage entry
point reaches every back storage device over cluster-internal NVMe-oF. This separation makes data locality
possible, but it does not require it.

!!! info "Data locality is turned off by default"
    By default, simplyblock does not apply data locality, not even in a hyper-converged deployment. It distributes
    volumes and their data for a fully balanced load across all nodes, devices, and network links. Data locality is
    enabled on purpose where lower latency and less network traffic matter more than an even cluster balance.

Data locality has two independent parts:

| Part                         | What it does                                                                                                                                                                    | How it is enabled                                                                                                          |
|------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------|
| Pod locality (front storage) | Places the NVMe-oF volume on the storage node on the pod's worker, which saves one network hop. When the pod moves, the volume follows it with an instant volume migration.     | Per volume, see [Co-Locating a Volume With a Pod](../kubernetes/usage/volume-placement.md#co-locating-a-volume-with-a-pod) |
| Node affinity (back storage) | Keeps the primary data of a volume on the node that hosts the volume, on a best-effort basis. This lowers latency and network load further, but concentrates data on that node. | Per cluster, see [Configuring Node Affinity](../kubernetes/operations/cluster/node-affinity.md)                            |

An [instant volume migration](concepts/volume-migration.md) moves only the front storage, so no data is copied.
With node affinity turned on, the back storage follows later, through the background rebalancing.

Data locality is always best-effort. It never limits the size of a volume, and it gives way where it would overload
a node. If I/O-intensive workloads are spread unevenly across workers, strict locality would make performance
worse, so simplyblock balances locality against an even distribution of I/O.

### Shared File Storage at Block Performance (pNFS)

Shared file storage (`ReadWriteMany`) is served through [distributed file storage](concepts/distributed-file-storage.md)
based on parallel NFS (pNFS), and it uses the same NVMe data path as block volumes:

- **No file server in the data path:** A metadata server handles only file metadata, such as opens, lookups, and
  allocations. Every client reads and writes file contents directly on the logical volume over its own NVMe/TCP
  connection.
- **Throughput scales with the clients:** Each client node drives its own connections to the storage nodes, so the
  total throughput grows with the number of clients instead of being capped by a single server.
- **Same latency and QoS:** Reads and writes take the same user-space path on the storage nodes, and the caps and
  service classes below apply unchanged. The only extra cost is one write-zeroes operation when the metadata server
  allocates new blocks.

Workloads with many small files, or with frequent creates and deletes, are bound by the single metadata server per
storage cluster. A client node whose kernel lacks the pNFS block layout driver falls back to sending its data
through the metadata server, at a fraction of the throughput (see
[Verifying the Direct Data Path](../kubernetes/usage/pnfs.md#verifying-the-direct-data-path)).

## Quality of Service

Simplyblock offers two independent QoS mechanisms: caps, which set an absolute ceiling, and service classes, which
guarantee a relative share.

### Caps on Volumes and Pools

A cap limits the IOPS, the throughput, or both, of a single volume or of a whole storage pool. Pooling
general-purpose volumes under a common cap keeps them from crowding out more critical workloads (the
noisy-neighbor effect). See [Defining Quality of Service](../kubernetes/usage/quality-of-service.md).

### Service Classes

A service class reserves a relative share of the cluster's I/O for a group of volumes. Every volume belongs to
exactly one class:

- **Default:** Every volume that names no other class.
- **Up to five named classes:** Each with its own weight, for example, for databases or other critical workloads.
- **Two internal classes:** One for metadata I/O and data migration, and one for replication between clusters, whose
  share is configurable.

When classes compete, each one receives a share in proportion to its weight. A class that does not use its share
leaves it to the others, so no capacity sits idle. See [Service Classes](../kubernetes/usage/service-classes.md) for
the configuration.

### Why Caps Alone Are Not Enough

A cluster does not have a fixed number of IOPS or a fixed throughput. What it delivers depends on the mix of reads
and writes, and of small random and large sequential I/O. A cap therefore protects other workloads from a volume or
a pool, but it cannot guarantee performance to anyone.

A service class can. As long as a class does not exceed its own share, the load in the rest of the cluster does not
affect the performance of its volumes.

## Monitoring Performance

The I/O statistics of clusters, nodes, devices, pools, and volumes are exported as Prometheus metrics (see
[Prometheus Metrics](../kubernetes/operations/monitoring/prometheus-metrics.md)). Devices whose latency falls
behind the rest of the cluster are detected and reported automatically (see
[Device Health](../kubernetes/operations/monitoring/device-health.md)).
