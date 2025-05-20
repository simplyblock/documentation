---
title: "Alerting"
weight: 30050
---

Simplyblock uses Grafana to configure and manage alerting rules.

By default, Grafana is configured to send alerts to Slack channels. However, Grafana also allows alerting via email
notifications, but this requires the use of an authorized SMTP server to send a message.

An SMTP server is currently not part of the management stack and must be deployed separately. Alerts can be triggered
based on on-time or interval-based thresholds of statistical data collected (IO statistics, capacity information) or
based on events from the cluster event log.

## Pre-Defined Alerts

The following pre-defined alerts are available:

| Alert                                  | Trigger                                                                                                                                                                                                                      |
|----------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| device-unavailable                     | Storage device became unavailable.                                                                                                                                                                                           |
| device-read-only                       | Storage device changed to status: read-only.                                                                                                                                                                                 |
| cluster-status-degraded                | Storage node changed to status: degraded.                                                                                                                                                                                    |
| cluster-status-suspended               | Storage node changed to status: suspended.                                                                                                                                                                                   |
| storage-node-unreachable               | Storage node became unreachable.                                                                                                                                                                                             |
| storage-node-offline                   | Storage node became unavailable.                                                                                                                                                                                             |
| storage-node-healthcheck-failure       | Storage node with negative healthcheck.                                                                                                                                                                                      |
| logical-volume-offline                 | Logical volume became unavailable.                                                                                                                                                                                           |
| critical-capacity-reached              | Critical absolute capacity utilization in a cluster was reached. The threshold value can be configured at [cluster creation](../../reference/cli/cluster.md#creates-a-new-cluster) time using `--cap-crit`.                                                                   |
| critical-provisioning-capacity-reached | Critical absolute provisioned capacity utilization in a cluster was reached. The threshold value can be configured at [cluster creation](../../reference/cli/cluster.md#creates-a-new-cluster) time using `--prov-cap-crit`.                                                  |
| root-fs-low-disk-space                 | Root filesystem free disk space is below 20%.                                                                                                                                                                                |

It is possible to configure the Slack webhook for alerting during cluster creation or to modify it at a later point in
time.
