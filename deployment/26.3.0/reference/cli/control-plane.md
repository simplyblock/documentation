---
title: "Control Plane Commands"
description: "Aliases: cp mgmt"
source: "https://docs.simplyblock.io/latest/reference/cli/control-plane/"
---

# Control Plane Commands

<!--
This file is generated. Do not edit it by hand.
Run ./doc-builder gen-sbcli-ref from the documentation repository.
-->

```bash
sbctl control-plane --help
```


**Aliases:**  cp  mgmt 


Control Plane Commands



## Adds a control plane to the cluster (local run).

Adds a control plane to the cluster (local run).

```bash
sbctl control-plane add
    <CLUSTER_IP>
    <CLUSTER_ID>
    <CLUSTER_SECRET>
    --ifname=<IFNAME>
    --mgmt-ip=<MGMT_IP>
    --mode=<MODE>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_IP | The cluster IP address. | string | True |
| CLUSTER_ID | The cluster id. | string | True |
| CLUSTER_SECRET | The cluster secret. | unknown | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --ifname| The management interface name. | string | False | - |
| --mgmt-ip| Management IP address to use for the node (e.g., 192.168.1.10). | string | False | - |
| --mode| The environment to deploy management services. Default: `docker`.<br/><br/>Available Options:<br/>- docker<br/>- kubernetes | string | False | docker |


## Lists all control plane nodes.

Lists all control plane nodes.

```bash
sbctl control-plane list
    --json
```


| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --json| Print outputs in json format. | marker | False | - |


## Removes a control plane node.

Removes a control plane node.

```bash
sbctl control-plane remove
    <NODE_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| NODE_ID | The control plane node id. | string | True |
