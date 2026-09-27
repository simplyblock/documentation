---
title: "Activating a Storage Cluster"
description: "Activate a simplyblock storage cluster on Kubernetes with the Activate action, and learn when the operator activates a cluster on its own."
weight: 10112
---

Activation makes a storage cluster serve I/O for the first time. It is normally automatic: a cluster is activated by
the Simplyblock Operator once every storage node of the cluster is online and healthy, and the number of those nodes
is at least the sum of the data chunks, the parity chunks, and one. See
[Create a Storage Cluster](../../installation/k8s-storage-plane.md#when-does-the-cluster-become-active) for the
conditions in detail.

The `Activate` action exists for the case where that did not happen, for example, because nodes came online after
the automatic check had already passed.

```bash title="Activating a cluster manually"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageClusterOps
metadata:
  name: activate-cluster
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  action: Activate
EOF
```

The action succeeds once the cluster reports the status `active`. How the request is executed, tracked, and cleared is
described in [Storage Cluster Actions](cluster-actions.md).

!!! warning
    A `StorageCluster` deleted while an `Activate` operation is still running can leave the backend cluster behind on
    the control plane, where it then has to be removed by hand. Let the operation reach a terminal phase before
    deleting the resource.
