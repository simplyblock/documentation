---
title: "Restarting a Storage Node"
description: "Restart a single simplyblock storage node with a Restart operation of a StorageNodeOps resource, optionally with the force flag of the control plane."
weight: 10214
---

A restart stops and starts one storage node. It is how an offline node is brought back, and how a change to the
storage node configuration or a new SPDK image is picked up on a single node. The operation succeeds once the node
reports the status `online`.

```yaml title="Example of a node restart (restart-node.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageNodeOps
metadata:
  name: restart-worker-1
  namespace: simplyblock
spec:
  nodeRef: simplyblock-cluster-worker-1-0
  action: Restart
```

```bash title="Restarting a single storage node"
kubectl apply -f restart-node.yaml
```

With the optional field `force`, the request carries the force flag of the control plane. A field that is left out is
not sent, and the control plane applies its own default. `reattachVolume` has no effect on a restart, since it is read
only when a restart moves the node to another host, as in [Migrating a Storage Node](migrating-a-storage-node.md).

```yaml title="Example of a forced restart"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageNodeOps
metadata:
  name: restart-worker-1-forced
  namespace: simplyblock
spec:
  nodeRef: simplyblock-cluster-worker-1-0
  action: Restart
  force: true
```

The operation runs the steps `Requesting` and `Awaiting`, and it holds with a `ClusterNotReady` event while the
cluster is not `active` or is rebalancing. An abort is honored only in `Requesting`, before the restart has been sent.

To restart every node of a cluster instead of one, see [Rolling Restart](../cluster/rolling-restart.md), which
sequences the nodes and waits for the rebalancing between them. How an operation is tracked and cleaned up is
described in [Storage Node Actions](storage-node-actions.md).
