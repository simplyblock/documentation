---
title: "Failover"
description: "Planned relocation with a final sync and no data loss versus unplanned failover with an RPO, readiness gating, overrides, metro fencing, and failback."
weight: 30920
---

A failover moves a protected application from its current site to the target site of a DR path. Simplyblock
Disaster Recovery (DR) distinguishes a planned move, called a relocation, from an unplanned move, called a failover.
Both are requested explicitly as a `RecoveryAction` on the DR hub, for a single application or for an ordered recovery
plan of several applications. Simplyblock DR never starts a failover on its own, since cluster state alone does not
distinguish a lost site from a transient outage.

## Planned and Unplanned

| Aspect                | Planned (`Relocate`)                             | Unplanned (`Failover`)            |
|-----------------------|--------------------------------------------------|-----------------------------------|
| Typical cause         | Maintenance, datacenter move, failback           | Loss or outage of the source site |
| Source site           | Reachable and healthy                            | Down or unreliable                |
| Final synchronization | Yes, after the application stopped on the source | No                                |
| Data loss             | None                                             | Up to the recovery point (RPO)    |
| preSource hooks       | Must succeed, otherwise nothing moves            | Best effort, capped at 2 minutes  |
| Rollback on timeout   | Rolls back to the source site                    | No rollback                       |

For a relocation, the application is stopped on the source, the remaining changes are synchronized, and the volumes
are demoted on the source and promoted on the target. A failover promotes the last replicated state on the target
without a final synchronization. For asynchronous replication, the achieved recovery point is the time between the
last completed group synchronization and the start of the failover, and it is recorded in the action report. For
synchronous replication, no data is lost while the replication is in sync.

## Action Flow

A recovery action passes through a fixed sequence of phases, and it resumes after a restart of the DR hub:

1. **PreFlight:** Checks that the path allows the action, that the application is at the path's source, that no
   other action runs for it, and that its readiness permits the action.
2. **PreSource:** Runs the external preSource hooks on the source site.
3. **RamenHandoff:** Hands the move to Ramen, which demotes and promotes the volumes and restores the Kubernetes
   objects in the tier order.
4. **TargetStarting:** Waits until the application is placed and available on the target site.
5. **Workflow:** Waits until all health probes pass. The recovery time (RTO) is measured up to this point.
6. **PostTargetReady:** Runs the external postTargetReady hooks, for example, to switch DNS.
7. **Confirming:** Writes the action report (JSON and PDF) to the S3 archive.

After the move, the DR hub removes the remaining workload objects of the application from the old site, so that it
does not run twice.

## Readiness Gate and Override

Before an action runs, the readiness of the application for the chosen path is checked. `Ready` and `Degraded`
applications move. A `NotReady` or `Unknown` application is refused, which is the normal case for an unplanned
failover while the source site is down. A DR administrator can override the gate by giving a written reason in the
action. The override requires a dedicated permission, and the reason is recorded in the action report. An action that
a path does not declare can never be overridden.

## Fencing for Metro DR

With synchronous (metro) replication, both sites access the same storage identity. Before the target is promoted in
an unplanned failover, the source site must be fenced, so that it can no longer write to the volumes. Simplyblock DR
uses the csi-addons NetworkFence for this.

!!! info "Coming soon"
    The metro fencing pre-flight is behind a feature gate until the simplyblock CSI driver supports csi-addons
    NetworkFence. Until then, the source site has to be isolated from the storage by other means, for example, by
    shutting it down, before an unplanned failover with synchronous replication.

## Failback

Failback returns an application to its original site. It is always a relocation along the reverse DR path, so it
includes a final synchronization and loses no data. After an unplanned failover, the original site must first be
recovered and replication back to it must have resumed (the reverse path reports the peer as ready) before the
failback can run.

## Further Reading

- [Relocation](relocation.md)
- [Planned Failover](../../disaster-recovery/operations/planned-failover.md)
- [Unplanned Failover](../../disaster-recovery/operations/unplanned-failover.md)
- [Relocate and Restart](../../disaster-recovery/operations/relocate-restart.md)
- [Recovery Plans](../../disaster-recovery/operations/recovery-plans.md)
- [Storage-Level Replication](replication.md)
