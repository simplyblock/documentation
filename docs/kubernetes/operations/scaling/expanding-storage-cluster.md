---
title: "Expanding a Storage Cluster"
description: "Add storage nodes to a running simplyblock cluster on Kubernetes with a growth ClusterDeploymentConfig, and follow the integration of every new node."
weight: 10310
---

A storage cluster is expanded while it serves I/O, so no maintenance window is required. New workers are described in
a growth `ClusterDeploymentConfig`, a deployment document that names the existing cluster in `spec.clusterRef` instead
of describing a new one. Once the document is approved, the Simplyblock Operator creates one `StorageNode` per worker
and slot, and every new node is integrated by the control plane on its own. The integration is followed by a
rebalancing that moves data onto the new devices. The rebalancing runs at low priority, but it is still work on the
data path, so an expansion is best started while the cluster is not fully utilized.

## How an Expansion Runs

Every storage node a growth document creates carries `spec.config.expand: true`. The flag reaches the control plane
with the node addition and selects the expansion path, in which the cluster keeps the status `active` and one
expansion task is queued for the new node.

That task re-wires the role rotation of the cluster. The secondary logical volume store moves to the direct successor
of the new node, and the tertiary one to the second node in line. Both donors have to be torn down and rebuilt for it,
which is why the cluster reports `in_expansion`, and the `StorageCluster` the phase `Provisioning`, while the rotation
is rebuilt. It returns to `active` afterward. Only then does the expansion migration start and move data onto the
devices of the new node.

One expansion runs per cluster at a time. Several workers may be listed in the same document: they are integrated one
after another, since the control plane refuses the addition of the next worker while an expansion is open, and the
operator retries it.

## Preconditions

The role rotation is only safe on a quiescent and fully redundant cluster, so the control plane refuses an expansion
unless

- the cluster is `active` and every storage node is `online`,
- no data migration, logical volume migration, node restart, or backup task is open anywhere in the cluster, where
  open means anything that has not finished, and
- no deletion is in flight on the two donor nodes.

The conditions are checked twice: cluster-wide when the node is added, and again with the donors of the planned role
moves right before the rotation is executed.

## Drafting the Growth Document

A growth document is either drafted by a discovery run or written by hand.

### With a Discovery Run

An `OperatorOps` with the action `Discover` probes the workers and writes a draft document. With
`spec.discover.clusterRef`, the draft grows the named cluster instead of describing a new one. A run that names no
workers inspects every schedulable worker that does not already run a storage node.

```yaml title="Example of a discovery run for a growth draft (discover-growth.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: OperatorOps
metadata:
  name: discover-rack-c
  namespace: simplyblock
spec:
  action: Discover
  discover:
    configName: grow-rack-c
    clusterRef: simplyblock-cluster
    workers:
      - worker-7.example.com
      - worker-8.example.com
```

```bash title="Running the discovery and finding the draft"
kubectl apply -f discover-growth.yaml
kubectl get operatorops discover-rack-c -n simplyblock -w
kubectl get operatorops discover-rack-c -n simplyblock -o jsonpath='{.status.configRef}{"\n"}'
```

The run walks the steps `Inspecting`, `Probing`, and `Writing`, and it names the document it wrote in
`status.configRef`. Without `configName`, the draft is named after the run. The device filters of a discovery run are
described in [Create a Storage Cluster](../../installation/k8s-storage-plane.md).

### By Hand

```yaml title="Example of a growth document (grow-rack-c.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ClusterDeploymentConfig
metadata:
  name: grow-rack-c
  namespace: simplyblock
spec:
  approved: false
  clusterRef: simplyblock-cluster
  nodeSets:
    - name: rack-c
      groups:
        - name: default
          workers:
            - worker-7.example.com
            - worker-8.example.com
          devices:
            nvme: ["0000:01:00.0", "0000:02:00.0"]
```

A growth document carries no `spec.cluster` block. The cluster-wide settings, such as the sizing, the erasure coding
scheme, and the storage-node workload, are those of the existing `StorageCluster`. Every group of the document uses the
same device class as the cluster.

On a cluster with `enableFailureDomains: true`, every group also sets `failureDomain`, otherwise the new nodes are held
with a `FailureDomainMissing` event. See [Managing Failure Domains](../cluster/failure-domains.md) for the assignment
and the balance rules.

## Approving the Expansion

A draft is inert until it is approved. The validation findings of the document, for example, a device that was not
found on a worker, are reported in `status.message`, and they are reviewed before the approval.

```bash title="Reviewing the draft"
kubectl get clusterdeploymentconfig grow-rack-c -n simplyblock -o yaml
```

```bash title="Approving the expansion"
kubectl patch clusterdeploymentconfig grow-rack-c -n simplyblock \
    --type=merge -p '{"spec": {"approved": true}}'
```

The approving edit is validated against the live cluster, and the document is immutable once it is approved. The
approval cannot be withdrawn.

The document then walks the steps below and reports the phase `Expanding`, then `Expanded`.

| Step              | Description                                                                                                           |
|-------------------|-----------------------------------------------------------------------------------------------------------------------|
| `Validating`      | The document is checked against the cluster and the workers.                                                          |
| `CreatingCluster` | Nothing is created for a growth document. The existing cluster is recorded in `status.clusterRef`.                    |
| `AwaitingCluster` | The existing cluster is confirmed.                                                                                    |
| `CreatingNodes`   | One `StorageNode` per worker and slot is created, with `spec.config.expand: true`, and recorded in `status.nodeRefs`. |
| `Activating`      | The step waits until every node the document created is `Online`.                                                     |

## Is an Expand Operation Needed?

No, not for nodes added by a growth document. The operator does not raise an `Expand` operation after a growth
document, and none is needed: the nodes carry the expansion flag, so the control plane integrates each of them on its
own. In the `Activating` step, the document raises an `Activate` operation named `<cluster>-activate`, or reuses the
one of the initial deployment if it still exists. An activation of a cluster that is already `active` succeeds without
a call to the control plane.

A `StorageClusterOps` with the action `Expand` is needed only for nodes that were added without the flag, for example,
a hand-written `StorageNode` without `spec.config.expand`. Such a node follows the older path: the cluster is set to
`in_expansion` when the node is registered, and the expansion is finalized with the operation once all new nodes are
online.

```yaml title="Example of finalizing an expansion of nodes added without the flag"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageClusterOps
metadata:
  name: expand-simplyblock-cluster
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  action: Expand
```

This path integrates all pending nodes at once, so it needs at least two new nodes, and at least three on a cluster
with dual fault tolerance (FTT 2), to build the failover paths of every one of them. The operation runs the steps
`Requesting` and `Awaiting`, and it succeeds once the cluster is `active`. The other actions are described in
[Storage Cluster Actions](../cluster/cluster-actions.md).

## Following the Expansion

```bash title="Watching the document"
kubectl get clusterdeploymentconfig grow-rack-c -n simplyblock -w
```

```bash title="Watching the new storage nodes"
kubectl get storagenodes -n simplyblock -l storage.simplyblock.io/cluster=simplyblock-cluster -w
```

A new node walks its own provisioning steps, `CheckingHost`, `CheckingConfig`, `AwaitingSlot`, `Posting`, and
`Resolving`, before it reaches the phase `Online`. How many workers are added at the same time is described in
[Parallel Storage Node Addition](parallel-node-addition.md).

The cluster reports the rotation and the rebalancing that follow it. The status returns to `active` once the rotation
is rebuilt, and `rebalancing` turns to `false` once the data has been moved.

```bash title="Watching the cluster status and the rebalancing flag"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status.phase}{"\t"}{.status.status}{"\t"}{.status.rebalancing}{"\n"}' -w
```

Once the expansion is complete, the growth document can be deleted. The storage nodes it created belong to the
`StorageCluster` and are kept.
