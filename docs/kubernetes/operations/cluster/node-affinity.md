---
title: "Configuring Node Affinity"
description: "Enable node affinity on a simplyblock cluster so a volume's data stays local to the storage node that owns it, and keep it local with data realignment."
weight: 10150
---

Node affinity, also called data locality, keeps the data of a logical volume on the storage node that owns the volume,
rather than spreading it evenly across the cluster. Reads are then served from the local node, which removes a network
hop from the data path. It is meant for latency-sensitive workloads in hyper-converged and hybrid deployments, where
the storage node and the workload consuming it run on the same worker.

Fault tolerance is not traded away for it. The parity chunks are still distributed across the other nodes of the
cluster, so a node failure still fails over transparently, and a volume whose local capacity runs out still spills over
onto other nodes.

!!! info
    Node affinity only has an effect in a hyper-converged or hybrid deployment. In a disaggregated deployment, the
    storage nodes are separate from the workloads, so there is no locality to preserve.

## Enabling Node Affinity

Node affinity is a cluster-level property, set with `spec.enableNodeAffinity` on the `StorageCluster`. It is sent to
the control plane when the cluster is created.

```yaml title="Example of a StorageCluster with node affinity enabled (storage-cluster.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageCluster
metadata:
  name: simplyblock-cluster
  namespace: simplyblock
spec:
  maxSubsystemCount: 50
  vcpuCount: 8
  fabricType: tcp
  enableNodeAffinity: true
  stripe:
    dataChunks: 2
    parityChunks: 1
```

!!! warning
    The field is read only when the cluster is created, and it is immutable once set. A cluster that should use node
    affinity has to be created with it. The cluster template of a `ClusterDeploymentConfig` does not carry the field,
    so such a cluster is created from a `StorageCluster` resource that states it.

## Placing a Volume on a Storage Node

Node affinity on its own changes how the data of a volume is laid out. Which storage node a volume belongs to is a
separate decision, made when the volume is provisioned, and it is what makes the locality useful. On Kubernetes, that
decision is driven by PVC annotations:

- **`storage.simplyblock.io/selected-storage-node`:** Pins a volume to the storage node with the given UUID.
- **`simplyblock.io/pod-affinity`:** Set to `"true"`, it places a new volume on the storage node that is co-located
  with the pod consuming it, which is the combination a hyper-converged deployment usually wants. The CSI driver reads
  this annotation under its `simplyblock.io/` spelling.

Both are described in [Automatic Volume Placement](../../usage/volume-placement.md). They work whether or not node
affinity is enabled for the cluster, and the difference is what the backend then does with the data. Without node
affinity, the volume is owned by that node, but its data is spread across the cluster. With node affinity, the data
follows the owner.

```yaml title="Example of a PVC co-located with its consuming pod"
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
  annotations:
    simplyblock.io/pod-affinity: "true"
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: simplyblock-simplyblock-simplyblock-cluster
```

The StorageClass must use the `WaitForFirstConsumer` binding mode for the co-location to take effect, which the class
the operator creates for the default pool of a cluster does. Its name is `simplyblock-<namespace>-<cluster>`.

## Keeping Locality After a Volume Moves

A volume that moves to another storage node leaves its data behind, so the locality is broken until the cluster
realigns its internal data structures to the new placement. That realignment restores both the fault-tolerance and
the node-affinity guarantees, and the operator requests it after volumes have moved. It applies to every move, whether
the volume was migrated manually, relocated by auto-rebalancing, or evacuated from a node being removed.

Realignment runs only when `spec.enableDataRealignment` is `true` on the `StorageCluster`. Its pacing is tuned under
`spec.volumeMigrationSettings.dataRealignment`.

| Field                                                   | Default | Description                                                         |
|---------------------------------------------------------|---------|---------------------------------------------------------------------|
| `spec.enableDataRealignment`                            | Off     | Turns the post-migration realignment on.                            |
| `spec.volumeMigrationSettings.dataRealignment.interval` | `10m`   | The minimum spacing between two realignment requests.               |
| `spec.volumeMigrationSettings.dataRealignment.minMoves` | `1`     | How many volume moves accumulate before a realignment is requested. |

```yaml title="Example of enabling data realignment"
spec:
  enableDataRealignment: true
  volumeMigrationSettings:
    dataRealignment:
      interval: 10m
      minMoves: 1
```

A realignment blocks volume migrations for as long as the control plane needs, so raising `minMoves` trades how
promptly the data is realigned for migration throughput. See [Volume Migration](../volumes/volume-migration.md) for the
migrations themselves.

On a cluster with node affinity, realignment is not a detail to leave unattended. A cluster that moves volumes
frequently and has realignment turned off keeps losing locality with every move, and never regains it.

```bash title="Checking whether a realignment is outstanding"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{"moves="}{.status.volumeMoveGeneration}{" realigned="}{.status.realignedGeneration}{" last="}{.status.lastDataRealignmentAt}{"\n"}'
```

A `volumeMoveGeneration` above `realignedGeneration` means volumes have moved since the last realignment, so one is
still pending.
