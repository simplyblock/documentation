---
title: "Backup and Restore"
description: "Back up protected applications to S3 with snapshot-s3 methods and restore them onto rebuilt sites after the loss of the hub and every site."
weight: 10470
---

Replication protects against the loss of one site: the peer site holds the data and takes over. It does not protect
against the loss of the hub and every site at once, or against a ransomware attack that reaches all clusters. For
these cases, simplyblock DR backs up protected applications to S3 with `snapshot-s3` methods. After a total loss, the
DR configuration is restored from the state bundle, and each application is restored from its latest backup onto its
rebuilt source site.

This is different from the storage-level backup of simplyblock volumes, which is described in
[Backup and Recovery](../../kubernetes/operations/data-protection/backup-recovery.md).

## snapshot-s3 Backups

A `snapshot-s3` method in a protection plan applies to every application of the plan, next to its sync or async
replication method. The method is configured in the plan (see
[Replication Types](../configuration/replication-types.md)):

```yaml title="Protection plan with a snapshot-s3 method"
apiVersion: dr.simplyblock.io/v1alpha1
kind: ProtectionPlan
metadata:
  name: metro
spec:
  # sites, storageProfile, and s3Profile omitted
  methods:
    - name: sync
      type: sync
    - name: backup-5m
      type: snapshot-s3
      snapshotS3:
        schedule: "*/5 * * * *"
        retention: 3
```

- **Schedule:** A cron expression. At every time, dr-hub asks dr-agent on the cluster each application currently runs
  on to take a backup.
- **Retention:** The number of complete backup sets kept per application. Older sets are deleted.
- **Store:** The Kubernetes objects and volume records go to the DR metadata bucket of the site, or to the S3
  profile named in `snapshotS3.s3ProfileName`, under the key prefix `simplyblock-dr/backups`. The volume data goes
  to the simplyblock backup bucket of the storage cluster.

!!! note "Prerequisite: simplyblock backups on the storage cluster"
    The volume data of a `snapshot-s3` backup is stored with the simplyblock backup feature of the storage cluster.
    Its bucket is configured when the storage cluster is deployed (`StorageCluster.spec.backup`, see
    [Backup and Recovery](../../kubernetes/operations/data-protection/backup-recovery.md)), not in DR. A storage
    cluster deployed without backups cannot be protected with a `snapshot-s3` method. See
    [S3 Buckets](../../deployment-preparation/dr-requirements.md#s3-buckets).

### Backup Sets

A backup set is named `dr-<appkey>-<yyyymmddhhmmss>-<method>`. It holds the application's Kubernetes objects and
one volume record per PVC, with the class, size, access modes, labels, and the reference to the simplyblock backup
that holds the volume data.

### Backup Status

Each ProtectedApplication reports its backups in `status.backups[]`, one entry per snapshot-s3 method:

| Field              | Content                                                                         |
|--------------------|---------------------------------------------------------------------------------|
| `method`           | The method name.                                                                |
| `running`          | The backup in progress, if any.                                                 |
| `lastSucceeded`    | The last complete backup set: name, data point, cluster, and number of volumes. |
| `lastScheduleTime` | When the last backup was started.                                               |
| `lastFailure`      | The message of the last failed backup.                                          |

```bash title="Showing the backup status"
kubectl -n ramen-ops get papp orders -o jsonpath='{.status.backups}' | jq
```

!!! info "Coming soon"
    The volume data of a backup comes from the storage backend. Integration of simplyblock volume snapshots exported
    to S3 as this backend is not available yet. Without a backend, dr-agent refuses backups instead of writing sets
    without data.

## Restoring After a Total Loss

When the hub and all sites are lost, only the S3 buckets remain: the archive bucket with the DR state, the DR
metadata buckets with the application objects, and the simplyblock backup buckets with the volume data. Recovery
follows these steps:

1. **Rebuild the clusters:** Build a new hub cluster and new site clusters with simplyblock storage. Deploy each
   storage cluster with access to the simplyblock backup bucket of the lost one, so that the volume data can be read.
   Install the hub as described in [Install the Hub](../install/hub.md).
2. **Restore the DR configuration:** Restore the state bundle with the `-fresh-sites` flag. See
   [Hub Recovery](hub-recovery.md) for the full procedure.

    ```bash title="Restoring the DR configuration for rebuilt sites"
    dr-restore restore -fresh-sites \
      -s3-endpoint s3.eu-central-1.amazonaws.com -bucket dr-archive -region eu-central-1 -prefix dr/ \
      -public-key bundle-signing.pub
    ```

    With `-fresh-sites`, every ProtectedApplication is annotated `dr.simplyblock.io/awaiting-restore=true`. While
    annotated, the application is not protected, so it is not deployed empty on the rebuilt site.

3. **Rejoin the sites:** Join the rebuilt site clusters under their old names. See [Join Sites](../install/sites.md).
4. **Restore each application:** A user with the `dr-admin` role creates one RestoreAction per application.

```yaml title="RestoreAction"
apiVersion: dr.simplyblock.io/v1alpha1
kind: RestoreAction
metadata:
  generateName: orders-restore-
  namespace: ramen-ops
spec:
  applicationRef:
    name: orders
  # backup: dr-orders-20260924101500-backup-5m   # optional, the newest complete set when empty
  timeout: 30m
```

### RestoreAction Phases

| Phase          | What happens                                                                                                                                                                                                                                                                                                 |
|----------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Pending`      | Checks that the application is awaiting restore and that its plan has a snapshot-s3 method.                                                                                                                                                                                                                  |
| `Restoring`    | The named or newest complete backup set is restored on the source site: the namespaces and one PVC per volume record are recreated with the recorded data, the objects are restored in tier order, and the pods become ready. The old protection data of the application is then removed from the S3 stores. |
| `Reprotecting` | The annotation is removed, and the application is protected again. The phase ends when the application is reported deployed and protected.                                                                                                                                                                   |
| `Completed`    | The application runs on its source site and is protected again.                                                                                                                                                                                                                                              |
| `Failed`       | A step failed. See `status.steps` and `status.message`.                                                                                                                                                                                                                                                      |

```bash title="Listing restore actions"
kubectl -n ramen-ops get rsa
```

`status.dataLoss` is the time between the backup's data point and the start of the restore, an upper bound of the data
lost.

## Restrictions

- **Source site only:** An application is restored onto its source site. Restoring onto another site is not
  supported.
- **Whole applications:** An application is restored as a whole. Partial restores are not supported.
- **No failback:** A RestoreAction is not a failover. An application that is still protected is refused. Use a
  [failover](unplanned-failover.md) or [relocation](relocate-restart.md) instead.
- **Hand-written Recipes:** An application with a hand-written Recipe is restored as a single group, because the
  Recipe was on the lost site.
