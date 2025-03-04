---
title: "Defining Quality of Service"
weight: 40600
---

Simplyblock's Kubernetes CSI driver supports Quality of Service (QoS) to define minimum guaranteed performance
characteristics of a logical volume.

To define the QoS properties, create a [StorageClass](storage-class.md) with the required parameters.

```yaml title="StorageClass with Quality of Service"
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
  ... other parameters
reclaimPolicy: Delete
volumeBindingMode: Immediate
```

The available parameters are:

| Parameter Name            | Value Type | Description                                                                                                                         | Optional | Default  |
|---------------------------|------------|-------------------------------------------------------------------------------------------------------------------------------------|----------|----------|
| qos_rw_iops               | int        | Defines the minimum IOPS reserved for a logical volume of this storage class. A zero (0) means no minimum.                          | true     | 0        |
| qos_rw_mbytes             | int        | Defines the minimum total throughput in megabytes reserved for a logical volume of this storage class. A zero (0) means no minimum. | true     | 0        |
| qos_r_mbytes              | int        | Defines the minimum read throughput in megabytes reserved for a logical volume of this storage class. A zero (0) means no minimum.  | true     | 0        |
| qos_w_mbytes              | int        | Defines the minimum write throughput in megabytes reserved for a logical volume of this storage class. A zero (0) means no minimum. | true     | 0        |
