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

Two basic types of logical volumes are supported by simplyblock:

- **NVMe-oF Subsystems**: Each logical volume is backed by a separate set of queue pairs. By default, each subsystem 
  provides three queue parts and one network connection.

  Volumes show up in Linux using `lsblk` as `/dev/nvme0n2`, `/dev/nvme1n1`, `/dev/nvmeXn1`, ...

- **NVMe-oF Namespaces**: Each logical volume is backed by an NVMe namespace. A namespace is a feature similar to a
  logical partition of a drive, although it is defined on the NVMe level (device or target). Up to 32 namespaces share
  a single NVMe subsystem and its queue pairs and connections.

  This is a more resource-efficient, but performance-limited, version of an individual volume. It is useful, if many,
  small volumes are required. Both methods can be combined in a single cluster.

  Volumes show up in Linux using `lsblk` as `/dev/nvme0n1`, `/dev/nvme0n2`, `/dev/nvme0nX`, ...
