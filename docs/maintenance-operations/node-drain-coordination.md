---
title: "Draining Coordination of a Kubernetes Worker Node"
description: "How the Simplyblock operator automatically protects storage availability during Kubernetes node maintenance such as cordon, drain, and rolling OS upgrades."
weight: 10800
---

When a Kubernetes worker node is cordoned or drained, for example, during a rolling OS upgrade or node replacement,
the Simplyblock Operator automatically coordinates the shutdown and restart of the backend storage node running on
that worker. No manual intervention is required.

Concurrency is controlled by `StorageCluster.spec.maxFaultTolerance`. It defines the at-most number of Kubernetes
workers that can be drained at the same time. This prevents the cluster from entering a degraded state during bulk
maintenance operations and restarting cycles.

## How It Works

When the operator detects that a worker node has become cordoned, it executes the following sequence:

1. Creates a `PodDisruptionBudget` to prevent premature pod eviction.
2. Calls the simplyblock shutdown API for the backend storage node and wait until `offline`.
3. Relaxes the `PodDisruptionBudget` to allow pod eviction. Kubernetes can now drain the worker.
4. Waits for the worker to return to a ready, uncordoned state.
5. Calls the simplyblock restart API and wait until the storage nodes are `online` and cluster `rebalancing` is `false`.
6. Marks drain coordination `complete` and remove the `PodDisruptionBudget`.

!!! warning
    If another worker is already in the drain window and `maxFaultTolerance` would be exceeded, the operator holds
    the new worker in the `detected` phase until an in-progress drain completes to ensure that the cluster remains
    available and connection loss is mitigated.

## Drain Phases

Each worker being drained progresses through the following phases, tracked in
`StorageNode.status.drainCoordination`:

| Phase             | Description                                                                   |
|-------------------|-------------------------------------------------------------------------------|
| `detected`        | Worker is cordoned. Waiting for a drain slot within `maxFaultTolerance`.      |
| `shutdown_called` | Backend shutdown API has been called. Waiting for `offline`.                  |
| `draining`        | Shutdown confirmed. `PodDisruptionBudget` relaxed. Kubernetes may evict pods. |
| `restart_called`  | Worker is back. Backend restart API has been called. Waiting for `online`.    |
| `complete`        | Node is back online and cluster rebalancing has finished.                     |
| `failed`          | An unrecoverable error occurred. Manual intervention may be required.         |

## Monitoring Drain State

The progress of the drain coordination can be monitored using the `StorageNode` custom resource.

```bash title="Inspecting drain coordination status"
kubectl get storagenode simplyblock-node -n simplyblock \
  -o jsonpath='{.status.drainCoordination}' | jq .
```

```bash title="Streaming live changes"
kubectl get storagenode simplyblock-node -n simplyblock -w
```

## Configuring Fault Tolerance

To control the number of workers that can be simultaneously drained, the property `spec.maxFaultTolerance` on the
`StorageCluster` resource can be configured.

```yaml title="Example: allow one worker in the drain window at a time"
spec:
  maxFaultTolerance: 1
```

A value of `1` is the safest default. The safe-maximum of this value depends on the selected erasure coding scheme and
replication factor. It reflects the maximum number of toleratable simultaneous node outages without connection loss and
traffic interruption.
