---
title: "Suspending a Storage Node"
description: "Suspend a single simplyblock storage node with a Suspend operation, so that no new volume is placed on it while it keeps serving the volumes it holds."
weight: 10216
---

A suspend keeps a storage node running but stops new volumes from being placed on it. The volumes the node already
serves are unaffected. The operation succeeds once the node reports the status `suspended`.

```yaml title="Example of a node suspension (suspend-node.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageNodeOps
metadata:
  name: suspend-worker-1
  namespace: simplyblock
spec:
  nodeRef: simplyblock-cluster-worker-1-0
  action: Suspend
```

```bash title="Suspending a single storage node"
kubectl apply -f suspend-node.yaml
```

The operation runs the steps `Requesting` and `Awaiting`. A suspension of a node that is already `suspended` succeeds
at once without a call to the control plane. The control plane suspends only an `online` node, and it refuses a request
against a node in any other state.

The node is returned to normal service with [Resuming a Storage Node](resuming-a-storage-node.md). A removal suspends
the node on its own before it moves the volumes off, as described in
[Removing a Storage Node](removing-a-storage-node.md). How an operation is tracked and cleaned up is described in
[Storage Node Actions](storage-node-actions.md).
