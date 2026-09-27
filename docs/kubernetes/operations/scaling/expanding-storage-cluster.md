---
title: "Expanding a Storage Cluster"
description: "Add storage nodes to a running simplyblock cluster on Kubernetes with a growth ClusterDeploymentConfig, and follow the integration of every new node."
weight: 10310
---

A storage cluster is expanded while it serves I/O, so no maintenance window is required. Every new storage node is
integrated by the control plane on its own, and the integration is followed by a rebalancing that moves data onto the
new devices. The rebalancing runs at low priority, but it is still work on the data path, so an expansion is best
started while the cluster is not fully utilized.

## How an Expansion Runs

A worker is enrolled through a `ClusterDeploymentConfig` that names the existing cluster in `spec.clusterRef`.
Naming it is what selects the expansion path: every `StorageNode` the document creates carries
`config.expand: true`, which reaches the control plane with the node addition. The cluster keeps the status
`active` and one expansion task is queued for the new node.

That task re-wires the role rotation of the cluster. The secondary logical volume store moves to the direct successor
of the new node, and the tertiary one to the second node in line. Both donors have to be torn down and rebuilt for it,
which is why the cluster reports `in_expansion` while the rotation is rebuilt and returns to `active` afterward. Only
then does the expansion migration start and move data onto the devices of the new node.

One expansion runs per cluster at a time. Several workers may be listed in the same document: they are integrated
one after another, since the addition of the next worker is refused while an expansion is open and retried by the
operator every 20 seconds.

## Preconditions

The role rotation is only safe on a quiescent and fully redundant cluster, so an expansion is refused unless

- the cluster is `active` and every storage node is `online`,
- no data migration, logical volume migration, node restart, or backup task is open anywhere in the cluster, where
  open means anything that has not finished, and
- no deletion is in flight on the two donor nodes.

The conditions are checked twice: cluster-wide when the node is added, and again with the donors of the planned role
moves right before the rotation is executed.

## Discovering the New Workers

A discovery run reports only what is unclaimed. A worker that already carries a `StorageNode`, and a device that
node already names, are not candidates, so a run against the deployed fleet finds exactly the machines and disks
nobody has taken yet.

Setting `spec.discover.clusterRef` makes the run write a growth document against that cluster rather than proposing
a new one:

```yaml title="Discovering the workers to expand onto (discover-expansion.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: OperatorOps
metadata:
  name: discover-expansion
  namespace: simplyblock
spec:
  action: Discover
  discover:
    configName: expansion
    clusterRef: simplyblock-cluster
    workers:
      - new-node-4.example.com
      - new-node-5.example.com
```

```bash title="Running the discovery"
kubectl apply -f discover-expansion.yaml
kubectl get clusterdeploymentconfig expansion -n simplyblock
```

Leaving `workers` out inspects every eligible worker and reports whatever is still unclaimed, which is the usual
way to find out what a fleet has left.

## Approving the Expansion

The document arrives as a `Draft`. Review it as with any other, then approve it:

```yaml title="Example of a growth document (expansion.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ClusterDeploymentConfig
metadata:
  name: expansion
  namespace: simplyblock
spec:
  approved: false
  clusterRef: simplyblock-cluster
  nodeSets:
    - name: expansion
      groups:
        - name: expansion-nodes
          workers:
            - new-node-4.example.com
            - new-node-5.example.com
```

```bash title="Approving the expansion"
kubectl patch clusterdeploymentconfig expansion -n simplyblock \
    --type=merge -p '{"spec": {"approved": true}}'
```

A growth document carries no `spec.cluster`: the cluster already exists and its settings are not restated. It also
adds only the nodes that do not exist yet, so a worker already enrolled is skipped rather than rebuilt.

On a cluster with `enableFailureDomains: true`, every group in the document has to carry a `failureDomain`,
otherwise the addition is rejected. See [Managing Failure Domains](../cluster/failure-domains.md) for the
assignment and the balance rules.

```yaml title="Example of a growth document on a failure-domain cluster"
spec:
  approved: false
  clusterRef: simplyblock-cluster
  nodeSets:
    - name: expansion
      groups:
        - name: rack-c-nodes
          failureDomain: rack-c
          workers:
            - new-node-4.example.com
        - name: rack-d-nodes
          failureDomain: rack-d
          workers:
            - new-node-5.example.com
```

## Configuring a Single Expansion Worker

A worker that needs a configuration of its own goes into its own group. A group carries `mgmtInterface`,
`dataInterfaces`, `devices`, `failureDomain`, `spdkSystemMemory`, `reservedSystemCPU`, and `journalManager`, so
workers whose hardware differs are described by grouping them separately rather than by overriding them
individually.

```yaml title="Example of a group with its own configuration"
spec:
  approved: false
  clusterRef: simplyblock-cluster
  nodeSets:
    - name: expansion
      groups:
        - name: large-memory
          spdkSystemMemory: "4G"
          workers:
            - new-node-4.example.com
          devices:
            nvme:
              - "0000:01:00.0"
              - "0000:02:00.0"
```

The document is the record of this one expansion. It is immutable once approved, so the audit trail of how a
cluster reached its current size is a series of documents rather than a series of revisions to one.

## Following the Expansion

The expansion of the document runs first, and its phase moves `Draft` → `Expanding` → `Expanded`:

```bash title="Watching the document expand"
kubectl get clusterdeploymentconfig expansion -n simplyblock -w
```

The state of the new nodes is then reported on the `StorageNode` resources:

```bash title="Watching the storage nodes of the expansion"
kubectl get storagenodes -n simplyblock -w
```

The cluster reports the rotation and the rebalancing that follow it. The status returns to `active` once the rotation
is rebuilt, and `rebalancing` turns to `false` once the data has been moved:

```bash title="Watching the cluster status and the rebalancing flag"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status.status}{"\t"}{.status.rebalancing}{"\n"}' -w
```

## Finalizing an Expansion of Nodes Added Without the Flag

A node added without the expansion flag follows the older path: the cluster is set to `in_expansion` when the node
is registered, and the expansion is finalized with a cluster operation once all new nodes are online.

```bash title="Finalizing a cluster expansion"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageClusterOps
metadata:
  name: finalize-expansion
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  action: Expand
EOF
```

This path integrates all pending nodes at once, so it needs at least two new nodes, and at least three on a cluster
with dual fault tolerance (FTT 2), to build the failover paths of every one of them. The outcome is reported in the
operation's `status.phase`. The other operations of the kind are described in
[Storage Cluster Actions](../cluster/cluster-actions.md).

## Sequencing and Parallel Additions

`StorageCluster.spec.storageNodes.nodeProvisioningBudget` governs how many workers are provisioned at the same
time, as described in [Parallel Storage Node Addition](parallel-node-addition.md). It does not widen an expansion:
the control plane integrates one new node at a time regardless of the value.
