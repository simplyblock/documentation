---
title: "Operating Storage Clusters via Simplyblock Operator"
description: "How to perform lifecycle operations on a Simplyblock storage cluster and its nodes using the Kubernetes operator and Custom Resource Definitions."
weight: 10750
---

When simplyblock is deployed on OpenShift or Kubernetes, cluster and node lifecycle operations are performed through
Custom Resources rather than using the CLI directly. The operator picks up changes, calls the backend API, polls for
the expected terminal state, and records the result in `.status`.

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

## StorageNodeOps Actions

Direct operations on individual backend storage nodes are performed by creating a `StorageNodeOps` resource. It
targets a single `StorageNode` by name, runs the requested action to completion, and records the outcome. Only one
`StorageNodeOps` may be active for a given `StorageNode` at a time.

```bash title="Find the StorageNode name to target"
kubectl get storagenodes -n simplyblock
```

```bash title="Restart a specific storage node"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeOps
metadata:
  name: restart-worker-1
  namespace: simplyblock
spec:
  storageNodeRef: simplyblock-node-worker-1.example.com-s0-n0
  action: restart
EOF
```

Track progress by watching the `StorageNodeOps` status:

```bash title="Watch the operation status"
kubectl get storagenodeops restart-worker-1 -n simplyblock -w
```

```bash title="Get detailed status"
kubectl get storagenodeops restart-worker-1 -n simplyblock \
  -o jsonpath='{.status}' | jq .
```

Once the operation is complete (`phase: Succeeded` or `phase: Failed`), the `StorageNodeOps` CR can be deleted.
The operator does not delete it automatically.

```bash title="Clean up after completion"
kubectl delete storagenodeops restart-worker-1 -n simplyblock
```

### Supported Actions and Terminal States

| Action     | Expected outcome after success                                               |
|------------|------------------------------------------------------------------------------|
| `shutdown` | Node transitions to `offline`.                                               |
| `restart`  | Node transitions back to `online`.                                           |
| `suspend`  | Node transitions to `suspended`.                                             |
| `resume`   | Node transitions back to `online`.                                           |
| `remove`   | Node is drained, all volumes migrated, node deleted from backend.            |

### Migrating a Node to a Different Worker

The `migrate` action relocates a storage node to a different Kubernetes worker **without removing it** from the
cluster. The node keeps its backend UUID and data — no volumes are moved between nodes. After the migration the
backend triggers a rebalance automatically.

```bash title="Migrate a storage node to a different worker"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeOps
metadata:
  name: migrate-worker-1
  namespace: simplyblock
spec:
  storageNodeRef: simplyblock-node-worker-1.example.com-s0-n0
  action: migrate
  targetWorkerNode: worker-5.example.com
EOF
```

```bash title="Watch migration progress"
kubectl get storagenodeops migrate-worker-1 -n simplyblock -w
```

The operation progresses through sub-phases: `Preparing → Restarting → Promoting`. See
[StorageNodeOps: migrate](../reference/operator/index.md#migrating-a-storage-node-to-a-different-worker-migrate)
for full details including `newSsdPcie` and `reattachVolume` options.

### Draining and Removing a Node

The `remove` action runs a multi-step drain workflow. Progress is tracked in `status.subPhase`:

```
Validating → Suspending → Migrating → Verifying → Removing
```

```bash title="Remove (drain) a storage node"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeOps
metadata:
  name: drain-worker-1
  namespace: simplyblock
spec:
  storageNodeRef: simplyblock-node-worker-1.example.com-s0-n0
  action: remove
EOF
```

```bash title="Watch drain progress"
kubectl get storagenodeops drain-worker-1 -n simplyblock \
  -o jsonpath='{.status.subPhase}{"\n"}' -w
```

## Monitoring Action Progress

### Watch Cluster Action State

```bash title="Getting current cluster action status"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
  -o jsonpath='{.status.actionStatus}' | jq .
```

```bash title="Streaming live cluster status changes"
kubectl get storagecluster simplyblock-cluster -n simplyblock -w
```

### Read Backend Cluster Status

```bash title="Getting backend lifecycle status"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
  -o jsonpath='{.status.status}{"\n"}'
```

### Inspecting individual node states

```bash title="Getting all storage node states from the StorageNodeSet"
kubectl get storagenodeset simplyblock-node -n simplyblock \
  -o jsonpath='{.status.nodes}' | jq .
```

```bash title="Getting individual StorageNode status"
kubectl get storagenodes -n simplyblock
```
