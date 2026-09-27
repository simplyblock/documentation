---
title: "Managing Failure Domains"
description: "Enable failure-domain mode on a simplyblock cluster and label Kubernetes workers with fault groups, so erasure-coding chunks are spread across racks or zones."
weight: 10140
---

Failure-domain mode groups the storage nodes of a cluster into independent fault groups, so that the control plane
spreads erasure-coding chunks and failover paths across them. A group stands for whatever fails together in the
physical layout: a rack, a power feed, or an availability zone. Losing one group then costs at most one chunk per
stripe.

The placement contract, the balance rules, and the interaction with the erasure coding scheme are described in
[Failure Domains](../../../architecture/concepts/failure-domains.md). This page covers how the mode is turned on and how
storage nodes are assigned to groups through the operator resources.

## Enabling Failure Domains

Failure-domain mode is a cluster-level property. In a `ClusterDeploymentConfig`, it is set with
`spec.cluster.enableFailureDomains`, which the operator copies into `StorageCluster.spec.enableFailureDomains` when it
creates the cluster.

```yaml title="Example of a deployment document with failure domains (cluster-config.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ClusterDeploymentConfig
metadata:
  name: simplyblock-deployment
  namespace: simplyblock
spec:
  approved: false
  cluster:
    name: simplyblock-cluster
    maxSubsystemCount: 50
    vcpuCount: 8
    stripe:
      dataChunks: 2
      parityChunks: 1
    enableFailureDomains: true
  nodeSets:
    - name: rack-a
      groups:
        - name: default
          failureDomain: rack-a
          workers: [worker-1.example.com, worker-2.example.com]
          devices:
            nvme: ["0000:01:00.0", "0000:02:00.0"]
          journalManager:
            count: 4
    - name: rack-b
      groups:
        - name: default
          failureDomain: rack-b
          workers: [worker-3.example.com, worker-4.example.com]
          devices:
            nvme: ["0000:01:00.0", "0000:02:00.0"]
          journalManager:
            count: 4
    - name: rack-c
      groups:
        - name: default
          failureDomain: rack-c
          workers: [worker-5.example.com, worker-6.example.com]
          devices:
            nvme: ["0000:01:00.0", "0000:02:00.0"]
          journalManager:
            count: 4
```

!!! warning
    `enableFailureDomains` is immutable. Failure-domain mode cannot be turned on for a cluster that is already
    running, and it cannot be turned off again. A cluster that should use failure domains has to be created with the
    field set.

## Assigning Storage Nodes to a Domain

A domain is a label, for example, `rack-a` or `zone-1`, with the shape of a Kubernetes label value: at most 63
characters, starting and ending with an alphanumeric character. Every storage node of a failure-domain cluster needs
one.

| Field                                                         | Scope | Description                                                                                |
|---------------------------------------------------------------|-------|--------------------------------------------------------------------------------------------|
| `ClusterDeploymentConfig` `nodeSets[].groups[].failureDomain` | Group | The domain of every worker in the group. Copied onto each `StorageNode` the group creates. |
| `StorageNode.spec.config.failureDomain`                       | Node  | The domain of one storage node. Immutable once set.                                        |

A discovery run seeds `failureDomain` of a draft from the `topology.kubernetes.io/zone` label of the workers, and it
leaves it empty where the workers carry no topology label.

Workers that share a domain are treated as failing together, so the label has to follow the physical layout. Two
workers in the same rack belong in the same domain, and two workers in different racks belong in different ones.

### Multi-Socket Workers

The group assigns the domain per worker. A worker that hosts several storage nodes, because it has more than one NUMA
socket or runs more than one node per socket, contributes all of them to the same domain. That is the intended
behavior, since a host cannot fail in two places at once, and the balance rules require a host to stay within one
domain.

## Journal Copies

A failure-domain cluster needs at least four copies of the high-availability journal, even with a single parity chunk.
The default is three, which would put two copies in one domain on a two-domain layout, so losing that domain would break
the journal quorum. The copy count is raised with `journalManager.count` of each group, as in the example above.

## A Missing Assignment Blocks the Node

On a cluster with `enableFailureDomains: true`, a storage node without a domain is not provisioned. The node holds in
the `CheckingConfig` step of its provisioning, and a `FailureDomainMissing` warning on the `StorageNode` names the field
to set. Provisioning continues on its own once the domain is added.

```bash title="Checking for nodes blocked on a missing failure domain"
kubectl get events -n simplyblock \
    --field-selector reason=FailureDomainMissing
```

`spec.config.failureDomain` can be set on a node that has none, and it is frozen from then on.

```bash title="Assigning a failure domain to a blocked storage node"
kubectl patch storagenode simplyblock-cluster-worker-1-0 -n simplyblock --type=merge \
    -p '{"spec": {"config": {"failureDomain": "rack-a"}}}'
```

## Activation

The activation of a failure-domain cluster waits until the domains are balanced. The operator mirrors the admission
rules of the control plane and holds the `Activate` operation, with a `FailureDomainNotReady` event, while

- no storage node has reported a domain yet,
- the cluster has fewer distinct domains than the number of parity chunks plus two (a layout of two domains is not
  supported at any parity level), or
- the domains do not all hold the same number of hosts.

See [Activating a Storage Cluster](activating-a-cluster.md) for the activation itself.

## Verifying the Assignment

The effective domain of a node is reported back from the control plane in `StorageNode.status.failureDomain`. It is
also a print column at a lower priority, so it shows with `-o wide`.

```bash title="Listing the storage nodes with their failure domains"
kubectl get storagenodes -n simplyblock -o wide
```

A node whose status reports no failure domain has not been registered with one on the backend. On a failure-domain
cluster, that means the node has not been added yet.

## Adding and Removing Nodes

Once a failure-domain cluster holds data, the control plane admits a topology change only while the domains stay
balanced. The host count per domain may not diverge by more than one, no domain may drop below two hosts, and adding
another storage node on a host that is already a member is always allowed. A change that would violate a rule is
refused before any data moves.

In practice, this means workers are added in whole rounds. On a balanced cluster, one worker can be added to any domain,
and the next worker has to go to a different one. The full rules are in
[Failure Domains: Balance Rules](../../../architecture/concepts/failure-domains.md#balance-rules).

Removal is meant to take a worker out of the cluster, either because it has failed for good or because the cluster is
being shrunk. A failed worker that is left in place still counts toward its domain's host total while serving nothing.
See [When to Remove a Node](../../../architecture/concepts/failure-domains.md#when-to-remove-a-node).

Removing a node also triggers journal-copy replacement on every journal redundancy set that referenced its journal
copy. The replacement prefers a candidate from the departed node's own failure domain, which leaves the set's domain
distribution as it was. See
[Journal Copy Replacement on Removal](../../../architecture/concepts/failure-domains.md#journal-copy-replacement-on-removal).

For the mechanics of adding workers, see [Expanding a Storage Cluster](../scaling/expanding-storage-cluster.md), and for
taking one out, [Removing a Storage Node](../storage-nodes/removing-a-storage-node.md).

!!! note
    Domain membership does not change on a live node, since `spec.config.failureDomain` is immutable once set. A
    worker that has to move to a different domain is drained and removed, then added again with the new domain.
