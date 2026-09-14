---
title: "Shutting Down a Storage Cluster"
description: "Suspend an entire simplyblock storage cluster on Kubernetes with the shutdown action, and learn what it means for the volumes the cluster serves."
source: "https://docs.simplyblock.io/latest/kubernetes/operations/cluster/shutting-down-a-cluster/"
---

# Shutting Down a Storage Cluster

A shutdown suspends the entire storage cluster. The backend shutdown API is called by the Simplyblock Operator, which
then polls until the cluster reports `suspended`.

```bash title="Shutting down the storage cluster"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
    --type=merge -p '{"spec": {"action": "shutdown"}}'
```

How the request is executed, tracked, and cleared is described in
[Storage Cluster Actions](cluster-actions.md). A suspended cluster is brought back with
[Starting a Storage Cluster](starting-a-cluster.md).

!!! warning
    A cluster shutdown takes every volume of the cluster offline. Workloads consuming those volumes lose their storage
    for the duration of the shutdown. To take a single storage node out of service instead, see
    [Shutting Down a Storage Node](../storage-nodes/shutting-down-a-storage-node.md).
