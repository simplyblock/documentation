---
title: "Backup and Recovery"
description: "Snapshot-based backup and recovery to Amazon S3 or S3-compatible object storage on plain Linux, managed through the Simplyblock CLI."
weight: 10510
---

Simplyblock provides snapshot-based backup and recovery to Amazon S3 or S3-compatible object storage. A backup is
an incremental copy of a volume snapshot; restoring reconstructs the data from the backup chain into a new volume.

On plain Linux, backups are managed through the CLI. In Kubernetes environments, the same engine is driven
declaratively through CRDs, see
[Backup and Recovery on Kubernetes](../../../kubernetes/operations/data-protection/backup-recovery.md).

## Configuring the Backup Target

The S3 target is configured at cluster creation time by passing a JSON configuration file:

```bash title="Enable backups at cluster creation"
{{ cliname }} cluster create ... --use-backup backup-config.json
```

The same parameter is available on `cluster add`. The configuration file has the following format:

```json title="backup-config.json"
{
  "access_key_id": "<S3_ACCESS_KEY>",
  "secret_access_key": "<S3_SECRET_KEY>",
  "local_endpoint": "http://minio.internal:9000",
  "bucket_name": "my-backup-bucket",
  "with_compression": false,
  "snapshot_backups": true
}
```

| Key                 | Default                           | Description                                                                      |
|---------------------|-----------------------------------|----------------------------------------------------------------------------------|
| `access_key_id`     | —                                 | S3 access key. **Required**.                                                     |
| `secret_access_key` | —                                 | S3 secret key. **Required**.                                                     |
| `local_endpoint`    | AWS S3                            | Endpoint URL for S3-compatible storage (e.g., MinIO). Leave unset for Amazon S3. |
| `bucket_name`       | `simplyblock-backup-<CLUSTER_ID>` | Bucket for backup data. Created automatically if it does not exist.              |
| `with_compression`  | `false`                           | Compress backup data before upload.                                              |
| `snapshot_backups`  | `true`                            | Allow snapshots to be used as backup sources.                                    |
| `secondary_target`  | `0`                               | Secondary backup target selector (advanced).                                     |

All storage nodes of the cluster must be able to reach the configured endpoint, since backups are written
directly from the storage nodes.

## Creating a Backup

Backups are created from volume snapshots. Create a snapshot and back it up in one step:

```bash title="Create a snapshot and back it up"
{{ cliname }} snapshot add <VOLUME_ID> <SNAPSHOT_NAME> --backup
```

Alternatively, back up an existing snapshot:

```bash title="Back up an existing snapshot"
{{ cliname }} snapshot backup <SNAPSHOT_ID>
```

The backup runs asynchronously in the background. Simplyblock automatically resolves the snapshot's ancestry chain
and backs up any parent snapshots that have not yet been backed up, so every backup is incremental against the
previous one.

Backups of encrypted volumes stay encrypted: the volume's data encryption keys are preserved through the cluster's
key management system and are applied again on restore.

!!! important
    Once a snapshot or its chain is backed up (completed), it can be deleted without impact on the backup itself.

## Listing Backups

To list all backups in the cluster:

```bash title="List backups"
{{ cliname }} backup list [--cluster-id <CLUSTER_ID>]
```

The list may also contain imported (external) backups taken on another cluster, see
[Cross-Cluster Backup](#cross-cluster-backup).

## Restoring from a Backup

Restoring a backup creates a new logical volume with the data reconstructed from the S3 backup chain:

```bash title="Restore a backup"
{{ cliname }} backup restore <BACKUP_ID> \
  --lvol <NEW_VOLUME_NAME> --pool <POOL_NAME_OR_ID> \
  [--node <TARGET_NODE_ID>]
```

The `--lvol` and `--pool` parameters are required. The target cluster is derived from the pool. Any node of the
cluster can restore any backup; without `--node`, a node is selected automatically by the regular volume placement.

The restore process downloads and applies each backup of the chain, newest first. The new volume is in the
`restoring` state during the transfer and transitions to online once complete.

A restore is only accepted when every backup in the chain has completed, and when the backup's source cluster
matches the currently active S3 backup source (see [Cross-Cluster Backup](#cross-cluster-backup) for restoring
backups taken on another cluster).

!!! warning
    The restore operation creates a new volume. It does not overwrite or modify any existing volume.

!!! note
    The restored volume is created with the cluster's default high-availability type and NVMe/TCP, regardless of
    the settings of the original volume. Encryption and the allowed-host list of the original volume are preserved.
    Deleting the original snapshot or volume does not affect its backups.

## Deleting Backups

To delete all backups for a specific volume, including the backup data in S3:

```bash title="Delete backups for a volume"
{{ cliname }} backup delete <LVOL_ID>
```

## Backup Policies

Backup policies automate backup creation and retention management.

### Creating a Policy

```bash title="Create a backup policy"
{{ cliname }} backup policy-add \
  <CLUSTER_ID> <POLICY_NAME> \
  [--versions <MAX_VERSIONS>] \
  [--age <MAX_AGE>] \
  [--schedule "<SCHEDULE>"]
```

Parameters:

- `--versions`: Maximum number of completed backup versions to retain (e.g., `10`).
- `--age`: Maximum backup age (e.g., `7d`, `12h`, `1w`).
- `--schedule`: Tiered backup schedule (e.g., `"15m,4 60m,11 24h,7"`).

The schedule format is a space-separated list of `interval,count` pairs. For example, `15m,4 60m,11 24h,7` means:
take a backup every 15 minutes (keep 4), every 60 minutes (keep 11), and every 24 hours (keep 7).

Retention does not delete data: when a policy's version or age limit is exceeded, the oldest backup is merged
into the next one, so the number of restore points shrinks while the backup chain stays complete.

### Attaching a Policy

Policies can be attached to individual volumes or entire storage pools:

```bash title="Attach a policy to a pool"
{{ cliname }} backup policy-attach <POLICY_ID> pool <POOL_ID>
```

```bash title="Attach a policy to a volume"
{{ cliname }} backup policy-attach <POLICY_ID> lvol <LVOL_ID>
```

### Detaching a Policy

```bash title="Detach a policy"
{{ cliname }} backup policy-detach <POLICY_ID> pool <POOL_ID>
{{ cliname }} backup policy-detach <POLICY_ID> lvol <LVOL_ID>
```

Detaching a policy does not impact existing backups!

### Listing and Removing Policies

```bash title="List backup policies"
{{ cliname }} backup policy-list [--cluster-id <CLUSTER_ID>]
```

```bash title="Remove a policy"
{{ cliname }} backup policy-remove <POLICY_ID>
```

## Cross-Cluster Backup

Cross-cluster backup enables restoring data on a different simplyblock cluster using backups stored in S3.

### Exporting Backup Metadata

Export backup metadata from the source cluster:

```bash title="Export backup metadata"
{{ cliname }} backup export \
  [--cluster-id <CLUSTER_ID>] \
  [--lvol <VOLUME_NAME>] \
  [-o <OUTPUT_FILE>]
```

This produces a JSON file containing backup metadata (not the actual data, which remains in S3).

### Importing Backup Metadata

On the target cluster, import the metadata:

```bash title="Import backup metadata"
{{ cliname }} backup import <METADATA_FILE> --cluster-id <TARGET_CLUSTER_ID>
```

### Switching the Backup Source

Before restoring imported backups, switch the target cluster's S3 source to read from the original cluster's
bucket:

```bash title="Switch backup source"
{{ cliname }} backup source-switch <SOURCE_CLUSTER_ID> [--cluster-id <TARGET_CLUSTER_ID>]
```

The switch changes only the bucket that is read; the target cluster's own S3 credentials and endpoint are reused,
so they must have access to the source cluster's bucket. Attempting to restore an imported backup without
switching the source first is rejected with a message naming the required source. To list available backup
sources:

```bash title="List backup sources"
{{ cliname }} backup source-list [--cluster-id <CLUSTER_ID>]
```

!!! warning
    While the backup source is switched to an external cluster, new backups cannot be created on the local cluster.
    Switch back to the local source after completing restore operations.

After switching the source, use the standard `backup restore` command to restore from the imported backups. The
target node is selected automatically in the target cluster; `--node` may be passed to pin one.

Once the restores are complete, switch the source back:

```bash title="Switch back to the local backup source"
{{ cliname }} backup source-switch local [--cluster-id <TARGET_CLUSTER_ID>]
```

## Kubernetes

In Kubernetes environments, the same backup engine is managed declaratively through the `StorageBackup`,
`BackupRestore`, `BackupPolicy`, and `BackupImport` custom resources. See
[Backup and Recovery on Kubernetes](../../../kubernetes/operations/data-protection/backup-recovery.md).
