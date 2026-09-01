---
title: "Logical Volume Commands"
description: "Aliases: lvol"
source: "https://docs.simplyblock.io/latest/reference/cli/volume/"
---

# Logical Volume Commands

<!--
This file is generated. Do not edit it by hand.
Run ./doc-builder gen-sbcli-ref from the documentation repository.
-->

```bash
sbctl volume --help
```


**Aliases:**  lvol 


Logical Volume Commands



## Adds a new logical volume.

Adds a new logical volume.

```bash
sbctl volume add
    <NAME>
    <SIZE>
    <POOL>
    --snapshot
    --max-size=<MAX_SIZE>
    --host-id=<HOST_ID>
    --encrypt
    --crypto-key1=<CRYPTO_KEY1>
    --crypto-key2=<CRYPTO_KEY2>
    --max-rw-iops=<MAX_RW_IOPS>
    --max-rw-mbytes=<MAX_RW_MBYTES>
    --max-r-mbytes=<MAX_R_MBYTES>
    --max-w-mbytes=<MAX_W_MBYTES>
    --max-namespace-per-subsys=<MAX_NAMESPACE_PER_SUBSYS>
    --ha-type=<HA_TYPE>
    --fabric=<FABRIC>
    --lvol-priority-class=<LVOL_PRIORITY_CLASS>
    --namespaced=<NAMESPACED>
    --pvc-name=<PVC_NAME>
    --data-chunks-per-stripe=<DATA_CHUNKS_PER_STRIPE>
    --parity-chunks-per-stripe=<PARITY_CHUNKS_PER_STRIPE>
    --replication-policy=<REPLICATION_POLICY>
    --replicate
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| NAME | The new logical volume name. | string | True |
| SIZE | Logical volume size: 10M, 10G, 10(bytes). | size | True |
| POOL | The storage pool id or name. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --snapshot, -s| Make logical volume with snapshot capability. Default: `false`. | marker | False | False |
| --max-size| The logical volume max size. Default: `1000T`. | size | False | 1000T |
| --host-id| The primary storage node id or hostname. | string | False | - |
| --encrypt| Use inline data encryption and decryption on the logical volume. | marker | False | - |
| --crypto-key1| The hex value of key1 to be used for logical volume encryption. | string | False | - |
| --crypto-key2| The hex value of key2 to be used for logical volume encryption. | string | False | - |
| --max-rw-iops| Maximum Read Write IO Per Second. | integer | False | - |
| --max-rw-mbytes| Maximum Read Write Megabytes Per Second. | integer | False | - |
| --max-r-mbytes| Maximum Read Megabytes Per Second. | integer | False | - |
| --max-w-mbytes| Maximum Write Megabytes Per Second. | integer | False | - |
| --max-namespace-per-subsys| The maximum Namespace per subsystem. Default: `32`. | integer | False | 32 |
| --ha-type| Logical volume HA type (single, ha), default is cluster HA type. Default: `default`.<br/><br/>Available Options:<br/>- single<br/>- default<br/>- ha | string | False | default |
| --fabric| The transport fabric type (tcp or rdma). The cluster must support the chosen fabric. Default: `tcp`.<br/><br/>Available Options:<br/>- tcp<br/>- rdma<br/>- tcp,rdma | string | False | tcp |
| --lvol-priority-class| The logical volume priority class. Default: `0`. | integer | False | 0 |
| --namespaced| Adds this LVol as a namespace on any available subsystem, if not found then create a new subsystem. Default: `false`. | boolean | False | False |
| --pvc-name, --pvc_name| Set the logical volume persistent volume claim name for Kubernetes clients.<br><br> The old parameter name `--pvc_name` is deprecated and shouldn't be used anymore. It will eventually be removed. Please exchange the use of `--pvc_name` with `--pvc-name`. | string | False | - |
| --data-chunks-per-stripe| The erasure coding schema parameter k (distributed raid). Default: `0`. | integer | False | 0 |
| --parity-chunks-per-stripe| The erasure coding schema parameter n (distributed raid). Default: `0`. | integer | False | 0 |
| --replication-policy| Replication policy (id or name) to assign at create time. Configures replication for this volume. | string | False | - |
| --replicate| Replicate LVol snapshot | marker | False | - |


## Changes QoS settings for an active logical volume.

Changes QoS settings for an active logical volume.

```bash
sbctl volume qos-set
    <VOLUME_ID>
    --max-rw-iops=<MAX_RW_IOPS>
    --max-rw-mbytes=<MAX_RW_MBYTES>
    --max-r-mbytes=<MAX_R_MBYTES>
    --max-w-mbytes=<MAX_W_MBYTES>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| VOLUME_ID | The logical volume id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --max-rw-iops| Maximum Read Write IO Per Second. | integer | False | - |
| --max-rw-mbytes| Maximum Read Write Megabytes Per Second. | integer | False | - |
| --max-r-mbytes| Maximum Read Megabytes Per Second. | integer | False | - |
| --max-w-mbytes| Maximum Write Megabytes Per Second. | integer | False | - |


## Lists logical volumes.

Lists logical volumes.

```bash
sbctl volume list
    --cluster-id=<CLUSTER_ID>
    --pool=<POOL>
    --json
    --all
```


| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --cluster-id| List logical volumes in particular cluster. | string | False | - |
| --pool| List logical volumes in particular pool id or name. | string | False | - |
| --json| Print outputs in json format. | marker | False | - |
| --all| List soft deleted logical volumes. | marker | False | - |


## Gets the logical volume details.

Gets the logical volume details.

```bash
sbctl volume get
    <VOLUME_ID>
    --json
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| VOLUME_ID | The logical volume id or name. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --json| Print outputs in json format. | marker | False | - |


## Deletes a logical volume.

Deletes a logical volume. Attention: All data will be lost! This is an irreversible operation! Actual storage capacity will be freed as an asynchronous background task. It may take a while until the actual storage is released.

```bash
sbctl volume delete
    <VOLUME_ID>
    --force
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| VOLUME_ID | The logical volumes id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --force| Force delete logical volume from the cluster. | marker | False | - |


## Gets the logical volume's NVMe/TCP connection string(s).

Multiple connections to the cluster are always available for multi-pathing and high-availability.

```bash
sbctl volume connect
    <VOLUME_ID>
    --ctrl-loss-tmo=<CTRL_LOSS_TMO>
    --host-nqn=<HOST_NQN>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| VOLUME_ID | The logical volume id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --ctrl-loss-tmo| The control loss timeout for this volume. | integer | False | - |
| --host-nqn| Host NQN for DH-HMAC-CHAP authentication (required when volume has allowed hosts with secrets). | string | False | - |


## Resizes a logical volume.

Resizes a logical volume. Only increasing a volume is possible. The new capacity must fit into the storage pool's free capacity.

```bash
sbctl volume resize
    <VOLUME_ID>
    <SIZE>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| VOLUME_ID | The logical volume id. | string | True |
| SIZE | New logical volume size size: 10M, 10G, 10(bytes). | size | True |


## Creates a snapshot from a logical volume.

Creates a snapshot from a logical volume.

```bash
sbctl volume create-snapshot
    <VOLUME_ID>
    <NAME>
    --backup
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| VOLUME_ID | The logical volume id. | string | True |
| NAME | The snapshot name. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --backup| Also create an S3 backup of this snapshot. | marker | False | - |


## Provisions a logical volumes from an existing snapshot.

Provisions a logical volumes from an existing snapshot.

```bash
sbctl volume clone
    <SNAPSHOT_ID>
    <CLONE_NAME>
    --resize=<RESIZE>
    --namespaced=<NAMESPACED>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| SNAPSHOT_ID | The snapshot id. | string | True |
| CLONE_NAME | The clone name. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --resize| New logical volume size: 10M, 10G, 10(bytes). Can only increase. Default: `0`. | size | False | 0 |
| --namespaced| Adds this LVol as a namespace on any available subsystem, if not found then create a new subsystem. Default: `true`. | boolean | False | True |



## Gets a logical volume's capacity.

Gets a logical volume's capacity.

```bash
sbctl volume get-capacity
    <VOLUME_ID>
    --history=<HISTORY>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| VOLUME_ID | The logical volume id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --history| (XXdYYh), list history records (one for every 15 minutes) for XX days and YY hours (up to 10 days in total). | string | False | - |


## Gets a logical volume's I/O statistics.

Gets a logical volume's I/O statistics.

```bash
sbctl volume get-io-stats
    <VOLUME_ID>
    --history=<HISTORY>
    --records=<RECORDS>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| VOLUME_ID | The logical volume id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --history| (XXdYYh), list history records (one for every 15 minutes) for XX days and YY hours (up to 10 days in total). | string | False | - |
| --records| The number of records. Default: `20`. | integer | False | 20 |


## Checks a logical volume's health.

Checks a logical volume's health.

```bash
sbctl volume check
    <VOLUME_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| VOLUME_ID | The logical volume id. | string | True |


## Inflate a logical volume.

All unallocated clusters are allocated and copied from the parent or zero filled if not allocated in the parent. Then all dependencies on the parent are removed.

```bash
sbctl volume inflate
    <VOLUME_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| VOLUME_ID | The logical volume id. | string | True |


## Puts a volume under a replication policy, or changes it (a change re-replicates in full)

Puts a volume under a replication policy, or changes it (a change re-replicates in full)

```bash
sbctl volume replication-policy-set
    <VOLUME_ID>
    <POLICY>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| VOLUME_ID | Logical volume id | string | True |
| POLICY | Replication policy id or name | string | True |


## Takes a volume out of its replication policy, stopping replication and deleting the internal replication snapshots on both sides

Takes a volume out of its replication policy, stopping replication and deleting the internal replication snapshots on both sides

```bash
sbctl volume replication-policy-clear
    <VOLUME_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| VOLUME_ID | Logical volume id | string | True |


## Shows the volume's counterpart on the other cluster (source to target volume id, and the reverse)

Shows the volume's counterpart on the other cluster (source to target volume id, and the reverse)

```bash
sbctl volume replication-relationship
    <VOLUME_ID>
    --json
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| VOLUME_ID | Logical volume id | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --json| Print outputs in json format. | marker | False | - |


## Start snapshot replication taken from lvol

Start snapshot replication taken from lvol

```bash
sbctl volume replication-start
    <LVOL_ID>
    --replication-cluster-id=<REPLICATION_CLUSTER_ID>
    --mode=<MODE>
    --interval-min=<INTERVAL_MIN>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| LVOL_ID | Logical volume id | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --replication-cluster-id| Cluster ID of the replication target cluster | string | False | - |
| --mode| Replication mode: 'failover' (async DR, default) or 'migration' (planned cutover)<br/><br/>Available Options:<br/>- failover<br/>- migration | string | False | - |
| --interval-min| Interval in minutes for automatic internal snapshots (0 = none) | integer | False | - |


## Commit a migration/fail-back cutover: minimize delta then fail the client over to the target

Commit a migration/fail-back cutover: minimize delta then fail the client over to the target

```bash
sbctl volume replication-commit
    <LVOL_ID>
    --delete-source
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| LVOL_ID | Logical volume id | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --delete-source| Delete the source volume once the cutover has completed (migration semantics) | marker | False | - |


## Configure fail-back of a failed-over volume to a source cluster (recovered = delta only; fresh = full). Cut over with replication-commit.

Configure fail-back of a failed-over volume to a source cluster (recovered = delta only; fresh = full). Cut over with replication-commit.

```bash
sbctl volume replication-failback
    <LVOL_ID>
    --source-cluster-id=<SOURCE_CLUSTER_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| LVOL_ID | Failed-over logical volume id (currently on the target cluster) | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --source-cluster-id| Fresh source cluster id. Omit to fail back (delta) to the recovered original source. | string | False | - |


## Stop snapshot replication taken from lvol

Stop snapshot replication taken from lvol

```bash
sbctl volume replication-stop
    <LVOL_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| LVOL_ID | Logical volume id | string | True |


## Lists replication status

Lists replication status

```bash
sbctl volume replication-status
    <CLUSTER_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | Cluster UUID | string | True |


## Show replication progress (time lag and outstanding data) for a volume

Show replication progress (time lag and outstanding data) for a volume

```bash
sbctl volume replication-info
    <VOLUME_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| VOLUME_ID | Logical volume id or name | string | True |


## Start replication for lvol

Start replication for lvol

```bash
sbctl volume replication-trigger
    <LVOL_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| LVOL_ID | Logical volume id | string | True |


## Suspend lvol subsystems

Suspend lvol subsystems

```bash
sbctl volume suspend
    <LVOL_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| LVOL_ID | Logical volume id | string | True |


## Resume lvol subsystems

Resume lvol subsystems

```bash
sbctl volume resume
    <LVOL_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| LVOL_ID | Logical volume id | string | True |


## Create logical volume clone by taking a snapshot and then cloning it.

Create logical volume clone by taking a snapshot and then cloning it.

```bash
sbctl volume clone-lvol
    <VOLUME_ID>
    <CLONE_NAME>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| VOLUME_ID | The logical volume id. | string | True |
| CLONE_NAME | The new logical volume clone name. | string | True |


## Pre-create the target NVMe-oF subsystem for a volume migration. Returns a migration ID (or group ID with --batch) and NVMe connect strings (inaccessible ANA state). Connect the client, then run migrate-continue.

Pre-create the target NVMe-oF subsystem for a volume migration. Returns a migration ID (or group ID with --batch) and NVMe connect strings (inaccessible ANA state). Connect the client, then run migrate-continue.

```bash
sbctl volume migrate
    <VOLUME_ID>
    <TARGET_NODE_ID>
    --ctrl-loss-tmo=<CTRL_LOSS_TMO>
    --host-nqn=<HOST_NQN>
    --batch
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| VOLUME_ID | The volume ID to migrate. With --batch, any member of the shared-namespace subsystem. | string | True |
| TARGET_NODE_ID | The target storage node ID. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --ctrl-loss-tmo| NVMe ctrl-loss-tmo in seconds. Default: `3600`. | integer | False | 3600 |
| --host-nqn| Host NQN for DH-HMAC-CHAP authentication (required when volume has allowed hosts). | string | False | - |
| --batch| Migrate all lvols sharing the same NVMe-oF subsystem as a coordinated group. | marker | False | - |


## Advance a pre-created migration to the snapshot-copy phase and launch the task runner.

Advance a pre-created migration to the snapshot-copy phase and launch the task runner.

```bash
sbctl volume migrate-continue
    <MIGRATION_ID>
    --max-retries=<MAX_RETRIES>
    --deadline=<DEADLINE>
    --batch
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| MIGRATION_ID | The migration ID returned by migrate (or group ID with --batch). | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --max-retries| Maximum retry attempts before aborting. Default: `10`. | integer | False | 10 |
| --deadline| Migration deadline in seconds (0 = no deadline). Default: `14400`. | integer | False | 14400 |
| --batch| ID is a batch migration group ID. | marker | False | - |


## List volume migrations.

List volume migrations.

```bash
sbctl volume migrate-list
    --cluster-id=<CLUSTER_ID>
    --json
```


| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --cluster-id| Filter by cluster id. | string | False | - |
| --json| Print output in json format. | marker | False | - |


## Cancel an active volume migration.

Cancel an active volume migration.

```bash
sbctl volume migrate-cancel
    <MIGRATION_ID>
    --batch
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| MIGRATION_ID | The migration id (or group ID with --batch). | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --batch| ID is a batch migration group ID. | marker | False | - |



## List batch (shared-namespace) migration groups.

List batch (shared-namespace) migration groups.

```bash
sbctl volume migrate-group-list
    --cluster-id=<CLUSTER_ID>
    --json
```


| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --cluster-id| Filter by cluster ID. | string | False | - |
| --json| Print output in JSON format. | marker | False | - |
