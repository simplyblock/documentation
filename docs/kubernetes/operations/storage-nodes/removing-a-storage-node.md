---
title: "Removing a Storage Node"
description: "Drain and remove a simplyblock storage node with the remove action, which evacuates its volumes onto the remaining nodes before the node leaves the cluster."
weight: 10240
---

The `remove` action of a `StorageNodeOps` resource takes a storage node out of the cluster. It is a drain, not a
delete: the node's volumes are migrated onto the remaining nodes first, and only an empty node is removed. The
operation runs through five sub-phases and reports how far the evacuation has progressed.

!!! danger
    A storage node that is removed without being drained makes the logical volumes it owns inaccessible. The `remove`
    action is the only supported way to take a node out of a cluster. To move a node to a different host instead, use
    [Migrating a Storage Node](migrating-a-storage-node.md), which keeps the node and its volumes.

## Requesting a Removal

```bash title="Removing a storage node"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeOps
metadata:
  name: drain-worker-1
  namespace: simplyblock
spec:
  storageNodeRef: simplyblock-node-mejue8
  action: remove
EOF
```

The name of the target `StorageNode` is read from the cluster, as described in
[Storage Node Actions](storage-node-actions.md#finding-the-target-node).

| Field                           | Type   | Default               | Description                                                                            |
|---------------------------------|--------|-----------------------|----------------------------------------------------------------------------------------|
| `drain.systemVolumeFilterRegex` | string | `^sb-fio-baseline-.*` | Go regular expression matched against backend volume names to identify system volumes. |

A removal always runs unforced, so `spec.force` has no effect on it.

## Sub-Phases

The removal progresses through the sub-phases below, tracked in `status.subPhase` while `status.phase` is `Running`.

| Sub-phase    | Description                                                                      |
|--------------|----------------------------------------------------------------------------------|
| `Validating` | The node's volumes are classified and the preconditions for a drain are checked. |
| `Suspending` | The node is suspended so that no new volume is placed on it.                     |
| `Migrating`  | The volumes are migrated off the node, one `VolumeMigration` per volume.         |
| `Verifying`  | The node is confirmed empty, and the system volumes left on it are deleted.      |
| `Removing`   | The empty node is deleted from the cluster.                                      |

### Validating

Every volume the backend reports on the node is sorted into one of three groups. A volume whose name matches the
system volume filter is ignored entirely. A volume that has a `PersistentVolume` is migratable. A volume without one is
unmanaged, for example, because it was created outside Kubernetes.

The drain does not start while any volume blocks it:

- **Pinned volume:** A PVC carrying the `simplyblock.io/selected-storage-node` annotation. A `PinnedVolumeBlocking`
  event names how many are affected, and the annotation has to be removed for the drain to proceed. See
  [Pinned Volumes](../volumes/volume-migration.md#pinned-volumes).
- **Unmanaged volume:** A volume without a `PersistentVolume`. An `UnmanagedVolumeBlocking` event is emitted, and the
  volume has to be removed by hand.

Both checks are rechecked every 60 seconds, so a drain that is blocked resumes on its own once the cause is cleared.

### Suspending

The node is suspended, which stops new volumes from being placed on it while its existing ones are moved. A node that
is already suspended is not asked again. The phase holds until the backend confirms the suspension, emitting
`DrainSuspendPending` while it waits.

### Migrating

One `VolumeMigration` resource is created per migratable volume, labeled with the UUID of the node being drained and
owned by the `StorageNodeOps`. Targets are assigned round-robin across the online nodes of the cluster, excluding the
node being drained, so the evacuated volumes spread rather than landing on one node.

Progress is counted in the operation status.

```bash title="Watching the evacuation progress"
kubectl get storagenodeops drain-worker-1 -n simplyblock \
    -o jsonpath='{.status.subPhase}{" migrated="}{.status.volumesMigrated}{" pending="}{.status.volumesPending}{"\n"}' -w
```

A migration that fails or is aborted is deleted and created again, which picks a new target, and a `MigrationRetry`
event records it. Once every migration has completed, the completed resources are deleted and the operation advances.
The individual migrations are observable while they run, as described in
[Volume Migration](../volumes/volume-migration.md#monitoring-a-migration).

If the cluster becomes unavailable during the evacuation, the drain pauses rather than failing. See
[Pausing](#pausing) below.

### Verifying

The backend is asked again which volumes remain on the node. A non-system volume that is still there holds the phase,
with a `DrainVerifyPending` event, until the backend confirms it is gone. The system volumes that were skipped during
the drain are then deleted in place, since they are benchmark artifacts and are not worth migrating.

### Removing

The empty node is deleted from the cluster, which emits `NodeRemoved` and completes the operation.

## Pausing

A drain only runs against a healthy cluster. Before each reconcile the operator checks the cluster, and if its status
is anything other than `active`, or if it is rebalancing, the drain pauses. A `DrainPaused` event records the reason,
`status.message` carries it, and the operation is retried every 60 seconds until the cluster is ready again.

The same check applies when a volume migration has failed. The failed migrations are deleted, and their recreation
waits for the cluster instead of retrying against an unhealthy one.

## Failure Handling

A drain that fails after the node has been suspended does not leave it suspended. The operator resumes the node,
emits `NodeResumed`, and only then marks the operation `Failed` with the reason in `status.message`. The cluster is
therefore left with the node in service, which is the safe outcome, and the removal can be retried with a new
`StorageNodeOps` resource once the cause has been addressed.

Transient backend errors do not fail the operation. They are classified, and a retryable error is retried rather than
treated as a failure.

## Checking a Stalled Removal

A removal that makes no progress is nearly always blocked by a volume or paused by the cluster. The events say which.

```bash title="Checking for blocking volumes"
kubectl get events -n simplyblock \
    --field-selector reason=PinnedVolumeBlocking
kubectl get events -n simplyblock \
    --field-selector reason=UnmanagedVolumeBlocking
```

```bash title="Checking whether the drain is paused"
kubectl get events -n simplyblock \
    --field-selector reason=DrainPaused
```

```bash title="Reading the current message of the operation"
kubectl get storagenodeops drain-worker-1 -n simplyblock \
    -o jsonpath='{.status.message}{"\n"}'
```

## Events

| Reason                    | Meaning                                                                 |
|---------------------------|-------------------------------------------------------------------------|
| `PinnedVolumeBlocking`    | A pinned volume prevents the drain from starting.                       |
| `UnmanagedVolumeBlocking` | A volume without a `PersistentVolume` prevents the drain from starting. |
| `DrainPaused`             | The drain is waiting for the cluster to become active.                  |
| `DrainSuspendPending`     | The node has not reported itself suspended yet.                         |
| `DrainNoMigrationTarget`  | No online node is available to receive the evacuated volumes.           |
| `MigrationRetry`          | A volume migration failed and was recreated against a new target.       |
| `MigrationCompleted`      | Every volume migration of the drain has completed.                      |
| `DrainVerifyPending`      | Volumes are still reported on the node after the evacuation.            |
| `NodeRemoved`             | The node was removed from the cluster.                                  |
| `NodeResumed`             | The drain failed and the node was resumed.                              |
| `OpsFailed`               | The removal failed. The message carries the reason.                     |

## Coordination with Kubernetes Node Drains

Removing a storage node is not the same as draining the Kubernetes worker it runs on. A cordoned or drained worker is
handled separately, and automatically, by the operator. See
[Coordinated Worker Node Drain](node-drain-coordination.md).
