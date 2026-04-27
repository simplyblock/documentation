---
title: "Defining Quality of Service"
description: "Defining Quality of Service: Simplyblock's Kubernetes CSI driver supports Quality of Service (QoS) to define minimum guaranteed performance characteristics of a."
weight: 40600
---

Simplyblock's CSI driver supports QoS limits on logical volumes. There are two ways to set them.

## Option 1: StorageClass

QoS applies to all volumes using the StorageClass. Values are fixed at creation time.

```yaml title="StorageClass with QoS"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: qos-volumes
provisioner: csi.simplyblock.io
parameters:
  qos_rw_iops: 1000
  qos_rw_mbytes: 125
  qos_r_mbytes: 125
  qos_w_mbytes: 125
reclaimPolicy: Delete
volumeBindingMode: Immediate
```

## Option 2: PVC Annotations

Use this for per-volume QoS without creating a dedicated StorageClass. Set annotations on the PVC before it is provisioned — values are locked in at volume creation time.

```yaml title="PVC with QoS annotations"
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: my-pvc
  annotations:
    simplybk/qos-rw-iops: "1000"
    simplybk/qos-rw-mbytes: "125"
    simplybk/qos-r-mbytes: "125"
    simplybk/qos-w-mbytes: "125"
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: simplyblock-csi-sc
```

## QoS Parameters

All parameters are optional. Default is `0` (no limit).

| Parameter / Annotation          | Description                          |
|---------------------------------|--------------------------------------|
| `qos_rw_iops` / `simplybk/qos-rw-iops`       | Max read+write IOPS      |
| `qos_rw_mbytes` / `simplybk/qos-rw-mbytes`   | Max read+write throughput (MB/s) |
| `qos_r_mbytes` / `simplybk/qos-r-mbytes`     | Max read throughput (MB/s)  |
| `qos_w_mbytes` / `simplybk/qos-w-mbytes`     | Max write throughput (MB/s) |

!!! note
    Annotation values override StorageClass values per parameter. You can annotate only the ones you want to override.
