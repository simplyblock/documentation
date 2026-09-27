---
title: "Backup and Recovery"
description: "Snapshot-based backup and recovery to Amazon S3 or S3-compatible object storage, managed through Kubernetes CRDs or the Simplyblock CLI."
weight: 10510
---

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

Include a `backup` section in the `StorageCluster` spec referencing the credentials secret. The block is the
location backups go to and nothing else: how a copy is taken and what it contains are the control plane's.

```yaml title="StorageCluster backup configuration"
spec:
  # ... other fields ...
  backup:
    endpoint: http://minio.minio.svc.cluster.local:9000
    bucket: simplyblock-backups
    prefix: cluster-a
    region: us-east-1
    credentialsSecretRef:
      name: backup-credentials
```

| Field                       | Default | Description                                                                  |
|-----------------------------|---------|------------------------------------------------------------------------------|
| `endpoint`                  | —       | S3 endpoint URL. **Required**.                                               |
| `bucket`                    | —       | Bucket backups are written to and read from. **Required**.                   |
| `credentialsSecretRef.name` | —       | Secret with the access key and the secret key. **Required**.                 |
| `prefix`                    | —       | Narrows the store to one key prefix, so several clusters can share a bucket. |
| `region`                    | —       | The bucket's region, for endpoints that do not imply one.                    |

The whole block is mutable. A cluster can be created without a store and given one later, and what changes when it
changes is which backups have objects, since the object set is derived from the location rather than accumulated.

See the [Operator Reference](../../../reference/operator/reference.md#backupstorespec) for all available fields.

### StorageBackup

A `StorageBackup` is one backup held in the store. It is **discovered, not created**: the operator subscribes to the
store's inventory and writes one object per backup it finds, so a user neither creates nor deletes these objects.
Its spec is only the backup's identity — the cluster and the backend backup id.

```bash title="List backups"
kubectl -n simplyblock get storagebackup
```

```plain
NAME            PHASE       SIZE        POOL             COMPLETED   AGE
my-pvc-backup   Available   1073741824  production-pool  3m          3m
```

Because the object set follows the location, a backup another cluster wrote into the same bucket appears here too.
There is no import step: the store is the inventory.

| Phase       | Description                                                   |
|-------------|---------------------------------------------------------------|
| `Pending`   | The backup is known and nothing has been copied yet.          |
| `Creating`  | The copy is being written.                                    |
| `Available` | The copy is complete and can be restored.                     |
| `Failed`    | The copy did not complete. `status.message` holds the reason. |

`Available` is the terminal success rather than `Succeeded`, because a backup is not an operation: what matters
afterward is that the copy can be restored, not that the copying finished.

#### Status Fields

The status is in two groups. `status.backup` describes the copy, and `status.source` what the volume was when the
copy was taken.

| Group           | Fields                                                                                                                                                               |
|-----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `status.backup` | `backupID`, `s3ID`, `size`, `previousBackupID`, `startedAt`, `completedAt`                                                                                           |
| `status.source` | `claimName`, `claimNamespace`, `persistentVolumeName`, `poolName`, `poolUUID`, `lvolID`, `lvolName`, `fsType`, `snapshotID`, `snapshotName`, `nodeID`, `clusterUUID` |

`status.source.fsType` is the source volume's filesystem type, so a later restore mounts the restored volume with
the same filesystem regardless of the target StorageClass defaults. `status.backup.previousBackupID` is what makes
the incremental chain visible.

```bash title="Inspect a backup"
kubectl -n simplyblock get storagebackup my-pvc-backup -o jsonpath='{.status}' | jq .
```

!!! note
    The first backup of a volume may take longer to complete as there is no prior incremental state.

### StorageBackupOps

A `StorageBackupOps` performs one operation against a `StorageBackup`, which today means a restore. It runs to a
terminal phase and stays afterward as the audit record of what was restored, into which pool, and how it ended.

```yaml title="Restore a backup into a new PVC"
kubectl apply -f - <<'EOF'
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageBackupOps
metadata:
  name: my-restore
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  backupRef: my-pvc-backup
  action: Restore
  restore:
    claimName: restored-pvc
    targetPool: production-pool
EOF
```

#### Spec Fields

| Field                      | Type   | Description                                                  |
|----------------------------|--------|--------------------------------------------------------------|
| `clusterRef`               | string | Name of the target StorageCluster. **Required**.             |
| `backupRef`                | string | Name of the `StorageBackup` to restore. **Required**.        |
| `action`                   | string | `Restore`. **Required**.                                     |
| `restore.claimName`        | string | Name of the `PersistentVolumeClaim` to create. **Required**. |
| `restore.targetPool`       | string | Pool to restore into. **Required**.                          |
| `restore.claimLabels`      | map    | Labels copied onto the new claim.                            |
| `restore.claimAnnotations` | map    | Annotations copied onto the new claim.                       |

#### Steps

| Step             | Description                                             |
|------------------|---------------------------------------------------------|
| `Validating`     | The references are resolved and the restore is checked. |
| `Restoring`      | The backend copies the data back.                       |
| `AwaitingVolume` | The restored logical volume is awaited.                 |
| `Binding`        | The `PersistentVolumeClaim` is created and bound.       |

```bash title="Follow a restore"
kubectl get storagebackupops my-restore -n simplyblock \
    -o jsonpath='{.status.phase}{"\t"}{.status.step.state}{"\n"}' -w
```

The claim a restore produces is not owned by the operation and outlives it: deleting the `StorageBackupOps` does
not delete the restored volume, and a failed restore leaves no claim behind because the claim is created only at
`Binding`. `status.persistentVolumeName` names the volume that was created.

Two restores of one backup do not run together. The backup carries `status.activeOpsRef`, and a second operation
queues behind the first.

### StorageBackupPolicy

A `StorageBackupPolicy` schedules and retains the backups of the claims it selects. It is the only thing that
decides a backup is taken; the copies themselves belong to the control plane and are pruned by its retention.

```yaml title="Create a backup policy"
kubectl apply -f - <<'EOF'
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageBackupPolicy
metadata:
  name: my-policy
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  claimSelector:
    matchLabels:
      backup: hourly
  schedule: "15m,4 60m,11 24h,7"
  maxVersions: 10
  maxAge: "7d"
EOF
```

#### Spec Fields

| Field           | Type           | Description                                                       |
|-----------------|----------------|-------------------------------------------------------------------|
| `clusterRef`    | string         | Name of the target StorageCluster. **Required**.                  |
| `claimSelector` | label selector | Which claims the policy covers.                                   |
| `schedule`      | string         | Tiered backup schedule as space-separated `interval,count` pairs. |
| `maxVersions`   | int            | Maximum number of completed backup versions to retain.            |
| `maxAge`        | string         | Maximum backup age (e.g., `7d`, `12h`, `30m`).                    |

The schedule format is a space-separated list of `interval,count` pairs with strictly increasing intervals. For
example, `15m,4 60m,11 24h,7` means: take a backup every 15 minutes (keep the 4 most recent), every 60 minutes
(keep 11), and every 24 hours (keep 7).

Retention does not delete data: when `maxVersions` or `maxAge` is exceeded, the oldest backup is merged into the
next one, so the number of restore points shrinks while the backup chain stays complete.

!!! important
    `spec.schedule` is immutable. The control plane offers no endpoint that applies a changed schedule, so a
    mutable field would leave the declaration and the backups actually being taken permanently disagreeing.
    Changing a schedule means replacing the policy.

#### Selecting the Claims

A policy covers claims by label rather than being attached to them one at a time. Labeling a claim brings it into
the policy, and removing the label takes it out.

```bash title="Bring a claim into a policy"
kubectl label pvc my-pvc -n simplyblock backup=hourly
```

```bash title="Take a claim out of a policy"
kubectl label pvc my-pvc -n simplyblock backup-
```

The claims a policy currently covers are published in its status, and existing backups are not deleted when a claim
leaves.

```bash title="Read the claims a policy covers"
kubectl get storagebackuppolicy my-policy -n simplyblock \
    -o jsonpath='{.status.attachedClaims}' | jq .
```

| Phase     | Description                                             |
|-----------|---------------------------------------------------------|
| `Pending` | The policy is being registered with the control plane.  |
| `Active`  | The policy is registered and taking backups.            |
| `Failed`  | Registration failed. `status.message` holds the reason. |

`status.lastBackupAt` is when the policy last produced a backup.

### Restoring a Backup Another Cluster Wrote

There is no import step. Point both clusters at the same bucket, with a different `prefix` for each, and every
backup in the bucket is discovered by whichever cluster walks it. A `StorageBackup` that another cluster wrote is
an ordinary object here and is restored with a `StorageBackupOps` like any other.

The target cluster's storage nodes have to be able to reach the bucket, and `status.source.clusterUUID` on the
backup names the cluster that wrote it.

## Control-Plane Backups

The CRDs on this page protect volume data. The control-plane database itself is backed up separately, see
[FoundationDB Backup and Restore](foundationdb-backup.md).
