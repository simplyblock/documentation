---
title: "Operations"
description: "Operating simplyblock DR with recovery actions: monitoring, failover, relocation, recovery plans, backups, restores, and recovery of a lost hub."
weight: 10400
---

Every disaster recovery operation in simplyblock DR is a custom resource on the hub cluster. A `RecoveryAction` moves
one application, or all applications of a recovery plan, along one declared DR path. Its status is a journal of every
step, and a finished action produces a report. This page gives an overview of the actions and the rules they share.

## Relocate and Failover

A recovery action has one of two kinds. The target is always the `to` site of the action's DR path, and the path must
list the kind in `spec.actions`.

| Kind       | Use                                                                                           | Final sync | Data loss              | Rollback                                                   |
|------------|-----------------------------------------------------------------------------------------------|------------|------------------------|------------------------------------------------------------|
| `Relocate` | [Planned failover](planned-failover.md), [failback, and permanent moves](relocate-restart.md) | Yes        | None                   | Yes, on timeout while the application starts on the target |
| `Failover` | [Unplanned failover](unplanned-failover.md) when the source site is lost or unusable          | No         | Up to the achieved RPO | No                                                         |

A failback is a `Relocate` along the reverse path. Both kinds restart the application on the target site. Moving
running workloads without a restart is described in [Relocate (Online)](relocate-online.md).

## RecoveryAction Lifecycle

A recovery action passes through the following phases in order. It resumes at the phase it stopped in after a
restart of dr-hub.

| Phase             | What happens                                                                                                                                                                                                        |
|-------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Pending`         | The action was accepted.                                                                                                                                                                                            |
| `PreFlight`       | Checks that the path declares the kind, the application is on the path and bound, no other action holds it, it runs at the path's `from` site, and its readiness allows the action. A failure here changes nothing. |
| `PreSource`       | Runs the `externalHooks.preSource` hooks on the source site.                                                                                                                                                        |
| `RamenHandoff`    | Hands the move to Ramen by setting the action and target cluster on the DRPlacementControl.                                                                                                                         |
| `TargetStarting`  | Waits until Ramen reports the application relocated or failed over and available on the target.                                                                                                                     |
| `Workflow`        | Waits for the application's health probes on the target (up to 15 minutes) and records the RTO.                                                                                                                     |
| `PostTargetReady` | Runs the `externalHooks.postTargetReady` hooks on the target site, for example, DNS or load balancer cutover.                                                                                                       |
| `Confirming`      | Completes the report.                                                                                                                                                                                               |
| `Completed`       | The application runs and is healthy on the target.                                                                                                                                                                  |
| `Failed`          | The action stopped. The step that failed is in `status.steps`.                                                                                                                                                      |
| `RolledBack`      | A `Relocate` timed out while starting on the target and was returned to the source.                                                                                                                                 |

The RTO is measured from the creation of the action until all health probes pass. The action times out after
`spec.timeout` (default `30m`).

## Readiness Gate and Override

dr-hub computes a readiness verdict for every application on every declared path (see
[Monitoring](monitoring.md#readiness)). Pre-flight uses it as a gate:

- **Ready or Degraded:** The action runs. Degraded checks become warnings in the report.
- **NotReady or Unknown:** The action is refused unless it carries an override.

An override is `spec.override.reason`, a text of 10 to 1024 characters that is recorded in the report. Creating an
action with an override requires the `override` verb on `recoveryactions`, which only the `dr-admin` role grants. An
action the path does not declare is never allowed, even with an override.

## Per-Application Lock

Only one unfinished recovery action may hold an application at a time. A second action for the same application,
or a plan action that includes it, fails pre-flight. Tests are also refused while an action is running.

## Reports

Each finished action writes `status.report`: the operator who created it, the override reason, the RTO, the
achieved RPO for a failover, hook results, probe results, warnings, and the pre-flight readiness. With an archive
configured, dr-hub stores the report as JSON and PDF in S3 and records the key in `status.reportKey`. See
[Monitoring](monitoring.md#reports).

## Section Contents

- [Monitoring](monitoring.md)
- [Planned Failover](planned-failover.md)
- [Unplanned Failover](unplanned-failover.md)
- [Relocate (Restart)](relocate-restart.md)
- [Relocate (Online)](relocate-online.md)
- [Recovery Plans](recovery-plans.md)
- [Backup and Restore](backup-restore.md)
- [Hub Recovery](hub-recovery.md)
