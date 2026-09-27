---
title: "Restarting a Storage Cluster"
description: "Restart an entire simplyblock storage cluster on Kubernetes with a Restart operation, which sequences a shutdown and a start, and follow its two steps."
weight: 10118
---

A restart sequences a shutdown and a start of the whole storage cluster, since the control plane offers no cluster
restart of its own. Both halves are driven by one `StorageClusterOps`, and the operation succeeds once the cluster is
`active` again.

```yaml title="Example of a cluster restart (restart-cluster.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageClusterOps
metadata:
  name: restart-simplyblock-cluster
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  action: Restart
```

```bash title="Restarting the storage cluster"
kubectl apply -f restart-cluster.yaml
```

The half that is currently running is the step of the operation.

| Step           | Description                                                                            |
|----------------|----------------------------------------------------------------------------------------|
| `ShuttingDown` | The shutdown is requested, and the step holds until the cluster is no longer `active`. |
| `Starting`     | The start is requested, and the step holds until the cluster is `active` again.        |

```bash title="Following the step of a running restart"
kubectl get storageclusterops restart-simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status.step.state}{" "}{.status.message}{"\n"}'
```

Neither step can be aborted, because the cluster is already going down or coming back. The operation cannot be deleted
until it is terminal.

!!! warning
    Every volume of the cluster is offline between the shutdown and the start. To restart the storage nodes one after
    another instead, so that the cluster keeps serving I/O, see [Rolling Restart](rolling-restart.md).

How an operation is tracked and cleaned up is described in [Storage Cluster Actions](cluster-actions.md).
