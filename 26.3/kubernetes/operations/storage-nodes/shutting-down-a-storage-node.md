---
title: "Shutting Down a Storage Node"
description: "Stop a single simplyblock storage node with the shutdown action of a StorageNodeOps resource, and learn the conditions that refuse a graceful shutdown."
source: "https://docs.simplyblock.io/latest/kubernetes/operations/storage-nodes/shutting-down-a-storage-node/"
---

# Shutting Down a Storage Node

A shutdown stops one storage node and leaves the rest of the cluster serving I/O. The volumes whose primary the node
was are served through their failover paths until it returns. The operation succeeds once the node reports the status
`offline`.

```bash title="Shutting down a single storage node"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeOps
metadata:
  name: shutdown-worker-1
  namespace: simplyblock
spec:
  storageNodeRef: simplyblock-node-mejue8
  action: shutdown
EOF
```

## Conditions That Refuse a Shutdown

A graceful shutdown is validated before it is accepted, and it is refused while

- another storage node of the cluster is restarting,
- another storage node of the cluster is already shutting down,
- a restart task is open for this node,
- a migration task is open for this node, unless the cluster tolerates the outage with dual fault tolerance (FTT 2), or
- the node is in a state other than `online`, `suspended`, or `down`.

A refusal is answered by the control plane rather than swallowed, and the operator retries the request every ten
seconds, so an operation created while one of the conditions holds proceeds on its own once the condition clears.

With `spec.force` set to `true` every one of these refusals is downgraded to a warning and the shutdown is carried out
regardless. Forcing a shutdown while data is being moved risks the redundancy of that data, so it is meant for a node
that has to go down whatever the state of the cluster is.

```yaml title="Example of a forced shutdown"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeOps
metadata:
  name: shutdown-worker-1-forced
  namespace: simplyblock
spec:
  storageNodeRef: simplyblock-node-mejue8
  action: shutdown
  force: true
```

The node is brought back with [Restarting a Storage Node](restarting-a-storage-node.md). Taking a node out of the
cluster for good is [Removing a Storage Node](removing-a-storage-node.md). How an operation is tracked and cleaned up
is described in [Storage Node Actions](storage-node-actions.md).
