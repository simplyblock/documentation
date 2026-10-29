---
title: "Concepts"
description: "The core concepts of simplyblock: clusters, pools, logical volumes, snapshots, erasure coding, failure domains, migration, and disaster recovery."
weight: 20300
---

This section explains the building blocks of simplyblock and how they work together. The concepts apply to every
deployment, whether the storage nodes run hyper-converged with the applications or on dedicated workers.

| Area                   | Concepts                                                                                                                                                                                             |
|------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Cluster and storage    | [Simplyblock Cluster](simplyblock-cluster.md), [Storage Pooling](storage-pooling.md), [Linux Block Devices](linux-block-devices.md)                                                                  |
| Volumes                | [Logical Volumes](logical-volumes.md), [NVMe Namespaces and Subsystems](nvme-namespaces-and-subsystems.md), [Persistent Volumes](persistent-volumes.md), [Snapshots and Clones](snapshots-clones.md) |
| Shared file storage    | [Distributed File Storage](distributed-file-storage.md), [ReadWriteMany (pNFS)](pnfs.md)                                                                                                             |
| Security               | [NVMe over Fabrics Security](nvmf-security.md), [External Key Management](external-key-management.md)                                                                                                |
| Data protection        | [Erasure Coding](erasure-coding.md), [Failure Domains](failure-domains.md), [Automatic Rebalancing](automatic-rebalancing.md)                                                                        |
| Placement and mobility | [Volume Migration](volume-migration.md), [Placement Groups](placement-groups.md)                                                                                                                     |
| Disaster recovery      | [DR Protection Plans](dr-protection-plans.md), [DR Applications](dr-applications.md), [Failover](failover.md), [Relocation](relocation.md)                                                           |
