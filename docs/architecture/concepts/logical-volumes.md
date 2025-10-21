---
title: "Logical Volumes"
weight: 30100
---

Logical Volumes (LVs) in Simplyblock are virtual NVMe devices that provide scalable, high-performance storage within a
distributed storage cluster. They enable flexible storage allocation, efficient resource utilization, and seamless data
management for cloud-native applications.

A Logical Volume (LV) in simplyblock is an abstracted storage entity dynamically allocated from a storage pool managed
by the simplyblock system. Unlike traditional block storage, simplyblock’s LVs offer advanced features such as thin
provisioning, snapshotting, and replication to enhance resilience and scalability.

Key characteristics of Logical Volumes include:

- **Dynamic Allocation:** LVs can be created, resized, and deleted on demand without manual intervention in the
  underlying hardware.
- **Thin Provisioning:** Storage space is allocated only when needed, optimizing resource utilization.
- **High Performance:** Simplyblock’s architecture ensures low-latency access to LVs, making them suitable for demanding
  workloads.
- **Fault Tolerance:** Data is distributed across multiple nodes to prevent data loss and improve reliability.
- **Integration with Kubernetes:** LVs can be used as persistent storage for Kubernetes workloads, enabling seamless
  stateful application management.

Two basic types of logical volumes are supported by Simplyblock:

- **NVMf subsystems**: Each volume receives a separate listener (either tcp or rdma).
  Host and storage nodes are connected via one or multiple queue pairs. Each queue pair 
  is backed by one network connection (socket). 
  The number of queue pairs can be set when manually connecting NVMf volumes to a host or via the CSI storage class, but 
  However, the actual amount used may be lower as it also depends on the number of cores available on the host).

- **NVMf Namespaces**: An nvme namespace is a feature similar to a logical partition of a drive, although
  in the case of nvme drives it is actually a hardware feature. In NVMf, a single subsystem can be split into 
  multiple namespaces. Simplyblock alternatively supports the creation of namespace volumes 
  (they show up under /dev/nvme1n1, /dev/nvme1n2, etc.) under a single subsystem. 
  They all share the same queue pairs, subsystem and listener, therefore their individual
  maximal performance is lower. However, they may be a good choice if a large number of 
  small volumes is required on a host and those volumes are frequently provisioned and de-provisioned.
