---
title: "Alerts Endpoint"
description: "REST endpoint returning the conditions in a simplyblock cluster that currently need an operator, with suppression of operator-initiated states and Slack integration."
weight: 20100
---

The cluster event log is a journal. It records what happened, keeps it, and never retracts anything. Answering
*"what is wrong right now"* from it means reading the whole history and working out which entries still apply.

The alerts endpoint answers that question directly. It returns the conditions that are true at this moment,
suppresses the ones an operator caused on purpose, and removes each entry as soon as it stops being true.

```plain title="Endpoint"
GET /api/v2/clusters/<CLUSTER_UUID>/alerts/
```

Authorization is the standard cluster header described in [API / Developer SDK](index.md).

## Getting the Current Alerts

By default, the endpoint returns only what is wrong now. Every entry has `status: firing`.

```bash title="What is wrong right now"
curl -H "Authorization: $CLUSTER_UUID $CLUSTER_SECRET" \
  "https://$MGMT_IP/api/v2/clusters/$CLUSTER_UUID/alerts/"
```

```json title="Response"
[
  {
    "id": "node_offline:08820485-de07-42b7-b43e-1d96113db000",
    "kind": "node_offline",
    "severity": "critical",
    "status": "firing",
    "message": "node worker-3 offline",
    "cluster_id": "d6e9a1c4-...",
    "node_id": "08820485-de07-42b7-b43e-1d96113db000",
    "device_id": null,
    "since": "2026-09-12 13:46:13.930000+00:00",
    "first_seen": "2026-09-12 13:46:19.210000+00:00",
    "resolved_at": null,
    "details": {"status": "offline"}
  }
]
```

An empty array means nothing is wrong.

The `id` is derived from the alert kind and the object it concerns, so it is stable across polls. A consumer can
deduplicate on it without keeping any state of its own. Critical alerts sort before warnings, and firing alerts
before resolved ones.

## Query Parameters

| Parameter         | Type                 | Default | Description                                                                            |
|-------------------|----------------------|---------|----------------------------------------------------------------------------------------|
| `severity`        | `critical`/`warning` | all     | Return only alerts of this severity.                                                   |
| `status`          | `firing`/`resolved`  | all     | Return only alerts in this state.                                                      |
| `history`         | boolean              | `false` | Also return alerts that have already resolved.                                         |
| `history_seconds` | integer ≥ 1          | —       | Limit the history to alerts resolved within this many seconds. Implies `history=true`. |

```bash title="Only the page-worthy ones"
curl ... "/api/v2/clusters/$CLUSTER_UUID/alerts/?severity=critical"
```

```bash title="Everything, including what has already resolved"
curl ... "/api/v2/clusters/$CLUSTER_UUID/alerts/?history=true"
```

```bash title="What happened in the last hour"
curl ... "/api/v2/clusters/$CLUSTER_UUID/alerts/?history_seconds=3600"
```

```bash title="Only the things that cleared in the last hour"
curl ... "/api/v2/clusters/$CLUSTER_UUID/alerts/?history_seconds=3600&status=resolved"
```

History is bounded: resolved alerts are kept for seven days, and at most 200 entries per cluster. For anything
older, the cluster event log holds an `ALERT_RAISED` and an `ALERT_RESOLVED` entry for every transition.

## Alert Kinds

| Kind                                    | Severity | Fires when                                                        | Stays quiet when                                           |
|-----------------------------------------|----------|-------------------------------------------------------------------|------------------------------------------------------------|
| `node_offline`                          | critical | A storage node is offline.                                        | An operator stopped it with `storage-node shutdown`.       |
| `node_restart_hung`                     | critical | A node has been restarting for more than three minutes.           | —                                                          |
| `node_unavailable`                      | critical | A storage node is unreachable.                                    | —                                                          |
| `node_down`                             | critical | A node has been down for more than 60 seconds.                    | Another node is restarting or shutting down.               |
| `cluster_degraded`                      | critical | The cluster is degraded.                                          | A node was stopped by an operator.                         |
| `cluster_suspended`                     | critical | The cluster is suspended.                                         | Never. A suspended cluster serves no I/O.                  |
| `device_unavailable`                    | critical | A device on an **online** node is unavailable, failed or removed. | The operator removed it, or the node itself is not online. |
| `node_jc_compression_error`             | critical | The journal reported a compression error.                         | —                                                          |
| `node_unrecoverable_io_error`           | critical | An unrecoverable I/O error (a *distr error* in the event log).    | —                                                          |
| `node_unrecoverable_jc_error`           | critical | An unrecoverable journal error.                                   | —                                                          |
| `api_slow`                              | critical | Mean control plane API request latency above 15 seconds.          | —                                                          |
| `cluster_capacity_critical`             | warning  | Absolute capacity passed `--cap-crit`.                            | —                                                          |
| `cluster_provisioned_capacity_critical` | warning  | Provisioned capacity passed `--prov-cap-crit`.                    | —                                                          |

### Why Operator-Initiated States Are Not Alerts

Every condition in the table above is also produced deliberately, many times a day, by ordinary operations. An
operator shuts a node down, so the node is offline and the cluster is degraded. A node restarts, so its peers go
briefly down. An operator pulls a device, so the device is unavailable.

An alert feed that fires on those is noise, and a noisy feed is one nobody reads. The endpoint therefore
suppresses each of them, using the record of the operator's intent rather than guessing:

- A node stopped with `{{ cliname }} storage-node shutdown` is marked as deliberately stopped until it comes back
  online. Neither the node nor the cluster degradation it causes raises an alert.
- A device removed with `{{ cliname }} storage-node remove-device` is marked as administratively removed.
- Device alerts are raised **only for online nodes**. A graceful shutdown marks every device on the node
  unavailable on purpose, and an offline node cannot report anything meaningful about its devices. In those cases
  the node is the alert, and one node operation must not become a storm of device alerts.

A cluster in `suspended` is the deliberate exception: it is not serving I/O, so it alerts whatever the cause.

## Alerts Resolve

An alert that only ever appears is a problem report with no end. Whoever was notified has no way to learn from
the same channel that the problem is over.

Each alert therefore has two transitions, and both are recorded in the cluster event log:

| Event            | Level               | Written when              |
|------------------|---------------------|---------------------------|
| `ALERT_RAISED`   | Critical or Warning | A condition starts.       |
| `ALERT_RESOLVED` | Info                | The same condition stops. |

Only transitions are written. A condition that persists for a week produces two event log entries, not one per
poll.

## Sending Alerts to Slack

Simplyblock clusters already send Grafana alerts to Slack through the contact point configured at cluster
creation, described in [Alerting](../../kubernetes/operations/monitoring/alerts.md). That covers the pre-defined
metric and event log rules. To get the alerts endpoint itself into Slack, use one of the following.

### Option 1: Grafana Event Log Rules

The endpoint writes `ALERT_RAISED` and `ALERT_RESOLVED` into the cluster event log, and Grafana can already read
that log through a REST data source. Enable the event log rules once, from any management node:

```bash title="Enable the event log alert rules"
{{ cliname }} cluster event-alerts <CLUSTER_UUID> --enable
```

Alerts then reach the same Slack channel as every other Grafana alert, and no additional component is needed.
Grafana downloads a plugin on the next restart, so it is briefly unavailable.

### Option 2: Poll the Endpoint and Post to a Slack Webhook

To work with the alert objects themselves, create a Slack
[Incoming Webhook](https://api.slack.com/messaging/webhooks){:target="_blank" rel="noopener"} for the target
channel and poll the endpoint. Each alert carries a stable `id`, so posting only the ones not already reported is
a set difference.

```bash title="/usr/local/bin/simplyblock-slack-alerts.sh"
#!/usr/bin/env bash
set -euo pipefail

: "${CLUSTER_UUID:?}" "${CLUSTER_SECRET:?}" "${MGMT_IP:?}" "${SLACK_WEBHOOK_URL:?}"
STATE=/var/lib/simplyblock/alerts.seen
mkdir -p "$(dirname "$STATE")"; touch "$STATE"

curl -fsS -H "Authorization: $CLUSTER_UUID $CLUSTER_SECRET" \
  "https://$MGMT_IP/api/v2/clusters/$CLUSTER_UUID/alerts/?severity=critical" \
  | jq -r '.[] | "\(.id)\t\(.message)"' > /tmp/alerts.now

# New alerts: firing now, not reported last time.
comm -13 <(sort "$STATE") <(sort /tmp/alerts.now) | while IFS=$'\t' read -r id message; do
  jq -n --arg t ":rotating_light: $message" '{text: $t}' \
    | curl -fsS -X POST -H 'Content-Type: application/json' -d @- "$SLACK_WEBHOOK_URL"
done

# Resolved alerts: reported last time, gone now.
comm -23 <(sort "$STATE") <(sort /tmp/alerts.now) | while IFS=$'\t' read -r id message; do
  jq -n --arg t ":white_check_mark: resolved: $message" '{text: $t}' \
    | curl -fsS -X POST -H 'Content-Type: application/json' -d @- "$SLACK_WEBHOOK_URL"
done

mv /tmp/alerts.now "$STATE"
```

Run it on a timer, for example, every minute:

```bash title="Run every minute"
*/1 * * * * CLUSTER_UUID=... CLUSTER_SECRET=... MGMT_IP=... SLACK_WEBHOOK_URL=... /usr/local/bin/simplyblock-slack-alerts.sh
```

!!! note
    Keep the Slack webhook URL out of the crontab itself. Anyone who can read it can post to the channel. Put it
    in a root-owned environment file and source it from the script.

!!! tip
    A poll interval of 30 to 60 seconds is a good default. The endpoint evaluates the cluster state on each
    request, and its alert lifecycle advances when it is polled, so a very long interval delays both the alert
    and its resolution.
