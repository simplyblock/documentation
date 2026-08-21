---
title: "Managing Failure Domains"
description: "Deploy and operate a simplyblock storage cluster with failure domains: cluster creation, node tagging, balance rules, expansion, and node removal."
weight: 20055
---

Failure domains group storage nodes by shared infrastructure (rack, cabinet, power unit, availability zone) so that
simplyblock can spread data, journal copies, and failover paths across independent fault groups. The concept and
the placement guarantees are described in
[Failure Domains](../../architecture/concepts/failure-domains.md).

This page describes how to deploy and operate a failure-domain cluster with the CLI. In Kubernetes environments,
failure domains are assigned declaratively through the Simplyblock Operator
(`enableFailureDomains` on the `StorageCluster` and `failureDomain` per node). See the
[Operator Reference](../../reference/operator/index.md).

## Enabling Failure Domains

Failure-domain support is enabled when the storage cluster is created and is immutable afterward:

```bash title="Creating a cluster with failure-domain support"
{{ cliname }} cluster create --enable-failure-domain <FURTHER_OPTIONS>
```

The same flag exists on `{{ cliname }} cluster add` when attaching an additional cluster to an existing control
plane.

!!! warning
    A cluster cannot be upgraded into failure-domain mode. If `--enable-failure-domain` was not given at creation
    time, the cluster must be redeployed to use failure domains.

## Tagging Storage Nodes

On a failure-domain cluster, every storage node must be added with a failure-domain label naming the rack,
cabinet, or availability zone it sits in. All nodes in the same physical fault group share the same label.

```bash title="Adding storage nodes to two different racks"
{{ cliname }} storage-node add-node <CLUSTER_ID> <SN_CTR_ADDR> <MGT_IF> \
    --failure-domain RACK1 \
    <FURTHER_OPTIONS>

{{ cliname }} storage-node add-node <CLUSTER_ID> <SN_CTR_ADDR> <MGT_IF> \
    --failure-domain RACK2 \
    <FURTHER_OPTIONS>
```

A domain comes into existence with the first node that carries its label, and every later node naming that label
joins it. There is no separate command to declare a domain up front.

The tag is mandatory on failure-domain clusters and must be omitted on clusters without the feature. Both
mismatches are rejected with an explanatory error.

All storage nodes on the same physical host must carry the same failure-domain label. On multi-socket hosts with
two storage nodes, both nodes belong to the host's domain.

### Label Syntax

A label starts with a letter, followed by up to 31 letters, digits, `_`, or `-`. `RACK1`, `AZ2`, `DC-EU-WEST_1`,
and `HOST1` are all valid. Labels are case-insensitive, so `rack1`, `Rack1`, and `RACK1` name the same domain.
They are stored upper-cased. A value that does not match the syntax is rejected before the node is touched.

Labels should match how the datacenter is actually described, so that a node list reads like the floor plan.

!!! note
    Internally, each label maps to a cluster-unique integer id that placement and the data plane key off. An
    all-digits value passed to `--failure-domain` is still read as that internal id rather than as a label, which
    keeps existing scripts and automation working unchanged. New deployments should use labels.

The assigned domains are shown in the node list once at least one node carries a tag:

```bash title="Listing the storage nodes with their failure domains"
{{ cliname }} storage-node list
```

The **Failure Domain** column shows the label. The id is shown instead for a cluster that has not been through
[label initialization](#labels-on-existing-clusters), and for a domain created by passing an internal id directly.

## Labels on Existing Clusters

Clusters deployed before labels existed identify their domains by internal id only. The label registry is
initialized by the regular cluster update:

```bash title="Initializing the labels of an existing cluster"
{{ cliname }} cluster update <CLUSTER_ID>
```

Every domain in service is given a derived name (`FD0`, `FD1`, and so on), and every physical label becomes
`HOST1`, `HOST2`, and so on. These names are placeholders. They make the existing topology addressable by name
without guessing at intent, so a domain the datacenter calls `RACK7` should be renamed afterward.

Initialization is idempotent and safe to repeat. An id that already carries a label is left untouched, so a rename
survives later updates. Where the derived name is already owned by a different id (a domain named `FD3` by hand,
for example), that id is left unnamed and a warning is logged rather than anything being renamed.

!!! note
    Only the names of the existing domains are initialized. The failure-domain feature itself is not enabled on a
    cluster created without `--enable-failure-domain`. That still requires a redeployment.

## Activation Requirements

Activating a freshly assembled failure-domain cluster enforces the following rules:

| Rule                                          | Enforcement                                                                         |
|-----------------------------------------------|-------------------------------------------------------------------------------------|
| Every node carries a failure-domain label     | Hard: activation fails                                                              |
| A host does not span two domains              | Hard: activation fails                                                              |
| At least two distinct domains exist           | Hard: activation fails                                                              |
| All domains hold an equal number of hosts     | Hard: activation fails                                                              |
| At least `parity chunks + 1` distinct domains | Recommendation: a warning is logged, activation proceeds with best-effort placement |

During activation, simplyblock computes the interleaved host rotation across the domains and assigns all secondary
and tertiary failover paths from it. Re-activation of an existing cluster (for example, during disaster recovery)
deliberately skips these gates: recovery always takes precedence over topology policy.

## Journal Copies

Failure-domain clusters require at least four copies of the high-availability journal, even with a single parity
chunk. The default of `--ha-jm-count` is 3 for single-parity clusters, so it must be raised explicitly:

```bash title="Adding a node with four journal copies"
{{ cliname }} storage-node add-node <CLUSTER_ID> <SN_CTR_ADDR> <MGT_IF> \
    --failure-domain RACK1 \
    --ha-jm-count 4 \
    <FURTHER_OPTIONS>
```

With three copies and two domains, one domain would hold two copies, and losing that domain would break the
journal quorum.

## Balance Rules During Operation

Once the cluster holds data, topology changes are admitted only if the failure domains stay balanced:

- The host count per domain may never diverge by more than one (±1 rule). On a balanced cluster, one host can be
  added to any domain. The next host must then go to a different domain.
- No domain may drop below two hosts.
- Adding another storage node slot on an already-member host (multi-socket systems) is balance-neutral and always
  admitted, as long as the host keeps its original domain label.

Violating additions and removals are refused up front, before any data is moved.

## Expanding a Failure-Domain Cluster

Single-node expansion integrates a new node into the cluster by re-homing existing secondary and tertiary
failover paths:

```bash title="Expanding the cluster by one node"
{{ cliname }} storage-node add-node <CLUSTER_ID> <SN_CTR_ADDR> <MGT_IF> \
    --failure-domain <FD_LABEL> \
    --expansion \
    <FURTHER_OPTIONS>
```

On failure-domain clusters, the expansion planner inserts the newcomer into the existing host rotation at a
position that preserves the cross-domain failover invariant. If no valid position exists, the expansion is refused
before any change is made.

!!! important
    On clusters with a single parity chunk (FTT 1), an odd total host count cannot satisfy the cross-domain
    invariant, because there is no tertiary path to fall back on. Grow such clusters in pairs, one host per
    domain at a time.

## Removing a Storage Node

Node removal applies the same balance rules (±1, minimum two hosts per domain). In addition, the failover paths
hosted by the node being removed are relocated to other nodes. If the path being relocated is the only
cross-domain path of its volume store, the replacement node **must** be in a different failure domain than the
primary. If no such node exists, the removal is refused.

## Moving a Host Between Domains

A host's failure domain is immutable. Re-adding a host or one of its node slots with a different domain label is
rejected. To move a host:

1. Remove the node with `{{ cliname }} storage-node remove`.
2. Restore the domain balance if necessary.
3. Re-add the node with the new `--failure-domain` label.

## Behavior During Outages

- Node and device outages confined to one failure domain keep the cluster **degraded but serving**, regardless of
  how many nodes of that domain are down.
- With two parity chunks, the cluster also tolerates a full domain outage plus one additional node or device
  outage in exactly one other domain.
- Anything broader suspends the cluster until enough nodes return.
- When an entire domain returns (for example, after a rack power cycle), its nodes are restarted in parallel.
  Parallel recovery stops automatically as soon as any node of that domain is online again or a node in another
  domain starts restarting.
