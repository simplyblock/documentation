---
title: "Starting a Storage Cluster"
description: "Bring a suspended simplyblock storage cluster on Kubernetes back into service with the start action, and follow the rebalancing that may follow it."
source: "https://docs.simplyblock.io/latest/kubernetes/operations/cluster/starting-a-cluster/"
---

# Starting a Storage Cluster

A start brings a suspended storage cluster back. The backend start API is called by the Simplyblock Operator, which
then polls until the cluster reports `active`.

```bash title="Starting a suspended storage cluster"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
    --type=merge -p '{"spec": {"action": "start"}}'
```

The rebalancing flag reported by the backend is recorded in `status.rebalancing` once the cluster is up, so data that
has to be moved after the downtime is visible on the resource.

```bash title="Reading the rebalancing flag of a started cluster"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status.rebalancing}{"\n"}'
```

How the request is executed, tracked, and cleared is described in
[Storage Cluster Actions](cluster-actions.md).
