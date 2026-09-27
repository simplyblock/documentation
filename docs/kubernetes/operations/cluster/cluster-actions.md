---
title: "Storage Cluster Actions"
description: "Trigger cluster-wide lifecycle operations on a simplyblock storage cluster with a StorageClusterOps resource and track their outcome."
weight: 10110
---

Cluster-wide lifecycle operations are requested declaratively on Kubernetes. Creating a `StorageClusterOps` resource
makes the Simplyblock Operator call the corresponding backend API, drive the operation to completion, and record the
outcome on the operation itself. The CLI is not involved.

A `StorageClusterOps` is analogous to a Kubernetes `Job`: it runs to a terminal phase and stays afterward as the
audit record of what was done, to which cluster, with which parameters, and how it ended.

This page describes the mechanism that every action shares: how one is requested, executed, re-run, aborted, and
monitored.

## Requesting an Action

An action is requested by creating the resource. The example below shuts the cluster down.

```bash title="Requesting a cluster action"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageClusterOps
metadata:
  name: shutdown-cluster
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  action: Shutdown
EOF
```

| Action           | Effect                                                                 | Expected cluster status | Page                                                                   |
|------------------|------------------------------------------------------------------------|-------------------------|------------------------------------------------------------------------|
| `Activate`       | Activates a cluster whose nodes have joined but which is not yet live. | `active`                | [Activating a Storage Cluster](activating-a-cluster.md)                |
| `Shutdown`       | Shuts the whole cluster down.                                          | `suspended`             | [Shutting Down a Storage Cluster](shutting-down-a-cluster.md)          |
| `Start`          | Starts a previously shut down cluster.                                 | `active`                | [Starting a Storage Cluster](starting-a-cluster.md)                    |
| `Restart`        | Runs a shutdown followed by a start.                                   | `active`                | [Restarting a Storage Cluster](restarting-a-cluster.md)                |
| `RollingRestart` | Restarts every storage node of the cluster, one after another.         | `active`                | [Rolling Restart](rolling-restart.md)                                  |
| `Expand`         | Finalizes a cluster expansion after new storage nodes came online.     | `active`                | [Expanding a Storage Cluster](../scaling/expanding-storage-cluster.md) |
| `CancelTask`     | Cancels one running backend task of the cluster.                       | unchanged               | [Canceling a Task](#canceling-a-task)                                  |

Any other value is rejected by the CRD schema. `spec.clusterRef` and `spec.action` are immutable: a repeat of the
same operation is a new resource.

## One Operation at a Time

Only one operation acts on a cluster at a time. A second is admitted rather than rejected, and waits until the
first has reached a terminal phase. The operation currently allowed to act is named on the cluster:

```bash title="Reading which operation holds the cluster"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status.activeOpsRef}{"\n"}'
```

The field is empty when no operation is running.

## How an Action Is Executed

Every action is a declared state machine, and the step it has reached is persisted in `status.step.state`. Which
steps belong to which action is the action's own, and the pages linked above describe them.

| Action                                                  | Steps                                                                                                |
|---------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| `Activate`, `Expand`, `Shutdown`, `Start`, `CancelTask` | `Requesting`, `Awaiting`                                                                             |
| `Restart`                                               | `ShuttingDown`, `Starting`                                                                           |
| `RollingRestart`                                        | `CheckingPeers`, `ShuttingDownNode`, `RefreshingPod`, `AwaitingPod`, `RestartingNode`, `Rebalancing` |

The persisted step is also what makes the operation safe to resume. Every step's completion condition is a
predicate over current state rather than an observation of a transition, and every call is skipped when its target
is already at or past what the call would produce, so a requeue or an operator restart never repeats a side effect.

`status.step.deadline` is when the current step expires, where it has one. A step whose deadline passed while the
operator was down is restored as already expired, which is what makes a stalled operation detectable.

## Phases

| Phase       | Meaning                                                                     |
|-------------|-----------------------------------------------------------------------------|
| `Pending`   | Admitted, not yet started. A second operation on a busy cluster waits here. |
| `Running`   | In progress. `status.step.state` says where.                                |
| `Succeeded` | Finished, terminal.                                                         |
| `Failed`    | Something went wrong, terminal. `status.message` says what.                 |
| `Aborted`   | Canceled deliberately, terminal, and distinct from `Failed`.                |

A failed operation is not retried automatically.

## Re-Running an Action

Re-running is creating a second resource. The first stays as the record of the earlier run, so the history of what
was done to a cluster is a series of objects rather than a field that was overwritten.

```bash title="Re-running an action"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageClusterOps
metadata:
  name: restart-cluster-2
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  action: Restart
EOF
```

## Aborting an Action

`spec.abort` asks a running operation to stop at its next step and unwind. Whether an abort is expressible from the
current step is declared by the action's own state machine: one arriving later is reported as an illegal transition
while the operation runs on, rather than leaving the work half done.

```bash title="Aborting a running operation"
kubectl patch storageclusterops restart-cluster -n simplyblock \
    --type=merge -p '{"spec": {"abort": true}}'
```

An operation that unwound reaches the phase `Aborted`, which is terminal and deliberately distinct from `Failed`:
a canceled operation did not go wrong.

## Canceling a Task

`CancelTask` cancels one running backend task, named by its identifier. The running tasks of a cluster are reported
in `status.tasks`.

```bash title="Reading the running tasks of a cluster"
kubectl get storagecluster simplyblock-cluster -n simplyblock -o jsonpath='{.status.tasks}'
```

```bash title="Canceling a task"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageClusterOps
metadata:
  name: cancel-migration
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  action: CancelTask
  cancelTask:
    taskID: 4f2c8a11-6b3d-4e19-9a55-0c7e1d8f2b34
EOF
```

## Monitoring an Action

```bash title="Listing the operations of a cluster"
kubectl get storageclusterops -n simplyblock
```

```bash title="Following a running operation"
kubectl get storageclusterops restart-cluster -n simplyblock \
    -o jsonpath='{.status.phase}{"\t"}{.status.step.state}{"\t"}{.status.message}{"\n"}' -w
```

`status.startedAt` and `status.completedAt` bracket the run.

The backend lifecycle status of the cluster is tracked separately from any operation.

```bash title="Reading the backend cluster status"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status.status}{"\n"}'
```

```bash title="Streaming live cluster status changes"
kubectl get storagecluster simplyblock-cluster -n simplyblock -w
```
