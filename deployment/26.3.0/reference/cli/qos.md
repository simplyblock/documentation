---
title: "QoS Commands"
description: "QoS Commands"
source: "https://docs.simplyblock.io/latest/reference/cli/qos/"
---

# QoS Commands

<!--
This file is generated. Do not edit it by hand.
Run ./doc-builder gen-sbcli-ref from the documentation repository.
-->

```bash
sbctl qos --help
```



QoS Commands



## Creates a new QoS class

Creates a new QoS class

```bash
sbctl qos add
    <NAME>
    <WEIGHT>
    <CLUSTER_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| NAME | QoS class name | string | True |
| WEIGHT | QoS class weight | integer | True |
| CLUSTER_ID | The cluster id. | string | True |


## Lists all qos classes.

Lists all qos classes.

```bash
sbctl qos list
    <CLUSTER_ID>
    --json
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --json| Print json output. | marker | False | - |


## Delete a class.

Delete a class.

```bash
sbctl qos delete
    <NAME>
    <CLUSTER_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| NAME | QoS class name | string | True |
| CLUSTER_ID | The cluster id. | string | True |
