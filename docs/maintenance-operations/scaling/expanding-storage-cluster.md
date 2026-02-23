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
```

After the expansion is complete, the cluster returns to **ACTIVE** and resumes normal operation mode.

```plain title="Example output for finalizing cluster expansion"
[demo@demo ~]# {{ cliname }} cluster complete-expand e2cda3fe-e9f2-42ce-bb2d-eecd10f58ccf
2026-02-19 11:28:49,995: 139892426475328: INFO: Connecting to remote_jm_af8d10c1-6613-47a9-8ed0-ebdf1f873738
2026-02-19 11:28:50,133: 139892426475328: INFO: Connecting to remote_jm_e17ffb0c-89aa-496d-98ec-700e58cb831f
2026-02-19 11:28:50,786: 139892426475328: INFO: Connecting to remote_jm_86ccd3d3-378b-4ba1-ba26-a299e168a8cb
2026-02-19 11:28:50,933: 139892426475328: INFO: Connecting to remote_jm_e17ffb0c-89aa-496d-98ec-700e58cb831f
2026-02-19 11:28:51,357: 139892426475328: INFO: Creating hublvol on 86ccd3d3-378b-4ba1-ba26-a299e168a8cb
2026-02-19 11:28:52,467: 139892426475328: INFO: Connecting node af8d10c1-6613-47a9-8ed0-ebdf1f873738 to hublvol on 86ccd3d3-378b-4ba1-ba26-a299e168a8cb
2026-02-19 11:28:52,681: 139892426475328: INFO: Connecting to remote_jm_86ccd3d3-378b-4ba1-ba26-a299e168a8cb
2026-02-19 11:28:52,687: 139892426475328: INFO: Connecting to remote_jm_6bc978d0-84ba-4815-8b25-697cc4de5d5d
2026-02-19 11:28:52,841: 139892426475328: INFO: Connecting to remote_jm_e17ffb0c-89aa-496d-98ec-700e58cb831f
2026-02-19 11:28:53,319: 139892426475328: INFO: Connecting to remote_jm_af8d10c1-6613-47a9-8ed0-ebdf1f873738
2026-02-19 11:28:53,326: 139892426475328: INFO: Connecting to remote_jm_e17ffb0c-89aa-496d-98ec-700e58cb831f
2026-02-19 11:28:53,344: 139892426475328: INFO: Connecting to remote_jm_6bc978d0-84ba-4815-8b25-697cc4de5d5d
2026-02-19 11:28:53,873: 139892426475328: INFO: Creating hublvol on af8d10c1-6613-47a9-8ed0-ebdf1f873738
2026-02-19 11:28:54,953: 139892426475328: INFO: Connecting node 86ccd3d3-378b-4ba1-ba26-a299e168a8cb to hublvol on af8d10c1-6613-47a9-8ed0-ebdf1f873738
2026-02-19 11:28:55,098: 139892426475328: INFO: {"cluster_id": "e2cda3fe-e9f2-42ce-bb2d-eecd10f58ccf", "event": "STATUS_CHANGE", "object_name": "Cluster", "message": "Cluster status changed from in_expansion to active", "caused_by": "cli"}
2026-02-19 11:28:55,100: 139892426475328: INFO: Cluster expanded successfully
True
```
