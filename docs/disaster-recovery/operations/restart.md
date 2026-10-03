---
title: "Restart After a Storage Recovery"
description: "Restart protected applications in place and in boot order after their storage cluster recovers from a suspension, automatically per plan or with a Restart action."
weight: 10455
---

A simplyblock storage cluster suspends when too many nodes or devices fail at once, and it comes back by itself once
enough of them return. The applications on the site did not move, but they did not recover either: their workloads
failed during the suspension, in no particular order, and their volumes need a clean reconnect. A `RecoveryAction` of
kind `Restart` brings such an application back on the same site, in boot order, with its hooks and health probes, and
with a report. With `autoRestart` enabled on the plan, dr-hub creates the action itself.

## Automatic Restarts

dr-agent watches the `StorageCluster` objects of its cluster and records every return from `Suspended` to `Online`
or `Degraded`. A recovery counts once the cluster has stayed up for `stableFor` (default `2m`). dr-hub maps every
protected application to its storage cluster through the `cluster_id` parameter of its StorageClasses and creates one
Restart per application and recovery when all of the following hold:

- **Opt-in:** The plan has `spec.autoRestart.enabled: true`, and the application is not annotated
  `dr.simplyblock.io/auto-restart: "false"`.
- **Scope:** The application runs on the site of the recovered storage cluster and has a volume on it.
- **Recent:** The recovery is at most one hour old.
- **Not concurrent:** No other action for the application is unfinished, and no Restart was created for this
  recovery before.

```yaml title="Automatic restarts in a protection plan"
spec:
  autoRestart:
    enabled: true
    stableFor: 2m
```

The created action is named `restart-<application>-<hash>`, annotated with the storage cluster, the recovery count,
and the recovery time, and stamped `created-by: dr-hub (storage recovery)`.

## Starting a Restart by Hand

A Restart names an application and no path, because source and target are the application's current site. Readiness
does not gate it, because the application is down. Managed applications are refused.

```yaml title="Restart recovery action"
apiVersion: dr.simplyblock.io/v1alpha1
kind: RecoveryAction
metadata:
  generateName: orders-restart-
  namespace: ramen-ops
spec:
  kind: Restart
  applicationRef:
    name: orders
```

## Phases

1. **PreFlight:** The application runs on the site that recovered, the storage cluster is `Online` or `Degraded`,
   and no other action runs.
2. **PreSource:** The `preSource` hooks run, best effort, as on a Failover.
3. **Restart:** A dr-agent task on the site stops the workloads all at once (Deployments and StatefulSets scaled to
   zero, VirtualMachines halted), waits until no pod uses the application's volumes (10 minutes at most), reconnects
   the volumes, and starts the workloads tier by tier: each tier is scaled back, and its ready conditions must pass
   before the next tier starts. Workloads no tier selects start last.
4. **Workflow:** The application's health probes.
5. **PostTargetReady:** The `postTargetReady` hooks announce the application again.
6. **Confirming:** The report is completed. The action ends in `Completed`.

A Restart that fails leaves the application stopped and reports the step it failed in. There is no retry loop: the
next recovery, or an operator, starts the next one.

## Report

`status.report.restart` holds the storage cluster, the recovery count, the time of the recovery, the seconds from the
recovery to the health probes passing (`recoveryToReadySeconds`), whether the volumes were reconnected
(`volumesReconnected`), and every step with its result and duration.

!!! info "Coming soon"
    The volume reconnect (a demote and promote of every volume through the Simplyblock Operator) waits on the
    operator. Until it is available, a Restart stops and starts the workloads in boot order only, and its report says
    that the volumes were not reconnected.
