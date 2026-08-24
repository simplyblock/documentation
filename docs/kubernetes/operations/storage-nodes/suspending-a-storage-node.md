---
title: "Suspending a Storage Node"
description: "Suspend a single simplyblock storage node so that no new volume is placed on it, while it keeps serving the volumes it already holds."
weight: 10216
---

A suspend keeps a storage node running but stops new volumes from being placed on it. The volumes the node already
serves are unaffected. The operation succeeds once the node reports the status `suspended`.

```bash title="Suspending a single storage node"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeOps
metadata:
  name: suspend-worker-1
  namespace: simplyblock
spec:
  storageNodeRef: simplyblock-node-mejue8
  action: suspend
EOF
```

Only an `online` node can be suspended, and a request against a node in any other state is refused. The node is
returned to normal service with [Resuming a Storage Node](resuming-a-storage-node.md). How an operation is tracked and
cleaned up is described in [Storage Node Actions](storage-node-actions.md).
