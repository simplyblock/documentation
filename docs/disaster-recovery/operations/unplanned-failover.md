---
title: "Unplanned Failover"
description: "Recover an application on the DR site after the loss of its primary site with a Failover recovery action, including overrides, achieved RPO, and cleanup."
weight: 10430
---

An unplanned failover recovers an application on the DR site when its primary site is lost or unusable. In simplyblock
DR, it is a `RecoveryAction` of kind `Failover`. There is no final sync: the application starts from the last
replicated state on the target, and the data written after that point is lost. The action records this window as
the achieved RPO.

## Before Starting

- **Path allows Failover:** The DR path from the failed site to the DR site lists `Failover` in `spec.actions`.
- **Readiness:** With the source site down, readiness usually turns `NotReady` (for example, the DRPlacementControl
  is no longer `PeerReady`, or the last sync is too old). The action then needs an override.
- **Permissions:** An override requires the `override` verb on `recoveryactions`, granted by the `dr-admin` role.
- **Fencing for Metro DR:** A sync (Metro) method requires the source to be fenced first, see below.

## Starting an Unplanned Failover

```yaml title="Failover with an override"
apiVersion: dr.simplyblock.io/v1alpha1
kind: RecoveryAction
metadata:
  generateName: billing-failover-
  namespace: ramen-ops
spec:
  kind: Failover
  pathRef: site-a-to-site-b
  applicationRef:
    name: billing
  override:
    reason: "Site site-a is down after a power outage, accepting the data loss"
```

The `override.reason` must be 10 to 1024 characters long and is recorded in the report. Without an override, an
action on a `NotReady` application fails pre-flight.

## Differences From a Planned Failover

The phases are the same as for a [planned failover](planned-failover.md#phases), with these differences:

- **PreSource is best effort:** The `preSource` hooks are attempted on the source, capped at 2 minutes. A failure or
  an unreachable dr-agent becomes a warning, and the action continues.
- **No final sync:** The DRPlacementControl is set to `Failover` with the target as failover cluster. At this point,
  dr-hub records the achieved RPO as the time since the last group sync.
- **No rollback:** If the application does not start on the target in time, the action ends in `Failed`. It is never
  returned to the source.

The achieved RPO is reported in `status.report.achievedRPOSeconds` and the metric `dr_achieved_rpo_seconds`. For async
methods, it can lag the real replication state by up to one interval.

## Metro DR and Fencing

With a sync method, both sites write to volumes with the same storage identity. Before failing over, the source must
be fenced, so that it can no longer write.

!!! info "Coming soon"
    The NetworkFence pre-flight for Metro DR is behind the `metroFencing` feature gate in `DRConfig.spec.featureGates`
    and waits on CSI driver support. Unplanned failover under a sync method is not validated yet.

## After the Failover

Once the action completes, the application runs on the DR site. The old primary is still down, so the reverse path
reports `NotReady` (the DRPlacementControl is not `PeerReady`) until the old primary site is back and replication has
resumed.

### Cleanup of the Old Primary

When the old primary site comes back, Ramen waits until the application's workload there is gone before it resumes
replication toward it. For discovered applications whose DRPlacementControl dr-hub created, dr-agent on the old
primary removes the workload automatically (see
[Relocate (Restart)](relocate-restart.md#cleanup-on-the-source)). To perform this cleanup manually, annotate the
ProtectedApplication before the site returns:

```bash title="Opting out of automatic cleanup"
kubectl -n ramen-ops annotate papp billing dr.simplyblock.io/manual-cleanup="true"
```

### Failback

When the reverse path's readiness is `Ready` or `Degraded` again (the DRPlacementControl is `PeerReady`), the
application can be moved back with a `Relocate` along the reverse path. See
[Relocate (Restart)](relocate-restart.md#failback-after-a-failover).
