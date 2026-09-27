---
title: "Operations"
description: "Operate a simplyblock deployment on Kubernetes through the Ops resources of the Simplyblock Operator: lifecycle, data protection, monitoring, and security."
weight: 40000
---

This section covers the operation of a running simplyblock deployment on Kubernetes: the lifecycle of a storage
cluster and its storage nodes, the placement and the protection of the data on them, and the monitoring and the
security of the deployment.

Entities such as a `StorageCluster` or a `StorageNode` describe what exists. They carry no action field. Every
imperative operation, such as a restart, a shutdown, or a node removal, is requested by creating a separate operation
resource, one of the `*Ops` kinds of the `storage.simplyblock.io/v1alpha2` API. The Simplyblock Operator calls the
control plane, drives the operation to completion, and records its progress in the status of that resource, so no
access to the control plane itself is needed.

## The Operation Pattern

Every Ops kind shares one shape. An operation acts on exactly one target, which it names by reference, and it runs
once. After it has finished, it stays in the cluster as the record of what was done, to which target, with which
parameters, and how it ended.

```yaml title="Example of an operation resource"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageNodeOps
metadata:
  name: restart-worker-1
  namespace: simplyblock
spec:
  nodeRef: simplyblock-cluster-worker-1-0
  action: Restart
```

### Spec

- **`spec.action`:** The operation to perform, as a PascalCase value such as `Restart`, `RollingRestart`, or
  `HostMaintenance`. It is required and immutable.
- **Target reference:** The entity the operation acts on, for example, `spec.clusterRef` or `spec.nodeRef`. It is
  required and immutable. An operation never owns its target, so deleting the operation never deletes the entity.
  `OperatorOps`, which probes the workers, is the one kind without a target reference.
- **Parameter block:** Some actions take parameters in a block named after the action, for example,
  `spec.rollingRestart` or `spec.migrate`. A block is ignored by every other action.
- **`spec.abort`:** The only field that can be changed after the operation was created. Setting it to `true` asks a
  running operation to stop at its current step.

A finished operation cannot be edited or re-run. Repeating an operation means creating a new resource with a new name.

### Status

| Field                       | Description                                                                    |
|-----------------------------|--------------------------------------------------------------------------------|
| `status.phase`              | `Pending`, `Running`, `Succeeded`, `Failed`, or `Aborted`.                     |
| `status.step.state`         | The step of the action that is currently running, for example, `Awaiting`.     |
| `status.step.deadline`      | The time at which the current step expires.                                    |
| `status.message`            | One sentence that explains the current phase, replaced as the operation moves. |
| `status.startedAt`          | When the operation acquired the lock on its target.                            |
| `status.completedAt`        | When the operation reached a terminal phase.                                   |
| `status.observedGeneration` | The generation of the spec the status was computed from.                       |

`Succeeded`, `Failed`, and `Aborted` are terminal. `Aborted` is distinct from `Failed`: an operation that was called
off did not go wrong.

Every step has a deadline. A step that is still running when its deadline passes fails the operation with a
`StepDeadlineExceeded` event. A step that is waiting by design, for example, on a peer node to come back, therefore
does not wait forever, and a stalled operation can be told apart from one that is still making progress.

```bash title="Following an operation"
kubectl get storagenodeops restart-worker-1 -n simplyblock -w
```

```bash title="Reading the step and its deadline"
kubectl get storagenodeops restart-worker-1 -n simplyblock \
    -o jsonpath='{.status.phase}{" "}{.status.step.state}{" "}{.status.step.deadline}{"\n"}'
```

### One Operation at a Time

Only one operation acts on an entity at a time. The operation that holds the lock is named in the `status.activeOpsRef`
field of the target, for example, `StorageNode.status.activeOpsRef`. A second operation for the same target is admitted,
waits in the `Pending` phase with an `OperationQueued` event, and starts once the lock is free. Several operations can
therefore be created up front, and they are served one after another.

```bash title="Finding the operation that holds a storage node"
kubectl get storagenode simplyblock-cluster-worker-1-0 -n simplyblock \
    -o jsonpath='{.status.activeOpsRef}{"\n"}'
```

### Events

The operator emits the same event reasons on every Ops kind.

| Reason                 | Meaning                                                      |
|------------------------|--------------------------------------------------------------|
| `OperationQueued`      | The target is held by another operation, and this one waits. |
| `OperationStarted`     | The operation acquired the lock on its target and started.   |
| `OperationSucceeded`   | The operation completed.                                     |
| `OperationFailed`      | The operation failed. The message carries the reason.        |
| `OperationAborted`     | The operation was stopped through `spec.abort`.              |
| `StepDeadlineExceeded` | A step outlived its deadline, which fails the operation.     |

Events of a `StorageNodeOps` are also mirrored onto the `StorageNode` it targets, so the history of a node can be read
from the node itself.

### Aborting and Deleting an Operation

An abort is honored only in a step that can be stopped cleanly, typically a step before the operation has asked the
control plane for anything. In any other step, the operation carries on, and `status.message` states that the abort
arrived too late.

```bash title="Aborting a running operation"
kubectl patch storagenodeops restart-worker-1 -n simplyblock \
    --type=merge -p '{"spec": {"abort": true}}'
```

A terminal operation can be deleted at any time. A running operation whose current step cannot be aborted cannot be
deleted either: a validating webhook refuses the deletion, because removing the record would not stop the work, and it
would leave the target locked by an object that no longer exists. Examples are a rolling restart while a node is
offline, or a node migration in its `Promoting` step.

## Operation Kinds

| Kind                     | Short name | Target                | Actions                                                                              |
|--------------------------|------------|-----------------------|--------------------------------------------------------------------------------------|
| `StorageClusterOps`      | `scops`    | `StorageCluster`      | `Activate`, `Expand`, `Shutdown`, `Start`, `Restart`, `RollingRestart`, `CancelTask` |
| `StorageNodeOps`         | `snops`    | `StorageNode`         | `Shutdown`, `Restart`, `Suspend`, `Resume`, `Remove`, `Migrate`, `HostMaintenance`   |
| `StorageDeviceOps`       | `sdops`    | `StorageDevice`       | `Restart`                                                                            |
| `StoragePoolOps`         | `spops`    | `StoragePool`         | None usable yet. `Rebalance` is declared but refused at run time.                    |
| `ControlPlaneOps`        | `cpops`    | `ControlPlane`        | `Restart`, `Upgrade`, `Backup`                                                       |
| `OperatorOps`            | `oops`     | The worker nodes      | `Discover`                                                                           |
| `PersistentVolumeOps`    | `pvops`    | `PersistentVolume`    | `Migrate`                                                                            |
| `StorageBackupOps`       | `sbops`    | `StorageBackup`       | `Restore`                                                                            |
| `VolumeGroupSnapshotOps` | `vgsops`   | `VolumeGroupSnapshot` | `Restore`                                                                            |

`PersistentVolumeOps` is cluster-scoped. Every other kind is namespaced and lives in the namespace of its target.
`VolumeGroupSnapshotOps` is the one kind without `spec.abort` and without the `Aborted` phase.

Some operations are raised by the operator itself. A cordoned worker raises a `HostMaintenance` operation, deleting a
`StorageNode` that holds data raises a `Remove` operation, and a node removal raises one `PersistentVolumeOps` per volume
it moves.

## Sections

| Section                                     | Contents                                                                        |
|---------------------------------------------|---------------------------------------------------------------------------------|
| [Cluster](cluster/index.md)                 | Cluster operations, rolling restarts, upgrades, failure domains, node affinity. |
| [Storage Nodes](storage-nodes/index.md)     | Node operations, migration, removal, replacement, and worker maintenance.       |
| [Scaling](scaling/index.md)                 | Expanding a cluster and adding storage nodes in parallel.                       |
| [Volumes](volumes/index.md)                 | Volume migration, filesystem trimming, and recovery from path loss.             |
| [Data Protection](data-protection/index.md) | Backup and recovery, asynchronous replication, FoundationDB backup.             |
| [Monitoring](monitoring/index.md)           | Cluster health, logical volume conditions, alerts, dashboards, and logs.        |
| [Security](security/index.md)               | Authentication, transport encryption, volume encryption, and multi-tenancy.     |
