---
title: "Control-Plane Database Backup"
description: "Back up and restore the FoundationDB key-value store behind the simplyblock control plane on plain Linux with the sbctl db-backup commands."
source: "https://docs.simplyblock.io/latest/non-kubernetes/operations/data-protection/control-plane-backup/"
---

# Control-Plane Database Backup

The simplyblock control plane stores all cluster metadata — clusters, nodes, pools, volumes, snapshots, tasks — in
a FoundationDB key-value store on the management nodes. Volume data is not affected by the loss of this database,
but the cluster cannot be managed without it. Simplyblock therefore takes periodic backups of the control-plane
database, which can be written to a local path or to Amazon S3.

On plain Linux (Docker-based deployments), these backups are managed with the `sbctl db-backup` commands
described here. On Kubernetes, control-plane backups are handled by the FoundationDB operator instead, see
[FoundationDB Backup and Restore](../../../kubernetes/operations/data-protection/foundationdb-backup.md).

## Configuring the Backup Destination

By default, backups are written every three hours to `/etc/foundationdb/backup/<CLUSTER_ID>` on the management
node. Both the destination and the frequency can be changed:

```bash title="Configure a local backup path and frequency"
sbctl db-backup config <CLUSTER_ID> \
  --backup-path /mnt/backup/fdb \
  --backup-frequency 3h
```

```bash title="Configure Amazon S3 as the backup destination"
sbctl db-backup config <CLUSTER_ID> \
  --s3-bucket <BUCKET_NAME> \
  --s3-region <REGION> \
  --s3-credentials <API_KEY>:<API_SECRET> \
  --backup-frequency 1d
```

| Parameter            | Default                    | Description                                            |
|----------------------|----------------------------|--------------------------------------------------------|
| `--backup-path`      | `/etc/foundationdb/backup` | Local backup directory on the management node.         |
| `--backup-frequency` | `3h`                       | Interval between automatic backups (e.g., `3h`, `1d`). |
| `--s3-bucket`        | —                          | Amazon S3 bucket name.                                 |
| `--s3-region`        | —                          | Amazon S3 region.                                      |
| `--s3-credentials`   | —                          | S3 API key and secret in the form `KEY:SECRET`.        |

The local path and S3 are mutually exclusive destinations: configuring a local path clears any stored S3
settings. When S3 is configured, access to the bucket is verified first and the configuration is rejected if the
bucket cannot be listed with the given credentials.

!!! note
    A local backup path only protects against database corruption, not against the loss of the management node.
    Place it on storage that is independent of the management node, or use S3.

## Automatic Backups

Once configured, the control plane takes a backup automatically whenever the last one is older than the
configured frequency. No further setup is required. Backup creation, restore, and failure events appear in the
cluster event log.

## Manual Operations

```bash title="Create a backup now"
sbctl db-backup create <CLUSTER_ID>
```

```bash title="List available backups"
sbctl db-backup list <CLUSTER_ID>
```

```bash title="Show the status of the running backup system"
sbctl db-backup status
```

## Restoring the Control-Plane Database

A restore replaces the complete content of the control-plane database with the backup:

```bash title="Restore a backup"
sbctl db-backup restore <BACKUP_NAME> <CLUSTER_ID>
```

`<BACKUP_NAME>` is a backup as reported by `db-backup list`.

!!! danger
    The restore first **clears the entire control-plane database** and then loads the backup. All metadata changes
    made after the backup was taken are lost — volumes, snapshots, or nodes added since then become unknown to the
    control plane, while their data continues to exist on the storage nodes. Only restore the database as part of a
    guided disaster recovery, and never while management services are actively modifying the cluster.
