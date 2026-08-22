---
title: "Migrating a Storage Node"
description: "Relocate a simplyblock storage node onto a different Kubernetes worker with the migrate action, keeping its backend identity, devices, and logical volumes."
weight: 10730
---

The `migrate` action of a `StorageNodeOps` resource moves a storage node onto a different Kubernetes worker without
taking it out of the cluster. The node keeps its backend UUID, its devices, and its logical volume assignments, and no
volume is moved between nodes. What changes is the host the node runs on.

This is the operation for replacing the hardware under a node, or for vacating a worker that has to be
decommissioned. It is not the operation for moving individual volumes, which is
[Volume Migration](volume-migration.md), and not the operation for taking a node out of the cluster, which is
[Removing a Storage Node](removing-a-storage-node.md).

!!! important
    A storage node must never be removed and re-added to move it to another host. Removing a node without draining it
    first makes the logical volumes it owns inaccessible. A migration keeps the node's identity, which is precisely
    what preserves those volumes.

`spec.workerNode` on a `StorageNode` cannot be edited directly either. A validating webhook rejects any change made by
a user, and only the operator re-points the field, as the final step of this operation.

## Prerequisites

The target worker has to be part of the storage plane before the migration starts. The operator labels it and waits
for its storage-node pod, but the node itself has to exist and be usable.

- The target is a Kubernetes node in the cluster and is `Ready`. A target that is missing or not ready fails the
  operation immediately.
- The target is not the worker the storage node currently runs on.
- The target has the devices the node expects, either because they carry the same PCIe addresses as on the source
  host, or because the additional addresses are declared in `spec.newSsdPcie`.

## Requesting a Migration

```bash title="Migrating a storage node to a different worker"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeOps
metadata:
  name: migrate-worker-1
  namespace: simplyblock
spec:
  storageNodeRef: simplyblock-node-mejue8
  action: migrate
  targetWorkerNode: worker-5.example.com
EOF
```

| Field              | Type     | Description                                                                                             |
|--------------------|----------|---------------------------------------------------------------------------------------------------------|
| `targetWorkerNode` | string   | Kubernetes worker hostname to relocate the node onto. Required for `migrate`, and immutable.            |
| `newSsdPcie`       | []string | Additional NVMe PCIe addresses to bind on the target host. Merged into the target's node configuration. |
| `reattachVolume`   | bool     | Reattaches the node's volumes as part of the restart.                                                   |
| `force`            | bool     | Overrides the forced restart. A migration restart is forced unless this is set to `false`.              |

## Sub-Phases

A migration is a four-step state machine, tracked in `status.subPhase`.

| Sub-phase    | Description                                                                                                                                   |
|--------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| `Preparing`  | The source node's configuration is cloned onto the target, the target is labeled into the storage plane, and its storage-node pod is awaited. |
| `Migrating`  | A restart is issued against the target's storage-node API. The phase holds until the node is observed leaving `online`.                       |
| `Restarting` | The node is awaited until it reports `online` again, now running on the target worker.                                                        |
| `Promoting`  | The node is promoted, which starts a cluster rebalance, and the Kubernetes topology is re-pointed from the source worker to the target.       |

### Preparing

The per-node configuration of the source worker is copied to the target first, so that the storage-node pod boots
there with the same effective settings. Any address in `spec.newSsdPcie` is merged into the PCIe allow list of that
configuration. The target is then labeled into the storage plane, which is what makes the DaemonSet schedule a
storage-node pod onto it.

The phase does not advance until that pod is `Ready` **and** its per-pod DNS name is published in the storage-node API
endpoints. Both conditions matter, because the restart in the next phase addresses the node by that DNS name. A
restart issued too early fails to resolve it, and the control plane then resets the node to offline.

A migration that sits in `Preparing` is therefore usually waiting for the target's pod, and `status.message` names
what is missing.

### Migrating and Restarting

The restart is issued against the control plane with the target host's storage-node API as the node address, which is
the same primitive that brings a node back after a worker reboot. The restart is forced, unless `spec.force` is
explicitly `false`, and it carries `reattachVolume` when that field is set.

The operator polls quickly during this phase, because the window in which the node reports `in_restart` is short and
has to be observed to confirm that the restart actually began. Once the node has left `online`, the operation advances
to `Restarting` and waits there for it to come back `online`.

### Promoting

The relocated node is promoted, which starts a cluster rebalance in the background. The Kubernetes topology is then
brought in line with the new reality:

- `StorageNode.spec.workerNode` is re-pointed at the target, and the node's worker label is refreshed with it.
- The `StorageNodeSet` worker list drops the source worker and gains the target, and the per-node configuration entry
  moves with it.
- The stale status entry for the node on the source worker is pruned from the `StorageNodeSet`.
- The storage-plane labels are removed from the source worker, unless another storage node still runs there, which is
  the case on a worker that hosts more than one NUMA socket.

The operation succeeds once the topology has been re-pointed. The rebalance the promote started continues afterward
and is tracked in `StorageCluster.status.rebalancing`.

## Tracking a Migration

```bash title="Watching a migration"
kubectl get storagenodeops migrate-worker-1 -n simplyblock -w
```

```plain title="Example output of a running migration"
NAME               NODE                      ACTION    PHASE     SUBPHASE     MESSAGE                                              AGE
migrate-worker-1   simplyblock-node-mejue8   migrate   Running   Preparing    waiting for storage-node-api pod on worker-5         25s
```

```bash title="Confirming the node runs on the target worker"
kubectl get storagenode simplyblock-node-mejue8 -n simplyblock \
    -o jsonpath='{.spec.workerNode}{" "}{.status.status}{"\n"}'
```

## Events

| Reason                | Meaning                                                                    |
|-----------------------|----------------------------------------------------------------------------|
| `TargetWorkerLabeled` | The target worker was labeled into the storage plane.                      |
| `MigrateStarted`      | The restart against the target host was issued.                            |
| `MigratePromoted`     | The relocated node was promoted and a rebalance started.                   |
| `MigrateCompleted`    | The node is online on the target worker and the topology has been updated. |
| `OpsFailed`           | The migration failed. The message carries the reason.                      |

Each of these is emitted on the `StorageNodeOps` resource and mirrored onto the `StorageNode`.

```bash title="Streaming migration events"
kubectl get events -n simplyblock --watch \
    --field-selector reason=MigrateCompleted
```
