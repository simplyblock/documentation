---
title: "Alerting"
weight: 30050
---

Simplyblock uses Grafana to configure and manage alerting rules.

By default, Grafana is configured to send alerts to Slack channels. However, Grafana also allows alerting via email
notifications, but this requires the use of an authorized SMTP server to send message.

An SMTP server is currently not part of the management stack and must be deployed separately. Alerts can be triggered
based on on-time or interval-based thresholds of statistical data collected (IO statistics, capacity information) or
based on events from the cluster event log.

## Pre-Defined Alerts

The following pre-defined alerts are available:

| Alert              | Trigger                                                       |
|--------------------|---------------------------------------------------------------|
| device-unavailable | Device Status changed from online to unavailable              |
| device-read-only   | Device Status changed from online to read-only                |
| sn-offline         | Storage node status changed from online to offline            |
| crit-cap-reached   | Critical absolute capacity utilization in cluster was reached |
| crit-prov-reached  | Critical absolute capacity utilization in cluster was reached |

It is possible to configure the Slack webhook for alerting during cluster creation or to modify it at a later point in
time.
