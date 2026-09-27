---
title: "Alerting"
description: "Pre-defined Grafana alert rules of the simplyblock control plane on Kubernetes, their notification channels configured through Helm, and the alerts endpoint."
weight: 10630
---

Simplyblock uses Grafana to evaluate and deliver alerts. On Kubernetes, Grafana is part of the optional observability
stack of a local control plane, installed when the Helm value `controlplane.observability.enabled` is `true`. The alert
rules are provisioned by the chart, and the notification channels are configured through Helm values. Independently of
Grafana, the control plane exposes the currently active conditions through a REST endpoint.

## Pre-Defined Alerts

The following alert rules are provisioned into Grafana and evaluated every minute:

| Alert rule                                 | Trigger                                                                   |
|--------------------------------------------|---------------------------------------------------------------------------|
| `Device_status_online_to_unavailable`      | A storage device became unavailable.                                      |
| `Device_status_online_to_read_only`        | A storage device changed to status read-only.                             |
| `Cluster_status_online_to_degraded`        | The cluster changed to status degraded.                                   |
| `Cluster_status_online_to_suspended`       | The cluster changed to status suspended.                                  |
| `StorageNode_status_online_to_unreachable` | A storage node became unreachable.                                        |
| `StorageNode_status_online_to_down`        | A storage node became unavailable.                                        |
| `StorageNode_health_check_false`           | A storage node reports a negative health check.                           |
| `Cluster_provisioned_capacity_reached`     | The critical provisioned capacity utilization of the cluster was reached. |
| `Cluster_absolute_capacity_reached`        | The critical absolute capacity utilization of the cluster was reached.    |
| `Lvol_status_online_to_offline`            | A logical volume became unavailable.                                      |
| `Root Filesystem Low Space Alert`          | Free space of a root filesystem fell below 20%.                           |

The capacity thresholds are set on the `StorageCluster`, in `spec.warningThreshold` and `spec.criticalThreshold`, each
with a `capacity` and a `provisionedCapacity` value:

```yaml title="Example of the capacity thresholds of a StorageCluster"
spec:
  warningThreshold:
    capacity: 75
    provisionedCapacity: 150
  criticalThreshold:
    capacity: 90
    provisionedCapacity: 200
```

## Notification Channels

Every enabled channel receives every simplyblock alert. The channels are configured under
`controlplane.observability.grafana.notifications` in the Helm values. With none of them enabled, no contact point is
provisioned and the default notification policy of Grafana stays in place.

| Channel   | Values                                                                                                                             |
|-----------|------------------------------------------------------------------------------------------------------------------------------------|
| Slack     | `slack.enabled`, `slack.url` (incoming webhook URL)                                                                                |
| Teams     | `teams.enabled`, `teams.url` (incoming webhook or workflow URL)                                                                    |
| PagerDuty | `pagerduty.enabled`, `pagerduty.integrationKey`, `pagerduty.severity`, and the optional `class`, `component`, and `group`          |
| Opsgenie  | `opsgenie.enabled`, `opsgenie.apiKey`, `opsgenie.apiUrl`, `opsgenie.autoClose`, `opsgenie.overridePriority`, `opsgenie.sendTagsAs` |
| Webhook   | `webhook.enabled`, `webhook.url`, `webhook.httpMethod`, basic or authorization-header credentials, `webhook.maxAlerts`             |

```yaml title="Example of Helm values enabling Slack notifications"
controlplane:
  observability:
    enabled: true
    grafana:
      notifications:
        slack:
          enabled: true
          url: https://hooks.slack.com/services/<WEBHOOK_PATH>
```

!!! warning
    The channel credentials are rendered into the `simplyblock-grafana-alerting` ConfigMap, so read access to the
    release namespace is read access to them.

E-mail notifications require an SMTP server, which is not part of the control plane and has to be provided
separately.

## Querying Alerts Directly

The control plane also exposes the currently active conditions as a REST resource, which answers what is wrong right
now without going through Grafana:

```plain title="Alerts endpoint"
GET /api/v2/clusters/<CLUSTER_UUID>/alerts/
```

It suppresses the states an operator caused on purpose, such as a node that was shut down or a device that was
removed, and it drops each alert as soon as the condition ends. The cluster UUID is held in
`StorageCluster.status.uuid`. See [Alerts Endpoint](../../../reference/api/alerts.md) for the full list of alert kinds,
the query parameters, and how to forward the alerts to a Slack webhook.
