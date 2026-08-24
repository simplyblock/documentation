---
title: "Restarting a Storage Node"
description: "Restart a single simplyblock storage node with the restart action of a StorageNodeOps resource, optionally forced and reattaching its volumes."
weight: 10214
---

A restart stops and starts one storage node. It is how an offline node is brought back, and how a change to the
storage node configuration or a new container image is picked up on a single node. The operation succeeds once the
node reports the status `online`.

```bash title="Restarting a single storage node"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeOps
metadata:
  name: restart-worker-1
  namespace: simplyblock
spec:
  storageNodeRef: simplyblock-node-mejue8
  action: restart
EOF
```

Two optional fields apply to a restart. With `force` the backend request carries the force flag, and with
`reattachVolume` the volumes of the node are reattached as part of the restart.

```yaml title="Example of a forced restart that reattaches the volumes"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeOps
metadata:
  name: restart-worker-1-forced
  namespace: simplyblock
spec:
  storageNodeRef: simplyblock-node-mejue8
  action: restart
  force: true
  reattachVolume: true
```

To restart every node of a cluster instead of one, see [Rolling Restart](../cluster/rolling-restart.md), which
sequences the nodes and waits for the rebalancing between them. How an operation is tracked and cleaned up is
described in [Storage Node Actions](storage-node-actions.md).
