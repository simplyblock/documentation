---
title: "Operations"
description: "Overview of the operations of a simplyblock deployment outside Kubernetes: the cluster and storage node lifecycle, volumes, data protection, and monitoring."
weight: 70000
---

This section covers the operation of a running simplyblock deployment outside Kubernetes: the lifecycle of a storage
cluster and its storage nodes, the placement and the protection of the data on them, and the monitoring and the
security of the deployment.

Every operation is performed with the `{{ cliname }}` command line interface, which is the direct interface to the
control plane and is meant for an operator who needs fine-grained control. The same operations expressed as Kubernetes
resources are described under [Kubernetes Operations](../../kubernetes/operations/index.md).

| Section                                     | Contents                                                                    |
|---------------------------------------------|-----------------------------------------------------------------------------|
| [Cluster](cluster/index.md)                 | Cluster upgrades, failure domains, and node affinity.                       |
| [Storage Nodes](storage-nodes/index.md)     | Node restarts, replacement, relocation, and the failover path lookup.       |
| [Scaling](scaling/index.md)                 | Expanding a storage pool of a running cluster.                              |
| [Volumes](volumes/index.md)                 | Volume migration, reconnecting, trimming, and quality of service.           |
| [Data Protection](data-protection/index.md) | Backup and recovery, and asynchronous replication.                          |
| [Monitoring](monitoring/index.md)           | Cluster health, logical volume conditions, I/O stats, alerts, and logs.     |
| [Security](security/index.md)               | Authentication, transport encryption, volume encryption, and multi-tenancy. |
