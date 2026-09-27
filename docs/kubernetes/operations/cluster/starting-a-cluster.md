---
title: "Starting a Storage Cluster"
description: "Bring a suspended simplyblock storage cluster on Kubernetes back into service with the Start action, and follow the rebalancing that may follow it."
weight: 10116
---

A start brings a suspended storage cluster back. The backend start API is called by the Simplyblock Operator, which
then polls until the cluster reports `active`.

```bash title="Starting a suspended storage cluster"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageClusterOps
metadata:
  name: start-cluster
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  action: Start
EOF
```

The rebalancing flag reported by the backend is recorded in `status.rebalancing` once the cluster is up, so data that
has to be moved after the downtime is visible on the resource.

```bash title="Reading the rebalancing flag of a started cluster"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status.rebalancing}{"\n"}'
```

How the request is executed, tracked, and cleared is described in
[Storage Cluster Actions](cluster-actions.md).
