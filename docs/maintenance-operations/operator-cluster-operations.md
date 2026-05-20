---
title: "Operating Storage Clusters via Simplyblock Operator"
description: "How to perform lifecycle operations on a Simplyblock storage cluster and its nodes using the Kubernetes operator and Custom Resource Definitions."
weight: 10750
---

When simplyblock is deployed on OpenShift or Kubernetes, cluster and node lifecycle operations are performed by patching
the `StorageCluster` and `StorageNode` Custom Resources rather than using the CLI directly. The operator picks up the
changes, calls the backend API, polls for the expected terminal state, and records the result in `.status.actionStatus`.

!!! info
    For CLI-based node operations on non-Kubernetes deployments, see
    [Stopping and Manually Restarting a Storage Node](manual-restarting-nodes.md).

## StorageCluster Actions

Storage cluster actions are cluster-wide operations that affect all nodes in the cluster.

To trigger a storage cluster action, the `spec.action` property on a `StorageCluster` resource must be patchec. Only
one action can run at any given time. The operator sets `.status.actionStatus.state` to `running` while the action is in
progress and to `success` or `failed` when it completes.

### Shutdown

```bash title="Shutting down the storage cluster"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
  --type=merge -p '{"spec": {"action": "shutdown"}}'
```

The operator calls the backend shutdown API and polls until the cluster reports `suspended`.

### Start

```bash title="Starting a suspended storage cluster"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
  --type=merge -p '{"spec": {"action": "start"}}'
```

The operator calls the backend start API and polls until the cluster reports `active`.

### Restart

```bash title="Restarting the storage cluster"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
  --type=merge -p '{"spec": {"action": "restart"}}'
```

The operator runs a shutdown, waits for `suspended`, runs start, and waits for `active`. The current sub-phase is stored
in `.status.actionStatus.message`.

### Activate and Reactivate

```bash title="Activating a newly created cluster"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
  --type=merge -p '{"spec": {"action": "activate"}}'
```

The operator calls the backend activate API and waits until the cluster reports `active`.

### Expand

```bash title="Finalizing a cluster expansion"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
  --type=merge -p '{"spec": {"action": "expand"}}'
```

The operator calls the backend expand API and waits until the cluster returns to `active`.

!!! info
    More information on how to add new worker nodes to the storage fabric first is available in
    [Expanding a Storage Cluster](scaling/expanding-storage-cluster.md).

### Node Recycle

Node recycle sequentially restarts every backend storage node in the cluster. Use it after updating the storage-node
container image or changing node configuration.

```bash title="Restarting all storage nodes"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
  --type=merge -p '{"spec": {"action": "node-recycle"}}'
```

To also refresh the storage-node DaemonSet pod on each worker after shutdown and before restart add
`nodeRecycle.refreshSNodeAPI: true`. Situations include when rolling out a new container image:

```bash title="Restarting all storage nodes and refreshing DaemonSet pods"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
  --type=merge -p '{"spec": {"action": "node-recycle", "nodeRecycle": {"refreshSNodeAPI": true}}}'
```

For each backend storage node the operator executes:

1. Shuts down the node and wait until `offline` or `in_restart`.
2. If `refreshSNodeAPI: true`, restarts the DaemonSet pod and wait for the storage-node API to become reachable.
3. Restarts the node and wait until `online`.
4. Waits until cluster `rebalancing` is `false`.
5. Proceeds to the next node.

Progress is tracked in `.status.actionStatus` and `.status.nodeRecycleStatus`:

```bash title="Watching node recycle progress"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
  -o jsonpath='{.status.nodeRecycleStatus}' | jq .
```

## StorageNode Actions

Direct operations on individual backend storage nodes are triggered by patching `spec.action` and `spec.nodeUUID`
on the `StorageNode` resource. Both fields are required together. The CRD validation rejects an `action` without a
`nodeUUID`.

```bash title="Restarting a specific storage node"
kubectl patch storagenode simplyblock-node -n simplyblock \
  --type=merge -p '{
    "spec": {
      "action": "restart",
      "nodeUUID": "<node-uuid>"
    }
  }'
```

After the action completes, `spec.action` and `spec.nodeUUID` must be cleared from the custom resource. The operator
does not automatically clear them.

### Supported Actions and Terminal States

| Action     | Expected backend state after success                            |
|------------|-----------------------------------------------------------------|
| `shutdown` | `offline`                                                       |
| `restart`  | `online`                                                        |
| `suspend`  | `suspended`                                                     |
| `resume`   | `online`                                                        |
| `remove`   | Node no longer present. A `404` response is treated as success. |

### Moving a Storage Node to a Different Worker Node (Storage Node Relocation)

For a `restart` action, two additional fields are available:

| Field            | Type   | Description                                                                                                                                                                   |
|------------------|--------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `workerNode`     | string | Kubernetes worker to restart the storage node on. The operator labels the worker and waits for the storage node API to become reachable before triggering the move operation. |
| `reattachVolume` | bool   | Reattach volumes during restart where the backend supports it.                                                                                                                |
| `force`          | bool   | Force the action where supported by the backend.                                                                                                                              |

## Monitoring Action Progress

### Watch Cluster Action State

```bash title="Getting current action status"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
  -o jsonpath='{.status.actionStatus}' | jq .
```

```bash title="Streaming live status changes"
kubectl get storagecluster simplyblock-cluster -n simplyblock -w
```

### Read Backend Cluster Status

```bash title="Getting backend lifecycle status"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
  -o jsonpath='{.status.status}{"\n"}'
```

### Inspecting individual node states

```bash title="Getting all storage node states"
kubectl get storagenode simplyblock-node -n simplyblock \
  -o jsonpath='{.status.nodes}' | jq .
```
