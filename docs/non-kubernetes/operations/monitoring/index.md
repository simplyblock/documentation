---
title: "Monitoring"
description: "Monitoring the health, performance, and resource utilization of a Simplyblock cluster is crucial for ensuring optimal operation, early issue detection, and."
weight: 20200
---

Monitoring the health, performance, and resource utilization of a simplyblock cluster is crucial for ensuring optimal
operation, early issue detection, and efficient capacity planning. The `{{ cliname }}` command line interface
provides a comprehensive set of tools to retrieve real-time and historical metrics related to Logical Volumes (LVs),
storage nodes, I/O performance, and system status. By leveraging `{{ cliname }}`, administrators can quickly
diagnose bottlenecks, monitor resource consumption, and maintain overall system stability.

## Monitoring Objectives

The monitoring stack should answer four operational questions:

- Is the cluster healthy and reachable?
- Are storage nodes and logical volumes in expected state?
- Is performance within expected latency and throughput ranges?
- Are alert channels configured and actively delivering events?

## Recommended First Checks

When investigating a possible incident, start in this order:

1. Verify overall cluster health and status.
2. Check active alerts for immediate failures or capacity thresholds.
3. Inspect storage node and logical volume conditions.
4. Review I/O statistics for bottlenecks and saturation patterns.
5. Use dashboards and logs for deeper root-cause analysis.

## Monitoring Areas

| Area | Typical Signals | Primary Source |
|------|------------------|----------------|
| Cluster health | degraded/suspended/offline state, failing health checks | CLI + Grafana |
| Capacity | critical/warning capacity thresholds, provisioning pressure | CLI + alerts |
| Storage node status | unreachable/offline nodes, node-level anomalies | CLI + alerts |
| Logical volume status | volume health/offline conditions | CLI + Grafana |
| Performance | throughput, IOPS, latency trends | CLI + Grafana |
| Events and logs | operational events, service/component errors | Graylog |

## Monitoring Guides

- [Cluster Health](cluster-health.md)
- [Logical Volume Conditions](lvol-conditions.md)
- [Accessing I/O Stats ({{ cliname }})](io-stats.md)
- [Alerting](alerts.md)
- [Accessing Grafana](accessing-grafana.md)
- [Accessing Graylog](accessing-graylog.md)
