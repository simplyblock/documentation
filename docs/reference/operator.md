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

| CRD                | Short Name | Description                                                           |
|--------------------|------------|-----------------------------------------------------------------------|
| `StorageCluster`   | -          | Creates and manages a simplyblock storage cluster                     |
| `StorageNodeSet`   | -          | Fleet-level declarative management of storage nodes across workers    |
| `StorageNode`      | -          | Represents a single backend storage node instance (auto-created)      |
| `StorageNodeOps`   | -          | One-shot operational action targeting a single storage node           |
| `Pool`             | -          | Creates and manages storage pools                                     |
| `Lvol`             | -          | Manages logical volumes                                               |
| `Device`           | -          | Manages NVMe devices on storage nodes                                 |
| `Task`             | -          | Monitors cluster tasks and their status                               |
| `StorageBackup`    | -          | Creates a one-time backup of a PVC to S3                              |
| `BackupRestore`    | -          | Restores a backup into a new PVC                                      |
| `BackupPolicy`     | -          | Defines an automated backup schedule for PVCs                         |

All CRDs use the API group `storage.simplyblock.io/v1alpha1`.

For the complete generated field reference, see [Simplyblock Operator API Reference](operator-api.md).

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

## Storage Nodes

Storage node management uses three separate CRDs with distinct responsibilities. Together they form a three-tier model:

```
StorageNodeSet   ──► declares which workers to use and how to configure them
      │                (fleet-level, declarative)
      ▼ creates
StorageNode      ──► represents one backend storage node instance
      │                (per-worker, read-mostly, auto-created by the operator)
      ▲ targeted by
StorageNodeOps   ──► drives a single one-shot operation to completion
                       (shutdown / restart / suspend / resume / remove)
```

## StorageNodeSet

The `StorageNodeSet` resource is the single point of configuration for a fleet of storage nodes. It declares which
Kubernetes workers to enrol, how to configure them (image versions, NUMA topology, device filtering, per-node
overrides), and how many nodes to add in parallel.

The operator creates one `StorageNode` CR per enrolled worker (and per configured NUMA socket when
`socketsToUse` has more than one entry). Those child CRs are managed automatically and must not be created or
deleted manually.

```yaml title="Example: Enrol three workers into a storage cluster"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeSet
metadata:
  name: simplyblock-node
  namespace: simplyblock
spec:
  clusterName: simplyblock-cluster
  maxLogicalVolumeCount: 20
  partitions: 0
  corePercentage: 50
  workerNodes:
    - worker-1.example.com
    - worker-2.example.com
    - worker-3.example.com
```

### Spec Fields

| Field                             | Type                  | Description                                                                                                          |
|-----------------------------------|-----------------------|----------------------------------------------------------------------------------------------------------------------|
| `clusterName`                     | string                | Name of the target `StorageCluster`. **Required, immutable**.                                                        |
| `clusterImage`                    | string                | Storage-node container image override.                                                                               |
| `spdkImage`                       | string                | SPDK service container image override.                                                                               |
| `spdkProxyImage`                  | string                | SPDK proxy container image override.                                                                                 |
| `maxLogicalVolumeCount`           | int                   | Maximum logical volumes per node.                                                                                    |
| `maxSize`                         | string                | Maximum allocatable huge pages memory (e.g., `16G`).                                                                |
| `partitions`                      | int                   | Partitions per backend storage device. **Immutable**.                                                                |
| `mgmtIfname`                      | string                | Management network interface. **Immutable**.                                                                         |
| `dataIfname`                      | []string              | Data-plane network interface names.                                                                                  |
| `corePercentage`                  | int                   | Percentage of CPU cores allocated to SPDK (0–99).                                                                    |
| `reservedSystemCPU`               | string                | CPUs reserved for system workloads (e.g., `0,1`).                                                                    |
| `enableCpuTopology`               | bool                  | Enable topology-aware CPU scheduling.                                                                                |
| `socketsToUse`                    | []string              | NUMA sockets to deploy storage on (e.g., `["0","1"]`).                                                               |
| `nodesPerSocket`                  | int                   | Storage nodes per NUMA socket. **Immutable**.                                                                        |
| `journalManager.count`            | int                   | Journal manager count.                                                                                               |
| `journalManager.percentPerDevice` | int                   | Journal manager capacity as a percentage of each device.                                                             |
| `pcieAllowList`                   | []string              | PCIe addresses of NVMe devices to include.                                                                           |
| `pcieDenyList`                    | []string              | PCIe addresses of NVMe devices to exclude.                                                                           |
| `pcieModel`                       | string                | Filter devices by PCI model string.                                                                                  |
| `deviceNames`                     | []string              | Explicit NVMe namespace names (alternative to PCIe filtering).                                                       |
| `driveSizeRange`                  | string                | Filter devices by capacity range (e.g., `100G-2T`).                                                                  |
| `forceFormat4K`                   | bool                  | Force 4K block-size formatting. **Immutable**.                                                                       |
| `skipKubeletConfiguration`        | bool                  | Skip kubelet configuration changes during node setup.                                                                |
| `openShiftCluster`                | bool                  | Enable OpenShift-specific behaviour.                                                                                 |
| `ubuntuHost`                      | bool                  | Indicate the host OS is Ubuntu.                                                                                      |
| `tolerations`                     | []Toleration          | Pod tolerations applied to storage-node DaemonSet pods.                                                              |
| `workerNodes`                     | []string              | Kubernetes worker node names to enrol. **Required, max 200**.                                                        |
| `maxParallelNodeAdds`             | int                   | Maximum number of nodes added concurrently (default: `1`).                                                           |
| `spdkSystemMemory`                | string                | Memory reserved for the SPDK system allocator (e.g., `4G`).                                                          |
| `expand`                          | bool                  | Mark this set as a cluster-expansion add.                                                                            |
| `nodeConfigs`                     | map[string]Overrides  | Per-worker configuration overrides keyed by worker hostname.                                                         |
| `nodeFailureDomains`              | map[string]int        | Failure-domain assignment per worker (integer ≥ 1).                                                                  |
| `imagePullPolicy`                 | string                | Image pull policy: `Always`, `Never`, or `IfNotPresent`.                                                             |
| `containerResources`              | ResourceRequirements  | CPU/memory requests and limits for the main storage-node container.                                                  |
| `initContainerResources`          | ResourceRequirements  | CPU/memory requests and limits for init containers.                                                                  |

### Status Fields

| Field                                | Type   | Description                                                                                        |
|--------------------------------------|--------|----------------------------------------------------------------------------------------------------|
| `totalNodes`                         | int    | Total number of owned `StorageNode` CRs.                                                           |
| `onlineNodes`                        | int    | Count of nodes currently in `online` state.                                                        |
| `offlineNodes`                       | int    | Count of nodes in `offline` state.                                                                 |
| `suspendedNodes`                     | int    | Count of nodes in `suspended` state.                                                               |
| `creatingNodes`                      | int    | Count of nodes in `in_creation` state.                                                             |
| `removedNodes`                       | int    | Count of nodes in `removed` state.                                                                 |
| `nodes[].uuid`                       | string | Backend node UUID.                                                                                 |
| `nodes[].hostname`                   | string | Kubernetes node hostname.                                                                          |
| `nodes[].status`                     | string | Backend lifecycle state.                                                                           |
| `nodes[].health`                     | bool   | Whether health checks are currently passing.                                                       |
| `nodes[].mgmtIp`                     | string | Management IP address.                                                                             |
| `nodes[].rpcPort`                    | int    | Node RPC service port.                                                                             |
| `nodes[].lvolPort`                   | int    | Logical volume subsystem port.                                                                     |
| `nodes[].nvmfPort`                   | int    | NVMe-oF service port.                                                                              |
| `drainCoordination[].hostname`       | string | Kubernetes node name being drained.                                                                |
| `drainCoordination[].activeNodeUUID` | string | Backend UUID of the storage node being shut down or restarted.                                     |
| `drainCoordination[].phase`          | string | Drain phase: `detected`, `shutdown_called`, `draining`, `restart_called`, `complete`, or `failed`. |
| `drainCoordination[].message`        | string | Additional status detail or error information.                                                     |
| `drainCoordination[].startedAt`      | string | Timestamp when drain coordination began for this node.                                             |

## StorageNode

The `StorageNode` resource represents a single backend storage node instance. One `StorageNode` CR is created
automatically by the operator for each (worker, NUMA socket) combination declared in a `StorageNodeSet`. These
CRs are read-mostly — their spec is set at creation and is effectively immutable.

```bash title="List all StorageNode instances"
kubectl get storagenodes -n simplyblock
```

```plain title="Example output"
NAME                                                   WORKER                      SOCKET  NODEIDX  UUID                                   STATUS   HEALTH  AGE
simplyblock-node-worker-1.example.com-s0-n0            worker-1.example.com        0       0        a1b2c3d4-...                           online   true    10m
simplyblock-node-worker-2.example.com-s0-n0            worker-2.example.com        0       0        b2c3d4e5-...                           online   true    8m
simplyblock-node-worker-3.example.com-s0-n0            worker-3.example.com        0       0        c3d4e5f6-...                           online   true    6m
```

### Spec Fields

| Field               | Type   | Description                                                                           |
|---------------------|--------|---------------------------------------------------------------------------------------|
| `storageNodeSetRef` | string | Name of the owning `StorageNodeSet`. **Required, immutable**.                         |
| `workerNode`        | string | Kubernetes node hostname. **Required, immutable**.                                    |
| `socketID`          | string | NUMA socket identifier from `socketsToUse`. **Immutable**.                            |
| `nodeIndex`         | int    | Per-socket node index (0…nodesPerSocket-1). **Immutable**.                            |
| `socketIndex`       | int    | Global ordinal across all sockets on this worker. **Immutable**.                      |
| `overrides`         | object | Per-node configuration overrides. See [StorageNode Overrides](#storagenode-overrides). |

### StorageNode Overrides

`spec.overrides` allows any field from the parent `StorageNodeSet` to be tuned on a per-node basis. Overrides win
over fleet defaults. They can be set in two ways:

1. **Via `StorageNodeSet.spec.nodeConfigs`** — the operator propagates the matching entry to the `StorageNode` CR
   automatically.
2. **Directly on a manually-created `StorageNode` CR** — useful when you need fine-grained control over a single
   node, for example during expansion.

#### Overrides Reference

| Field                  | Type     | Description                                                                                  |
|------------------------|----------|----------------------------------------------------------------------------------------------|
| `maxLogicalVolumeCount`| int      | Maximum logical volumes for this node.                                                       |
| `maxSize`              | string   | Maximum allocatable huge pages memory (e.g., `16G`).                                         |
| `spdkImage`            | string   | SPDK image override (e.g., for phased rollouts of a new image version).                      |
| `spdkProxyImage`       | string   | SPDK proxy image override.                                                                   |
| `spdkSystemMemory`     | string   | SPDK huge-page memory allocation (e.g., `4G`, `512M`). Useful for nodes with less RAM.      |
| `corePercentage`       | int      | Percentage of CPU cores allocated to SPDK (0–99).                                            |
| `journalManager`       | object   | Journal manager tuning (`count`, `percentPerDevice`).                                        |
| `pcieAllowList`        | []string | PCIe addresses allowed for this node.                                                        |
| `pcieDenyList`         | []string | PCIe addresses excluded on this node.                                                        |
| `pcieModel`            | string   | PCI model string filter for this node.                                                       |
| `driveSizeRange`       | string   | Drive size range filter (e.g., `100G-2T`).                                                   |
| `deviceNames`          | []string | Explicit NVMe namespace names (e.g., `["nvme0n1","nvme1n1"]`).                               |
| `enableCpuTopology`    | bool     | Topology-aware CPU scheduling override.                                                      |
| `reservedSystemCPU`    | string   | CPUs reserved for system workloads (e.g., `0,1`).                                            |
| `failureDomain`        | int      | Failure-domain group index (≥ 1). Required when the cluster has `enableFailureDomains=true`. |
| `expand`               | bool     | Mark this node as a cluster-expansion add (triggers rebalancing on the backend).             |

#### Use Cases

**Different memory allocation per node**

Some nodes may have less RAM. Override `spdkSystemMemory` to cap huge-page allocation:

```yaml
# StorageNodeSet.spec.nodeConfigs
nodeConfigs:
  low-ram-worker.example.com:
    spdkSystemMemory: "2G"
```

**Failure domain assignment**

Required when the `StorageCluster` has `enableFailureDomains: true`. Assign each worker to a domain so the
cluster can maintain fault tolerance across racks or availability zones:

```yaml
nodeConfigs:
  worker-rack-a-1.example.com:
    failureDomain: 1
  worker-rack-a-2.example.com:
    failureDomain: 1
  worker-rack-b-1.example.com:
    failureDomain: 2
  worker-rack-b-2.example.com:
    failureDomain: 2
```

**Node-level volume limit**

Limit the number of volumes on a specific node that has fewer or smaller devices:

```yaml
nodeConfigs:
  small-worker.example.com:
    maxLogicalVolumeCount: 5
```

**Expansion add (manual StorageNode CR)**

When creating a `StorageNode` CR manually for cluster expansion, set `expand: true` so the backend applies
rebalancing rather than treating it as a fresh node. Combine with any other node-specific tuning:

```yaml
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNode
metadata:
  name: simplyblock-node-vm15-expansion
  namespace: simplyblock
spec:
  storageNodeSetRef: simplyblock-node
  workerNode: vm15.simplyblock3.localdomain
  socketIndex: 0
  overrides:
    expand: true
    maxLogicalVolumeCount: 20
    spdkSystemMemory: "4G"
    failureDomain: 2
```

**Device filtering per node**

Use different device selection strategies per node when hardware is mixed across workers:

```yaml
nodeConfigs:
  nvme-only-worker.example.com:
    deviceNames:
      - nvme0n1
      - nvme1n1
  pcie-filter-worker.example.com:
    pcieAllowList:
      - "0000:01:00.0"
      - "0000:02:00.0"
    driveSizeRange: "1.7T-2T"
```

### Status Fields

| Field               | Type   | Description                                                 |
|---------------------|--------|-------------------------------------------------------------|
| `uuid`              | string | Backend storage node UUID (set after provisioning).         |
| `status`            | string | Backend lifecycle status (`online`, `offline`, `suspended`, `in_creation`, etc.). |
| `health`            | bool   | Backend health flag.                                        |
| `hostname`          | string | Node hostname as reported by the backend.                   |
| `resources.cpu`     | int    | SPDK CPU cores allocated.                                   |
| `resources.memory`  | string | SPDK memory allocation.                                     |
| `resources.volumes` | int    | Current logical volume count.                               |
| `resources.devices` | string | Device summary (online/total).                              |
| `ports.management`  | string | Management IP address.                                      |
| `ports.nvmeof`      | int    | NVMe-oF fabric port.                                        |
| `ports.lvol`        | int    | Logical volume subsystem port.                              |
| `ports.rpc`         | int    | RPC/management API port.                                    |
| `postedAt`          | string | Timestamp of the node-add POST (provisioning guard).        |

## StorageNodeOps

The `StorageNodeOps` resource drives a single one-shot operation against one `StorageNode`. It is analogous to a
Kubernetes `Job` — the operator executes the requested action, records the outcome, and the CR is left in a
terminal state. Only one `StorageNodeOps` may be active for a given `StorageNode` at a time.

```yaml title="Example: Restart a specific storage node"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeOps
metadata:
  name: restart-worker-1
  namespace: simplyblock
spec:
  storageNodeRef: simplyblock-node-worker-1.example.com-s0-n0
  action: restart
```

```yaml title="Example: Remove (drain) a storage node"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeOps
metadata:
  name: drain-worker-1
  namespace: simplyblock
spec:
  storageNodeRef: simplyblock-node-worker-1.example.com-s0-n0
  action: remove
```

### Spec Fields

| Field              | Type   | Description                                                                                              |
|--------------------|--------|----------------------------------------------------------------------------------------------------------|
| `storageNodeRef`   | string | Name of the target `StorageNode` CR. **Required, immutable**.                                            |
| `action`           | string | Operation: `shutdown`, `restart`, `suspend`, `resume`, `remove`. **Required, immutable**.                |
| `force`            | bool   | Force execution where the backend supports it.                                                           |
| `reattachVolume`   | bool   | Reattach volumes during restart (`restart` only).                                                        |
| `drain.systemVolumeFilterRegex` | string | Go regex matching system volumes to exclude from migration and delete in the Verifying phase. Defaults to `^sb-fio-baseline-.*`. |

### Status Fields

| Field             | Type   | Description                                                                                           |
|-------------------|--------|-------------------------------------------------------------------------------------------------------|
| `phase`           | string | High-level lifecycle: `Pending`, `Running`, `Succeeded`, or `Failed`.                                 |
| `subPhase`        | string | Active drain step (`remove` only): `Validating`, `Suspending`, `Migrating`, `Verifying`, `Removing`.  |
| `message`         | string | Human-readable state description or failure reason.                                                   |
| `volumesMigrated` | int    | Number of volumes successfully migrated (`remove` only).                                              |
| `volumesPending`  | int    | Number of volumes still awaiting migration (`remove` only).                                           |
| `startedAt`       | string | Operation start timestamp.                                                                            |
| `completedAt`     | string | Operation completion timestamp.                                                                       |

### Supported Actions

| Action     | Expected outcome after success                                    |
|------------|-------------------------------------------------------------------|
| `shutdown` | Node transitions to `offline`.                                    |
| `restart`  | Node transitions back to `online`.                                |
| `suspend`  | Node transitions to `suspended`.                                  |
| `resume`   | Node transitions back to `online`.                                |
| `remove`   | Node is drained, all volumes migrated, node deleted from backend. |
| `migrate`  | Node is relocated to a different Kubernetes worker, promoted.     |

### Migrating a Storage Node to a Different Worker (`migrate`)

The `migrate` action **relocates** a storage node to a different Kubernetes worker without removing it from the
cluster. Unlike `remove`, the node retains its backend UUID, its data partitions, and its logical-volume
assignments — no `VolumeMigration` CRs are created and no volumes are moved between nodes. The backend rebalance
triggered by the final promote redistributes load automatically.

```yaml title="Example: Relocate a storage node to a different worker"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeOps
metadata:
  name: migrate-worker-1
  namespace: simplyblock
spec:
  storageNodeRef: simplyblock-node-worker-1.example.com-s0-n0
  action: migrate
  targetWorkerNode: worker-5.example.com
```

**`migrate`-specific spec fields:**

| Field              | Type     | Description                                                                                            |
|--------------------|----------|--------------------------------------------------------------------------------------------------------|
| `targetWorkerNode` | string   | Kubernetes worker hostname to relocate the node to. **Required for `migrate`**, immutable.             |
| `reattachVolume`   | bool     | Reattach volumes during the restart phase.                                                             |
| `newSsdPcie`       | []string | Additional NVMe PCIe addresses to bind on the target host (passed as `new_ssd_pcie` to the backend).  |

**Sub-phases for `migrate`:**

| SubPhase      | Description                                                                                                   |
|---------------|---------------------------------------------------------------------------------------------------------------|
| `Preparing`   | Operator clones per-node config to the target worker, labels it into the storage plane, and waits until the storage-node-api pod is Ready and reachable. |
| `Restarting`  | Operator issues a control-plane restart pointing at the target host. Waits for the node to leave `online` (restart started) and return to `online` (restart finished). |
| `Promoting`   | Operator issues `/promote` on the relocated node, triggering a cluster rebalance. StorageNodeSet.workerNodes is updated to replace the source worker with the target. |

### Pinned Volume Behaviour During `remove`

PVCs annotated with `simplyblock.io/pinned-volume` affect the `remove` drain flow:

- If the annotation value is a **valid storage node UUID** (different from the node being drained), the volume is
  migrated to that specific node — drain proceeds normally.
- If the annotation value is **empty, not a UUID, or self-referencing** (pointing to the node being drained),
  drain is blocked and a `PinnedVolumeBlocking` event is emitted naming the affected PVC.

To migrate a pinned volume to a specific node, set the annotation to the target node UUID before draining:

```bash title="Set migration target for a pinned volume"
kubectl annotate pvc <pvc-name> -n <namespace> \
  simplyblock.io/pinned-volume=<target-storage-node-uuid> --overwrite
```

See [Pinned Volume Migration During Node Removal](../maintenance-operations/node-drain-coordination.md#pinned-volume-migration-during-node-removal) for full details.


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
