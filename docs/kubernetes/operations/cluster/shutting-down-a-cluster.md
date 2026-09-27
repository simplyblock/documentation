---
title: "Shutting Down a Storage Cluster"
description: "Suspend an entire simplyblock storage cluster on Kubernetes with a Shutdown operation, and learn what it means for the volumes the cluster serves."
weight: 10114
---

A shutdown suspends the entire storage cluster. The Simplyblock Operator calls the shutdown of the control plane and
waits until the cluster is no longer `active`. The `StorageCluster` then reports the phase `Suspended`.

```yaml title="Example of a cluster shutdown (shutdown-cluster.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageClusterOps
metadata:
  name: shutdown-simplyblock-cluster
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  action: Shutdown
```

```bash title="Shutting down the storage cluster"
kubectl apply -f shutdown-cluster.yaml
```

```bash title="Confirming that the cluster is suspended"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status.phase}{" "}{.status.status}{"\n"}'
```

The operation runs the steps `Requesting` and `Awaiting`. A shutdown of a cluster that is not `active` succeeds at once
without a call to the control plane. Once the request has been sent, in `Awaiting`, the shutdown can no longer be
aborted, and the operation cannot be deleted until it is terminal.

How an operation is tracked and cleaned up is described in [Storage Cluster Actions](cluster-actions.md). A suspended
cluster is brought back with [Starting a Storage Cluster](starting-a-cluster.md).

!!! warning
    A cluster shutdown takes every volume of the cluster offline. Workloads consuming those volumes lose their storage
    for the duration of the shutdown. To take a single storage node out of service instead, see
    [Shutting Down a Storage Node](../storage-nodes/shutting-down-a-storage-node.md).
