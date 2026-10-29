---
title: "Automatic Rebalancing"
description: "How simplyblock rebalances data across devices and nodes after failures, expansions, and removals, with bounded impact on client I/O."
weight: 30700
---

Automatic rebalancing keeps the data of a storage cluster evenly distributed across its devices and nodes. When the
cluster changes, for example, through a failure, an expansion, or a removal, simplyblock moves data in the background
until every device is again utilized equally relative to its capacity.

Rebalancing concerns the back storage, the data on the devices. Moving the front storage, the NVMe-oF entry point of
a volume, is a [volume migration](volume-migration.md), which copies no data.

## When Rebalancing Runs

- **After a device is failed:** The data of the failed device is rebuilt from parity onto the remaining devices
  (failure migration), which restores full redundancy without waiting for a replacement.
- **After a temporary outage:** A node or device that returns catches up on the writes it missed.
- **When the cluster is expanded:** Data moves onto new devices and nodes, so they share the load right away.
- **When a node is removed:** The data of the departing node moves to the remaining nodes before it leaves.

## How Data Is Placed

All data and parity chunks are distributed for an equal utilization of all devices, while honoring the protection
rules: the chunks of a stripe stay on different nodes and, with [failure domains](failure-domains.md), in different
domains. With [node affinity](../storage-performance-and-qos.md#data-locality) turned on (it is off by default),
the primary data of a volume is preferably placed on the node that hosts the volume.

In very small clusters, such as one- and two-node edge clusters, a rebuild cannot always keep the chunks of a stripe
on different nodes. Rebalancing then runs in a relaxed mode, so that redundancy is restored on the remaining devices
instead of waiting for another node.

## Limited Impact on Client I/O

Rebalancing follows three principles:

- **Large transfers:** It moves the longest contiguous segments possible, which is far cheaper than many small
  random I/Os.
- **Bounded share:** It runs in the internal metadata and migration
  [service class](../storage-performance-and-qos.md#service-classes), so client I/O keeps the larger share of the
  cluster's performance.
- **Maximum parallelism:** Within its share, it loads all devices of the cluster equally to finish as fast as
  possible.

A rebalancing can also be started explicitly through the cluster API, for example, after a manual change to the
cluster.
