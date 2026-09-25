---
title: "Simplyblock Operator"
description: "Overview of the Simplyblock Operator API storage.simplyblock.io/v1alpha2: served versions, resource kinds, the common Ops shape, metrics, and label keys."
weight: 20090
---

The Simplyblock Operator provides a declarative, Kubernetes-native interface for installing and operating simplyblock.
The control plane, the CSI driver, storage clusters, storage nodes, devices, pools, and backups are described by
custom resources of the API group `storage.simplyblock.io`, and the operator continuously reconciles their desired
state with the actual state of the simplyblock cluster. Imperative operations, such as restarting a node or migrating a
volume, are separate `*Ops` resources rather than fields on the entities.

The current API version is `storage.simplyblock.io/v1alpha2`. All examples in this documentation use it.

For the complete field reference, see [Simplyblock Operator Reference](reference.md).

## Served Versions

Every kind of the API group falls into one of three groups. No CRD is marked as deprecated.

| Group                  | Served versions                                   | Storage version | Kinds                                                                                                                                                                                                                               |
|------------------------|---------------------------------------------------|-----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Converted              | `v1alpha1` and `v1alpha2`, converted by a webhook | `v1alpha2`      | `ControlPlane`, `StorageCluster`, `StorageClusterOps`, `StorageNode`, `StorageNodeOps`, `StoragePool`, `StorageBackup`                                                                                                              |
| New                    | `v1alpha2` only                                   | `v1alpha2`      | `ClusterDeploymentConfig`, `ControlPlaneOps`, `OperatorOps`, `PersistentVolumeOps`, `SimplyblockDriver`, `StorageBackupOps`, `StorageBackupPolicy`, `StorageDevice`, `StorageDeviceOps`, `StoragePoolOps`, `VolumeGroupSnapshotOps` |
| Legacy and replication | `v1alpha1` only                                   | `v1alpha1`      | `ReplicationPair`, `ReplicationPolicy`, `ReplicationSlot`, `ReplicationOps`, `VolumeMigration`, `BackupPolicy`, `BackupRestore`, `BackupImport`, `StorageNodeSet`, `Task`                                                           |

A fresh installation stores `v1alpha2` from the start and does not deploy the conversion webhook. A cluster upgraded
from an earlier release keeps `v1alpha1` as the stored form of the converted kinds until the objects are rewritten by
the upgrade.

The `v1alpha1`-only kinds have the following status:

- **Replication:** `ReplicationPair`, `ReplicationPolicy`, `ReplicationSlot`, and `ReplicationOps` are active and
  keep their `v1alpha1` shape, including lowercase enum values. See
  [Asynchronous Replication](../../kubernetes/operations/data-protection/asynchronous-replication.md).
- **VolumeMigration:** Superseded by `PersistentVolumeOps`. Its controller only runs with the Helm value
  `volumeMigration.legacy: true`. See
  [Legacy VolumeMigration](../../kubernetes/operations/volumes/volume-migration.md#legacy-volumemigration).
- **BackupPolicy, BackupRestore, and BackupImport:** Superseded by `StorageBackupPolicy` and `StorageBackupOps`.
  `BackupImport` is retired. See [Backup and Recovery](../../kubernetes/operations/data-protection/backup-recovery.md).
- **StorageNodeSet:** Retired. The CRD is still shipped, but no controller reconciles it. Its settings moved to
  `StorageCluster.spec.storageNodes`, and storage nodes are generated from a `ClusterDeploymentConfig`.
- **Task:** Not part of the current model. Backend tasks are reported in `StorageCluster.status.tasks`.

## Resource Kinds

Every `v1alpha2` kind belongs to one of three categories:

- **Entity:** A resource that declares desired state and is reconciled continuously.
- **Observed:** A resource that mirrors backend state. It is written by the operator only.
- **Action:** An `*Ops` resource that runs one operation against one target and then stays as its record.

| Kind                      | Short name | Scope                                  | Category | Purpose                                                                                                                 | Documentation                                                                                                                                                                                                                |
|---------------------------|------------|----------------------------------------|----------|-------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `ControlPlane`            | `cp`       | Namespaced, singleton `simplyblock`    | Entity   | The control plane (FoundationDB and management API), installed locally or managed elsewhere. Created by the Helm chart. | [Install Simplyblock Operator](../../kubernetes/installation/k8s-control-plane.md), [Control Plane Cluster Architecture](../../kubernetes/installation/management-cluster-architecture.md)                                   |
| `ControlPlaneOps`         | `cpops`    | Namespaced                             | Action   | `Restart`, `Upgrade`, or `Backup` of a local control plane.                                                             | [Upgrading a Cluster](../../kubernetes/operations/cluster/cluster-upgrade.md), [FoundationDB Backup and Restore](../../kubernetes/operations/data-protection/foundationdb-backup.md)                                         |
| `SimplyblockDriver`       | `sbd`      | Namespaced, one per Kubernetes cluster | Entity   | The CSI driver deployment. Created by the Helm chart.                                                                   | [Install Simplyblock Operator](../../kubernetes/installation/k8s-control-plane.md#waiting-for-the-control-plane-and-the-csi-driver), [Connecting to an External Control Plane](../../kubernetes/installation/install-csi.md) |
| `OperatorOps`             | `oops`     | Namespaced                             | Action   | `Discover`: probes the workers and writes a draft `ClusterDeploymentConfig`.                                            | [Create a Storage Cluster](../../kubernetes/installation/k8s-storage-plane.md#discover-workers-and-devices)                                                                                                                  |
| `ClusterDeploymentConfig` | `cdc`      | Namespaced                             | Entity   | A complete deployment in one document. Once approved, it is expanded into a storage cluster and its nodes.              | [Create a Storage Cluster](../../kubernetes/installation/k8s-storage-plane.md#review-the-draft)                                                                                                                              |
| `StorageCluster`          | `stc`      | Namespaced, at most one per namespace  | Entity   | One simplyblock storage cluster. Owns its nodes and pools and creates the default pool.                                 | [Create a Storage Cluster](../../kubernetes/installation/k8s-storage-plane.md), [Multi-Tenancy](../../kubernetes/operations/security/multi-tenancy.md#one-storagecluster-per-namespace)                                      |
| `StorageClusterOps`       | `scops`    | Namespaced                             | Action   | `Activate`, `Expand`, `Shutdown`, `Start`, `Restart`, `RollingRestart`, or `CancelTask`.                                | [Storage Cluster Actions](../../kubernetes/operations/cluster/cluster-actions.md)                                                                                                                                            |
| `StorageNode`             | `sn`       | Namespaced                             | Entity   | One storage node on a worker and socket. Owned by its cluster.                                                          | [Storage Nodes](../../kubernetes/operations/storage-nodes/index.md)                                                                                                                                                          |
| `StorageNodeOps`          | `snops`    | Namespaced                             | Action   | `Shutdown`, `Restart`, `Suspend`, `Resume`, `Remove`, `Migrate`, or `HostMaintenance`.                                  | [Storage Node Actions](../../kubernetes/operations/storage-nodes/storage-node-actions.md)                                                                                                                                    |
| `StorageDevice`           | `sd`       | Namespaced                             | Observed | Mirrors one device of a storage node. Owned by its node.                                                                | [Cluster Health](../../kubernetes/operations/monitoring/cluster-health.md)                                                                                                                                                   |
| `StorageDeviceOps`        | `sdops`    | Namespaced                             | Action   | `Restart` of one device.                                                                                                | [Restarting a Storage Device](../../kubernetes/operations/storage-nodes/storage-node-actions.md#restarting-a-storage-device)                                                                                                 |
| `StoragePool`             | `sp`       | Namespaced                             | Entity   | A tenancy unit with limits, volume defaults, and allowed nodes. StorageClasses attach to it by label.                   | [Multi-Tenancy](../../kubernetes/operations/security/multi-tenancy.md#storage-pools-as-tenancy-units), [Storage Class](../../kubernetes/usage/storage-class.md)                                                              |
| `StoragePoolOps`          | `spops`    | Namespaced                             | Action   | `Rebalance` is declared but refused at run time.                                                                        | [Operation Kinds](../../kubernetes/operations/index.md#operation-kinds)                                                                                                                                                      |
| `PersistentVolumeOps`     | `pvops`    | Cluster                                | Action   | `Migrate`: moves the logical volume of a PersistentVolume to another storage node.                                      | [Volume Migration](../../kubernetes/operations/volumes/volume-migration.md)                                                                                                                                                  |
| `StorageBackup`           | `sb`       | Namespaced                             | Observed | One backup found in the backup store. Users cannot create or delete it.                                                 | [Listing Backups](../../kubernetes/operations/data-protection/backup-recovery.md#listing-backups)                                                                                                                            |
| `StorageBackupPolicy`     | `sbp`      | Namespaced                             | Entity   | Backup schedule and retention for the claims its selector matches.                                                      | [Backup Policies](../../kubernetes/operations/data-protection/backup-recovery.md#backup-policies)                                                                                                                            |
| `StorageBackupOps`        | `sbops`    | Namespaced                             | Action   | `Restore` of a backup into a new PersistentVolumeClaim.                                                                 | [Restoring a Backup](../../kubernetes/operations/data-protection/backup-recovery.md#restoring-a-backup)                                                                                                                      |
| `VolumeGroupSnapshotOps`  | `vgsops`   | Namespaced                             | Action   | `Restore` of every member of a VolumeGroupSnapshot.                                                                     | [Snapshotting](../../kubernetes/usage/snapshotting.md#restoring-a-volume-group-snapshot)                                                                                                                                     |

The names of `StorageCluster`, `StorageNode`, and `StoragePool` resources, and every `clusterRef`, are limited to
63 characters.

## Common Ops Shape

Every `*Ops` kind shares one shape. The full description, with examples, is in
[Operations](../../kubernetes/operations/index.md#the-operation-pattern).

- **`spec.action`:** The operation to perform, as a PascalCase value, for example, `Restart` or `RollingRestart`. It
  is required and immutable.
- **Target reference:** The entity the operation acts on, for example, `spec.clusterRef` or `spec.nodeRef`. It is
  immutable. `OperatorOps` has no target reference.
- **`spec.abort`:** The only mutable field. Setting it to `true` stops a running operation at its current step, if
  that step can be stopped cleanly.
- **`status.phase`:** `Pending`, `Running`, `Succeeded`, `Failed`, or `Aborted`. The last three are terminal.
- **`status.step`:** The current step, as `state` and `deadline`. A step that outlives its deadline fails the
  operation.
- **Further status fields:** `status.message`, `status.startedAt`, `status.completedAt`, and
  `status.observedGeneration`.

Only one operation acts on an entity at a time. The operation that holds the lock is named in `status.activeOpsRef` of
the target. For PersistentVolumes, the lock is the annotation `storage.simplyblock.io/active-ops`. A second operation
for the same target waits in `Pending`. A finished operation cannot be edited or re-run, and a running operation whose
current step cannot be aborted cannot be deleted.

All Ops kinds emit the same event reasons:

| Reason                 | Meaning                                                      |
|------------------------|--------------------------------------------------------------|
| `OperationQueued`      | The target is held by another operation, and this one waits. |
| `OperationStarted`     | The operation acquired the lock on its target and started.   |
| `OperationSucceeded`   | The operation completed.                                     |
| `OperationFailed`      | The operation failed. The message carries the reason.        |
| `OperationAborted`     | The operation was stopped through `spec.abort`.              |
| `StepDeadlineExceeded` | A step outlived its deadline, which fails the operation.     |

## Metrics API

The operator also serves the read-only API `metrics.simplyblock.io/v1alpha2` through an aggregated API server. Its
kinds are not CRDs and are not stored. The API is enabled by default through the Helm value `metricsAPI.enabled`.

| Kind                    | Short name | Named after                                 |
|-------------------------|------------|---------------------------------------------|
| `StorageClusterMetrics` | `scm`      | The `StorageCluster`                        |
| `StorageNodeMetrics`    | `snm`      | The `StorageNode`                           |
| `StoragePoolMetrics`    | `spm`      | The `StoragePool`                           |
| `StorageDeviceMetrics`  | `sdm`      | The `StorageDevice`                         |
| `LogicalVolumeMetrics`  | `lvm`      | The PersistentVolumeClaim, in its namespace |

Each reading carries a `timestamp` and a `capacity` block. For the fields and access control, see
[Capacity Metrics API](../../kubernetes/operations/monitoring/index.md#capacity-metrics-api).

## Labels and Annotations

Labels and annotations are written with the prefix `storage.simplyblock.io/`, for example,
`storage.simplyblock.io/selected-storage-node` on a PersistentVolumeClaim. The older spellings with the prefixes
`simplyblock.io/` and `simplybk/` are still read, so objects created by earlier releases keep working. When an object
carries more than one spelling, the newest one wins.

The following keys are still read only under the old `simplyblock.io/` prefix:

| Key                                       | Carried by                                | Documentation                                                                                            |
|-------------------------------------------|-------------------------------------------|----------------------------------------------------------------------------------------------------------|
| `simplyblock.io/pod-affinity`             | A PersistentVolumeClaim                   | [Automatic Volume Placement](../../kubernetes/usage/volume-placement.md#co-locating-a-volume-with-a-pod) |
| `simplyblock.io/auto-restart-on-pathloss` | A StorageClass or a PersistentVolumeClaim | [Recovering from Path Loss](../../kubernetes/operations/volumes/path-loss-recovery.md)                   |
| `simplyblock.io/guardian-disable`         | A PersistentVolumeClaim                   | [Recovering from Path Loss](../../kubernetes/operations/volumes/path-loss-recovery.md)                   |
| `simplyblock.io/trigger-realignment`      | A `StorageCluster`                        | [Data Realignment](../../kubernetes/operations/volumes/volume-migration.md#data-realignment)             |

Pinned volumes, which carry `storage.simplyblock.io/selected-storage-node`, are covered in
[Pinned Volumes](../../kubernetes/operations/volumes/volume-migration.md#pinned-volumes) and, for node removal, in
[Removing a Storage Node](../../kubernetes/operations/storage-nodes/removing-a-storage-node.md#validating).

## Field Reference

The [Simplyblock Operator Reference](reference.md) lists every field of every kind. It is generated from the Go API
types of the operator by `scripts/operator-reference-gen.sh` and must not be edited by hand.
