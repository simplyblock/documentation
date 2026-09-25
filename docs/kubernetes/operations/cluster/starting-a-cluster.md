---
title: "Starting a Storage Cluster"
description: "Bring a suspended simplyblock storage cluster on Kubernetes back into service with a Start operation, and follow the rebalancing that may follow it."
weight: 10116
---

A start brings a suspended storage cluster back into service. The Simplyblock Operator calls the start of the control
plane and waits until the cluster reports the backend status `active`.

```yaml title="Example of a cluster start (start-cluster.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageClusterOps
metadata:
  name: start-simplyblock-cluster
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  action: Start
```

```bash title="Starting a suspended storage cluster"
kubectl apply -f start-cluster.yaml
```

The operation runs the steps `Requesting` and `Awaiting`. A start of a cluster that is already `active` succeeds at
once without a call to the control plane.

Data that has to be moved after the downtime is rebalanced once the cluster is up. The rebalancing flag reported by the
control plane is mirrored into `status.rebalancing` of the `StorageCluster`.

```bash title="Reading the rebalancing flag of a started cluster"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status.phase}{" rebalancing="}{.status.rebalancing}{"\n"}'
```

How an operation is tracked and cleaned up is described in [Storage Cluster Actions](cluster-actions.md).
