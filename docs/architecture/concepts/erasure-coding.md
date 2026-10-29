---
title: "Erasure Coding"
description: "How simplyblock protects data with distributed erasure coding: data and parity chunks on different nodes, the supported schemes, and their overhead."
weight: 30600
---

Erasure coding protects data with less capacity overhead than full copies. Data is split into **k** data chunks, and
**m** parity chunks are computed from them. Together, the **k+m** chunks form a stripe. Any **k** chunks of a stripe
are enough to reconstruct it, so up to **m** chunks can be lost or corrupted without losing data.

Replication, by comparison, keeps full copies. To survive two failures, three copies are needed, a capacity overhead
of 200%. Erasure coding with `4+2` survives the same two failures with an overhead of 50%.

## Distributed Erasure Coding in Simplyblock

Simplyblock places every chunk of a stripe on a different storage node. Data is therefore protected not only from
device failures, but stays available when one or two whole nodes are down. With
[failure domains](failure-domains.md), the chunks are also spread across racks or zones. In a
[single-node cluster](../deployment-topologies/edge-clusters.md#one-node-edge-clusters), the chunks are placed on
different devices of the node instead.

The scheme is chosen once, when the cluster is created, and applies to all volumes of the cluster.

| Scheme | Tolerated failures | Capacity overhead | Minimum nodes |
|--------|--------------------|-------------------|---------------|
| `1+0`  | 0                  | 0%                | 1             |
| `1+1`  | 1                  | 100%              | 3             |
| `2+1`  | 1                  | 50%               | 4             |
| `4+1`  | 1                  | 25%               | 6             |
| `1+2`  | 2                  | 200%              | 5             |
| `2+2`  | 2                  | 100%              | 6             |
| `4+2`  | 2                  | 50%               | 8             |

The minimum node count includes spare nodes, so that the cluster can rebuild the data of a failed node onto the
others and keep full redundancy. A scheme without parity (`1+0`) offers no protection against failures.

The number of parity chunks also decides the failover paths of every volume: one parity chunk gives each volume a
secondary path, and two parity chunks give it a secondary and a tertiary path (see
[High Availability and Fault Tolerance](../high-availability-fault-tolerance.md#node-failures)).

See [Erasure Coding Configuration](../../deployment-preparation/erasure-coding-scheme.md) for how to choose a scheme.
