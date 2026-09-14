---
title: "Backup and Recovery"
description: "Snapshot-based backup and recovery to Amazon S3 or S3-compatible object storage, managed through Kubernetes CRDs or the Simplyblock CLI."
source: "https://docs.simplyblock.io/latest/kubernetes/operations/data-protection/backup-recovery/"
---

# Backup and Recovery

Simplyblock provides snapshot-based backup and recovery to Amazon S3 or S3-compatible object storage. In
Kubernetes environments, backups are managed declaratively using Custom Resource Definitions (CRDs). This is
especially useful for automated backup workflows integrated with Kubernetes-native tooling. The same engine can
also be driven through the CLI, see
[Backup and Recovery on plain Linux](../../../non-kubernetes/operations/data-protection/backup-recovery.md).

### Prerequisites

#### S3-Compatible Object Storage

Backups require an S3-compatible object storage endpoint. For local testing, a MinIO instance can be deployed:

```bash title="Deploy a local MinIO instance for testing"
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

Store the S3 credentials in a Kubernetes Secret in the same namespace as the `StorageCluster`:

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

Include a `backup` section in the `StorageCluster` spec referencing the credentials secret:

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

| Field                       | Default | Description                                                                      |
|-----------------------------|---------|----------------------------------------------------------------------------------|
| `credentialsSecretRef.name` | —       | Secret with `access_key_id` and `secret_access_key`. **Required**.               |
| `localEndpoint`             | AWS S3  | Endpoint URL for S3-compatible storage (e.g., MinIO). Leave unset for Amazon S3. |
| `snapshotBackups`           | `true`  | Allow snapshots to be used as backup sources.                                    |
| `withCompression`           | `false` | Compress backup data before upload.                                              |
| `secondaryTarget`           | `0`     | Secondary backup target selector (advanced).                                     |

See the [Operator Reference](../../../reference/operator/reference.md#storagecluster) for all available `backup` spec fields.

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

| Field          | Type   | Description                                                      |
|----------------|--------|------------------------------------------------------------------|
| `clusterName`  | string | Name of the target StorageCluster. **Required**.                 |
| `pvcRef.name`  | string | Name of the PVC to back up. **Required**.                        |
| `snapshotName` | string | Overrides the name of the internally created snapshot. Optional. |

The backup also records the source volume's filesystem type in its status (`fsType`), so a later restore mounts
the restored volume with the same filesystem regardless of the target StorageClass defaults.

#### Status Fields

| Column     | Description                               |
|------------|-------------------------------------------|
| `PHASE`    | Current phase: `InProgress` or `Done`.    |
| `PVC`      | Name of the source PVC.                   |
| `BACKUPID` | Backend backup identifier.                |
| `SNAPSHOT` | Name of the snapshot used for the backup. |

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
to a pod. The restored PersistentVolume is created with the filesystem type recorded in the source backup, and an
encrypted source volume is restored encrypted.

#### Spec Fields

| Field                       | Type   | Description                                                                 |
|-----------------------------|--------|-----------------------------------------------------------------------------|
| `clusterName`               | string | Name of the target StorageCluster. **Required**.                            |
| `backupRef.name`            | string | Name of the `StorageBackup` to restore from. **Required**.                  |
| `targetPool`                | string | Pool to restore into. Defaults to the source backup PVC's pool.             |
| `targetNode`                | string | Storage node to restore to. Defaults to automatic placement in the cluster. |
| `pvcTemplate.metadata.name` | string | Name of the new PVC to create. **Required**.                                |
| `pvcTemplate.spec`          | object | PVC spec (accessModes, resources, etc.).                                    |

!!! warning
    A backup can only be restored to the same namespace as the `BackupRestore` object.

### BackupPolicy CRD

A `BackupPolicy` defines an automated backup schedule with retention settings. Attach it to a PVC using the
`simplyblock.io/backup-policy` annotation to automatically create `StorageBackup` objects on schedule.

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

| Field         | Type   | Description                                                       |
|---------------|--------|-------------------------------------------------------------------|
| `clusterName` | string | Name of the target StorageCluster. **Required**.                  |
| `maxVersions` | int    | Maximum number of completed backup versions to retain.            |
| `maxAge`      | string | Maximum backup age (e.g., `7d`, `12h`, `30m`).                    |
| `schedule`    | string | Tiered backup schedule as space-separated `interval,count` pairs. |

The schedule format is a space-separated list of `interval,count` pairs with strictly increasing intervals. For
example, `15m,4 60m,11 24h,7` means: take a backup every 15 minutes (keep the 4 most recent), every 60 minutes
(keep 11), and every 24 hours (keep 7).

Retention does not delete data: when `maxVersions` or `maxAge` is exceeded, the oldest backup is merged into the
next one, so the number of restore points shrinks while the backup chain stays complete.

#### Attaching a Policy to a PVC

Apply the `simplyblock.io/backup-policy` annotation to start automatic backups for a PVC:

```bash title="Attach a backup policy"
kubectl annotate pvc my-pvc -n simplyblock simplyblock.io/backup-policy=my-policy
```

The policy will begin creating `StorageBackup` objects automatically. View them with:

```bash title="List auto-created backups"
kubectl get storagebackup -n simplyblock
```

#### Updating and Detaching Policies

To switch a PVC to a different policy (detaches from the old policy and attaches to the new one):

```bash title="Switch to a different policy"
kubectl annotate pvc my-pvc -n simplyblock simplyblock.io/backup-policy=new-policy --overwrite
```

To detach a policy from a PVC (existing backups are not deleted):

```bash title="Detach a backup policy"
kubectl annotate pvc my-pvc -n simplyblock simplyblock.io/backup-policy-
```

### BackupImport CRD (Cross-Cluster Restore)

A `BackupImport` makes a backup taken on one simplyblock cluster restorable on another. Both clusters must be
represented as `StorageCluster` resources managed by the same operator, and the target cluster's storage nodes
must be able to reach the source cluster's S3 bucket.

Find the backup to import on the source cluster (`BACKUPID` column of `kubectl get storagebackup`), then create
the import against the target cluster:

```yaml title="Import a backup from another cluster"
kubectl apply -f - <<'MANIFEST'
apiVersion: storage.simplyblock.io/v1alpha1
kind: BackupImport
metadata:
  name: my-import
  namespace: simplyblock
spec:
  sourceClusterName: cluster-a
  sourceBackupID: 7fab02f8-03f6-4e76-a9ac-78b63b1ce8ef
  targetClusterName: cluster-b
MANIFEST
```

The phase transitions from `Pending` → `Exporting` → `Importing` → `Done`. On completion, the controller has
imported the backup metadata into the target cluster and created a `StorageBackup` resource marked as imported;
its name is published in `status.storageBackupRef`.

```bash title="Check the import"
kubectl -n simplyblock get backupimport my-import -o jsonpath='{.status.storageBackupRef}'
```

Reference that `StorageBackup` in a regular [`BackupRestore`](#backuprestore-crd) to restore it. The restore
controller detects the foreign source and reads from the source cluster's bucket using the source
`StorageCluster`'s own backup credentials — unlike the CLI flow, no cluster-wide backup-source switch is needed,
and local backups continue uninterrupted.

#### Spec Fields

| Field               | Type   | Description                                                            |
|---------------------|--------|------------------------------------------------------------------------|
| `sourceClusterName` | string | StorageCluster name of the cluster that owns the backup. **Required**. |
| `sourceBackupID`    | string | Backup UUID on the source cluster. **Required**.                       |
| `targetClusterName` | string | StorageCluster name of the cluster to import into. **Required**.       |

## Control-Plane Backups

The CRDs on this page protect volume data. The control-plane database itself is backed up separately, see
[FoundationDB Backup and Restore](foundationdb-backup.md).
