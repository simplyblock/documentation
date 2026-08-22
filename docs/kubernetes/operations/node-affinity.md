---
title: "Configuring Node Affinity"
description: "Enable node affinity on a simplyblock cluster so a volume's data stays local to the storage node that owns it, and combine it with per-PVC placement."
weight: 10620
---

Node affinity, also called data locality, keeps the data of a logical volume on the storage node that owns the volume,
rather than spreading it evenly across the cluster. Reads are then served from the local node, which removes a network
hop from the data path. It is meant for latency-sensitive workloads in hyper-converged and hybrid deployments, where
the storage node and the workload consuming it run on the same worker.

Fault tolerance is not traded away for it. The parity chunks are still distributed across the other nodes of the
cluster, so a node failure still fails over transparently, and a volume whose local capacity runs out still spills over
onto other nodes.

!!! info
    Node affinity only has an effect in a hyper-converged or hybrid deployment. In a disaggregated deployment the
    storage nodes are separate from the workloads, so there is no locality to preserve.

## Enabling Node Affinity

Node affinity is a cluster-level property, set through `spec.enableNodeAffinity` on the `StorageCluster`.

```yaml title="Example of a StorageCluster with node affinity enabled (storage-cluster.yaml)"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageCluster
metadata:
  name: simplyblock-cluster
  namespace: simplyblock
spec:
  fabricType: tcp
  maxSubsystemCount: 75
  vcpuCount: 16
  enableNodeAffinity: true
  stripe:
    dataChunks: 2
    parityChunks: 1
```

!!! important
    The field is only read when the cluster is created. Setting it on a cluster that already exists has no effect, and
    a cluster that should use node affinity has to be created with it.

## Placing a Volume on a Storage Node

Node affinity on its own changes how the data of a volume is laid out. Which storage node a volume belongs to is a
separate decision, made when the volume is provisioned, and it is what makes the locality useful.

On Kubernetes that decision is driven by PVC annotations:

- `simplyblock.io/pod-affinity` places a new volume on the storage node that is co-located with the pod consuming it,
  which is the combination a hyper-converged deployment usually wants.
- `simplyblock.io/selected-storage-node` pins a volume to a named storage node.

Both are described in [Automatic Volume Placement](../usage/volume-placement.md). They work whether or not node
affinity is enabled for the cluster, and the difference is what the backend then does with the data. Without node
affinity the volume is owned by that node but its data is spread across the cluster. With node affinity the data
follows the owner.

```yaml title="Example of a PVC co-located with its consuming pod"
kind: PersistentVolumeClaim
apiVersion: v1
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
  storageClassName: simplyblock-csi-sc
```

## Keeping Locality After a Volume Moves

A volume that moves to another storage node leaves its data behind, so the locality is broken until the cluster
re-aligns its internal data structures to the new placement. That realignment restores both the fault-tolerance and
the node-affinity guarantees, and the operator triggers it automatically after volumes have moved.

It applies to every move, whether the volume was migrated manually, relocated by auto-rebalancing, or evacuated from a
node being drained. It is enabled by default and configured under `volumeMigrationSettings.dataRealignment`, described
in [Volume Migration: Data Realignment](volume-migration.md#data-realignment).

On a cluster with node affinity this is not a detail to leave unattended. A cluster that moves volumes frequently and
has realignment turned off keeps losing locality with every move, and never regains it.

```bash title="Checking that data realignment is enabled"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{.spec.volumeMigrationSettings.dataRealignment}' | jq .
```

```bash title="Checking whether a realignment is outstanding"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{"moves="}{.status.volumeMoveGeneration}{" realigned="}{.status.realignedGeneration}{"\n"}'
```

A `volumeMoveGeneration` above `realignedGeneration` means volumes have moved since the last realignment, so one is
still pending.
