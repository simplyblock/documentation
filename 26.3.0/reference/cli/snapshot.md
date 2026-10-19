---
title: "Snapshot Commands"
description: "Snapshot Commands"
source: "https://docs.simplyblock.io/latest/reference/cli/snapshot/"
---

# Snapshot Commands

<!--
This file is generated. Do not edit it by hand.
Run ./doc-builder gen-sbcli-ref from the documentation repository.
-->

```bash
sbctl snapshot --help
```



Snapshot Commands



## Creates a new snapshot.

Creates a new snapshot.

```bash
sbctl snapshot add
    <VOLUME_ID>
    <NAME>
    --backup
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| VOLUME_ID | The logical volume id. | string | True |
| NAME | The new snapshot name. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --backup| Also create an S3 backup of this snapshot. | marker | False | - |


## Lists all snapshots.

Lists all snapshots.

```bash
sbctl snapshot list
    --lvol-id=<LVOL_ID>
    --node-id=<NODE_ID>
    --pool=<POOL>
    --cluster-id=<CLUSTER_ID>
    --with-details
    --json
```


| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --lvol-id, -l| List snapshots for a specific logical volume. | string | False | - |
| --node-id, -n| List snapshots for a specific node uuid | string | False | - |
| --pool, -p| List snapshots in particular pool id or name. | string | False | - |
| --cluster-id, -c| Filter snapshots by cluster UUID | string | False | - |
| --with-details, -w| List snapshots with replicate and chaining details | marker | False | - |
| --json, -j| List snapshots in JSON format | marker | False | - |


## Deletes a snapshot.

Deletes a snapshot.

```bash
sbctl snapshot delete
    <SNAPSHOT_ID>
    --force
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| SNAPSHOT_ID | The snapshot id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --force| Force remove. | marker | False | - |


## Check a snapshot health

Check a snapshot health

```bash
sbctl snapshot check
    <SNAPSHOT_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| SNAPSHOT_ID | Snapshot id | string | True |


## Provisions a new logical volume from an existing snapshot.

Provisions a new logical volume from an existing snapshot.

```bash
sbctl snapshot clone
    <SNAPSHOT_ID>
    <LVOL_NAME>
    --resize=<RESIZE>
    --namespaced=<NAMESPACED>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| SNAPSHOT_ID | The snapshot id. | string | True |
| LVOL_NAME | The logical volume name. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --resize| New logical volume size: 10M, 10G, 10(bytes). Can only increase. Default: `0`. | size | False | 0 |
| --namespaced| Adds this LVol as a namespace on any available subsystem, if not found then create a new subsystem. Default: `false`. | boolean | False | True |


## Lists snapshots replication status

Lists snapshots replication status

```bash
sbctl snapshot replication-status
    <CLUSTER_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | Cluster UUID | string | True |


## Delete replicated version of a snapshot

Delete replicated version of a snapshot

```bash
sbctl snapshot delete-replication-only
    <SNAPSHOT_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| SNAPSHOT_ID | Snapshot UUID | string | True |


## Gets a snapshot information

Gets a snapshot information

```bash
sbctl snapshot get
    <SNAPSHOT_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| SNAPSHOT_ID | Snapshot UUID | string | True |



## Create an S3 backup of an existing snapshot.

Create an S3 backup of an existing snapshot.

```bash
sbctl snapshot backup
    <SNAPSHOT_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| SNAPSHOT_ID | The snapshot id. | string | True |
