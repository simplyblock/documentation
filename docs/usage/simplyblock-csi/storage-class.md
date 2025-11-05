---
title: "Storage Class"
weight: 30400
---

A Kubernetes StorageClass defines the way dynamic storage provisioning is handled within a cluster. StorageClasses allow
administrators to specify different types of storage with varying performance characteristics, redundancy
configurations, and provisioning parameters. When a PersistentVolumeClaim (PVC) references a StorageClass, Kubernetes
automatically provisions a Persistent Volume (PV) according to the defined specifications.

## How Simplyblock Uses StorageClass

Simplyblock integrates with Kubernetes through its CSI (Container Storage Interface) driver and leverages StorageClasses
to manage the dynamic provisioning of Logical Volumes (LVs). The simplyblock StorageClass defines how LVs are created
within the simplyblock cluster, specifying parameters such as:

- Provisioning size
- Quality of Service (QoS)
- Encryption

When a user deploys a PVC referencing the simplyblock StorageClass, the CSI driver automatically communicates with the
simplyblock control plane to provision a logical volume matching the requested specifications. This process abstracts
the complexity of volume creation and ensures that workloads running in Kubernetes receive high-performance, resilient
block storage directly backed by simplyblock.

## Example Usage

A typical simplyblock StorageClass contains the name of the storage class, a filesystem type to automatically format
the logical volume (or provide a raw block device if missing), the
[reclaim policy](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#reclaiming){:target="_blank" rel="noopener"}.

```yaml title="Example StorageClass"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: encrypted-volumes
provisioner: csi.simplyblock.io
parameters:
  encryption: "True"
  csi.storage.k8s.io/fstype: ext4
  ... other parameters
reclaimPolicy: Delete
volumeBindingMode: Immediate
allowVolumeExpansion: true
```

## StorageClass Parameters

Each cluster has a default schema, but each volume can optionally use an alternative schema. However, the schema must
"fit" into the cluster, meaning `n+k` must be equal to (or better smaller) than the number of nodes in the cluster.

See the [Erasure Coding Configuration](../../deployments/deployment-preparation/erasure-coding-scheme.md) for more details.

See here how to configure [Service Classes] and [Qos Limits](../../usage/qos/limiting-iops-and-throughput.md). 

##Namespace Volumes

For a definition of namespace volumes, as well as the advantages and disadvantages of NVMe namespaces versus NVMe
subsystems, see [Logical Volumes](../../architecture/concepts/logical-volumes.md).

If `namespace-volumes` is set to `yes`, you also need to define the number of namespaces per subsystem (e.g.,
`max_namespace_per_subsys: <n>`). This means that for every new subsystem <n> namespaces will be created. 

## Available Parameters

| Parameter Name            | Value Type | Description                                                                                                                         | Optional | Default  |
|---------------------------|------------|-------------------------------------------------------------------------------------------------------------------------------------|----------|----------|
| cluster_id                | string     | Defines the backing cluster id the storage class.                                                                                   | true     |          |
| fabric                    | string     | Defines the fabric type to connect to the storage cluster. Valid values are `tcp` and `rdma`.                                       | true     | tcp      |
| csi.storage.k8s.io/fstype | string     | Defines the filesystem to format the logical volume. If not specific, a raw block device is given to the container.                 | true     |          |
| pool_name                 | string     | Defines the simplyblock storage pool name to use.                                                                                   | false    | testing1 |
| qos_rw_iops               | int        | Defines the minimum IOPS reserved for a logical volume of this storage class. A zero (0) means no minimum.                          | true     | 0        |
| qos_rw_mbytes             | int        | Defines the minimum total throughput in megabytes reserved for a logical volume of this storage class. A zero (0) means no minimum. | true     | 0        |
| qos_r_mbytes              | int        | Defines the minimum read throughput in megabytes reserved for a logical volume of this storage class. A zero (0) means no minimum.  | true     | 0        |
| qos_w_mbytes              | int        | Defines the minimum write throughput in megabytes reserved for a logical volume of this storage class. A zero (0) means no minimum. | true     | 0        |
| compression               | bool       | Defines if the logical volume of this storage class will be stored compressed or not.                                               | true     | false    |
| encryption                | bool       | Defines if the logical volume of this storage class will be encrypted or not.                                                       | true     | false    |
| distr_ndcs                | int        | Defines the number of data chunks for the erasure coding scheme.                                                                    | true     | 1        |
| distr_npcs                | int        | Defines the number of parity chunks for the erasure coding scheme.                                                                  | true     | 1        |
| lvol_priority_class       | int        | Defines the priority class of a logical volume of this storage class.                                                               | true     | 0        |
| max_namespace_per_subsys  | int        | Defines the number of namespaces per NVMe subsystem.                                                                                | true     | 1        |
| tune2fs_reserved_blocks   | int        | Defines the number of reserved blocks for tune2fs operations.                                                                       | true     | 0        |
