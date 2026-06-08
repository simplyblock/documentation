---
title: "Simplyblock Operator Reference"
description: "The simplyblock Kubernetes operator manages simplyblock storage clusters, storage nodes, pools, logical volumes, and devices using Custom Resource Definitions (CRDs)."
weight: 20090
---

The simplyblock Kubernetes operator provides a declarative, Kubernetes-native interface for managing simplyblock storage
infrastructure. Instead of using the CLI, administrators can define storage clusters, storage nodes, pools, and logical
volumes as Kubernetes Custom Resource Definitions (CRDs). The operator continuously reconciles the desired state with
the actual state of the simplyblock cluster.

## Overview

The operator manages the following Custom Resource Definitions (CRDs):

| CRD              | Short Name | Description                                       |
|------------------|------------|---------------------------------------------------|
| `StorageCluster` | -          | Creates and manages a simplyblock storage cluster |
| `StorageNode`    | -          | Manages storage nodes within a cluster            |
| `Pool`           | -          | Creates and manages storage pools                 |
| `Lvol`           | -          | Manages logical volumes                           |
| `Device`         | -          | Manages NVMe devices on storage nodes             |
| `Task`           | -          | Monitors cluster tasks and their status           |
| `StorageBackup`  | -          | Creates a one-time backup of a PVC to S3          |
| `BackupRestore`  | -          | Restores a backup into a new PVC                  |
| `BackupPolicy`   | -          | Defines an automated backup schedule for PVCs     |

All CRDs use the API group `storage.simplyblock.io/v1alpha1`.

## Storage Cluster

The `StorageCluster` resource creates and manages a simplyblock storage cluster.

```yaml title="Example: Create a storage cluster"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageCluster
metadata:
  name: production
  namespace: simplyblock
spec:
  mgmtIfname: eth0
  haType: ha
  stripe:
    dataChunks: 2
    parityChunks: 1
  fabricType: tcp
  warningThreshold:
    capacity: 89
    provisionedCapacity: 250
  criticalThreshold:
    capacity: 99
    provisionedCapacity: 500
```

### Spec Fields

| Field                                   | Type   | Description                                                                                                                    |
|-----------------------------------------|--------|--------------------------------------------------------------------------------------------------------------------------------|
| `mgmtIfname`                            | string | Management network interface (e.g., `eth0`).                                                                                   |
| `haType`                                | string | High availability type: `single` or `ha`.                                                                                      |
| `stripe.dataChunks`                     | int    | Erasure coding data chunks per stripe.                                                                                         |
| `stripe.parityChunks`                   | int    | Erasure coding parity chunks per stripe.                                                                                       |
| `fabricType`                            | string | NVMe-oF fabric type: `tcp`, `rdma`, or `tcp,rdma`.                                                                             |
| `clientDataIfname`                      | string | Client-side data network interface name.                                                                                       |
| `enableNodeAffinity`                    | bool   | Enable node affinity for data placement.                                                                                       |
| `strictNodeAntiAffinity`                | bool   | Enforce strict node anti-affinity for chunks.                                                                                  |
| `isSingleNode`                          | bool   | Set to `true` for single-node clusters.                                                                                        |
| `blockSize`                             | int    | Logical block size in bytes (`512` or `4096`).                                                                                 |
| `pageSizeInBlocks`                      | int    | Page size expressed in blocks.                                                                                                 |
| `qpairCount`                            | int    | NVMe queue pair count per volume.                                                                                              |
| `maxQueueSize`                          | int    | Maximum backend queue size.                                                                                                    |
| `inflightIOThreshold`                   | int    | Inflight I/O threshold before back-pressure is applied.                                                                        |
| `maxFaultTolerance`                     | int    | Maximum number of concurrent node faults tolerated.                                                                            |
| `nvmfBasePort`                          | int    | Base port for NVMe-oF services. Subsequent nodes increment from this value.                                                    |
| `rpcBasePort`                           | int    | Base port for RPC services.                                                                                                    |
| `snodeApiPort`                          | int    | Storage node API port.                                                                                                         |
| `warningThreshold.capacity`             | int    | Capacity warning threshold (percent).                                                                                          |
| `criticalThreshold.capacity`            | int    | Capacity critical threshold (percent).                                                                                         |
| `warningThreshold.provisionedCapacity`  | int    | Provisioned capacity warning threshold (percent).                                                                              |
| `criticalThreshold.provisionedCapacity` | int    | Provisioned capacity critical threshold (percent).                                                                             |
| `action`                                | string | Lifecycle action: `activate` or `expand`.                                                                                      |
| `hashicorpVaultSettings.base_url`       | string | Base URL of an external Hashicorp Vault or Openbao instance used to manage volume encryption keys (e.g., `https://vault.vault:8200/`). See [Securing the Control Plane: External KMS](../deployments/kubernetes/security.md#external-key-management-kms). |
| `backup.credentialsSecretRef.name`      | string | Name of the Secret (in the same namespace) holding `access_key_id` and `secret_access_key`. **Required when `backup` is set**. |
| `backup.localEndpoint`                  | string | S3-compatible endpoint URL for backup storage.                                                                                 |
| `backup.snapshotBackups`                | bool   | Enable snapshot-based backups.                                                                                                 |
| `backup.withCompression`                | bool   | Enable compression for backup data.                                                                                            |
| `backup.secondaryTarget`                | int    | Secondary backup target identifier.                                                                                            |
| `backup.localTesting`                   | bool   | Enable local testing mode for backup.                                                                                          |

### Auto-Managed CSI Credentials

The cluster identifier is the `StorageCluster` resource name (`metadata.name`). The operator uses that name when
creating the backend cluster and the cluster credential Secret.

When a `StorageCluster` is created or becomes active, the operator automatically creates or updates the
`simplyblock-csi-secret-v2` Secret in the operator's namespace with the cluster's credentials. This Secret is
consumed by the CSI driver and requires no manual management. When the cluster is deleted, the operator removes
the cluster's entry from the Secret automatically.

### Status Fields

| Field                             | Type   | Description                                                 |
|-----------------------------------|--------|-------------------------------------------------------------|
| `uuid`                            | string | Cluster UUID assigned after creation.                       |
| `clusterName`                     | string | Cluster name, derived from `metadata.name`.                 |
| `nqn`                             | string | Cluster NVMe Qualified Name.                                |
| `status`                          | string | Current cluster lifecycle status.                           |
| `rebalancing`                     | bool   | Whether cluster rebalancing is currently active.            |
| `erasureCodingScheme`             | string | Active erasure coding layout, for example `2x1`.            |
| `secretName`                      | string | Name of the Kubernetes Secret holding cluster credentials.  |
| `configured`                      | bool   | Whether initial cluster setup has completed.                |
| `actionStatus.action`             | string | Most recently requested action name.                        |
| `actionStatus.state`              | string | Action execution state.                                     |
| `actionStatus.message`            | string | Human-readable result or error message.                     |
| `actionStatus.updatedAt`          | string | Timestamp of the last status transition.                    |
| `actionStatus.triggered`          | bool   | Whether the underlying backend action has been fired.       |
| `actionStatus.observedGeneration` | int    | Resource generation observed when this status was recorded. |

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
  maxLogicalVolumeCount: 100
  workerNodes:
    - worker-1
    - worker-2
  partitions: 1
  coreIsolation: true
```

### Spec Fields

| Field                                     | Type         | Description                                                                                                           |
|-------------------------------------------|--------------|-----------------------------------------------------------------------------------------------------------------------|
| `clusterName`                             | string       | Name of the cluster this node belongs to. **Required**.                                                               |
| `clusterImage`                            | string       | Storage-node container image override. If omitted, the operator inherits the image from the ControlPlane CRD.          |
| `spdkImage`                               | string       | SPDK service container image override.                                                                                |
| `spdkProxyImage`                          | string       | SPDK proxy service container image override.                                                                          |
| `maxLogicalVolumeCount`                   | int          | Maximum number of logical volumes per node. **Required when `action` is not specified**.                              |
| `maxSize`                                 | string       | Maximum allocatable huge pages memry (e.g., `16G`).                                                                   |
| `partitions`                              | int          | Number of partitions per backend storage device.                                                                      |
| `mgmtIfname`                              | string       | Management network interface name used by storage nodes.                                                              |
| `dataIfname`                              | []string     | Data-plane network interface names.                                                                                   |
| `coreIsolation`                           | bool         | Enable CPU core isolation mode.                                                                                       |
| `corePercentage`                          | int          | Percentage of CPU cores to allocate to SPDK (0–99).                                                                   |
| `reservedSystemCPU`                       | string       | CPUs reserved for system workloads (e.g., `0,1` or `0-1`).                                                            |
| `enableCpuTopology`                       | bool         | Enable topology-aware CPU scheduling.                                                                                 |
| `socketsToUse`                            | []string     | NUMA sockets to deploy storage on (e.g., `["0","1"]`).                                                                |
| `nodesPerSocket`                          | int          | Number of storage nodes to create per NUMA socket.                                                                    |
| `journalManager.count`                    | int          | Number of journal managers to configure.                                                                              |
| `journalManager.percentPerDevice`         | int          | Journal manager capacity as a percentage of each device.                                                              |
| `pcieAllowList`                           | []string     | PCIe addresses of NVMe devices to include.                                                                            |
| `pcieDenyList`                            | []string     | PCIe addresses of NVMe devices to exclude.                                                                            |
| `pcieModel`                               | string       | Filter devices by PCI device model string.                                                                            |
| `deviceNames`                             | []string     | Explicit NVMe namespace names to use (e.g., `["nvme0n1","nvme1n1"]`). Alternative to PCIe-based filtering.            |
| `driveSizeRange`                          | string       | Filter devices by capacity range (e.g., `100G-2T`).                                                                   |
| `forceFormat4K`                           | bool         | Force 4K block-size formatting on NVMe devices that support it.                                                       |
| `skipKubeletConfiguration`                | bool         | Skip kubelet configuration changes during node setup.                                                                 |
| `openShiftCluster`                        | bool         | Enable OpenShift-specific behavior (required on OpenShift). See [OpenShift](../deployments/kubernetes/openshift.md).  |
| `ubuntuHost`                              | bool         | Indicate the host OS is Ubuntu for OS-specific initialization.                                                        |
| `tolerations`                             | []Toleration | Kubernetes pod tolerations applied to storage-node pods.                                                              |
| `workerNodes`                             | []string     | Kubernetes worker node names to deploy storage on. **Required and must be non-empty when `action` is not specified**. |
| `action`                                  | string       | Node lifecycle action: `shutdown`, `restart`, `suspend`, `resume`, `remove`.                                          |
| `nodeUUID`                                | string       | UUID of the target node. **Required when `action` is specified**.                                                     |

### Status Fields

The `status.nodes` list reflects the observed state of each managed storage node.

| Field                                | Type   | Description                                                                                        |
|--------------------------------------|--------|----------------------------------------------------------------------------------------------------|
| `nodes[].uuid`                       | string | Backend node UUID.                                                                                 |
| `nodes[].hostname`                   | string | Kubernetes node hostname.                                                                          |
| `nodes[].status`                     | string | Backend lifecycle state.                                                                           |
| `nodes[].health`                     | bool   | Whether health checks are currently passing.                                                       |
| `nodes[].cpu`                        | int    | Reported CPU core count.                                                                           |
| `nodes[].memory`                     | string | Reported memory value.                                                                             |
| `nodes[].volumes`                    | int    | Current logical volume count.                                                                      |
| `nodes[].devices`                    | string | Backend device summary for this node.                                                              |
| `nodes[].mgmtIp`                     | string | Management IP address.                                                                             |
| `nodes[].rpcPort`                    | int    | Node RPC service port.                                                                             |
| `nodes[].lvolPort`                   | int    | Logical volume subsystem port.                                                                     |
| `nodes[].nvmfPort`                   | int    | NVMe-oF service port.                                                                              |
| `nodes[].uptime`                     | string | Reported node uptime.                                                                              |
| `actionStatus.action`                | string | Most recently requested action name.                                                               |
| `actionStatus.nodeUUID`              | string | Target node UUID for the action.                                                                   |
| `actionStatus.state`                 | string | Action execution state: `pending`, `running`, `success`, or `failed`.                              |
| `actionStatus.message`               | string | Human-readable result or error message.                                                            |
| `actionStatus.updatedAt`             | string | Timestamp of the last status transition.                                                           |
| `actionStatus.triggered`             | bool   | Whether the underlying backend action has been fired.                                              |
| `actionStatus.observedGeneration`    | int    | Resource generation observed when this status was recorded.                                        |
| `drainCoordination[].hostname`       | string | Kubernetes node name being drained.                                                                |
| `drainCoordination[].activeNodeUUID` | string | Backend UUID of the storage node being shut down or restarted.                                     |
| `drainCoordination[].phase`          | string | Drain phase: `detected`, `shutdown_called`, `draining`, `restart_called`, `complete`, or `failed`. |
| `drainCoordination[].message`        | string | Additional status detail or error information.                                                     |
| `drainCoordination[].startedAt`      | string | Timestamp when drain coordination began for this node.                                             |

### Node Operations

The `StorageNode` CR operates in two distinct modes depending on whether `spec.action` is set.

#### Triggering an Action

Set `spec.action` and `spec.nodeUUID` together. Both fields are required — the CRD validation will reject a CR that has `action` without `nodeUUID`.

```yaml title="Example: Suspend a storage node"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNode
metadata:
  name: storage-nodes
  namespace: simplyblock
spec:
  clusterName: production
  action: suspend
  nodeUUID: "d4e5f6a7-..."
```

To clear the action after it completes, remove `spec.action` and `spec.nodeUUID` from the CR. The operator does not clear these fields automatically.

#### Action Lifecycle

When an action is triggered, the operator transitions `status.actionStatus.state` through the following states:

```
(spec.action set) → running → success
                            ↘ failed  (retried after 10 s)
```


## Storage Pool

The `Pool` resource creates and manages storage pools. When a pool becomes active, the operator automatically
creates a Kubernetes `StorageClass` named `simplyblock-<namespace>-<clusterName>-<poolName>`. The StorageClass is deleted
when the pool is deleted.

```yaml title="Example: Create a storage pool"
apiVersion: storage.simplyblock.io/v1alpha1
kind: Pool
metadata:
  name: production-pool
  namespace: simplyblock
spec:
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

| Field                      | Type   | Description                                                                                                                                                        |
|----------------------------|--------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `clusterName`              | string | Name of the cluster. **Required**.                                                                                                                                 |
| `capacityLimit`            | string | Maximum pool capacity (e.g., `10T`).                                                                                                                               |
| `qos.iops`                 | int    | Maximum IOPS for the pool.                                                                                                                                         |
| `qos.throughput.readWrite` | int    | Maximum combined read/write throughput (MiB/s).                                                                                                                    |
| `qos.throughput.read`      | int    | Maximum read throughput (MiB/s).                                                                                                                                   |
| `qos.throughput.write`     | int    | Maximum write throughput (MiB/s).                                                                                                                                  |
| `action`                   | string | Pool lifecycle action.                                                                                                                                             |
| `storageClassParameters`   | object | Default volume parameters baked into the auto-created StorageClass. See [Quality of Service](../usage/simplyblock-csi/quality-of-service.md) for available fields. |

### Auto-Created StorageClass

The pool identifier is the `Pool` resource name (`metadata.name`). The operator uses that name as the backend pool
name and as the `pool_name` CSI StorageClass parameter.

When the pool reaches an active state, the operator creates a `StorageClass` with:

- **Name**: `simplyblock-<namespace>-<clusterName>-<poolName>`
- **Provisioner**: `csi.simplyblock.io`
- **VolumeBindingMode**: `WaitForFirstConsumer`
- **ReclaimPolicy**: `Delete`
- **AllowVolumeExpansion**: `true`

The `cluster_id` and `pool_name` parameters are set automatically. Any fields specified in
`spec.storageClassParameters` are merged in as additional CSI driver parameters.

Because Kubernetes StorageClass parameters are immutable after creation, the StorageClass is created once and
left unchanged if it already exists. To change parameters, delete the pool and recreate it with updated values.

The StorageClass is deleted when the pool is deleted.

### Status Fields

| Field                      | Type   | Description                                                  |
|----------------------------|--------|--------------------------------------------------------------|
| `uuid`                     | string | Backend pool UUID assigned after creation.                   |
| `status`                   | string | Backend lifecycle status.                                    |
| `qos.host`                 | string | Backend host responsible for enforcing pool QoS.             |
| `qos.iops`                 | int    | Currently configured IOPS limit.                             |
| `qos.throughput.readWrite` | int    | Currently configured combined read/write throughput (MiB/s). |
| `qos.throughput.read`      | int    | Currently configured read throughput (MiB/s).                |
| `qos.throughput.write`     | int    | Currently configured write throughput (MiB/s).               |

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

| Field                       | Type     | Description                                                                                               |
|-----------------------------|----------|-----------------------------------------------------------------------------------------------------------|
| `uuid`                      | string   | Volume UUID.                                                                                              |
| `lvolName`                  | string   | Volume name.                                                                                              |
| `status`                    | string   | Backend lifecycle status.                                                                                 |
| `size`                      | string   | Volume size.                                                                                              |
| `ha`                        | bool     | High availability enabled.                                                                                |
| `health`                    | bool     | Whether health checks are passing.                                                                        |
| `encrypted`                 | bool     | Whether the volume is encrypted. See [Volume Encryption](../deployments/kubernetes/volume-encryption.md). |
| `erasureCodingScheme`       | string   | Active erasure coding layout for this volume (e.g., `2x1`).                                               |
| `nqn`                       | string   | NVMe Qualified Name for the volume.                                                                       |
| `subsysPort`                | int      | NVMe subsystem listener port.                                                                             |
| `namespaceID`               | int      | NVMe namespace identifier.                                                                                |
| `poolName`                  | string   | Storage pool name.                                                                                        |
| `poolUUID`                  | string   | Storage pool UUID.                                                                                        |
| `nodeUUID`                  | []string | Node UUIDs associated with this volume.                                                                   |
| `hostname`                  | string   | Node hostname associated with the volume.                                                                 |
| `pvcName`                   | string   | Bound Kubernetes PVC name, if applicable.                                                                 |
| `fabricType`                | string   | Storage fabric/protocol in use (`tcp` or `rdma`).                                                         |
| `clonedFromSnapshot`        | string   | Source snapshot ID if this volume was cloned from a snapshot.                                             |
| `sourceSnapshotName`        | string   | Source snapshot name if this volume was cloned from a snapshot.                                           |
| `qos.class`                 | int      | Assigned QoS class identifier.                                                                            |
| `qos.iops`                  | int      | IOPS limit for this volume.                                                                               |
| `qos.throughput.read`       | int      | Read throughput limit (MiB/s).                                                                            |
| `qos.throughput.write`      | int      | Write throughput limit (MiB/s).                                                                           |
| `qos.throughput.readWrite`  | int      | Combined read/write throughput limit (MiB/s).                                                             |
| `blobID`                    | int      | Backend blob identifier.                                                                                  |
| `maxNamespacesPerSubsystem` | int      | Maximum number of NVMe namespaces per subsystem.                                                          |

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

### Status Fields

| Field                                      | Type   | Description                                                          |
|--------------------------------------------|--------|----------------------------------------------------------------------|
| `nodes[].nodeUUID`                         | string | Backend UUID of the storage node.                                    |
| `nodes[].devices[].uuid`                   | string | Backend device UUID.                                                 |
| `nodes[].devices[].status`                 | string | Backend lifecycle status of the device.                              |
| `nodes[].devices[].health`                 | string | Backend health indicator for the device.                             |
| `nodes[].devices[].model`                  | string | Reported device model.                                               |
| `nodes[].devices[].size`                   | string | Formatted device capacity.                                           |
| `actionStatus.action`                      | string | Most recently requested action name.                                 |
| `actionStatus.nodeUUID`                    | string | Target node UUID for the action.                                     |
| `actionStatus.state`                       | string | Action execution state.                                              |
| `actionStatus.message`                     | string | Human-readable result or error message.                              |
| `actionStatus.updatedAt`                   | string | Timestamp of the last status transition.                             |
| `actionStatus.triggered`                   | bool   | Whether the underlying backend action has been fired.                |
| `actionStatus.observedGeneration`          | int    | Resource generation observed when this status was recorded.          |

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
  taskID: "abc123"   # optional: filter to a specific task
```

### Spec Fields

| Field         | Type   | Description                                                          |
|---------------|--------|----------------------------------------------------------------------|
| `clusterName` | string | Target storage cluster name. **Required**.                           |
| `taskID`      | string | Filter results to a specific backend task UUID.                      |

### Status Fields

| Field                  | Type   | Description                                          |
|------------------------|--------|------------------------------------------------------|
| `tasks[].uuid`         | string | Backend task UUID.                                   |
| `tasks[].taskType`     | string | Backend task function or type name.                  |
| `tasks[].taskStatus`   | string | Backend lifecycle status for the task.               |
| `tasks[].taskResult`   | string | Backend result payload or message.                   |
| `tasks[].retried`      | int    | Number of retry attempts made for the task.          |
| `tasks[].canceled`     | bool   | Whether the task was canceled.                       |

## StorageBackup

The `StorageBackup` resource creates a one-time backup of a PVC to the S3-compatible storage endpoint configured
in the `StorageCluster`. For backup configuration prerequisites, see
[Backup and Recovery](../usage/backup-recovery.md#kubernetes-crd-operations).

```yaml title="Example: Create a PVC backup"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageBackup
metadata:
  name: my-backup
  namespace: simplyblock
spec:
  clusterName: production
  pvcRef:
    name: my-pvc
```

### Spec Fields

| Field         | Type   | Description                                          |
|---------------|--------|------------------------------------------------------|
| `clusterName` | string | Name of the target StorageCluster. **Required**.     |
| `pvcRef.name` | string | Name of the PVC to back up. **Required**.            |

### Status Fields

| Field      | Type   | Description                                                 |
|------------|--------|-------------------------------------------------------------|
| `phase`    | string | Current phase: `InProgress` or `Done`.                      |
| `pvc`      | string | Name of the source PVC.                                     |
| `backupID` | string | Backend backup identifier assigned after the backup starts. |
| `snapshot` | string | Name of the snapshot used for the backup.                   |

## BackupRestore

The `BackupRestore` resource restores a `StorageBackup` into a new PVC. The backup may be directed to a
different pool or storage node, but must be restored within the same namespace as the `BackupRestore` object.

```yaml title="Example: Restore a backup to a new PVC"
apiVersion: storage.simplyblock.io/v1alpha1
kind: BackupRestore
metadata:
  name: my-restore
  namespace: simplyblock
spec:
  clusterName: production
  backupRef:
    name: my-backup
  pvcTemplate:
    metadata:
      name: restored-pvc
    spec:
      accessModes:
        - ReadWriteOnce
      resources:
        requests:
          storage: 10Gi
```

### Spec Fields

| Field                       | Type   | Description                                                                     |
|-----------------------------|--------|---------------------------------------------------------------------------------|
| `clusterName`               | string | Name of the target StorageCluster. **Required**.                                |
| `backupRef.name`            | string | Name of the `StorageBackup` to restore from. **Required**.                      |
| `targetPool`                | string | Pool to restore into. Defaults to the source backup PVC's pool.                 |
| `targetNode`                | string | Storage node to restore to. Defaults to the node that held the original backup. |
| `pvcTemplate.metadata.name` | string | Name of the new PVC to create. **Required**.                                    |
| `pvcTemplate.spec`          | object | PVC spec including `accessModes` and `resources`.                               |

### Status Fields

| Field    | Type   | Description                                           |
|----------|--------|-------------------------------------------------------|
| `phase`  | string | Current phase: `InProgress`, `PVCBinding`, or `Done`. |
| `backup` | string | Name of the source `StorageBackup`.                   |
| `pvc`    | string | Name of the newly created PVC.                        |

!!! warning
    `BackupRestore` can only restore a PVC to the same namespace as the restore object.

## BackupPolicy

The `BackupPolicy` resource defines an automated backup schedule with retention settings. Policies are attached
to PVCs using the `simplybk/backup-policy` Kubernetes annotation, which causes `StorageBackup` objects to be
created automatically on schedule. Removing the annotation detaches the policy; updating it switches the PVC to
the new policy.

```yaml title="Example: Create a backup policy"
apiVersion: storage.simplyblock.io/v1alpha1
kind: BackupPolicy
metadata:
  name: my-policy
  namespace: simplyblock
spec:
  clusterName: production
  maxVersions: 10
  maxAge: "7d"
  schedule: "15m,4 60m,11 24h,7"
```

Attach the policy to a PVC:

```bash title="Attach a backup policy to a PVC"
kubectl annotate pvc my-pvc -n simplyblock simplybk/backup-policy=my-policy
```

### Spec Fields

| Field         | Type   | Description                                                       |
|---------------|--------|-------------------------------------------------------------------|
| `clusterName` | string | Name of the target StorageCluster. **Required**.                  |
| `maxVersions` | int    | Maximum number of backup versions to retain.                      |
| `maxAge`      | string | Maximum backup age before cleanup (e.g., `7d`, `12h`).            |
| `schedule`    | string | Tiered backup schedule as space-separated `interval,count` pairs. |

The schedule format is a space-separated list of `interval,count` pairs. For example, `15m,4 60m,11 24h,7` means:
take a backup every 15 minutes (keep the 4 most recent), every 60 minutes (keep 11), and every 24 hours (keep 7).
