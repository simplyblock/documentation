---
title: "Activating a Storage Cluster"
description: "Activate a simplyblock storage cluster on Kubernetes with the activate action, and learn when the operator activates a cluster on its own."
source: "https://docs.simplyblock.io/latest/kubernetes/operations/cluster/activating-a-cluster/"
---

# Activating a Storage Cluster

Activation makes a storage cluster serve I/O for the first time. It is normally automatic: a cluster is activated by
the Simplyblock Operator once every storage node declared in its `StorageNodeSet` is online and healthy, and the
number of those nodes is at least the sum of the data chunks, the parity chunks, and one. See
[Create a Storage Cluster](../../installation/k8s-storage-plane.md#when-does-the-cluster-become-active) for the
conditions in detail.

The `activate` action exists for the case where that did not happen, for example, because nodes came online after the
automatic check had already passed.

```bash title="Activating a cluster manually"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
    --type=merge -p '{"spec": {"action": "activate"}}'
```

The action succeeds once the cluster reports the status `active`. How the request is executed, tracked, and cleared is
described in [Storage Cluster Actions](cluster-actions.md).

!!! warning
    A `StorageCluster` that is deleted while `spec.action` is `activate` has its finalizer removed without the backend
    cluster being deleted. The cluster is then left behind on the control plane and has to be removed there. Clear
    `spec.action` before deleting the resource.
