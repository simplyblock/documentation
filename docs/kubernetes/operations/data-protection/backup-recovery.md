---
title: "Backup and Recovery"
description: "Policy-driven and on-demand backups of simplyblock volumes to S3-compatible object storage, listed as StorageBackup objects and restored with StorageBackupOps."
weight: 10510
---

Simplyblock backs up volumes to Amazon S3 or S3-compatible object storage as chains of incremental snapshots. On
Kubernetes, the `StorageCluster` names the S3 location, a `StorageBackupPolicy` selects the claims to back up and sets
the schedule and the retention, and the control plane takes the copies. A single backup of one claim can also be
requested at any time by creating a `StorageBackup`, the way a `VolumeSnapshot` is created. Every copy the control
plane holds appears as a `StorageBackup` object, and a copy is restored into a new claim with a `StorageBackupOps`
operation.

| Kind                  | Short name | Written by            | Purpose                                                                                 |
|-----------------------|------------|-----------------------|-----------------------------------------------------------------------------------------|
| `StorageCluster`      | `stc`      | Administrator         | `spec.backup` names the S3 location and its credentials.                                |
| `StorageBackupPolicy` | `sbp`      | Administrator         | Schedule and retention for the claims its selector matches, or for a consistency group. |
| `StorageBackup`       | `sb`       | Operator, or a user   | A record of one backup the control plane holds, or a user's request for one backup.     |
| `StorageGroupBackup`  | `sgb`      | Administrator or user | A request for one backup of a whole consistency group.                                  |
| `StorageBackupOps`    | `sbops`    | Administrator or user | Restores one backup, or one group backup, into new claims.                              |

All five use the API version `storage.simplyblock.io/v1alpha2`. The policy and the backup records live in the namespace
of the `StorageCluster`. A backup request lives in the namespace of its claim, and so does a restore.

!!! info "Backups and disaster recovery"
    The backup bucket is part of the storage cluster and is configured when the cluster is deployed. Simplyblock
    Disaster Recovery does not use it: the backup method types of a protection plan back volumes up with the same
    mechanism into the DR metadata store of the site. See
    [Backup and Restore](../../../disaster-recovery/operations/backup-restore.md).

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

For `credentials.source: Secret` (the default), the S3 access key is stored in a Secret in the namespace of the
`StorageCluster`, under the keys `access_key_id` and `secret_access_key`:

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

A deployment on Amazon EKS can skip this Secret entirely and authenticate through the cluster's own IAM role instead.
See [Keyless S3 Backup Credentials on Amazon EKS](../../installation/eks.md#keyless-s3-backup-credentials-irsa) below.

### Backup Store of the StorageCluster

The backup store is set in `StorageCluster.spec.backup`, and it has to be set when the cluster is created. The operator
passes the store to the control plane only in the request that creates the cluster, and the control plane offers no
call to change it afterward. The field can still be edited, but a store added or changed later is not applied. Backups
of a cluster created without a store fail with `Cluster <UUID> has no backup configuration`.

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
    region: us-east-1
    credentials:
      source: Secret
      secretRef:
        name: production-backup
```

| Field                                    | Required                                                              | Description                                                                                                                                                                                                                                                                                                                                                     |
|------------------------------------------|-----------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `endpoint`                               | yes                                                                   | S3 endpoint URL, for example, `https://s3.example.com`. Loopback and link-local addresses are refused.                                                                                                                                                                                                                                                          |
| `bucket`                                 | yes                                                                   | Bucket the backups are written to and read from.                                                                                                                                                                                                                                                                                                                |
| `region`                                 | no                                                                    | Region of the bucket, for endpoints that do not imply one.                                                                                                                                                                                                                                                                                                      |
| `credentials.source`                     | yes, unless the deprecated `credentialsSecretRef` is set instead      | `Secret` (the default) reads a static key from `secretRef`. `ProviderChain` takes no static key at all and authenticates through the AWS SDK's default credential provider chain, which on Amazon EKS resolves through the cluster's IAM role. See [Keyless S3 Backup Credentials on Amazon EKS](../../installation/eks.md#keyless-s3-backup-credentials-irsa). |
| `credentials.secretRef.name`             | required with `source: Secret`, rejected with `source: ProviderChain` | Secret in the same namespace with the keys `access_key_id` and `secret_access_key`.                                                                                                                                                                                                                                                                             |
| `credentialsSecretRef.name` (deprecated) | yes, unless `credentials` is set instead                              | The pre-`credentials` way to name the same Secret. Still accepted, but set `credentials` instead: this spelling cannot express `ProviderChain`.                                                                                                                                                                                                                 |

The store has no key prefix, and the object keys inside the bucket are fixed (see
[Contents of the Bucket](#contents-of-the-bucket)).

The `StorageBackup` objects list the copies that the control plane of this cluster took or imported. Copies that
another cluster wrote into the same bucket are listed only after they are imported into this cluster's control plane
with `{{ cliname }} backup import --bucket`, run in the `simplyblock-admin-control` pod (see
[Using the CLI](../monitoring/cluster-health.md#using-the-cli)).

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
  schedule: "24h,7"
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

The schedule `24h,7` takes a backup every 24 hours and keeps the 7 most recent. The intervals have to be strictly
increasing. Backups are taken at the shortest interval of the schedule only. A policy without a schedule takes no
backups and only applies `maxVersions` and `maxAge`.

Each tier limits the backups in an age band. The band of a tier starts at the interval of the tier before it (zero for
the first tier) and ends at the interval of the tier after it (no end for the last tier), so neighboring bands overlap.
When a band holds more backups than its count, its oldest backup is merged into the next newer one. The backups that
remain are therefore always the newest ones, spaced at the shortest interval, and a tiered schedule does not keep
hourly or daily backups further back:

| Schedule             | Backups kept                 |
|----------------------|------------------------------|
| `24h,7`              | 7 daily backups              |
| `60m,24`             | 24 hourly backups            |
| `60m,24 24h,7`       | 8 hourly backups             |
| `15m,4 60m,11 24h,7` | 11 backups, 15 minutes apart |

!!! note
    `schedule`, `maxVersions`, and `maxAge` cannot be changed on an existing policy. A different schedule or retention
    requires a new policy, and the old one is deleted afterward.

### How Retention Merges

Retention is enforced by the control plane, which evaluates every attached volume once a minute. The oldest backup is
merged into the next newer one, so the number of restore points shrinks while the backup chain stays complete. A pass
merges at most one backup per volume under the schedule and one under `maxVersions` and `maxAge`, so a volume far over
its limits is brought down over several minutes. A merge needs two completed backups, which is why `maxAge` never
removes the last one.

Backups taken by a [backup request](#requesting-a-backup) count toward the limits like scheduled ones, and the next
scheduled backup is due one interval after the newest backup of either kind. A request whose backup is merged away
turns `Failed` with the message `The backup left the store`.

Only volumes that exist and are attached to a policy are evaluated. The backups of a detached claim, of a claim whose
policy was deleted, and of a deleted volume are never merged or removed.

A merge removes the `StorageBackup` of the merged backup and records a `BackupGone` event on the `StorageCluster`.
`status.backup.previousBackupID` of the surviving backup then names the predecessor of the merged one.

A policy that sets none of `schedule`, `maxVersions`, and `maxAge` is refused by the control plane.

### Selecting the Claims

A claim is covered by a policy when its labels match the policy's `claimSelector`. Labeling a claim attaches it, and
removing the label detaches it. Existing backups are kept in both cases.

```bash title="Attaching a claim to the nightly policy"
kubectl label pvc my-pvc -n simplyblock backup=nightly
```

```bash title="Detaching a claim from the policy"
kubectl label pvc my-pvc -n simplyblock backup-
```

A policy only selects claims in its own namespace, which is the namespace of the `StorageCluster`. The backups it takes
are recorded in that namespace too. An absent selector is reported with a `SelectorEmpty` event on the policy.

The attached claims are listed in `status.attachedClaims`, and `status.lastBackupAt` holds the time of the most recent
backup.

```bash title="Checking the backup policies"
kubectl get storagebackuppolicy -n simplyblock
```

```plain title="Example output of the backup policy listing"
NAME      CLUSTER      PHASE    SCHEDULE   CLAIMS   LASTBACKUP   AGE
nightly   production   Active   24h,7      3        5h           2d
```

## Requesting a Backup

A single backup of one claim is requested by creating a `StorageBackup` with `spec.source.claimName`, the way a
`VolumeSnapshot` is created. No policy is involved, so a claim can be backed up before an upgrade without giving it a
schedule.

```yaml title="Example of a backup request (backup-request.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageBackup
metadata:
  name: my-pvc-before-upgrade
  namespace: app
spec:
  source:
    claimName: my-pvc
```

```bash title="Requesting the backup"
kubectl apply -f backup-request.yaml
```

Create the request in the namespace of the claim. The claim must be bound to a simplyblock volume, and the cluster
that provisioned the volume must have `spec.backup` set. The operator finds the cluster from the volume, so a request
has no `clusterRef`.

| Field              | Description                                                                         |
|--------------------|-------------------------------------------------------------------------------------|
| `source.claimName` | Name of the claim to back up, in the namespace of the request. Required, immutable. |

A `StorageBackup` sets exactly one of `spec.source` (a request) and `spec.clusterRef` (a record written by the
operator). The API server rejects an object that sets both or neither.

The operator makes a single call to the control plane, which takes a snapshot of the volume named
`_backup_<volume>_<time>` and backs it up. The snapshot stays on the volume after the backup completes (see
[Backup Snapshots](#backup-snapshots)). `status.backup.backupID` is filled in and `status.phase` is set to `Creating`
once the control plane returns the ID. Until then, `status.phase` stays empty.

```bash title="Watching the request"
kubectl get storagebackup my-pvc-before-upgrade -n app -w
```

| Phase       | Meaning                                                                                                |
|-------------|--------------------------------------------------------------------------------------------------------|
| `Pending`   | Waiting for something that may still appear. See the list below.                                       |
| `Creating`  | The control plane is writing the copy.                                                                 |
| `Available` | The copy is complete and can be restored.                                                              |
| `Failed`    | The claim is not on a simplyblock volume, the control plane refused the request, or the backup failed. |

A request stays `Pending` while

- the claim does not exist or is not bound yet,
- no `StorageCluster` reports the cluster that provisioned the volume,
- that cluster has no `spec.backup`, or
- the operator has not yet received the current snapshot and backup state of the cluster from the control plane.

`status.message` gives the reason, and a `Pending` request emits a `BackupRequestBlocked` event. A request that is
`Available` or `Failed` is not retried. To take another backup, create another request.

The request is the only object for its copy. Deleting the request leaves the copy in the store, and the operator then
records the copy as a regular `StorageBackup` in the namespace of the cluster. If the store stops reporting the copy,
the request is marked `Failed` and is not deleted.

A request records the pool by its UUID only, so the `Pool` column of `kubectl get sb -o wide` stays empty for it.
Requests live in the namespaces of their claims, and the backups of every namespace are listed with
`kubectl get sb -A`.

!!! note
    Creating and deleting a request needs the `create` and `delete` verbs on `storagebackups` in the claim's namespace.
    A record is still refused for every identity but the operator.

## Listing Backups

Every backup the control plane holds is mirrored as one `StorageBackup` object, named after its backup ID. Backups
taken by a policy are always recorded in the namespace of the `StorageCluster`, whatever namespace the claim is in. A
record is an observation, and `spec.clusterRef` names the cluster whose store holds the copy. A webhook refuses to
create or delete a record for anyone but the operator, and deleting a record never deletes the copy in the bucket.

The webhook does not block backup requests. An object with `spec.source` is a request, not a record, and a user can
create and delete it. See [Requesting a Backup](#requesting-a-backup).

```bash title="Listing the backups of a cluster"
kubectl get storagebackup -n simplyblock
```

```plain title="Example output of the backup listing"
NAME                                   CLAIM    PHASE       SIZE         COMPLETED   AGE
7fab02f8-03f6-4e76-a9ac-78b63b1ce8ef   my-pvc   Available   1073741824   3m          3m
```

`status.phase` is one of `Pending`, `Creating`, `Available`, or `Failed`. The backup ID is in
`status.backup.backupID`. `status.source` records where the copy came from (the claim, the PersistentVolume, the
pool, the logical volume, the snapshot, and the filesystem type), and `status.backup` records the copy itself (its
ID, size, the previous backup of the chain, and the timestamps). The objects carry the labels
`storage.simplyblock.io/cluster` and `storage.simplyblock.io/claim`, which allows the backups of one claim to be
selected. The member backups of a [consistency group](#consistency-groups) also carry
`storage.simplyblock.io/group-backup-id`, and `storage.simplyblock.io/group-backup` when a `StorageGroupBackup` took
them.

```bash title="Listing the backups of one claim"
kubectl get sb -n simplyblock -l storage.simplyblock.io/claim=my-pvc
```

!!! note
    The first backup of a claim may take longer to complete, as there is no prior incremental state.

### Backup Snapshots

Every backup is taken from a snapshot of its own: `auto_<volume>_<time>` for a scheduled backup and
`_backup_<volume>_<time>` for a requested one. These snapshots are not `VolumeSnapshot` objects, and nothing deletes
them, not even a merge that removes their backup.

!!! warning "Backups stop at 40 snapshots"
    Before a backup is taken, the control plane counts the snapshots in the line of the volume, including the snapshot
    the volume was cloned from and the ancestors of that snapshot. Once that line holds 40 snapshots, no further backup
    of the volume is taken, because 40 is the longest chain the storage plane backs up and restores. A scheduled backup
    is then skipped with only a warning in the control-plane log. A request turns `Failed` with a message that the
    chain accepts at most 40 backups. At a schedule of `15m`, a volume without other snapshots reaches this limit after
    ten hours.

Backup snapshots that are no longer needed are deleted with the CLI in the `simplyblock-admin-control` pod (see
[Using the CLI](../monitoring/cluster-health.md#using-the-cli)). The ID of the logical volume is in
`status.source.lvolID` of its `StorageBackup` objects. Deleting a snapshot leaves its backup in the store, and a
snapshot whose backup is still being written cannot be deleted.

```bash title="Listing the snapshots of a logical volume"
kubectl -n simplyblock exec -it deploy/simplyblock-admin-control -- \
    {{ cliname }} snapshot list --lvol-id <LVOL_ID>
```

```bash title="Deleting a backup snapshot"
kubectl -n simplyblock exec -it deploy/simplyblock-admin-control -- \
    {{ cliname }} snapshot delete <SNAPSHOT_ID>
```

A restore is refused for a chain of more than 40 backups as well, so a policy has to keep at most 40 backups per claim.

### Contents of the Bucket

A backup uploads the clusters its snapshot holds, which are the data written since the snapshot before it. The first
backup of a volume is therefore a full backup, and every later one is incremental. Snapshots of the volume that have
no backup yet are uploaded first, each as a backup of its own, so that the chain has no gap. A restore reads the chain
newest first and takes each cluster from the newest backup that holds it.

| Key                             | Content                                                                                    |
|---------------------------------|--------------------------------------------------------------------------------------------|
| `<s3_id>/0/<n>`                 | One data cluster of a backup, 2 to 8 MiB depending on the erasure coding scheme.           |
| `<s3_id>/1/0`                   | The root record of a backup, written by the storage plane.                                 |
| `<s3_id>/1/<n>`                 | The extent map of a backup.                                                                |
| `manifests/<backup_id>.json`    | The manifest of a backup: its volume, size, encoding, and the backup it is incremental on. |
| `groups/<group_backup_id>.json` | The manifest of a group backup, written after the manifests of all its members.            |

`<s3_id>` is a number the control plane assigns to each backup, and `status.backup.s3ID` of the `StorageBackup` holds
it.

!!! warning
    An expiration lifecycle rule must not be set on the bucket. A rule that deletes objects by age removes the data of
    old backups that newer incremental backups still depend on, and those backups can then no longer be restored.

## Restoring a Backup

A backup is restored into a new claim by a `StorageBackupOps` operation with `action: Restore`. The backup can be a
record or a request. The claim named in `restore.claimName` must not exist yet, because a restore creates a claim and
never replaces the data of an existing one. The target pool is required, since an imported backup may come from a
pool this cluster does not have.

```yaml title="Example of a restore into a new claim (restore.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageBackupOps
metadata:
  name: restore-my-pvc
  namespace: simplyblock
spec:
  clusterRef:
    name: production
  backupRef:
    name: 7fab02f8-03f6-4e76-a9ac-78b63b1ce8ef
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

| Field                      | Description                                                                                                        |
|----------------------------|--------------------------------------------------------------------------------------------------------------------|
| `clusterRef.name`          | Name of the `StorageCluster`. Required.                                                                            |
| `clusterRef.namespace`     | Namespace of the `StorageCluster`. Defaults to the namespace of the operation.                                     |
| `backupRef.name`           | Name of the `StorageBackup` to restore, a record or a request.                                                     |
| `backupRef.namespace`      | Namespace of the `StorageBackup`. Defaults to the namespace of the operation.                                      |
| `groupBackupRef.name`      | Name of a `StorageGroupBackup` whose group backup is restored. See [Consistency Groups](#consistency-groups).      |
| `groupBackupRef.namespace` | Namespace of the `StorageGroupBackup`. Defaults to the namespace of the operation.                                 |
| `groupBackupID`            | ID of a group backup no `StorageGroupBackup` stands for, such as one a policy took.                                |
| `action`                   | `Restore`, the only action. Required.                                                                              |
| `abort`                    | Stops the restore, as long as no logical volume has been created yet.                                              |
| `restore.claimName`        | Name of the claim to create. Required, and must not exist.                                                         |
| `restore.targetPool`       | `StoragePool` to restore into, read from the namespace of the cluster. Required.                                   |
| `restore.claimLabels`      | Labels applied to the created claim, for example, to attach it to a backup policy.                                 |
| `restore.claimAnnotations` | Annotations applied to the created claim.                                                                          |
| `restore.volumeMode`       | `Filesystem` or `Block`. Defaults to the volume mode recorded in the backup, and to `Filesystem` without a record. |

Exactly one of `backupRef`, `groupBackupRef`, and `groupBackupID` is set. `clusterRef`, `backupRef`, and
`groupBackupRef` are objects. The API server rejects a string such as `backupRef: 7fab02f8-...`.

!!! warning
    A backup of a `Block` volume that is restored with `volumeMode: Filesystem` is formatted on its first mount, which
    overwrites the restored data.

### Restoring Across Namespaces

The claim is always created in the namespace of the operation. The backup and the cluster can be in other namespaces,
so a team can restore into its own namespace by creating the operation there and naming them with their namespaces:

```yaml title="Example of a restore from the namespace of the cluster into the namespace app"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageBackupOps
metadata:
  name: restore-my-pvc
  namespace: app
spec:
  clusterRef:
    name: production
    namespace: simplyblock
  backupRef:
    name: 7fab02f8-03f6-4e76-a9ac-78b63b1ce8ef
    namespace: simplyblock
  action: Restore
  restore:
    claimName: restored-pvc
    targetPool: production-default
```

The operator reads these objects with its own permissions, so the webhook checks the requesting user first. Each
reference outside the namespace of the operation needs the `get` verb there:

- A `backupRef` in another namespace needs `get` on `storagebackups` in that namespace.
- A `clusterRef` in another namespace needs `get` on `storageclusters` and on `storagepools` in that namespace, since
  the target pool is read from there.

References inside the operation's namespace need no extra permission.

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
backup run one after the other, including restores created in different namespaces.

## Consistency Groups

The claims of a consistency group (see
[Snapshotting a Group of Volumes](../../usage/snapshotting.md#snapshotting-a-group-of-volumes)) are backed up as one
unit. A group backup holds one backup per member, all taken from one crash-consistent generation of the group. A
policy backs up a group when it names the group in `consistencyGroupName` instead of setting a `claimSelector`. It
takes one generation per shortest interval of its schedule, and its retention removes whole generations.

```yaml title="Example of a backup policy for a consistency group"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageBackupPolicy
metadata:
  name: db-group-daily
  namespace: simplyblock
spec:
  clusterRef: production
  consistencyGroupName: db-group
  schedule: "24h,7"
```

A single group backup is requested by a `StorageGroupBackup` in the namespace of the group's claims. Its member
backups are recorded as `StorageBackup` objects next to it, and deleting it deletes no backup. `status.phase` is
`Pending`, `Creating`, `Available`, or `Failed`.

```yaml title="Example of a group backup request"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageGroupBackup
metadata:
  name: db-group-before-upgrade
  namespace: prod
spec:
  source:
    consistencyGroupName: db-group
```

A group backup is restored by a `StorageBackupOps` that names the `StorageGroupBackup` in `groupBackupRef`. A group
backup taken by a policy has no `StorageGroupBackup` and is named by `groupBackupID` instead, whose value is the
`storage.simplyblock.io/group-backup-id` label of its member backups. One claim is created per member, named
`<claimName>-<member volume>`, and the restored claims form a new consistency group.

```yaml title="Example of a group restore"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageBackupOps
metadata:
  name: restore-db-group
  namespace: prod
spec:
  clusterRef:
    name: production
    namespace: simplyblock
  groupBackupRef:
    name: db-group-before-upgrade
  action: Restore
  restore:
    claimName: restored-db
    targetPool: production-default
```

A crash-consistent copy of a group that stays inside the cluster is a `VolumeGroupSnapshot`, restored by a
`VolumeGroupSnapshotOps` operation (see
[Restoring a Volume Group Snapshot](../../usage/snapshotting.md#restoring-a-volume-group-snapshot)).

## Control-Plane Backups

The kinds on this page protect volume data. The control-plane database itself is backed up separately, see
[FoundationDB Backup and Restore](foundationdb-backup.md). For application-level protection across sites, see
[Disaster Recovery](../../../disaster-recovery/index.md).
