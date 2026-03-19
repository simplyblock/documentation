---
title: "Backup and Recovery"
weight: 30600
---

Simplyblock provides built-in backup and recovery capabilities using Amazon S3 or S3-compatible object storage as a
backup target. This enables off-cluster disaster recovery, long-term data retention, and cross-cluster data portability.

## Snapshot-Based Backups

Backups in simplyblock are created from volume snapshots. When a backup is requested for a snapshot, simplyblock
automatically walks the snapshot's ancestry chain and ensures all parent snapshots are backed up first. This produces an
incremental backup chain where each backup only contains data that changed since the previous backup, minimizing storage
consumption and transfer time.

Key characteristics of simplyblock backups:

- **Incremental:** Each backup stores only the delta from its predecessor in the chain, reducing S3 storage usage and
  backup duration.
- **Chain-Aware:** The backup system automatically resolves snapshot ancestry and backs up any missing parent snapshots
  before processing the requested snapshot.
- **Asynchronous:** Backup transfers run in the background on the storage node's data plane, allowing the cluster to
  continue serving I/O without interruption.
- **Compression:** Optional compression can be enabled for backup data to further reduce S3 storage consumption.

## Backup Policies

Simplyblock supports policy-driven backup automation. Backup policies define retention rules and schedules that can be
attached to individual volumes or entire storage pools.

A backup policy includes:

- **Maximum Versions:** The maximum number of backup versions to retain. When exceeded, older backups are automatically
  merged.
- **Maximum Age:** The maximum age of a backup before it becomes eligible for cleanup (for example, `7d` for seven
  days or `12h` for twelve hours).
- **Backup Schedule:** A tiered schedule defining how frequently backups are taken at different intervals. For example,
  `15m,4 60m,11 24h,7` creates a backup every 15 minutes (keeping 4), every 60 minutes (keeping 11), and every 24
  hours (keeping 7).

When retention limits are exceeded, simplyblock automatically merges older backups into newer ones, shortening the chain
while preserving data integrity.

## Recovery

Restoring from a backup creates a new logical volume with data reconstructed from the S3 backup chain. The restore
process:

1. Creates a new volume on the target storage node with full NVMe subsystem and namespace configuration.
2. Downloads and applies each backup in the chain, starting from the oldest ancestor.
3. Once complete, the volume transitions to online status and is ready for use.

Restores can target any storage node in the cluster, not just the node where the original volume resided.

## Cross-Cluster Backup

Simplyblock supports exporting backup metadata from one cluster and importing it into another. This enables disaster
recovery scenarios where data must be restored on a completely different cluster.

The cross-cluster workflow involves:

- **Export:** Backup metadata (not the actual data) is exported as a JSON file from the source cluster.
- **Import:** The metadata is imported into the target cluster, which records the source cluster identity for S3 bucket
  resolution.
- **Source Switching:** The target cluster can switch its S3 source to read from the original cluster's backup bucket,
  enabling restore operations against the imported backup chain.

This mechanism allows organizations to maintain backup portability across independent simplyblock deployments.

## S3 Configuration

Backup storage is configured at the cluster level with the following parameters:

- **Bucket Name:** The S3 bucket used for storing backups (defaults to `simplyblock-backup-<cluster-id>`).
- **Access Credentials:** AWS access key and secret key for S3 authentication.
- **Custom Endpoint:** For S3-compatible storage (such as MinIO), a custom endpoint URL can be specified.
- **Compression:** Optionally enable compression for backup data.

For operational procedures including creating backups, restoring volumes, and managing policies, see
[Backup and Recovery Operations](../../maintenance-operations/backup-recovery.md).
