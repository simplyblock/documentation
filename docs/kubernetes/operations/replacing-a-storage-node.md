---
title: "Replacing a Storage Node"
description: "Replace the host under a simplyblock storage node, or retire a node and add a replacement, without making the logical volumes it owns inaccessible."
weight: 10750
---

A storage cluster is designed to stay up, so replacing a storage node is an online operation. Which operation it is
depends on what is being replaced. Moving a node onto different hardware keeps the node, while retiring a node and
putting a new one in its place does not.

!!! danger
    A storage node must never be removed and re-added to replace it. Removing a node without draining it first makes
    the logical volumes it owns inaccessible. The two procedures below both avoid that, and neither of them deletes a
    node that still holds volumes.

## Choosing the Procedure

| Situation                                                              | Procedure                                                                 |
|------------------------------------------------------------------------|---------------------------------------------------------------------------|
| The host has to be swapped, and the node should keep its data.         | [Relocate the node](#relocating-the-node)                                 |
| The node is being retired, and its capacity is replaced by a new node. | [Retire and replace](#retiring-and-replacing)                             |
| The worker is only down for maintenance and comes back.                | Neither. See [Coordinated Worker Node Drain](node-drain-coordination.md). |

Relocating is the cheaper of the two by a wide margin. The node keeps its backend identity, its devices, and its
logical volume assignments, so no volume data is copied between nodes. Retiring moves every volume off the node first,
which is a data movement across the cluster.

## Relocating the Node

The `migrate` action moves a storage node onto a different Kubernetes worker. The node keeps its UUID and its volumes,
and the cluster rebalances afterward.

This is the procedure for a host that is being replaced, decommissioned, or taken out of the storage plane while its
storage node lives on.

1. Bring the replacement worker into the cluster and confirm it is `Ready`. The devices it offers have to match what
   the node expects, either at the same PCIe addresses as on the old host or declared through `spec.newSsdPcie`.
2. Create a `StorageNodeOps` resource with `action: migrate` and the new worker as `targetWorkerNode`.
3. Follow the operation to `Succeeded`.

```bash title="Relocating a storage node onto a replacement worker"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeOps
metadata:
  name: replace-worker-1
  namespace: simplyblock
spec:
  storageNodeRef: simplyblock-node-mejue8
  action: migrate
  targetWorkerNode: worker-9.example.com
EOF
```

The operator labels the target into the storage plane, waits for its storage-node pod, restarts the node against the
new host, promotes it, and re-points the Kubernetes topology onto the new worker. The details of each phase, and what
to check when one of them stalls, are in [Migrating a Storage Node](migrating-a-storage-node.md).

## Retiring and Replacing

When the node itself is being retired, its volumes are evacuated first and the node is then removed. The replacement
capacity is added as a new storage node.

The order matters. Adding the replacement first keeps the cluster's capacity and redundancy intact throughout, which
is why it is the recommended sequence.

1. **Add the replacement node.** Create a `StorageNodeSet` for the new worker with `spec.expand: true`, or add the
   worker to an existing set, as described in
   [Expanding a Storage Cluster](scaling/expanding-storage-cluster.md).
2. **Finalize the expansion** with the `expand` action once the new node is online, see
   [Storage Cluster Actions](cluster-actions.md#expand).
3. **Drain and remove the old node** with a `StorageNodeOps` resource carrying `action: remove`. Its volumes are
   migrated onto the remaining nodes, including the one just added, before the node leaves the cluster. See
   [Removing a Storage Node](removing-a-storage-node.md).
4. **Verify** that the old node is gone and every volume is accounted for.

```bash title="Removing the retired node once the replacement is online"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeOps
metadata:
  name: retire-worker-1
  namespace: simplyblock
spec:
  storageNodeRef: simplyblock-node-mejue8
  action: remove
EOF
```

A removal is blocked while any volume on the node is pinned to it, or while any volume has no
`PersistentVolume`. Both are reported as events, and both have to be resolved before the drain proceeds.

## Failure-Domain Clusters

On a cluster with failure domains, a replacement has to keep the domains balanced. The host count per domain may not
diverge by more than one, and no domain may drop below two hosts, so a node is replaced within its own domain and the
replacement carries the same group index as the node it replaces.

Relocating a node is the simpler option here as well, since the node keeps its domain membership. A retired node that
is replaced by a new one needs the group index set explicitly on the new worker, as described in
[Managing Failure Domains](failure-domains.md#assigning-workers-to-a-domain).

## Verifying the Replacement

The cluster is back to its expected shape when every storage node is online and healthy, the node count matches, and
the cluster has finished rebalancing.

```bash title="Checking the storage nodes after a replacement"
kubectl get storagenodes -n simplyblock -o wide
```

```bash title="Checking that the cluster settled"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status.status}{" rebalancing="}{.status.rebalancing}{"\n"}'
```

```bash title="Checking that no volume is left without a home"
kubectl get pv -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,CLAIM:.spec.claimRef.name
```

A `PersistentVolume` that is `Bound` and whose consuming pod is running is served by a storage node. A volume that
lost its paths during the replacement recovers on its own, as described in
[Recovering from Path Loss](path-loss-recovery.md).
