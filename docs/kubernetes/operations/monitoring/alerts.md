---
title: "Alerting"
description: "Simplyblock uses Grafana to configure and manage alerting rules By default, Grafana is configured to send alerts to Slack channels."
weight: 10630
---

Simplyblock uses Grafana to configure and manage alerting rules.

By default, Grafana is configured to send alerts to Slack channels. However, Grafana also allows alerting via email
notifications, but this requires the use of an authorized SMTP server to send a message.

An SMTP server is currently not part of the management stack and must be deployed separately. Alerts can be triggered
based on on-time or interval-based thresholds of statistical data collected (I/O statistics, capacity information) or
based on events from the cluster event log.

## Pre-Defined Alerts

The following pre-defined alerts are available:

| Alert                                  | Trigger                                                                                                                                                                                                   |
|----------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| device-unavailable                     | Storage device became unavailable.                                                                                                                                                                        |
| device-read-only                       | Storage device changed to status: read-only.                                                                                                                                                              |
| cluster-status-degraded                | Storage node changed to status: degraded.                                                                                                                                                                 |
| cluster-status-suspended               | Storage node changed to status: suspended.                                                                                                                                                                |
| storage-node-unreachable               | Storage node became unreachable.                                                                                                                                                                          |
| storage-node-offline                   | Storage node became unavailable.                                                                                                                                                                          |
| storage-node-healthcheck-failure       | Storage node with negative healthcheck.                                                                                                                                                                   |
| logical-volume-offline                 | Logical volume became unavailable.                                                                                                                                                                        |
| critical-capacity-reached              | Critical absolute capacity utilization in a cluster was reached. The threshold value can be configured at [cluster creation](../../../reference/cli/cluster.md) time using `--cap-crit`.                  |
| critical-provisioning-capacity-reached | Critical absolute provisioned capacity utilization in a cluster was reached. The threshold value can be configured at [cluster creation](../../../reference/cli/cluster.md) time using `--prov-cap-crit`. |
| root-fs-low-disk-space                 | Root filesystem free disk space is below 20%.                                                                                                                                                             |

It is possible to configure the Slack webhook for alerting during cluster creation or to modify it at a later point in
time.

## Event Log Alerts

The alerts above read the metrics collected into Thanos. A second, optional set of alerts reads the cluster event log
through the control plane's `/api/v2/clusters/<cluster-id>/logs` endpoint instead.

The distinction matters because the event log carries the transition an entity made, not only the state it ended in.
That is what lets these alerts tell a shutdown an operator asked for apart from a fault that produced the same end
state, and stay quiet for the former.

Each rule folds the newest event records into the current state of every node, device, and cluster, and returns one
row per entity that is currently wrong. Healing is therefore structural: the reverting event removes the row, the
row's absence removes the alert instance, and an entirely empty result resolves the alert.

Event log alerts are **disabled by default**. See [Enabling event log alerts](#enabling-event-log-alerts) below.

| Alert                           | Severity | Fires while                                                                                | Suppressed when                                                                                           | Clears when                                                                         |
|---------------------------------|----------|--------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| `StorageNode_left_online`       | critical | A storage node is in any state other than `online` or `in_creation`.                       | The node reached `in_shutdown`, `in_removal`, `pending_removal`, or `removed`, which no fault path does.  | The node returns to `online`.                                                       |
| `Device_became_unavailable`     | warning  | A device is currently `unavailable`.                                                       | The device went down within 120 seconds of its node leaving `online`, reported as the node alert instead. | The device returns to `online`.                                                     |
| `Device_removed`                | critical | A device reached `removed` within the last 24 hours.                                       | —                                                                                                         | The 24-hour window expires.                                                         |
| `Cluster_became_degraded`       | warning  | The cluster state is `degraded`.                                                           | A node is down as part of an operation an operator requested.                                             | The cluster returns to `active`.                                                    |
| `Cluster_became_suspended`      | critical | The cluster state is `suspended`.                                                          | —                                                                                                         | The cluster returns to `active`.                                                    |
| `Cluster_capacity_reached`      | warning  | The newest absolute or provisioned capacity event is at `Warning` or `Critical` level.     | —                                                                                                         | The freshness window expires (3 minutes, 20 minutes for a critical absolute event). |
| `JM_records_threshold_exceeded` | critical | A journal reported a compression backlog above its threshold within the last hour.         | —                                                                                                         | The one-hour window expires.                                                        |
| `JM_compression_error`          | critical | The newest compression event for a node and journal is a failure or a non-zero error code. | —                                                                                                         | The same journal reports a clean compression run.                                   |

Each alert title and each alert instance carries the cluster ID, so in a multi-cluster deployment the rules appear
once per cluster. The capacity thresholds are the same ones configured at
[cluster creation](../../../reference/cli/cluster.md) time with `--cap-warn`, `--cap-crit`, `--prov-cap-warn`, and
`--prov-cap-crit`.

### Enabling Event Log Alerts

Three values must all be set. If any one of them is missing, the data sources and the rules render as nothing at all,
with no error and no warning anywhere:

```yaml
controlplane:
  observability:
    # 1. The monitoring stack itself. Without this there is no Grafana to
    #    provision anything into.
    enabled: true
    grafana:
      eventAlerts:
        # 2. The event log alerts specifically.
        enabled: true

# 3. The cluster the alerts read, by ID and secret. Both are required.
csiConfig:
  simplybk:
    uuid: "<cluster-id>"
csiSecret:
  simplybk:
    secret: "<cluster-secret>"
```

The third item is the one that catches people out. A cluster ID and secret only exist once
[`cluster create`](../../../reference/cli/cluster.md) has run, which is *after* the chart is installed. A fresh
install therefore has an empty cluster list and provisions no event log alerts, even with `eventAlerts.enabled` set
to `true`. Retrieve the values and apply them in a second step:

```bash
# The cluster ID is also on the StorageCluster resource, as .status.uuid
sbcli cluster list
sbcli cluster get-secret <cluster-id>

helm upgrade simplyblock-operator <chart> -n <namespace> --reuse-values \
  --set csiConfig.simplybk.uuid=<cluster-id> \
  --set csiSecret.simplybk.secret=<cluster-secret>
```

!!! warning "Grafana must be restarted after any change"

    Grafana reads its provisioning files only at startup, and these alerts live in a ConfigMap. A `helm upgrade`
    that changes only the rules or the data source leaves the Grafana pod untouched, so the change has no effect
    until the pod restarts:

    ```bash
    kubectl rollout restart deploy/simplyblock-grafana -n <namespace>
    ```

    Allow a minute or two afterward. The Grafana image carries no plugins, so the REST data source plugin these
    alerts need is downloaded on every pod start, and the rules do not evaluate until it has loaded. An air-gapped
    installation must bake the plugin into the image and set
    `controlplane.observability.grafana.eventAlerts.plugin.preinstalled` to `true`.

### Multiple Clusters

Clusters are not discovered automatically. Each one is listed explicitly, and each contributes its own data source
and its own copy of every rule:

```yaml
storagenode:
  multiCluster:
    enable: true
    clusters:
      - cluster_id: "<first-cluster-id>"
        secret: "<first-cluster-secret>"
      - cluster_id: "<second-cluster-id>"
        secret: "<second-cluster-secret>"
```

An entry missing either its ID or its secret is skipped rather than provisioned half-configured. Adding a cluster
means editing these values, upgrading the release, and restarting Grafana as above.

### Tuning

| Value                             | Default | Effect                                                                                                                                                                 |
|-----------------------------------|---------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `eventAlerts.logLimit`            | `1000`  | How many of the newest event records each evaluation reads. Too low on a busy cluster and an alert heals itself once its opening transition scrolls out of the window. |
| `eventAlerts.interval`            | `1m`    | How often the rules run.                                                                                                                                               |
| `eventAlerts.for`                 | `1m`    | How long a condition must hold before it notifies.                                                                                                                     |
| `eventAlerts.plugin.preinstalled` | `false` | Set to `true` when the REST data source plugin is baked into the Grafana image, which skips a download on every pod start.                                             |

### Verifying

Confirm the rules loaded and are evaluating without error. A rule that cannot reach its data source reports
`health=error` while still appearing in the interface, so checking that the rules exist is not enough on its own:

```bash
kubectl exec -n <namespace> deploy/simplyblock-grafana -- sh -c \
  'curl -s -u admin:$GF_SECURITY_ADMIN_PASSWORD \
   "http://localhost:3000/api/prometheus/grafana/api/v1/rules"'
```

Every rule in the `simplyblock_events` group should report `health=ok`. On a healthy cluster they also report
`state=inactive`, because no entity is currently wrong.

To iterate on a rule's query, use **Explore** in Grafana against the `Simplyblock Events <cluster-id>` data source
with type `JSON`, source `URL`, parser `Backend`, and format `Table`. The rules themselves are provisioned from a
ConfigMap and are read-only in the interface, so they cannot be edited or previewed there.

### Current Limitations

- **A planned node restart still notifies.** A restart passes through `in_restart`, which is neither a healthy state
  nor one of the states treated as operator-requested, and a restart takes longer than the default `for` of one
  minute. The same applies to `sbcli storage-node suspend`, which reaches `suspended`.
- **Four of the alerts clear on a timer, not on recovery.** `Device_removed`, `Cluster_capacity_reached`,
  `JM_records_threshold_exceeded`, and `JM_compression_error` resolve when their freshness window expires rather
  than when the underlying condition is fixed.
- **Nothing is notified by default.** With no receiver enabled under
  `controlplane.observability.grafana.notifications`, no contact point and no notification policy are provisioned,
  and firing alerts are visible only in the Grafana interface. This includes the error a rule raises when it cannot
  reach its data source.
