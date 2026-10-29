---
title: "Consistency-group backup commands"
description: "Aliases: gb"
source: "https://docs.simplyblock.io/latest/reference/cli/group-backup/"
---

# Consistency-group backup commands

<!--
This file is generated. Do not edit it by hand.
Run ./doc-builder gen-sbcli-ref from the documentation repository.
-->

```bash
sbctl group-backup --help
```


**Aliases:**  gb 


Consistency-group backup commands



## List the cluster's consistency-group backups.

List the cluster's consistency-group backups.

```bash
sbctl group-backup list
    <CLUSTER_ID>
    --json
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | Cluster UUID. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --json, -j| Print output in JSON format. | marker | False | - |


## Show one consistency-group backup and its members.

Show one consistency-group backup and its members.

```bash
sbctl group-backup get
    <GROUP_BACKUP_ID>
    --json
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| GROUP_BACKUP_ID | Group backup id (or uuid). | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --json, -j| Print output in JSON format. | marker | False | - |


## Restore a consistency-group backup into a NEW consistency group, all-or-nothing. Each member volume recovers asynchronously.

Restore a consistency-group backup into a NEW consistency group, all-or-nothing. Each member volume recovers asynchronously.

```bash
sbctl group-backup restore
    <GROUP_BACKUP_ID>
    --name=<NAME>
    --pool=<POOL>
    --node=<NODE>
    --access-key-id=<ACCESS_KEY_ID>
    --secret-access-key=<SECRET_ACCESS_KEY>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| GROUP_BACKUP_ID | Group backup id (or uuid). | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --name| Name of the NEW consistency group to form from the restored volumes. Must not already exist. | string | True | - |
| --pool| The target pool name or id. | string | True | - |
| --node| The target storage node id. Omit to auto-select; every member is pinned to one store. | string | False | - |
| --access-key-id| Access key for the backup's bucket, when it is not this cluster's own. | unknown | False | - |
| --secret-access-key| Secret key for the backup's bucket, when it is not this cluster's own. | unknown | False | - |


## Delete a consistency-group backup: its group manifest and record. Its member backups are retired: merged into the copy of the next generation while that chains against them, deleted once nothing does.

Delete a consistency-group backup: its group manifest and record. Its member backups are retired: merged into the copy of the next generation while that chains against them, deleted once nothing does.

```bash
sbctl group-backup delete
    <GROUP_BACKUP_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| GROUP_BACKUP_ID | Group backup id (or uuid). | string | True |


## Export a consistency-group backup's manifests as a unit, to a JSON file for cross-cluster restore.

Export a consistency-group backup's manifests as a unit, to a JSON file for cross-cluster restore.

```bash
sbctl group-backup export
    <GROUP_BACKUP_ID>
    --cluster-id=<CLUSTER_ID>
    -o=<O>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| GROUP_BACKUP_ID | Group backup id (or uuid). | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --cluster-id| The cluster id. | string | False | - |
| -o, --output| The output file path. | string | False | - |


## List the consistency-group backups a bucket contains, reading its group manifests. Needs no cluster.

List the consistency-group backups a bucket contains, reading its group manifests. Needs no cluster.

```bash
sbctl group-backup discover
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
| --bucket| The bucket holding the group backups. | string | True | - |
| --region| The bucket's region. Omit to let the AWS SDK resolve it. | string | False | - |
| --endpoint| Endpoint of an S3-compatible store, e.g. http://minio:9000. Omit for AWS. | string | False | - |
| --access-key-id| Access key for the bucket. Omit to use the node's instance role. | unknown | False | - |
| --secret-access-key| Secret key for the bucket. Omit to use the node's instance role. | unknown | False | - |
| --no-verify-tls| Skip certificate verification for the endpoint. | marker | False | - |
| --path-style| Use path-style addressing, as MinIO and most S3-compatible stores need. | marker | False | - |


## Register the consistency-group backups held in a bucket, or in an export file, into this cluster.

Register the consistency-group backups held in a bucket, or in an export file, into this cluster.

```bash
sbctl group-backup import
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
| --bucket| Import every group backup in this bucket. Give this or --from-file, not both. | string | False | - |
| --from-file| Import the group backup in this file, from 'group-backup export'. It records which bucket its members live in, so --bucket is neither needed nor accepted. | string | False | - |
| --region| The bucket's region. Omit to let the AWS SDK resolve it. | string | False | - |
| --endpoint| Endpoint of an S3-compatible store, e.g. http://minio:9000. Omit for AWS. | string | False | - |
| --access-key-id| Access key for the bucket. Omit to use the node's instance role. | unknown | False | - |
| --secret-access-key| Secret key for the bucket. Omit to use the node's instance role. | unknown | False | - |
| --no-verify-tls| Skip certificate verification for the endpoint. | marker | False | - |
| --path-style| Use path-style addressing, as MinIO and most S3-compatible stores need. | marker | False | - |
