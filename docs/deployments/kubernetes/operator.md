---
title: "Simplyblock Operator"
description: "The simplyblock Kubernetes operator manages simplyblock storage clusters, storage nodes, pools, logical volumes, and devices using Custom Resource Definitions (CRDs)."
weight: 30050
---

The simplyblock Kubernetes operator provides a declarative, Kubernetes-native interface for managing simplyblock storage
infrastructure. Instead of using the CLI, administrators can define storage clusters, storage nodes, pools, and logical
volumes as Kubernetes Custom Resources (CRs). The operator continuously reconciles the desired state with the actual
state of the simplyblock cluster.

## Overview

The operator manages the following Custom Resource Definitions (CRDs):

| CRD                         | Short Name | Description                                      |
|-----------------------------|------------|--------------------------------------------------|
| `StorageCluster` | -          | Creates and manages a simplyblock storage cluster |
| `StorageNode`    | -          | Manages storage nodes within a cluster            |
| `Pool`           | -          | Creates and manages storage pools                 |
| `Lvol`           | -          | Manages logical volumes                           |
| `Device`         | -          | Manages NVMe devices on storage nodes             |
| `Task`           | -          | Monitors cluster tasks and their status            |

All CRDs use the API group `storage.simplyblock.io/v1alpha1`.

## Storage Cluster

The `StorageCluster` resource creates and manages a simplyblock storage cluster.

```yaml title="Example: Create a storage cluster"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageCluster
metadata:
  name: my-cluster
  namespace: simplyblock
spec:
  clusterName: production
  mgmtIfname: eth0
  haType: ha
  stripe:
    dataChunks: 2
    parityChunks: 1
  fabric: tcp
  warningThreshold:
    capacity: 89
    provisionedCapacity: 250
  criticalThreshold:
    capacity: 99
    provisionedCapacity: 500
```

### Spec Fields

| Field                                   | Type     | Description                                                                        |
|-----------------------------------------|----------|------------------------------------------------------------------------------------|
| `clusterName`                           | string   | Human-readable cluster name. **Required**.                                         |
| `mgmtIfname`                            | string   | Management network interface (e.g., `eth0`).                                       |
| `haType`                                | string   | High availability type: `single` or `ha`.                                          |
| `stripe.dataChunks`                     | int      | Erasure coding data chunks per stripe.                                             |
| `stripe.parityChunks`                   | int      | Erasure coding parity chunks per stripe.                                           |
| `fabric`                                | string   | NVMe-oF fabric type: `tcp`, `rdma`, or `tcp,rdma`.                                 |
| `clientDataNic`                         | string   | Client-side data network interface name.                                           |
| `enableNodeAffinity`                    | bool     | Enable node affinity for data placement.                                           |
| `strictNodeAntiAffinity`                | bool     | Enforce strict node anti-affinity for chunks.                                      |
| `isSingleNode`                          | bool     | Set to `true` for single-node clusters.                                            |
| `blockSize`                             | int      | Logical block size in bytes (`512` or `4096`).                                     |
| `pageSizeInBlocks`                      | int      | Page size expressed in blocks.                                                     |
| `qpairCount`                            | int      | NVMe queue pair count per volume.                                                  |
| `clientQpairCount`                      | int      | Client-side queue pair count per volume.                                           |
| `maxQueueSize`                          | int      | Maximum backend queue size.                                                        |
| `inflightIOThreshold`                   | int      | Inflight I/O threshold before back-pressure is applied.                            |
| `maxFaultTolerance`                     | int      | Maximum number of concurrent node faults tolerated.                                |
| `nvmfBasePort`                          | int      | Base port for NVMe-oF services. Subsequent nodes increment from this value.        |
| `rpcBasePort`                           | int      | Base port for RPC services.                                                        |
| `snodeApiPort`                          | int      | Storage node API port.                                                             |
| `qosClasses`                            | string   | Backend QoS class configuration string.                                            |
| `warningThreshold.capacity`             | int      | Capacity warning threshold (percent).                                              |
| `criticalThreshold.capacity`            | int      | Capacity critical threshold (percent).                                             |
| `warningThreshold.provisionedCapacity`  | int      | Provisioned capacity warning threshold (percent).                                  |
| `criticalThreshold.provisionedCapacity` | int      | Provisioned capacity critical threshold (percent).                                 |
| `includeEventLog`                       | bool     | Include event log entries in cluster status responses.                             |
| `eventLogEntries`                       | int      | Number of event log entries to retain.                                             |
| `action`                                | string   | Lifecycle action: `activate` or `expand`.                                          |

### Status Fields

| Field                 | Type   | Description                                                        |
|-----------------------|--------|--------------------------------------------------------------------|
| `uuid`                | string | Cluster UUID assigned after creation.                              |
| `clusterName`         | string | Cluster name.                                                      |
| `mgmtNodes`           | int    | Number of management nodes.                                        |
| `storageNodes`        | int    | Number of storage nodes.                                           |
| `nqn`                 | string | Cluster NVMe Qualified Name.                                       |
| `status`              | string | Current cluster lifecycle status.                                  |
| `rebalancing`         | bool   | Whether cluster rebalancing is currently active.                   |
| `erasureCodingScheme` | string | Active erasure coding layout, for example `2x1`.                   |
| `secretName`          | string | Name of the Kubernetes Secret holding cluster credentials.         |
| `configured`          | bool   | Whether initial cluster setup has completed.                       |
| `actionStatus`        | object | Most recent action state: `action`, `state`, `message`, `updatedAt`. |

## Storage Node

The `StorageNode` resource manages storage nodes within a cluster.

```yaml title="Example: Deploy storage nodes"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNode
metadata:
  name: storage-nodes
  namespace: simplyblock
spec:
  clusterName: production
  clusterImage: "public.ecr.aws/simply-block/simplyblock:26.1.2"
  maxLogicalVolumeCount: 100
  workerNodes:
    - worker-1
    - worker-2
  maxSize: "500G"
  partitions: 1
  coreIsolation: true
```

### Spec Fields

| Field                      | Type        | Description                                                                                                           |
|----------------------------|-------------|-----------------------------------------------------------------------------------------------------------------------|
| `clusterName`              | string      | Name of the cluster this node belongs to. **Required**.                                                               |
| `clusterImage`             | string      | Storage-node container image. **Required when `action` is not specified**.                                            |
| `spdkImage`                | string      | SPDK service container image override.                                                                                |
| `maxLogicalVolumeCount`    | int         | Maximum number of logical volumes per node. **Required when `action` is not specified**.                              |
| `maxSize`                  | string      | Maximum allocatable storage size for the node (e.g., `500G`).                                                         |
| `partitions`               | int         | Number of partitions per backend storage device.                                                                      |
| `mgmtIfname`               | string      | Management network interface name used by storage nodes.                                                              |
| `dataIfname`               | []string    | Data-plane network interface names.                                                                                   |
| `coreIsolation`            | bool        | Enable CPU core isolation mode.                                                                                       |
| `corePercentage`           | int         | Percentage of CPU cores to allocate to SPDK (0–99).                                                                   |
| `reservedSystemCPU`        | string      | CPUs reserved for system workloads (e.g., `0,1` or `0-1`).                                                            |
| `coreMask`                 | string      | Explicit CPU core mask for SPDK.                                                                                      |
| `enableCpuTopology`        | bool        | Enable topology-aware CPU scheduling.                                                                                 |
| `socketsToUse`             | []string    | NUMA sockets to deploy storage on (e.g., `["0","1"]`).                                                                |
| `nodesPerSocket`           | int         | Number of storage nodes to create per NUMA socket.                                                                    |
| `journalManager.count`     | int         | Number of journal managers to configure.                                                                              |
| `journalManager.percentPerDevice` | int  | Journal manager capacity as a percentage of each device.                                                              |
| `journalManager.useSeparateJournalDevice` | bool | Use dedicated devices for journals instead of sharing with data. |
| `pcieAllowList`            | []string    | PCIe addresses of NVMe devices to include.                                                                            |
| `pcieDenyList`             | []string    | PCIe addresses of NVMe devices to exclude.                                                                            |
| `pcieModel`                | string      | Filter devices by PCI device model string.                                                                            |
| `deviceNames`              | []string    | Explicit NVMe namespace names to use (e.g., `["nvme0n1","nvme1n1"]`). Alternative to PCIe-based filtering.           |
| `driveSizeRange`           | string      | Filter devices by capacity range (e.g., `100G-2T`).                                                                   |
| `forceFormat4K`            | bool        | Force 4K block-size formatting on NVMe devices that support it.                                                       |
| `skipKubeletConfiguration` | bool        | Skip kubelet configuration changes during node setup.                                                                 |
| `openShiftCluster`         | bool        | Enable OpenShift-specific behavior (required on OpenShift). See [OpenShift](openshift.md).                            |
| `ubuntuHost`               | bool        | Indicate the host OS is Ubuntu for OS-specific initialization.                                                        |
| `tolerations`              | []Toleration | Kubernetes pod tolerations applied to storage-node pods.                                                             |
| `workerNodes`              | []string    | Kubernetes worker node names to deploy storage on. **Required and must be non-empty when `action` is not specified**. |
| `action`                   | string      | Node lifecycle action: `shutdown`, `restart`, `suspend`, `resume`, `remove`.                                          |
| `nodeUUID`                 | string      | UUID of the target node. **Required when `action` is specified**.                                                     |
| `addPcieToAllowList`       | []string    | Additional PCIe addresses appended to the allow-list during `restart` actions.                                        |
| `force`                    | bool        | Force action execution where supported.                                                                               |

### Status Fields

The `status.nodes` list reflects the observed state of each managed storage node.

| Field                   | Type   | Description                                      |
|-------------------------|--------|--------------------------------------------------|
| `nodes[].uuid`          | string | Backend node UUID.                               |
| `nodes[].hostname`      | string | Kubernetes node hostname.                        |
| `nodes[].status`        | string | Backend lifecycle state.                         |
| `nodes[].health`        | bool   | Whether health checks are currently passing.     |
| `nodes[].cpu`           | int    | Reported CPU core count.                         |
| `nodes[].memory`        | string | Reported memory value.                           |
| `nodes[].volumes`       | int    | Current logical volume count.                    |
| `nodes[].devices`       | string | Backend device summary for this node.            |
| `nodes[].mgmtIp`        | string | Management IP address.                           |
| `nodes[].rpcPort`       | int    | Node RPC service port.                           |
| `nodes[].lvolPort`      | int    | Logical volume subsystem port.                   |
| `nodes[].nvmfPort`      | int    | NVMe-oF service port.                            |
| `nodes[].uptime`        | string | Reported node uptime.                            |
| `actionStatus.action`   | string | Most recently requested action name.             |
| `actionStatus.nodeUUID` | string | Target node UUID for the action.                 |
| `actionStatus.state`    | string | Action execution state: `pending`, `running`, `success`, or `failed`. |
| `actionStatus.message`  | string | Human-readable result or error message.          |
| `actionStatus.updatedAt`| string | Timestamp of the last status transition.         |

## Storage Pool

The `Pool` resource creates and manages storage pools.

```yaml title="Example: Create a storage pool"
apiVersion: storage.simplyblock.io/v1alpha1
kind: Pool
metadata:
  name: my-pool
  namespace: simplyblock
spec:
  name: production-pool
  clusterName: production
  capacityLimit: "10T"
  qos:
    iops: 100000
    throughput:
      readWrite: 2048
      read: 1024
      write: 1024
```

### Spec Fields

| Field                      | Type   | Description                                    |
|----------------------------|--------|------------------------------------------------|
| `name`                     | string | Pool name. **Required**.                        |
| `clusterName`              | string | Name of the cluster. **Required**.              |
| `capacityLimit`            | string | Maximum pool capacity (e.g., `10T`).            |
| `qos.iops`                 | int    | Maximum IOPS for the pool.                      |
| `qos.throughput.readWrite` | int    | Maximum combined read/write throughput (MiB/s). |
| `qos.throughput.read`      | int    | Maximum read throughput (MiB/s).                |
| `qos.throughput.write`     | int    | Maximum write throughput (MiB/s).               |
| `action`                   | string | Pool lifecycle action.                          |

### Status Fields

| Field                    | Type   | Description                                              |
|--------------------------|--------|----------------------------------------------------------|
| `uuid`                   | string | Backend pool UUID assigned after creation.               |
| `status`                 | string | Backend lifecycle status.                                |
| `qos.host`               | string | Backend host responsible for enforcing pool QoS.         |
| `qos.iops`               | int    | Currently configured IOPS limit.                         |
| `qos.throughput.readWrite` | int  | Currently configured combined read/write throughput (MiB/s). |
| `qos.throughput.read`    | int    | Currently configured read throughput (MiB/s).            |
| `qos.throughput.write`   | int    | Currently configured write throughput (MiB/s).           |

## Logical Volume

The `Lvol` resource manages logical volumes. It provides a read-only view of volumes in a cluster and pool.

```yaml title="Example: List logical volumes"
apiVersion: storage.simplyblock.io/v1alpha1
kind: Lvol
metadata:
  name: cluster-volumes
  namespace: simplyblock
spec:
  clusterName: production
  poolName: production-pool
```

### Status Fields

Each volume in the `status.lvols` list includes:

| Field                  | Type     | Description                                                             |
|------------------------|----------|-------------------------------------------------------------------------|
| `uuid`                 | string   | Volume UUID.                                                            |
| `lvolName`             | string   | Volume name.                                                            |
| `status`               | string   | Backend lifecycle status.                                               |
| `size`                 | string   | Volume size.                                                            |
| `ha`                   | bool     | High availability enabled.                                              |
| `health`               | bool     | Whether health checks are passing.                                      |
| `encrypted`            | bool     | Whether the volume is encrypted. See [Volume Encryption](volume-encryption.md). |
| `erasureCodingScheme`  | string   | Active erasure coding layout for this volume (e.g., `2x1`).            |
| `nqn`                  | string   | NVMe Qualified Name for the volume.                                     |
| `subsysPort`           | int      | NVMe subsystem listener port.                                           |
| `namespaceID`          | int      | NVMe namespace identifier.                                              |
| `poolName`             | string   | Storage pool name.                                                      |
| `poolUUID`             | string   | Storage pool UUID.                                                      |
| `nodeUUID`             | []string | Node UUIDs associated with this volume.                                 |
| `hostname`             | string   | Node hostname associated with the volume.                               |
| `pvcName`              | string   | Bound Kubernetes PVC name, if applicable.                               |
| `fabric`               | string   | Storage fabric/protocol in use (`tcp` or `rdma`).                       |
| `clonedFromSnapshot`   | string   | Source snapshot ID if this volume was cloned from a snapshot.           |
| `sourceSnapshotName`   | string   | Source snapshot name if this volume was cloned from a snapshot.         |
| `qos.class`            | int      | Assigned QoS class identifier.                                          |
| `qos.iops`             | int      | IOPS limit for this volume.                                             |
| `qos.throughput.read`  | int      | Read throughput limit (MiB/s).                                          |
| `qos.throughput.write` | int      | Write throughput limit (MiB/s).                                         |
| `qos.throughput.readWrite` | int  | Combined read/write throughput limit (MiB/s).                           |

### Snapshot Cloning

When a volume is cloned from a snapshot, the `clonedFromSnapshot` and `sourceSnapshotName` fields in its status entry identify the origin. These fields are read-only and set by the backend at creation time — they cannot be specified in the `Lvol` spec.

To see which volumes in a pool are snapshot clones:

```bash
kubectl get simplyblocklvol cluster-volumes -n simplyblock -o jsonpath='{.status.lvols[?(@.clonedFromSnapshot!="")].lvolName}'
```

## Device

The `Device` resource manages NVMe devices on storage nodes.

```yaml title="Example: List devices"
apiVersion: storage.simplyblock.io/v1alpha1
kind: Device
metadata:
  name: cluster-devices
  namespace: simplyblock
spec:
  clusterName: production
```

### Actions

To perform actions on a specific device, set the `action`, `nodeUUID`, and `deviceID` fields:

| Action    | Description                  |
|-----------|------------------------------|
| `remove`  | Remove a device from a node  |
| `restart` | Restart a device on a node   |

## Task

The `Task` resource provides visibility into cluster tasks (migrations, rebalancing, etc.).

```yaml title="Example: Monitor tasks"
apiVersion: storage.simplyblock.io/v1alpha1
kind: Task
metadata:
  name: cluster-tasks
  namespace: simplyblock
spec:
  clusterName: production
  subtasks: true
```

The `status.tasks` list shows each task's UUID, type, status, result, and timing information.
