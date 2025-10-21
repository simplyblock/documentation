---
title: "Performance and QoS"
weight: 20100
---

## Storage Performance Indicators

Storage performance can be categorized by latency,the aggregate response time of an io request from the host to the storage
system, and throughput. throughput can be broken down into random IOPS throughput and sequential throughput.

IOPS and Sequential Throughput must be measured in relation to the capacity (i.e. IOPS per TB).

Latency and IOPS throughput depend heavily on the io operation (read, write, unmap)
and the block size (4K, 8K, 16K, 32K, ...). For comparability, it is typically tested
with 4K io size, but tests with 8K to 128K are common too. 

Latency is strongly influenced by the overall load on the overall storage system.
If there is strong io pressure, queues build up and response times go up. This is no
different from a traffic jam on the highway or a queue at the airline counter. 
Therefore, to compare latency results it must be measured under a fixed system load
(amount of parallel IO and its size and io type mix).

!!! Important
    For latency, consistency matters. A high variability of latency with a high tail latency can impact workloads in a 
    very negative manner. Therefore, 99 percentile latency may be more important than
    the average or median.

## Challenges with hyper-converged and software-defined storage

Unequal load distribution across cluster nodes and dynamics of particular nodes
under Linux or Windows (dynamic multi-threading, network bandwidth dynamics, etc.) create significant challenges for consistent and 
high storage performance in such an environment.

These challenges are increased by mixed io patterns from different workloads.

This can cause strong variability of latency IOPS throughput and high tail latency will all of the 
negative effects on workloads.

## Simplyblock: How we ensure ultra-low latency in the 99 percentile

Simplyblock exhibits a range of architectural characteristics and features to
guarantee consistently low latency and IOPS in both disaggregated and hyper-
converged environments.

### Pseudo-Randomized, Distributed Data Placement with fast Re-Balancing

Simplyblock is a fully distributed solution. Back-storage is balanced across 
all nodes in the cluster on a very granular level. Relative to their capacity and
performance, each device and node in the cluster receives the same amount and size of io.
This feature ensures entirely equal distribution of load accross the network, compute and 
and nvme drives. 

In case of drive or node failures, re-distribution and re-balancing is again fully equalized.
In case of adding drives and nodes, performance can increase linearily. This mechanism
avoids local overload and keeps latency and iops throughput consistent across the cluster,
independent of which node is accessed.

### built end-to-end on and for nvme and nvmf

Storage access is entirely based on nvme (local back-storage) and nvmf (hosts to storage nodes and 
storage nodes to storage nodes). This protocol is inherently asynchronous and supports highly parallel processing,
eliminating bottlenecks specific to mixed io patterns on other protocols (such as iscsi) 
and ensuring consistently low latency.

### Support for ROCEv2

In particular, Simplyblock also supports nvmf/rdma (rocev2), which as an L3/L4 networking protocol
comes with a significantly lower latency and particularly tail latency than TCP.

### Full Core Isolation and Numa-Node Awareness/Affinity

Next, Simplyblock implements full cpu core isolation and numa-socket affinity.
Simplyblock Storage Nodes are auto-deployed per Numa-Socket and only use Socket-specific resources
(compute, ram, NICs, NVMe).

All cpu cores assigned to Simplyblock are isolated from the operating system 
- user-space compute and IRQs - and internally threads are pinned to cores to avoid
any scheduling-induced delays or variability to storage processing.

### User-space, zero-copy framework (lockless, asynchronous)

The use of a user-space framework (spdk), based on a zero-copy model through
the entire chain of storage processing on the data plane, the linux vfio driver
and the entirely non-locking, asynchronous dpdk threading model (full avoidance of linux p-threads and any inter-thread
synchronization), gives much higher predictibility of latency and lower baseline latency.

### Advanced Qos

On top of those, Simplyblock implements two independent, critical QoS mechanisms:

#### Volume and Pool-Level Caps

A cap - an IOPS or Throughput limit or a Combination of Both - 
which can be set on both individual volumes and entire pools 
within the cluster. Through this limit, general-purpose volumes can be pooled and 
limited in their total IOPS or Throughput to avoid noisy-neighbour effects and 
protect more critical workloads. 

#### QoS Service Classes for full isolation of performance

A second QoS feature is based on service classes. On each cluster, up to 7 service
classes can be defined (class 0 is the default class). 
For each class, a relative allocation of resources (a combination of IOPS and
throughput) can be defined using weights. 
General-purpose volumes can be allocated in the default class
while more critical workloads can be split across other service classes.
These are guarantees and not limits! 
If other classes do not use up their quotas, the
default class can still allocate all available resources. 

#### Why QoS Service Classes are Critical 

Why is a limit not sufficient? Imagine a heavily mixed workload in the cluster. Some
workloads are read-intensive, while others are write-intensive. Some workloads require 
a lot of small-sized random IO, while other workloads read and write large 
sequential io. There is no absolute number of IOPS or throughput a cluster can
provide considering the dynamics of workloads. 
Therefore, using absolute limits on one pool of volumes is good to protect others
from spill-over effects and undesired behaviour, but it does not give you 
a guarantee on what is really left. Service classes provide a much 
better degree of isolation under the consideration of dynamic workloads.
As long as you do not overload a particular service class, the general io pressure
on the cluster will not matter for the performance of volumes in that class.

























and many individual 
components. Particularly, with hyper-converged systems, this can be an issue, as the
load on the local node (compute, network) matters most.



