---
title: "Performance and QoS"
description: "Performance and QoS: Storage performance can be categorized by latency (the aggregate response time of an I/O request from the host to the storage system) and."
weight: 20100
---

## Storage Performance Indicators

Storage performance can be categorized by latency (the aggregate response time of an I/O request from the host to the
storage system) and throughput. Throughput can be broken down into random IOPS throughput and sequential throughput.

IOPS and sequential throughput must be measured relative to capacity (i.e., IOPS per TB).

Latency and IOPS throughput depend heavily on the I/O operation (read, write, unmap) and the I/O size (4K, 8K, 16K,
32K, ...). For comparability, it is typically tested with a 4K I/O size, but tests with 8K to 128K are standard too.

Latency is strongly influenced by the overall load on the overall storage system. If there is intense I/O pressure,
queues build up and response times go up. This is no different from a traffic jam on the highway or a queue at the
airline counter. Therefore, to compare latency results, it must be measured under a fixed system load (amount of
parallel I/O, its size, and I/O type mix).

!!! important
    For latency, consistency matters. High latency variability, especially in the tail, can severely impact workloads.
    Therefore, the 99th percentile latency may be more important than the average or median.

## Challenges with Hyper-Converged and Software-Defined Storage

Unequal load distribution across cluster nodes, and the dynamics of specific nodes under Linux or Windows (dynamic
multithreading, network bandwidth fluctuations, etc.), create significant challenges for consistent, high storage
performance in such an environment.

Mixed I/O patterns increase these challenges from different workloads.

This can cause substantial variability in latency, IOPS throughput, and high-tail latency, with a negative impact on
workloads.

## Simplyblock: How Ultra-Low Latency In The 99th Percentile Is Ensured

Simplyblock exhibits a range of architectural characteristics and features to guarantee consistently low latency and
IOPS in both disaggregated and hyper-converged environments.

### Data Locality

Simplyblock uses NVMe/TCP or NVMe/RDMA (RoCEv2) to connect initiators (storage consumers) to the storage cluster. While those protocols
are networked and allow any type of distributed topology between clients and cluster nodes, simplyblock can co-locate data with the
workloads that use it to reduce network latency and bandwidth utilization.

In simplyblock, front storage (the NVMe-oF volumes, the "docking points" of the clients into the cluster) and back storage (the actual
NVMe storage layer) are distributed separately. All back storage devices of the cluster can be accessed from any front storage entry point
using cluster-internal NVMe-oF.

!!! info "Data locality is turned off by default"
    By default, simplyblock does not apply data locality, not even in a hyper-converged deployment. Instead, it distributes volumes and
    their data to achieve a fully balanced load across all nodes, devices, and network links of the cluster. Data locality is a
    trade-off that is enabled on purpose where lower latency and less network traffic matter more than an even cluster balance.

Data locality has two aspects, which are independent of each other:

1. **Pod locality (front storage):** The NVMe-oF volume is placed on the storage node on the same worker as the pod that consumes
   it. The I/O between the pod and its volume then stays on the worker, which eliminates one network hop. When a pod is relocated to
   another worker, its NVMe-oF volume follows the workload instantly with an
   [instant volume migration](concepts/volume-migration.md). Only the front storage moves, no data is copied. On Kubernetes, pod
   locality is requested per volume (see [Co-Locating a Volume With a Pod](../kubernetes/usage/volume-placement.md#co-locating-a-volume-with-a-pod)).
2. **Back storage locality (node affinity):** If node affinity is turned on, the primary chunk or data copy of a volume is co-located
   with its front storage NVMe-oF volume on a best-effort basis. This reduces the network load and improves the latency further, but it
   concentrates data on the nodes that host the volumes and therefore impacts the balance of the cluster. Node affinity is a
   cluster-wide setting and is turned off by default (see [Configuring Node Affinity](../kubernetes/operations/cluster/node-affinity.md)).
   When the front storage of a volume moves, its back storage does not move instantly. Once the cluster is rebalanced in the
   background, the data is moved to satisfy node affinity again.

The rebalancing algorithm which moves data around is optimized for minimal overhead:

* First, it tries to maximize transfer size, in fact turning smaller random writes into large sequential writes, which are much more efficient.
* Secondly, it runs in the background and does not consume more than 20% of cluster resources (guaranteed by QoS). Therefore, its impact on
  I/O performance is quite limited. With node affinity turned on, volumes therefore converge toward full data locality whenever possible.
* At the same time, this does not result in any hard limits.
    * For example, in a cluster with 2 PB of storage, it is still possible to create a single volume consuming all of these 2 PB.
    * Also, it can be balanced against scalability and consistency. Meaning, if I/O-intensive workloads are not well-balanced across worker nodes,
      data locality could lead to actually worse performance. Therefore, data locality is not an absolute requirement, but remains a best effort,
      and is balanced against an optimal distribution of I/O across nodes.

### Pseudo-Randomized, Distributed Data Placement With Fast Re-Balancing

Simplyblock is a fully distributed solution. Back-storage is balanced across all nodes in the cluster on a very granular
level. Relative to their capacity and performance, each device and node in the cluster receives a similar amount and
size of I/O. This feature ensures an entirely equal distribution of load across the network, compute, and NVMe drives.

In case of drive or node failures, distributed rebalancing occurs to reach the fully balanced state as quickly as
possible. When adding drives and nodes, performance increases in a **linear manner**. This mechanism avoids local
overload and keeps latency and IOPS throughput consistent across the cluster, independent of which node is accessed.

### Built End-To-End With And For NVMe

Storage access is entirely based on NVMe (local back-storage) and NVMe over Fabric (hosts to storage nodes and storage
nodes to storage nodes). This protocol is inherently asynchronous and supports highly parallel processing, eliminating
bottlenecks specific to mixed I/O patterns on other protocols (such as iSCSI) and ensuring consistently low latency.

### Support for ROCEv2

Simplyblock also supports NVMe over RDMA (ROCEv2). RDMA, as a transport layer, offers significant latency and tail
latency advantages over TCP. Today, RDMA can be used in most datacenter environments because it requires only specific
hardware features from NICs, which are available across a broad range of models. It runs over UDP/IP and, as such, does
not require any changes to the networking.

### Full Core-Isolation And NUMA Awareness

Simplyblock implements full CPU core isolation and NUMA socket affinity. Simplyblock’s storage nodes are auto-deployed
per NUMA socket and utilize only socket-specific resources, meaning compute, memory, network interfaces, and NVMe.

All CPU cores assigned to simplyblock are isolated from the operating system (user-space compute and IRQ handling), and
internal threads are pinned to cores. This avoids any scheduling-induced delays or variability in storage processing.

### User-Space, Zero-Copy Framework (Lockless and Asynchronous)

Simplyblock uses a user-space framework ([SPDK](https://spdk.io/){:target="_blank" rel="noopener"}). SPDK implemented a
zero-copy model across the entire storage processing chain. This includes the data plane, the Linux vfio driver, and the
entirely non-locking, asynchronous DPDK threading model. It enables avoiding Linux p-threads and any inter-thread
synchronization, providing much higher latency predictability and a lower baseline latency.

### Advanced QoS (Quality of Service)

Simplyblock implements two independent, critical QoS mechanisms.

#### Volume and Pool-Level Caps

A cap, such as an IOPS, throughput limit, or a combination of both, can be set on an individual volume or an entire pool
within the cluster. Through this limit, general-purpose volumes can be pooled and limited in their total IOPS or
throughput to avoid noisy-neighbor effects and protect more critical workloads.

#### QoS Service Classes

On each cluster, up to 7 service classes can be defined (class 0 is the default). For each class, cluster performance (a
combination of IOPS and throughput) can be allocated in relative terms (e.g., 20%) for performance guarantees.

General-purpose volumes can be allocated in the default class, while more critical workloads can be split across other
service classes. If other classes do not use up their quotas, the default class can still allocate all available
resources.

#### Why QoS Service Classes are Critical

Why is a limit not sufficient? Imagine a heavily mixed workload in the cluster. Some workloads are read-intensive, while
others are write-intensive. Some workloads require a lot of small random I/O, while others read and write large
sequential I/O. There is no absolute number of IOPS or throughput a cluster can provide, considering the dynamics of
workloads.

Therefore, using absolute limits on one pool of volumes is effective for protecting others from spillover effects and
undesired behavior. Still, it does not guarantee performance for a particular class of volumes.

Service classes provide a much better degree of isolation under the consideration of dynamic workloads. As long as a
particular service class is not overloaded, the general I/O pressure on the cluster will not matter for the performance
of volumes in that class.
