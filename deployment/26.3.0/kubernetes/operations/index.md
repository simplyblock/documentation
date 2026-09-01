---
title: "Operations"
description: "Overview of the operations of a simplyblock deployment on Kubernetes: the cluster and storage node lifecycle, data protection, monitoring, and security."
source: "https://docs.simplyblock.io/latest/kubernetes/operations/"
---

# Operations

This section covers the operation of a running simplyblock deployment on Kubernetes: the lifecycle of a storage
cluster and its storage nodes, the placement and the protection of the data on them, and the monitoring and the
security of the deployment.

An action against a storage cluster or a storage node is declared as a resource of the Simplyblock Operator and applied
with `kubectl`. The operator calls the control plane, drives the action to completion, and records its outcome in the
status of the resource, so no access to the control plane itself is needed. The remaining topics act on the worker or
on the workload itself.

| Section                                     | Contents                                                                     |
|---------------------------------------------|------------------------------------------------------------------------------|
| [Cluster](cluster/index.md)                 | Cluster actions, rolling restarts, upgrades, failure domains, node affinity. |
| [Storage Nodes](storage-nodes/index.md)     | Node actions, migration, removal, replacement, and worker drain.             |
| [Scaling](scaling/index.md)                 | Expanding a cluster and adding storage nodes in parallel.                    |
| [Volumes](volumes/index.md)                 | Volume migration, filesystem trimming, and recovery from path loss.          |
| [Data Protection](data-protection/index.md) | Backup and recovery, asynchronous replication, FoundationDB backup.          |
| [Monitoring](monitoring/index.md)           | Cluster health, logical volume conditions, alerts, dashboards, and logs.     |
| [Security](security/index.md)               | Authentication, transport encryption, volume encryption, and multi-tenancy.  |
