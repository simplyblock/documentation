---
title: "Fault Tolerance and Erasure Coding"
description: "Choose the erasure coding scheme and fault tolerance of a simplyblock cluster: supported schemes, minimum nodes, failure domains, small clusters, and arrays."
weight: 29975
---

The erasure coding scheme decides how many failures a storage cluster tolerates, how much capacity protection costs,
and how many storage nodes the cluster needs. It is chosen once, when the cluster is created, and applies to all
volumes of the cluster. How erasure coding works is explained in
[Erasure Coding](../architecture/concepts/erasure-coding.md).

## Supported Schemes

A scheme `k+m` splits data into `k` data chunks and adds `m` parity chunks, each on a different storage node:

- **FTT** (failures to tolerate) is the number of storage nodes that can fail at the same time without data loss
  (`m`).
- **Overhead** is the additional raw capacity stored on top of the usable data.
- **Minimum nodes** is the number of storage nodes required for full redundancy, including the spare capacity to
  rebuild a failed node.

| Scheme | FTT | Overhead | IOPS and Latency | Minimum Nodes |
|--------|-----|----------|------------------|---------------|
| `1+0`  | 0   | 0%       | Very good        | 1             |
| `1+1`  | 1   | 100%     | Excellent        | 3             |
| `2+1`  | 1   | 50%      | Very good        | 4             |
| `4+1`  | 1   | 25%      | Very good        | 6             |
| `1+2`  | 2   | 200%     | Very good        | 5             |
| `2+2`  | 2   | 100%     | Very good        | 6             |
| `4+2`  | 2   | 50%      | Very good        | 8             |

## Choosing the Scheme

1. **Failures to tolerate:** One parity chunk survives one node failure, and two parity chunks survive two. Two parity
   chunks also give every volume a second standby path (see
   [High Availability and Fault Tolerance](../architecture/high-availability-fault-tolerance.md)).
2. **Capacity:** Wider schemes cost less capacity. `4+1` and `4+2` have the lowest overhead for their fault tolerance.
3. **Performance:** `1+1` and `1+2` keep full copies, which gives the lowest latency and the fastest rebuilds. Wider
   schemes reconstruct lost data from parity.
4. **Cluster size:** The scheme sets the minimum number of nodes. Small clusters therefore use `1+1` or `2+1`, and
   larger clusters can use the wider schemes.

## Failure Domains

With [failure domains](../architecture/concepts/failure-domains.md), the chunks of a stripe are also spread across
racks or zones. Activation then requires at least `parity chunks + 2` domains with an equal number of hosts each. How
many whole domains a scheme survives depends on the number of domains, as shown in
[Failure Domains and Erasure Coding Schemes](../architecture/concepts/failure-domains.md#failure-domains-and-erasure-coding-schemes).

## Small Clusters

One-node and two-node [edge clusters](../architecture/deployment-topologies/edge-clusters.md) place the chunks on
different devices of a node instead. A one-node cluster supports every scheme with one data device per chunk, and a
two-node cluster uses `1+1`.

## Storage Arrays and RAID Controllers

On [storage array](storage-arrays.md) LUNs or volumes of a local RAID controller, the RAID below simplyblock already
handles drive failures. An `n+1` scheme, preferably `4+1`, is then sufficient: on top of RAID 5, it tolerates two
failures, similar to RAID 6, with as little as 25% additional overhead.
