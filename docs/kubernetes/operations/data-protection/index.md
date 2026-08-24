---
title: "Data Protection"
description: "Protect the data of a simplyblock cluster on Kubernetes with snapshot backups to object storage, asynchronous replication, and FoundationDB backups."
weight: 10500
---

Data is protected on three levels. A volume is backed up to S3-compatible object storage as a chain of snapshots, and
it is replicated to a second cluster for a controlled failover. The state of the control plane itself lives in
FoundationDB and is backed up separately, since a cluster cannot be rebuilt from its volumes alone.

| Topic                                                     | Purpose                                                                         |
|-----------------------------------------------------------|---------------------------------------------------------------------------------|
| [Backup and Recovery](backup-recovery.md)                 | Backing up a volume to S3-compatible object storage, and restoring it.          |
| [Asynchronous Replication](asynchronous-replication.md)   | Replicating volumes to a second cluster, with controlled failover and failback. |
| [FoundationDB Backup and Restore](foundationdb-backup.md) | Backing up and restoring the control plane state held in FoundationDB.          |
