---
title: "FoundationDB Backup and Restore"
description: "Back up and restore the FoundationDB key-value store behind the simplyblock control plane with the FoundationDBBackup and FoundationDBRestore CRDs."
weight: 20110
---

All state of a simplyblock control plane is held in FoundationDB: the cluster topology, the logical volume metadata,
and the task queues. The [FoundationDB Kubernetes Operator](https://github.com/FoundationDB/fdb-kubernetes-operator){:target="_blank" rel="noopener"}
is installed together with the control plane, and backups of that key-value store can be written to S3-compatible
object storage through it. A backup is driven by the `FoundationDBBackup` resource, a restore by the
`FoundationDBRestore` resource. Both live in the `apps.foundationdb.org/v1beta2` API group.

!!! warning
    A FoundationDB backup covers control plane metadata only. The data on the logical volumes is not part of it and
    is backed up separately, see [Backup and Recovery](backup-recovery.md).

The control plane ships FoundationDB 7.3.63 in a `FoundationDBCluster` resource named `simplyblock-fdb-cluster`,
deployed in the `simplyblock` namespace with `imageType: unified`. All examples below use those values. For the
surrounding components, see
[Control Plane Cluster Architecture](../installation/management-cluster-architecture.md).

## Prerequisites

### Object Store Account

An account on an S3-compatible object store is required, and the backup is written into a bucket on it. The bucket
name defaults to `fdb-backups`. Bucket creation is attempted by the backup process, but object stores differ in
whether that is permitted, so the bucket is best created in advance.

### Blob Store Credentials

The account key is passed to the backup agents through a credentials file in the format defined by the
[FoundationDB backup documentation](https://apple.github.io/foundationdb/backups.html){:target="_blank" rel="noopener"}.
In that file the secret is keyed by the account name, written without its port:

```yaml title="Example of a blob store credentials secret (fdb-backup-credentials.yaml)"
apiVersion: v1
kind: Secret
metadata:
  name: fdb-backup-credentials
  namespace: simplyblock
type: Opaque
stringData:
  credentials: |
    {
        "accounts": {
            "account@object-store.example": {
                "secret": "<ACCOUNT_KEY>"
            }
        }
    }
```

The path to the file is announced to the backup agents through the `FDB_BLOB_CREDENTIALS` environment variable.

### Object Store Access for the Operator

The `fdbbackup` and `fdbrestore` commands are run by the FoundationDB operator itself, so the same credentials have
to be reachable from the `simplyblock-fdb-controller-manager` deployment. That deployment is rendered by the control
plane chart without a credentials mount and has to be patched:

```yaml title="Example of a patch mounting the credentials into the operator (fdb-operator-credentials.yaml)"
spec:
  template:
    spec:
      volumes:
        - name: backup-credentials
          secret:
            secretName: fdb-backup-credentials
      containers:
        - name: manager
          env:
            - name: FDB_BLOB_CREDENTIALS
              value: /var/backup-credentials/credentials
          volumeMounts:
            - name: backup-credentials
              mountPath: /var/backup-credentials
```

```bash title="Mounting the blob store credentials into the FoundationDB operator"
kubectl -n simplyblock patch deployment simplyblock-fdb-controller-manager \
    --type strategic \
    --patch-file fdb-operator-credentials.yaml
```

!!! note
    The patch is overwritten by the next `helm upgrade` of the control plane chart and has to be reapplied
    afterward.

### TLS Material

Backup agents connect to the cluster as ordinary FoundationDB clients. The `enableTls` flag of `mainContainer` and
`sidecarContainer` applies to server processes and is ignored by them. When the control plane is installed with
mutual TLS, the certificate, the key, and the CA file are read from the paths named by
`FDB_TLS_CERTIFICATE_FILE`, `FDB_TLS_KEY_FILE`, and `FDB_TLS_CA_FILE`. The material is held in the
`simplyblock-foundationdb-tls` secret and is mounted into the backup agent pods through `podTemplateSpec`. The same
three variables are set on the operator deployment by the chart whenever mutual TLS is enabled.

The certificate and the key have to be parseable so that the TLS subsystem of the agents initializes. They are not
used for the connection to the object store, which is verified against the CA file instead.

## Creating a Backup

A backup is started by creating a `FoundationDBBackup` resource that names the cluster and the object store:

```yaml title="Example of a continuous FoundationDB backup (fdb-backup.yaml)"
apiVersion: apps.foundationdb.org/v1beta2
kind: FoundationDBBackup
metadata:
  name: simplyblock-fdb-cluster
  namespace: simplyblock
spec:
  version: 7.3.63
  clusterName: simplyblock-fdb-cluster
  imageType: unified
  agentCount: 2
  snapshotPeriodSeconds: 86400
  mainContainer:
    imageConfigs:
      - baseImage: quay.io/simplyblock-io/fdb-kubernetes-monitor
  blobStoreConfiguration:
    accountName: account@object-store.example:443
    bucket: fdb-backups
  podTemplateSpec:
    spec:
      volumes:
        - name: backup-credentials
          secret:
            secretName: fdb-backup-credentials
      containers:
        - name: foundationdb
          env:
            - name: FDB_BLOB_CREDENTIALS
              value: /var/backup-credentials/credentials
          volumeMounts:
            - name: backup-credentials
              mountPath: /var/backup-credentials
```

```bash title="Starting the FoundationDB backup"
kubectl apply -f fdb-backup.yaml
```

Two things are done by the operator in response. A deployment of backup agent pods is created, which connect to
`simplyblock-fdb-cluster` and perform the transfer. An `fdbbackup start` command is then run against the cluster,
which begins a continuous backup and keeps taking snapshots at the configured interval.

The `version` and the `imageType` have to match the `FoundationDBCluster` resource, since the agents run the same
FoundationDB binaries as the cluster. With `imageType: unified` the backup agent image is the
`fdb-kubernetes-monitor` image, which is why the same repository is named in `mainContainer.imageConfigs`.

The destination is derived from `blobStoreConfiguration`. The backup is written to the bucket under the name in
`backupName`, which defaults to the name of the `FoundationDBBackup` resource. When no port is given in
`accountName`, port 443 is used, or port 80 when secure connections are disabled.

!!! note
    Backups are always continuous in this version of the CRD. A one-time snapshot is not offered, and neither are
    backup tags, so one `FoundationDBBackup` resource per cluster is supported.

### Spec Fields

| Field                                  | Type   | Description                                                                                           |
|----------------------------------------|--------|-------------------------------------------------------------------------------------------------------|
| `clusterName`                          | string | Name of the `FoundationDBCluster` to back up. **Required**.                                           |
| `version`                              | string | FoundationDB version of the backup agents. Has to match the cluster. **Required**.                    |
| `blobStoreConfiguration.accountName`   | string | Account and endpoint of the object store, as `<ACCOUNT>@<HOST>:<PORT>`. **Required**.                 |
| `blobStoreConfiguration.backupName`    | string | Name of the backup in the bucket. Defaults to the name of the resource.                               |
| `blobStoreConfiguration.bucket`        | string | Bucket the backup is written to. Defaults to `fdb-backups`.                                           |
| `blobStoreConfiguration.urlParameters` | list   | Additional backup URL parameters, each written as `<KEY>=<VALUE>`.                                    |
| `agentCount`                           | int    | Number of backup agent pods. Defaults to `2`.                                                         |
| `snapshotPeriodSeconds`                | int    | Interval between two snapshots, in seconds. Defaults to `864000`, ten days.                           |
| `backupState`                          | string | Desired state of the backup: `Running`, `Stopped`, or `Paused`.                                       |
| `backupType`                           | string | `backup_agent` (default) or `partitioned_log`.                                                        |
| `deletionPolicy`                       | string | Action taken when the resource is deleted: `noop` (default), `stop`, or `cleanup`.                    |
| `imageType`                            | string | `split` (default) or `unified`. Has to match the cluster.                                             |
| `mainContainer`                        | object | Image configuration and TLS settings of the `foundationdb` container.                                 |
| `podTemplateSpec`                      | object | Pod template of the backup agents, used for credential and certificate volumes.                       |
| `customParameters`                     | list   | Additional command line parameters passed to the backup agents.                                       |
| `backupDeploymentMetadata`             | object | Labels and annotations added to the backup agent deployment.                                          |
| `encryptionKeyPath`                    | string | Path to the backup encryption key. Requires FoundationDB 7.4.6 or newer and is unavailable on 7.3.63. |

### Backup Types

Two backup types are selectable through `backupType`:

- `backup_agent`, the default, uses the file backup system. The whole backup lifecycle is managed by the operator.
- `partitioned_log` uses the partitioned log backup system. Key-range snapshots are taken by operator-managed backup
  agents, while the mutation backup requires backup workers in the `FoundationDBCluster` resource.

!!! warning
    Migration between backup types is not supported. To switch, the existing backup is stopped and cleaned up, the
    `FoundationDBBackup` resource is deleted, and a new resource is created with the other type.

### Backup State

The `backupState` field holds the desired state of the backup. With `Running`, or with the field unset, snapshots
are taken at the configured interval. With `Stopped`, the backup agent deployment is kept in place but no backup is
run, which is the setting used to prepare a cluster for a restore. With `Paused`, the agents stop processing until
the state is set back to `Running`.

Pausing and resuming act on all backup agents of a cluster at once. There is no per-backup pause.

### Deletion Policy

The `deletionPolicy` field decides what happens to the backup itself when the `FoundationDBBackup` resource is
deleted:

| Value     | Behavior                                                                                            |
|-----------|-----------------------------------------------------------------------------------------------------|
| `noop`    | Default. The backup is left as it is. Mutation logs keep accumulating without agents to drain them. |
| `stop`    | The backup is aborted.                                                                              |
| `cleanup` | The backup is aborted and its data is deleted from the object store.                                |

With `stop` or `cleanup`, the `foundationdb.org/fdb-kubernetes-operator` finalizer is added to the resource.
Removing that finalizer by hand risks an incomplete removal and is not recommended. The deletion step is carried out
by the operator and can block for up to ten minutes before the reconciliation is retried.

!!! note
    A `noop` policy leaves the backup running while its agents are gone. As long as the cluster still takes writes,
    mutation logs are retained in the cluster and are never trimmed, which grows the keyspace until the backup is
    aborted.

### Connections Without TLS

Secure connections to the object store are used by default. Additional backup URL parameters are passed through
`blobStoreConfiguration.urlParameters`, among them `secure_connection`, which disables TLS toward the object store
when set to `0`:

```yaml title="Example of a backup to an object store without TLS"
spec:
  blobStoreConfiguration:
    accountName: account@object-store.example:80
    urlParameters:
      - "secure_connection=0"
```

## Checking the Backup Status

```bash title="Listing the FoundationDB backups"
kubectl -n simplyblock get foundationdbbackup
```

```plain title="Example output of the backup listing"
NAME                     GENERATION   RECONCILED   AGE
simplyblock-fdb-cluster  1            1            12m
```

The backup is reconciled once `RECONCILED` has caught up with `GENERATION`. The state of the backup itself is
reported under `status.backupDetails`, which carries the destination `url`, the `running` and `paused` flags, and
the `snapshotTime` of the last snapshot:

```bash title="Reading the backup details"
kubectl -n simplyblock get foundationdbbackup simplyblock-fdb-cluster \
    -o jsonpath='{.status.backupDetails}'
```

The agent pods carry the FoundationDB command line tools, so the backup can also be queried directly:

```bash title="Querying the backup status from a backup agent pod"
kubectl -n simplyblock exec deploy/simplyblock-fdb-cluster-backup-agents -- \
    fdbbackup status
```

## Restoring a Backup

A restore is started by creating a `FoundationDBRestore` resource. Two conditions have to be met before it succeeds.

The destination database has to be empty. A restore into a database that still holds keys is rejected, so a
restore over an existing control plane requires the keyspace to be cleared first.

Backup agents have to exist for the destination cluster, because the restore is carried out by them. When the
destination is a freshly created cluster that is not being backed up itself, the agents are brought up by a
`FoundationDBBackup` resource with `backupState: Stopped`, which deploys the agents without starting a backup.

!!! warning
    The destination cluster is locked for the duration of the restore, and the control plane cannot serve requests
    against it. After the restore completes, the control plane services are restarted so that the restored state is
    picked up.

```yaml title="Example of a FoundationDB restore (fdb-restore.yaml)"
apiVersion: apps.foundationdb.org/v1beta2
kind: FoundationDBRestore
metadata:
  name: simplyblock-fdb-cluster
  namespace: simplyblock
spec:
  destinationClusterName: simplyblock-fdb-cluster
  blobStoreConfiguration:
    accountName: account@object-store.example:443
    backupName: simplyblock-fdb-cluster
    bucket: fdb-backups
```

```bash title="Starting the FoundationDB restore"
kubectl apply -f fdb-restore.yaml
```

An `fdbrestore` command is run against the destination cluster by the operator. Without further fields, the entire
keyspace is restored to the most recent restorable version of the backup.

### Spec Fields

| Field                                  | Type   | Description                                                                               |
|----------------------------------------|--------|-------------------------------------------------------------------------------------------|
| `destinationClusterName`               | string | Name of the `FoundationDBCluster` the backup is restored into. **Required**.              |
| `blobStoreConfiguration.accountName`   | string | Account and endpoint of the object store, as `<ACCOUNT>@<HOST>:<PORT>`. **Required**.     |
| `blobStoreConfiguration.backupName`    | string | Name of the backup in the bucket to restore from.                                         |
| `blobStoreConfiguration.bucket`        | string | Bucket the backup was written to. Defaults to `fdb-backups`.                              |
| `blobStoreConfiguration.urlParameters` | list   | Additional backup URL parameters, each written as `<KEY>=<VALUE>`.                        |
| `backupVersion`                        | int    | Version to restore to. Defaults to the highest restorable version of the backup.          |
| `keyRanges`                            | list   | Key ranges to restore, each with a `start` and an `end`. Defaults to the entire keyspace. |
| `customParameters`                     | list   | Additional command line parameters passed to the restore.                                 |
| `encryptionKeyPath`                    | string | Path to the encryption key of the backup. Requires FoundationDB 7.4.6 or newer.           |

A point in time is selected through `backupVersion`. Any version after the end of the first snapshot is restorable,
which is what makes the continuous backup a point-in-time backup.

!!! note
    A control plane restore is only consistent when the whole keyspace is restored. The `keyRanges` field is meant
    for partial recovery and leaves the metadata in a mixed state when used against a simplyblock control plane.

### Checking the Restore Status

```bash title="Listing the FoundationDB restores"
kubectl -n simplyblock get foundationdbrestore
```

```plain title="Example output of the restore listing"
NAME                     AGE   STATE
simplyblock-fdb-cluster  4m    running
```

The `STATE` column mirrors the state reported by `fdbrestore` and changes to `completed` once all data has been
written. The same information is available from a backup agent pod:

```bash title="Querying the restore status from a backup agent pod"
kubectl -n simplyblock exec deploy/simplyblock-fdb-cluster-backup-agents -- \
    sh -c 'fdbrestore status --dest_cluster_file ${FDB_CLUSTER_FILE}'
```

## Troubleshooting

When a restore does not start, the reason is recorded in the log of the `simplyblock-fdb-controller-manager` pod:

```bash title="Reading the FoundationDB operator log"
kubectl -n simplyblock logs deploy/simplyblock-fdb-controller-manager \
    | grep "Error from FDB command"
```

The most common cause is a destination cluster that still holds data:

```plain title="Example output of a restore into a non-empty destination"
Using target restore version 123
Backup Description
URL: blobstore://object-store.example
Restorable: true
Partitioned logs: false
Restoring backup to version: 123
ERROR: Attempted to restore into a non-empty destination database
Fatal Error: Attempted to restore into a non-empty destination database
```

The content of the destination cluster is inspected through `fdbcli` from any FoundationDB pod:

```bash title="Opening a FoundationDB shell on the destination cluster"
kubectl -n simplyblock exec -it simplyblock-fdb-cluster-storage-1 -- fdbcli
```

```plain title="Example of listing the keys of the destination cluster"
fdb> getrange "" \xff
```

!!! danger
    Clearing the keyspace destroys all control plane state of the destination cluster and cannot be undone. It is
    only performed when the data is known to be expendable, such as on a cluster created for the restore.

```plain title="Example of clearing the keyspace of the destination cluster"
fdb> writemode on; clearrange "" \xff
```
