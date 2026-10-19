---
title: "Defining Quality of Service"
description: "Defining Quality of Service: Simplyblock's Kubernetes CSI driver supports Quality of Service (QoS) to define minimum guaranteed performance characteristics of a."
source: "https://docs.simplyblock.io/latest/kubernetes/usage/quality-of-service/"
---

# Defining Quality of Service

Simplyblock's CSI driver supports QoS (Quality of Service) limits on logical volumes.

To configure the QoS limits, simplyblock offers the following two options.

## Option 1: StorageClass

Using StorageClass instances, QoS limits can be defined for all volumes sharing the same StorageClass. This enables
the definition of paid performance classes for the user.

With applying a StorageClass, the QoS limits are locked in at volume creation time.

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

If more control is required, simplyblock supports defining QoS limits on a per-PVC basis using Kubernetes PVC
annotations.

When using PVC annotations, no definition inside a StorageClass is required. If both are defined, PVC annotations take
precedence.

Like with StorageClass definitions, the QoS limits are locked in at volume creation time.

```yaml title="PVC with QoS annotations"
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: my-pvc
  annotations:
    simplyblock.io/qos-rw-iops: "1000"
    simplyblock.io/qos-rw-mbps: "125"
    simplyblock.io/qos-r-mbps: "125"
    simplyblock.io/qos-w-mbps: "125"
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

| StorageClass Parameter | Annotation                   | Description                      |
|------------------------|------------------------------|----------------------------------|
| `qos_rw_iops`          | `simplyblock.io/qos-rw-iops` | Max read+write IOPS              |
| `qos_rw_mbytes`        | `simplyblock.io/qos-rw-mbps` | Max read+write throughput (MB/s) |
| `qos_r_mbytes`         | `simplyblock.io/qos-r-mbps`  | Max read throughput (MB/s)       |
| `qos_w_mbytes`         | `simplyblock.io/qos-w-mbps`  | Max write throughput (MB/s)      |

!!! note
    Annotation values override StorageClass values per parameter. Use annotations only for the values to be
    overridden.

!!! warning "Deprecated annotations"
    The `simplybk/` annotations are deprecated. Existing PVCs using them continue to work for backward
    compatibility, but new deployments have to use the `simplyblock.io/` annotations. The throughput
    annotations were also renamed, so the deprecated names are not a plain prefix exchange:

    | Deprecated Annotation    | Annotation                   |
    |--------------------------|------------------------------|
    | `simplybk/qos-rw-iops`   | `simplyblock.io/qos-rw-iops` |
    | `simplybk/qos-rw-mbytes` | `simplyblock.io/qos-rw-mbps` |
    | `simplybk/qos-r-mbytes`  | `simplyblock.io/qos-r-mbps`  |
    | `simplybk/qos-w-mbytes`  | `simplyblock.io/qos-w-mbps`  |
