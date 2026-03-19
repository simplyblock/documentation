---
title: "Kubernetes Custom Resource Definitions"
weight: 20200
---

Simplyblock provides Custom Resource Definitions (CRDs) for managing storage infrastructure directly from Kubernetes.
CRDs enable declarative management of clusters, storage nodes, volumes, backups, replication, and migrations using
standard `kubectl` commands.

## Common Patterns

All simplyblock CRDs follow these patterns:

- **Actions:** Many CRDs support an `action` field in the spec to trigger operations (e.g., `restore`, `fail-over`).
  Actions are one-shot operations -- once processed, the action field is cleared.
- **Status subresource:** Each CRD uses a separate status subresource updated by the operator. Use `kubectl get` with
  `-o wide` or `-o yaml` to see full status details.
- **Statistics:** Most CRDs support optional `includeStats` and `statsHistoryInSeconds` fields to include performance
  metrics in the status.

## SimplyBlockStorageCluster

Manages the lifecycle of a simplyblock storage cluster.

**Resource:** `storage-clusters.simplyblock.com` | **Short name:** `sbc`

### Actions

| Action     | Description                                              |
|------------|----------------------------------------------------------|
| `activate` | Activates a newly created cluster                        |
| `upgrade`  | Initiates a cluster upgrade to a newer version           |

### Spec Fields

**Create-only fields** (cannot be changed after creation):

| Field                     | Type    | Description                                                       |
|---------------------------|---------|-------------------------------------------------------------------|
| `mgmtIfc`                | string  | Management network interface name                                  |
| `enableNodeAffinity`     | boolean | Enable node affinity for storage nodes                             |
| `stripeWdata`            | integer | Erasure coding data chunks (1, 2, or 4)                            |
| `stripeWparity`          | integer | Erasure coding parity chunks (0, 1, or 2)                          |
| `haType`                 | string  | High availability type: `ha` or `single`                           |
| `isSingleNode`           | boolean | Single-node cluster mode                                           |
| `ingressHostSource`      | string  | Ingress source: `hostip`, `loadbalancer`, or `dns`                 |
| `tlsSecretName`          | string  | Kubernetes Secret name for TLS certificates                        |
| `dnsName`                | string  | Fully qualified DNS name (required if `ingressHostSource=dns`)     |
| `strictNodeAntiAffinity` | boolean | Enforce strict node anti-affinity for HA                           |
| `qpairCount`             | integer | NVMe/TCP queue pair count per logical volume                       |

**Updatable fields:**

| Field                     | Type    | Default | Description                                              |
|---------------------------|---------|---------|----------------------------------------------------------|
| `ClusterName`            | string  |         | Human-readable cluster name                               |
| `GrafanaEndpoint`        | string  |         | Grafana endpoint URL                                      |
| `qosClasses`             | string  |         | Comma-separated list of up to 6 QoS classes               |
| `capWarn`                | integer | 89      | Capacity warning threshold (%)                             |
| `capCrit`                | integer | 99      | Capacity critical threshold (%)                            |
| `provCapWarn`            | integer | 250     | Provisioned capacity warning threshold (%)                 |
| `provCapCrit`            | integer | 500     | Provisioned capacity critical threshold (%)                |
| `logDelInterval`         | string  | `3d`    | Log retention period                                       |
| `metricsRetentionPeriod` | string  | `7d`    | Prometheus metrics retention period                        |
| `clientQpairCount`       | integer |         | Client-side NVMe/TCP queue pair count                      |
| `contactPoint`           | string  |         | Email or webhook URL for alerts                            |

### Status Fields

| Field                      | Type     | Description                                                          |
|----------------------------|----------|----------------------------------------------------------------------|
| `UUID`                    | string   | Cluster UUID (auto-generated)                                         |
| `state`                   | string   | Cluster state: `UNREADY`, `IN_ACTIVATION`, `ACTIVE`, `SUSPENDED`, `DEGRADED` |
| `health`                  | boolean  | Overall cluster health                                                |
| `mgmtNodes`              | integer  | Number of management nodes                                            |
| `storageNodes`            | integer  | Number of storage nodes                                               |
| `NQN`                    | string   | Cluster NVMe Qualified Name                                          |
| `mgmtIp`                 | string   | Management IP address                                                 |
| `rebalancing`             | boolean  | Whether the cluster is currently rebalancing data                     |
| `secretName`              | string   | Kubernetes Secret containing cluster credentials                      |
| `grafana_endpoint`        | string   | Grafana dashboard endpoint                                            |
| `graylog_endpoint`        | string   | Graylog log management endpoint                                       |

### kubectl Output Columns

```plain
NAME    CLUSTERUUID   CLUSTERNAME   HA TYPE   STATE    REBALANCING   LAST UPDATED
```

---

## StorageNode

Manages the lifecycle and configuration of individual storage nodes.

**Resource:** `storage-nodes.simplyblock.com` | **Short name:** `sbn`

### Actions

| Action     | Description                                              |
|------------|----------------------------------------------------------|
| `restart`  | Restarts the storage node (optionally at a new address)  |
| `suspend`  | Suspends the storage node                                |
| `shutdown` | Shuts down the storage node                              |
| `remove`   | Removes the storage node from the cluster                |

### Spec Fields

| Field                    | Type           | Description                                                     |
|--------------------------|----------------|-----------------------------------------------------------------|
| `clusterUUID`           | string         | UUID of the parent cluster                                       |
| `MaxLVol`               | integer        | Maximum number of logical volumes                                |
| `MaxSize`               | string         | Maximum total provisioning size (e.g., `10Ti`)                   |
| `spdkImage`             | string         | SPDK container image override                                    |
| `mgmtIfc`               | string         | Management network interface                                     |
| `coreIsolation`         | boolean        | Enable CPU core isolation for SPDK                               |
| `corePercentage`        | integer (1-100)| Percentage of CPU cores to isolate                               |
| `coreMask`              | string         | Hexadecimal CPU core mask                                        |
| `pcieAllowList`         | string[]       | PCIe device addresses to use                                     |
| `pcieDenyList`          | string[]       | PCIe device addresses to exclude                                 |
| `pcieModel`             | string         | PCIe device model filter                                         |
| `driveSizeRange`        | string         | Drive size range filter (e.g., `1TB-4TB`)                        |
| `socketsToUse`          | integer        | Number of CPU sockets to use                                     |
| `nodesPerSocket`        | integer        | NUMA nodes per socket                                            |
| `dataNIC`               | string[]       | Network interfaces for data traffic                              |
| `haJmCount`             | integer        | HA journal manager count                                         |
| `useSeparateJournalDevice` | boolean     | Use a separate device for journaling                             |
| `nodeAddr`              | string         | New node address (used with `restart` action)                    |
| `nodeIp`                | string         | New node IP (used with `restart` action)                         |
| `force`                 | boolean        | Force the action                                                 |
| `addPcieToAllowList`    | string[]       | PCIe devices to add during restart                               |

### Status Fields

| Field                | Type    | Description                                                                      |
|----------------------|---------|----------------------------------------------------------------------------------|
| `uuid`              | string  | Storage node UUID                                                                 |
| `state`             | string  | Node state: `online`, `offline`, `schedulable`, `unreachable`, `in_restart`, `in_shutdown`, `suspended` |
| `health`            | string  | Health status                                                                     |
| `hostname`          | string  | Node hostname                                                                     |
| `mgmtIp`           | string  | Management IP address                                                             |
| `uptime`            | string  | Node uptime                                                                       |
| `memory`            | string  | Available memory                                                                  |
| `secondaryNodeUUID` | string  | UUID of the assigned secondary node                                               |
| `lvolsProvisioned`  | integer | Number of provisioned logical volumes                                             |
| `hugepagesAssigned` | string  | Huge pages memory allocated                                                       |
| `devices.total`     | integer | Total NVMe devices                                                                |
| `devices.active`    | integer | Active NVMe devices                                                               |
| `capacity.totalBytes`   | string  | Total storage capacity                                                        |
| `capacity.usedBytes`    | string  | Used storage capacity                                                         |
| `capacity.usedPercent`  | integer | Storage utilization percentage                                                |

### kubectl Output Columns

```plain
NAME   UUID   HOSTNAME   MGMTIP   STATUS   HEALTH   UPTIME   DEVICES   CAPACITY%   USED   TOTAL
```

---

## Pool

Manages storage pools within a cluster.

**Resource:** `pools.simplyblock.com` | **Short name:** `pl`

### Spec Fields

| Field           | Type    | Required | Description                                     |
|-----------------|---------|----------|-------------------------------------------------|
| `name`         | string  | Yes      | Pool name                                        |
| `clusterUUID`  | string  | Yes      | UUID of the parent cluster                       |
| `status`       | string  |          | Pool status: `enabled` or `disabled`             |
| `capacityLimit`| string  |          | Total capacity limit (e.g., `100Gi`)             |
| `qosIOPSLimit` | integer |          | QoS IOPS limit for the pool                      |
| `rwLimit`      | integer |          | Read/write throughput limit                       |
| `rLimit`       | integer |          | Read throughput limit                             |
| `wLimit`       | integer |          | Write throughput limit                            |
| `action`       | string  |          | One-shot action (e.g., restart, resync)           |

### Status Fields

| Field  | Type   | Description            |
|--------|--------|------------------------|
| `uuid` | string | Auto-generated pool UUID |

---

## Logical Volume (Rackup/lvol)

Provides read-only status information about logical volumes.

**Resource:** `lvols.simplyblock.com` | **Short name:** `lvl`

### Actions

| Action       | Description                          |
|--------------|--------------------------------------|
| `get-status` | Retrieves current volume status      |

### Spec Fields

| Field                   | Type    | Description                           |
|-------------------------|---------|---------------------------------------|
| `namePVC`              | string  | Name of the Persistent Volume Claim    |
| `includeStats`         | boolean | Include performance statistics         |
| `statsHistoryInSeconds`| integer | Duration of statistics history         |

### Status Fields

| Field             | Type     | Description                                    |
|-------------------|----------|------------------------------------------------|
| `uuid`           | string   | Volume UUID                                     |
| `nodeUUID`       | string   | UUID of the primary storage node                |
| `hostname`       | string   | Primary node hostname                           |
| `nqn`            | string   | NVMe Qualified Name                             |
| `poolUUID`       | string   | Storage pool UUID                               |
| `poolName`       | string   | Storage pool name                               |
| `status`         | string   | Volume status                                   |
| `health`         | string   | Volume health                                   |
| `size`           | integer  | Volume size in bytes                            |
| `utilization`    | integer  | Current usage in bytes                          |
| `percentUtil`    | integer  | Utilization percentage                          |
| `isCrypto`       | boolean  | Whether volume is encrypted                     |
| `clonedFromSnap` | string   | Source snapshot UUID (if cloned)                 |
| `qosIOPS`        | integer  | QoS IOPS limit                                  |
| `qosRWTP`        | integer  | QoS read/write throughput limit                  |
| `fabric`         | string   | Fabric type                                     |
| `stats`          | array    | Performance metrics (wiops, riops, wtp, rtp, capacityUtil) |

---

## Backup

Manages snapshot-based backups to S3 or filesystem targets.

**Resource:** `backups.simplyblock.com` | **Short name:** `bkp`

### Actions

| Action    | Description                                                  |
|-----------|--------------------------------------------------------------|
| `restore` | Restores volumes from this backup set                        |

### Spec Fields

| Field                | Type    | Description                                                      |
|----------------------|---------|------------------------------------------------------------------|
| `clusterUUID`       | string  | UUID of the cluster                                               |
| `pool`              | string  | Pool to snapshot and back up (all PVCs in pool)                   |
| `pvc`               | string  | Individual PVC to back up (alternative to pool)                   |
| `s3.bucket`         | string  | S3 bucket name                                                    |
| `s3.region`         | string  | AWS region                                                        |
| `s3.accessKeySecret`| string  | Kubernetes Secret reference for S3 access key                     |
| `s3.secretKeySecret`| string  | Kubernetes Secret reference for S3 secret key                     |
| `filesystem.mountPoint` | string | Filesystem mount point (alternative to S3)                    |
| `retention`         | integer | Number of backups to retain                                       |
| `keepOnlineBackup`  | boolean | Keep the online snapshot after backup completes                   |
| `backupRestoreList` | string  | JSON file with backup list for cross-cluster restore              |
| `replacePVConRestore` | boolean | Replace existing bound PVCs during restore                     |

### Status Fields

| Field          | Type      | Description                                              |
|----------------|-----------|----------------------------------------------------------|
| `scheduleID`  | string    | Backup schedule UUID                                      |
| `lastAction`  | string    | Last action performed by the operator                     |
| `lastActionAt`| date-time | Timestamp of last action                                  |
| `state`       | string    | Backup state: `Pending`, `Running`, `Completed`, `Failed` |
| `PVCs`        | array     | Per-PVC backup details (name, poolUUID, backups[])        |

### kubectl Output Columns

```plain
NAME   CLUSTER   POOL   PVC   TARGET   FILESYSTEM   INTERVAL   RETENTION   LASTBACKUP   STATE
```

### Example

```yaml title="Create a backup of all PVCs in a pool"
apiVersion: simplyblock.com/v25.10.5
kind: Backup
metadata:
  name: daily-backup
  namespace: simplyblock
spec:
  clusterUUID: "4ec308a1-61cf-4ec6-bff9-aa837f7bc0ea"
  pool: "production"
  s3:
    bucket: "simplyblock-backups"
    region: "eu-central-1"
    accessKeySecret: "backup-s3-credentials"
    secretKeySecret: "backup-s3-credentials"
  retention: 7
```

```yaml title="Restore from a backup"
apiVersion: simplyblock.com/v25.10.5
kind: Backup
metadata:
  name: daily-backup
  namespace: simplyblock
spec:
  clusterUUID: "4ec308a1-61cf-4ec6-bff9-aa837f7bc0ea"
  pool: "production"
  action: restore
  s3:
    bucket: "simplyblock-backups"
    region: "eu-central-1"
    accessKeySecret: "backup-s3-credentials"
    secretKeySecret: "backup-s3-credentials"
```

---

## BackupSchedule

Defines recurring backup schedules for automated data protection.

**Resource:** `backupscheduless.simplyblock.com` | **Short name:** `bks`

### Actions

| Action               | Description                                      |
|----------------------|--------------------------------------------------|
| `restore`           | Restores volumes from backups in this schedule    |
| `delete-all-backups`| Deletes all backups created by this schedule      |

### Spec Fields

Same as [Backup](#backup) spec fields, with the addition of:

| Field                | Type    | Description                                                  |
|----------------------|---------|--------------------------------------------------------------|
| `backupRestoreList` | string  | JSON file with backup metadata for cross-cluster restore      |
| `replacePVConRestore` | boolean | Replace existing bound PVCs during restore                 |

### Status Fields

| Field          | Type      | Description                                                    |
|----------------|-----------|----------------------------------------------------------------|
| `backupID`    | array     | List of backup UUIDs created by this schedule                   |
| `lastAction`  | string    | Last action performed by the operator                           |
| `lastActionAt`| date-time | Timestamp of last action                                        |
| `state`       | string    | Schedule state: `Pending`, `Running`, `Completed`, `Failed`     |
| `PVCs`        | array     | Per-PVC backup details (name, poolUUID, backups[])              |

---

## Replication

Configures asynchronous snapshot-based replication between two simplyblock clusters for disaster recovery.

**Resource:** `replications.simplyblock.com` | **Short name:** `rpl`

### Actions

| Action      | Description                                                                    |
|-------------|--------------------------------------------------------------------------------|
| `stop`      | Stops an ongoing replication (can be resumed later)                            |
| `resume`    | Resumes a stopped replication; intermediate data will be caught up             |
| `fail-over` | Promotes target PVCs to primary; disconnects and re-provisions on target site  |
| `fail-back` | Synchronizes delta back to primary using iterative snapshots, then re-provisions |

### Spec Fields

| Field              | Type   | Required | Description                                                |
|--------------------|--------|----------|------------------------------------------------------------|
| `clusterUUID`     | string | Yes      | UUID of the source cluster                                  |
| `targetClusterUUID`| string | Yes     | UUID of the target cluster                                  |
| `pool`            | string |          | Pool name -- all PVCs in this pool are replicated           |
| `pvc`             | string |          | Individual PVC name (alternative to pool)                   |
| `interval`        | string |          | Replication frequency (minimum 60 seconds)                  |

### Status Fields

| Field          | Type      | Description                                                       |
|----------------|-----------|-------------------------------------------------------------------|
| `replicationID`| string   | Unique replication identifier                                      |
| `lastAction`  | string    | Last action performed by the operator                              |
| `lastActionAt`| date-time | Timestamp of last action                                           |
| `state`       | string    | Replication state: `Stopped`, `Running`, `Delayed`, `Failed`       |
| `backlog`     | integer   | Number of snapshots waiting for or in active replication           |
| `dataBacklog` | integer   | Amount of data (GB) waiting for or in replication                  |

### kubectl Output Columns

```plain
NAME   CLUSTER   TARGETCLUSTER   POOL   PVC   STATUS   BACKLOG   DATABACKLOG   INTERVAL
```

### Lifecycle

1. **Create:** A new replication relationship is established between two clusters. It can cover an entire pool or a
   single PVC. An interval defines the replication frequency.
2. **Running:** Snapshots are periodically transferred from source to target at the configured interval.
3. **Stop/Resume:** Replication can be paused and resumed. On resume, accumulated changes are caught up, which may
   take additional time.
4. **Fail-over:** Target PVCs are promoted from secondary to primary. Source PVCs are disconnected (if reachable).
   The same PVCs are re-provisioned on target nodes.
5. **Fail-back:** The delta between the most recent snapshot on primary and the current state on secondary is
   synchronized back. This is done iteratively with progressively smaller snapshots. Finally, the PVC is frozen, a
   final snapshot is taken, the remaining data is synchronized, and the PVC is disconnected and re-provisioned on
   the primary site.
6. **Delete:** The replication relationship is removed. Target PVCs are also removed.

### Example

```yaml title="Set up async replication for a pool"
apiVersion: simplyblock.com/v25.11.1
kind: Rackup
metadata:
  name: dr-replication
  namespace: simplyblock
spec:
  clusterUUID: "source-cluster-uuid"
  targetClusterUUID: "target-cluster-uuid"
  pool: "production"
  interval: "300"
```

```yaml title="Initiate failover"
apiVersion: simplyblock.com/v25.11.1
kind: Rackup
metadata:
  name: dr-replication
  namespace: simplyblock
spec:
  clusterUUID: "source-cluster-uuid"
  targetClusterUUID: "target-cluster-uuid"
  pool: "production"
  interval: "300"
  action: "fail-over"
```

---

## SyncReplication

Configures synchronous real-time replication for zero-RPO disaster recovery.

**Resource:** `synchreplications.simplyblock.com` | **Short name:** `srp`

### Actions

| Action      | Description                                                                    |
|-------------|--------------------------------------------------------------------------------|
| `stop`      | Stops synchronous replication                                                  |
| `resume`    | Resumes synchronous replication                                                |
| `fail-over` | Promotes target to primary                                                     |
| `fail-back` | Synchronizes delta back to primary and re-provisions                           |

### Spec Fields

| Field          | Type   | Required | Description                                          |
|----------------|--------|----------|------------------------------------------------------|
| `clusterUUID` | string | Yes      | UUID of the cluster                                   |
| `pool`        | string |          | Pool name -- all PVCs in this pool are replicated     |
| `pvc`         | string |          | Individual PVC name (alternative to pool)             |

!!! note
    Unlike asynchronous replication, synchronous replication does not have an `interval` field (writes are mirrored
    in real time) or a `targetClusterUUID` field (the target is configured at the cluster level).

### Status Fields

| Field                | Type      | Description                                                   |
|----------------------|-----------|---------------------------------------------------------------|
| `synReplicationID`  | string    | Unique synchronous replication identifier                      |
| `lastAction`        | string    | Last action performed by the operator                          |
| `lastActionAt`      | date-time | Timestamp of last action                                       |
| `state`             | string    | Replication state: `Stopped`, `Running`, `Failed`              |
| `backlog`           | integer   | Time of replication interruption in seconds                    |
| `dataBacklog`       | integer   | Amount of data (GB) waiting for or in replication              |

### kubectl Output Columns

```plain
NAME   CLUSTER   POOL   PVC   STATUS   BACKLOG   DATABACKLOG
```

!!! info
    The `backlog` field for synchronous replication represents the duration of any replication interruption in seconds,
    unlike asynchronous replication where it represents the number of pending snapshots.

---

## LVolMigration

Manages live migration of logical volumes between storage nodes.

**Resource:** `lvolmigrations.simplyblock.com` | **Short name:** `lmg`

### Spec Fields

| Field          | Type   | Required | Description                                               |
|----------------|--------|----------|-----------------------------------------------------------|
| `clusterUUID` | string | Yes      | UUID of the cluster                                        |
| `targetNode`  | string |          | UUID of the target storage node                            |
| `pool`        | string |          | Pool name -- all PVCs in this pool are migrated            |
| `pvc`         | string |          | Individual PVC name (alternative to pool)                  |

### Status Fields

| Field          | Type      | Description                                            |
|----------------|-----------|--------------------------------------------------------|
| `migrationID` | string    | Unique migration identifier                             |
| `lastAction`  | string    | Last action performed                                   |
| `lastActionAt`| date-time | Timestamp of last action                                |
| `startTime`   | date-time | Migration start timestamp                               |
| `state`       | string    | Migration state: `Running`, `Cleanup`, `Failed`         |

### kubectl Output Columns

```plain
NAME   CLUSTER   TARGETNODE   POOL   PVC   STATUS   STARTTIME
```

### Example

```yaml title="Migrate a PVC to a target node"
apiVersion: simplyblock.com/v25.11.1
kind: Rackup
metadata:
  name: migrate-db-volume
  namespace: simplyblock
spec:
  clusterUUID: "cluster-uuid"
  targetNode: "target-node-uuid"
  pvc: "postgres-data"
```

---

## Devices

Provides read-only status information about NVMe devices on storage nodes.

**Resource:** `devices.simplyblock.com` | **Short name:** `dev`

### Actions

| Action       | Description                          |
|--------------|--------------------------------------|
| `get-status` | Retrieves current device status      |

### Spec Fields

| Field                   | Type    | Description                        |
|-------------------------|---------|------------------------------------|
| `nodeUUID`             | string  | UUID of the storage node to query   |
| `includeStats`         | boolean | Include performance statistics      |
| `statsHistoryInSeconds`| integer | Duration of statistics history      |

### Status Fields

| Field               | Type    | Description                                    |
|---------------------|---------|------------------------------------------------|
| `devices[].uuid`       | string  | Device UUID                                |
| `devices[].health`     | string  | Device health status                       |
| `devices[].capacity`   | integer | Device capacity                            |
| `devices[].model`      | string  | Device model name                          |
| `devices[].utilization`| integer | Current utilization                        |
| `devices[].status`     | string  | Device status                              |
| `devices[].stats`      | array   | Performance metrics (wiops, riops, wtp, rtp, capacityUtil) |

---

## ClusterTasks

Provides visibility into background tasks running on the cluster.

**Resource:** `tasks.simplyblock.com` | **Short name:** `tsk`

### Actions

| Action   | Description                          |
|----------|--------------------------------------|
| `cancel` | Cancels a specific task by ID        |

### Spec Fields

| Field          | Type    | Description                                |
|----------------|---------|--------------------------------------------|
| `clusterUUID` | string  | UUID of the cluster                         |
| `taskID`      | string  | UUID of the task to cancel                  |
| `subtasks`    | boolean | Include subtasks in the output              |
| `completed`   | boolean | Include completed tasks in the output       |

### Status Fields

| Field                  | Type      | Description                         |
|------------------------|-----------|-------------------------------------|
| `tasks[].uuid`        | string    | Task UUID                            |
| `tasks[].taskType`    | string    | Type of task (e.g., migration, backup) |
| `tasks[].taskStatus`  | string    | Current task status                  |
| `tasks[].parentTask`  | string    | Parent task UUID (for subtasks)      |
| `tasks[].startedAt`   | date-time | Task start timestamp                 |
| `tasks[].retried`     | integer   | Number of retries                    |
