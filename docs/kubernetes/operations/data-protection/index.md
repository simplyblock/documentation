---
title: "Data Protection"
description: "Protect the data of a simplyblock cluster on Kubernetes with policy-driven backups to S3, asynchronous replication, and FoundationDB backups."
weight: 10500
---

Data is protected on three levels. A volume is backed up to S3-compatible object storage by a `StorageBackupPolicy`,
and it is replicated to a second cluster for a controlled failover. The state of the control plane itself lives in
FoundationDB and is backed up separately, since a cluster cannot be rebuilt from its volumes alone.

The pages in this section protect volumes and the control plane of one simplyblock deployment. Protecting whole
applications (their volumes together with their Kubernetes objects) across sites, with planned and unplanned
failover, is the subject of [Disaster Recovery](../../../disaster-recovery/index.md).

| Topic                                                     | Purpose                                                                         |
|-----------------------------------------------------------|---------------------------------------------------------------------------------|
| [Backup and Recovery](backup-recovery.md)                 | Backing up volumes to S3-compatible object storage, and restoring them.         |
| [Asynchronous Replication](asynchronous-replication.md)   | Replicating volumes to a second cluster, with controlled failover and failback. |
| [FoundationDB Backup and Restore](foundationdb-backup.md) | Backing up and restoring the control plane state held in FoundationDB.          |
