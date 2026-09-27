---
title: "Rolling Restart"
description: "Restart every storage node of a simplyblock cluster in sequence with the RollingRestart action, optionally refreshing the storage-node pod on each worker."
weight: 10120
---

A rolling restart restarts every backend storage node of a cluster, one node at a time, waiting for the cluster to
finish rebalancing before it moves on. It is useful after a change to the storage-node configuration, and after a new
storage-node container image has been rolled out.

The operation is requested with a `StorageClusterOps`, like the other
[Storage Cluster Actions](cluster-actions.md). Its action is `RollingRestart`.

```bash title="Starting a rolling restart of all storage nodes"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageClusterOps
metadata:
  name: rolling-restart
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  action: RollingRestart
EOF
```

## Refreshing the Storage Node Pod

By default, a rolling restart shuts each backend node down and restarts it, which leaves the storage-node pod on the
worker untouched. A pod that is already running keeps the image it started with, so a newly pulled image only takes
effect once that pod is replaced.

Setting `spec.rollingRestart.refreshSNodeAPI` to `true` adds that replacement to every node's turn. The storage-node
pod is deleted after the backend node has been shut down and before it is restarted, so the DaemonSet recreates it,
and the node comes back on the current image.

```bash title="Rolling restart that also refreshes the storage node pods"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageClusterOps
metadata:
  name: rolling-restart-refresh
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  action: RollingRestart
  rollingRestart:
    refreshSNodeAPI: true
EOF
```

!!! note
    Without `refreshSNodeAPI`, a rolling restart is a backend restart only. An image change on
    `StorageCluster.spec.storageNodes` does not reach the running pods, so the nodes come back on the image they
    were already running.

## Steps

Each node passes through the steps below, tracked in `status.step.state`. They apply to the node currently being
restarted, which is the entry of `status.rollingRestart.nodes` at `status.rollingRestart.nodeIndex`.

| Step               | Description                                                                                          |
|--------------------|------------------------------------------------------------------------------------------------------|
| `CheckingPeers`    | The remaining nodes are checked, so that a node is only taken down while the cluster can carry it.   |
| `ShuttingDownNode` | The backend shutdown was requested. The step holds until the node reports `offline` or `in_restart`. |
| `RefreshingPod`    | The storage-node pod is deleted. Only entered when `refreshSNodeAPI` is `true`.                      |
| `AwaitingPod`      | The replacement pod is awaited until it is Ready.                                                    |
| `RestartingNode`   | The backend restart was requested with `force`. The step holds until the node reports `online`.      |
| `Rebalancing`      | The cluster is polled until it reports that rebalancing has finished.                                |

Once rebalancing is done, `nodeIndex` is incremented and the next node starts at `CheckingPeers`. The operation
succeeds when the index reaches the end of the list.

A node that is already in `in_shutdown`, `offline`, or `in_restart` is not asked to shut down again, and a node that
is already `in_restart` or `online` is not asked to restart. Both checks make a resumed run skip work that has already
happened. A node missing from the backend node list during `RefreshingPod` skips the pod refresh and advances
straight to `RestartingNode`.

## Monitoring the Progress

`status.rollingRestart` is the walk's position over the cluster's nodes, and `status.step` is where the machine has
got to within the node currently being restarted. Neither is complete without the other.

```bash title="Watching the progress of a rolling restart"
kubectl get storageclusterops rolling-restart -n simplyblock \
    -o jsonpath='{.status.rollingRestart}' | jq .
```

```plain title="Example output of a running rolling restart"
{
  "nodes": [
    "114899a6-d708-499e-8051-bc9ca9713cf8",
    "82198a36-fcbb-43e3-949c-0260bf40f0ac",
    "707dd443-5d0e-470f-bdde-92f1238c4b01"
  ],
  "nodeIndex": 1
}
```

```bash title="Following the node and the step together"
kubectl get storageclusterops rolling-restart -n simplyblock \
    -o jsonpath='{.status.rollingRestart.nodeIndex}{"/"}{.status.rollingRestart.nodes[*]}{"\t"}{.status.step.state}{"\n"}' -w
```

`status.rollingRestart.nodes` is written once when the walk starts and is not modified afterward, so a node added
mid-walk is not restarted and one removed mid-walk is skipped when the walk reaches it.

## Duration and Interruptions

A rolling restart takes as long as the sum of its nodes, since the nodes are handled strictly one after another and
each one waits for a full cluster rebalance. On a large cluster the operation therefore runs for a long time, and it
stays in the phase `Running` for its whole duration.

A restart of the operator does not start the rollout over. The node list, the index, and the step live in the
operation's status, so the next reconcile resumes at the node and the step that were last persisted.

The spec is immutable, so a rollout cannot be re-aimed once it is running. Stopping one is
[aborting it](cluster-actions.md#aborting-an-action), which unwinds at the next step and leaves the operation in the
phase `Aborted`. A rollout that should cover a changed set of nodes is a new `StorageClusterOps`.

!!! warning
    A rolling restart takes one storage node down at a time, so the cluster runs degraded for the duration of each
    node's turn. The cluster has to tolerate the loss of one node throughout, which the erasure coding scheme has to
    allow for. See [Erasure Coding](../../../deployment-preparation/erasure-coding-scheme.md).
