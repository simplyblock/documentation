---
title: "Monitoring"
description: "Monitor a simplyblock cluster on Kubernetes through the status of its custom resources, the capacity metrics API, Grafana dashboards, alerts, and Graylog."
weight: 10600
---

Monitoring the health, performance, and resource utilization of a simplyblock cluster is crucial for ensuring optimal
operation, early issue detection, and efficient capacity planning. On Kubernetes, the first source is the status of
the simplyblock custom resources, which the Simplyblock Operator keeps current: the control plane, the storage
cluster, its storage nodes, devices, and pools. Capacity readings are served as Kubernetes resources of their own
through the metrics API `metrics.simplyblock.io/v1alpha2`. Performance history, alerting, and logs are provided by the
optional observability stack of the control plane (Prometheus, Grafana, and Graylog), and the `{{ cliname }}` command
line interface remains available for detailed diagnosis.

## Monitoring Objectives

The monitoring stack should answer four operational questions:

- Is the cluster healthy and reachable?
- Are storage nodes and logical volumes in expected state?
- Is performance within expected latency and throughput ranges?
- Are alert channels configured and actively delivering events?

## Recommended First Checks

When investigating a possible incident, start in this order:

1. Verify the control plane and its components (`kubectl get cp`).
2. Verify overall cluster health and status (`kubectl get stc`, `kubectl get sn`).
3. Check active alerts for immediate failures or capacity thresholds.
4. Inspect storage devices and logical volume conditions.
5. Review I/O statistics for bottlenecks and saturation patterns.
6. Use dashboards and logs for deeper root-cause analysis.

```bash title="First checks of a simplyblock deployment"
kubectl -n simplyblock get controlplane,storagecluster,storagenodes,storagepools
```

## Resource Status at a Glance

| Resource            | Short name | Health fields                                                                                                |
|---------------------|------------|--------------------------------------------------------------------------------------------------------------|
| `ControlPlane`      | `cp`       | `status.phase` (`Installing`, `Available`, `Degraded`, `Unavailable`), `status.components`, `status.version` |
| `StorageCluster`    | `stc`      | `status.phase`, `status.status` (backend state), `status.maxFaultTolerance`, `status.tasks`                  |
| `StorageNode`       | `sn`       | `status.phase`, `status.status`, `status.health`, `status.resources`                                         |
| `StorageDevice`     | `sd`       | `status.phase` (`Online`, `Degraded`, `Unknown`, `Removed`, `Failed`), `status.deviceStatus`                 |
| `StoragePool`       | `sp`       | `status.phase` (`Pending`, `Ready`, `Deleting`), `status.limits`                                             |
| `SimplyblockDriver` | `sbd`      | `status.phase`, `status.nodesReady`, `status.nodesTotal`, `status.controllerReady`                           |

Every status carries a `message` with the latest human-readable finding. The details of each resource are covered in
[Cluster Health](cluster-health.md).

## Capacity Metrics API

The Simplyblock Operator serves capacity readings through an aggregated Kubernetes API, `metrics.simplyblock.io/v1alpha2`.
The readings are read-only, computed on request from the control plane's metrics, and are not stored as custom
resources. The API is enabled by default through the Helm value `metricsAPI.enabled`.

| Kind                    | Short name | Named after and located with                | Fields besides `capacity`                      |
|-------------------------|------------|---------------------------------------------|------------------------------------------------|
| `StorageClusterMetrics` | `scm`      | The `StorageCluster`                        | `clusterID`, `erasureCodingScheme`             |
| `StorageNodeMetrics`    | `snm`      | The `StorageNode`                           | `nodeID`, `storageCluster`, `workerNode`       |
| `StoragePoolMetrics`    | `spm`      | The `StoragePool`                           | `poolID`, `clusterID`                          |
| `StorageDeviceMetrics`  | `sdm`      | The `StorageDevice`                         | `deviceID`, `storageNode`                      |
| `LogicalVolumeMetrics`  | `lvm`      | The PersistentVolumeClaim, in its namespace | `volumeHandle`, `persistentVolume`, `poolName` |

Each reading carries a `timestamp` and a `capacity` block with `total`, `used`, `free`, `provisioned`, and
`utilizationPercent`, where the sizes are Kubernetes quantities.

```bash title="Reading the capacity of the cluster, its nodes, pools, and devices"
kubectl -n simplyblock get scm,snm,spm,sdm
```

```bash title="Reading the capacity of one volume from its claim's namespace"
kubectl -n my-app get lvm data -o yaml
```

The readings are namespaced, so access follows ordinary Kubernetes RBAC. The operator aggregates `get` and `list` on all
five resources into the built-in `view` role. A tenant bound to `view` in an application namespace sees the
`LogicalVolumeMetrics` of the claims in that namespace, while the cluster, node, pool, and device readings reach whoever
administers the namespace of the `StorageCluster`.

## Monitoring Areas

| Area                  | Typical Signals                                             | Primary Source                 |
|-----------------------|-------------------------------------------------------------|--------------------------------|
| Cluster health        | degraded/suspended/offline state, failing health checks     | `kubectl` status, CLI, Grafana |
| Capacity              | critical/warning capacity thresholds, provisioning pressure | Metrics API, alerts            |
| Storage node status   | unreachable/offline nodes, node-level anomalies             | `kubectl get sn`, alerts       |
| Logical volume status | volume health/offline conditions                            | Metrics API, CLI, Grafana      |
| Performance           | throughput, IOPS, latency trends                            | CLI, Grafana                   |
| Events and logs       | operational events, service/component errors                | `kubectl get events`, Graylog  |

## Monitoring Guides

- [Cluster Health](cluster-health.md)
- [Logical Volume Conditions](lvol-conditions.md)
- [Alerting](alerts.md)
- [Accessing Grafana](accessing-grafana.md)
- [Accessing Graylog](accessing-graylog.md)
