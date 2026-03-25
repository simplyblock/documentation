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
| `SimplyBlockStorageCluster` | -          | Creates and manages a simplyblock storage cluster |
| `SimplyBlockStorageNode`    | -          | Manages storage nodes within a cluster            |
| `SimplyBlockPool`           | -          | Creates and manages storage pools                 |
| `SimplyBlockLvol`           | -          | Manages logical volumes                           |
| `SimplyBlockDevice`         | -          | Manages NVMe devices on storage nodes             |
| `SimplyBlockTask`           | -          | Monitors cluster tasks and their status            |

All CRDs use the API group `simplyblock.simplyblock.io/v1alpha1`.

## Storage Cluster

The `SimplyBlockStorageCluster` resource creates and manages a simplyblock storage cluster.

```yaml title="Example: Create a storage cluster"
apiVersion: simplyblock.simplyblock.io/v1alpha1
kind: SimplyBlockStorageCluster
metadata:
  name: my-cluster
  namespace: simplyblock
spec:
  clusterName: production
  mgmtIfc: eth0
  haType: ha
  stripeWdata: 2
  stripeWparity: 1
  fabric: tcp
  capWarn: 89
  capCrit: 99
  provCapWarn: 250
  provCapCrit: 500
```

### Spec Fields

| Field                    | Type    | Description                                                                  |
|--------------------------|---------|------------------------------------------------------------------------------|
| `clusterName`            | string  | Human-readable cluster name. **Required**.                                   |
| `mgmtIfc`               | string  | Management network interface (e.g., `eth0`).                                 |
| `haType`                 | string  | High availability type: `single` or `ha`.                                    |
| `stripeWdata`            | int     | Erasure coding data chunks per stripe.                                       |
| `stripeWparity`          | int     | Erasure coding parity chunks per stripe.                                     |
| `fabric`                 | string  | NVMe-oF fabric type: `tcp`, `rdma`, or `tcp,rdma`.                          |
| `enableNodeAffinity`     | bool    | Enable node affinity for data placement.                                     |
| `strictNodeAntiAffinity` | bool    | Enforce strict node anti-affinity for chunks.                                |
| `isSingleNode`           | bool    | Set to `true` for single-node clusters.                                      |
| `qpairCount`             | int     | Queue pair count per volume.                                                 |
| `clientQpairCount`       | int     | Client queue pair count per volume.                                          |
| `capWarn`                | int     | Capacity warning threshold (percent).                                        |
| `capCrit`                | int     | Capacity critical threshold (percent).                                       |
| `provCapWarn`            | int     | Provisioning capacity warning threshold (percent).                           |
| `provCapCrit`            | int     | Provisioning capacity critical threshold (percent).                          |
| `action`                 | string  | Lifecycle action: `activate` or `expand`.                                    |

### Status Fields

| Field          | Type   | Description                          |
|----------------|--------|--------------------------------------|
| `UUID`         | string | Cluster UUID assigned after creation |
| `clusterName`  | string | Cluster name                         |
| `mgmtNodes`    | int    | Number of management nodes           |
| `storageNodes` | int    | Number of storage nodes              |
| `NQN`          | string | Cluster NQN                          |
| `status`       | string | Current cluster status               |

## Storage Node

The `SimplyBlockStorageNode` resource manages storage nodes within a cluster.

```yaml title="Example: Deploy storage nodes"
apiVersion: simplyblock.simplyblock.io/v1alpha1
kind: SimplyBlockStorageNode
metadata:
  name: storage-nodes
  namespace: simplyblock
spec:
  clusterName: production
  maxLVol: 100
  maxSize: "500G"
  partitions: 1
  coreIsolation: true
```

### Spec Fields

| Field                     | Type     | Description                                                      |
|---------------------------|----------|------------------------------------------------------------------|
| `clusterName`             | string   | Name of the cluster this node belongs to. **Required**.          |
| `maxLVol`                 | int      | Maximum number of logical volumes on this node.                  |
| `maxSize`                 | string   | Maximum provisioning size for the node.                          |
| `partitions`              | int      | Number of partitions per device.                                 |
| `coreIsolation`           | bool     | Enable CPU core isolation.                                       |
| `corePercentage`          | int      | Percentage of cores to allocate.                                 |
| `coreMask`                | string   | Explicit CPU core mask.                                          |
| `pcieAllowList`           | []string | List of allowed NVMe PCIe addresses.                             |
| `pcieDenyList`            | []string | List of blocked NVMe PCIe addresses.                             |
| `dataNIC`                 | []string | Data network interface names.                                    |
| `socketsToUse`            | int      | Number of NUMA sockets to use.                                   |
| `nodesPerSocket`          | int      | Number of storage nodes per NUMA socket.                         |
| `workerNodes`             | []string | List of Kubernetes worker node names to deploy on.               |
| `action`                  | string   | Node action: `shutdown`, `restart`, `suspend`, `resume`, `remove`.|
| `nodeUUID`                | string   | Node UUID (required when action is specified).                   |

## Storage Pool

The `SimplyBlockPool` resource creates and manages storage pools.

```yaml title="Example: Create a storage pool"
apiVersion: simplyblock.simplyblock.io/v1alpha1
kind: SimplyBlockPool
metadata:
  name: my-pool
  namespace: simplyblock
spec:
  name: production-pool
  clusterName: production
  capacityLimit: "10T"
  qosIOPSLimit: 100000
```

### Spec Fields

| Field            | Type   | Description                                            |
|------------------|--------|--------------------------------------------------------|
| `name`           | string | Pool name. **Required**.                               |
| `clusterName`    | string | Name of the cluster. **Required**.                     |
| `capacityLimit`  | string | Maximum pool capacity (e.g., `10T`).                   |
| `qosIOPSLimit`   | int    | Maximum IOPS for the pool.                             |
| `rwLimit`        | int    | Maximum read/write throughput (MB/s).                  |
| `rLimit`         | int    | Maximum read throughput (MB/s).                        |
| `wLimit`         | int    | Maximum write throughput (MB/s).                       |
| `action`         | string | Pool lifecycle action.                                 |

## Logical Volume

The `SimplyBlockLvol` resource manages logical volumes. It provides a read-only view of volumes in a cluster and pool.

```yaml title="Example: List logical volumes"
apiVersion: simplyblock.simplyblock.io/v1alpha1
kind: SimplyBlockLvol
metadata:
  name: cluster-volumes
  namespace: simplyblock
spec:
  clusterName: production
  poolName: production-pool
```

### Status Fields

Each volume in the `status.lvols` list includes:

| Field           | Type   | Description                            |
|-----------------|--------|----------------------------------------|
| `uuid`          | string | Volume UUID                            |
| `lvolName`      | string | Volume name                            |
| `status`        | string | Volume status                          |
| `size`          | string | Volume size                            |
| `ha`            | bool   | High availability enabled              |
| `health`        | bool   | Volume health status                   |
| `nqn`           | string | NVMe NQN                              |
| `poolName`      | string | Pool name                              |
| `fabric`        | string | Fabric type (tcp/rdma)                 |

## Device

The `SimplyBlockDevice` resource manages NVMe devices on storage nodes.

```yaml title="Example: List devices"
apiVersion: simplyblock.simplyblock.io/v1alpha1
kind: SimplyBlockDevice
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

The `SimplyBlockTask` resource provides visibility into cluster tasks (migrations, rebalancing, etc.).

```yaml title="Example: Monitor tasks"
apiVersion: simplyblock.simplyblock.io/v1alpha1
kind: SimplyBlockTask
metadata:
  name: cluster-tasks
  namespace: simplyblock
spec:
  clusterName: production
  subtasks: true
```

The `status.tasks` list shows each task's UUID, type, status, result, and timing information.
