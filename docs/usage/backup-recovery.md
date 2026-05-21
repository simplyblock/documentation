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

!!! important
    Once a snapshot or its chain is backed up (completed), it can be deleted without impact on the backup itself.

### Listing Backups

To list all backups in the cluster:

```bash title="List backups"
{{ cliname }} backup list [--cluster-id <CLUSTER_ID>]
```

This may also reference imported (external) backups taken on another cluster.

### Restoring from a Backup

Restoring a backup creates a new logical volume with the data reconstructed from the S3 backup chain:

```bash title="Restore a backup"
{{ cliname }} backup restore <BACKUP_ID> \
  --lvol <NEW_VOLUME_NAME> --pool <POOL_ID> \
  [--node <TARGET_NODE_ID>] [--cluster-id <CLUSTER_ID>]
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
{{ cliname }} backup policy-add \
  <CLUSTER_ID> <POLICY_NAME> \
  [--versions <MAX_VERSIONS>] \
  [--age <MAX_AGE>] \
  [--schedule "<SCHEDULE>"]
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
{{ cliname }} backup export \
  [--cluster-id <CLUSTER_ID>] \
  [--lvol <VOLUME_NAME>] \
  [-o <OUTPUT_FILE>]
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

!!! warning
    Do not forget to switch back the source to the internal cluster to resume normal backup operations.

## Kubernetes CRD Operations

In Kubernetes environments, backups can be managed declaratively using Custom Resource Definitions (CRDs). This
is especially useful for automated backup workflows integrated with Kubernetes-native tooling.

### Prerequisites

#### S3-Compatible Object Storage

Backups require an S3-compatible object storage endpoint. For local testing, you can deploy a Minio instance:

```sh title="Deploy a local Minio instance for testing"
kubectl create ns minio

kubectl -n minio create deployment minio \
  --image=minio/minio \
  -- /bin/sh -c "minio server /data --console-address :9001"

kubectl -n minio expose deploy/minio --port 9000

kubectl -n minio set env deploy/minio \
  MINIO_ROOT_USER=minioadmin \
  MINIO_ROOT_PASSWORD=minioadmin123
```

#### Backup Credentials Secret

Store your S3 credentials in a Kubernetes Secret in the same namespace as your `StorageCluster`:

```yaml title="Create backup credentials secret"
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: backup-credentials
  namespace: simplyblock
type: Opaque
stringData:
  access_key_id: <YOUR_ACCESS_KEY>
  secret_access_key: <YOUR_SECRET_KEY>
EOF
```

#### StorageCluster Backup Configuration

Include a `backup` section in your `StorageCluster` spec referencing the credentials secret:

```yaml title="StorageCluster backup configuration"
spec:
  # ... other fields ...
  backup:
    credentialsSecretRef:
      name: backup-credentials
    localEndpoint: http://minio.minio.svc.cluster.local:9000
    snapshotBackups: true
    withCompression: false
```

See the [Operator Reference](../reference/operator.md#storage-cluster) for all available `backup` spec fields.

### StorageBackup CRD

The `StorageBackup` resource creates a one-time backup of a PVC to the configured S3-compatible storage endpoint.

```yaml title="Create a backup for a PVC"
kubectl apply -f - <<'EOF'
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageBackup
metadata:
  name: my-pvc-backup
  namespace: simplyblock
spec:
  clusterName: simplyblock-cluster
  pvcRef:
    name: my-pvc
EOF
```

Monitor the backup status:

```bash title="List backups"
kubectl -n simplyblock get storagebackup
```

```plain
NAME            PHASE   PVC      BACKUPID                               SNAPSHOT              AGE
my-pvc-backup   Done    my-pvc   7fab02f8-03f6-4e76-a9ac-78b63b1ce8ef   backup-my-pvc-backup  3m
```

!!! note
    The first backup may take longer to complete as there is no prior incremental state.

#### Spec Fields

| Field         | Type   | Description                                          |
|---------------|--------|------------------------------------------------------|
| `clusterName` | string | Name of the target StorageCluster. **Required**.     |
| `pvcRef.name` | string | Name of the PVC to back up. **Required**.            |

#### Status Fields

| Column     | Description                                      |
|------------|--------------------------------------------------|
| `PHASE`    | Current phase: `InProgress` or `Done`.           |
| `PVC`      | Name of the source PVC.                          |
| `BACKUPID` | Backend backup identifier.                       |
| `SNAPSHOT` | Name of the snapshot used for the backup.        |

### BackupRestore CRD

The `BackupRestore` resource restores a `StorageBackup` into a new PVC. The restored PVC is created in the
same namespace as the `BackupRestore` object.

```yaml title="Restore a backup to a new PVC"
kubectl apply -f - <<'EOF'
apiVersion: storage.simplyblock.io/v1alpha1
kind: BackupRestore
metadata:
  name: my-restore
  namespace: simplyblock
spec:
  clusterName: simplyblock-cluster
  backupRef:
    name: my-pvc-backup
  pvcTemplate:
    metadata:
      name: restored-pvc
    spec:
      accessModes:
        - ReadWriteOnce
      resources:
        requests:
          storage: 10Gi
EOF
```

Monitor the restore status:

```bash title="List restores"
kubectl -n simplyblock get backuprestore
```

```plain
NAME         PHASE   BACKUP          PVC            AGE
my-restore   Done    my-pvc-backup   restored-pvc   79s
```

The phase transitions from `InProgress` → `PVCBinding` → `Done`. Once `Done`, the new PVC is ready to attach
to a pod.

#### Spec Fields

| Field                       | Type   | Description                                                                    |
|-----------------------------|--------|--------------------------------------------------------------------------------|
| `clusterName`               | string | Name of the target StorageCluster. **Required**.                               |
| `backupRef.name`            | string | Name of the `StorageBackup` to restore from. **Required**.                     |
| `targetPool`                | string | Pool to restore into. Defaults to the source backup PVC's pool.                |
| `targetNode`                | string | Storage node to restore to. Defaults to the node that held the original backup.|
| `pvcTemplate.metadata.name` | string | Name of the new PVC to create. **Required**.                                   |
| `pvcTemplate.spec`          | object | PVC spec (accessModes, resources, etc.).                                       |

!!! warning
    A backup can only be restored to the same namespace as the `BackupRestore` object.

### BackupPolicy CRD

A `BackupPolicy` defines an automated backup schedule with retention settings. Attach it to a PVC using the
`simplybk/backup-policy` annotation to automatically create `StorageBackup` objects on schedule.

```yaml title="Create a backup policy"
kubectl apply -f - <<'EOF'
apiVersion: storage.simplyblock.io/v1alpha1
kind: BackupPolicy
metadata:
  name: my-policy
  namespace: simplyblock
spec:
  clusterName: simplyblock-cluster
  maxVersions: 10
  maxAge: "7d"
  schedule: "15m,4 60m,11 24h,7"
EOF
```

#### Spec Fields

| Field         | Type   | Description                                                                       |
|---------------|--------|-----------------------------------------------------------------------------------|
| `clusterName` | string | Name of the target StorageCluster. **Required**.                                  |
| `maxVersions` | int    | Maximum number of backup versions to retain.                                      |
| `maxAge`      | string | Maximum backup age before cleanup (e.g., `7d`, `12h`).                           |
| `schedule`    | string | Tiered backup schedule as space-separated `interval,count` pairs.                 |

The schedule format is a space-separated list of `interval,count` pairs. For example, `15m,4 60m,11 24h,7` means:
take a backup every 15 minutes (keep the 4 most recent), every 60 minutes (keep 11), and every 24 hours (keep 7).

#### Attaching a Policy to a PVC

Apply the `simplybk/backup-policy` annotation to start automatic backups for a PVC:

```bash title="Attach a backup policy"
kubectl annotate pvc my-pvc -n simplyblock simplybk/backup-policy=my-policy
```

The policy will begin creating `StorageBackup` objects automatically. View them with:

```bash title="List auto-created backups"
kubectl get storagebackup -n simplyblock
```

#### Updating and Detaching Policies

To switch a PVC to a different policy (detaches from the old policy and attaches to the new one):

```bash title="Switch to a different policy"
kubectl annotate pvc my-pvc -n simplyblock simplybk/backup-policy=new-policy --overwrite
```

To detach a policy from a PVC (existing backups are not deleted):

```bash title="Detach a backup policy"
kubectl annotate pvc my-pvc -n simplyblock simplybk/backup-policy-
```
