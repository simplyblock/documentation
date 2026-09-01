---
title: "Cluster Commands"
description: "Cluster Commands"
source: "https://docs.simplyblock.io/latest/reference/cli/cluster/"
---

# Cluster Commands

<!--
This file is generated. Do not edit it by hand.
Run ./doc-builder gen-sbcli-ref from the documentation repository.
-->

```bash
sbctl cluster --help
```



Cluster Commands



## Creates a new cluster.

Created a new control plane cluster with the current node as the primary control plane node.

```bash
sbctl cluster create
    --cap-warn=<CAP_WARN>
    --cap-crit=<CAP_CRIT>
    --prov-cap-warn=<PROV_CAP_WARN>
    --prov-cap-crit=<PROV_CAP_CRIT>
    --ifname=<IFNAME>
    --mgmt-ip=<MGMT_IP>
    --tls-secret-name=<TLS_SECRET_NAME>
    --log-del-interval=<LOG_DEL_INTERVAL>
    --metrics-retention-period=<METRICS_RETENTION_PERIOD>
    --contact-point=<CONTACT_POINT>
    --grafana-endpoint=<GRAFANA_ENDPOINT>
    --data-chunks-per-stripe=<DATA_CHUNKS_PER_STRIPE>
    --parity-chunks-per-stripe=<PARITY_CHUNKS_PER_STRIPE>
    --ha-type=<HA_TYPE>
    --is-single-node
    --mode=<MODE>
    --ingress-host-source=<INGRESS_HOST_SOURCE>
    --dns-name=<DNS_NAME>
    --enable-node-affinity
    --fabric=<FABRIC>
    --strict-node-anti-affinity
    --enable-failure-domain
    --name=<NAME>
    --qpair-count=<QPAIR_COUNT>
    --client-qpair-count=<CLIENT_QPAIR_COUNT>
    --client-data-nic=<CLIENT_DATA_NIC>
    --use-backup=<USE_BACKUP>
    --nvmf-base-port=<NVMF_BASE_PORT>
    --rpc-base-port=<RPC_BASE_PORT>
    --snode-api-port=<SNODE_API_PORT>
    --max-subsys=<MAX_SUBSYS>
    --hugepages-mem=<HUGEPAGES_MEM>
    --vcpu-count=<VCPU_COUNT>
    --hashicorp-vault-url=<HASHICORP_VAULT_URL>
```


| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --cap-warn| The capacity warning level in percent. Default: `89`. | integer | False | 89 |
| --cap-crit| The capacity critical level in percent. Default: `99`. | integer | False | 99 |
| --prov-cap-warn| The capacity warning level in percent. Default: `250`. | integer | False | 250 |
| --prov-cap-crit| The capacity critical level in percent. Default: `500`. | integer | False | 500 |
| --ifname| Management interface name, e.g. eth0. | string | False | - |
| --mgmt-ip| Management IP address to use for the node (e.g., 192.168.1.10). | string | False | - |
| --tls-secret-name| Name of the Kubernetes TLS Secret to be used by the Ingress for HTTPS termination (e.g., my-tls-secret). | string | False | - |
| --log-del-interval| The logging retention policy. Default: `3d`. | string | False | 3d |
| --metrics-retention-period| Retention period for I/O statistics (Prometheus). Default: `7d`. | string | False | 7d |
| --contact-point| The email or slack webhook url to be used for alerting. | string | False |  |
| --grafana-endpoint| The endpoint url for Grafana. | string | False |  |
| --data-chunks-per-stripe| The erasure coding schema parameter k (distributed raid). Default: `1`. | integer | False | 1 |
| --parity-chunks-per-stripe| The erasure coding schema parameter n (distributed raid). Default: `1`. | integer | False | 1 |
| --ha-type| Logical volume HA type (single, ha), default is cluster ha type. Default: `ha`.<br/><br/>Available Options:<br/>- single<br/>- ha | string | False | ha |
| --is-single-node| For single-node clusters only. Default: `false`. | marker | False | False |
| --mode| The environment to deploy management services. Default: `docker`.<br/><br/>Available Options:<br/>- docker<br/>- kubernetes | string | False | docker |
| --ingress-host-source| Ingress host source: 'hostip' for node IP, 'loadbalancer' for external LB, or 'dns' for custom domain. Default: `hostip`.<br/><br/>Available Options:<br/>- hostip<br/>- loadbalancer<br/>- dns | string | False | hostip |
| --dns-name| Fully qualified DNS name to use as the Ingress host (required if --ingress-host-source=dns). | string | False |  |
| --enable-node-affinity| Enable node affinity for storage nodes. | marker | False | - |
| --fabric| The NVMe fabric to use (specify: `tcp`, `rdma`, `tcp,rdma`). Default: `tcp`.<br/><br/>Available Options:<br/>- tcp<br/>- rdma<br/>- tcp,rdma | string | False | tcp |
| --strict-node-anti-affinity| Enable strict node anti affinity for storage nodes. Never more than one chunk is placed on a node. This requires a minimum of _data-chunks-in-stripe + parity-chunks-in-stripe + 1_ nodes in the cluster. | marker | False | - |
| --enable-failure-domain| Enable failure-domain anti-affinity. Each storage node must then be added with a --failure-domain tag (rack/cabinet/DC); data, journal and secondary/tertiary copies are spread across distinct failure domains (best-effort). Deploy-time only: a cluster cannot be upgraded into this feature, it must be redeployed. | marker | False | - |
| --name, -n| Assigns a name to the newly created cluster. | string | False | - |
| --qpair-count| Increase for clusters with few but very large logical volumes or decrease for clusters with a large number of very small logical volumes. | range(0..128) | False | 32 |
| --client-qpair-count| Increase for clusters with few but very large logical volumes or decrease for clusters with a large number of very small logical volumes. | range(0..128) | False | 3 |
| --client-data-nic| Network interface name from client to use for logical volume connection. | string | False | - |
| --use-backup| The path to JSON file with S3/MinIO backup configuration. | string | False | - |
| --nvmf-base-port| Base port for all NVMe-oF listeners (lvol, hublvol, device). Default: `4420`. | integer | False | 4420 |
| --rpc-base-port| The base port for SPDK JSON-RPC. Default: `8080`. | integer | False | 8080 |
| --snode-api-port| The SNodeAPI/firewall port (one per host IP). Default: `50001`. | integer | False | 50001 |
| --max-subsys| Cluster-wide ceiling on nvmf subsystems per storage node. 75 is a hard product limit and larger values are rejected. Set here rather than per node so every node in the cluster is sized alike; a node adopts a change on its next restart. | integer | False | 0 |
| --hugepages-mem| Huge-page memory floor per storage node, e.g. 4G. Cluster-wide; a node adopts it on its next restart. | string | False |  |
| --vcpu-count| Absolute core budget for SPDK on every storage node, replacing the old cores-percentage: a percentage meant different things on different hardware, a count does not. One core beyond this is required for the system, so a node with fewer than count+1 vCPUs is refused rather than silently under-provisioned. | integer | False | 0 |
| --hashicorp-vault-url| Hashicorp vault URL for storing encryption keys for this cluster | string | False | - |


## Adds a new cluster.

Adds a new cluster.

```bash
sbctl cluster add
    --cap-warn=<CAP_WARN>
    --cap-crit=<CAP_CRIT>
    --prov-cap-warn=<PROV_CAP_WARN>
    --prov-cap-crit=<PROV_CAP_CRIT>
    --data-chunks-per-stripe=<DATA_CHUNKS_PER_STRIPE>
    --parity-chunks-per-stripe=<PARITY_CHUNKS_PER_STRIPE>
    --ha-type=<HA_TYPE>
    --enable-node-affinity
    --fabric=<FABRIC>
    --is-single-node
    --qpair-count=<QPAIR_COUNT>
    --client-qpair-count=<CLIENT_QPAIR_COUNT>
    --strict-node-anti-affinity
    --enable-failure-domain
    --name=<NAME>
    --client-data-nic=<CLIENT_DATA_NIC>
    --use-backup=<USE_BACKUP>
    --nvmf-base-port=<NVMF_BASE_PORT>
    --rpc-base-port=<RPC_BASE_PORT>
    --snode-api-port=<SNODE_API_PORT>
    --max-subsys=<MAX_SUBSYS>
    --hugepages-mem=<HUGEPAGES_MEM>
    --vcpu-count=<VCPU_COUNT>
    --hashicorp-vault-url=<HASHICORP_VAULT_URL>
```


| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --cap-warn| The capacity warning level in percent. Default: `89`. | integer | False | 89 |
| --cap-crit| The capacity critical level in percent. Default: `99`. | integer | False | 99 |
| --prov-cap-warn| The capacity warning level in percent. Default: `250`. | integer | False | 250 |
| --prov-cap-crit| The capacity critical level in percent. Default: `500`. | integer | False | 500 |
| --data-chunks-per-stripe| The erasure coding schema parameter k (distributed raid). Default: `1`. | integer | False | 1 |
| --parity-chunks-per-stripe| The erasure coding schema parameter n (distributed raid). Default: `1`. | integer | False | 1 |
| --ha-type| Logical volume HA type (single, ha), default is cluster single type. Default: `ha`.<br/><br/>Available Options:<br/>- single<br/>- ha | string | False | ha |
| --enable-node-affinity| Enables node affinity for storage nodes. | marker | False | - |
| --fabric| Fabric: tcp, rdma or both (specify: tcp, rdma). Default: `tcp`.<br/><br/>Available Options:<br/>- tcp<br/>- rdma<br/>- tcp,rdma | string | False | tcp |
| --is-single-node| For single-node clusters only. Default: `false`. | marker | False | False |
| --qpair-count| Increase for clusters with few but very large logical volumes or decrease for clusters with a large number of very small logical volumes. | range(0..128) | False | 32 |
| --client-qpair-count| Increase for clusters with few but very large logical volumes or decrease for clusters with a large number of very small logical volumes. | range(0..128) | False | 3 |
| --strict-node-anti-affinity| Enable strict node anti affinity for storage nodes. Never more than one chunk is placed on a node. This requires a minimum of _data-chunks-in-stripe + parity-chunks-in-stripe + 1_ nodes in the cluster." | marker | False | - |
| --enable-failure-domain| Enable failure-domain anti-affinity. Each storage node must then be added with a --failure-domain tag (rack/cabinet/DC); data, journal and secondary/tertiary copies are spread across distinct failure domains (best-effort). Deploy-time only: a cluster cannot be upgraded into this feature, it must be redeployed. | marker | False | - |
| --name, -n| Assigns a name to the newly created cluster. | string | False | - |
| --client-data-nic| Network interface name from client to use for logical volume connection. | string | False | - |
| --use-backup| The path to JSON file with S3/MinIO backup configuration. | string | False | - |
| --nvmf-base-port| Base port for all NVMe-oF listeners (lvol, hublvol, device). Default: `4420`. | integer | False | 4420 |
| --rpc-base-port| The base port for SPDK JSON-RPC. Default: `8080`. | integer | False | 8080 |
| --snode-api-port| The SNodeAPI/firewall port (one per host IP). Default: `50001`. | integer | False | 50001 |
| --max-subsys| Cluster-wide ceiling on nvmf subsystems per storage node. 75 is a hard product limit and larger values are rejected. Set here rather than per node so every node in the cluster is sized alike; a node adopts a change on its next restart. | integer | False | 0 |
| --hugepages-mem| Huge-page memory floor per storage node, e.g. 4G. Cluster-wide; a node adopts it on its next restart. | string | False |  |
| --vcpu-count| Absolute core budget for SPDK on every storage node, replacing the old cores-percentage: a percentage meant different things on different hardware, a count does not. One core beyond this is required for the system, so a node with fewer than count+1 vCPUs is refused rather than silently under-provisioned. | integer | False | 0 |
| --hashicorp-vault-url| Hashicorp vault URL for storing encryption keys for this cluster | string | False | - |


## Stops the cluster accepting object lifecycle operations: creation, deletion and modification of volumes, snapshots, clones and pools. Read paths and the cluster's own maintenance are unaffected.

Stops the cluster accepting object lifecycle operations: creation, deletion and modification of volumes, snapshots, clones and pools. Read paths and the cluster's own maintenance are unaffected.

```bash
sbctl cluster op-stop
    <CLUSTER_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |


## Resumes object lifecycle operations on the cluster.

Resumes object lifecycle operations on the cluster.

```bash
sbctl cluster op-start
    <CLUSTER_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |


## Activates a cluster.


Once a cluster has sufficient nodes added, it needs to be activated. Can also be used to re-activate a suspended cluster.

```bash
sbctl cluster activate
    <CLUSTER_ID>
    --force
    --force-lvstore-create
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --force| Force recreate distr and lv stores. | marker | False | - |
| --force-lvstore-create| Force recreate lv stores. | marker | False | - |


## Shows the cluster list.

Shows the cluster list.

```bash
sbctl cluster list
    --json
```


| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --json| Print json output. | marker | False | - |


## Shows a cluster's status.

Shows a cluster's status.

```bash
sbctl cluster status
    <CLUSTER_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |


## Create lvstore on newly added nodes to the cluster.

Create lvstore on newly added nodes to the cluster.

```bash
sbctl cluster complete-expand
    <CLUSTER_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |


## Shows a cluster's statistics.

Shows a cluster's statistics.

```bash
sbctl cluster show
    <CLUSTER_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |


## Gets a cluster's information.

Gets a cluster's information.

```bash
sbctl cluster get
    <CLUSTER_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |



## Gets a cluster's capacity.

Gets a cluster's capacity.

```bash
sbctl cluster get-capacity
    <CLUSTER_ID>
    --json
    --history=<HISTORY>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --json| Print json output. | marker | False | - |
| --history| (XXdYYh), list history records (one for every 15 minutes) for XX days and YY hours (up to 10 days in total). | string | False | - |


## Gets a cluster's I/O statistics.

Gets a cluster's I/O statistics.

```bash
sbctl cluster get-io-stats
    <CLUSTER_ID>
    --records=<RECORDS>
    --history=<HISTORY>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --records| The number of records. Default: `20`. | integer | False | 20 |
| --history| (XXdYYh), list history records (one for every 15 minutes) for XX days and YY hours (up to 10 days in total). | string | False | - |


## Returns a cluster's status logs.

Returns a cluster's status logs.

```bash
sbctl cluster get-logs
    <CLUSTER_ID>
    --json
    --limit=<LIMIT>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --json| Return JSON formatted logs. | marker | False | - |
| --limit| Show last number of logs, default 50. Default: `50`. | integer | False | 50 |


## Gets a cluster's secret.

Gets a cluster's secret.

```bash
sbctl cluster get-secret
    <CLUSTER_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |


## Updates a cluster's secret.

Updates a cluster's secret.

```bash
sbctl cluster update-secret
    <CLUSTER_ID>
    <SECRET>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |
| SECRET | The new 20 characters password. | unknown | True |


## Updates a cluster's fabric.

Updates a cluster's fabric.

```bash
sbctl cluster update-fabric
    <CLUSTER_ID>
    <FABRIC>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |
| FABRIC | Fabric: tcp, rdma or both (specify: tcp, rdma). Default: `tcp`. | string | True |


## Checks a cluster's health.

Checks a cluster's health.

```bash
sbctl cluster check
    <CLUSTER_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |


## Updates a cluster to new version.

Updates a the control plane to a new version. To update the storage nodes, they have to be shutdown and restarted. This can be done in a rolling manner. Attention: verify that an upgrade path is available and has been tested!"

```bash
sbctl cluster update
    <CLUSTER_ID>
    --cp-only=<CP_ONLY>
    --spdk-image=<SPDK_IMAGE>
    --mgmt-image=<MGMT_IMAGE>
    --max-subsys=<MAX_SUBSYS>
    --hugepages-mem=<HUGEPAGES_MEM>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --cp-only| Update the control plane only. Default: `false`. | boolean | False | False |
| --spdk-image| Restart the storage nodes using the provided image. | string | False | - |
| --mgmt-image| Restart the management services using the provided image. | string | False | - |
| --max-subsys| Change the cluster-wide max nvmf subsystems per storage node. Applied by each node on its next restart. Given alone, no image update runs. | integer | False | - |
| --hugepages-mem| Change the cluster-wide huge-page memory floor per storage node, e.g. 4G. Applied by each node on its next restart. Given alone, no image update runs. | string | False | - |


## Completes a cluster upgrade.

Runs the completion step of a cluster upgrade started with `cluster update`: resumes JC compression on all storage nodes (deferred to a resume task on nodes with running data migrations) and stamps the installed release. All storage nodes must be online.

```bash
sbctl cluster upgrade-complete
    <CLUSTER_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |


## Initiates a graceful shutdown of a cluster's storage nodes.

Initiates a graceful shutdown of a cluster's storage nodes.

```bash
sbctl cluster graceful-shutdown
    <CLUSTER_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |


## Performs a full cluster restart: shuts down every node that is not offline, restarts all nodes in parallel and reactivates the cluster.

Performs a full cluster restart: shuts down every node that is not offline, restarts all nodes in parallel and reactivates the cluster.

```bash
sbctl cluster restart
    <CLUSTER_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |


## Initiates a graceful startup of a cluster's storage nodes.

Initiates a graceful startup of a cluster's storage nodes.

```bash
sbctl cluster graceful-startup
    <CLUSTER_ID>
    --clear-data
    --spdk-image=<SPDK_IMAGE>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --clear-data| Clear Alceml data. | marker | False | - |
| --spdk-image| The SPDK image URI. | string | False | - |


## Lists tasks of a cluster.

Lists tasks of a cluster.

```bash
sbctl cluster list-tasks
    <CLUSTER_ID>
    --limit=<LIMIT>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --limit| Show last number of tasks, default 50. Default: `50`. | integer | False | 50 |


## Cancels task by task id.

Cancels task by task id.

```bash
sbctl cluster cancel-task
    <TASK_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| TASK_ID | The cluster task id. | string | True |


## Get rebalancing subtasks list.

Get rebalancing subtasks list.

```bash
sbctl cluster get-subtasks
    <TASK_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| TASK_ID | The cluster task id. | string | True |


## Deletes a cluster.

This is only possible, if no storage nodes and pools are attached to the cluster

```bash
sbctl cluster delete
    <CLUSTER_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |



## Enable cluster-wide per-chunk data placement-binding for distrib bdevs (forward-only upgrade; --disable is reserved for debug).

Preflight: every storage node must be ONLINE; the cluster must be ACTIVE and not rebalancing. The runtime distr_shared_placement RPC is dispatched to every online node, then the flag is persisted on the cluster row and on every node's lvstore_stack distrib entries so subsequent restarts re-create with the new mode.

```bash
sbctl cluster set-shared-placement
    <CLUSTER_ID>
    --disable
    --force
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --disable| Reverse transition (per-chunk -> per-page). Debug only; only safe on a balanced or empty bdev. Requires --force. | marker | False | - |
| --force| Bypass the rebalancing / non-online-node guards. Required when --disable is passed. | marker | False | - |


## Assigns or changes a name to a cluster

Assigns or changes a name to a cluster

```bash
sbctl cluster change-name
    <CLUSTER_ID>
    <NAME>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |
| NAME | The new cluster name. | string | True |


## DEPRECATED: use replication-target-add and replication-policy-add. Assigns the single snapshot replication target cluster.

DEPRECATED: use replication-target-add and replication-policy-add. Assigns the single snapshot replication target cluster.

```bash
sbctl cluster add-replication
    <CLUSTER_ID>
    <TARGET_CLUSTER_ID>
    --timeout=<TIMEOUT>
    --target-pool=<TARGET_POOL>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | Cluster id | string | True |
| TARGET_CLUSTER_ID | Target Cluster id | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --timeout| Snapshot replication network timeout | integer | False | 3600 |
| --target-pool| Target cluster pool ID or name | string | False | - |


## Adds a named replication destination to a cluster (several are allowed)

Adds a named replication destination to a cluster (several are allowed)

```bash
sbctl cluster replication-target-add
    <CLUSTER_ID>
    <NAME>
    <TARGET_CLUSTER_ID>
    --target-pool=<TARGET_POOL>
    --timeout=<TIMEOUT>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | Source cluster id | string | True |
| NAME | Name of the replication target, unique per source cluster | string | True |
| TARGET_CLUSTER_ID | Destination cluster id | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --target-pool| Pool on the destination cluster (ID or name). Stored as a UUID. | string | False | - |
| --timeout| Replication network timeout in seconds. Default: `600`. | integer | False | - |


## Lists the replication targets of a cluster

Lists the replication targets of a cluster

```bash
sbctl cluster replication-target-list
    --cluster-id=<CLUSTER_ID>
    --json
```


| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --cluster-id| Source cluster id | string | False | - |
| --json| Print outputs in json format. | marker | False | - |


## Removes a replication target. Refused while a policy still uses it.

Removes a replication target. Refused while a policy still uses it.

```bash
sbctl cluster replication-target-remove
    <TARGET_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| TARGET_ID | Replication target id | string | True |


## Fails over EVERY volume replicating to this target (site loss)

Fails over EVERY volume replicating to this target (site loss)

```bash
sbctl cluster replication-target-failover
    <TARGET_ID>
    --json
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| TARGET_ID | Replication target id | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --json| Print outputs in json format. | marker | False | - |


## Adds a replication policy on a target, defining the replication cadence

Adds a replication policy on a target, defining the replication cadence

```bash
sbctl cluster replication-policy-add
    <CLUSTER_ID>
    <NAME>
    --target=<TARGET>
    --interval-min=<INTERVAL_MIN>
    --mode=<MODE>
    --keep=<KEEP>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | Source cluster id | string | True |
| NAME | Name of the policy, unique per source cluster | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --target| Replication target id or name | string | True | - |
| --interval-min| Cadence: minutes between internal replication snapshots. 0 replicates user snapshots only. Default: `1`. | integer | False | - |
| --mode| Replication mode. Default: `failover`.<br/><br/>Available Options:<br/>- failover<br/>- migration | string | False | - |
| --keep| Replicated internal snapshots to retain on each side. Minimum (and default): `2`. | integer | False | - |


## Lists the replication policies of a cluster

Lists the replication policies of a cluster

```bash
sbctl cluster replication-policy-list
    --cluster-id=<CLUSTER_ID>
    --json
```


| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --cluster-id| Source cluster id | string | False | - |
| --json| Print outputs in json format. | marker | False | - |


## Removes a replication policy. Refused while a volume still follows it.

Removes a replication policy. Refused while a volume still follows it.

```bash
sbctl cluster replication-policy-remove
    <POLICY_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| POLICY_ID | Replication policy id | string | True |


## Fails over EVERY volume following this policy

Fails over EVERY volume following this policy

```bash
sbctl cluster replication-policy-failover
    <POLICY_ID>
    --json
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| POLICY_ID | Replication policy id | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --json| Print outputs in json format. | marker | False | - |
