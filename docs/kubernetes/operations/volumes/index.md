---
title: "Volumes"
description: "Operate simplyblock volumes on Kubernetes: migrate the backing logical volume, reclaim unused blocks, and recover a workload after a path loss."
weight: 10400
---

The lifecycle of a volume, from provisioning to deletion, is covered under [Usage](../../usage/index.md). This section
covers what is operated on an existing volume: moving its backing logical volume between storage nodes, reclaiming the
blocks its filesystem no longer uses, and getting a workload back to work after its NVMe-oF paths were gone.

| Topic                                              | Purpose                                                                                |
|----------------------------------------------------|----------------------------------------------------------------------------------------|
| [Volume Migration](volume-migration.md)            | Moving the backing logical volume between storage nodes while the volume stays online. |
| [Trimming a Filesystem](trimming.md)               | Reclaiming the unused blocks of a thin-provisioned logical volume.                     |
| [Recovering from Path Loss](path-loss-recovery.md) | Restoring a workload whose I/O failed while its NVMe-oF paths were gone.               |
