---
title: "Restarting a Storage Cluster"
description: "Restart an entire simplyblock storage cluster on Kubernetes with the restart action, which sequences a shutdown and a start, and follow its two legs."
weight: 10118
---

A restart sequences a shutdown and a start. Both legs are driven by the same action, and the leg currently running is
held in `status.actionStatus.message` as either `shutdown` or `start`. The action succeeds once the cluster is `active`
again.

```bash title="Restarting the storage cluster"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
    --type=merge -p '{"spec": {"action": "restart"}}'
```

```bash title="Following the leg of a running restart"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status.actionStatus.message}{"\n"}'
```

Every volume of the cluster is offline for the duration of the shutdown leg. To restart the storage nodes one after
another instead, so that the cluster keeps serving I/O, see [Rolling Restart](rolling-restart.md). How the request is
executed, tracked, and cleared is described in [Storage Cluster Actions](cluster-actions.md).
