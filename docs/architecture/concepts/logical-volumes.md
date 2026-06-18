---
title: "Logical Volumes"
description: "Logical Volumes (LVs) in Simplyblock are virtual NVMe devices that provide scalable, high-performance storage within a distributed storage cluster."
weight: 30100
---

Logical Volumes (LVs) in simplyblock are virtual NVMe devices that provide scalable, high-performance storage within a
distributed storage cluster. They enable flexible storage allocation, efficient resource utilization, and seamless data
management for cloud-native applications.

A Logical Volume (LV) in simplyblock is an abstracted storage entity dynamically allocated from a storage pool managed
by the simplyblock system. Unlike traditional block storage, simplyblock’s LVs offer advanced features such as thin
provisioning, snapshotting, and replication to enhance resilience and scalability.

A volume is connected to the cluster via NVMe-oF (TCP or RoCEv2). 

Key characteristics of Logical Volumes include:

- **Dynamic Allocation:** LVs can be created, resized, and deleted on demand without manual intervention in the
  underlying hardware.
- **Thin Provisioning:** Storage space is allocated only when needed, optimizing resource utilization.
- **High Performance:** Simplyblock’s architecture ensures low-latency access to LVs, making them suitable for demanding
  workloads.
- **Fault Tolerance:** Data is distributed across multiple nodes to prevent data loss and improve reliability.

Simplyblock has no limit to the capacity of a single volume in relation to the size of the cluster: a single volume
can consume all the cluster capacity, or cluster capacity can be distributed across 50,000 volumes.

Volumes can also contain an almost arbitrary number of snapshots, and new volumes can be created from any snapshot
(copy-on-write cloning).

Simplyblock allows to "tune" the performance and network isolation of volumes and the cardinality between NVMe 
namespaces (/dev/nvme1n1, /dev/nvme1n2, ...) and NVMe subsystems (/dev/nvme1n1, /dev/nvme2n1, ...) 
can be set on storage-pool level.

NVMe subsystems can be created with a number of namespaces in between one and 500.

A subsystem comes with its own set of TCP connections. The amount corresponds to the number of queue pairs on the subsystem but
is always limited by the number of cores/vcpus on the client. Meaning, a client with 10 vCPUs cannot connect via more than 10
queue pairs to any NVMe-oF subsystem, even if that subsystem provides 32 or more queue pairs.
 
Depending on the size of a storage node and particularly its available network bandwidth, the upper recommended limit of 
subsystems per node typically lies between five and 50. Therefore, it depends on the upper number of provisioned volumes targeted per node
how to set the relationship between namespaces and subsystems.

If the target is only a handful of high-performance volumes, the number of namespaces can be set to 1. However, if the
target is, for example, 2,000 small volumes, the number of namespaces should be set to a higher value, for example, 100. 


