---
title: "Shutting Down a Storage Node"
description: "Stop a single simplyblock storage node with a Shutdown operation of a StorageNodeOps resource, and learn the conditions under which it is held or refused."
weight: 10212
---

A shutdown stops one storage node and leaves the rest of the cluster serving I/O. The volumes whose primary the node
was are served through their failover paths until it returns. The operation succeeds once the node reports the status
`offline`.

```yaml title="Example of a node shutdown (shutdown-node.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageNodeOps
metadata:
  name: shutdown-worker-1
  namespace: simplyblock
spec:
  nodeRef: simplyblock-cluster-worker-1-0
  action: Shutdown
```

```bash title="Shutting down a single storage node"
kubectl apply -f shutdown-node.yaml
```

The operation runs the steps `Requesting` and `Awaiting`. A shutdown of a node that is already `offline` succeeds at
once without a call to the control plane.

## Conditions That Hold or Refuse a Shutdown

The operator holds the shutdown, with a `ClusterNotReady` event, while the cluster is not `active` or is rebalancing.
Taking a node down in that state could exceed the fault tolerance of the cluster, and the operation continues on its
own once the cluster has settled.

The control plane validates a graceful shutdown before it accepts it, and it refuses it while

- another storage node of the cluster is restarting,
- another storage node of the cluster is already shutting down,
- a restart task is open for this node,
- a migration task is open for this node, unless the cluster tolerates the outage with dual fault tolerance (FTT 2), or
- the node is in a state other than `online`, `suspended`, or `down`.

A refusal is written to `status.message`, and the request is retried. An operation created while one of the conditions
holds therefore proceeds on its own once the condition clears, within the two-minute deadline of the `Requesting` step.

!!! note
    A shutdown is always graceful. `spec.force` applies to the restart-based actions and has no effect on a shutdown.

The node is brought back with [Restarting a Storage Node](restarting-a-storage-node.md). Taking a node out of the
cluster for good is [Removing a Storage Node](removing-a-storage-node.md). How an operation is tracked and cleaned up
is described in [Storage Node Actions](storage-node-actions.md).
