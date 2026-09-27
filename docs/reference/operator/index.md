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

The operator manages the following Custom Resource Definitions (CRDs), all in the `storage.simplyblock.io` API
group.

An `Ops` kind is a one-shot operation against the kind it is named for, analogous to a Kubernetes `Job`: it drives
one action to completion, records the outcome, and stays afterward as the audit record. Only one operation acts on
a given target at a time.

| CRD                                                               | Short Name | Description                                                                                       |
|-------------------------------------------------------------------|------------|---------------------------------------------------------------------------------------------------|
| [`ClusterDeploymentConfig`](reference.md#clusterdeploymentconfig) | `cdc`      | A discovered cluster layout an administrator approves, expanded into a cluster and its nodes      |
| [`ControlPlane`](reference.md#controlplane)                       | `cp`       | FoundationDB and the management API, installed here or owned by a remote control plane            |
| [`ControlPlaneOps`](reference.md#controlplaneops)                 | `cpops`    | One operation against the control plane (`Restart`, `Upgrade`, `Backup`)                          |
| [`OperatorOps`](reference.md#operatorops)                         | `oops`     | One operation against the operator itself (`Discover`)                                            |
| [`PersistentVolumeOps`](reference.md#persistentvolumeops)         | `pvops`    | One operation against a `PersistentVolume` (`Migrate`). Cluster-scoped                            |
| [`SimplyblockDriver`](reference.md#simplyblockdriver)             | `sbd`      | The CSI driver deployment: node plugin, controller plugin, RBAC, and the `CSIDriver` they produce |
| [`StorageBackup`](reference.md#storagebackup)                     | `sb`       | One backup held in the cluster's backup store. Discovered, never authored                         |
| [`StorageBackupOps`](reference.md#storagebackupops)               | `sbops`    | One operation against a `StorageBackup`, today a restore                                          |
| [`StorageBackupPolicy`](reference.md#storagebackuppolicy)         | `sbp`      | Schedules and retains the backups of the claims it selects                                        |
| [`StorageCluster`](reference.md#storagecluster)                   | `stc`      | Creates and manages a simplyblock storage cluster                                                 |
| [`StorageClusterOps`](reference.md#storageclusterops)             | `scops`    | One operation against a `StorageCluster`                                                          |
| [`StorageDevice`](reference.md#storagedevice)                     | `sd`       | One backend device of one storage node. Discovered, never authored                                |
| [`StorageDeviceOps`](reference.md#storagedeviceops)               | `sdops`    | One operation against a `StorageDevice`                                                           |
| [`StorageNode`](reference.md#storagenode)                         | `sn`       | One backend storage node instance                                                                 |
| [`StorageNodeOps`](reference.md#storagenodeops)                   | `snops`    | One operation against a `StorageNode`                                                             |
| [`StoragePool`](reference.md#storagepool)                         | `sp`       | Creates and manages storage pools                                                                 |
| [`StoragePoolOps`](reference.md#storagepoolops)                   | `spops`    | One operation against a `StoragePool` (`Rebalance`)                                               |
| [`VolumeGroupSnapshotOps`](reference.md#volumegroupsnapshotops)   | `vgsops`   | One operation against a `VolumeGroupSnapshot` (`Restore`)                                         |

Asynchronous replication between two clusters has four kinds of its own, described in
[Asynchronous Replication](../../kubernetes/operations/data-protection/asynchronous-replication.md). They are
served at `storage.simplyblock.io/v1alpha1`, where every other kind above is served at `v1alpha2`.

| CRD                                                   | Short Name | Description                                                      |
|-------------------------------------------------------|------------|------------------------------------------------------------------|
| [`ReplicationPair`](reference.md#replicationpair)     | `relpair`  | Pairs a source cluster with a disaster-recovery target           |
| [`ReplicationPolicy`](reference.md#replicationpolicy) | `repl`     | The replication mode, interval, and snapshot retention of a pair |
| [`ReplicationSlot`](reference.md#replicationslot)     | `relslot`  | One volume's replication stream within a pair                    |
| [`ReplicationOps`](reference.md#replicationops)       | `replops`  | One operation against a replication pair, policy, or slot        |

For the complete generated field reference, see [Simplyblock Operator Reference](reference.md).

## Auto-Managed CSI Credentials

The cluster identifier is the `StorageCluster` resource name (`metadata.name`). The operator uses that name when
creating the backend cluster and the cluster credential Secret.

When a `StorageCluster` is created or becomes active, the operator automatically creates or updates the
`simplyblock-csi-secret-v2` Secret in the operator's namespace with the cluster's credentials. This Secret is
consumed by the CSI driver and requires no manual management. When the cluster is deleted, the operator removes
the cluster's entry from the Secret automatically.

## Storage Nodes

Storage node management uses three CRDs with distinct responsibilities. Together, they form a three-tier model:

```plain
StorageCluster   ──► declares the fleet: which image, which interfaces, which
      │                sockets, and how many nodes to provision at a time
      ▼ owns             (spec.storageNodes)
StorageNode      ──► represents one backend storage node instance
      │                (per-worker, read-mostly, auto-created by the operator)
      ▲ targeted by
StorageNodeOps   ──► drives a single one-shot operation to completion
                       (Shutdown / Restart / Suspend / Resume / Remove /
                        Migrate / HostMaintenance)
```

Which workers are enrolled, and how each is configured, comes from a
[`ClusterDeploymentConfig`](#clusterdeploymentconfig): the operator discovers the layout, an administrator
approves it, and the expansion writes the `StorageCluster` and one `StorageNode` per worker and NUMA socket.

## ClusterDeploymentConfig

The `ClusterDeploymentConfig` resource is a proposed cluster layout. The operator discovers the candidate workers,
their interfaces, and their devices, and writes them into the document. An administrator reviews it, sets
`spec.approved: true`, and the operator expands it into a `StorageCluster` and its `StorageNode` objects.

`spec.cluster` is the cluster template: sizing, stripe, fabric, ports, and the cluster-wide toggles. Sizing is
uniform across a cluster and is stated once here rather than per node.

`spec.nodeSets[]` is the organizational grouping of the deployment, usually a rack: the workers a document adds or
grows together. Each set has `groups[]`, and a group carries the workers and what they share:

```yaml title="Example: Two racks of workers, one failure domain each"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ClusterDeploymentConfig
metadata:
  name: production
  namespace: simplyblock
spec:
  approved: true
  cluster:
    name: simplyblock-cluster
    maxSubsystemCount: 75
    vcpuCount: 16
    stripe:
      dataChunks: 2
      parityChunks: 1
  nodeSets:
    - name: rack-a
      groups:
        - name: rack-a-nodes
          failureDomain: rack-a
          workers:
            - worker-a-1.example.com
            - worker-a-2.example.com
    - name: rack-b
      groups:
        - name: rack-b-nodes
          failureDomain: rack-b
          workers:
            - worker-b-1.example.com
            - worker-b-2.example.com
```

A group may also carry `mgmtInterface`, `dataInterfaces`, `devices`, `spdkSystemMemory`, `reservedSystemCPU`, and
`journalManager`, which is how workers with mixed hardware are described in one document.

The document is ephemeral. Everything the expansion produces is self-describing, so it can be edited or deleted
once it has been expanded.

The complete set of `ClusterDeploymentConfig` fields is available in
[ClusterDeploymentConfig reference](reference.md#clusterdeploymentconfig).

## Fleet Configuration on the StorageCluster

`StorageCluster.spec.storageNodes` holds what every storage node of the cluster shares: the SPDK image and its pull
policy, the management and data interfaces, which NUMA sockets to use and how many nodes per socket, how many nodes
may be provisioned at once, the host-level toggles, and the tolerations and resource requests of the storage-node
workload.

```yaml title="Example: Fleet configuration for a cluster's storage nodes"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageCluster
metadata:
  name: simplyblock-cluster
  namespace: simplyblock
spec:
  fabricType: tcp
  maxSubsystemCount: 75
  vcpuCount: 16
  storageNodes:
    socketsToUse:
      - "0"
    nodesPerSocket: 1
    nodeProvisioningBudget: 5
    enableCpuTopology: true
    reservedSystemCPU: "0,1"
```

`nodeProvisioningBudget` is how many workers may be added at a time. The operator creates one `StorageNode` per
enrolled worker, and per configured NUMA socket when `socketsToUse` has more than one entry. Those CRs are managed
automatically and must not be created or deleted by hand, except for the expansion case below.

## StorageNode

The `StorageNode` resource represents a single backend storage node instance. One `StorageNode` CR is created
automatically by the operator for each (worker, NUMA socket) combination the approved deployment declares. These
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

### StorageNode Configuration

`spec.config` holds the per-node configuration: what the cluster's fleet configuration says, narrowed to this node
where the hardware differs. It can be set in two ways:

1. **Via the group the node was declared under** in `ClusterDeploymentConfig.nodeSets[].groups[]`. The operator
   writes the matching entry into the `StorageNode` CR when it expands the document.
2. **Directly on a manually created `StorageNode` CR:** useful for fine-grained control over a single
   node, for example, during expansion.

`spec.nodeSet` records the group a node was declared under. It is a label rather than a reference: nothing is
fetched by it, and it exists so that a node can be traced back to the document that produced it.

#### Configuration Reference

| Field                      | Type     | Description                                                                                                                              |
|----------------------------|----------|------------------------------------------------------------------------------------------------------------------------------------------|
| `sizing`                   | object   | The vCPU count and huge-page size this node was sized from. Written by the operator alone.                                               |
| `spdkImage`                | string   | SPDK image override (e.g., for phased rollouts of a new image version).                                                                  |
| `spdkImagePullPolicy`      | string   | Pull policy for `spdkImage`.                                                                                                             |
| `spdkProxyImage`           | string   | SPDK proxy image override.                                                                                                               |
| `spdkProxyImagePullPolicy` | string   | Pull policy for `spdkProxyImage`.                                                                                                        |
| `spdkSystemMemory`         | string   | SPDK huge-page memory allocation (e.g., `4G`, `512M`). Useful for nodes with less RAM.                                                   |
| `reservedSystemCPU`        | string   | CPUs reserved for system workloads (e.g., `0,1`).                                                                                        |
| `journalManager`           | object   | Journal manager tuning (`count`, `percentPerDevice`).                                                                                    |
| `deviceNames`              | []string | Explicit NVMe namespace names (e.g., `["nvme0n1","nvme1n1"]`).                                                                           |
| `pcieAllowList`            | []string | PCIe addresses allowed for this node.                                                                                                    |
| `pcieDenyList`             | []string | PCIe addresses excluded on this node.                                                                                                    |
| `pcieModel`                | string   | PCI model string filter for this node.                                                                                                   |
| `driveSizeRange`           | string   | Drive size range filter (e.g., `100G-2T`).                                                                                               |
| `failureDomain`            | string   | Failure-domain the node belongs to. Required when the cluster has `enableFailureDomains: true`. Immutable.                               |
| `expand`                   | bool     | Marks this node as an addition to an already-active cluster, which the control plane reads as a request to rebalance onto it. Immutable. |

`enableCpuTopology` is not a per-node field. It is set once for the whole cluster, at
`StorageCluster.spec.storageNodes.enableCpuTopology`.

#### Use Cases

**Different memory allocation per group**

Some workers may have less RAM. Put them in their own group and cap the huge-page allocation there:

```yaml title="ClusterDeploymentConfig.spec.nodeSets[].groups[]"
groups:
  - name: low-ram
    workers:
      - low-ram-worker.example.com
    spdkSystemMemory: "2G"
```

**Failure domain assignment**

Required when the cluster has `enableFailureDomains: true`. Give each group a domain so the cluster can maintain
fault tolerance across racks or availability zones:

```yaml title="ClusterDeploymentConfig.spec.nodeSets[].groups[]"
groups:
  - name: rack-a-nodes
    failureDomain: rack-a
    workers:
      - worker-rack-a-1.example.com
      - worker-rack-a-2.example.com
  - name: rack-b-nodes
    failureDomain: rack-b
    workers:
      - worker-rack-b-1.example.com
      - worker-rack-b-2.example.com
```

**Device selection per group**

Use different device selection strategies per group when hardware is mixed across workers:

```yaml title="ClusterDeploymentConfig.spec.nodeSets[].groups[]"
groups:
  - name: nvme-only
    workers:
      - nvme-only-worker.example.com
    devices:
      nvme:
        - "0000:01:00.0"
        - "0000:02:00.0"
```

**Expansion add (manual StorageNode CR)**

When creating a `StorageNode` CR manually for cluster expansion, set `config.expand: true` so the backend applies
rebalancing rather than treating it as a fresh node. `spec.clusterRef` names the cluster the node joins. Combine
with any other node-specific tuning:

```yaml
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageNode
metadata:
  name: simplyblock-node-vm15-expansion
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  nodeSet: rack-b
  workerNode: vm15.simplyblock3.localdomain
  slot: 0
  config:
    expand: true
    spdkSystemMemory: "4G"
    failureDomain: rack-b
```

The complete set of `StorageNode` fields is available in [StorageNode reference](reference.md#storagenode).

## StorageNodeOps

The `StorageNodeOps` resource drives a single one-shot operation against one `StorageNode`. It is analogous to a
Kubernetes `Job`, in that the requested action is executed by the operator, the outcome is recorded, and the CR is
left in a terminal state. Only one `StorageNodeOps` may be active for a given `StorageNode` at a time.

```yaml title="Example: Restart a specific storage node"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageNodeOps
metadata:
  name: restart-worker-1
  namespace: simplyblock
spec:
  nodeRef: simplyblock-node-worker-1.example.com-s0-n0
  action: Restart
```

```yaml title="Example: Remove (drain) a storage node"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageNodeOps
metadata:
  name: drain-worker-1
  namespace: simplyblock
spec:
  nodeRef: simplyblock-node-worker-1.example.com-s0-n0
  action: Remove
```

### Supported Actions

| Action            | Expected outcome after success                                                   |
|-------------------|----------------------------------------------------------------------------------|
| `Shutdown`        | Node transitions to `offline`.                                                   |
| `Restart`         | Node transitions back to `online`.                                               |
| `Suspend`         | Node transitions to `suspended`.                                                 |
| `Resume`          | Node transitions back to `online`.                                               |
| `Remove`          | Node is drained, all volumes migrated, node deleted from backend.                |
| `Migrate`         | Node is relocated to a different Kubernetes worker, promoted.                    |
| `HostMaintenance` | Node is held offline while its host is worked on, then brought back to `online`. |

The complete set of `StorageNodeOps` fields is available in [StorageNodeOps reference](reference.md#storagenodeops).

## Migrating a Storage Node to a Different Worker (`Migrate`)

The `Migrate` action **relocates** a storage node to a different Kubernetes worker without removing it from the
cluster. Unlike `Remove`, the node retains its backend UUID, its data partitions, and its logical-volume
assignments, and no volume is moved between nodes. The backend rebalance triggered by the final promote
redistributes load automatically.

```yaml title="Example: Relocate a storage node to a different worker"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageNodeOps
metadata:
  name: migrate-worker-1
  namespace: simplyblock
spec:
  nodeRef: simplyblock-node-worker-1.example.com-s0-n0
  action: Migrate
  migrate:
    targetWorkerNode: worker-5.example.com
```

**`Migrate`-specific spec fields:**

| Field                      | Type     | Description                                                                                          |
|----------------------------|----------|------------------------------------------------------------------------------------------------------|
| `migrate.targetWorkerNode` | string   | Kubernetes worker hostname to relocate the node to. **Required for `Migrate`**, immutable.           |
| `migrate.newSsdPcie`       | []string | Additional NVMe PCIe addresses to bind on the target host (passed as `new_ssd_pcie` to the backend). |
| `reattachVolume`           | bool     | Reattach volumes during the restart step.                                                            |

**Steps for `Migrate`,** tracked in `status.step.state`:

| Step           | Description                                                                                                                                                   |
|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Preparing`    | Operator clones per-node config to the target worker, labels it into the storage plane, and waits until the storage-node-api pod is Ready and reachable.      |
| `Relocating`   | Operator issues a control-plane restart pointing at the target host, and waits for the node to leave `online`.                                                |
| `AwaitingNode` | Operator waits for the node to return to `online`, now running on the target worker.                                                                          |
| `Promoting`    | Operator issues `/promote` on the relocated node, triggering a cluster rebalance, and re-points the Kubernetes topology from the source worker to the target. |

### Pinned Volume Behavior During `Remove`

PVCs annotated with `storage.simplyblock.io/selected-storage-node` affect the `Remove` drain flow:

- If the annotation value is a **valid storage node UUID** (different from the node being drained), the volume is
  migrated to that specific node and the drain proceeds normally.
- If the annotation value is **empty, not a UUID, or self-referencing** (pointing to the node being drained),
  drain is blocked and a `PinnedVolumeBlocking` event is emitted naming the affected PVC.

To migrate a pinned volume to a specific node, set the annotation to the target node UUID before draining:

```bash title="Set migration target for a pinned volume"
kubectl annotate pvc <pvc-name> -n <namespace> \
  storage.simplyblock.io/selected-storage-node=<target-storage-node-uuid> --overwrite
```

See [Pinned Volume Migration During Node Removal](../../kubernetes/operations/storage-nodes/node-drain-coordination.md#pinned-volume-migration-during-node-removal) for full details.


## Storage Pool

The `StoragePool` resource creates and manages storage pools. A pool is one tenancy unit within a
`StorageCluster`: `spec.limits` are the ceilings the pool as a whole is held to, and `spec.volumeDefaults` are the
defaults every volume in it is created with. The two use the same units, so a pool's ceiling and a volume's default
can be compared.

```yaml title="Example: Create a storage pool"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StoragePool
metadata:
  name: production-pool
  namespace: simplyblock
spec:
  clusterRef: production
  limits:
    capacity: "10T"
    iops: 100000
    throughput:
      readWrite: 2048
      read: 1024
      write: 1024
```

The complete set of `StoragePool` fields is available in [StoragePool reference](reference.md#storagepool).

### A StorageClass Is Assigned to a Pool

A `StorageClass` is authored rather than generated, and a pool may have zero or more of them. Nothing about a pool
implies a single way to consume it: one pool can back a class with compression on and another with it off, a class
formatted `ext4` and a class formatted `xfs`. A pool with no class at all is a valid state.

The assignment is three labels on the class, not a name the operator recomputes:

```yaml title="Example: Assign a StorageClass to a pool"
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: fast-xfs
  labels:
    storage.simplyblock.io/namespace: simplyblock
    storage.simplyblock.io/cluster: production
    storage.simplyblock.io/pool: production-pool
provisioner: csi.simplyblock.io
parameters:
  cluster_id: 4f2c8a11-6b3d-4e19-9a55-0c7e1d8f2b34
  pool_name: production-pool
  max_iops: "20000"
```

All three labels are needed and none is redundant: a pool name is unique within a namespace and a cluster, so a
class naming only the pool would also match a pool of the same name in another namespace. `parameters` carries
what the driver needs to reach the backend, and the operator validates that the two agree.

`status.storageClassNames` lists the classes currently assigned to the pool, so the assignment is readable from the
pool without a cluster-wide `kubectl get storageclass`.

The parameter names are described in
[Storage Class](../../kubernetes/usage/storage-class.md#assigning-a-storageclass-to-a-storage-pool).

### The Default Pool and Its Class

A `StorageCluster` is created with a default pool named `<clusterName>-default`, so that a cluster can hold volumes
without anybody authoring a pool first. That pool alone gets one class written for it, with:

- **Name:** `simplyblock-<namespace>-<clusterName>`
- **Provisioner:** `csi.simplyblock.io`
- **VolumeBindingMode:** `WaitForFirstConsumer`
- **ReclaimPolicy:** `Delete`
- **AllowVolumeExpansion:** `true`

It carries `storage.simplyblock.io/managed-by: storagecluster` beside the three assignment labels, and is published
as `status.defaultStorageClassName`. It is an ordinary class in every respect a claim can observe; the label decides
only who may delete it. The operator deletes a class it created when the pool goes, and refuses on one it did not.

It is deliberately not marked as the Kubernetes default class. That annotation would make every claim naming no
class bind through this driver cluster-wide, which is a decision an administrator can see the consequences of and
the operator cannot.

Because Kubernetes `StorageClass` parameters are immutable after creation, `spec.volumeDefaults` is immutable once
the pool is created. A pool whose defaults changed would have a class the operator cannot update and a spec that no
longer describes it.

## Cluster Tasks

Backend tasks (migrations, rebalancing, and the like) are reported on the cluster that runs them, in
`status.tasks`. Each entry carries the task's `id`, `type`, `status`, and `retry` count. Completed and canceled
tasks leave the list and become Kubernetes events, so its length tracks concurrency rather than history.

```bash title="Monitor the running tasks of a cluster"
kubectl get storagecluster simplyblock-cluster -n simplyblock -o jsonpath='{.status.tasks}'
```

A task can be canceled through a [`StorageClusterOps`](reference.md#storageclusterops) with
`action: CancelTask`.

## StorageBackup

The `StorageBackup` resource is one backup held in the S3-compatible store configured on the `StorageCluster`. It
is discovered rather than authored: the operator walks the store and creates an object per backup it finds, so the
set of objects follows from the location rather than accumulating. Nothing about the object requests a backup, and
`spec` is only the backup's identity.

```yaml title="A StorageBackup, as the operator writes it"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageBackup
metadata:
  name: my-backup
  namespace: simplyblock
spec:
  clusterRef: production
  backupID: 7fab02f8-03f6-4e76-a9ac-78b63b1ce8ef
```

`status.backup` describes the copy and `status.source` what the volume was when the copy was taken. Restoring one
is a `StorageBackupOps`, and scheduling them is a `StorageBackupPolicy`.

```bash title="List the backups of a cluster"
kubectl get storagebackups -n simplyblock
```

For backup configuration prerequisites, see
[Backup and Recovery](../../kubernetes/operations/data-protection/backup-recovery.md).

The complete set of `StorageBackup` fields is available in [StorageBackup reference](reference.md#storagebackup).

## StorageBackupOps

The `StorageBackupOps` resource performs one operation against a `StorageBackup`, which today means a restore. It
runs to a terminal phase and stays afterward as the audit record of what was restored, into which pool, and how it
ended.

```yaml title="Example: Restore a backup into a new PVC"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageBackupOps
metadata:
  name: my-restore
  namespace: simplyblock
spec:
  clusterRef: production
  backupRef: my-backup
  action: Restore
  restore:
    claimName: restored-pvc
    targetPool: production-pool
```

`spec.restore` parameterizes the action: `claimName` is the `PersistentVolumeClaim` to create and `targetPool` the
pool to restore into. `claimLabels` and `claimAnnotations` are copied onto the new claim.

The claim a restore produces is not owned by the operation and outlives it: deleting the `StorageBackupOps` does
not delete the restored volume. `status.persistentVolumeName` names the volume that was created.

The complete set of `StorageBackupOps` fields is available in
[StorageBackupOps reference](reference.md#storagebackupops).

## StorageBackupPolicy

The `StorageBackupPolicy` resource schedules and retains the backups of the claims it selects. It is the only thing
that decides a backup is taken; the copies themselves belong to the control plane and are pruned by its retention.

A policy selects its claims with a label selector rather than being attached to them one at a time:

```yaml title="Example: Back up every claim labeled tier=production"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageBackupPolicy
metadata:
  name: my-policy
  namespace: simplyblock
spec:
  clusterRef: production
  claimSelector:
    matchLabels:
      tier: production
  schedule: "15m,4 60m,11 24h,7"
  maxVersions: 10
  maxAge: "7d"
```

The schedule format is a space-separated list of `interval,count` pairs. For example, `15m,4 60m,11 24h,7` means:
take a backup every 15 minutes (keep the 4 most recent), every 60 minutes (keep 11), and every 24 hours (keep 7).

`spec.schedule` is immutable. The control plane offers no endpoint that applies a changed schedule, so a mutable
field would leave the declaration and the backups actually being taken permanently disagreeing. Changing a schedule
means replacing the policy.

The complete set of `StorageBackupPolicy` fields is available in
[StorageBackupPolicy reference](reference.md#storagebackuppolicy).
