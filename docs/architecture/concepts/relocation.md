---
title: "Relocation"
description: "Restart-based relocation of whole workloads between sites with simplyblock DR, and the planned online migration of VMs and volumes across clusters."
weight: 30930
---

Relocation moves a running workload to another location. Simplyblock distinguishes three kinds of relocation. A DR
relocation moves entire applications between Kubernetes clusters and restarts them on the target site. An online
migration across clusters would move virtual machines and volumes without a restart and is planned for the future.
Within a single storage cluster, volumes already move between storage nodes online today.

## DR Relocation (Restart-Based)

A DR relocation is a planned move of a protected application, including its Kubernetes objects and its volumes,
along a DR path. It is requested as a `RecoveryAction` of kind `Relocate` on the DR hub and applies to a single
application or to a recovery plan with several applications in priority order.

The relocation runs in the following steps:

1. **Stop and demote:** The application is stopped on the source site, and its volumes are demoted.
2. **Final synchronization:** The remaining changes are replicated to the target site, so no data is lost.
3. **Promote:** The volumes are promoted on the target site.
4. **Restart on the target:** The Kubernetes objects are restored on the target site in the tier order of the
   application, and the application starts. Health probes confirm that it is up.
5. **Clean up:** The remaining workload objects on the old site are removed.

The application is unavailable between the stop on the source and the successful start on the target. If the target
does not become healthy within the action timeout while the source is still healthy, the relocation rolls back and
the application runs on the source again.

Failback is a relocation along the reverse DR path. The differences between a relocation and an unplanned failover
are described in [Failover](failover.md).

## Online Migration Across Clusters

!!! info "Coming soon"
    Online migration across clusters is not designed yet. It is intended to cover the live migration of KubeVirt virtual
    machines and the live migration of volumes from one simplyblock cluster to another, without restarting the
    workload. Until it is available, workloads move between clusters with a restart-based DR relocation.

## Volume Migration Within a Cluster

Within one simplyblock storage cluster, volumes can already be migrated online between storage nodes without service
interruption, for example, to follow a workload for data locality, to balance I/O, or to drain a node before its
removal. See [Volume Migration](volume-migration.md).

## Further Reading

- [Failover](failover.md)
- [Relocate and Restart](../../disaster-recovery/operations/relocate-restart.md)
- [Online Relocation](../../disaster-recovery/operations/relocate-online.md)
- [Recovery Plans](../../disaster-recovery/operations/recovery-plans.md)
