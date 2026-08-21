---
title: "Simplyblock Operator"
description: "The simplyblock Kubernetes operator manages simplyblock storage clusters, storage nodes, pools, logical volumes, and devices using Custom Resource Definitions (CRDs)."
weight: 20090
---

The simplyblock Kubernetes operator provides a declarative, Kubernetes-native interface for managing simplyblock storage
infrastructure. Instead of using the CLI, administrators can define storage clusters, storage nodes, pools, and logical
volumes as Kubernetes Custom Resource Definitions (CRDs). The operator continuously reconciles the desired state with
the actual state of the simplyblock cluster.

## Overview

The operator manages the following Custom Resource Definitions (CRDs):

| CRD                                             | Short Name | Description                                                        |
|-------------------------------------------------|------------|--------------------------------------------------------------------|
| [`StorageCluster`](reference.md#storagecluster) | -          | Creates and manages a simplyblock storage cluster                  |
| [`StorageNodeSet`](reference.md#storagenodeset) | -          | Fleet-level declarative management of storage nodes across workers |
| [`StorageNode`](reference.md#storagenode)       | -          | Represents a single backend storage node instance (auto-created)   |
| [`StorageNodeOps`](reference.md#storagenodeops) | -          | One-shot operational action targeting a single storage node        |
| [`StoragePool`](reference.md#storagepool)       | -          | Creates and manages storage pools                                  |
| [`Task`](reference.md#task)                     | -          | Monitors cluster tasks and their status                            |
| [`StorageBackup`](reference.md#storagebackup)   | -          | Creates a one-time backup of a PVC to S3                           |
| [`BackupRestore`](reference.md#backuprestore)   | -          | Restores a backup into a new PVC                                   |
| [`BackupPolicy`](reference.md#backuppolicy)     | -          | Defines an automated backup schedule for PVCs                      |

All CRDs use the API group `storage.simplyblock.io/v1alpha1`.

For the complete generated field reference, see [Simplyblock Operator Reference](reference.md).

## Auto-Managed CSI Credentials

The cluster identifier is the `StorageCluster` resource name (`metadata.name`). The operator uses that name when
creating the backend cluster and the cluster credential Secret.

When a `StorageCluster` is created or becomes active, the operator automatically creates or updates the
`simplyblock-csi-secret-v2` Secret in the operator's namespace with the cluster's credentials. This Secret is
consumed by the CSI driver and requires no manual management. When the cluster is deleted, the operator removes
the cluster's entry from the Secret automatically.

## Storage Nodes

Storage node management uses three separate CRDs with distinct responsibilities. Together, they form a three-tier model:

```plain
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
Kubernetes workers to enroll, how to configure them (image versions, NUMA topology, device filtering, per-node
overrides), and how many nodes to add in parallel.

The operator creates one `StorageNode` CR per enrolled worker (and per configured NUMA socket when
`socketsToUse` has more than one entry). Those child CRs are managed automatically and must not be created or
deleted manually.

```yaml title="Example: Enroll three workers into a storage cluster"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeSet
metadata:
  name: simplyblock-node
  namespace: simplyblock
spec:
  clusterName: simplyblock-cluster
  workerNodes:
    - worker-1.example.com
    - worker-2.example.com
    - worker-3.example.com
```

The complete set of `StorageNodeSet` fields is available in [StorageNodeSet reference](reference.md#storagenodeset).

## StorageNode

The `StorageNode` resource represents a single backend storage node instance. One `StorageNode` CR is created
automatically by the operator for each (worker, NUMA socket) combination declared in a `StorageNodeSet`. These
CRs are read-mostly: their spec is set at creation and is effectively immutable.

```bash title="List all StorageNode instances"
kubectl get storagenodes -n simplyblock
```

```plain title="Example output"
NAME                                                   WORKER                      SOCKET  NODEIDX  UUID                                   STATUS   HEALTH  AGE
simplyblock-node-worker-1.example.com-s0-n0            worker-1.example.com        0       0        a1b2c3d4-...                           online   true    10m
simplyblock-node-worker-2.example.com-s0-n0            worker-2.example.com        0       0        b2c3d4e5-...                           online   true    8m
simplyblock-node-worker-3.example.com-s0-n0            worker-3.example.com        0       0        c3d4e5f6-...                           online   true    6m
```

### StorageNode Overrides

`spec.overrides` allows any field from the parent `StorageNodeSet` to be tuned on a per-node basis. Overrides win
over fleet defaults. They can be set in two ways:

1. **Via `StorageNodeSet.spec.nodeConfigs`:** the operator propagates the matching entry to the `StorageNode` CR
   automatically.
2. **Directly on a manually created `StorageNode` CR:** useful for fine-grained control over a single
   node, for example, during expansion.

#### Overrides Reference

| Field               | Type     | Description                                                                                  |
|---------------------|----------|----------------------------------------------------------------------------------------------|
| `spdkImage`         | string   | SPDK image override (e.g., for phased rollouts of a new image version).                      |
| `spdkProxyImage`    | string   | SPDK proxy image override.                                                                   |
| `spdkSystemMemory`  | string   | SPDK huge-page memory allocation (e.g., `4G`, `512M`). Useful for nodes with less RAM.       |
| `journalManager`    | object   | Journal manager tuning (`count`, `percentPerDevice`).                                        |
| `pcieAllowList`     | []string | PCIe addresses allowed for this node.                                                        |
| `pcieDenyList`      | []string | PCIe addresses excluded on this node.                                                        |
| `pcieModel`         | string   | PCI model string filter for this node.                                                       |
| `driveSizeRange`    | string   | Drive size range filter (e.g., `100G-2T`).                                                   |
| `deviceNames`       | []string | Explicit NVMe namespace names (e.g., `["nvme0n1","nvme1n1"]`).                               |
| `enableCpuTopology` | bool     | Topology-aware CPU scheduling override.                                                      |
| `reservedSystemCPU` | string   | CPUs reserved for system workloads (e.g., `0,1`).                                            |
| `failureDomain`     | int      | Failure-domain group index (≥ 1). Required when the cluster has `enableFailureDomains=true`. |
| `expand`            | bool     | Mark this node as a cluster-expansion add (triggers rebalancing on the backend).             |

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

The complete set of `StorageNode` fields is available in [StorageNode reference](reference.md#storagenode).

## StorageNodeOps

The `StorageNodeOps` resource drives a single one-shot operation against one `StorageNode`. It is analogous to a
Kubernetes `Job`, in that the requested action is executed by the operator, the outcome is recorded, and the CR is
left in a terminal state. Only one `StorageNodeOps` may be active for a given `StorageNode` at a time.

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

### Supported Actions

| Action     | Expected outcome after success                                    |
|------------|-------------------------------------------------------------------|
| `shutdown` | Node transitions to `offline`.                                    |
| `restart`  | Node transitions back to `online`.                                |
| `suspend`  | Node transitions to `suspended`.                                  |
| `resume`   | Node transitions back to `online`.                                |
| `remove`   | Node is drained, all volumes migrated, node deleted from backend. |
| `migrate`  | Node is relocated to a different Kubernetes worker, promoted.     |

The complete set of `StorageNodeOps` fields is available in [StorageNodeOps reference](reference.md#storagenodeops).

## Migrating a Storage Node to a Different Worker (`migrate`)

The `migrate` action **relocates** a storage node to a different Kubernetes worker without removing it from the
cluster. Unlike `remove`, the node retains its backend UUID, its data partitions, and its logical-volume
assignments, and no `VolumeMigration` CRs are created or volumes moved between nodes. The backend rebalance
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

| Field              | Type     | Description                                                                                          |
|--------------------|----------|------------------------------------------------------------------------------------------------------|
| `targetWorkerNode` | string   | Kubernetes worker hostname to relocate the node to. **Required for `migrate`**, immutable.           |
| `reattachVolume`   | bool     | Reattach volumes during the restart phase.                                                           |
| `newSsdPcie`       | []string | Additional NVMe PCIe addresses to bind on the target host (passed as `new_ssd_pcie` to the backend). |

**Sub-phases for `migrate`:**

| SubPhase     | Description                                                                                                                                                            |
|--------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Preparing`  | Operator clones per-node config to the target worker, labels it into the storage plane, and waits until the storage-node-api pod is Ready and reachable.               |
| `Restarting` | Operator issues a control-plane restart pointing at the target host. Waits for the node to leave `online` (restart started) and return to `online` (restart finished). |
| `Promoting`  | Operator issues `/promote` on the relocated node, triggering a cluster rebalance. StorageNodeSet.workerNodes is updated to replace the source worker with the target.  |

### Pinned Volume Behavior During `remove`

PVCs annotated with `simplyblock.io/pinned-volume` affect the `remove` drain flow:

- If the annotation value is a **valid storage node UUID** (different from the node being drained), the volume is
  migrated to that specific node and the drain proceeds normally.
- If the annotation value is **empty, not a UUID, or self-referencing** (pointing to the node being drained),
  drain is blocked and a `PinnedVolumeBlocking` event is emitted naming the affected PVC.

To migrate a pinned volume to a specific node, set the annotation to the target node UUID before draining:

```bash title="Set migration target for a pinned volume"
kubectl annotate pvc <pvc-name> -n <namespace> \
  simplyblock.io/pinned-volume=<target-storage-node-uuid> --overwrite
```

See [Pinned Volume Migration During Node Removal](../../kubernetes/operations/node-drain-coordination.md#pinned-volume-migration-during-node-removal) for full details.


## Storage Pool

The `StoragePool` resource creates and manages storage pools. When a pool becomes active, the operator automatically
creates a Kubernetes `StorageClass` named `simplyblock-<namespace>-<clusterName>-<poolName>`. The StorageClass is deleted
when the pool is deleted.

```yaml title="Example: Create a storage pool"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StoragePool
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

The complete set of `StoragePool` fields is available in [StoragePool reference](reference.md#storagepool).

### Auto-Created StorageClass

The pool identifier is the `StoragePool` resource name (`metadata.name`). The operator uses that name as the backend pool
name and as the `pool_name` CSI StorageClass parameter.

When the pool reaches an active state, the operator creates a `StorageClass` with:

- **Name:** `simplyblock-<namespace>-<clusterName>-<poolName>`
- **Provisioner:** `csi.simplyblock.io`
- **VolumeBindingMode:** `WaitForFirstConsumer`
- **ReclaimPolicy:** `Delete`
- **AllowVolumeExpansion:** `true`

The `cluster_id` and `pool_name` parameters are set automatically. Any fields specified in
`spec.storageClassParameters` are merged in as additional CSI driver parameters.

Because Kubernetes StorageClass parameters are immutable after creation, the StorageClass is created once and
left unchanged if it already exists. To change parameters, delete the pool and recreate it with updated values.

The StorageClass is deleted when the pool is deleted.

### Snapshot Cloning

When a volume is cloned from a snapshot, the `clonedFromSnapshot` and `sourceSnapshotName` fields in its status entry identify the origin. These fields are read-only and set by the backend at creation time, so they cannot be specified in the `Lvol` spec.

To see which volumes in a pool are snapshot clones:

```bash
kubectl get simplyblocklvol cluster-volumes -n simplyblock -o jsonpath='{.status.lvols[?(@.clonedFromSnapshot!="")].lvolName}'
```

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

The complete set of `Task` fields is available in [Task reference](reference.md#task).

## StorageBackup

The `StorageBackup` resource creates a one-time backup of a PVC to the S3-compatible storage endpoint configured
in the `StorageCluster`. For backup configuration prerequisites, see
[Backup and Recovery](../../kubernetes/operations/backup-recovery.md).

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

The complete set of `StorageBackup` fields is available in [StorageBackup reference](reference.md#storagebackup).

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

!!! warning
    `BackupRestore` can only restore a PVC to the same namespace as the restore object.

The complete set of `BackupRestore` fields is available in [BackupRestore reference](reference.md#backuprestore).

## BackupPolicy

The `BackupPolicy` resource defines an automated backup schedule with retention settings. Policies are attached
to PVCs using the `simplybk/backup-policy` Kubernetes annotation, which causes `StorageBackup` objects to be
created automatically on schedule. Removing the annotation detaches the policy, and updating it switches the PVC
to the new policy.

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
kubectl annotate pvc my-pvc -n simplyblock simplyblock.io/backup-policy=my-policy
```

The schedule format is a space-separated list of `interval,count` pairs. For example, `15m,4 60m,11 24h,7` means:
take a backup every 15 minutes (keep the 4 most recent), every 60 minutes (keep 11), and every 24 hours (keep 7).

The complete set of `BackupPolicy` fields is available in [BackupPolicy reference](reference.md#backuppolicy).
