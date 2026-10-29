---
title: Architecture
description: "The architecture of simplyblock: one NVMe-oF storage platform for block, shared file (pNFS), and object storage, with its components and core concepts."
weight: 10080
---

Simplyblock is a cloud-native, software-defined storage platform built for high performance, scalability, and
resilience. It is deployed and operated through Kubernetes, and it serves three kinds of storage from the same
NVMe-oF infrastructure and the same storage clusters:

- **Block storage:** Logical volumes over NVMe/TCP and NVMe/RoCE.
- **Shared file storage:** `ReadWriteMany` volumes through [parallel NFS (pNFS)](concepts/pnfs.md), whose clients
  read and write the data directly over NVMe-oF.
- **Object storage:** An S3-compatible interface (coming soon as a beta).

File and object storage are built on top of the block layer, so all three share the benefits of the storage
architecture:

- Distributed scale-out storage with high IOPS and low latency
- Live storage migration between clusters
- Policy-based asynchronous replication, and synchronous replication with stretched clusters (coming soon)
- Efficient, policy-based backup and restore
- Granular encryption with end-to-end key management through an external KMS
- True QoS and performance isolation
- Compression and deduplication

This section explains how simplyblock works internally. Understanding the architecture helps with planning a
deployment, sizing a cluster, and choosing between the available protection and placement options.

| Page                                                                          | Content                                                                                  |
|-------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| [What is Simplyblock?](what-is-simplyblock.md)                                | An overview of the platform and what sets it apart.                                      |
| [Simplyblock Architecture](simplyblock-architecture.md)                       | The operator, the control plane, the CSI driver, and the storage plane.                  |
| [Performance and QoS](storage-performance-and-qos.md)                         | How latency stays low and predictable, data locality, caps, and service classes.         |
| [High Availability and Fault Tolerance](high-availability-fault-tolerance.md) | How volumes stay available through device, node, rack, and site failures.                |
| [Deployment Topologies](deployment-topologies/index.md)                       | Where the control plane and the storage nodes run: hyper-converged, disaggregated, edge. |
| [Concepts](concepts/index.md)                                                 | Logical volumes, snapshots, erasure coding, failure domains, migration, and more.        |
