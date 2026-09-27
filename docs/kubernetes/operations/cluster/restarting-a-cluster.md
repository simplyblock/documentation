---
title: "Restarting a Storage Cluster"
description: "Restart an entire simplyblock storage cluster on Kubernetes with the Restart action, which sequences a shutdown and a start, and follow its two legs."
weight: 10118
---

A restart sequences a shutdown and a start. Both legs are driven by the same operation, and the leg currently
running is the operation's step: `ShuttingDown`, then `Starting`. The operation succeeds once the cluster is
`active` again.

```bash title="Restarting the storage cluster"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageClusterOps
metadata:
  name: restart-cluster
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  action: Restart
EOF
```

```bash title="Following the leg of a running restart"
kubectl get storageclusterops restart-cluster -n simplyblock \
    -o jsonpath='{.status.step.state}{"\n"}'
```

Every volume of the cluster is offline for the duration of the shutdown leg. To restart the storage nodes one after
another instead, so that the cluster keeps serving I/O, see [Rolling Restart](rolling-restart.md). How the request is
executed, tracked, and cleared is described in [Storage Cluster Actions](cluster-actions.md).
