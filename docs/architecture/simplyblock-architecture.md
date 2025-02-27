---
title: "Simplyblock Architecture"
weight: 20100
---

## Control Plane

The control plane hosts the Simplyblock Management API and CLI endpoints with identical features. The CLI is equally
available on all management nodes. The API and CLI are secured using HTTPS / TLS.

The control plane provides the following functionality:

- Lifecycle management of clusters:
    - Deploy storage clusters
    - Manages nodes and devices
    - Resize and re-configure clusters
- Lifecycle management of logical volumes and pools
    - For Kubernetes, the Simplyblock CSI driver integrates with the persistent volume lifecycle management
- Cluster operations
    - I/O Statistics
    - Capacity Statistics
    - Alerts
    - Logging
    - others

The control plane also provides real-time collection and aggregation of io stats (performance, capacity,
utilization), proactive cluster monitoring and health checks, monitoring dashboards, alerting, a log file repository
with a management interface, data migration and automated node and device restart services.

For monitoring dashboards and alerting, the simplyblock control plane provides Grafana and Prometheus. Both systems are
configured to provide a set of standard alerts which can be delivered via Slack or email. Additionally, customers
are free to define their own custom alerts.

For log management, simplyblock uses Graylog. For a comprehensive insight, Graylog is configured to collect container
logs from control plane and storage plane services, the RPC communication between the control plane and storage cluster
and the data services logs (SPDK).

### Control Plane State Storage

The control plane is implemented as a stack of containers running on one or more management nodes. For production
environments, simplyblock requires at least 3 management nodes for high availability. The management nodes run as 
a set of replicated, stateful services.

For internal state storage, the control plane uses ([FoundationDB](https://www.foundationdb.org/){:target="_blank"}) as
its key-value store. FoundationDB, by itself, operates in a replicated high-available cluster across all management
nodes.

## Storage Plane




