---
title: "Removing a Storage Node"
description: "Drain and remove a simplyblock storage node with a Remove operation, which evacuates its volumes onto the remaining nodes before the node leaves the cluster."
weight: 10240
---

The `Remove` action of a `StorageNodeOps` resource takes a storage node out of the cluster. It is a drain, not a
delete: the node's volumes are migrated onto the remaining nodes first, and only an empty node is removed. The
operation runs through five steps and reports how far the evacuation has progressed.

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
the finalizer of the `StorageNode` until that operation has reached a terminal phase. A `StorageNode` that never
received a backend UUID is deleted at once.

```bash title="Removing a storage node by deleting it"
kubectl delete storagenode simplyblock-cluster-worker-1-0 -n simplyblock --wait=false
kubectl get storagenodeops simplyblock-cluster-worker-1-0-remove -n simplyblock -w
```

A removal that fails leaves the operation as the record of why, and the `StorageNode` is released anyway, so the object
is not held by a drain nobody retries.

## Steps

The removal walks the steps below, tracked in `status.step.state` while `status.phase` is `Running`.

| Step               | Deadline   | Description                                                                      |
|--------------------|------------|----------------------------------------------------------------------------------|
| `Validating`       | 24 hours   | The node's volumes are classified and the preconditions for a drain are checked. |
| `Suspending`       | 15 minutes | The node is suspended so that no new volume is placed on it.                     |
| `MigratingVolumes` | 12 hours   | The volumes are migrated off the node, one `PersistentVolumeOps` per volume.     |
| `Verifying`        | 30 minutes | The system volumes are deleted, and the node is confirmed empty.                 |
| `Removing`         | 30 minutes | The empty node is removed from the cluster.                                      |

Unlike the other node operations, a removal runs whatever the state of the cluster, since removing a node is sometimes
what makes an unready cluster ready again. A node that the control plane no longer knows counts as removed, so every
step succeeds at once for a node that is already gone.

### Validating

Every volume the control plane reports on the node is sorted into one of four groups.

- **System:** The volume name matches `spec.remove.systemVolumeFilterRegex`. It is skipped by the migration and deleted
  in `Verifying`.
- **Managed:** A `PersistentVolume` accounts for the volume. It is migrated.
- **Pinned:** The claim of the volume carries the `storage.simplyblock.io/selected-storage-node` annotation. It blocks
  the drain.
- **Unmanaged:** No `PersistentVolume` accounts for the volume, for example, because it was created outside Kubernetes.
  It blocks the drain.

While any volume blocks, the step holds with a `DrainBlocked` warning that names the volumes and what to do about them.
The node is not suspended yet, so it stays fully in service while the blocker is resolved. A pinned volume is resolved
by removing the annotation, or by changing it to the UUID of another storage node, which moves the volume there. An
unmanaged volume has to be removed by hand. See [Automatic Volume Placement](../../usage/volume-placement.md) for
pinning.

At the end of the step, the number of managed volumes is written to `status.drain.volumesTotal`.

### Suspending

The node is suspended, which stops new volumes from being placed on it while its existing ones are moved. A node that
is already suspended or offline is not asked again.

### MigratingVolumes

One cluster-scoped `PersistentVolumeOps` with the action `Migrate` is created per managed volume. It is labeled
`storage.simplyblock.io/drain-node` with the UUID of the node being drained, and it names the removal in its
`spec.creatorRef`. Targets are spread round-robin across the online peers of the node, so the evacuated volumes do not
land on one node.

```bash title="Listing the volume migrations of a drain"
kubectl get persistentvolumeops \
    -l storage.simplyblock.io/drain-node=82198a36-fcbb-43e3-949c-0260bf40f0ac
```

```bash title="Watching the evacuation progress"
kubectl get storagenodeops remove-worker-1 -n simplyblock \
    -o jsonpath='{.status.step.state}{" migrated="}{.status.drain.volumesMigrated}{" total="}{.status.drain.volumesTotal}{"\n"}'
```

A migration that fails is deleted and created again against another peer, and a `MigrationRetried` event records it.
Completed migrations are deleted once all of them have finished, and `status.drain.volumesMigrated` keeps the count.
While no online peer is available, the step holds with a `NoMigrationTarget` event, and it continues once one returns.
A `DrainCompleted` event is emitted when every volume has been moved. The individual migrations are described in
[Volume Migration](../volumes/volume-migration.md).

### Verifying

The system volumes that were skipped during the drain are deleted, since they are per-node benchmark volumes and are
not worth migrating. A system volume that cannot be deleted fails the operation. Any other volume still reported on the
node holds the step with a `DrainBlocked` event, until the control plane confirms it is gone.

### Removing

The empty node is removed from the cluster. A removal that the control plane refuses, for example, because the
failure domains of the cluster would no longer be balanced, fails the operation.

## Failure and Abort Handling

A removal that fails or is aborted after the node has been suspended does not leave it suspended. The operator resumes
the node before it marks the operation `Failed` or `Aborted`, with the reason in `status.message`. The cluster is
therefore left with the node in service, which is the safe outcome, and the removal can be retried with a new
`StorageNodeOps` once the cause has been addressed. If the resume itself fails, a `NodeResumeFailed` event is emitted,
and the node is brought back with [Resuming a Storage Node](resuming-a-storage-node.md).

A removal can be aborted in every step except `Removing`. Deleting a running removal aborts its volume migrations
first. Transient errors of the control plane do not fail the operation, they are retried.

## Checking a Stalled Removal

A removal that makes no progress is nearly always blocked by a volume or waiting for a peer. The events say which.

```bash title="Checking for blocking volumes"
kubectl get events -n simplyblock \
    --field-selector reason=DrainBlocked
```

```bash title="Checking for a missing migration target"
kubectl get events -n simplyblock \
    --field-selector reason=NoMigrationTarget
```

```bash title="Reading the current message of the operation"
kubectl get storagenodeops remove-worker-1 -n simplyblock \
    -o jsonpath='{.status.message}{"\n"}'
```

## Coordination with Kubernetes Node Drains

Removing a storage node is not the same as draining the Kubernetes worker it runs on. A cordoned or drained worker is
handled separately, and automatically, by the operator. See
[Coordinated Worker Node Drain](node-drain-coordination.md).
