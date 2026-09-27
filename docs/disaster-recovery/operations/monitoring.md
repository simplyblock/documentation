---
title: "Monitoring"
description: "Monitor simplyblock DR: readiness verdicts and checks, status fields, kubectl views, events, Prometheus metrics, suggested alerts, and the report archive."
weight: 10410
---

simplyblock DR continuously evaluates whether each protected application can be moved along each of its declared DR
paths. The result, a readiness verdict with the checks behind it, is written to the application's status, emitted as
events, and exported as Prometheus metrics. Recovery actions and tests add their own status, events, metrics, and
reports.

## Readiness

dr-hub computes readiness for every pair of application and declared path, and re-evaluates it at least once a
minute. The verdict is one of the following:

| Verdict    | Meaning                                       | Effect on actions                                                     |
|------------|-----------------------------------------------|-----------------------------------------------------------------------|
| `Ready`    | Every check passed.                           | Actions run.                                                          |
| `Degraded` | At least one advisory check failed or warned. | Actions run. The warnings go into the report.                         |
| `NotReady` | At least one blocking check failed.           | Actions are refused unless they carry an override. Tests are refused. |
| `Unknown`  | Readiness has not been evaluated yet.         | Treated like `NotReady`.                                              |

!!! note
    In this release, the `storage-replicating` check always warns, because the replication state of the CSI driver
    is not yet reported. A fully healthy application therefore shows `Degraded`, not `Ready`.

### Readiness Checks

| Check                 | Blocks (NotReady) when                                                                                                                                                                                                                                                                     | Warns (Degraded) when                                                                                    |
|-----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| `path-declared`       | The plan, source, or target is missing, no DR path from source to target exists, or an adopted DRPlacementControl belongs to another site pair.                                                                                                                                            | Never                                                                                                    |
| `protection-bound`    | Any other binding problem, for example, the DR policy is not derived yet, the Placement is not Ramen-schedulable, the DRPlacementControl drifted, or no DRPlacementControl exists yet.                                                                                                     | Never                                                                                                    |
| `at-path-source`      | The application does not run at the path's `from` site. This makes the return path NotReady while the application is at its source.                                                                                                                                                        | The current site is unknown.                                                                             |
| `ramen-healthy`       | No DRPlacementControl, the application runs on a site no declared path starts from (placement off path), the DRPlacementControl is not `Available`, `PeerReady`, and `Protected`, or, for async, no group sync yet or the last group sync is older than 1.5 times the scheduling interval. | Never                                                                                                    |
| `storage-replicating` | Never                                                                                                                                                                                                                                                                                      | Always in this release (replication state unavailable).                                                  |
| `recipe-valid`        | A hand-written Recipe does not exist on the cluster the application runs on, or the generated Recipe failed to apply there.                                                                                                                                                                | The Recipe was not read or applied yet.                                                                  |
| `executor-ready`      | A job hook's image is not in `DRConfig.spec.agent.hookImageAllowList`, the target's dr-agent is down (for `postTargetReady` hooks), or an AAP hook has no executor.                                                                                                                        | The source's dr-agent is down (for `preSource` hooks).                                                   |
| `test-prereqs`        | On a path declaring Test, the target's dr-agent is down.                                                                                                                                                                                                                                   | No isolated NAD is configured on the path.                                                               |
| `test-recent`         | Never                                                                                                                                                                                                                                                                                      | No test along the path has passed, or the last pass is older than `test.recentWithin` (default 30 days). |
| `site-mapping`        | Never                                                                                                                                                                                                                                                                                      | Never. Informational only, reports `NotAvailable`.                                                       |

Checks that do not apply to a path, for example, `test-prereqs` on a path without Test, are reported as not
applicable and never lower the verdict.

## Status Fields

### ProtectedApplication

| Field                                                | Content                                                                                                                                                                                                     |
|------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `status.paths[]`                                     | One entry per declared path: `name`, `from`, `to`, `actions`, and `readiness` (with `verdict`, `checks[]`, and `lastTransitionTime`). Each check has `name`, `status`, `blocking`, `reason`, and `message`. |
| `status.currentCluster`                              | The cluster the application runs on, as reported by Ramen.                                                                                                                                                  |
| `status.drpc`, `status.placement`, `status.drPolicy` | The Ramen and OCM objects the application is bound to.                                                                                                                                                      |
| `status.recipe`                                      | The Recipe in use: `name`, `namespace`, `generated`, and `hash`.                                                                                                                                            |
| `status.backups[]`                                   | Per snapshot-s3 method: `method`, `running`, `lastSucceeded`, `lastScheduleTime`, and `lastFailure`.                                                                                                        |
| `status.lastAction`                                  | The most recent recovery action of the application.                                                                                                                                                         |
| `status.conditions`                                  | `Bound` and `Protected`.                                                                                                                                                                                    |

### ProtectionPlan

The conditions `Derived`, `InventoryReady`, `S3ProfileResolved`, and `Ready` show whether the plan's Ramen objects and
storage classes are in place. `status.sites[]` lists each site with its DR cluster, whether the storage classes were
applied, and whether its dr-agent is available. `status.pairs[]` lists each site pair with its paths, DR policies,
and whether Ramen resolved peer storage classes.

### DRPath

`status.applications` lists the applications on the path, `status.lastActions[]` the latest actions along it, and the
`Valid` condition whether the path is usable.

### DRConfig

`status.agents[]` shows each site's dr-agent: `cluster`, `available`, `version`, `veleroNamespace`, and `lastSeen`.
`status.stack[]` shows the delivered site stack components, and `status.lastBundle` the most recent state bundle.

## Command-Line Views

All simplyblock DR resources can be listed with `kubectl` on the hub. Short names and printer columns:

| Resource             | Short name | Columns                                          |
|----------------------|------------|--------------------------------------------------|
| DRConfig             | none       | Executor, Recovery, Bundle (wide)                |
| ProtectionPlan       | `pplan`    | Ready                                            |
| DRPath               | none       | From, To, Plan, Actions, Valid                   |
| ProtectedApplication | `papp`     | Plan, Source, Target, Kind, Current, Protected   |
| RecoveryPlan         | `rplan`    | Path, Readiness                                  |
| RecoveryAction       | `ract`     | Kind, Path, Application, Plan, Phase, RTO (wide) |
| TestBubble           | `tbub`     | Path, Application, Plan, Phase, Outcome          |
| TestSchedule         | `tsched`   | Schedule, Path, Suspend, Last                    |
| RestoreAction        | `rsa`      | Application, Phase, Cluster, Backup              |

Common commands:

```bash title="Inspecting DR status"
# Plans, paths, and site agents
kubectl get pplan
kubectl get drpaths
kubectl get drconfig default -o jsonpath='{range .status.agents[*]}{.cluster}{"\t"}{.available}{"\t"}{.lastSeen}{"\n"}{end}'

# Protected applications and their readiness per path
kubectl get papp -A
kubectl -n ramen-ops get papp orders \
  -o jsonpath='{range .status.paths[*]}{.name}{"\t"}{.readiness.verdict}{"\n"}{end}'

# Failing or warning checks of one path
kubectl -n ramen-ops get papp orders -o json \
  | jq '.status.paths[] | select(.name=="site-a-to-site-b") | .readiness.checks[] | select(.status=="Fail" or .status=="Warn")'

# Actions and tests
kubectl get ract -A -o wide
kubectl get tbub -A
```

## Events

- **ReadinessChanged:** Emitted on the ProtectedApplication whenever a verdict changes. It is a Warning event naming
  the first blocking check when the verdict becomes NotReady.
- **Phase transitions:** RecoveryActions, TestBubbles, and RestoreActions emit an event for every phase change, with
  the reason set to the new phase.
- **CleanupFailed:** Emitted on the ProtectedApplication when removing the workload from the cluster it left fails.

```bash title="Listing readiness events"
kubectl -n ramen-ops get events --field-selector involvedObject.kind=ProtectedApplication
```

## Prometheus Metrics

dr-hub serves Prometheus metrics over HTTPS on port `8443` of the dr-hub pod (named port `metrics`). The certificate
is self-signed.

| Metric                       | Type      | Labels                                              | Meaning                                                                                       |
|------------------------------|-----------|-----------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `dr_readiness_verdict`       | Gauge     | `namespace`, `application`, `path`, `verdict`       | 1 for the current verdict of the application on the path, 0 for the other verdicts.           |
| `dr_action_duration_seconds` | Histogram | `namespace`, `application`, `path`, `kind`, `phase` | Duration of finished recovery actions, by outcome phase.                                      |
| `dr_action_rto_seconds`      | Gauge     | `namespace`, `application`, `path`, `kind`          | RTO of the last completed action: creation until health probes passed.                        |
| `dr_achieved_rpo_seconds`    | Gauge     | `namespace`, `application`, `path`                  | Achieved RPO of the last failover: hand-off time minus the last replicated consistency point. |

The Helm chart ships neither a metrics Service nor a ServiceMonitor. With the Prometheus Operator, a PodMonitor such
as the following example can be created:

```yaml title="Example PodMonitor (not shipped with the chart)"
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: dr-hub
  namespace: dr-simplyblock
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: dr-hub
  podMetricsEndpoints:
    - port: metrics
      scheme: https
      path: /metrics
      tlsConfig:
        insecureSkipVerify: true
```

### Suggested Alerts

The following Prometheus rules are examples:

```yaml title="Example PrometheusRule"
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: dr-simplyblock
  namespace: dr-simplyblock
spec:
  groups:
    - name: dr-simplyblock
      rules:
        - alert: DRApplicationNotReady
          expr: dr_readiness_verdict{verdict="NotReady"} == 1
          for: 10m
          labels:
            severity: critical
          annotations:
            summary: "A protected application cannot be moved along one of its DR paths"
        - alert: DRFailoverRPOAboveInterval
          # 300 = the method's schedulingInterval (5m) in seconds
          expr: dr_achieved_rpo_seconds > 300
          labels:
            severity: warning
          annotations:
            summary: "The last failover lost more than one replication interval of data"
        - alert: DRActionFailed
          expr: increase(dr_action_duration_seconds_count{phase=~"Failed|RolledBack"}[1h]) > 0
          labels:
            severity: warning
```

An ongoing RPO breach of an async application (last group sync older than 1.5 times the interval) turns the
`ramen-healthy` check red with the reason `RPOExceeded`, so it fires `DRApplicationNotReady`. The metric
`dr_achieved_rpo_seconds` is written only after a failover.

## Reports

When `DRConfig.spec.archive` is configured, dr-hub writes a report for every finished RecoveryAction and TestBubble:
first a PDF, then a JSON document (`schema: dr.simplyblock.io/report/v1`). The JSON key is recorded in
`status.reportKey`. Free text in reports, such as hook log lines, is redacted for passwords, tokens, access keys,
and private keys.

The archive bucket uses the following layout:

```plain title="Archive bucket layout"
<prefix>reports/<namespace>/<kind>/<yyyy>/<mm>/<completed>-<name>-<uid8>.json
<prefix>reports/<namespace>/<kind>/<yyyy>/<mm>/<completed>-<name>-<uid8>.pdf
<prefix>bundle/<generation>.tar
<prefix>bundle/<generation>.sig
```

The prefix defaults to `dr/`. Finished runs are pruned from the hub per application or plan: the newest
`retention.keepPerApplication` (default 10) always stay, and older runs are deleted once they are older than
`retention.days` (default 90) and archived. Without an archive, nothing is pruned. With `archive.reportRetainDays`
set, reports are written under a compliance object lock.
