---
title: "Backup and Restore"
description: "Back up protected applications to S3 with the backup method types and restore them onto rebuilt sites with a RestoreAction after the loss of the hub and every site."
source: "https://docs.simplyblock.io/latest/disaster-recovery/operations/backup-restore/"
---

# Backup and Restore

Replication protects against the loss of one site: the peer site holds the data and takes over. It does not protect
against the loss of the hub and every site at once, or against a ransomware attack that reaches all clusters. For
these cases, a protection plan uses one of the backup method types (`s3-backup`, `sync-s3-backup`, or
`async-s3-backup`): the storage backs every primary volume up to S3. After a total loss, the DR configuration is
restored from the state bundle, and each application is restored onto its rebuilt source site with a `RestoreAction`.

The volume backups are the storage cluster's own backups, described in
[Backup and Recovery](../../kubernetes/operations/data-protection/backup-recovery.md). DR configures their interval
and retention through the replication method and reads nothing but the volume handle.

## Backups

A backup type is a replication method of the plan (see [Replication Types](../configuration/replication-types.md)).
Every application that uses the method is backed up:

```yaml title="Protection plan with asynchronous replication and backups"
apiVersion: dr.simplyblock.io/v1alpha1
kind: ProtectionPlan
metadata:
  name: fra
spec:
  # sites, storageProfile, and s3Profiles omitted
  methods:
    - name: async-5m-backup
      type: async-s3-backup
      schedulingInterval: 5m
      s3Backup:
        interval: 1h
        retention: 24
```

- **Interval and retention:** `s3Backup.interval` is the backup interval in Ramen's notation (`15m`, `1h`, `1d`).
  `s3Backup.retention` is the number of backups kept per volume.
- **Store:** The DR metadata store of the site the volume is primary on (`spec.s3Profiles`). A backup can be restored
  from any store of the plan.
- **Key:** Backups are keyed by the volume handle of the PersistentVolume, which stays the same through every
  failover and relocation.
- **Objects:** The Kubernetes objects of the application are the captures Ramen keeps in the DR metadata bucket. No
  second capture is taken for a backup.

The replication class of the method carries the interval, retention, and stores to the CSI driver. For a
`sync-s3-backup` application, dr-agent keeps one VolumeReplication per PVC with that class on the zone the
application runs in, because no Ramen object exists for a sync application.

!!! info "Coming soon"
    The backups of the backup types are written by the simplyblock CSI driver on the `integrate_csi_addons` branch of
    the Simplyblock Operator. On a released driver, the method is accepted, but no backup is written.

## Restoring After a Total Loss

When the hub and all sites are lost, only the S3 buckets remain: the archive bucket with the DR state, and the DR
metadata buckets with the application captures and the volume backups. Recovery follows these steps:

1. **Rebuild the clusters:** Build a new hub cluster and new site clusters with simplyblock storage. Install the hub
   as described in [Install the Hub](../install/hub.md).
2. **Restore the DR configuration:** Restore the state bundle with the `-fresh-sites` flag. See
   [Hub Recovery](hub-recovery.md) for the full procedure.

    ```bash title="Restoring the DR configuration for rebuilt sites"
    dr-restore restore -fresh-sites \
      -s3-endpoint s3.eu-central-1.amazonaws.com -bucket dr-archive -region eu-central-1 -prefix dr/ \
      -public-key bundle-signing.pub
    ```

    With `-fresh-sites`, DRPCs and Placements are left out, and every ProtectedApplication is annotated
    `dr.simplyblock.io/awaiting-restore=true`. While annotated, the application is not protected, so it is not
    deployed empty on the rebuilt site.

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
  timeout: 30m
```

### RestoreAction Phases

| Phase          | What happens                                                                                                                                                                                                                                                     |
|----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Pending`      | Checks that the application is awaiting restore and that its method is a backup type.                                                                                                                                                                            |
| `Restoring`    | dr-hub reads the lost protection record from the DR metadata store, which names the capture to recover from. dr-agent on the source site creates the namespaces and restores the application's objects from that capture in the order of the generated Recipe.   |
| `Reprotecting` | The annotation is removed, and the application is protected again. Ramen restores the PVs and PVCs from its store, and the storage restores every volume whose handle it does not know from its newest backup. The phase ends when the application is protected. |
| `Verifying`    | dr-agent waits for the application's pods to be ready and reports what each volume was restored from.                                                                                                                                                            |
| `Completed`    | The application runs on its source site and is protected again.                                                                                                                                                                                                  |
| `Failed`       | A step failed. See `status.steps` and `status.message`.                                                                                                                                                                                                          |

```bash title="Listing restore actions"
kubectl -n ramen-ops get rsa
```

`status.capture` names the capture the objects came from, `status.volumes[]` the restore point of every volume, and
`status.dataLoss` the time between the oldest restore point and the start of the restore, an upper bound of the data
lost.

## Restrictions

- **Source site only:** An application is restored onto its source site. Restoring onto another site is not
  supported.
- **Whole applications:** An application is restored as a whole. Partial restores are not supported.
- **No failback:** A RestoreAction is not a failover. An application that is still protected is refused. Use a
  [failover](unplanned-failover.md) or [relocation](relocate-restart.md) instead.
- **Managed applications:** A managed application has no capture. GitOps deploys it again once it is protected.
- **Sync applications:** A `sync-s3-backup` application has no capture either, so it cannot be restored onto a
  rebuilt stretch cluster yet.
- **Shared S3 profile:** A plan that references an existing Ramen S3 profile (`spec.s3Profile`) cannot use a backup
  type, because dr-hub does not know its store.
