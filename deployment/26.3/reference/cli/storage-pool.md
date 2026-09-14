---
title: "Storage Pool Commands"
description: "Aliases: pool"
source: "https://docs.simplyblock.io/latest/reference/cli/storage-pool/"
---

# Storage Pool Commands

<!--
This file is generated. Do not edit it by hand.
Run ./doc-builder gen-sbcli-ref from the documentation repository.
-->

```bash
sbctl storage-pool --help
```


**Aliases:**  pool 


Storage Pool Commands



## Adds a new storage pool.

Adds a new storage pool.

```bash
sbctl storage-pool add
    <NAME>
    <CLUSTER_ID>
    --pool-max=<POOL_MAX>
    --lvol-max=<LVOL_MAX>
    --max-rw-iops=<MAX_RW_IOPS>
    --max-rw-mbytes=<MAX_RW_MBYTES>
    --max-r-mbytes=<MAX_R_MBYTES>
    --max-w-mbytes=<MAX_W_MBYTES>
    --qos-host=<QOS_HOST>
    --dhchap
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| NAME | The new pool name. | string | True |
| CLUSTER_ID | The cluster id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --pool-max| Pool maximum size: 20M, 20G, 0. Default: `0`. | size | False | 0 |
| --lvol-max| Logical volume maximum size: 20M, 20G, 0. Default: `0`. | size | False | 0 |
| --max-rw-iops| Maximum Read Write IO Per Second. | integer | False | - |
| --max-rw-mbytes| Maximum Read Write Megabytes Per Second. | integer | False | - |
| --max-r-mbytes| Maximum Read Megabytes Per Second. | integer | False | - |
| --max-w-mbytes| Maximum Write Megabytes Per Second. | integer | False | - |
| --qos-host| The node id for QoS pool. | string | False | - |
| --dhchap| Enable DH-HMAC-CHAP authentication for all volumes in the pool. | marker | False | False |


## Sets a storage pool's attributes.

Sets a storage pool's attributes.

```bash
sbctl storage-pool set
    <POOL_ID>
    --pool-max=<POOL_MAX>
    --lvol-max=<LVOL_MAX>
    --max-rw-iops=<MAX_RW_IOPS>
    --max-rw-mbytes=<MAX_RW_MBYTES>
    --max-r-mbytes=<MAX_R_MBYTES>
    --max-w-mbytes=<MAX_W_MBYTES>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| POOL_ID | The storage pool id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --pool-max| Pool maximum size: 20M, 20G. | size | False | - |
| --lvol-max| Logical volume maximum size: 20M, 20G. | size | False | - |
| --max-rw-iops| Maximum Read Write IO Per Second. | integer | False | - |
| --max-rw-mbytes| Maximum Read Write Megabytes Per Second. | integer | False | - |
| --max-r-mbytes| Maximum Read Megabytes Per Second. | integer | False | - |
| --max-w-mbytes| Maximum Write Megabytes Per Second. | integer | False | - |


## Lists all storage pools.

Lists all storage pools.

```bash
sbctl storage-pool list
    --json
    --cluster-id=<CLUSTER_ID>
```


| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --json| Print outputs in json format. | marker | False | - |
| --cluster-id| The cluster id. | string | False | - |


## Gets a storage pool's details.

Gets a storage pool's details.

```bash
sbctl storage-pool get
    <POOL_ID>
    --json
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| POOL_ID | The storage pool id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --json| Print outputs in json format. | marker | False | - |


## Deletes a storage pool.

It is only possible to delete a pool if it is empty (no provisioned logical volumes contained).

```bash
sbctl storage-pool delete
    <POOL_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| POOL_ID | The storage pool id. | string | True |


## Set a storage pool's status to Active.

Set a storage pool's status to Active.

```bash
sbctl storage-pool enable
    <POOL_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| POOL_ID | The storage pool id. | string | True |


## Sets a storage pool's status to Inactive.

Sets a storage pool's status to Inactive.

```bash
sbctl storage-pool disable
    <POOL_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| POOL_ID | The storage pool id. | string | True |


## Gets a storage pool's capacity.

Gets a storage pool's capacity.

```bash
sbctl storage-pool get-capacity
    <POOL_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| POOL_ID | The storage pool id. | string | True |


## Gets a storage pool's I/O statistics.

Gets a storage pool's I/O statistics.

```bash
sbctl storage-pool get-io-stats
    <POOL_ID>
    --history=<HISTORY>
    --records=<RECORDS>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| POOL_ID | The storage pool id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --history| (XXdYYh), list history records (one for every 15 minutes) for XX days and YY hours (up to 10 days in total). | string | False | - |
| --records| The number of records. Default: `20`. | integer | False | 20 |


## Add an allowed host NQN to a storage pool.

Add an allowed host NQN to a storage pool.

```bash
sbctl storage-pool add-host
    <POOL_ID>
    <HOST_NQN>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| POOL_ID | The storage pool id. | string | True |
| HOST_NQN | The host NQN to allow access. | string | True |


## Remove an allowed host NQN from a storage pool.

Remove an allowed host NQN from a storage pool.

```bash
sbctl storage-pool remove-host
    <POOL_ID>
    <HOST_NQN>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| POOL_ID | The storage pool id. | string | True |
| HOST_NQN | The host NQN to remove. | string | True |
