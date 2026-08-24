---
title: "Storage Cluster Actions"
description: "Trigger cluster-wide lifecycle operations on a simplyblock storage cluster through the action field of the StorageCluster resource and track their outcome."
weight: 10110
---

Cluster-wide lifecycle operations are requested declaratively on Kubernetes. Setting `spec.action` on a
`StorageCluster` resource makes the Simplyblock Operator call the corresponding backend API, poll until the cluster
reaches the expected state, and record the outcome in `status.actionStatus`. The CLI is not involved.

Only one action can be requested at a time, since `spec.action` holds a single value.

## Requesting an Action

An action is requested by patching the field. The example below shuts the cluster down.

```bash title="Requesting a cluster action"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
    --type=merge -p '{"spec": {"action": "shutdown"}}'
```

| Action         | Effect                                                                 | Expected cluster status |
|----------------|------------------------------------------------------------------------|-------------------------|
| `activate`     | Activates a cluster whose nodes have joined but which is not yet live. | `active`                |
| `expand`       | Finalizes a cluster expansion after new storage nodes came online.     | `active`                |
| `shutdown`     | Shuts the whole cluster down.                                          | `suspended`             |
| `start`        | Starts a previously shut down cluster.                                 | `active`                |
| `restart`      | Runs a shutdown followed by a start.                                   | `active`                |
| `node-recycle` | Restarts every storage node of the cluster, one after another.         | `active`                |

Any other value is rejected by the CRD schema. The `node-recycle` action has its own page, see
[Rolling Restart](rolling-restart.md).

## How an Action Is Executed

Every action follows the same pattern. The operator records the action in `status.actionStatus` with the state
`running`, sends the backend request once, and then polls the cluster until the expected status is reached. The first
poll follows five seconds after the request, and further polls follow every ten seconds.

The `status.actionStatus.triggered` flag marks that the request has already been sent, so a requeue or an operator
restart never sends it twice. A failed request moves the state to `failed` and writes the reason into
`status.actionStatus.message`. A failed action is not retried automatically.

| Field                | Description                                                              |
|----------------------|--------------------------------------------------------------------------|
| `action`             | The action this status belongs to.                                       |
| `state`              | `running` while the action is in progress, then `success` or `failed`.   |
| `message`            | The result, the failure reason, or the current sub-phase of a `restart`. |
| `triggered`          | Whether the backend request has already been sent.                       |
| `observedGeneration` | The `metadata.generation` of the spec this action was started for.       |
| `updatedAt`          | The time of the last status transition.                                  |

## Re-Running and Clearing an Action

An action counts as complete when its state is `success` **and** its `observedGeneration` matches the current
`metadata.generation` of the resource. Patching `spec.action` with the value it already holds does not change the
generation, so nothing happens. Re-running the same action therefore takes two patches: the field is cleared first
and set again afterward.

```bash title="Re-running the same action"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
    --type=merge -p '{"spec": {"action": ""}}'
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
    --type=merge -p '{"spec": {"action": "restart"}}'
```

!!! important
    While `spec.action` holds a value, the reconciler serves the action instead of its periodic status sync. Once the
    action has succeeded, nothing further happens to the resource, and the remaining `status` fields are no longer
    refreshed from the backend. Clearing `spec.action` after a completed action returns the cluster to normal status
    reconciliation.

## Shutdown

A shutdown suspends the entire cluster. The operator calls the backend shutdown API and polls until the cluster
reports `suspended`.

```bash title="Shutting down the storage cluster"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
    --type=merge -p '{"spec": {"action": "shutdown"}}'
```

!!! warning
    A cluster shutdown takes every volume of the cluster offline. Workloads consuming those volumes lose their storage
    for the duration of the shutdown. To take a single storage node out of service instead, see
    [Storage Node Actions](../storage-nodes/storage-node-actions.md).

## Start

A start brings a suspended cluster back. The operator calls the backend start API and polls until the cluster reports
`active`. The rebalancing flag reported by the backend is recorded in `status.rebalancing` once the cluster is up.

```bash title="Starting a suspended storage cluster"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
    --type=merge -p '{"spec": {"action": "start"}}'
```

## Restart

A restart sequences a shutdown and a start. Both legs are driven by the same action, and the leg currently running is
held in `status.actionStatus.message` as either `shutdown` or `start`. The action succeeds once the cluster is `active`
again.

```bash title="Restarting the storage cluster"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
    --type=merge -p '{"spec": {"action": "restart"}}'
```

```bash title="Following the leg of a running restart"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status.actionStatus.message}{"\n"}'
```

## Activate

Activation is normally automatic. The operator activates a cluster on its own once every storage node declared in its
`StorageNodeSet` is online and healthy, and the number of those nodes is at least the sum of the data chunks, the
parity chunks, and one. See
[Create a Storage Cluster](../../installation/k8s-storage-plane.md#when-does-the-cluster-become-active).

The `activate` action exists for the case where that did not happen, for example, because nodes came online after the
automatic check had already passed.

```bash title="Activating a cluster manually"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
    --type=merge -p '{"spec": {"action": "activate"}}'
```

!!! warning
    A `StorageCluster` that is deleted while `spec.action` is `activate` has its finalizer removed without the backend
    cluster being deleted. The cluster is then left behind on the control plane and has to be removed there. Clear
    `spec.action` before deleting the resource.

## Expand

An expansion is finalized with the `expand` action, after the new storage nodes have been added and are online. The
operator calls the backend expand API and polls until the cluster returns to `active`.

```bash title="Finalizing a cluster expansion"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
    --type=merge -p '{"spec": {"action": "expand"}}'
```

Adding the storage nodes themselves is the step before this one, described in
[Expanding a Storage Cluster](../scaling/expanding-storage-cluster.md).

## Monitoring an Action

The action state is exposed in the resource status.

```bash title="Reading the current action status"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status.actionStatus}' | jq .
```

```plain title="Example output of a running action"
{
  "action": "restart",
  "state": "running",
  "message": "start",
  "observedGeneration": 7,
  "triggered": true,
  "updatedAt": "2026-08-22T09:14:03Z"
}
```

The backend lifecycle status of the cluster is tracked separately from the action.

```bash title="Reading the backend cluster status"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status.status}{"\n"}'
```

```bash title="Streaming live cluster status changes"
kubectl get storagecluster simplyblock-cluster -n simplyblock -w
```
