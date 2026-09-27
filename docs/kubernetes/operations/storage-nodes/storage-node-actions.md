---
title: "Storage Node Actions"
description: "Request an operation against a single simplyblock storage node with a StorageNodeOps resource, track it through its steps, and restart a single device."
weight: 10210
---

An operation against one storage node is requested by creating a `StorageNodeOps` resource. It names the target
`StorageNode`, carries the action to perform, and is driven to completion by the Simplyblock Operator, which records
the progress in its status. The resource behaves like a Kubernetes `Job`: it runs once and is then terminal.

This page describes what every node operation shares: how the target node is found, how a request is made, how the
operations of one node exclude each other, and how one is tracked, aborted, and cleaned up. What each action does is
described on its own page. The pattern common to all Ops kinds is described in
[Operations](../index.md#the-operation-pattern).

## Finding the Target Node

`spec.nodeRef` names a `StorageNode` resource in the same namespace, not a Kubernetes worker. A worker with more than
one NUMA socket, or with more than one node per socket, carries one `StorageNode` per slot, so the name is read from
the cluster.

```bash title="Listing the storage nodes with their workers"
kubectl get storagenodes -n simplyblock -o wide
```

```plain title="Example output of the storage node listing"
NAME                             CLUSTER               WORKER                 SOCKET   SLOT   PHASE    STEP   STATUS   HEALTH   UUID                                   FD       AGE
simplyblock-cluster-worker-1-0   simplyblock-cluster   worker-1.example.com   0        0      Online          online   true     82198a36-fcbb-43e3-949c-0260bf40f0ac   rack-a   43h
simplyblock-cluster-worker-2-0   simplyblock-cluster   worker-2.example.com   0        0      Online          online   true     707dd443-5d0e-470f-bdde-92f1238c4b01   rack-b   43h
simplyblock-cluster-worker-3-0   simplyblock-cluster   worker-3.example.com   0        0      Online          online   true     114899a6-d708-499e-8051-bc9ca9713cf8   rack-c   43h
```

The `SOCKET` and `SLOT` columns tell the nodes of one worker apart. `STATUS` is the backend status of the node, and
`UUID` is the ID the control plane knows it by.

## Requesting an Action

```yaml title="Example of a node operation (restart-node.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageNodeOps
metadata:
  name: restart-worker-1
  namespace: simplyblock
spec:
  nodeRef: simplyblock-cluster-worker-1-0
  action: Restart
```

```bash title="Requesting the operation"
kubectl apply -f restart-node.yaml
```

| Action            | Effect                                                           | Completes when                      | Page                                                            |
|-------------------|------------------------------------------------------------------|-------------------------------------|-----------------------------------------------------------------|
| `Shutdown`        | Stops the storage node.                                          | The node is `offline`.              | [Shutting Down a Storage Node](shutting-down-a-storage-node.md) |
| `Restart`         | Stops and starts the storage node.                               | The node is `online`.               | [Restarting a Storage Node](restarting-a-storage-node.md)       |
| `Suspend`         | Keeps the node running but stops new volumes being placed on it. | The node is `suspended`.            | [Suspending a Storage Node](suspending-a-storage-node.md)       |
| `Resume`          | Returns a suspended node to normal service.                      | The node is `online`.               | [Resuming a Storage Node](resuming-a-storage-node.md)           |
| `Remove`          | Drains the volumes off the node and removes it.                  | The node is removed.                | [Removing a Storage Node](removing-a-storage-node.md)           |
| `Migrate`         | Moves the node onto a different Kubernetes worker.               | The node is promoted on the target. | [Migrating a Storage Node](migrating-a-storage-node.md)         |
| `HostMaintenance` | Takes the node down for a worker drain and brings it back.       | The node is `online` again.         | [Coordinated Worker Node Drain](node-drain-coordination.md)     |

`spec.nodeRef` and `spec.action` are required and immutable. A repeat of the same operation requires a new resource.

### Optional Fields

| Field                            | Type     | Applies to                              | Description                                                                                                    |
|----------------------------------|----------|-----------------------------------------|----------------------------------------------------------------------------------------------------------------|
| `force`                          | bool     | `Restart`, `Migrate`, `HostMaintenance` | Sends the restart with the force flag of the control plane. `Migrate` defaults it to `true`.                   |
| `reattachVolume`                 | bool     | `Restart`, `Migrate`, `HostMaintenance` | Reattaches the node's volumes as part of the restart.                                                          |
| `migrate.targetWorkerNode`       | string   | `Migrate`                               | The Kubernetes worker to relocate the node onto. Required for `Migrate`, and immutable.                        |
| `migrate.newSsdPcie`             | []string | `Migrate`                               | Additional NVMe PCIe addresses to bind on the target worker.                                                   |
| `remove.systemVolumeFilterRegex` | string   | `Remove`                                | Matches the names of system volumes, which are deleted instead of migrated. Defaults to `^sb-fio-baseline-.*`. |
| `abort`                          | bool     | All actions                             | Asks the running operation to stop at its current step.                                                        |

Every field is ignored by the actions it does not apply to. Where `force` and `reattachVolume` are left out, the
control plane applies its own defaults.

```yaml title="Example of a forced restart that reattaches the volumes"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageNodeOps
metadata:
  name: restart-worker-1-forced
  namespace: simplyblock
spec:
  nodeRef: simplyblock-cluster-worker-1-0
  action: Restart
  force: true
  reattachVolume: true
```

## Execution and Mutual Exclusion

Only one operation may act on a `StorageNode` at a time. The running operation is named in
`StorageNode.status.activeOpsRef`, and a second operation for the same node waits in the `Pending` phase, with an
`OperationQueued` event, until the lock is free. It is not rejected, so several operations can be created up front and
are then served in turn.

A node operation also runs inside its cluster. Every action except `Remove` holds, with a `ClusterNotReady` event,
while the cluster is not `active` or is rebalancing, and it resumes once the cluster has settled. `Remove` is exempt,
since removing a node is sometimes what makes an unready cluster ready again.

Once it holds the lock, the operation walks the steps of its action. Every call to the control plane is skipped when
the node is already where the call would put it, which makes a resumed operation safe after a restart of the operator.

| Action                                     | Steps                                                                                |
|--------------------------------------------|--------------------------------------------------------------------------------------|
| `Shutdown`, `Restart`, `Suspend`, `Resume` | `Requesting` → `Awaiting`                                                            |
| `Remove`                                   | `Validating` → `Suspending` → `MigratingVolumes` → `Verifying` → `Removing`          |
| `Migrate`                                  | `Preparing` → `Relocating` → `AwaitingNode` → `Promoting`                            |
| `HostMaintenance`                          | `Holding` → `ShuttingDown` → `Releasing` → `AwaitingHost` → `Restarting` → `Cleanup` |

Every step has a deadline, and an operation whose step outlives it fails with `StepDeadlineExceeded`. For the four
single-call actions, `Requesting` has two minutes and `Awaiting` 30 minutes. The deadlines of the multi-step actions
are listed on their pages.

| Phase       | Description                                                          |
|-------------|----------------------------------------------------------------------|
| `Pending`   | The operation is waiting for the node's operation lock.              |
| `Running`   | The operation holds the lock and walks its steps.                    |
| `Succeeded` | The node reached the expected state.                                 |
| `Failed`    | The operation could not complete. `status.message` holds the reason. |
| `Aborted`   | The operation was stopped through `spec.abort`.                      |

## Tracking an Operation

```bash title="Watching the operation status"
kubectl get storagenodeops restart-worker-1 -n simplyblock -o wide -w
```

```plain title="Example output of the operation listing"
NAME               NODE                             ACTION    PHASE     STEP       MESSAGE                                 AGE
restart-worker-1   simplyblock-cluster-worker-1-0   Restart   Running   Awaiting   waiting on Awaiting                     12s
```

```bash title="Reading the full operation status"
kubectl get storagenodeops restart-worker-1 -n simplyblock \
    -o jsonpath='{.status}' | jq .
```

Every event the operator emits on a `StorageNodeOps` is mirrored onto the `StorageNode` it targets, so the history of
a node is readable from the node itself.

```bash title="Reading the event history of a storage node"
kubectl describe storagenode simplyblock-cluster-worker-1-0 -n simplyblock
```

## Aborting an Operation

An abort is honored only in a step that can be stopped cleanly.

| Action                                     | Abortable steps                                                                   |
|--------------------------------------------|-----------------------------------------------------------------------------------|
| `Shutdown`, `Restart`, `Suspend`, `Resume` | `Requesting`                                                                      |
| `Remove`                                   | `Validating`, `Suspending`, `MigratingVolumes`, `Verifying`. The node is resumed. |
| `Migrate`                                  | `Preparing`                                                                       |
| `HostMaintenance`                          | `Holding`                                                                         |

```bash title="Aborting a node operation"
kubectl patch storagenodeops restart-worker-1 -n simplyblock \
    --type=merge -p '{"spec": {"abort": true}}'
```

In any other step, the operation carries on, and `status.message` states that the abort arrived too late. A running
operation cannot be deleted while it is in `Awaiting`, `Removing`, `Relocating`, `AwaitingNode`, `Promoting`,
`ShuttingDown`, `Releasing`, `AwaitingHost`, `Restarting`, or `Cleanup`, since the node is part-way through a change
that only the operation drives to an end.

## Events

In addition to the common operation events, a node operation emits the following reasons. The events of a removal and a
maintenance window are described on their pages.

| Reason              | Meaning                                                                       |
|---------------------|-------------------------------------------------------------------------------|
| `ClusterNotReady`   | The cluster is not `active` or is rebalancing, and the operation holds.       |
| `DrainBlocked`      | A removal is blocked by a pinned or an unmanaged volume.                      |
| `NoMigrationTarget` | A removal has no online peer to move the volumes to.                          |
| `MigrationRetried`  | A volume migration of a removal failed and is retried against another peer.   |
| `DrainCompleted`    | Every volume of a removal has been migrated off the node.                     |
| `NodeResumeFailed`  | A failed or aborted removal could not resume the node, which stays suspended. |
| `MaintenanceQueued` | A maintenance window waits for a slot, because other workers are in one.      |

## Cleaning Up

A terminal `StorageNodeOps` is kept. The operator does not delete it, which leaves the outcome of past operations
readable, and it is removed by hand once it is no longer of interest.

```bash title="Deleting a completed operation"
kubectl delete storagenodeops restart-worker-1 -n simplyblock
```

```bash title="Deleting every succeeded operation of a namespace"
kubectl get storagenodeops -n simplyblock \
    -o jsonpath='{range .items[?(@.status.phase=="Succeeded")]}{.metadata.name}{"\n"}{end}' \
    | xargs -r kubectl delete storagenodeops -n simplyblock
```

## Restarting a Storage Device

A single device of a storage node is restarted with a `StorageDeviceOps` resource, which recycles that one device
instead of the whole node. The other devices of the node keep serving throughout. `Restart` is the only action of the
kind.

The target is a `StorageDevice`, the read-only mirror of one device that the operator keeps per device and names
`<storage-node>-<first 8 characters of the device ID>`.

```bash title="Listing the devices of a storage node"
kubectl get storagedevices -n simplyblock \
    -l storage.simplyblock.io/node=simplyblock-cluster-worker-1-0 -o wide
```

```yaml title="Example of a device restart"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageDeviceOps
metadata:
  name: restart-device-5e0000a1
  namespace: simplyblock
spec:
  deviceRef: simplyblock-cluster-worker-1-0-5e0000a1
  action: Restart
```

The operation runs the steps `Requesting` and `Awaiting`, and it succeeds once the device reports `online` again. The
device status seen when the operation started is recorded in `status.deviceStatusBefore`. Only one operation acts on a
device at a time, tracked in `StorageDevice.status.activeOpsRef`. An abort is honored only in `Requesting`, before the
restart has been sent.
