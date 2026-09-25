---
title: "Relocate (Restart)"
description: "Move workloads between sites by restart with simplyblock DR: failback after a failover, permanent moves, application impact, and cleanup on the source."
weight: 10440
---

A relocation moves an application from one site to another by stopping it on the source and restarting it on the
target. It is a `RecoveryAction` of kind `Relocate` along a DR path. Ramen performs a final sync, demotes the
volumes on the source, promotes them on the target, and redeploys the application's Kubernetes objects there in the
order of its Recipe tiers. The same action serves for a [planned failover](planned-failover.md), for a failback after
an unplanned failover, and for a permanent move.

## How a Relocation Works

1. **Demote:** The application is stopped on the source. Its workload is removed so that its volumes can be
   demoted.
2. **Final sync:** The last changes are replicated to the target, so no data is lost.
3. **Promote:** The target's replicas become the primary volumes.
4. **Redeploy:** The application's objects are restored on the target tier by tier, with the readiness gates of each
   tier, and dr-hub waits for its health probes.

The phases, pre-checks, and rollback behavior are described in [Planned Failover](planned-failover.md#phases).

## Failback After a Failover

A failback is a `Relocate` along the reverse DR path, from the DR site back to the original primary. It requires:

- **Reverse path:** A DR path from the current site to the original site that lists `Relocate`, for example,
  `site-b-to-site-a` with `actions: [Relocate]`.
- **PeerReady:** After an [unplanned failover](unplanned-failover.md), the original site must be back and replication
  toward it must have resumed. Until then, the reverse path reports `NotReady`.

```yaml title="Failback along the reverse path"
apiVersion: dr.simplyblock.io/v1alpha1
kind: RecoveryAction
metadata:
  generateName: billing-failback-
  namespace: ramen-ops
spec:
  kind: Relocate
  pathRef: site-b-to-site-a
  applicationRef:
    name: billing
```

## Permanent Moves

A relocation along a path leaves the application at the path's `to` site for as long as needed. Protection continues
in the reverse direction, and readiness is evaluated on the paths starting at the new site. The application's
`spec.source` and `spec.target` do not change. `status.currentCluster` shows where it runs.

To protect the application toward a different site, or with a different replication method, a new
ProtectedApplication is required, because the DR policy of a DRPlacementControl is immutable.

## What Applications Experience

- **Downtime:** The application is unavailable from the moment it is stopped on the source until it is healthy on the
  target. This is the RTO recorded in the report.
- **Restart:** Pods and KubeVirt VMs are restarted on the target. In-memory state and open client connections are
  lost. VMs boot from their replicated disks.
- **Network identity:** Objects are restored exactly as captured. Clients reach the application on the target
  through whatever the `postTargetReady` hooks change, for example, DNS or a load balancer.
- **No data loss:** The final sync ensures that every write acknowledged before the stop is on the target.

## Cleanup on the Source

Ramen moves a discovered application only after its workload on the old site is gone, and waits for this in the
DRPlacementControl progression `WaitOnUserToCleanUp`. For DRPlacementControls that dr-hub created, dr-hub handles
this state: dr-agent on every cluster other than the target deletes, in the application's protected namespaces, all
unowned objects of the following kinds:

- **Workloads:** VirtualMachines, Deployments, StatefulSets, DaemonSets, ReplicaSets, CronJobs, Jobs, and Pods.
- **Configuration and networking:** Services, ConfigMaps, Secrets, ServiceAccounts, Ingresses, and Routes.
- **Volumes:** The PVCs selected by the application's `pvcSelector`.

It keeps the namespaces, the default service accounts and root CA ConfigMaps, and the replication objects that Ramen
needs to demote the volumes. Objects of other kinds stay on the old site and must be removed manually.

For a relocation, this happens before the application starts on the target. After an unplanned failover, it happens
when the old primary becomes reachable again. To opt out, annotate the ProtectedApplication with
`dr.simplyblock.io/manual-cleanup: "true"` and remove the workload manually when Ramen waits for it.
