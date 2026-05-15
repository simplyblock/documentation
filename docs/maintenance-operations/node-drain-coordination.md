---
title: "Kubernetes Node Drain Coordination"
description: "How the Simplyblock operator automatically protects storage availability during Kubernetes node maintenance such as cordon, drain, and rolling OS upgrades."
weight: 10800
---

When a Kubernetes worker node is cordoned or drained — for example during a rolling OS upgrade or node replacement —
the Simplyblock operator automatically coordinates the shutdown and restart of the backend storage node running on
that worker. No manual intervention is required.

Concurrency is controlled by `StorageCluster.spec.maxFaultTolerance`. At most that many workers may be inside the
active drain window at once, preventing the cluster from entering a degraded state during bulk maintenance.

## How It Works

When the operator detects that a worker node has become cordoned, it executes the following sequence:

1. Create a PodDisruptionBudget to prevent premature pod eviction.
2. Call the Simplyblock shutdown API for the backend storage node and wait until `offline`.
3. Relax the PDB to allow pod eviction — Kubernetes can now drain the worker.
4. Wait for the worker to return to a ready, uncordoned state.
5. Call the Simplyblock restart API and wait until `online` and cluster `rebalancing` is `false`.
6. Mark drain coordination `complete` and remove the PDB.

!!! warning
    If another worker is already in the drain window and `maxFaultTolerance` would be exceeded, the operator holds
    the new worker in the `detected` phase until an in-progress drain completes.

## Drain Phases

Each worker being drained progresses through the following phases, tracked in
`StorageNode.status.drainCoordination`:

| Phase             | Description                                                                 |
|-------------------|-----------------------------------------------------------------------------|
| `detected`        | Worker is cordoned; waiting for a drain slot within `maxFaultTolerance`.    |
| `shutdown_called` | Backend shutdown API has been called; waiting for `offline`.                |
| `draining`        | Shutdown confirmed; PDB relaxed — Kubernetes may evict pods.                |
| `restart_called`  | Worker is back; backend restart API has been called; waiting for `online`.  |
| `complete`        | Node is back online and cluster rebalancing has finished.                   |
| `failed`          | An unrecoverable error occurred; manual intervention may be required.       |

## Monitoring Drain State

```bash title="Inspect drain coordination status"
kubectl get storagenode simplyblock-node -n simplyblock \
  -o jsonpath='{.status.drainCoordination}' | jq .
```

```bash title="Stream live changes"
kubectl get storagenode simplyblock-node -n simplyblock -w
```

## Configuring Fault Tolerance

Set `spec.maxFaultTolerance` on the `StorageCluster` resource to control how many workers can be simultaneously
inside the drain window:

```yaml title="Example: allow one worker in the drain window at a time"
spec:
  maxFaultTolerance: 1
```

A value of `1` is the safest default. Increase it only if your erasure coding scheme and replication factor can
tolerate multiple simultaneous node outages without data unavailability.
