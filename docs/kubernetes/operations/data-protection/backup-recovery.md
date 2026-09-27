---
title: "Backup and Recovery"
description: "Policy-driven backups of simplyblock volumes to Amazon S3 or S3-compatible object storage, observed as StorageBackup objects and restored with StorageBackupOps."
weight: 10510
---

Simplyblock backs up volumes to Amazon S3 or S3-compatible object storage as chains of incremental snapshots. On
Kubernetes, backups are declared, not requested: the `StorageCluster` names the S3 location, a
`StorageBackupPolicy` selects the claims to back up and sets the schedule and the retention, and the control plane
takes the copies. Every copy found in the store appears as a `StorageBackup` object, and a copy is restored into a new
claim with a `StorageBackupOps` operation.

| Kind                  | Short name | Written by    | Purpose                                                         |
|-----------------------|------------|---------------|-----------------------------------------------------------------|
| `StorageCluster`      | `stc`      | Administrator | `spec.backup` names the S3 location and its credentials.        |
| `StorageBackupPolicy` | `sbp`      | Administrator | Schedule and retention for the claims its selector matches.     |
| `StorageBackup`       | `sb`       | Operator only | One backup found in the store. Observed, never created by hand. |
| `StorageBackupOps`    | `sbops`    | Administrator | Restores one backup into a new claim.                           |

All four live in the namespace of the `StorageCluster` and use the API version `storage.simplyblock.io/v1alpha2`.

## Prerequisites

### S3-Compatible Object Storage

Backups require an S3-compatible object storage endpoint and a bucket. For local testing, a MinIO instance can be
deployed:

```bash title="Deploying a local MinIO instance for testing"
kubectl create ns minio

kubectl -n minio create deployment minio \
  --image=minio/minio \
  -- /bin/sh -c "minio server /data --console-address :9001"

kubectl -n minio expose deploy/minio --port 9000

kubectl -n minio set env deploy/minio \
  MINIO_ROOT_USER=minioadmin \
  MINIO_ROOT_PASSWORD=minioadmin123
```

### Backup Credentials Secret

The S3 credentials are stored in a Secret in the namespace of the `StorageCluster`, under the keys `access_key_id` and
`secret_access_key`:

```yaml title="Example of a backup credentials Secret (backup-credentials.yaml)"
apiVersion: v1
kind: Secret
metadata:
  name: production-backup
  namespace: simplyblock
type: Opaque
stringData:
  access_key_id: <ACCESS_KEY>
  secret_access_key: <SECRET_KEY>
```

### Backup Store of the StorageCluster

The backup store is set in `StorageCluster.spec.backup`. The block is mutable, so a cluster created without a store can
be given one later.

```yaml title="Example of the backup store of a StorageCluster"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageCluster
metadata:
  name: production
  namespace: simplyblock
spec:
  # ... other fields ...
  backup:
    endpoint: http://minio.minio.svc.cluster.local:9000
    bucket: simplyblock-backups
    prefix: production/
    credentialsSecretRef:
      name: production-backup
```

| Field                       | Required | Description                                                                                            |
|-----------------------------|----------|--------------------------------------------------------------------------------------------------------|
| `endpoint`                  | yes      | S3 endpoint URL, for example, `https://s3.example.com`. Loopback and link-local addresses are refused. |
| `bucket`                    | yes      | Bucket the backups are written to and read from.                                                       |
| `prefix`                    | no       | Key prefix inside the bucket, so that several clusters can share a bucket.                             |
| `region`                    | no       | Region of the bucket, for endpoints that do not imply one.                                             |
| `credentialsSecretRef.name` | yes      | Secret in the same namespace with the keys `access_key_id` and `secret_access_key`.                    |

The store is both the target copies are written to and the inventory the operator reads. Setting it makes every backup
already under that bucket and prefix visible as a `StorageBackup` object, including backups written by another
cluster that shares the bucket and prefix.

## Backup Policies

A `StorageBackupPolicy` defines which claims are backed up, how often, and how long the copies are kept. The control
plane runs the policy, so no Kubernetes CronJob or trigger is involved.

```yaml title="Example of a backup policy for labeled claims (backup-policy.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageBackupPolicy
metadata:
  name: nightly
  namespace: simplyblock
spec:
  clusterRef: production
  claimSelector:
    matchLabels:
      backup: nightly
  schedule: "15m,4 60m,11 24h,7"
  maxVersions: 22
  maxAge: 30d
```

```bash title="Creating the backup policy"
kubectl apply -f backup-policy.yaml
```

| Field           | Mutability | Description                                                                                                 |
|-----------------|------------|-------------------------------------------------------------------------------------------------------------|
| `clusterRef`    | immutable  | Name of the `StorageCluster` in the same namespace. Required.                                               |
| `claimSelector` | mutable    | Label selector for the claims to back up. An absent selector selects nothing, and `{}` selects every claim. |
| `schedule`      | immutable  | Tiered schedule as space-separated `interval,count` pairs, with units `m`, `h`, `d`, and `w`.               |
| `maxVersions`   | immutable  | Number of backups kept per claim. `0` means no limit by count.                                              |
| `maxAge`        | immutable  | Age after which a backup is no longer kept, for example, `30d` or `720h`. Empty means no limit by age.      |

The schedule `15m,4 60m,11 24h,7` takes a backup every 15 minutes (keeping the 4 most recent), every 60 minutes (keeping
11), and every 24 hours (keeping 7). The intervals have to be strictly increasing. Retention is enforced by the control
plane: the oldest backup is merged into the next one, so the number of restore points shrinks while the backup chain
stays complete.

!!! note
    `schedule`, `maxVersions`, and `maxAge` cannot be changed on an existing policy. A different schedule or retention
    requires a new policy, and the old one is deleted afterward.

### Selecting the Claims

A claim is covered by a policy when its labels match the policy's `claimSelector`. Labeling a claim attaches it, and
removing the label detaches it. Existing backups are kept in both cases.

```bash title="Attaching a claim to the nightly policy"
kubectl label pvc my-pvc -n simplyblock backup=nightly
```

```bash title="Detaching a claim from the policy"
kubectl label pvc my-pvc -n simplyblock backup-
```

A policy only selects claims in its own namespace, which is the namespace of the `StorageCluster`. An absent selector
is reported with a `SelectorEmpty` event on the policy.

The attached claims are listed in `status.attachedClaims`, and `status.lastBackupAt` holds the time of the most recent
backup.

```bash title="Checking the backup policies"
kubectl get storagebackuppolicy -n simplyblock
```

```plain title="Example output of the backup policy listing"
NAME      CLUSTER      PHASE    SCHEDULE             CLAIMS   LASTBACKUP   AGE
nightly   production   Active   15m,4 60m,11 24h,7   3        4m           2d
```

## Listing Backups

Every backup in the store is mirrored as one `StorageBackup` object, named after its backup ID. The objects are
observations: a validating webhook refuses a `StorageBackup` that is created or deleted by anybody but the operator,
and deleting the object would never delete the copy in the bucket.

```bash title="Listing the backups of a cluster"
kubectl get storagebackup -n simplyblock
```

```plain title="Example output of the backup listing"
NAME                                   CLAIM    PHASE       SIZE         COMPLETED   AGE
7fab02f8-03f6-4e76-a9ac-78b63b1ce8ef   my-pvc   Available   1073741824   3m          3m
```

`status.phase` is one of `Pending`, `Creating`, `Available`, or `Failed`. `status.source` records where the copy came
from (the claim, the PersistentVolume, the pool, the logical volume, the snapshot, and the filesystem type), and
`status.backup` records the copy itself (its ID, size, the previous backup of the chain, and the timestamps). The
objects carry the labels `storage.simplyblock.io/cluster`, `storage.simplyblock.io/claim`, and
`storage.simplyblock.io/backup-policy`, which allows the backups of one claim to be selected:

```bash title="Listing the backups of one claim"
kubectl get sb -n simplyblock -l storage.simplyblock.io/claim=my-pvc
```

!!! note
    The first backup of a claim may take longer to complete, as there is no prior incremental state.

## Restoring a Backup

A backup is restored into a new claim by a `StorageBackupOps` operation with `action: Restore`. The claim named in
`restore.claimName` must not exist yet, because a restore creates a claim and never replaces the data of an existing
one. The target pool is required, since a backup found in a shared store may come from a pool this cluster does not
have.

```yaml title="Example of a restore into a new claim (restore.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageBackupOps
metadata:
  name: restore-my-pvc
  namespace: simplyblock
spec:
  clusterRef: production
  backupRef: 7fab02f8-03f6-4e76-a9ac-78b63b1ce8ef
  action: Restore
  restore:
    claimName: restored-pvc
    targetPool: production-default
    claimLabels:
      backup: nightly
```

```bash title="Starting the restore"
kubectl apply -f restore.yaml
```

| Field                      | Description                                                                        |
|----------------------------|------------------------------------------------------------------------------------|
| `clusterRef`               | Name of the `StorageCluster` in the same namespace. Required.                      |
| `backupRef`                | Name of the `StorageBackup` to restore, in the same namespace. Required.           |
| `action`                   | `Restore`, the only action. Required.                                              |
| `abort`                    | Stops the restore, as long as no logical volume has been created yet.              |
| `restore.claimName`        | Name of the claim to create. Required, and must not exist.                         |
| `restore.targetPool`       | `StoragePool` to restore into. Required.                                           |
| `restore.claimLabels`      | Labels applied to the created claim, for example, to attach it to a backup policy. |
| `restore.claimAnnotations` | Annotations applied to the created claim.                                          |

The restored claim is created in the namespace of the operation, with access mode `ReadWriteOnce` and the size of the
backup. Its StorageClass is the default class of the target pool, or otherwise the first StorageClass assigned to the
pool (see [Storage Class](../../usage/storage-class.md)). The volume is mounted with the filesystem type
recorded in the backup. The claim carries the label `storage.simplyblock.io/restored-by` and is not owned by the
operation, so deleting the `StorageBackupOps` leaves the restored data in place.

```bash title="Watching the restore"
kubectl get storagebackupops -n simplyblock -w
```

```plain title="Example output of the restore listing"
NAME             BACKUP                                 ACTION    PHASE       STEP   AGE
restore-my-pvc   7fab02f8-03f6-4e76-a9ac-78b63b1ce8ef   Restore   Succeeded          79s
```

While the phase is `Running`, `status.step.state` moves through `Validating`, `Restoring`, `AwaitingVolume`, and
`Binding`. Once the phase is `Succeeded`, the claim is bound and can be attached to a pod. Two restores of the same
backup run one after the other.

## Restoring a Volume Group

Backups cover single claims. A crash-consistent restore of several claims from one `VolumeGroupSnapshot` is performed
by a `VolumeGroupSnapshotOps` operation, see
[Restoring a Volume Group Snapshot](../../usage/snapshotting.md#restoring-a-volume-group-snapshot).

## Control-Plane Backups

The kinds on this page protect volume data. The control-plane database itself is backed up separately, see
[FoundationDB Backup and Restore](foundationdb-backup.md). For application-level protection across sites, see
[Disaster Recovery](../../../disaster-recovery/index.md).
