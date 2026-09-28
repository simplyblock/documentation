---
title: "Consistency Group Commands"
description: "Aliases: cg"
source: "https://docs.simplyblock.io/latest/reference/cli/consistency-group/"
---

# Consistency Group Commands

<!--
This file is generated. Do not edit it by hand.
Run ./doc-builder gen-sbcli-ref from the documentation repository.
-->

```bash
sbctl consistency-group --help
```


**Aliases:**  cg 


Consistency Group Commands



## List the cluster's consistency groups.

List the cluster's consistency groups.

```bash
sbctl consistency-group list
    <CLUSTER_ID>
    --json
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | Cluster UUID. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --json, -j| Print output in JSON format. | marker | False | - |


## List the current members of a consistency group.

List the current members of a consistency group.

```bash
sbctl consistency-group members
    <GROUP_ID>
    --json
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| GROUP_ID | Consistency group id (or uuid). | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --json, -j| Print output in JSON format. | marker | False | - |


## Join an EXISTING volume to a consistency group. The volume must live on the group's pinned node/LVS and in the members' storage pool; a volume that once left the group cannot rejoin (membership is one-way).

Join an EXISTING volume to a consistency group. The volume must live on the group's pinned node/LVS and in the members' storage pool; a volume that once left the group cannot rejoin (membership is one-way).

```bash
sbctl consistency-group add-member
    <GROUP_ID>
    <LVOL_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| GROUP_ID | Consistency group id (or uuid). | string | True |
| LVOL_ID | The logical volume id to join. | string | True |


## Detach a member from a consistency group: closes its epoch one-way, preserving its snapshots in prior generations. The volume itself is untouched.

Detach a member from a consistency group: closes its epoch one-way, preserving its snapshots in prior generations. The volume itself is untouched.

```bash
sbctl consistency-group remove-member
    <GROUP_ID>
    <LVOL_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| GROUP_ID | Consistency group id (or uuid). | string | True |
| LVOL_ID | The logical volume id to detach. | string | True |


## Take ONE crash-consistent snapshot generation across every current member.

Take ONE crash-consistent snapshot generation across every current member.

```bash
sbctl consistency-group snapshot-take
    <GROUP_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| GROUP_ID | Consistency group id (or uuid). | string | True |


## List a consistency group's snapshot generations with expected-versus-present member counts.

List a consistency group's snapshot generations with expected-versus-present member counts.

```bash
sbctl consistency-group snapshot-list
    <GROUP_ID>
    --json
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| GROUP_ID | Consistency group id (or uuid). | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --json, -j| Print output in JSON format. | marker | False | - |


## Delete one generation and all its member snapshots; never the group.

Delete one generation and all its member snapshots; never the group.

```bash
sbctl consistency-group snapshot-delete
    <GROUP_ID>
    <SEQ>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| GROUP_ID | Consistency group id (or uuid). | string | True |
| SEQ | The generation number (group_seq) to delete. | integer | True |


## Clone every member snapshot of a generation into a new volume, optionally forming a new group.

Clone every member snapshot of a generation into a new volume, optionally forming a new group.

```bash
sbctl consistency-group clone
    <GROUP_ID>
    <SEQ>
    --into=<INTO>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| GROUP_ID | Consistency group id (or uuid). | string | True |
| SEQ | The generation number (group_seq) to clone. | integer | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --into| Name of the new consistency group to form from the clones. When omitted, the clones are independent volumes. | string | False | - |
