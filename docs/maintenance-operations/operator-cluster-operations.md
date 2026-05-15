---
title: "Cluster and Node Operations via the Kubernetes Operator"
description: "How to perform lifecycle operations on a Simplyblock storage cluster and its nodes using the Kubernetes operator and Custom Resource Definitions."
weight: 10750
---

When Simplyblock is deployed on Kubernetes, cluster and node lifecycle operations are performed by patching the
`StorageCluster` and `StorageNode` Custom Resources rather than using the CLI directly. The operator picks up the
change, calls the backend API, polls for the expected terminal state, and records the result in `.status.actionStatus`.

!!! info
    For CLI-based node operations on non-Kubernetes deployments, see
    [Stopping and Manually Restarting a Storage Node](manual-restarting-nodes.md).

## StorageCluster Actions

Trigger a cluster-wide action by patching `spec.action` on the `StorageCluster` resource. Only one action runs at
a time. The operator sets `.status.actionStatus.state` to `running` while the action is in progress and to
`success` or `failed` when it completes.

### Shutdown

```bash title="Shut down the storage cluster"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
  --type=merge -p '{"spec": {"action": "shutdown"}}'
```

The operator calls the backend shutdown API and polls until the cluster reports `suspended`.

### Start

```bash title="Start a suspended storage cluster"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
  --type=merge -p '{"spec": {"action": "start"}}'
```

The operator calls the backend start API and polls until the cluster reports `active`.

### Restart

```bash title="Restart the storage cluster"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
  --type=merge -p '{"spec": {"action": "restart"}}'
```

Runs shutdown → waits for `suspended` → runs start → waits for `active`. The current sub-phase is stored in
`.status.actionStatus.message`.

### Activate

```bash title="Activate a newly created cluster"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
  --type=merge -p '{"spec": {"action": "activate"}}'
```

The operator calls the backend activate API and waits until the cluster reports `active`.

### Expand

```bash title="Finalize a cluster expansion"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
  --type=merge -p '{"spec": {"action": "expand"}}'
```

The operator calls the backend expand API and waits until the cluster returns to `active`.

!!! info
    To add new worker nodes to the storage fabric first, see
    [Expanding a Storage Cluster](scaling/expanding-storage-cluster.md).

### Node Recycle

Node recycle sequentially restarts every backend storage node in the cluster. Use it after updating the storage-node
container image or changing node configuration.

```bash title="Recycle all storage nodes"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
  --type=merge -p '{"spec": {"action": "node-recycle"}}'
```

To also refresh the storage-node DaemonSet pod on each worker after shutdown and before restart — for example when
rolling out a new container image — add `nodeRecycle.refreshSNodeAPI: true`:

```bash title="Recycle all storage nodes and refresh DaemonSet pods"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
  --type=merge -p '{"spec": {"action": "node-recycle", "nodeRecycle": {"refreshSNodeAPI": true}}}'
```

For each backend storage node the operator executes:

1. Shut down the node and wait until `offline` or `in_restart`.
2. If `refreshSNodeAPI: true`, restart the DaemonSet pod and wait for the storage-node API to become reachable.
3. Restart the node and wait until `online`.
4. Wait until cluster `rebalancing` is `false`.
5. Proceed to the next node.

Progress is tracked in `.status.actionStatus` and `.status.nodeRecycleStatus`:

```bash title="Watch node recycle progress"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
  -o jsonpath='{.status.nodeRecycleStatus}' | jq .
```

## StorageNode Actions

Direct operations on individual backend storage nodes are triggered by patching `spec.action` and `spec.nodeUUID`
on the `StorageNode` resource. Both fields are required together — CRD validation rejects an `action` without a
`nodeUUID`.

```bash title="Restart a specific storage node"
kubectl patch storagenode simplyblock-node -n simplyblock \
  --type=merge -p '{
    "spec": {
      "action": "restart",
      "nodeUUID": "<node-uuid>"
    }
  }'
```

After the action completes, clear `spec.action` and `spec.nodeUUID` from the CR — the operator does not clear them
automatically.

### Supported Actions and Terminal States

| Action     | Expected backend state after success           |
|------------|------------------------------------------------|
| `shutdown` | `offline`                                      |
| `restart`  | `online`                                       |
| `suspend`  | `suspended`                                    |
| `resume`   | `online`                                       |
| `remove`   | node no longer present; `404` treated as success |

### Restart with Worker Relocation

For a `restart` action, two additional fields are available:

| Field            | Type | Description |
|------------------|------|-------------|
| `workerNode`     | string | Kubernetes worker to restart the node on. The operator labels the worker and waits for the storage-node API to become reachable before triggering restart. |
| `reattachVolume` | bool | Reattach volumes during restart where the backend supports it. |
| `force`          | bool | Force the action where supported by the backend. |

## Monitoring Action Progress

### Watch cluster action state

```bash title="Get current action status"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
  -o jsonpath='{.status.actionStatus}' | jq .
```

```bash title="Stream live status changes"
kubectl get storagecluster simplyblock-cluster -n simplyblock -w
```

### Read backend cluster status

```bash title="Get backend lifecycle status"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
  -o jsonpath='{.status.status}{"\n"}'
```

### Inspect individual node states

```bash title="Get all storage node states"
kubectl get storagenode simplyblock-node -n simplyblock \
  -o jsonpath='{.status.nodes}' | jq .
```
