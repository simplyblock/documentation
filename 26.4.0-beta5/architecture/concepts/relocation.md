---
title: "Relocation"
description: "Restart-based relocation of whole workloads between sites with simplyblock DR, and the online migration of volumes between clusters and nodes."
source: "https://docs.simplyblock.io/latest/architecture/concepts/relocation/"
---

# Relocation

Relocation moves a running workload to another location. Simplyblock distinguishes three kinds of relocation. A DR
relocation moves entire applications between Kubernetes clusters and restarts them on the target site. An online
cluster migration moves volumes from one storage cluster to another without restarting the workloads that use them.
Within a single storage cluster, volumes move between storage nodes online.

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

An online cluster migration moves volumes to another storage cluster of the same control plane while their workloads
keep running. The volumes are replicated to the target cluster with asynchronous replication in `migration` mode while
the source keeps serving them. A migration plan in the control plane holds the volumes, places each of them on a
target storage node, and forecasts when the migration completes. Each source storage node migrates one volume at a
time.

Each volume ends with a cutover, and the cutover is online. The target volume is exposed under the same NQN as the
source, with its paths in the ANA state `inaccessible`, and these paths are connected on the consuming Kubernetes node
beforehand. The source is then fenced by making all of its paths inaccessible, and the remaining delta is transferred
during a brief I/O freeze. Finally, the ANA states flip: the storage node that leads the target logical volume store,
normally the primary, becomes optimized, and the other online members of the target non-optimized. Queued I/O drains
on the target without a disconnect, and the workload keeps running.

On Kubernetes, a migration is started by a `ReplicationOps` resource with `action: migration`, which can cover every
volume of a storage cluster. See
[Online Cluster Migration](../../kubernetes/operations/data-protection/online-cluster-migration.md).

The live migration of KubeVirt virtual machines between clusters is not covered by it. Workloads that cannot rely on
NVMe multipathing move between clusters with a restart-based DR relocation.

## Volume Migration Within a Cluster

Within one simplyblock storage cluster, volumes can already be migrated online between storage nodes without service
interruption, for example, to follow a workload for data locality, to balance I/O, or to drain a node before its
removal. See [Volume Migration](volume-migration.md).

## Further Reading

- [Failover](failover.md)
- [Relocate and Restart](../../disaster-recovery/operations/relocate-restart.md)
- [Online Relocation](../../disaster-recovery/operations/relocate-online.md)
- [Recovery Plans](../../disaster-recovery/operations/recovery-plans.md)
