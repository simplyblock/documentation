---
title: "Backup Commands"
description: "Backup Commands"
source: "https://docs.simplyblock.io/latest/reference/cli/backup/"
---

# Backup Commands

<!--
This file is generated. Do not edit it by hand.
Run ./doc-builder gen-sbcli-ref from the documentation repository.
-->

```bash
sbctl backup --help
```



Backup Commands



## List all backups.

List all backups.

```bash
sbctl backup list
    --cluster-id=<CLUSTER_ID>
```


| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --cluster-id| The cluster id. | string | False | - |


## Delete all backups for a logical volume.

Delete all backups for a logical volume.

```bash
sbctl backup delete
    <LVOL_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| LVOL_ID | The logical volume id. | string | True |


## Restore a backup to a new logical volume.

Restore a backup to a new logical volume.

```bash
sbctl backup restore
    <BACKUP_ID>
    --lvol=<LVOL>
    --pool=<POOL>
    --node=<NODE>
    --access-key-id=<ACCESS_KEY_ID>
    --secret-access-key=<SECRET_ACCESS_KEY>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| BACKUP_ID | The volume backup id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --lvol| The new logical volume name. | string | True | - |
| --pool| The target pool name or id. | string | True | - |
| --node| The target storage node id. | string | False | - |
| --access-key-id| Access key for the backup's bucket, when it is not this cluster's own. | unknown | False | - |
| --secret-access-key| Secret key for the backup's bucket, when it is not this cluster's own. | unknown | False | - |


## Export backup metadata to a JSON file for cross-cluster restore.

Export backup metadata to a JSON file for cross-cluster restore.

```bash
sbctl backup export
    --cluster-id=<CLUSTER_ID>
    --backup-id=<BACKUP_ID>
    --lvol=<LVOL>
    -o=<O>
```


| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --cluster-id| The cluster id. | string | False | - |
| --backup-id| Export the chain ending at this backup and nothing else, which is the unit a restore needs. | string | False | - |
| --lvol| Filter exports to a specific logical volume name. | string | False | - |
| -o, --output| The output file path. | string | False | - |


## List the backups a bucket contains, reading its manifests. Needs no cluster.

List the backups a bucket contains, reading its manifests. Needs no cluster.

```bash
sbctl backup discover
    --bucket=<BUCKET>
    --region=<REGION>
    --endpoint=<ENDPOINT>
    --access-key-id=<ACCESS_KEY_ID>
    --secret-access-key=<SECRET_ACCESS_KEY>
    --no-verify-tls
    --path-style
```


| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --bucket| The bucket holding the backups. | string | True | - |
| --region| The bucket's region. Omit to let the AWS SDK resolve it. | string | False | - |
| --endpoint| Endpoint of an S3-compatible store, e.g. http://minio:9000. Omit for AWS. | string | False | - |
| --access-key-id| Access key for the bucket. Omit to use the node's instance role. | unknown | False | - |
| --secret-access-key| Secret key for the bucket. Omit to use the node's instance role. | unknown | False | - |
| --no-verify-tls| Skip certificate verification for the endpoint. | marker | False | - |
| --path-style| Use path-style addressing, as MinIO and most S3-compatible stores need. | marker | False | - |


## Register the backups held in a bucket into this cluster.

Register the backups held in a bucket into this cluster.

```bash
sbctl backup import
    --cluster-id=<CLUSTER_ID>
    --bucket=<BUCKET>
    --from-file=<FROM_FILE>
    --region=<REGION>
    --endpoint=<ENDPOINT>
    --access-key-id=<ACCESS_KEY_ID>
    --secret-access-key=<SECRET_ACCESS_KEY>
    --no-verify-tls
    --path-style
```


| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --cluster-id| The target cluster to import into (required for cross-cluster restore). | string | False | - |
| --bucket| Import every backup in this bucket. Give this or --from-file, not both. | string | False | - |
| --from-file| Import the backups in this file, from 'backup export'. It records which bucket each one lives in, so --bucket is neither needed nor accepted. | string | False | - |
| --region| The bucket's region. Omit to let the AWS SDK resolve it. | string | False | - |
| --endpoint| Endpoint of an S3-compatible store, e.g. http://minio:9000. Omit for AWS. | string | False | - |
| --access-key-id| Access key for the bucket. Omit to use the node's instance role. | unknown | False | - |
| --secret-access-key| Secret key for the bucket. Omit to use the node's instance role. | unknown | False | - |
| --no-verify-tls| Skip certificate verification for the endpoint. | marker | False | - |
| --path-style| Use path-style addressing, as MinIO and most S3-compatible stores need. | marker | False | - |


## Create a new backup policy.

Create a new backup policy.

```bash
sbctl backup policy-add
    <CLUSTER_ID>
    <NAME>
    --versions=<VERSIONS>
    --age=<AGE>
    --schedule=<SCHEDULE>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |
| NAME | The policy name. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --versions| The maximum number of backup versions. | integer | False | - |
| --age| Maximum backup age (e.g. 2d, 12h, 1w). | string | False | - |
| --schedule| Auto-backup schedule as space-separated tiers: "15m,4 60m,11 24h,7" (interval,keep_count per tier). | string | False | - |


## Remove a backup policy.

Remove a backup policy.

```bash
sbctl backup policy-remove
    <POLICY_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| POLICY_ID | The backup policy id. | string | True |


## List all backup policies.

List all backup policies.

```bash
sbctl backup policy-list
    --cluster-id=<CLUSTER_ID>
```


| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --cluster-id| The cluster id. | string | False | - |


## Attach a backup policy to a storage pool or logical volume.

Attach a backup policy to a storage pool or logical volume.

```bash
sbctl backup policy-attach
    <POLICY_ID>
    <TARGET_TYPE>
    <TARGET_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| POLICY_ID | The backup policy id. | string | True |
| TARGET_TYPE | The target type. | string | True |
| TARGET_ID | The target id (storage pool or logical volume id). | string | True |


## Detach a backup policy from a storage pool or logical volume.

Detach a backup policy from a storage pool or logical volume.

```bash
sbctl backup policy-detach
    <POLICY_ID>
    <TARGET_TYPE>
    <TARGET_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| POLICY_ID | The backup policy id. | string | True |
| TARGET_TYPE | The target type. | string | True |
| TARGET_ID | The target id (storage pool or logical volume id). | string | True |
