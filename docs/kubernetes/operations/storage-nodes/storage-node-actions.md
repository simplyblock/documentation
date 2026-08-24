---
title: "Storage Node Actions"
description: "Request an operation against a single simplyblock storage node with a StorageNodeOps resource, and track it through the phases of its status."
weight: 10210
---

An operation against one storage node is requested by creating a `StorageNodeOps` resource. It names the target
`StorageNode`, carries the action to perform, and is driven to completion by the Simplyblock Operator, which records
the outcome in `status`. The resource behaves like a Kubernetes `Job`: it runs once and is then terminal.

This page describes what every operation shares: how the target node is found, how a request is made, how the
operations of one node exclude each other, and how one is tracked and cleaned up. What each action does is described
on its own page.

## Finding the Target Node

The `spec.storageNodeRef` field names a `StorageNode` resource, not a Kubernetes worker. The name is generated when
the node is enrolled and does not encode the worker or the NUMA socket, so it has to be read from the cluster.

```bash title="Listing the storage nodes with their workers"
kubectl get storagenodes -n simplyblock
```

```plain title="Example output of the storage node listing"
NAME                      WORKER                          SOCKET   NODEIDX   UUID                                   STATUS   HEALTH   AGE
simplyblock-node-mejue8   vm04.simplyblock3.localdomain   0        0         82198a36-fcbb-43e3-949c-0260bf40f0ac   online   true     43h
simplyblock-node-o6x20i   vm03.simplyblock3.localdomain   0        0         707dd443-5d0e-470f-bdde-92f1238c4b01   online   true     43h
simplyblock-node-v92jx7   vm02.simplyblock3.localdomain   0        0         114899a6-d708-499e-8051-bc9ca9713cf8   online   true     43h
```

A worker with more than one NUMA socket, or with more than one node per socket, carries one `StorageNode` per
instance. The `SOCKET` and `NODEIDX` columns tell them apart.

## Requesting an Action

```bash title="Requesting an operation against a storage node"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeOps
metadata:
  name: restart-worker-1
  namespace: simplyblock
spec:
  storageNodeRef: simplyblock-node-mejue8
  action: restart
EOF
```

| Action     | Effect                                                           | Expected node status | Page                                                            |
|------------|------------------------------------------------------------------|----------------------|-----------------------------------------------------------------|
| `shutdown` | Stops the storage node.                                          | `offline`            | [Shutting Down a Storage Node](shutting-down-a-storage-node.md) |
| `restart`  | Stops and starts the storage node.                               | `online`             | [Restarting a Storage Node](restarting-a-storage-node.md)       |
| `suspend`  | Keeps the node running but stops new volumes being placed on it. | `suspended`          | [Suspending a Storage Node](suspending-a-storage-node.md)       |
| `resume`   | Returns a suspended node to normal service.                      | `online`             | [Resuming a Storage Node](resuming-a-storage-node.md)           |
| `migrate`  | Moves the node onto a different Kubernetes worker.               | `online`             | [Migrating a Storage Node](migrating-a-storage-node.md)         |
| `remove`   | Drains the volumes off the node and removes it.                  | removed              | [Removing a Storage Node](removing-a-storage-node.md)           |

`spec.storageNodeRef` and `spec.action` are immutable. A repeat of the same operation requires a new resource.

### Optional Fields

| Field            | Type | Applies to                                 | Description                                           |
|------------------|------|--------------------------------------------|-------------------------------------------------------|
| `force`          | bool | `shutdown`, `restart`, `suspend`, `resume` | Sends the request with the backend's force flag set.  |
| `reattachVolume` | bool | `restart`                                  | Reattaches the node's volumes as part of the restart. |

Both fields are ignored by the actions they do not apply to. A node removal always runs unforced, so `force` has no
effect on `action: remove`.

```yaml title="Example of a forced restart that reattaches the volumes"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeOps
metadata:
  name: restart-worker-1-forced
  namespace: simplyblock
spec:
  storageNodeRef: simplyblock-node-mejue8
  action: restart
  force: true
  reattachVolume: true
```

## Execution and Mutual Exclusion

Only one operation may run against a `StorageNode` at a time. The running operation is recorded in
`StorageNode.status.activeOpsRef`, and a second operation for the same node waits, rechecking every 15 seconds, until
the lock is free. It is not rejected, so several operations can be created up front and are then served in turn.

Once the lock is held, the phase moves to `Running` and the backend request is sent. The node is then polled every
five seconds until it reaches the status the action expects. A request that the backend rejects is retried every ten
seconds rather than failing the operation, so a transient backend error does not abandon the work.

| Phase       | Description                                                          |
|-------------|----------------------------------------------------------------------|
| `Pending`   | The operation is waiting for the node's operation lock.              |
| `Running`   | The request has been sent and the node is being polled.              |
| `Succeeded` | The node reached the expected status.                                |
| `Failed`    | The operation could not complete. `status.message` holds the reason. |

An operation whose target `StorageNode` does not exist fails immediately. `status.startedAt` and
`status.completedAt` bracket the run, and the lock is released in both terminal phases.

## Tracking an Operation

```bash title="Watching the operation status"
kubectl get storagenodeops restart-worker-1 -n simplyblock -w
```

```plain title="Example output of the operation listing"
NAME               NODE                      ACTION    PHASE       SUBPHASE   MESSAGE                                     AGE
restart-worker-1   simplyblock-node-mejue8   restart   Running                restart request sent, waiting for node      12s
```

```bash title="Reading the full operation status"
kubectl get storagenodeops restart-worker-1 -n simplyblock \
    -o jsonpath='{.status}' | jq .
```

Every event the operator emits on a `StorageNodeOps` is mirrored onto the `StorageNode` it targets, so the history of
a node is readable from the node itself.

```bash title="Reading the event history of a storage node"
kubectl describe storagenode simplyblock-node-mejue8 -n simplyblock
```

## Cleaning Up

A terminal `StorageNodeOps` is kept. The operator does not delete it, which leaves the outcome of past operations
readable, and it has to be removed by hand once it is no longer of interest.

```bash title="Deleting a completed operation"
kubectl delete storagenodeops restart-worker-1 -n simplyblock
```

```bash title="Deleting every completed operation of a namespace"
kubectl get storagenodeops -n simplyblock \
    -o jsonpath='{range .items[?(@.status.phase=="Succeeded")]}{.metadata.name}{"\n"}{end}' \
    | xargs -r kubectl delete storagenodeops -n simplyblock
```

## Events

| Reason      | Meaning                                               |
|-------------|-------------------------------------------------------|
| `OpsFailed` | The operation failed. The message carries the reason. |

The in-place actions emit no events of their own on success. Their progress is read from `status.phase` and
`status.message`. The events emitted during a migration or a removal are listed on their respective pages.
