---
title: "Storage Cluster Actions"
description: "Trigger cluster-wide lifecycle operations on a simplyblock storage cluster through the action field of the StorageCluster resource and track their outcome."
source: "https://docs.simplyblock.io/latest/kubernetes/operations/cluster/cluster-actions/"
---

# Storage Cluster Actions

Cluster-wide lifecycle operations are requested declaratively on Kubernetes. Setting `spec.action` on a
`StorageCluster` resource makes the Simplyblock Operator call the corresponding backend API, poll until the cluster
reaches the expected state, and record the outcome in `status.actionStatus`. The CLI is not involved.

This page describes the mechanism that every action shares: how one is requested, executed, re-run, and monitored.

Only one action can be requested at a time, since `spec.action` holds a single value.

## Requesting an Action

An action is requested by patching the field. The example below shuts the cluster down.

```bash title="Requesting a cluster action"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
    --type=merge -p '{"spec": {"action": "shutdown"}}'
```

| Action         | Effect                                                                 | Expected cluster status | Page                                                                   |
|----------------|------------------------------------------------------------------------|-------------------------|------------------------------------------------------------------------|
| `activate`     | Activates a cluster whose nodes have joined but which is not yet live. | `active`                | [Activating a Storage Cluster](activating-a-cluster.md)                |
| `shutdown`     | Shuts the whole cluster down.                                          | `suspended`             | [Shutting Down a Storage Cluster](shutting-down-a-cluster.md)          |
| `start`        | Starts a previously shut down cluster.                                 | `active`                | [Starting a Storage Cluster](starting-a-cluster.md)                    |
| `restart`      | Runs a shutdown followed by a start.                                   | `active`                | [Restarting a Storage Cluster](restarting-a-cluster.md)                |
| `node-recycle` | Restarts every storage node of the cluster, one after another.         | `active`                | [Rolling Restart](rolling-restart.md)                                  |
| `expand`       | Finalizes a cluster expansion after new storage nodes came online.     | `active`                | [Expanding a Storage Cluster](../scaling/expanding-storage-cluster.md) |

Any other value is rejected by the CRD schema. What each action does is described on its own page, listed in the last
column. This page covers what all of them share.

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
