---
title: Operations
weight: 10500
---

Ensuring data resilience and maintaining cluster health are critical aspects of managing a simplyblock storage
deployment. This section covers best practices for backing up and restoring individual volumes or entire clusters,
helping organizations safeguard their data against failures, corruption, or accidental deletions.

Key operational topics include:

- **[Backup and Recovery](backup-recovery.md):** Snapshot-based backup to S3 with policy-driven automation,
  cross-cluster restore, and retention management.
- **[Migrating a Storage Node](migrating-storage-node.md):** Live volume migration between nodes and full node
  replacement procedures.
- **[Replication](replication.md):** Cross-cluster asynchronous and synchronous replication with failover and failback
  for multi-site disaster recovery.
- **[Monitoring](monitoring/index.md):** Prometheus and Grafana dashboards for real-time cluster health, I/O
  statistics, and alerting.

Additionally, simplyblock provides comprehensive monitoring capabilities using built-in Prometheus and Grafana for
real-time visualization of cluster health, I/O statistics, and performance metrics.

This section details how to configure and use these tools, ensuring optimal performance, early issue detection, and
proactive storage management in cloud-native and enterprise environments.
