---
title: "Coordinated Worker Node Drain"
description: "How the Simplyblock operator automatically protects storage availability during Kubernetes node maintenance such as cordon, drain, and rolling OS upgrades."
weight: 10250
---

When a Kubernetes worker node is cordoned or drained, for example, during a rolling OS upgrade or node replacement,
the Simplyblock Operator automatically coordinates the shutdown and restart of the backend storage node running on
that worker. No manual intervention is required.

This is a temporary absence, after which the storage node returns to the same worker. Taking a node out of the
cluster for good is a different operation, described in
[Removing a Storage Node](removing-a-storage-node.md).

Concurrency is controlled by `StorageCluster.spec.maxConcurrentWorkerRestarts`. It defines the at-most number of
Kubernetes workers that can be drained at the same time. This prevents the cluster from entering a degraded state
during bulk maintenance operations and restarting cycles.

## How It Works

The operator watches Kubernetes `Node` objects. When a worker becomes cordoned, it raises a `StorageNodeOps` with
`action: HostMaintenance` against the storage node on that worker. Nobody has to create one, and one created by hand
is accepted and behaves identically.

Modeling the window as an operation is what gives it the discipline the other node actions have: it takes the node's
lock, so nothing else touches a node whose host is rebooting; its position is a persisted step rather than a phase
string; and it stays afterward as the audit record of the maintenance window.

The `PodDisruptionBudget` runs backward from the usual one. A per-node budget allowing no disruption is created
**before** the shutdown, so `kubectl drain` blocks on it while the backend node is taken down gracefully. Relaxing
it is what lets the drain proceed.

!!! warning
    If another worker is already in a maintenance window and `maxConcurrentWorkerRestarts` would be exceeded, the
    operator holds the new window at the `Holding` step until an in-progress one completes, to ensure that the
    cluster remains available and connection loss is mitigated.

## Steps

Each window progresses through the steps below, tracked in `status.step.state`:

| Step           | Description                                                                             |
|----------------|-----------------------------------------------------------------------------------------|
| `Holding`      | Waiting for a slot within `maxConcurrentWorkerRestarts`. Nothing has been done yet.     |
| `ShuttingDown` | The backend node is shut down gracefully, while the budget blocks the Kubernetes drain. |
| `Releasing`    | The budget is relaxed. Kubernetes may now evict the pods and drain the worker.          |
| `AwaitingHost` | Waiting for the worker to return ready and uncordoned.                                  |
| `Restarting`   | The backend node is restarted and awaited until it is `online`.                         |
| `Cleanup`      | What the window put in place is removed, so the worker is left as it was found.         |

A window still at `Holding` holds no slot: it is queued behind the same gate as every other.

## Monitoring a Maintenance Window

```bash title="Listing the maintenance windows"
kubectl get storagenodeops -n simplyblock \
    -o jsonpath='{range .items[?(@.spec.action=="HostMaintenance")]}{.metadata.name}{"\t"}{.spec.nodeRef}{"\t"}{.status.phase}{"\t"}{.status.step.state}{"\n"}{end}'
```

```bash title="Streaming live changes"
kubectl get storagenodeops -n simplyblock -w
```

The operation reaches the phase `Succeeded` once the node is back online and the cluster has finished rebalancing,
and `Failed` with a reason in `status.message` if it could not get there.

## Configuring Concurrent Worker Restarts

To control the number of workers that can be simultaneously drained, the property `spec.maxConcurrentWorkerRestarts` on the
`StorageCluster` resource can be configured.

```yaml title="Example: allow one worker in the drain window at a time"
spec:
  maxConcurrentWorkerRestarts: 1
```

A value of `1` is the safest default. The safe-maximum of this value depends on the selected erasure coding scheme and
replication factor. It reflects the maximum number of toleratable simultaneous node outages without connection loss and
traffic interruption.

## Pinned Volume Migration During Node Removal

By default, a PVC annotated with `simplyblock.io/selected-storage-node` blocks node drain. When draining a node (via a
`StorageNodeOps` with `action: Remove`), the operator will not migrate a pinned volume and will instead emit a
`PinnedVolumeBlocking` event until the annotation is removed.

**User-directed placement** specifies exactly which node the volume should migrate _to_ during drain
by setting the annotation value to the target storage node UUID. The operator then migrates the volume to that
specific node instead of blocking.

### Specifying a Migration Target

Set the annotation value to the target `StorageNode` UUID before triggering drain:

```bash title="Pin a PVC to a specific target node for migration"
kubectl annotate pvc <pvc-name> -n <namespace> \
  simplyblock.io/selected-storage-node=<target-storage-node-uuid> --overwrite
```

Find the available storage node UUIDs with:

```bash title="List storage node UUIDs"
kubectl get storagenodeset simplyblock-node -n simplyblock \
  -o jsonpath='{.status.nodes[*].uuid}' | tr ' ' '\n'
```

Once annotated, trigger the drain as usual:

```bash title="Remove the node"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageNodeOps
metadata:
  name: drain-worker-1
  namespace: simplyblock
spec:
  nodeRef: simplyblock-node-mejue8
  action: Remove
EOF
```

The operator will migrate the volume to the specified target instead of blocking.

### Annotation Rules

| Annotation value                                                  | Drain behavior                                              |
|-------------------------------------------------------------------|-------------------------------------------------------------|
| A valid storage node UUID (different from the node being drained) | Volume is migrated to that node, drain proceeds             |
| Empty string                                                      | Drain is blocked, a `PinnedVolumeBlocking` event is emitted |
| A non-UUID value                                                  | Drain is blocked, a `PinnedVolumeBlocking` event is emitted |
| The UUID of the node being drained                                | Drain is blocked, a `PinnedVolumeBlocking` event is emitted |

A `PinnedVolumeBlocking` event names the affected PVC and states exactly what to fix:

```bash title="Check for pinned volume blocking events"
kubectl get events -n simplyblock --field-selector reason=PinnedVolumeBlocking
```
