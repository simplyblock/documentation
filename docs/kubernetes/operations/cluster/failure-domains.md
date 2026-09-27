---
title: "Managing Failure Domains"
description: "Enable failure-domain mode on a simplyblock cluster and assign Kubernetes workers to fault groups so erasure-coding chunks are spread across racks or zones."
weight: 10140
---

Failure-domain mode groups the storage nodes of a cluster into independent fault groups, so that the control plane
spreads erasure-coding chunks and failover paths across them. A group stands for whatever fails together in the
physical layout: a rack, a power unit, or an availability zone. Losing one group then costs at most one chunk per
stripe.

The placement contract, the balance rules, and the interaction with the erasure coding scheme are described in
[Failure Domains](../../../architecture/concepts/failure-domains.md). This page covers how the mode is turned on and how
workers are assigned to groups through the operator resources.

## Enabling Failure Domains

Failure-domain mode is a cluster-level property, set through `spec.enableFailureDomains` on the `StorageCluster`.

```yaml title="Example of a StorageCluster with failure domains enabled (storage-cluster.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageCluster
metadata:
  name: simplyblock-cluster
  namespace: simplyblock
spec:
  fabricType: tcp
  maxSubsystemCount: 75
  vcpuCount: 16
  enableFailureDomains: true
  stripe:
    dataChunks: 2
    parityChunks: 1
```

!!! important
    The field is immutable. Failure-domain mode cannot be turned on for a cluster that is already running, and it
    cannot be turned off again. A cluster that should use failure domains has to be created with the field set.

## Assigning Workers to a Domain

A domain is a label value naming whatever fails together — `rack-a`, `zone-1`, `psu-left` — and every worker of a
failure-domain cluster needs one. Two places carry the assignment.

| Field                                                            | Scope    | Description                                 |
|------------------------------------------------------------------|----------|---------------------------------------------|
| `ClusterDeploymentConfig.spec.nodeSets[].groups[].failureDomain` | Group    | The domain of every worker in the group.    |
| `StorageNode.spec.config.failureDomain`                          | Per node | The domain of one node. Immutable once set. |

The deployment config is the readable form, because a group is already the set of workers that belong together and
giving it a domain says so once for all of them.

```yaml title="Example of a deployment spread across three failure domains"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ClusterDeploymentConfig
metadata:
  name: production
  namespace: simplyblock
spec:
  approved: false
  cluster:
    name: simplyblock-cluster
    maxSubsystemCount: 75
    vcpuCount: 16
    enableFailureDomains: true
    stripe:
      dataChunks: 2
      parityChunks: 1
  nodeSets:
    - name: production
      groups:
        - name: rack-a-nodes
          failureDomain: rack-a
          journalManager:
            count: 4
          workers:
            - worker-1.example.com
            - worker-2.example.com
        - name: rack-b-nodes
          failureDomain: rack-b
          journalManager:
            count: 4
          workers:
            - worker-3.example.com
            - worker-4.example.com
        - name: rack-c-nodes
          failureDomain: rack-c
          journalManager:
            count: 4
          workers:
            - worker-5.example.com
            - worker-6.example.com
```

Workers that share a domain are treated as failing together, so the value has to follow the physical layout. Two
workers in the same rack belong in the same domain, and two workers in different racks belong in different ones.

A worker whose configuration differs from the rest of its rack goes into its own group with the same
`failureDomain`, which is how a domain holds workers that are not otherwise alike.

```yaml title="Example of two groups in one failure domain"
groups:
  - name: rack-a-standard
    failureDomain: rack-a
    workers:
      - worker-1.example.com
  - name: rack-a-large-memory
    failureDomain: rack-a
    spdkSystemMemory: "8G"
    workers:
      - worker-2.example.com
```

The value takes the shape of a Kubernetes label value, which is what it is seeded from where a cluster carries
topology labels at all.

### Multi-Socket Workers

The assignment is per worker, not per storage node. A worker that hosts several storage nodes, because it has more
than one NUMA socket or runs more than one node per socket, contributes all of them to the same domain. That is the
intended behavior, since a host cannot fail in two places at once, and the balance rules require a host to stay
within one domain.

## Journal Copies

A failure-domain cluster needs at least four copies of the high-availability journal, even with a single parity chunk.
The default is three, which would put two copies in one domain on a two-domain cluster, so losing that domain would
break the journal quorum.

The copy count is raised through the journal manager configuration of each group, as above, and reaches the node as
`StorageNode.spec.config.journalManager`.

```yaml title="Example of raising the journal copies for a failure-domain cluster"
groups:
  - name: rack-a-nodes
    failureDomain: rack-a
    journalManager:
      count: 4
    workers:
      - worker-1.example.com
```

## Verifying the Assignment

The effective group of a node is reported back from the control plane in `StorageNode.status.failureDomain`. It is
also a print column, at a lower priority, so it shows with `-o wide`.

```bash title="Listing the storage nodes with their failure domains"
kubectl get storagenodes -n simplyblock -o wide
```

```plain title="Example output of the storage node listing"
NAME                      WORKER                 SOCKET   NODEIDX   FD   UUID                                   STATUS   HEALTH   AGE
simplyblock-node-mejue8   worker-1.example.com   0        0         1    82198a36-fcbb-43e3-949c-0260bf40f0ac   online   true     43h
simplyblock-node-o6x20i   worker-3.example.com   0        0         2    707dd443-5d0e-470f-bdde-92f1238c4b01   online   true     43h
simplyblock-node-v92jx7   worker-5.example.com   0        0         3    114899a6-d708-499e-8051-bc9ca9713cf8   online   true     43h
```

```bash title="Reading the failure domain of every storage node"
kubectl get storagenodes -n simplyblock \
    -o jsonpath='{range .items[*]}{.status.hostname}{"\t"}{.status.failureDomain}{"\n"}{end}'
```

A node whose status reports no failure domain has not been assigned one on the backend. On a failure-domain cluster
that means the node was never added, since the operator refuses to add it.

## A Missing Assignment Blocks the Node

On a cluster with `enableFailureDomains: true`, a storage node without a failure domain is not provisioned. The operator
holds the node-add, emits a `FailureDomainMissing` warning on the `StorageNode`, and retries every 60 seconds. The
event names the worker and the field to set, and provisioning continues on its own once the assignment is added.

```bash title="Checking for nodes blocked on a missing failure domain"
kubectl get events -n simplyblock \
    --field-selector reason=FailureDomainMissing
```

```bash title="Assigning a failure domain to a node that has none"
kubectl patch storagenode simplyblock-node-mejue8 -n simplyblock --type=merge \
    -p '{"spec": {"config": {"failureDomain": "rack-a"}}}'
```

The field is immutable once set: it describes where the node physically is, and chunk placement was computed from
it. A node whose domain was wrong is drained, removed, and added again.

## Adding and Removing Nodes

Once a failure-domain cluster holds data, the control plane admits a topology change only while the domains stay
balanced. The host count per domain may not diverge by more than one, no domain may drop below two hosts, and adding
another storage node on a host that is already a member is always allowed. A change that would violate a rule is
refused before any data moves.

In practice, this means workers are added in whole rounds. On a balanced cluster one worker can be added to any domain,
and the next worker has to go to a different one. The full rules are in
[Failure Domains: Balance Rules](../../../architecture/concepts/failure-domains.md#balance-rules).

Removal is meant to take a worker out of the cluster, either because it has failed for good or because the cluster
is being shrunk. A failed worker that is left in place still counts toward its domain's host total while serving
nothing, and if a second worker in the same domain fails before the first is removed, only one of the two can be
removed at all. See
[When to Remove a Node](../../../architecture/concepts/failure-domains.md#when-to-remove-a-node).

Removing a node also triggers journal-copy replacement on every journal redundancy set that referenced its
journal copy. Failover-path relocation can require a cross-domain target. The journal replacement instead prefers
a candidate from the departed node's own failure domain, which leaves the set's domain distribution as it was. See
[Journal Copy Replacement on Removal](../../../architecture/concepts/failure-domains.md#journal-copy-replacement-on-removal).

For the mechanics of adding the workers themselves, see
[Expanding a Storage Cluster](../scaling/expanding-storage-cluster.md), and for taking one out,
[Removing a Storage Node](../storage-nodes/removing-a-storage-node.md).

!!! note
    Domain membership does not change on a live node. A worker that has to move to a different domain is drained and
    removed, then added again with the new domain.
