---
title: "Test Schedules"
description: "Run simplyblock DR test failovers automatically on a cron schedule with a TestSchedule. Covers retention, suspension, overlap, and missed runs."
weight: 10320
---

A `TestSchedule` creates a [TestBubble](test-failover.md) at every time of a cron schedule. Regular tests keep the
`test-recent` readiness check green and produce a continuous record of achieved RPO and estimated RTO.

## TestSchedule Specification

| Field                | Description                                                                                                                                           |
|----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| `schedule`           | Standard 5-field cron expression, evaluated in UTC. Required.                                                                                         |
| `template`           | The specification of each TestBubble: `pathRef`, `applicationRef` or `planRef`, and optionally `cloneSource`, `holdFor`, and `maxLifetime`. Required. |
| `retention.keepLast` | Number of newest test runs to keep (default `10`). Older runs are deleted.                                                                            |
| `retention.keepFor`  | Deletes runs older than this duration.                                                                                                                |
| `suspend`            | Set to `true` to stop creating new runs. Running tests are not affected.                                                                              |

The status shows `lastScheduleTime`, `lastSuccessfulTime`, and `active` (the test currently running).

## Scheduling Behavior

- **No overlap:** A new run is never started while the previous one is still in progress.
- **No catch-up:** Missed runs, for example, during a hub outage or while suspended, are not made up.
- **Archive first:** With an archive configured, a run is deleted only once its report is archived.

## Example: Weekly Test

The following schedule tests the `erp` application along `fra-a-to-fra-b` every Sunday at 03:00 UTC and keeps the
last run:

```yaml title="Weekly TestSchedule"
apiVersion: dr.simplyblock.io/v1alpha1
kind: TestSchedule
metadata:
  name: erp-weekly
  namespace: ramen-ops
spec:
  schedule: "0 3 * * 0"
  template:
    pathRef: fra-a-to-fra-b
    applicationRef:
      name: erp
  retention:
    keepLast: 1
```

List schedules and their runs with the short names `tsched` and `tbub`:

```bash title="Listing schedules and test runs"
kubectl -n ramen-ops get tsched
kubectl -n ramen-ops get tbub
```

To pause a schedule, for example, during planned maintenance:

```bash title="Suspending a schedule"
kubectl -n ramen-ops patch tsched erp-weekly --type merge -p '{"spec":{"suspend":true}}'
```
