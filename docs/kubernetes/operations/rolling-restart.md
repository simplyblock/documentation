---
title: "Rolling Restart"
description: "Restart every storage node of a simplyblock cluster in sequence with the node-recycle action, optionally refreshing the storage-node pod on each worker."
weight: 10710
---

A rolling restart restarts every backend storage node of a cluster, one node at a time, waiting for the cluster to
finish rebalancing before it moves on. It is useful after a change to the storage-node configuration, and after a new
storage-node container image has been rolled out.

The operation is requested through the `spec.action` field of the `StorageCluster` resource, like the other
[Storage Cluster Actions](cluster-actions.md). Its action name is `node-recycle`.

```bash title="Starting a rolling restart of all storage nodes"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
    --type=merge -p '{"spec": {"action": "node-recycle"}}'
```

## Refreshing the Storage Node Pod

By default, a rolling restart shuts each backend node down and restarts it, which leaves the storage-node pod on the
worker untouched. A pod that is already running keeps the image it started with, so a newly pulled image only takes
effect once that pod is replaced.

Setting `nodeRecycle.refreshSNodeAPI` to `true` adds that replacement to every node's turn. The storage-node pod is
deleted after the backend node has been shut down and before it is restarted, so the DaemonSet recreates it, and the
node comes back on the current image.

```bash title="Rolling restart that also refreshes the storage node pods"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
    --type=merge -p '{"spec": {"action": "node-recycle", "nodeRecycle": {"refreshSNodeAPI": true}}}'
```

!!! note
    Without `refreshSNodeAPI`, a rolling restart is a backend restart only. An image change on the `StorageNodeSet`
    does not reach the running pods, so the nodes come back on the image they were already running.

## Phases

Each node passes through the phases below, tracked in `status.nodeRecycleStatus.nodePhase`. The phase applies to the
node currently being restarted, which is the first entry of `status.nodeRecycleStatus.pendingNodes`.

| Phase                | Description                                                                                           |
|----------------------|-------------------------------------------------------------------------------------------------------|
| `shutting-down`      | The backend shutdown was requested. The phase holds until the node reports `offline` or `in_restart`. |
| `snode-refresh`      | The storage-node pod is deleted. Only entered when `refreshSNodeAPI` is `true`.                       |
| `snode-refresh-wait` | The replacement pod is awaited until it is Ready.                                                     |
| `restarting`         | The backend restart was requested with `force`. The phase holds until the node reports `online`.      |
| `rebalancing`        | The cluster is polled every 15 seconds until it reports that rebalancing has finished.                |

Once rebalancing is done, the node moves from `pendingNodes` to `status.nodeRecycleStatus.processedNodes`, and the
next node starts at `shutting-down`. The action succeeds when `pendingNodes` is empty. A cluster without storage nodes
completes immediately with the message `No nodes to recycle`.

A node that is already in `in_shutdown`, `offline`, or `in_restart` is not asked to shut down again, and a node that
is already `in_restart` or `online` is not asked to restart. Both checks make a resumed run skip work that has already
happened. A node missing from the backend node list during `snode-refresh` skips the pod refresh and advances straight
to `restarting`.

## Monitoring the Progress

The per-node progress is held in `status.nodeRecycleStatus`, and the overall state of the action in
`status.actionStatus`.

```bash title="Watching the progress of a rolling restart"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status.nodeRecycleStatus}' | jq .
```

```plain title="Example output of a running rolling restart"
{
  "nodePhase": "rebalancing",
  "pendingNodes": [
    "82198a36-fcbb-43e3-949c-0260bf40f0ac",
    "707dd443-5d0e-470f-bdde-92f1238c4b01"
  ],
  "phaseTriggered": true,
  "processedNodes": [
    "114899a6-d708-499e-8051-bc9ca9713cf8"
  ]
}
```

The number of remaining entries in `pendingNodes` is the number of nodes still to be restarted, including the one
currently in progress.

```bash title="Counting the storage nodes still to be restarted"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status.nodeRecycleStatus.pendingNodes[*]}' | wc -w
```

## Duration and Interruptions

A rolling restart takes as long as the sum of its nodes, since the nodes are handled strictly one after another and
each one waits for a full cluster rebalance. On a large cluster the action therefore runs for a long time, and it
stays `running` in `status.actionStatus` for its whole duration.

A restart of the operator does not start the rollout over. The phase and the node lists live in the resource status,
so the next reconcile resumes at the node and phase that were last persisted.

Changing the spec while a rollout runs discards its progress: the run is re-initialized whenever
`status.actionStatus.observedGeneration` no longer matches the generation of the resource, and `nodeRecycleStatus` is
cleared with it. The rollout then starts again at the first node.

!!! warning
    A rolling restart takes one storage node down at a time, so the cluster runs degraded for the duration of each
    node's turn. The cluster has to tolerate the loss of one node throughout, which the erasure coding scheme has to
    allow for. See [Erasure Coding](../../deployment-preparation/erasure-coding-scheme.md).
