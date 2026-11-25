---
title: "Removing a Storage Node"
description: "Drain and remove a simplyblock storage node with a Remove operation, which evacuates its volumes onto the remaining nodes before the node leaves the cluster."
weight: 10240
---

The `Remove` action of a `StorageNodeOps` resource takes a storage node out of the cluster. It is a drain, not a
delete: the node's volumes and devices are migrated onto the remaining nodes first, and only an empty node is
removed. The operation runs through seven steps and reports how far the evacuation has progressed.

!!! warning
    A storage node that is removed without being drained makes the logical volumes it owns inaccessible. The `Remove`
    action is the only supported way to take a node out of a cluster. To move a node to a different host instead, use
    [Migrating a Storage Node](migrating-a-storage-node.md), which keeps the node and its volumes.

## Requesting a Removal

A removal is requested either with a `StorageNodeOps` or by deleting the `StorageNode` resource.

```yaml title="Example of a node removal (remove-node.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageNodeOps
metadata:
  name: remove-worker-1
  namespace: simplyblock
spec:
  nodeRef: simplyblock-cluster-worker-1-0
  action: Remove
```

```bash title="Removing a storage node"
kubectl apply -f remove-node.yaml
```

| Field                                 | Type   | Default               | Description                                                                            |
|---------------------------------------|--------|-----------------------|----------------------------------------------------------------------------------------|
| `spec.remove.systemVolumeFilterRegex` | string | `^sb-fio-baseline-.*` | Go regular expression matched against backend volume names to identify system volumes. |

### Deleting the StorageNode

Deleting a `StorageNode` that is registered with the control plane does not delete the backend node directly. The
operator raises a `StorageNodeOps` named `<storage-node>-remove` with the action `Remove`, owned by the node, and holds
the finalizer of the `StorageNode` until that operation has succeeded. A `StorageNode` that never received a backend
UUID is deleted at once.

```bash title="Removing a storage node by deleting it"
kubectl delete storagenode simplyblock-cluster-worker-1-0 -n simplyblock --wait=false
kubectl get storagenodeops simplyblock-cluster-worker-1-0-remove -n simplyblock -w
```

If the removal fails or is aborted, the `StorageNode` stays, and an `OperationFailed` event with the reason is repeated
on it. Once the cause is fixed, deleting the finished `<storage-node>-remove` record makes the operator raise a new
removal.

## Steps

The removal walks the steps below, tracked in `status.step.state` while `status.phase` is `Running`. The control
plane shuts the node down and rebuilds its devices onto its peers (`ShuttingDown` and `MigratingDevices`), and later
takes the node apart (`Removing` and `AwaitingRemoval`). The operator itself drives the volume migration between
them (`MigratingVolumes`) and the checks around it (`Validating`, `Verifying`).

| Step               | Deadline   | Description                                                                               |
|--------------------|------------|-------------------------------------------------------------------------------------------|
| `Validating`       | 24 hours   | The node's volumes are classified, and the preconditions for a drain are checked.         |
| `ShuttingDown`     | 15 minutes | The node is shut down, so that it serves nothing while its devices and volumes are moved. |
| `MigratingDevices` | 7 hours    | The control plane rebuilds the node's devices onto its peers.                             |
| `MigratingVolumes` | 12 hours   | The volumes are migrated off the node, one migration object per NVMe-oF subsystem.        |
| `Verifying`        | 30 minutes | The system volumes are deleted, and the node is confirmed empty.                          |
| `Removing`         | 2 hours    | The empty node is removed from the cluster.                                               |
| `AwaitingRemoval`  | 7 hours    | The control plane finishes taking the node apart.                                         |

`MigratingDevices` and `AwaitingRemoval` bound a control-plane process without progress rather than a flat total:
every change of the node's status or of one of its devices moves the deadline a whole budget out again, so a rebuild
or a teardown that keeps moving is waited on for as long as it moves.

Unlike the other node operations, a removal runs whatever the state of the cluster, since removing a node is sometimes
what makes an unready cluster ready again. A node that the control plane no longer knows counts as removed, so every
step succeeds at once for a node that is already gone.

### Validating

Every volume the control plane reports on the node is sorted into one of four groups.

- **System:** The volume name matches `spec.remove.systemVolumeFilterRegex`. It is skipped by the migration and deleted
  in `Verifying`.
- **Managed:** A `PersistentVolume` accounts for the volume. It is migrated.
- **Pinned:** The claim of the volume carries the `storage.simplyblock.io/selected-storage-node` annotation. It
  cannot be moved off the node, so the removal fails outright rather than holding.
- **Unmanaged:** No `PersistentVolume` accounts for the volume, for example, because it was created outside Kubernetes.
  It holds the step with a `DrainBlocked` event.

A pinned volume is resolved by removing the annotation, or by changing it to the UUID of another storage node, which
moves the volume there, and the node is removed again with a new `StorageNodeOps`. An unmanaged volume has to be
removed by hand. See [Automatic Volume Placement](../../usage/volume-placement.md) for pinning.

Once no volume blocks, the step checks the failure-domain balance the removal would leave. A refusal holds the step
with a `RemovalNotAdmitted` event while the node still serves. The control plane's own admission (fault-tolerance
headroom, failure-domain balance, replica relocation, and active tasks) is not checked here. It runs in
`MigratingDevices`, when the node is already offline.

At the end of the step, the number of managed volumes is written to `status.drain.volumesTotal`.

### ShuttingDown

The node is shut down, through its own shutdown action, before anything is moved off it. A node already offline, or
past this step, is not shut down again. A `409` is a shutdown precondition not met yet — a peer restarting or
shutting down, a migration or restart task, a live restart claim — and the step holds with a `RemovalDeferred` event
until it clears. Any other refusal fails the operation with the node still serving.

### MigratingDevices

Once the node is down, the control plane rebuilds its devices onto its peers. The first request is where the control
plane admits the removal. A refusal for a passing condition, such as rebalancing or an active task, holds the step
with a `RemovalDeferred` event. Any other refusal fails the operation and leaves the node offline, and a
[Restart](restarting-a-storage-node.md) operation brings it back. The step sends the request again on every pass while
the rebuild runs, which the control plane treats as a no-op or as a restart of a rebuild that stopped. A node still
stuck short of being shut down is retried up to three times before the operation fails.

### MigratingVolumes

Every `PersistentVolume`-managed volume is moved to a peer, one migration object per NVMe-oF subsystem the node
hosts, rather than one per volume. It is labeled `storage.simplyblock.io/drain-node` with the UUID of the node being
drained, and it names the removal in its `spec.creatorRef`. Targets are spread round-robin across the online peers of
the node, so the evacuated volumes do not land on one node.

```bash title="Listing the volume migrations of a drain"
kubectl get persistentvolumeops \
    -l storage.simplyblock.io/drain-node=82198a36-fcbb-43e3-949c-0260bf40f0ac
```

```bash title="Watching the evacuation progress"
kubectl get storagenodeops remove-worker-1 -n simplyblock \
    -o jsonpath='{.status.step.state}{" migrated="}{.status.drain.volumesMigrated}{" total="}{.status.drain.volumesTotal}{"\n"}'
```

A migration that fails is kept until the step ends, as the record of the peer the subsystem could not move to. A new
migration to another peer is created beside it, and a `MigrationRetried` event records it. Completed migrations are
deleted once all of them have finished, and `status.drain.volumesMigrated` keeps the count.
While no online peer is available, the step holds with a `NoMigrationTarget` event, and it continues once one returns.
A `DrainCompleted` event is emitted when every volume has been moved. The individual migrations are described in
[Volume Migration](../volumes/volume-migration.md).

### Verifying

The system volumes that were skipped during the drain are deleted, since they are per-node benchmark volumes and are
not worth migrating. A system volume that cannot be deleted fails the operation. Any other volume still reported on
the node holds the step with a `DrainBlocked` event. Once the node carries none, the control plane's own check closes
the step; if it still reports a volume or a snapshot the node's own records missed, the step holds on that instead.

### Removing

The empty node is removed from the cluster. A refusal the control plane gives a reason for fails the operation
outright, and the node is left offline — a [Restart](restarting-a-storage-node.md) operation brings it back. A
refusal caused by a passing cluster condition, such as rebalancing or an active task, holds the step with a
`RemovalDeferred` event instead and is retried.

### AwaitingRemoval

The control plane finishes taking the node apart in the background. Its devices and volumes have already moved by
then. The control plane tears down the standby copies of the node's own logical volume store on its peers, replaces
the node's journal in the journal groups of the other nodes, relocates the standby roles the node held for other
primaries, verifies them, and marks the node removed. The step closes once the control plane reports the node
removed. If the control plane gives up and reports the removal failed, the operation fails with that outcome rather
than waiting out its deadline.

## Failure and Abort Handling

`Validating` is the only step that can be stopped: it performs no side effect at all, so an abort or a delete there
ends the operation as `Aborted` immediately, with the node untouched.

From `ShuttingDown` onward there is no way back. Nothing in the `Remove` action resumes the node, the `StorageNodeOps`
record cannot be deleted, and `spec.abort` is not honored. A removal that fails past that point leaves the node
exactly where the failing step left it — shut down, mid rebuild, or partway through the volume migration — for an
operator to diagnose and recover by hand, typically with a [Restart](restarting-a-storage-node.md). Transient errors
of the control plane do not fail the operation; they are retried.

### Cleaning Up After a Removal

A `StorageNodeOps` with the action `Remove` leaves the `StorageNode` in place in the phase `Removed`, and a growth
document still counts it toward the limit of 32 storage nodes per cluster. Once the operation has `Succeeded`, the
`StorageNode` is deleted. When the removal was named `<storage-node>-remove`, the deletion finds its record and
releases the object at once. Under any other name, the deletion raises a second removal of its own.

```bash title="Deleting the StorageNode of a removed node"
kubectl delete storagenode simplyblock-cluster-worker-1-0 -n simplyblock
```

The worker keeps its storage-plane labels, `io.simplyblock.storagenodeset` and
`simplyblock.io/storage-node-uuid.<cluster-uuid>.<slot>`, so the storage-node pod stays on it until they are removed by
hand. The worker is cordoned and drained only after the `StorageNode` is deleted. A cordon before that raises a
`<storage-node>-maintenance` window for the removed node.

## Checking a Stalled Removal

A removal that makes no progress is nearly always blocked by a volume, waiting for a peer, or waiting on the control
plane's own admission. The events say which.

```bash title="Checking for blocking volumes"
kubectl get events -n simplyblock \
    --field-selector reason=DrainBlocked
```

```bash title="Checking for a missing migration target"
kubectl get events -n simplyblock \
    --field-selector reason=NoMigrationTarget
```

```bash title="Checking for a refused or deferred removal"
kubectl get events -n simplyblock \
    --field-selector reason=RemovalNotAdmitted
kubectl get events -n simplyblock \
    --field-selector reason=RemovalDeferred
```

```bash title="Reading the current message of the operation"
kubectl get storagenodeops remove-worker-1 -n simplyblock \
    -o jsonpath='{.status.message}{"\n"}'
```

## Coordination with Kubernetes Node Drains

Removing a storage node is not the same as draining the Kubernetes worker it runs on. A cordoned or drained worker is
handled separately, and automatically, by the operator. See
[Coordinated Worker Node Drain](node-drain-coordination.md).
