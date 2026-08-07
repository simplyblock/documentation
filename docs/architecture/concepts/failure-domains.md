---
title: "Failure Domains"
description: "How simplyblock failure domains group storage nodes by rack, cabinet, or availability zone and constrain data, journal, and failover-path placement."
weight: 30750
---

A failure domain groups storage nodes that share a common infrastructure dependency — a rack, a cabinet, a power
distribution unit, or an availability zone. When failure domains are enabled, simplyblock spreads data chunks,
journal copies, and failover paths across the domains so that the loss of one entire domain does not interrupt
the availability of the cluster.

Failure domains are identified by a non-negative integer chosen by the operator. Simplyblock does not detect the
physical topology itself: every storage node is explicitly tagged with the id of the domain it belongs to when it
is added to the cluster.

!!! important
    Failure-domain support is a deploy-time decision. It is enabled when the storage cluster is created and cannot
    be switched on or off for an existing cluster. To gain the feature, a cluster must be redeployed.

## What Failure Domains Protect

With failure domains enabled, placement decisions consider the domain tag in four independent dimensions:

1. **Data and parity chunks:** The distributed erasure coding spreads the chunks of each stripe across distinct
   failure domains, so that a full domain outage leaves enough chunks to reconstruct all data within the configured
   erasure coding scheme.
2. **Journal copies:** The copies of the high-availability write journal are balanced across domains with a
   per-domain cap, so that losing a whole domain always leaves enough journal copies to maintain the journal quorum.
3. **Failover paths:** The secondary (and, with two parity chunks, tertiary) failover nodes of each logical volume
   are placed in different failure domains than the primary node wherever possible.
4. **Cluster status:** The health assessment of the cluster understands domains. Any combination of node and
   device outages confined to a single failure domain keeps the cluster serving I/O in a degraded state instead
   of suspending it.

## The Placement Contract

Placement constraints are applied in a fixed priority order: distinct hosts are a hard requirement, distinct
failure domains are enforced next, and distinct physical labels are considered last.

For the failover paths, the guaranteed invariant is:

> Every logical volume store keeps **at least one failover path in a different failure domain** than its
> primary node.

With two failure domains and three paths (primary, secondary, tertiary), it is mathematically impossible to place
all three paths in distinct domains. Simplyblock therefore guarantees at least one cross-domain failover path per
volume store — enough to survive a full domain outage — and places the remaining paths cross-domain wherever the
topology allows it.

At cluster activation, simplyblock arranges the hosts in a round-robin order across the failure domains and derives
all secondary and tertiary assignments from this interleaved rotation. On a cluster with equally sized domains, this
construction makes every secondary path cross-domain by design.

## Balance Rules

Failure-domain placement only works if the domains stay comparable in size. Simplyblock enforces this:

- At **activation**, all failure domains must contain an **equal number of hosts**, and at least two domains must
  exist.
- During **operation**, the host count per domain may never diverge by more than **one host** (±1 rule). Adding or
  removing a node is refused if it would unbalance the domains further.
- Every domain must keep at least **two hosts** once the cluster holds data.

A cluster with a one-host imbalance stays fully within the availability contract: exactly one volume store then has
a same-domain secondary path, and its tertiary path is still guaranteed to be cross-domain.

!!! note
    Balance is counted in physical hosts, not storage nodes. On multi-socket hosts running two storage nodes, both
    nodes count as one host and must carry the same failure-domain id. Dedicated secondary nodes are not counted
    toward the balance.

## Failure Domains and Erasure Coding Schemes

The number of failure domains should match the data protection goal:

| Goal                                                                            | Recommendation                                                                                                |
|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| Survive one full domain outage                                                  | At least `parity chunks + 1` distinct failure domains                                                         |
| Survive one full domain outage plus one further node or drive failure elsewhere | Erasure coding scheme with two parity chunks (e.g., `1+2`, `2+2`) and at least as many domains as data chunks |

The high-availability journal requires at least **four** journal copies on failure-domain clusters (instead of
three), even with a single parity chunk. With three copies and two domains, one domain would hold two copies and
its loss would break the journal quorum.

## Domain Membership Is Immutable

A host's failure domain cannot be changed while the host is part of the cluster. Moving a host between domains
requires removing the node, restoring the domain balance, and re-adding it with the new failure-domain id. This
prevents accidental topology changes that would silently invalidate the placement of existing data.

## Recovery Behavior

Failure domains also change how the cluster recovers from large outages:

- An outage confined to one domain — up to and including every node of the domain — keeps the cluster **degraded
  but serving**. The cluster is not suspended.
- With two parity chunks, the cluster additionally tolerates the loss of one entire domain **plus** one further
  node or device outage in exactly one other domain.
- When a whole domain returns from an outage (for example, after a rack power loss), its nodes are restarted **in
  parallel** instead of strictly one-by-one, substantially shortening the recovery of large domains.

For operating instructions — creating a failure-domain cluster, adding and removing nodes, and expansion rules —
see [Managing Failure Domains](../../non-kubernetes/operations/failure-domains.md). For Kubernetes-based
deployments, failure domains are assigned through the Simplyblock Operator; see the
[Operator Reference](../../reference/operator/index.md).
