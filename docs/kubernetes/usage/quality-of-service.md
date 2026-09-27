---
title: "Defining Quality of Service"
description: "Set per-volume IOPS and throughput ceilings for simplyblock volumes through pool volume defaults, StorageClass parameters, or PVC annotations."
weight: 40600
---

Simplyblock's CSI driver supports QoS (Quality of Service) limits on logical volumes: a combined IOPS ceiling and
throughput ceilings for reads and writes together, reads alone, and writes alone. The limits of a volume are fixed when
the volume is created. They come from the StorageClass the claim uses, and each of them can be overridden per claim by
an annotation.

Per-volume limits are distinct from the limits of a whole `StoragePool` (`spec.limits`), which cap the pool as a
budget. See [Multi-Tenancy](../operations/security/multi-tenancy.md) for pool limits.

## Option 1: StorageClass

Using StorageClass instances, QoS limits can be defined for all volumes sharing the same StorageClass. This enables the
definition of performance classes for the users of a pool.

For a pool, the limits are normally stated in `StoragePool.spec.volumeDefaults` (`iops` and `throughput.readWrite`,
`throughput.read`, `throughput.write`), and the StorageClass of the pool carries them under the parameter keys below
(see [Storage Class](storage-class.md)).

```yaml title="Example of a StorageClass with QoS limits"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: tenant-a-qos
  labels:
    storage.simplyblock.io/namespace: simplyblock
    storage.simplyblock.io/cluster: production
    storage.simplyblock.io/pool: tenant-a
provisioner: csi.simplyblock.io
parameters:
  cluster_id: <CLUSTER_UUID>
  pool_name: tenant-a
  max_iops: "1000"
  max_mbytes_per_sec: "125"
  max_read_mbytes_per_sec: "125"
  max_write_mbytes_per_sec: "125"
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
```

## Option 2: PVC Annotations

If more control is required, simplyblock supports defining QoS limits on a per-PVC basis using annotations. When a
ceiling is set both on the StorageClass and on the PVC, the annotation wins. Like the StorageClass values, the limits
are fixed at volume creation time.

```yaml title="Example of a PVC with QoS annotations"
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: my-pvc
  annotations:
    storage.simplyblock.io/max-iops: "1000"
    storage.simplyblock.io/max-mbytes-per-sec: "125"
    storage.simplyblock.io/max-read-mbytes-per-sec: "125"
    storage.simplyblock.io/max-write-mbytes-per-sec: "125"
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: simplyblock-simplyblock-production
```

## QoS Parameters

All parameters are optional. An unset ceiling, or `0`, means no limit. There is no read-only or write-only IOPS
ceiling, because the control plane enforces one combined IOPS limit.

| Pool `volumeDefaults` field | StorageClass Parameter     | PVC Annotation                                    | Description                      |
|-----------------------------|----------------------------|---------------------------------------------------|----------------------------------|
| `iops`                      | `max_iops`                 | `storage.simplyblock.io/max-iops`                 | Max read+write IOPS              |
| `throughput.readWrite`      | `max_mbytes_per_sec`       | `storage.simplyblock.io/max-mbytes-per-sec`       | Max read+write throughput (MB/s) |
| `throughput.read`           | `max_read_mbytes_per_sec`  | `storage.simplyblock.io/max-read-mbytes-per-sec`  | Max read throughput (MB/s)       |
| `throughput.write`          | `max_write_mbytes_per_sec` | `storage.simplyblock.io/max-write-mbytes-per-sec` | Max write throughput (MB/s)      |

!!! note
    Annotation values override StorageClass values per parameter. Use annotations only for the values to be
    overridden.

## Legacy Keys

StorageClasses and claims written for earlier versions keep working. The older keys are still read, and when an
object carries more than one spelling of the same ceiling, the newest one wins.

| Current key                                                                    | Legacy StorageClass parameter | Legacy annotations                                     |
|--------------------------------------------------------------------------------|-------------------------------|--------------------------------------------------------|
| `max_iops` / `storage.simplyblock.io/max-iops`                                 | `qos_rw_iops`                 | `simplyblock.io/qos-rw-iops`, `simplybk/qos-rw-iops`   |
| `max_mbytes_per_sec` / `storage.simplyblock.io/max-mbytes-per-sec`             | `qos_rw_mbytes`               | `simplyblock.io/qos-rw-mbps`, `simplybk/qos-rw-mbytes` |
| `max_read_mbytes_per_sec` / `storage.simplyblock.io/max-read-mbytes-per-sec`   | `qos_r_mbytes`                | `simplyblock.io/qos-r-mbps`, `simplybk/qos-r-mbytes`   |
| `max_write_mbytes_per_sec` / `storage.simplyblock.io/max-write-mbytes-per-sec` | `qos_w_mbytes`                | `simplyblock.io/qos-w-mbps`, `simplybk/qos-w-mbytes`   |

New StorageClasses and claims should use the current keys.
