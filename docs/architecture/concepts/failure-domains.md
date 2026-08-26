---
title: "Failure Domains"
description: "How simplyblock failure domains group storage nodes by rack, cabinet, or availability zone and constrain data, journal, and failover-path placement."
weight: 30750
---

A failure domain groups storage nodes that share a common infrastructure dependency: a rack, a cabinet, a power
distribution unit, or an availability zone. When failure domains are enabled, simplyblock spreads data chunks,
journal copies, and failover paths across the domains so that the loss of one entire domain does not interrupt
the availability of the cluster.

Each domain is identified by a label, such as `RACK1`, `AZ2`, or `HOST1`. Simplyblock does not detect the
physical topology itself: every storage node is explicitly tagged with the label of the domain it belongs to when
it is added to the cluster. The domain is created by the first node carrying a given label, and every later node
naming that label joins it.

Internally, each label maps to a cluster-unique integer id, which is what placement and the data plane key off.
That id is assigned automatically and does not have to be tracked. It surfaces only in low-level logs and in the
`failure_domain` field of the API, which keeps its integer type for compatibility.

!!! important
    Failure-domain support is a deploy-time decision. It is enabled when the storage cluster is created and cannot
    be switched on or off for an existing cluster. To gain the feature, a cluster must be redeployed.

## What Failure Domains Protect

With failure domains enabled, placement decisions consider the domain tag in four independent dimensions:

1. **Data and parity chunks:** The distributed erasure coding spreads the chunks of each stripe across distinct
   failure domains so that a full domain outage leaves enough chunks to reconstruct all data within the configured
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
volume store, which is enough to survive a full domain outage. The remaining paths are placed cross-domain
wherever the topology allows it.

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

A cluster with a one-host imbalance stays fully within the availability contract. Exactly one volume store then has
a same-domain secondary path, and its tertiary path is still guaranteed to be cross-domain.

!!! note
    Balance is counted in physical hosts, not storage nodes. On multi-socket hosts running two storage nodes, both
    nodes count as one host and must carry the same failure-domain label. Dedicated secondary nodes are not counted
    toward the balance.

## Failure Domains and Erasure Coding Schemes

The number of failure domains determines both whether a cluster can activate with failure domains enabled at all,
and how much simultaneous node or domain loss it can then absorb.

!!! important
    Fresh activation requires **at least `parity chunks + 2` distinct failure domains**. Two domains are never
    enough, at any parity-chunk count: with only `parity chunks + 1` domains the layout has no spare host, so the
    very next node add or remove would strand a failover path with nowhere valid to go. Below the minimum,
    activation is refused. Disable failure domains, or add hosts in further domains first.

Once activated, tolerance for simultaneous node or domain outages follows from how evenly a stripe's
`data chunks + parity chunks` spread across the available domains:

- With **`data chunks + parity chunks` domains or more**, each domain holds at most one chunk per stripe, so the
  cluster tolerates the **complete loss of up to `parity chunks` domains** at once (the same guarantee as running
  without failure domains, now scoped to whole domains instead of individual nodes).
- With **fewer domains than `data chunks + parity chunks`**, at least one domain necessarily holds more than one
  chunk. A domain already carrying `⌈(data chunks + parity chunks) / domains⌉` down nodes has spent its entire
  worst-case contribution: further nodes going down in that same domain cost nothing extra, but a different
  domain going down spends a fresh share of the same budget. Any combination is tolerated as long as the summed
  worst-case contribution of the affected domains stays within `parity chunks`.

| Domains | 1+1             | 2+1             | 4+1             | 1+2             | 2+2             | 4+2             |
|---------|-----------------|-----------------|-----------------|-----------------|-----------------|-----------------|
| 1 – 2   | cannot activate | cannot activate | cannot activate | cannot activate | cannot activate | cannot activate |
| 3       | 1 whole domain  | 1 whole domain  | 1 node total    | cannot activate | cannot activate | cannot activate |
| 4       | 1 whole domain  | 1 whole domain  | 1 node total    | 2 whole domains | 2 whole domains | 1 whole domain  |
| 5       | 1 whole domain  | 1 whole domain  | 1 whole domain  | 2 whole domains | 2 whole domains | 1 whole domain  |
| 6+      | 1 whole domain  | 1 whole domain  | 1 whole domain  | 2 whole domains | 2 whole domains | 2 whole domains |

"1 whole domain" means every node in one domain, regardless of the domain's size, can go down at once and the
cluster stays available. Spending the identical budget as individual nodes spread one-per-domain across that many
domains is tolerated the same way. A cell short of a whole domain (`4+1` at 3 – 4 domains) instead means only that
many individual nodes total, anywhere in the cluster, survive at once, not a domain's worth.

The high-availability journal requires at least **four** journal copies on failure-domain clusters (instead of
three), even with a single parity chunk. With three copies and two domains, one domain would hold two copies and
its loss would break the journal quorum.

## Domain Membership Is Immutable

A host's failure domain cannot be changed while the host is part of the cluster. Moving a host between domains
requires removing the node, restoring the domain balance, and re-adding it with the new failure-domain label. This
prevents accidental topology changes that would silently invalidate the placement of existing data.

## Journal Copy Replacement on Removal

Removing a node also affects every journal redundancy set that included the departed node's journal copy. Each
surviving node running a local copy of such a set picks a replacement member before the departed journal is
retired.

The replacement is chosen with the same domain-balance goal as the original placement: a candidate from the
**same failure domain** as the departed node is preferred, so the set's domain distribution is left unchanged
rather than reshuffled. This is a best-effort preference, not a hard requirement: if no same-domain candidate is
available, a cross-domain one is used instead, and the removal itself is never blocked by it. This is the opposite
direction from failover-path relocation (see [The Placement Contract](#the-placement-contract)), which sometimes
requires a cross-domain target and refuses the removal if none exists.

## Recovery Behavior

Failure domains also change how the cluster recovers from large outages:

- An outage confined to one domain (up to and including every node of the domain) keeps the cluster **degraded
  but serving**. The cluster is not suspended.
- With two parity chunks, the cluster additionally tolerates the loss of one entire domain **plus** one further
  node or device outage in exactly one other domain.
- When a whole domain returns from an outage (for example, after a rack power loss), its nodes are restarted **in
  parallel** instead of strictly one-by-one, substantially shortening the recovery of large domains.

For operating instructions (cluster creation, node addition, node removal, and the expansion rules), see
[Managing Failure Domains](../../non-kubernetes/operations/cluster/failure-domains.md). For Kubernetes-based
deployments, failure domains are assigned through the Simplyblock Operator. See the
[Operator Reference](../../reference/operator/index.md).
