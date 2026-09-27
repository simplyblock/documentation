---
title: "Rolling Restart"
description: "Restart every storage node of a simplyblock cluster in sequence with a RollingRestart operation, optionally replacing the storage-node pod on each worker."
weight: 10120
---

A rolling restart restarts every backend storage node of a cluster, one node at a time, and waits for the cluster to
finish rebalancing before it moves on. It is useful after a change to the storage-node configuration, and after a new
storage-node container image has been rolled out.

The operation is a `StorageClusterOps` with the action `RollingRestart`, like the other
[Storage Cluster Actions](cluster-actions.md).

```yaml title="Example of a rolling restart (rolling-restart.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageClusterOps
metadata:
  name: roll-simplyblock-cluster
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  action: RollingRestart
```

```bash title="Starting a rolling restart of all storage nodes"
kubectl apply -f rolling-restart.yaml
```

## Refreshing the Storage Node Pod

By default, a rolling restart shuts each backend node down and restarts it, which leaves the storage-node pod on the
worker untouched. A pod that is already running keeps the image it started with.

Setting `spec.rollingRestart.refreshSNodeAPI` to `true` adds a pod replacement to every node's turn. The storage-node
pod is deleted after the backend node has been shut down and before it is restarted, the DaemonSet recreates it, and
the node comes back on the current image.

```yaml title="Example of a rolling restart that refreshes the storage-node pods"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageClusterOps
metadata:
  name: roll-simplyblock-cluster-refresh
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  action: RollingRestart
  rollingRestart:
    refreshSNodeAPI: true
```

This is the form used after a storage-node image change, as described in [Upgrading a Cluster](cluster-upgrade.md).

## Steps

When the operation starts, it lists the storage nodes of the cluster and writes their UUIDs, in the order they will be
restarted, to `status.rollingRestart.nodes`. The list is not changed afterward: a node that joins the cluster during the
walk is not restarted, and a node that leaves it is skipped when the walk reaches it. `status.rollingRestart.nodeIndex`
is the position of the node currently being restarted.

Each node passes through the steps below, tracked in `status.step.state`.

| Step               | Description                                                                                                |
|--------------------|------------------------------------------------------------------------------------------------------------|
| `CheckingPeers`    | The walk holds until every other storage node of the cluster is `online`. Nothing is changed in this step. |
| `ShuttingDownNode` | The backend shutdown is requested, and the step holds until the node is `offline` or `in_restart`.         |
| `RefreshingPod`    | The storage-node pod on the node's worker is deleted. Only entered when `refreshSNodeAPI` is `true`.       |
| `AwaitingPod`      | The replacement pod is awaited until it is Ready. Only entered when `refreshSNodeAPI` is `true`.           |
| `RestartingNode`   | The backend restart is requested, and the step holds until the node is `online`.                           |
| `Rebalancing`      | The step holds until the cluster reports that rebalancing has finished.                                    |

Once rebalancing is done, the index advances, and the next node starts at `CheckingPeers`. The operation succeeds when
the index reaches the end of the list. A cluster without storage nodes completes immediately.

Every call is skipped when the node is already where the call would put it, so a resumed operation does not shut down
or restart a node twice. A restart of the operator does not start the walk over, since the node list, the index, and
the step are persisted in the status of the operation.

## Holding for Peers

Taking a node down while another one is already offline can exceed the fault tolerance of the cluster, so every
shutdown is gated on all peers being `online`. While a peer is not, the walk holds in `CheckingPeers`, and a
`PeerNodeNotOnline` warning names the peers it waits for.

```bash title="Checking why a rolling restart holds"
kubectl get events -n simplyblock \
    --field-selector reason=PeerNodeNotOnline
```

`CheckingPeers` has a deadline of two hours. A walk that holds for longer fails with `StepDeadlineExceeded`, which
separates a cluster that is degraded for good from one that recovers on its own.

## Monitoring the Progress

```bash title="Watching the progress of a rolling restart"
kubectl get storageclusterops roll-simplyblock-cluster -n simplyblock -o wide -w
```

```bash title="Reading the position of the walk"
kubectl get storageclusterops roll-simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status}' | jq '{phase, step, rollingRestart}'
```

```plain title="Example of the rolling restart status"
{
  "phase": "Running",
  "rollingRestart": {
    "nodeIndex": 1,
    "nodes": [
      "114899a6-d708-499e-8051-bc9ca9713cf8",
      "82198a36-fcbb-43e3-949c-0260bf40f0ac",
      "707dd443-5d0e-470f-bdde-92f1238c4b01"
    ]
  },
  "step": {
    "deadline": "2026-09-25T14:52:10Z",
    "state": "Rebalancing"
  }
}
```

A `NodeRestarted` event is emitted each time the walk advances to the next node.

## Aborting a Rolling Restart

A rolling restart can be aborted in `CheckingPeers` and in `Rebalancing`, where no node is down on behalf of the
operation. From `ShuttingDownNode` to `RestartingNode`, the node is offline and the operation is the only thing that
brings it back, so an abort there is not honored, and the webhook refuses deleting the operation.

```bash title="Aborting a rolling restart"
kubectl patch storageclusterops roll-simplyblock-cluster -n simplyblock \
    --type=merge -p '{"spec": {"abort": true}}'
```

The abort takes effect at the next step boundary where it is allowed. A walk that holds in `CheckingPeers` on a
degraded cluster is the usual reason to abort one.

!!! warning
    A rolling restart takes one storage node down at a time, so the cluster runs degraded for the duration of each
    node's turn. The cluster has to tolerate the loss of one node throughout, which the erasure coding scheme has to
    allow for. See [Erasure Coding](../../../deployment-preparation/erasure-coding-scheme.md).
