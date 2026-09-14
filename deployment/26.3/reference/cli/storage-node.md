---
title: "Storage Node Commands"
description: "Aliases: sn"
source: "https://docs.simplyblock.io/latest/reference/cli/storage-node/"
---

# Storage Node Commands

<!--
This file is generated. Do not edit it by hand.
Run ./doc-builder gen-sbcli-ref from the documentation repository.
-->

```bash
sbctl storage-node --help
```


**Aliases:**  sn 


Storage Node Commands



## Prepares a host to be used as a storage node.

Runs locally on to-be storage node hosts. Installs storage node dependencies and prepares it to be used as a storage node. Only required, in standalone deployment outside of Kubernetes.


```bash
sbctl storage-node deploy
    --ifname=<IFNAME>
    --isolate-cores
```


| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --ifname| The network interface to be used for communication between the control plane and the storage node. | string | False | - |
| --isolate-cores| Isolates cores in kernel args for the provided CPU mask. Default: `false`. | marker | False | False |


## Prepare a configuration file to be used when adding the storage node.

Runs locally on to-be storage node hosts. Reads system information (CPUs topology, NVME devices) and prepares yaml config to be used when adding the storage node.


```bash
sbctl storage-node configure
    --nodes-per-socket=<NODES_PER_SOCKET>
    --sockets-to-use=<SOCKETS_TO_USE>
    --pci-allowed=<PCI_ALLOWED>
    --pci-blocked=<PCI_BLOCKED>
    --device-model=<DEVICE_MODEL>
    --size-range=<SIZE_RANGE>
    --nvme-names=<NVME_NAMES>
    --force
    --calculate-hp-only
    --number-of-devices=<NUMBER_OF_DEVICES>
```


| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --nodes-per-socket| The number of each node to be added per each socket. Default: `1`. | integer | False | 1 |
| --sockets-to-use| System socket to use when adding storage nodes. Comma-separated list: e.g. 0,1 | string | False | 0 |
| --pci-allowed| Storage PCI addresses to use for storage devices(Normal address and full address are accepted). Comma-separated list: e.g. 0000:00:01.0,00:02.0 | string | False |  |
| --pci-blocked| Storage PCI addresses to not use for storage devices(Normal address and full address are accepted). Comma-separated list: e.g. 0000:00:01.0,00:02.0 | string | False |  |
| --device-model| NVMe SSD model string, example: --model PM1628. Can be used alone to filter NVMe devices by model, or combined with --size-range: if both are given, only devices matching both filters are selected. | string | False |  |
| --size-range| NVMe SSD device size range separated by -, can be X(m,g,t) or bytes as integer, example: --size-range 50G-1T or --size-range 1232345-67823987. Can be used alone to filter NVMe devices by size range, or combined with --device-model: if both are given, only devices matching both filters are selected. | string | False |  |
| --nvme-names| Comma separated list of nvme namespace names like nvme0n1,nvme1n1... | string | False |  |
| --force| Force format detected or passed nvme pci address to 4K and clean partitions. | marker | False | - |
| --calculate-hp-only| Calculate the minimum required huge pages, it depends on the following params: --sockets-to-use, --nodes-per-socket, --number-of-devices. Subsystem count and the vCPU budget are cluster-level settings. | marker | False | - |
| --number-of-devices| Number of devices that will be used on this host. For calculating huge pages memory only. | integer | False | - |


## Upgrade the automated configuration file with new changes of cpu mask or storage devices.

Regenerate the core distribution and auto calculation according to changes in cpu_mask and ssd_pcis only


```bash
sbctl storage-node configure-upgrade
```



## Cleans a previous simplyblock deploy (local run).

Run locally on storage nodes and control plane hosts. Remove a previous deployment to support a fresh scratch-deployment of cluster software.


```bash
sbctl storage-node deploy-cleaner
```



## Clean devices stored in /etc/simplyblock/sn_config_file (local run)

Run locally on storage nodes to clean nvme devices and free them.


```bash
sbctl storage-node clean-devices
    --config-path=<CONFIG_PATH>
    --format-4k
```


| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --config-path| The config path to read stored nvme devices from. Default: `/etc/simplyblock/sn_config_file`. | string | False | /etc/simplyblock/sn_config_file |
| --format-4k| Force format nvme devices with 4K. | marker | False | - |


## Adds a storage node by its IP address.

Adds a storage node by its IP address.

```bash
sbctl storage-node add-node
    <CLUSTER_ID>
    <NODE_ADDR>
    <IFNAME>
    --journal-partition=<JOURNAL_PARTITION>
    --enable-journal-device
    --format-4k
    --data-nics=<DATA_NICS>
    --ha-jm-count=<HA_JM_COUNT>
    --failure-domain=<FAILURE_DOMAIN>
    --namespace=<NAMESPACE>
    --spdk-sys-mem=<SPDK_SYS_MEM>
    --expansion
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| CLUSTER_ID | The cluster id. | string | True |
| NODE_ADDR | Address of storage node api to add, like <node-ip>:5000. | string | True |
| IFNAME | The management interface name. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --journal-partition| 1: Auto-create small partitions for journal on nvme devices. 0: use a separate (the smallest) nvme device of the node for journal. The journal needs a maximum of 3 percent of total available raw disk space. Default: `1`.<br/><br/>Available Options:<br/>- 0<br/>- 1 | integer | False | 1 |
| --enable-journal-device| Enables the use of a separate (the smallest) NVMe device of the node for the journal. Otherwise, the journal uses a maximum of 3% of total available raw disk space across all NVMe devices. | marker | False | False |
| --format-4k| Force format nvme devices with 4K. | marker | False | - |
| --data-nics| Storage network interface names, e.g. eth0,eth1 | unknown | False | - |
| --ha-jm-count| HA JM count. Defaults to 4 for FT=2 clusters, otherwise 3. | integer | False | - |
| --failure-domain| The failure-domain id (a non-negative integer identifying the rack/cabinet/DC) this node belongs to. Required when the cluster was created with --enable-failure-domain; must be omitted otherwise. | integer | False | - |
| --namespace| The Kubernetes namespace to deploy on. | string | False | - |
| --spdk-sys-mem| System memory reserved for non-SPDK use (e.g. 2G, 4096M). Overrides the auto-calculated minimum_sys_memory. If not set, the value is derived from the node configuration. | string | False | - |
| --expansion| After adding the node, integrate it into the cluster by re-homing existing secondary/tertiary roles. Use this to add a single node to an FTT2 cluster instead of staging FTT+1 nodes at once. | marker | False | False |


## Deletes a storage node object from the state database.

Deletes a storage node object from the state database. It must only be used on clusters without any logical volumes. Warning: This is dangerous and could lead to unstable cluster if used on active cluster.

```bash
sbctl storage-node delete
    <NODE_ID>
    --force
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| NODE_ID | Storage node id | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --force| Force delete storage node from DB. Ensure you know what you're doing. | marker | False | - |


## Removes a storage node from the cluster (inverse of cluster expansion). The node must be ONLINE and all other nodes ONLINE; it must host no logical volumes or snapshots (migrate those first). Runs as a background task: shuts the node down, rewires LVS replicas onto other nodes, then removes, fails and migrates its devices before marking the node removed.

Removes a storage node from the cluster (inverse of cluster expansion). The node must be ONLINE and all other nodes ONLINE; it must host no logical volumes or snapshots (migrate those first). Runs as a background task: shuts the node down, rewires LVS replicas onto other nodes, then removes, fails and migrates its devices before marking the node removed.

```bash
sbctl storage-node remove
    <NODE_ID>
    --force-remove
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| NODE_ID | Storage node id | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --force-remove| Cancel any active tasks on the node before starting removal. | marker | False | - |


## Lists all storage nodes.

Lists all storage nodes.

```bash
sbctl storage-node list
    --cluster-id=<CLUSTER_ID>
    --json
```


| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --cluster-id| The cluster id. | string | False | - |
| --json| Print outputs in json format. | marker | False | - |


## Gets a storage node's information.

Gets a storage node's information.

```bash
sbctl storage-node get
    <NODE_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| NODE_ID | Storage node id | string | True |


## Restarts a storage node.

A storage node is required to be _offline_ to be restarted. All functions and device drivers will be reset as a result of the restart. New physical devices can only be added with a storage node restart. During restart, the node will not accept any I/O.


```bash
sbctl storage-node restart
    <NODE_ID>
    --node-addr=<NODE_ADDR>
    --force
    --ssd-pcie=<SSD_PCIE>
    --force-lvol-recreate
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| NODE_ID | Storage node id | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --node-addr, --node-ip| Allows to restart an existing storage node on new host or hardware. Devices attached to storage nodes have to be attached to new hosts. Otherwise, they have to be marked as failed and removed from cluster. Triggers a pro-active migration of data from those devices onto other storage nodes.<br><br> The provided value must be presented in the form of _IP:PORT_. Be default the port number is _5000_. | string | False | - |
| --force| Force restart. | marker | False | - |
| --ssd-pcie| New Nvme PCIe address to add to the storage node. Can be more than one. | string | False |  |
| --force-lvol-recreate| Force logical volume recreation on node restart even if the logical volume bdev was not recovered. Default: `False`. | marker | False | False |


## Exclude node from lvol allocation.

Exclude node from lvol allocation.

```bash
sbctl storage-node suspend
    <NODE_ID>
    --force
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| NODE_ID | Storage node id | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --force| Force suspend | marker | False | False |


## Initiates a storage node shutdown.

Once the command is issued, the node will stop accepting IO,but IO, which was previously received, will still be processed. In a high-availability setup, this will not impact operations.

```bash
sbctl storage-node shutdown
    <NODE_ID>
    --force
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| NODE_ID | Storage node id | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --force| Force node shutdown. | marker | False | - |


## Gets storage node IO statistics.

Gets storage node IO statistics.

```bash
sbctl storage-node get-io-stats
    <NODE_ID>
    --history=<HISTORY>
    --records=<RECORDS>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| NODE_ID | Storage node id | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --history| List history records -one for every 15 minutes- for XX days and YY hours -up to 10 days in total-, format: XXdYYh. | string | False | - |
| --records| The number of records. Default: `20`. | integer | False | 20 |


## Gets a storage node's capacity statistics.

Gets a storage node's capacity statistics.

```bash
sbctl storage-node get-capacity
    <NODE_ID>
    --history=<HISTORY>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| NODE_ID | Storage node id | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --history| List history records -one for every 15 minutes- for XX days and YY hours -up to 10 days in total-, format: XXdYYh. | string | False | - |


## Lists storage devices.

Lists storage devices.

```bash
sbctl storage-node list-devices
    <NODE_ID>
    --json
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| NODE_ID | Storage node id | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --json| Print outputs in json format. | marker | False | - |




## Gets storage device by its id.

Gets storage device by its id.

```bash
sbctl storage-node get-device
    <DEVICE_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| DEVICE_ID | The storage device id. | string | True |


## Restarts a storage device.

A previously logically or physically removed or unavailable device, which has been re-inserted, may be returned into online state. If the device is not physically present, accessible or healthy, it will flip back into unavailable state again.

```bash
sbctl storage-node restart-device
    <DEVICE_ID>
    --force
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| DEVICE_ID | The storage device id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --force| Force restart. | marker | False | - |


## Adds a new storage device.

Adds a device, including a previously detected device (currently in "new" state) into cluster and launches an auto-rebalancing background process in which some cluster capacity is re-distributed to this newly added device.

```bash
sbctl storage-node add-device
    <DEVICE_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| DEVICE_ID | The storage device id. | string | True |


## Logically removes a storage device.

Logical removes a storage device. The device will become unavailable, irrespectively if it was physically removed from the server. This function can be used if auto-detection of removal did not work or if the device must be maintained while remaining inserted into the server.

```bash
sbctl storage-node remove-device
    <DEVICE_ID>
    --force
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| DEVICE_ID | The storage device id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --force| Force device remove. | marker | False | - |


## Sets storage device to failed state.

Sets a storage device to state failed. This command can be used, if an administrator believes that the device must be replaced. Attention: a failed state is final, meaning, all data on the device will be automatically recovered to other devices in the cluster.

```bash
sbctl storage-node set-failed-device
    <DEVICE_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| DEVICE_ID | The storage device id. | string | True |


## Gets a device's capacity.

Gets a device's capacity.

```bash
sbctl storage-node get-capacity-device
    <DEVICE_ID>
    --history=<HISTORY>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| DEVICE_ID | The storage device id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --history| List history records -one for every 15 minutes- for XX days and YY hours -up to 10 days in total-, format: XXdYYh. | string | False | - |


## Gets a device's IO statistics.

Gets a device's IO statistics.

```bash
sbctl storage-node get-io-stats-device
    <DEVICE_ID>
    --history=<HISTORY>
    --records=<RECORDS>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| DEVICE_ID | The storage device id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --history| List history records -one for every 15 minutes- for XX days and YY hours -up to 10 days in total-, format: XXdYYh. | string | False | - |
| --records| The number of records. Default: `20`. | integer | False | 20 |


## Gets the data interfaces list of a storage node.

Gets the data interfaces list of a storage node.

```bash
sbctl storage-node port-list
    <NODE_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| NODE_ID | The storage node id. | string | True |


## Gets the data interfaces' IO stats.

Gets the data interfaces' IO stats.

```bash
sbctl storage-node port-io-stats
    <PORT_ID>
    --history=<HISTORY>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| PORT_ID | The data port id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --history| List history records -one for every 15 minutes- for XX days and YY hours -up to 10 days in total, format: XXdYYh. | string | False | - |


## Checks the health status of a storage node.

Verifies if all of the NVMe-oF connections to and from the storage node, including those to and from other storage devices in the cluster and the meta-data journal, are available and healthy and all internal objects of the node, such as data placement and erasure coding services, are in a healthy state.


```bash
sbctl storage-node check
    <NODE_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| NODE_ID | The storage node id. | string | True |


## Checks the health status of a device.

Checks the health status of a device.

```bash
sbctl storage-node check-device
    <DEVICE_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| DEVICE_ID | The storage device id. | string | True |


## Gets the node's information.

Gets the node's information.

```bash
sbctl storage-node info
    <NODE_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| NODE_ID | The storage node id. | string | True |




## Restarts a journaling device.

Restarts a journaling device.

```bash
sbctl storage-node restart-jm-device
    <JM_DEVICE_ID>
    --force
    --format
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| JM_DEVICE_ID | The journaling device id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --force| Force device remove. | marker | False | - |
| --format| Format the Alceml device used for JM device. | marker | False | - |




## Forces to make the provided node id primary.

Makes the storage node the primary node. This is required after certain storage cluster operations, such
as a storage node migration.


```bash
sbctl storage-node make-primary
    <NODE_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| NODE_ID | The storage node id. | string | True |




## Adds a new device to from failed device information.

A previously failed and migrated device may be added back into the cluster as a new device. The new device would have the same info as the failed device but would be empty and not contain any data.

```bash
sbctl storage-node new-device-from-failed
    <DEVICE_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| DEVICE_ID | The storage device id. | string | True |


## List snapshots on a storage node.

List snapshots on a storage node.

```bash
sbctl storage-node list-snapshots
    <NODE_ID>
    --json
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| NODE_ID | The storage node id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --json| Print json output. | marker | False | - |


## List logical volumes on a storage node.

List logical volumes on a storage node.

```bash
sbctl storage-node list-lvols
    <NODE_ID>
    --json
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| NODE_ID | The storage node id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --json| Print json output. | marker | False | - |


## Try repair any inconsistencies in lvstore on a storage node.

Try repair any inconsistencies in lvstore on a storage node.

```bash
sbctl storage-node repair-lvstore
    <NODE_ID>
    --validate-only
    --force-remove-inconsistent
    --force_remove_wrong_ref
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| NODE_ID | The storage node id. | string | True |

| Parameter | Description | Data Type | Required | Default |
| --------- | ----------- | --------- | -------- | ------- |
| --validate-only| Validate only, do not perform any repair actions. | marker | False | - |
| --force-remove-inconsistent| Force remove any inconsistent logical volumes or snapshots. | marker | False | - |
| --force_remove_wrong_ref| Force remove logical volumes or snapshots with wrong reference count. | marker | False | - |



## Returns the device health information from SPDK.

Returns the device health information from SPDK.

```bash
sbctl storage-node get-device-health-info
    <DEVICE_ID>
```


| Argument | Description | Data Type | Required |
| -------- | ----------- | --------- | -------- |
| DEVICE_ID | The device node id. | string | True |
