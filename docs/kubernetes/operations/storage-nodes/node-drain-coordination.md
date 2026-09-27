---
title: "Coordinated Worker Node Drain"
description: "How the Simplyblock Operator protects storage availability with a HostMaintenance operation when a Kubernetes worker is cordoned and drained."
weight: 10250
---

When a Kubernetes worker is cordoned or drained, for example, during a rolling OS upgrade, the Simplyblock Operator
takes the storage node on that worker down gracefully, lets the drain proceed, and brings the node back once the
worker returns. The sequence is a `StorageNodeOps` with the action `HostMaintenance`, which the operator raises on its
own. No manual intervention is required.

This is a temporary absence, after which the storage node returns to the same worker. Taking a node out of the
cluster for good is a different operation, described in [Removing a Storage Node](removing-a-storage-node.md).

## How It Is Triggered

The operator watches the Kubernetes nodes. When the worker of a registered storage node is cordoned, it creates a
`StorageNodeOps` named `<storage-node>-maintenance` with the action `HostMaintenance`, owned by the `StorageNode`. A
worker that hosts several storage nodes gets one operation per node.

```bash title="Cordoning and draining a worker"
kubectl cordon worker-1.example.com
kubectl drain worker-1.example.com --ignore-daemonsets --delete-emptydir-data
```

```bash title="Following the maintenance window"
kubectl get storagenodeops simplyblock-cluster-worker-1-0-maintenance -n simplyblock -o wide -w
```

A `HostMaintenance` operation can also be created by hand, and it then behaves identically, which is useful for
testing the flow without cordoning anything.

!!! warning
    The operator raises the operation only if no object named `<storage-node>-maintenance` exists yet. A completed
    maintenance record is therefore deleted before the next maintenance window of the same worker, otherwise that
    window is not coordinated.

    ```bash title="Deleting the record of a completed maintenance window"
    kubectl delete storagenodeops simplyblock-cluster-worker-1-0-maintenance -n simplyblock
    ```

## Steps

| Step           | Deadline   | Description                                                                                                 |
|----------------|------------|-------------------------------------------------------------------------------------------------------------|
| `Holding`      | 6 hours    | Waits for a maintenance slot, so that no more workers than allowed are in maintenance at once.              |
| `ShuttingDown` | 15 minutes | Blocks the eviction of the storage-node pod with a `PodDisruptionBudget`, then shuts the backend node down. |
| `Releasing`    | 15 minutes | Relaxes the budget, so that the drain can evict the pod, and waits until the pod is gone.                   |
| `AwaitingHost` | 4 hours    | Waits until the storage-node API on the worker answers again after the reboot.                              |
| `Restarting`   | 45 minutes | Restarts the backend node, and waits until it is `online`.                                                  |
| `Cleanup`      | 5 minutes  | Removes the disruption budgets the window put in place.                                                     |

The `PodDisruptionBudget` runs backward from the usual one. It allows no disruption and is created before the
shutdown, so that `kubectl drain` blocks on the storage-node pod while the backend node is being taken down
gracefully. Relaxing it in `Releasing` is what lets the drain proceed. On a hyper-converged worker, the operator also
protects its own pod in the same way until `Releasing`, so that the drain cannot evict the operator before the storage
node is safely offline.

`spec.force` and `spec.reattachVolume` of the operation apply to the restart in `Restarting`.

!!! note
    If the worker does not come back within the four hours of `AwaitingHost`, the operation fails and the node stays
    offline. It is then recovered with a [Restart](restarting-a-storage-node.md) once the worker is back.

## Concurrent Maintenance Windows

How many workers may be in maintenance at the same time is capped by the `StorageCluster`. A window that has passed
`Holding` holds a slot, counted by distinct worker, so the storage nodes of a multi-socket worker share one slot. A
window that has to wait holds in `Holding` with a `MaintenanceQueued` event, and it continues once a slot frees up.

| Field                                | Description                                                                         |
|--------------------------------------|-------------------------------------------------------------------------------------|
| `spec.maxConcurrentWorkerRestarts`   | The number of workers that may be in maintenance at once. Minimum `1`, default `1`. |
| `status.maxFaultTolerance`           | The fault tolerance the control plane reports for the cluster.                      |
| `status.maxConcurrentWorkerRestarts` | The effective cap: the smaller of the two values above.                             |

```yaml title="Example of allowing two workers in maintenance at a time"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageCluster
metadata:
  name: simplyblock-cluster
  namespace: simplyblock
spec:
  maxConcurrentWorkerRestarts: 2
```

```bash title="Reading the effective number of concurrent maintenance windows"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status.maxConcurrentWorkerRestarts}{" of ftt="}{.status.maxFaultTolerance}{"\n"}'
```

A value of `1` is the safest setting. The effective value never exceeds the number of simultaneous node outages the
erasure coding scheme of the cluster tolerates, so a higher setting only takes effect on a cluster that can afford it.

Like the other node operations, a maintenance window also holds with a `ClusterNotReady` event while the cluster is not
`active` or is rebalancing.

## Aborting a Maintenance Window

A maintenance window can be aborted only in `Holding`, before the node has been taken down. From `ShuttingDown`
onward, the node is going down for a reboot that nothing else brings it back from, so an abort is not honored, and the
webhook refuses deleting the operation until it is terminal.

## Monitoring Maintenance Windows

```bash title="Listing the maintenance windows of a namespace"
kubectl get storagenodeops -n simplyblock \
    -o custom-columns=NAME:.metadata.name,NODE:.spec.nodeRef,ACTION:.spec.action,PHASE:.status.phase,STEP:.status.step.state \
    | grep -E 'NAME|HostMaintenance'
```

```bash title="Checking for queued maintenance windows"
kubectl get events -n simplyblock \
    --field-selector reason=MaintenanceQueued
```
