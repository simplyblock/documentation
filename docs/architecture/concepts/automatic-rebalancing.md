---
title: "Automatic Rebalancing"
description: "Automatic rebalancing is a fundamental feature of distributed data storage systems designed to maintain an even distribution of data across storage nodes."
weight: 30700
---

Automatic rebalancing is a fundamental feature of distributed data storage systems designed to maintain an even
distribution of data and performance across storage nodes. This process ensures optimal performance, prevents resource under-utilization,
and enhances system resilience by dynamically redistributing data in response to changes in cluster topology or workload
patterns.

In Simplyblock, re-balancing concerns the re-balancing of back storage (for rebalancing of front storage or volume "docking points", see 
[volume migration](volume-migration.md) for details). It's behaviour depends on weather local node affinity is turned on.

If local node affinity is turned on, primary data chunks are re-balanced with a preference to the node at which also the front storage resides.
If local node affinity is turned off, all data and parity chunks are distributed with the target to achieve absolute equal (in a relative sense) utilization
levels across all NVMe devices in the cluster under consideration of failure domains and data protection rules.

Data re-balancing uses three important principles:
- always try to move the longest contigous segments of data to minimize random-access IOPS
- do not use more than 20% of the cluster performance capacity, this is guaranteed by internal QoS
- use maximum parallelism (during migration, load all devices in the cluster equally to maximize migration speed within the 20%)

Rebalancing is used in the following scenarios:

- After temporary node outages (planned or unplanned)
- When expanding the cluster (adding nodes / devices)
- When "failing" devices or entire nodes (rebuild to restablish full redundancy without the devices)
