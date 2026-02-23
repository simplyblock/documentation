---
title: "Expanding a Storage Cluster"
weight: 29001
---

Simplyblock is designed as an always-on storage solution. Hence, storage cluster expansion is an online operation
without a need for maintenance downtime.

However, every operation that changes the cluster topology comes with a set of migration tasks, moving data across
the cluster to ensure equal usage distribution. While these migration tasks are low priority and their overhead is
designed to be minimal, it is still recommended to expand the cluster at times when the storage cluster isn't under
full utilization.

!!! info
    Add storage nodes in **pairs** (i.e., 2, 4, 6, … nodes at a time).  
    Expansions with an odd number of nodes are **not supported**.

To add a new storage node, follow the installation steps for your chosen deployment method up to the point where nodes are added to the cluster, then continue here:

- [Storage nodes in Kubernetes](../../deployments/kubernetes/index.md)
- [Storage nodes on Linux](../../deployments/install-on-linux/install-sp.md)

After adding the **first** new storage node, the cluster transitions to **IN_EXPANSION** and starts background rebalancing.
Add the remaining node(s) required for the expansion (storage nodes must be added in **pairs**).
Once all newly added nodes are healthy/ready, finalize the expansion:

```bash title="Finalize cluster expansion"
{{ cliname }} complete-expand <CLUSTER_ID>
