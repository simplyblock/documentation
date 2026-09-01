---
title: "Backup and Recovery"
description: "Snapshot-based backup and recovery to Amazon S3 or S3-compatible object storage, managed through Kubernetes CRDs or the Simplyblock CLI."
source: "https://docs.simplyblock.io/latest/kubernetes/operations/data-protection/backup-recovery/"
---

# Backup and Recovery

Simplyblock provides snapshot-based backup and recovery to Amazon S3 or S3-compatible object storage. Backups can be
managed via the CLI or through Kubernetes CRDs.

In Kubernetes environments, backups can be managed declaratively using Custom Resource Definitions (CRDs). This
is especially useful for automated backup workflows integrated with Kubernetes-native tooling.

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

| Field         | Type   | Description                                      |
|---------------|--------|--------------------------------------------------|
| `clusterName` | string | Name of the target StorageCluster. **Required**. |
| `pvcRef.name` | string | Name of the PVC to back up. **Required**.        |

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
to a pod.

#### Spec Fields

| Field                       | Type   | Description                                                                     |
|-----------------------------|--------|---------------------------------------------------------------------------------|
| `clusterName`               | string | Name of the target StorageCluster. **Required**.                                |
| `backupRef.name`            | string | Name of the `StorageBackup` to restore from. **Required**.                      |
| `targetPool`                | string | Pool to restore into. Defaults to the source backup PVC's pool.                 |
| `targetNode`                | string | Storage node to restore to. Defaults to the node that held the original backup. |
| `pvcTemplate.metadata.name` | string | Name of the new PVC to create. **Required**.                                    |
| `pvcTemplate.spec`          | object | PVC spec (accessModes, resources, etc.).                                        |

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
| `maxVersions` | int    | Maximum number of backup versions to retain.                      |
| `maxAge`      | string | Maximum backup age before cleanup (e.g., `7d`, `12h`).            |
| `schedule`    | string | Tiered backup schedule as space-separated `interval,count` pairs. |

The schedule format is a space-separated list of `interval,count` pairs. For example, `15m,4 60m,11 24h,7` means:
take a backup every 15 minutes (keep the 4 most recent), every 60 minutes (keep 11), and every 24 hours (keep 7).

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
