---
title: "Logical Volume Conditions"
description: "Check the capacity, health, and I/O statistics of the logical volume behind a simplyblock PersistentVolumeClaim with the metrics API, Prometheus, and the CLI."
weight: 10620
---

Logical volumes are the core storage abstraction in simplyblock, representing high-performance, distributed NVMe
block devices backed by the cluster. On Kubernetes, every PersistentVolumeClaim of the simplyblock CSI driver is backed
by one logical volume. Its capacity is readable from the claim's own namespace through the metrics API, and its health
and I/O statistics are exported as Prometheus metrics, which also feed the Grafana dashboards, and are available
through the CLI.

## Finding the Logical Volume of a Claim

The volume handle of a PersistentVolume has the form `<clusterUUID>:<poolUUID>:<volumeUUID>`, where the last part is
the UUID of the logical volume.

```bash title="Reading the volume handle of a claim"
kubectl get pv "$(kubectl get pvc my-pvc -n my-app -o jsonpath='{.spec.volumeName}')" \
  -o jsonpath='{.spec.csi.volumeHandle}'
```

## Accessing Logical Volume Capacity

The `LogicalVolumeMetrics` resource (short name `lvm`) is named after the PersistentVolumeClaim and lives in the
claim's namespace. It reports the volume handle, the PersistentVolume, the pool, and the capacity (`total`, `used`,
`free`, `provisioned`, and `utilizationPercent`).

```bash title="Reading the capacity of the volumes of a namespace"
kubectl -n my-app get lvm
```

```bash title="Reading the capacity of one volume"
kubectl -n my-app get lvm my-pvc -o yaml
```

Access follows Kubernetes RBAC, so a user bound to the built-in `view` role in the namespace can read the capacity of
the volumes there. See [Capacity Metrics API](index.md#capacity-metrics-api).

## Accessing Logical Volume Statistics

The I/O statistics of every logical volume are exported as Prometheus metrics, labeled with the PersistentVolumeClaim
the volume belongs to. They include read, write, and unmap operations, bytes, and latency, and the volume's capacity
and status. See [Prometheus Metrics](prometheus-metrics.md) for the full list and example queries.

```plain title="IOPS of the volume behind a claim"
rate(simplyblock_lvol_read_operations_total{pvc_name="data"}[5m])
  + rate(simplyblock_lvol_write_operations_total{pvc_name="data"}[5m])
```

To access a logical volume's performance and I/O statistics, the `{{ cliname }}` command line tool can be used in the
`simplyblock-admin-control` pod (see [Using the CLI](cluster-health.md#using-the-cli)):

```bash title="Accessing the statistics of a logical volume"
{{ cliname }} volume get-io-stats <VOLUME_ID>
```

All details of the command are available in the [CLI reference](../../../reference/cli/index.md). The information is
also available through Grafana in the logical volume's dashboard.

## Accessing Logical Volume Health Information

To access a logical volume's health status, the `{{ cliname }}` command line tool can be used:

```bash title="Accessing the health status of a logical volume"
{{ cliname }} volume check <VOLUME_ID>
```

All details of the command are available in the [CLI reference](../../../reference/cli/index.md).
