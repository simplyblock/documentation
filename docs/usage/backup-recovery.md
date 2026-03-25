---
title: "Backup and Recovery"
weight: 20100
---

Simplyblock provides snapshot-based backup and recovery to Amazon S3 or S3-compatible object storage. Backups can be
managed via the CLI or through Kubernetes CRDs.

For Kubernetes deployment and configuration details, see
[Kubernetes Helm Chart Parameters](../reference/kubernetes/index.md).

## CLI Operations

### Creating a Backup

Backups are created from existing volume snapshots. First, create a snapshot of the volume, then back it up:

```bash title="Create a snapshot and back it up"
{{ cliname }} snapshot add <VOLUME_ID> <SNAPSHOT_NAME> --backup
```

Alternatively, back up an existing snapshot:

```bash title="Back up an existing snapshot"
{{ cliname }} snapshot backup <SNAPSHOT_ID>
```

The backup runs asynchronously in the background. Simplyblock automatically resolves the snapshot's ancestry chain
and backs up any parent snapshots that have not yet been backed up.

!!! Important
    Once a snapshot or it's chain is backed up (completed), it can be deleted without impact on the backup itself.

### Listing Backups

To list all backups in the cluster:

```bash title="List backups"
{{ cliname }} backup list [--cluster-id <CLUSTER_ID>]
```

This may also reference imported (external) backups taken on another cluster.

### Restoring from a Backup

Restoring a backup creates a new logical volume with the data reconstructed from the S3 backup chain:

```bash title="Restore a backup"
{{ cliname }} backup restore <BACKUP_ID> --lvol <NEW_VOLUME_NAME> --pool <POOL_ID> [--node <TARGET_NODE_ID>] [--cluster-id <CLUSTER_ID>]
```

The restore process downloads and applies each backup in the chain. The new volume is set to a restoring state during
the transfer and transitions to online once complete.

!!! warning
    The restore operation creates a new volume. It does not overwrite or modify any existing volume.

### Deleting Backups

To delete all backups for a specific volume:

```bash title="Delete backups for a volume"
{{ cliname }} backup delete <LVOL_ID>
```

### Backup Policies

Backup policies automate backup creation and retention management.

#### Creating a Policy

```bash title="Create a backup policy"
{{ cliname }} backup policy-add <CLUSTER_ID> <POLICY_NAME> [--versions <MAX_VERSIONS>] [--age <MAX_AGE>] [--schedule "<SCHEDULE>"]
```

Parameters:

- `--versions`: Maximum number of backup versions to retain (e.g., `10`).
- `--age`: Maximum backup age before cleanup (e.g., `7d`, `12h`, `1w`).
- `--schedule`: Tiered backup schedule (e.g., `"15m,4 60m,11 24h,7"`).

The schedule format is a space-separated list of `interval,count` pairs. For example, `15m,4 60m,11 24h,7` means:
take a backup every 15 minutes (keep 4), every 60 minutes (keep 11), and every 24 hours (keep 7).

#### Attaching a Policy

Policies can be attached to individual volumes or entire storage pools:

```bash title="Attach a policy to a pool"
{{ cliname }} backup policy-attach <POLICY_ID> pool <POOL_ID>
```

```bash title="Attach a policy to a volume"
{{ cliname }} backup policy-attach <POLICY_ID> lvol <LVOL_ID>
```

#### Detaching a Policy

```bash title="Detach a policy"
{{ cliname }} backup policy-detach <POLICY_ID> pool <POOL_ID>
{{ cliname }} backup policy-detach <POLICY_ID> lvol <LVOL_ID>
```

Detaching a policy does not impact existing backups!

#### Listing and Removing Policies

```bash title="List backup policies"
{{ cliname }} backup policy-list [--cluster-id <CLUSTER_ID>]
```

```bash title="Remove a policy"
{{ cliname }} backup policy-remove <POLICY_ID>
```

### Cross-Cluster Backup

Cross-cluster backup enables restoring data on a different simplyblock cluster using backups stored in S3.

#### Exporting Backup Metadata

Export backup metadata from the source cluster:

```bash title="Export backup metadata"
{{ cliname }} backup export [--cluster-id <CLUSTER_ID>] [--lvol <VOLUME_NAME>] [-o <OUTPUT_FILE>]
```

This produces a JSON file containing backup metadata (not the actual data, which remains in S3).

#### Importing Backup Metadata

##### Switching Backup Source

Before restoring imported backups, switch the cluster's S3 source to read from the original cluster's bucket:

```bash title="Switch backup source"
{{ cliname }} backup source-switch <SOURCE_CLUSTER_ID> [--cluster-id <CLUSTER_ID>]
```

To list available backup sources:

```bash title="List backup sources"
{{ cliname }} backup source-list [--cluster-id <CLUSTER_ID>]
```

!!! warning
    While the backup source is switched to an external cluster, new backups cannot be created on the local cluster.
    Switch back to the local source after completing restore operations.

After switching the source, use the standard `backup restore` command to restore from the imported backups.

On the target cluster, import the metadata:

```bash title="Import backup metadata"
{{ cliname }} backup import <METADATA_FILE> [--cluster-id <CLUSTER_ID>]
```

!!! Warning
    Do not forget to switch back the source to the internal cluster to resume normal backup operations.

## Kubernetes CRD Operations

In Kubernetes environments, backups can also be managed declaratively using Custom Resource Definitions. This is
especially useful for automated backup workflows integrated with Kubernetes-native tooling.

### Backup CRD

The `Backup` CRD (`backups.simplyblock.com`, short name: `bkp`) creates a one-time backup of all PVCs in a pool or a
single PVC.

```yaml title="Back up all PVCs in a pool to S3"
apiVersion: simplyblock.com/v25.10.5
kind: Backup
metadata:
  name: daily-backup
  namespace: simplyblock
spec:
  clusterUUID: "<CLUSTER_UUID>"
  pool: "production"
  s3:
    bucket: "simplyblock-backups"
    region: "eu-central-1"
    accessKeySecret: "backup-s3-credentials"
    secretKeySecret: "backup-s3-credentials"
  retention: 7
```

```yaml title="Back up a single PVC"
apiVersion: simplyblock.com/v25.10.5
kind: Backup
metadata:
  name: db-backup
  namespace: simplyblock
spec:
  clusterUUID: "<CLUSTER_UUID>"
  pvc: "postgres-data"
  s3:
    bucket: "simplyblock-backups"
    region: "eu-central-1"
    accessKeySecret: "backup-s3-credentials"
    secretKeySecret: "backup-s3-credentials"
```

#### Spec Fields

| Field                    | Type    | Description                                                     |
|--------------------------|---------|-----------------------------------------------------------------|
| `clusterUUID`           | string  | UUID of the cluster                                              |
| `pool`                  | string  | Pool to snapshot and back up (all PVCs)                          |
| `pvc`                   | string  | Individual PVC to back up (alternative to pool)                  |
| `s3.bucket`             | string  | S3 bucket name                                                   |
| `s3.region`             | string  | AWS region                                                       |
| `s3.accessKeySecret`    | string  | Kubernetes Secret for S3 access key                              |
| `s3.secretKeySecret`    | string  | Kubernetes Secret for S3 secret key                              |
| `filesystem.mountPoint` | string  | Filesystem mount point (alternative to S3)                       |
| `retention`             | integer | Number of backups to retain                                      |
| `keepOnlineBackup`      | boolean | Keep the online snapshot after backup completes                  |
| `backupRestoreList`     | string  | JSON file with backup metadata for cross-cluster restore         |
| `replacePVConRestore`   | boolean | Replace existing bound PVCs during restore (instead of creating new ones) |

#### Monitoring Backup Status

```bash title="List backups"
kubectl get bkp -n simplyblock
```

```plain
NAME           CLUSTER      POOL         PVC   TARGET                RETENTION   STATE
daily-backup   abc123...    production         simplyblock-backups   7           Completed
```

The status field shows: `Pending`, `Running`, `Completed`, or `Failed`.

For detailed status including per-PVC backup details:

```bash title="Get detailed backup status"
kubectl get bkp daily-backup -n simplyblock -o yaml
```

The status includes a `PVCs` array with per-PVC information: PVC name, pool UUID, and the list of backup IDs with
their corresponding snapshot UUIDs.

#### Restoring from a Backup CRD

To restore, update the Backup CRD with the `restore` action:

```yaml title="Restore from backup"
apiVersion: simplyblock.com/v25.10.5
kind: Backup
metadata:
  name: daily-backup
  namespace: simplyblock
spec:
  clusterUUID: "<CLUSTER_UUID>"
  pool: "production"
  action: "restore"
  s3:
    bucket: "simplyblock-backups"
    region: "eu-central-1"
    accessKeySecret: "backup-s3-credentials"
    secretKeySecret: "backup-s3-credentials"
```

To restore from a cross-cluster backup, provide the backup metadata JSON file:

```yaml title="Cross-cluster restore"
spec:
  action: "restore"
  backupRestoreList: "/path/to/backup-metadata.json"
  replacePVConRestore: false
```

Setting `replacePVConRestore: true` will replace existing bound PVCs with the restored data instead of creating new
PVCs.

### BackupSchedule CRD

The `BackupSchedule` CRD (`backupscheduless.simplyblock.com`, short name: `bks`) defines recurring backup schedules.

```yaml title="Scheduled backup for a pool"
apiVersion: simplyblock.com/v25.10.5
kind: BackupSchedule
metadata:
  name: hourly-backup
  namespace: simplyblock
spec:
  clusterUUID: "<CLUSTER_UUID>"
  pool: "production"
  s3:
    bucket: "simplyblock-backups"
    region: "eu-central-1"
    accessKeySecret: "backup-s3-credentials"
    secretKeySecret: "backup-s3-credentials"
```

#### Actions

| Action               | Description                                      |
|----------------------|--------------------------------------------------|
| `restore`           | Restores volumes from backups in this schedule    |
| `delete-all-backups`| Deletes all backups created by this schedule      |

#### Monitoring Schedule Status

```bash title="List backup schedules"
kubectl get bks -n simplyblock
```

The status tracks the list of backup IDs created by the schedule, along with per-PVC backup details.
