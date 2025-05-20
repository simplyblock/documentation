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
