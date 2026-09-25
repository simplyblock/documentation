---
title: "Migrating a Storage Node"
description: "Relocate a simplyblock storage node onto a different Kubernetes worker with a Migrate operation, keeping its backend identity, devices, and logical volumes."
weight: 10230
---

The `Migrate` action of a `StorageNodeOps` resource moves a storage node onto a different Kubernetes worker without
taking it out of the cluster. The node keeps its backend UUID, its devices, and its logical volume assignments, and no
volume is moved between nodes, so no `PersistentVolumeOps` is created. What changes is the host the node runs on.

This is the operation for replacing the hardware under a node, or for vacating a worker that has to be
decommissioned. It is not the operation for moving individual volumes, which is
[Volume Migration](../volumes/volume-migration.md), and not the operation for taking a node out of the cluster, which is
[Removing a Storage Node](removing-a-storage-node.md).

!!! warning
    A storage node must never be removed and re-added to move it to another host. Removing a node without draining it
    first makes the logical volumes it owns inaccessible. A migration keeps the node's identity, which is precisely
    what preserves those volumes.

`spec.workerNode` of a `StorageNode` cannot be edited directly either. A validating webhook rejects any change made by
a user, and only the operator re-points the field, as the final step of this operation.

## Prerequisites

The target worker has to be part of the Kubernetes cluster before the migration starts. The operator labels it into
the storage plane and waits for its storage-node pod, but the machine itself has to exist and be usable.

- **Ready:** The target is a Kubernetes node and is `Ready`. A target that is missing or not ready fails the operation
  immediately.
- **Different:** The target is not the worker the storage node currently runs on. A migration whose node already runs
  on the target succeeds at once, without doing anything.
- **Devices:** The target has the devices the node expects, either because they carry the same PCIe addresses as on
  the source host, or because the additional addresses are declared in `spec.migrate.newSsdPcie`.

## Requesting a Migration

```yaml title="Example of a node migration (migrate-node.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageNodeOps
metadata:
  name: migrate-worker-1
  namespace: simplyblock
spec:
  nodeRef: simplyblock-cluster-worker-1-0
  action: Migrate
  migrate:
    targetWorkerNode: worker-5.example.com
    newSsdPcie:
      - "0000:61:00.0"
```

```bash title="Migrating a storage node to a different worker"
kubectl apply -f migrate-node.yaml
```

| Field                           | Type     | Description                                                                                        |
|---------------------------------|----------|----------------------------------------------------------------------------------------------------|
| `spec.migrate.targetWorkerNode` | string   | The Kubernetes worker to relocate the node onto. Required, and immutable.                          |
| `spec.migrate.newSsdPcie`       | []string | Additional NVMe PCIe addresses to bind on the target host. Merged into the node's PCIe allow list. |
| `spec.reattachVolume`           | bool     | Reattaches the node's volumes as part of the restart onto the target.                              |
| `spec.force`                    | bool     | Forces the restart onto the target. Defaults to `true` for a migration.                            |

A migration restart is forced unless `spec.force` is explicitly `false`, because the control plane rejects a non-forced
restart of a node that is still `online`.

## Steps

| Step           | Deadline   | Description                                                                                                      |
|----------------|------------|------------------------------------------------------------------------------------------------------------------|
| `Preparing`    | 15 minutes | The node's configuration is cloned onto the target, the target is labeled, and its storage-node pod is awaited.  |
| `Relocating`   | 15 minutes | A restart is issued with the target host as the node's address. The step holds until the node leaves `online`.   |
| `AwaitingNode` | 45 minutes | The node is awaited until it reports `online` again, now running on the target worker.                           |
| `Promoting`    | 30 minutes | The node is promoted, which starts a cluster rebalance, and the Kubernetes topology is re-pointed to the target. |

### Preparing

The per-node configuration of the source worker is copied to the target first, so that the storage-node pod boots
there with the same effective settings. Any address in `spec.migrate.newSsdPcie` is merged into the PCIe allow list of
that configuration. The target is then labeled into the storage plane, which makes the DaemonSet schedule a
storage-node pod onto it.

The step does not advance until that pod is Ready **and** its DNS name is published in the endpoints of the
storage-node service. Both conditions matter, because the control plane addresses the node by that name in the next
step. A restart issued too early fails to resolve it, and the control plane then resets the node to offline. A
migration that sits in `Preparing` is therefore usually waiting for the target's pod.

### Relocating and AwaitingNode

The restart is issued against the control plane with the target host's storage-node API as the node address, which is
the same primitive that brings a node back after a worker reboot. `Relocating` completes when the node has left
`online`, which confirms that the restart began, and `AwaitingNode` waits for it to come back `online`.

### Promoting

The promotion is the step with no way back. It activates the devices on the target host, fails and migrates those of
the source host, starts a rebalance, and re-homes the logical volumes. It is only issued once the node reports
`online`. The Kubernetes topology is then brought in line:

- `StorageNode.spec.workerNode` is re-pointed at the target, and the addresses of `spec.migrate.newSsdPcie` are merged
  into `spec.config.pcieAllowList`, so they survive a later rebuild of the node.
- The target worker keeps its storage-plane labels.
- The storage-plane labels are removed from the source worker, unless another storage node still runs there, which is
  the case on a worker that hosts more than one NUMA socket.

The operation succeeds once the topology has been re-pointed. The rebalance the promotion started continues afterward
and is tracked in `StorageCluster.status.rebalancing`.

## Aborting a Migration

A migration can be aborted only in `Preparing`, where nothing but a label on the target has changed. From `Relocating`
onward, the node is mid-restart with the operation as the only thing watching it back, so an abort is not honored and
the webhook refuses deleting the operation until it is terminal.

## Tracking a Migration

```bash title="Watching a migration"
kubectl get storagenodeops migrate-worker-1 -n simplyblock -o wide -w
```

```bash title="Confirming the node runs on the target worker"
kubectl get storagenode simplyblock-cluster-worker-1-0 -n simplyblock \
    -o jsonpath='{.spec.workerNode}{" "}{.status.status}{"\n"}'
```

The progress is reported through the common operation events, `OperationStarted`, `OperationSucceeded`, and
`OperationFailed`, which are mirrored onto the `StorageNode`.
