---
title: "Data Protection"
description: "Protect the data of a simplyblock cluster outside Kubernetes with snapshot backups to S3-compatible object storage and asynchronous replication."
source: "https://docs.simplyblock.io/latest/non-kubernetes/operations/data-protection/"
---

# Data Protection

Data is protected on two levels outside Kubernetes. A logical volume is backed up to S3-compatible object storage as a
chain of snapshots, and its snapshots are replicated to a second cluster, from which a failover can be served.

| Topic                                                   | Purpose                                                                |
|---------------------------------------------------------|------------------------------------------------------------------------|
| [Backup and Recovery](backup-recovery.md)               | Backing up a volume to S3-compatible object storage, and restoring it. |
| [Asynchronous Replication](asynchronous-replication.md) | Replicating snapshots to a second cluster for a failover.              |
