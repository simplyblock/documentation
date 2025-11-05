---
title: "Performance and QoS"
weight: 20100
---

## Storage Performance Indicators

Storage performance can be categorized by latency (the aggregate response time of an IO request from the host to the
storage system) and throughput. Throughput can be broken down into random IOPS throughput and sequential throughput.

IOPS and sequential throughput must be measured relative to capacity (i.e., IOPS per TB).

Latency and IOPS throughput depend heavily on the IO operation (read, write, unmap) and the IO size (4K, 8K, 16K,
32K, ...). For comparability, it is typically tested with a 4K IO size, but tests with 8K to 128K are standard too.

Latency is strongly influenced by the overall load on the overall storage system. If there is intense IO pressure,
queues build up and response times go up. This is no different from a traffic jam on the highway or a queue at the
airline counter. Therefore, to compare latency results, it must be measured under a fixed system load (amount of
parallel IO, its size, and IO type mix).

!!! Important
    For latency, consistency matters. High latency variability, especially in the tail, can severely impact workloads.
    Therefore, 99th percentile latency may be more important than the average or median.

## Challenges with Hyper-Converged and Software-Defined Storage

Unequal load distribution across cluster nodes, and the dynamics of specific nodes under Linux or Windows (dynamic
multithreading, network bandwidth fluctuations, etc.), create significant challenges for consistent, high storage
performance in such an environment.

Mixed IO patterns increase these challenges from different workloads.

This can cause substantial variability in latency, IOPS throughput, and high-tail latency, with a negative impact on
workloads.

## Simplyblock: How We Ensure Ultra-Low Latency In The 99th Percentile

Simplyblock exhibits a range of architectural characteristics and features to guarantee consistently low latency and
IOPS in both disaggregated and hyper-converged environments.

### Pseudo-Randomized, Distributed Data Placement With Fast Re-Balancing

Simplyblock is a fully distributed solution. Back-storage is balanced across all nodes in the cluster on a very granular
level. Relative to their capacity and performance, each device and node in the cluster receives a similar amount and
size of IO. This feature ensures an entirely equal distribution of load across the network, compute, and NVMe drives.

In case of drive or node failures, distributed rebalancing occurs to reach the fully balanced state as quickly as
possible. When adding drives and nodes, performance increases in a **linear manner**. This mechanism avoids local
overload and keeps latency and IOPS throughput consistent across the cluster, independent of which node is accessed.

### Built End-To-End With And For NVMe

Storage access is entirely based on NVMe (local back-storage) and NVMe over Fabric (hosts to storage nodes and storage
nodes to storage nodes). This protocol is inherently asynchronous and supports highly parallel processing, eliminating
bottlenecks specific to mixed IO patterns on other protocols (such as iSCSI) and ensuring consistently low latency.

### Support for ROCEv2

Simplyblock also supports NVMe over RDMA (ROCEv2). RDMA, as a transport layer, offers significant latency and tail
latency advantages over TCP. Today, RDMA can be used in most data center environments because it requires only specific
hardware features from NICs, which are available across a broad range of models. It runs over UDP/IP and, as such, does
not require any changes to the networking.

### Full Core-Isolation And NUMA Awareness

Simplyblock implements full CPU core isolation and NUMA socket affinity. Simplyblock’s storage nodes are auto-deployed
per NUMA socket and utilize only socket-specific resources, meaning compute, memory, network interfaces, and NVMe.

All CPU cores assigned to simplyblock are isolated from the operating system (user-space compute and IRQ handling), and
internal threads are pinned to cores. This avoids any scheduling-induced delays or variability in storage processing.

### User-Space, Zero-Copy Framework (Kockless and Asynchronous)

Simplyblock uses a user-space framework ([SPDK](https://spdk.io/){:target="_blank" rel="noopener"}). SPDK implemented a
zero-copy model across the entire storage processing chain. This includes the data plane, the Kinux vfio driver, and the
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
others are write-intensive. Some workloads require a lot of small random IO, while others read and write large
sequential IO. There is no absolute number of IOPS or throughput a cluster can provide, considering the dynamics of
workloads.

Therefore, using absolute limits on one pool of volumes is effective for protecting others from spillover effects and
undesired behavior. Still, it does not guarantee performance for a particular class of volumes.

Service classes provide a much better degree of isolation under the consideration of dynamic workloads. As long as you
do not overload a particular service class, the general IO pressure on the cluster will not matter for the performance
of volumes in that class.

