---
title: "Expanding a Storage Cluster"
description: "Add storage nodes to a running simplyblock cluster on Kubernetes with an expansion StorageNodeSet, and follow the integration of every new node."
source: "https://docs.simplyblock.io/latest/kubernetes/operations/scaling/expanding-storage-cluster/"
---

# Expanding a Storage Cluster

A storage cluster is expanded while it serves I/O, so no maintenance window is required. Every new storage node is
integrated by the control plane on its own, and the integration is followed by a rebalancing that moves data onto the
new devices. The rebalancing runs at low priority, but it is still work on the data path, so an expansion is best
started while the cluster is not fully utilized.

## How an Expansion Runs

A worker is enrolled through a `StorageNodeSet` whose `spec.expand` is set to `true`. The flag reaches the control
plane with the node addition and selects the expansion path, in which the cluster keeps the status `active` and one
expansion task is queued for the new node.

That task re-wires the role rotation of the cluster. The secondary logical volume store moves to the direct successor
of the new node, and the tertiary one to the second node in line. Both donors have to be torn down and rebuilt for it,
which is why the cluster reports `in_expansion` while the rotation is rebuilt and returns to `active` afterward. Only
then does the expansion migration start and move data onto the devices of the new node.

One expansion runs per cluster at a time. Several workers may be listed in the same `StorageNodeSet`: they are
integrated one after another, since the addition of the next worker is refused while an expansion is open and retried
by the operator every 20 seconds.

## Preconditions

The role rotation is only safe on a quiescent and fully redundant cluster, so an expansion is refused unless

- the cluster is `active` and every storage node is `online`,
- no data migration, logical volume migration, node restart, or backup task is open anywhere in the cluster, where
  open means anything that has not finished, and
- no deletion is in flight on the two donor nodes.

The conditions are checked twice: cluster-wide when the node is added, and again with the donors of the planned role
moves right before the rotation is executed.

## Enrolling the Expansion Workers

The expansion workers are declared in their own `StorageNodeSet`, which keeps them separate from the resource that
carries the original nodes and leaves that resource untouched.

```yaml title="Example of a StorageNodeSet that expands a cluster (expansion-nodeset.yaml)"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeSet
metadata:
  name: simplyblock-node-expansion
  namespace: simplyblock
spec:
  clusterName: simplyblock-cluster
  expand: true
  workerNodes:
    - new-node-4.example.com
    - new-node-5.example.com
```

```bash title="Enrolling the expansion workers"
kubectl apply -f expansion-nodeset.yaml
```

One `StorageNode` resource per worker is created by the operator, the storage node DaemonSet is rolled out on that
worker, and the node is registered with the control plane. Every configuration field of the original `StorageNodeSet`
that the new workers do not share has to be repeated in the expansion resource, since the two resources are
independent.

On a cluster with `enableFailureDomains: true`, the expansion resource also has to assign every new worker to a
failure domain, otherwise the addition is rejected. See
[Managing Failure Domains](../cluster/failure-domains.md) for the assignment and the balance rules.

```yaml title="Example of an expansion StorageNodeSet on a failure-domain cluster"
spec:
  clusterName: simplyblock-cluster
  expand: true
  workerNodes:
    - new-node-4.example.com
    - new-node-5.example.com
  nodeFailureDomains:
    new-node-4.example.com: 0
    new-node-5.example.com: 1
```

## Following the Expansion

The state of the new nodes is reported on the `StorageNode` resources:

```bash title="Watching the storage nodes of the expansion"
kubectl get storagenodes -n simplyblock -w
```

The cluster reports the rotation and the rebalancing that follow it. The status returns to `active` once the rotation
is rebuilt, and `rebalancing` turns to `false` once the data has been moved:

```bash title="Watching the cluster status and the rebalancing flag"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status.status}{"\t"}{.status.rebalancing}{"\n"}' -w
```

## Configuring a Single Expansion Worker

A worker that needs a configuration of its own is given an entry under `spec.nodeConfigs`, keyed by its name. The
entry overrides the fleet defaults of the `StorageNodeSet` for that worker only, and it accepts `expand`,
`failureDomain`, `spdkSystemMemory`, the PCI filters, and the device names.

```yaml title="Example of a per-worker configuration in an expansion StorageNodeSet"
spec:
  clusterName: simplyblock-cluster
  expand: true
  workerNodes:
    - new-node-4.example.com
  nodeConfigs:
    new-node-4.example.com:
      spdkSystemMemory: "4G"
      failureDomain: 0
```

The `StorageNodeSet` is the single source of truth for this configuration. The entries are propagated into
`StorageNode.spec.overrides` on every reconcile, so an override edited on a `StorageNode` directly is overwritten
again. A `StorageNode` resource created by hand is kept, since the operator only deletes the resources it owns, but it
is needed only for a worker that is deliberately absent from `spec.workerNodes`.

## Finalizing an Expansion of Nodes Added Without the Flag

A node added without `expand` follows the older path: the cluster is set to `in_expansion` when the node is
registered, and the expansion is finalized with a cluster action once all new nodes are online.

```bash title="Finalizing a cluster expansion"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
    --type=merge -p '{"spec": {"action": "expand"}}'
```

This path integrates all pending nodes at once, so it needs at least two new nodes, and at least three on a cluster
with dual fault tolerance (FTT 2), to build the failover paths of every one of them. The outcome is reported in
`status.actionStatus`, which holds the state `running`, `success`, or `failed` together with a message. The other
actions of the resource are described in [Storage Cluster Actions](../cluster/cluster-actions.md).

## Sequencing and Parallel Additions

`maxParallelNodeAdds` governs how many workers of a `StorageNodeSet` are provisioned at the same time, as described in
[Parallel Storage Node Addition](parallel-node-addition.md). It does not widen an expansion: the control plane
integrates one new node at a time regardless of the value.
