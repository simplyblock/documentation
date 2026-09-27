---
title: "Planned Failover"
description: "Move an application to its DR site without data loss with a Relocate recovery action: pre-checks, final sync, phases, rollback, hooks, and the report."
weight: 10420
---

A planned failover moves a healthy application from its current site to the DR site while both sites are available.
In simplyblock DR, it is a `RecoveryAction` of kind `Relocate` along a forward DR path. Ramen performs a final sync of
the volumes before the target takes over, so no data is lost. The application is stopped on the source and restarted
on the target, and the downtime is the RTO of the action.

## Use Cases

- **Maintenance:** Taking the primary site down for hardware, network, or platform work.
- **Site evacuation:** Moving applications away from a site ahead of a known risk, such as a power or cooling event.
- **Rehearsed cutover:** Exercising the complete move, including promotion and the external cutover hooks, which a
  [test failover](../testing/index.md) never exercises.

## Pre-Checks

Before creating the action, confirm the following:

- **Path allows Relocate:** The DR path from the current site to the DR site lists `Relocate` in `spec.actions`.
- **Readiness:** The application's readiness on the path is `Ready` or `Degraded`. Check the verdict and any failing
  checks as described in [Monitoring](monitoring.md#readiness).
- **Recent replication:** For async methods, the last group sync is recent. A red `ramen-healthy` check blocks the
  action.
- **No running action:** No other recovery action or test holds the application.
- **Hooks:** The images of all external hooks are in `DRConfig.spec.agent.hookImageAllowList` (check
  `executor-ready`).

```bash title="Checking readiness per path"
kubectl -n ramen-ops get papp orders \
  -o jsonpath='{range .status.paths[*]}{.name}{"\t"}{.readiness.verdict}{"\n"}{end}'
```

## Starting a Planned Failover

```yaml title="Relocate recovery action"
apiVersion: dr.simplyblock.io/v1alpha1
kind: RecoveryAction
metadata:
  generateName: orders-relocate-
  namespace: ramen-ops
spec:
  kind: Relocate
  pathRef: site-a-to-site-b
  applicationRef:
    name: orders
  timeout: 30m
```

The action is created in the namespace of the ProtectedApplication (`ramen-ops` for discovered applications). The
specification is immutable. The admission webhook records the creator in the annotation
`dr.simplyblock.io/created-by`. Several applications are moved together with a
[recovery plan](recovery-plans.md).

## Phases

1. **PreFlight:** Re-checks the path, binding, lock, current site, and readiness. A failure changes nothing.
2. **PreSource:** Runs the application's `externalHooks.preSource` hooks on the source site, for example, draining
   clients or withdrawing a virtual IP. A failing hook fails the action, and nothing is moved.
3. **RamenHandoff:** Sets the DRPlacementControl to `Relocate` with the target as preferred cluster. Ramen then
   performs the final sync, demotes the volumes on the source, promotes them on the target, and restores the
   Kubernetes objects in the order of the Recipe tiers. When Ramen waits for the workload to be removed from the
   source, dr-hub removes it (see [Relocate (Restart)](relocate-restart.md#cleanup-on-the-source)).
4. **TargetStarting:** Waits until Ramen reports the application relocated and available on the target.
5. **Workflow:** Waits up to 15 minutes for all `health.probes` to pass on the target and records the RTO.
6. **PostTargetReady:** Runs the `externalHooks.postTargetReady` hooks on the target site, for example, a DNS or load
   balancer update.
7. **Confirming:** Completes the report. The action ends in `Completed`.

## Watching Progress

```bash title="Watching a recovery action"
kubectl -n ramen-ops get ract -w -o wide
kubectl -n ramen-ops get ract orders-relocate-8f2lq -o jsonpath='{.status.steps}' | jq
kubectl -n ramen-ops get events --field-selector involvedObject.name=orders-relocate-8f2lq
```

`status.sourceCluster` and `status.targetCluster` show the clusters involved, and `status.steps` the journal of every
step.

## Rollback

If the application does not reach the target within `spec.timeout` (default `30m`) in `TargetStarting`, a `Relocate`
rolls back: the application is returned to the source, the `postTargetReady` hooks are re-run at the source, and the
action ends in `RolledBack`. There is no storage-level rollback.

After `TargetStarting`, there is no rollback. If the application moved but does not become healthy in `Workflow`, or
a `postTargetReady` hook fails, the action ends in `Failed` with the application running on the target.

## Result and Report

`status.report` contains the operator, the RTO in `rtoSeconds`, hook results, probe results, warnings (for example, from
a Degraded pre-flight), and the pre-flight readiness. With an archive configured, the report is stored as JSON and
PDF, and `status.reportKey` holds its key. See [Monitoring](monitoring.md#reports).

After a successful planned failover, the application runs at the path's `to` site, and the reverse path becomes the
one to use for moving it back. See [Relocate (Restart)](relocate-restart.md).
