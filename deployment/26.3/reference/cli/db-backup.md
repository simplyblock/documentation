---
title: "FDB Backup operations"
description: "FDB Backup operations"
source: "https://docs.simplyblock.io/latest/reference/cli/db-backup/"
---

# FDB Backup operations

<!--
This file is generated. Do not edit it by hand.
Run ./doc-builder gen-sbcli-ref from the documentation repository.
-->

```bash
sbctl db-backup --help
```



FDB Backup operations



## Creates an fdb backup

Creates an fdb backup

```bash
sbctl db-backup create
    <CLUSTER_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | Cluster ID to create db backup for | string | True |


## Lists all fdb backups

Lists all fdb backups

```bash
sbctl db-backup list
    <CLUSTER_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | Cluster ID to restore db backup to | string | True |


## get backup status

get backup status

```bash
sbctl db-backup status
```



## restore a backup

restore a backup

```bash
sbctl db-backup restore
    <NAME>
    <CLUSTER_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| NAME | backup class name | string | True |
| CLUSTER_ID | Cluster ID to restore db backup to | string | True |


## Set backup configuration

Set backup configuration

```bash
sbctl db-backup config
    <CLUSTER_ID>
    --backup-path=<BACKUP_PATH>
    --backup-frequency=<BACKUP_FREQUENCY>
    --s3-bucket=<S3_BUCKET>
    --s3-region=<S3_REGION>
    --s3-credentials=<S3_CREDENTIALS>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | Cluster ID to configure db backup for | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --backup-path| local backup path, defaults to /etc/foundationdb/backup | string | False | - |
| --backup-frequency| backup frequency, can be 3h, 1d | string | False | - |
| --s3-bucket| AWS S3 bucket name | string | False | - |
| --s3-region| AWS S3 region | string | False | - |
| --s3-credentials| AWS S3 API key and secret, should be supplied like this: [API_KEY]:[API_SECRET] | string | False | - |
