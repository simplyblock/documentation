---
title: "Parallel Storage Node Addition"
description: "How the Simplyblock operator adds storage nodes in parallel while preserving FoundationDB fault tolerance with sequential adds for FDB-hosting workers."
weight: 10760
---

When a `StorageNode` resource is created with multiple worker nodes, the operator can add non-FDB workers
concurrently rather than sequentially. This significantly reduces cluster provisioning time for large deployments.

## How It Works

The operator classifies each worker node into one of two groups before starting the add process:

- **Non-FDB workers** — workers that do not host any FoundationDB process pods. These are added in parallel up
  to the configured `maxParallelNodeAdds` limit.
- **FDB workers** — workers running pods labelled `foundationdb.org/fdb-cluster-name`. These are always added
  one at a time, in sequence.

The sequential constraint for FDB workers exists because the storage node add process triggers a worker reboot.
Rebooting multiple FDB nodes simultaneously reduces the number of available FDB coordinators below the quorum
threshold, which would cause cluster unavailability.

## Configuration

Parallelism for non-FDB workers is controlled by `StorageNode.spec.maxParallelNodeAdds`.

| Value | Behaviour |
|-------|-----------|
| `1` (default) | All workers added one at a time — safe for all topologies |
| `> 1` | Up to N non-FDB workers added concurrently per reconcile pass |

```yaml title="Enable parallel node addition"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNode
metadata:
  name: simplyblock-node
  namespace: simplyblock
spec:
  clusterName: simplyblock-cluster
  maxParallelNodeAdds: 5   # add up to 5 non-FDB workers at a time
  workerNodes:
    - worker-1
    - worker-2
    - worker-3
    - worker-4
    - worker-5
    - worker-6
    - worker-7
    - worker-8
```

!!! note
    `maxParallelNodeAdds` applies only to non-FDB workers. Workers hosting FoundationDB processes are always
    added sequentially, regardless of this value.

## Pinning FDB to Dedicated Nodes

For the parallelism to be most effective, run FoundationDB on a dedicated subset of storage nodes rather than
spreading it across all workers. Label the FDB-dedicated nodes before installation:

```bash
kubectl label node worker-1 worker-2 worker-4 simplyblock.io/fdb-node=true
```

Then configure the `FoundationDBCluster` resource to use only those nodes via a `nodeSelector`:

```yaml
spec:
  processes:
    general:
      podTemplate:
        spec:
          nodeSelector:
            simplyblock.io/fdb-node: "true"
```

With this setup, only the three labelled nodes are treated as FDB workers. All remaining workers are added
in parallel.

## Validation

The following example shows a cluster with 8 storage workers where 6 non-FDB workers started in parallel.
All SPDK pods entered `ContainerCreating` within the same reconcile pass:

```
NAME                        NODE                    STATUS
snode-spdk-pod-4420-cb5317  worker-7   ContainerCreating
snode-spdk-pod-4421-cb5317  worker-6   ContainerCreating
snode-spdk-pod-4422-cb5317  worker-3   ContainerCreating
snode-spdk-pod-4423-cb5317  worker-5   ContainerCreating
snode-spdk-pod-4424-cb5317  worker-1   ContainerCreating
snode-spdk-pod-4425-cb5317  worker-8   ContainerCreating
```

The two FDB workers (nodes 2 and 4) were then added sequentially. All 8 nodes came online and the cluster
reached `ACTIVE` status.
