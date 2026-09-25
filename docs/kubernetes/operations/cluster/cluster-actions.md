---
title: "Storage Cluster Actions"
description: "Request cluster-wide lifecycle operations on a simplyblock storage cluster with a StorageClusterOps resource, and track them through their steps."
weight: 10110
---

Cluster-wide lifecycle operations are requested declaratively on Kubernetes. A `StorageClusterOps` resource names a
`StorageCluster`, carries one action, and is driven to completion by the Simplyblock Operator, which calls the control
plane, waits until the cluster reaches the expected state, and records the progress in the status of the operation.
The CLI is not involved.

This page describes what every cluster operation shares. What each action does is described on its own page, listed
in the table below. The pattern common to all Ops kinds is described in
[Operations](../index.md#the-operation-pattern).

## Requesting an Action

```yaml title="Example of a cluster operation (shutdown-cluster.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageClusterOps
metadata:
  name: shutdown-simplyblock-cluster
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  action: Shutdown
```

```bash title="Requesting the operation"
kubectl apply -f shutdown-cluster.yaml
```

The operation lives in the namespace of its cluster. `spec.clusterRef` and `spec.action` are required and immutable.

| Action           | Effect                                                                      | Completes when                     | Page                                                                   |
|------------------|-----------------------------------------------------------------------------|------------------------------------|------------------------------------------------------------------------|
| `Activate`       | Activates a cluster whose nodes have joined but which is not yet live.      | The cluster is `active`.           | [Activating a Storage Cluster](activating-a-cluster.md)                |
| `Expand`         | Finalizes an expansion of nodes that were added without the expansion flag. | The cluster is `active`.           | [Expanding a Storage Cluster](../scaling/expanding-storage-cluster.md) |
| `Shutdown`       | Shuts the whole cluster down.                                               | The cluster is no longer `active`. | [Shutting Down a Storage Cluster](shutting-down-a-cluster.md)          |
| `Start`          | Starts a previously shut down cluster.                                      | The cluster is `active`.           | [Starting a Storage Cluster](starting-a-cluster.md)                    |
| `Restart`        | Runs a shutdown followed by a start.                                        | The cluster is `active`.           | [Restarting a Storage Cluster](restarting-a-cluster.md)                |
| `RollingRestart` | Restarts every storage node of the cluster, one after another.              | Every node has been restarted.     | [Rolling Restart](rolling-restart.md)                                  |
| `CancelTask`     | Cancels one task of the control plane.                                      | The task is no longer running.     | [Canceling a Task](#canceling-a-task)                                  |

Any other value is rejected by the CRD schema.

### Parameters

| Field                                 | Type   | Applies to       | Description                                                                               |
|---------------------------------------|--------|------------------|-------------------------------------------------------------------------------------------|
| `spec.rollingRestart.refreshSNodeAPI` | bool   | `RollingRestart` | Replaces the storage-node pod of every node between its shutdown and its restart.         |
| `spec.cancelTask.taskID`              | string | `CancelTask`     | The control-plane ID of the task to cancel, from `StorageCluster.status.tasks`. Required. |
| `spec.abort`                          | bool   | All actions      | Asks the running operation to stop at its current step.                                   |

A parameter block is ignored by every action it does not belong to.

## How an Action Is Executed

Only one operation acts on a cluster at a time. The running operation is named in `StorageCluster.status.activeOpsRef`,
and a second operation for the same cluster waits in the `Pending` phase with an `OperationQueued` event until the lock
is free.

Once it holds the lock, the operation walks the steps of its action. Every call to the control plane is skipped when the
cluster is already in the state the call would produce, for example, a `Start` of a cluster that is already `active`.
This makes an operation safe to resume after a restart of the operator, and it makes a request against a cluster that
is already in the target state succeed at once.

| Action                                                  | Steps                                                                                                                 |
|---------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| `Activate`, `Expand`, `Shutdown`, `Start`, `CancelTask` | `Requesting` → `Awaiting`                                                                                             |
| `Restart`                                               | `ShuttingDown` → `Starting`                                                                                           |
| `RollingRestart`                                        | Per node: `CheckingPeers` → `ShuttingDownNode` → [`RefreshingPod` → `AwaitingPod`] → `RestartingNode` → `Rebalancing` |

A request that the control plane refuses with a transient error is retried, and the reason is written to
`status.message`. The operation fails when a step outlives its deadline.

| Step                           | Deadline   |
|--------------------------------|------------|
| `Requesting`                   | 2 minutes  |
| `Awaiting`                     | 30 minutes |
| `ShuttingDown`, `Starting`     | 30 minutes |
| `CheckingPeers`                | 2 hours    |
| `ShuttingDownNode`             | 30 minutes |
| `RefreshingPod`, `AwaitingPod` | 10 minutes |
| `RestartingNode`               | 45 minutes |
| `Rebalancing`                  | 4 hours    |

## Monitoring an Action

```bash title="Listing the cluster operations"
kubectl get storageclusterops -n simplyblock
```

```plain title="Example output of the operation listing"
NAME                           CLUSTER               ACTION     PHASE     STEP       AGE
shutdown-simplyblock-cluster   simplyblock-cluster   Shutdown   Running   Awaiting   12s
```

```bash title="Reading the full status of an operation"
kubectl get storageclusterops shutdown-simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status}' | jq .
```

The backend lifecycle status of the cluster is tracked on the `StorageCluster` itself, separately from the operation.

```bash title="Reading the phase and the backend status of the cluster"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status.phase}{" "}{.status.status}{" rebalancing="}{.status.rebalancing}{"\n"}'
```

## Aborting an Action

An abort is honored where no request is outstanding: in the `Requesting` step of the single-call actions, and in the
`CheckingPeers` and `Rebalancing` steps of a rolling restart. Anywhere else, the cluster or one of its nodes is already
part-way through what was asked for, so the operation carries on, and `status.message` says that the abort arrived too
late.

```bash title="Aborting a cluster operation"
kubectl patch storageclusterops shutdown-simplyblock-cluster -n simplyblock \
    --type=merge -p '{"spec": {"abort": true}}'
```

A running operation cannot be deleted while it is in `Awaiting`, `ShuttingDown`, `Starting`, `ShuttingDownNode`,
`RefreshingPod`, `AwaitingPod`, or `RestartingNode`. The webhook refuses the deletion, and the record can be deleted
once the operation is terminal.

## Canceling a Task

The control plane runs long-running work, such as data migrations and node restarts, as tasks. The running and pending
tasks of a cluster are listed in `StorageCluster.status.tasks`, at most 20 of them, each with its `id`, `type`,
`status`, and `retry` count.

```bash title="Listing the tasks of a cluster"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{range .status.tasks[*]}{.id}{"\t"}{.type}{"\t"}{.status}{"\n"}{end}'
```

A task is canceled by its ID.

```yaml title="Example of canceling a task"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageClusterOps
metadata:
  name: cancel-migration-task
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  action: CancelTask
  cancelTask:
    taskID: 1b1f1c9e-3a7d-4d0f-9d3c-6f3f8a2e41b7
```

The operation succeeds once the task is no longer running or pending, and a `TaskCanceled` event is emitted. A task
that is already gone when the operation runs counts as success as well.

## Events

In addition to the common operation events, a cluster operation emits the following reasons.

| Reason                  | Meaning                                                                                   |
|-------------------------|-------------------------------------------------------------------------------------------|
| `FailureDomainNotReady` | An activation waits because the failure domains do not hold an equal number of hosts yet. |
| `StripeNodesNotReady`   | An activation waits because the cluster has fewer storage nodes than its stripe needs.    |
| `PeerNodeNotOnline`     | A rolling restart holds, because a peer node is not online.                               |
| `NodeRestarted`         | A rolling restart advanced to the next node.                                              |
| `TaskCanceled`          | The task named by a `CancelTask` operation is no longer running.                          |

## Cleaning Up

A terminal operation is kept as the audit record of what was done. The operator does not delete it, and it is removed
by hand once it is no longer of interest.

```bash title="Deleting a completed cluster operation"
kubectl delete storageclusterops shutdown-simplyblock-cluster -n simplyblock
```
