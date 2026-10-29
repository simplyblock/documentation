---
title: "Prometheus Metrics"
description: "Reference of the simplyblock Prometheus metrics: I/O, latency, capacity, status, CPU, and replication series of the control plane, and the operator metrics."
source: "https://docs.simplyblock.io/latest/kubernetes/operations/monitoring/prometheus-metrics/"
---

# Prometheus Metrics

Simplyblock exports its I/O statistics, capacity, status, CPU utilization, and replication health as Prometheus
metrics. They are the source of the Grafana dashboards, and any Prometheus-compatible system can scrape and query them
directly, for example, to build its own dashboards, alert rules, or capacity reports.

There are two sources:

- The **control plane exporter** publishes the state of every cluster, storage node, device, pool, logical volume,
  and replication relationship. It is scraped by the Prometheus of the control plane's observability stack.
- The **Simplyblock Operator** publishes the state of the Kubernetes resources it manages and of the operations it
  runs.

## Control Plane Exporter

The exporter is served by the management API:

```plain title="Scrape endpoint"
GET /api/v2/metrics
```

The Prometheus of the control plane scrapes it every 30 seconds as the job `simplyblock_metrics`, from the
`simplyblock-webappapi` service, authenticated with its Kubernetes service account token. An external Prometheus
can scrape it the same way, with the cluster's API credentials (see [API / Developer SDK](../../../reference/api/index.md))
or with a service account token that the control plane admits for metrics.

Every series is rebuilt from the cluster database on each scrape. An object that no longer exists stops being
exported, and every instance of the management API returns the same values.

### Labels

| Level          | Labels                                                                          |
|----------------|---------------------------------------------------------------------------------|
| Cluster        | `cluster`, `cluster_name`                                                       |
| Storage node   | `cluster`, `cluster_name`, `snode`, `hostname`                                  |
| Device         | `cluster`, `cluster_name`, `snode`, `device`                                    |
| Pool           | `cluster`, `cluster_name`, `pool`, `pool_name`                                  |
| Logical volume | `cluster`, `cluster_name`, `pool`, `pool_name`, `lvol`, `lvol_name`, `pvc_name` |
| Replication    | The logical volume labels, and `policy`, `policy_name`, `peer_cluster`          |
| CPU core       | The storage node labels, and `core_id`                                          |
| CPU thread     | The CPU core labels, and `thread_name`                                          |

The labels `cluster`, `snode`, `device`, `pool`, `lvol`, and `policy` hold UUIDs, so series of different levels join on
them. For example, the `pool` label of a logical volume series matches the `pool` label of its pool. The `*_name`
labels and `pvc_name` hold the human-readable names for filters and legends. `pvc_name` is the PersistentVolumeClaim
the volume belongs to.

### I/O Statistics

The following counters exist for each of the levels `cluster`, `snode`, `device`, `pool`, and `lvol`, so the name of
a metric is `simplyblock_<level>_<name>`, for example, `simplyblock_lvol_read_operations_total`:

| Name                        | Type    | Description                                |
|-----------------------------|---------|--------------------------------------------|
| `read_operations_total`     | Counter | Read operations since the counter started. |
| `read_bytes_total`          | Counter | Bytes read.                                |
| `read_latency_ticks_total`  | Counter | Accumulated read latency, in SPDK ticks.   |
| `write_operations_total`    | Counter | Write operations.                          |
| `write_bytes_total`         | Counter | Bytes written.                             |
| `write_latency_ticks_total` | Counter | Accumulated write latency, in SPDK ticks.  |
| `unmap_operations_total`    | Counter | Unmap (trim) operations.                   |
| `unmap_bytes_total`         | Counter | Bytes unmapped.                            |
| `unmap_latency_ticks_total` | Counter | Accumulated unmap latency, in SPDK ticks.  |

The counters are cumulative, so IOPS and throughput are their rates, and a restart of a storage node is handled by
`rate()`:

```plain title="IOPS and throughput of each logical volume"
sum by (lvol_name, pvc_name) (rate(simplyblock_lvol_read_operations_total[5m]) + rate(simplyblock_lvol_write_operations_total[5m]))
sum by (lvol_name, pvc_name) (rate(simplyblock_lvol_read_bytes_total[5m]) + rate(simplyblock_lvol_write_bytes_total[5m]))
```

The mean latency is the rate of the latency counter divided by the rate of the operation counter. Summing both before
the division gives the correct mean of a node or a cluster as well. The result is in SPDK ticks. On the device level,
`simplyblock_device_tick_rate_hertz` holds the tick rate of the node that measures the device, which converts ticks
into seconds:

```plain title="Mean write latency of each device, in seconds"
rate(simplyblock_device_write_latency_ticks_total[5m])
  / rate(simplyblock_device_write_operations_total[5m])
  / simplyblock_device_tick_rate_hertz
```

### Capacity

The following gauges are in bytes. They hold the effective capacity, which is what clients can store, so the ratio of
provisioned to total capacity is meaningful. The `raw` gauges hold the physical capacity the devices report. The
difference to the effective capacity is the erasure-coding overhead.

| Name                     | Levels                                       | Description               |
|--------------------------|----------------------------------------------|---------------------------|
| `size_total_bytes`       | `cluster`, `snode`, `device`, `pool`, `lvol` | Total effective capacity. |
| `size_used_bytes`        | `cluster`, `snode`, `device`, `pool`, `lvol` | Used effective capacity.  |
| `size_free_bytes`        | `cluster`, `snode`, `device`, `pool`, `lvol` | Free effective capacity.  |
| `size_provisioned_bytes` | `cluster`, `snode`                           | Provisioned capacity.     |
| `size_total_raw_bytes`   | `cluster`, `snode`, `device`                 | Total physical capacity.  |
| `size_used_raw_bytes`    | `cluster`, `snode`, `device`                 | Used physical capacity.   |
| `size_free_raw_bytes`    | `cluster`, `snode`, `device`                 | Free physical capacity.   |

The thresholds configured on the cluster are exported as ratios, so they compare directly with a ratio of the byte
gauges:

| Metric                                                              | Description                                                                                             |
|---------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| `simplyblock_cluster_capacity_warning_threshold_ratio`              | Used-capacity ratio that raises a warning.                                                              |
| `simplyblock_cluster_capacity_critical_threshold_ratio`             | Used-capacity ratio that raises a critical alert.                                                       |
| `simplyblock_cluster_provisioned_capacity_warning_threshold_ratio`  | Provisioned-capacity ratio that raises a warning. It can exceed 1, because provisioning may overcommit. |
| `simplyblock_cluster_provisioned_capacity_critical_threshold_ratio` | Provisioned-capacity ratio that raises a critical alert.                                                |

```plain title="Clusters above their critical capacity threshold"
simplyblock_cluster_size_used_bytes / simplyblock_cluster_size_total_bytes
  > on (cluster) simplyblock_cluster_capacity_critical_threshold_ratio
```

### Status and Health

| Metric                            | Labels                       | Description                                                               |
|-----------------------------------|------------------------------|---------------------------------------------------------------------------|
| `simplyblock_<level>_status`      | The level's labels, `status` | 1 on the series whose `status` label is the current status of the object. |
| `simplyblock_snode_health_check`  | Storage node labels          | 1 when the latest health check passed, 0 when it failed.                  |
| `simplyblock_device_health_check` | Device labels                | 1 when the latest health check passed, 0 when it failed.                  |
| `simplyblock_lvol_health_check`   | Logical volume labels        | 1 when the latest health check passed, 0 when it failed.                  |

The status gauge exists for the levels `cluster`, `snode`, `device`, `pool`, and `lvol`. The `status` label holds the
status as the control plane reports it, for example, `online`, `offline`, `unavailable`, or `degraded`. An alert
names the status it cares about:

```plain title="Storage nodes that are not online"
simplyblock_snode_status{status!="online"} == 1
```

An object without a health check verdict has no `health_check` series.

### CPU Utilization

The reactors and lightweight threads of SPDK on each storage node are exported as cumulative tick counters:

| Metric                                       | Labels            | Description                 |
|----------------------------------------------|-------------------|-----------------------------|
| `simplyblock_snode_reactor_busy_ticks_total` | CPU core labels   | Ticks the reactor was busy. |
| `simplyblock_snode_reactor_idle_ticks_total` | CPU core labels   | Ticks the reactor was idle. |
| `simplyblock_snode_reactor_irq_ticks_total`  | CPU core labels   | Ticks spent in interrupts.  |
| `simplyblock_snode_reactor_sys_ticks_total`  | CPU core labels   | Ticks spent in the kernel.  |
| `simplyblock_snode_thread_busy_ticks_total`  | CPU thread labels | Ticks the thread was busy.  |
| `simplyblock_snode_thread_idle_ticks_total`  | CPU thread labels | Ticks the thread was idle.  |

```plain title="Utilization of each reactor"
rate(simplyblock_snode_reactor_busy_ticks_total[5m])
  / (rate(simplyblock_snode_reactor_busy_ticks_total[5m]) + rate(simplyblock_snode_reactor_idle_ticks_total[5m]))
```

### Replication

Each logical volume that replicates to another cluster has the following gauges, with the replication labels:

| Metric                                      | Description                                                                                                                    |
|---------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| `simplyblock_replication_lag_seconds`       | Age of the newest snapshot that has been fully replicated. Absent before the first one.                                        |
| `simplyblock_replication_backlog_bytes`     | Bytes of snapshots that are queued and not yet shipped.                                                                        |
| `simplyblock_replication_last_sync_seconds` | Duration of the last completed shipping cycle.                                                                                 |
| `simplyblock_replication_last_sync_bytes`   | Size of the last shipped snapshot.                                                                                             |
| `simplyblock_replication_rpo_violation`     | 1 while the lag exceeds the recovery point objective of the policy, 0 otherwise. Absent when the policy declares no objective. |
| `simplyblock_replication_degraded`          | 1 while the replication is degraded or in error, 0 otherwise.                                                                  |

```plain title="Volumes that miss their recovery point objective"
simplyblock_replication_rpo_violation == 1
```

See [Asynchronous Replication](../data-protection/asynchronous-replication.md) for the replication policies.

### Storage Node Latency Probe

When automatic volume rebalancing is enabled, a probe on each storage node measures the write latency of the node
with small random writes. Its results are scraped as the job `simplyblock_rebalancer_probe`:

| Metric                                      | Labels            | Description                                |
|---------------------------------------------|-------------------|--------------------------------------------|
| `simplyblock_node_fio_write_latency_p50_ns` | `cluster`, `node` | Median latency of 4K random writes, in ns. |
| `simplyblock_node_fio_write_latency_p99_ns` | `cluster`, `node` | 99th percentile of the same, in ns.        |

## Simplyblock Operator Metrics

The operator registers its metrics with its own metrics endpoint. The endpoint is turned on with the operator
argument `--metrics-bind-address`, for example, `:8443` for HTTPS, and is off when the argument is not set.

!!! note
    The Helm chart of the Simplyblock Operator does not set `--metrics-bind-address`, so these metrics are not
    exposed by a default installation, and the Prometheus of the control plane does not scrape them.

The metrics are named after the resource they describe. The `*_phase_state` gauges are 1 on the series whose `phase`
label is the current phase and 0 on the others. The `*_operations_total` counters and `*_duration_seconds` histograms
cover the `*Ops` resources, with the labels `action` and `result` (`succeeded`, `failed`, or `aborted`).

| Area               | Metrics                                                                                                                                                                                                                                           | Labels                                                              |
|--------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------|
| Storage devices    | `simplyblock_storagedevice_capacity_bytes`, `_used_bytes`, `_phase_state`                                                                                                                                                                         | `cluster`, `node`, `device`, (`phase`)                              |
| Device health      | `simplyblock_storagedevice_performance_state`, `_smart_state`, `_latency_ratio`, `_iops_share_ratio`                                                                                                                                              | `cluster`, `node`, `device`, (`verdict`)                            |
| Storage nodes      | `simplyblock_storagenode_phase_state`, `_devices_count`, `_devices_failed_count`, `_network_attached_state`, `_network_host_reachable_state`, `_provisioning_duration_seconds`                                                                    | `cluster`, `node`, (`phase`, `network`)                             |
| Node operations    | `simplyblock_storagenode_operations_total`, `_operation_duration_seconds`, `_operation_step_duration_seconds`, `_operation_lock_wait_seconds`, `_drain_volumes_migrated_total`, `_drain_blocked_volumes_count`, `_maintenance_hold_seconds`       | `cluster`, `action`, `result`, `step`, `reason`                     |
| Storage clusters   | `simplyblock_storagecluster_phase_state`, `_operations_total`, `_operation_duration_seconds`, `_operation_step_duration_seconds`, `_rolling_restart_node_index_count`, `_rolling_restart_node_count`                                              | `cluster`, `phase`, `action`, `result`, `step`                      |
| Superclusters      | `simplyblock_supercluster_member_count`, `_capacity_bytes`, `_placement_decisions_total`, `_placement_duration_seconds`                                                                                                                           | `namespace`, `supercluster`, `state`, `kind`, `cluster`, `result`   |
| Storage pools      | `simplyblock_storagepool_capacity_bytes`, `_used_bytes`, `_provisioned_bytes`, `_volumes_count`, `_bound_volumes_count`, `_storageclasses_count`, `_phase_state`, `_operations_total`                                                             | `cluster`, `pool`, (`phase`, `action`, `result`)                    |
| Persistent volumes | `simplyblock_persistentvolume_operations_total`, `_operation_duration_seconds`, `_operation_step_duration_seconds`, `_operation_queued_seconds`                                                                                                   | `cluster`, `action`, `result`, `step`                               |
| Backups            | `simplyblock_storagebackup_completions_total`, `_duration_seconds`, `_size_bytes`, `_age_seconds`, `_available_count`, `_operations_total`, `simplyblock_storagebackuppolicy_attached_claims_count`, `simplyblock_group_restore_duration_seconds` | `cluster`, `policy`, `claim`, `action`, `result`                    |
| Volume rebalancing | `simplyblock_rebalancer_evaluation_total`, `_migrations_total`, `_pinned_blocked_total`, `_max_latency_deviation_pct`, `_node_latency_deviation_pct`, `_baseline_ns`, `_cooldown_volumes`                                                         | `cluster`, `node`, `result`, `source_node`, `target_node`           |
| Control plane      | `simplyblock_controlplane_ready_state`, `_component_ready_count`, `_component_desired_count`, `_probe_duration_seconds`, `_probe_failures_total`, `_operations_total`                                                                             | `namespace`, `component`, `essential`, `reason`, `action`, `result` |
| CSI driver         | `simplyblock_simplyblockdriver_version_info`, `_nodes_ready_count`, `_nodes_expected_count`, `_controller_ready_state`                                                                                                                            | `namespace`, `version`                                              |
| Deployment         | `simplyblock_clusterdeploymentconfig_phase_state`, `_expansion_duration_seconds`, `_nodes_created_total`, `simplyblock_operator_discovery_workers_found_count`, `_discovery_devices_found_count`                                                  | `namespace`, `name`, `phase`, `reason`                              |

In the table, a name that starts with an underscore continues the prefix of the first metric of its row. The device
health metrics are described in [Device Health](device-health.md#events-and-metrics).
