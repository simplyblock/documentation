---
title: "Storage Class"
description: "Storage Class: A Kubernetes StorageClass defines the way dynamic storage provisioning is handled within a cluster."
source: "https://docs.simplyblock.io/latest/kubernetes/usage/storage-class/"
---

# Storage Class

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

## StorageClass Created by a Storage Pool

A StorageClass named `simplyblock-<namespace>-<clusterName>-<poolName>` is created automatically by the operator once
a `StoragePool` resource becomes active, as described in
[Create a Storage Pool](../installation/k8s-storage-plane.md#create-a-storage-pool). `cluster_id` and `pool_name` are
always set from the storage pool and cannot be overridden. The rest of the parameters are copied from
`StoragePool.spec.storageClassParameters`. Defaults for each field are listed at
[Simplyblock Operator: StorageClassParameters](../../reference/operator/reference.md#storageclassparameters).

The CRD fields carry camel case names and are written to the StorageClass under the parameter names of the CSI driver:

| `storageClassParameters` Field | StorageClass Parameter      |
|--------------------------------|-----------------------------|
| `qosRwIops`                    | `qos_rw_iops`               |
| `qosRwMbytes`                  | `qos_rw_mbytes`             |
| `qosRMbytes`                   | `qos_r_mbytes`              |
| `qosWMbytes`                   | `qos_w_mbytes`              |
| `compression`                  | `compression`               |
| `encryption`                   | `encryption`                |
| `replicate`                    | `replicate`                 |
| `lvolPriorityClass`            | `lvol_priority_class`       |
| `fabric`                       | `fabric`                    |
| `maxNamespacePerSubsys`        | `max_namespace_per_subsys`  |
| `tune2fsReservedBlocks`        | `tune2fs_reserved_blocks`   |
| `filesystem`                   | `csi.storage.k8s.io/fstype` |

For a storage pool with `dhchap` enabled and `allowedNodes` set, `dhchap_node_label` is added by the operator as well,
and the generated StorageClass is restricted to those nodes through its allowed topologies.

Kubernetes does not allow the `parameters` of a StorageClass to be changed after creation, so
`StoragePool.spec.storageClassParameters` is immutable once the storage pool is created. There is no supported way to
reconfigure the generated StorageClass afterward. A new storage pool has to be created to provision volumes with
different defaults.

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
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

## StorageClass Parameters

The erasure coding schema (the number of data and parity chunks per stripe) is set once at cluster creation and
applies to all volumes in the cluster. It cannot be configured per volume or through a StorageClass.

See the [Erasure Coding Configuration](../../deployment-preparation/erasure-coding-scheme.md) for more details.

See here how to configure [Service Classes](../../non-kubernetes/operations/volumes/qos-service-classes.md) and [QoS Limits](../../non-kubernetes/operations/volumes/limiting-iops-and-throughput.md).

## Namespace Volumes

For a definition of namespace volumes, as well as the advantages and disadvantages of NVMe namespaces versus NVMe
subsystems, see [Logical Volumes](../../architecture/concepts/logical-volumes.md).

Namespace volumes are enabled through `max_namespace_per_subsys` alone. A value above one makes every volume of
the storage class a namespace volume, sharing an NVMe subsystem with up to `<n>` siblings. At the default of one,
each volume receives its own subsystem.

!!! warning
    A namespace volume cannot be migrated or rebalanced on its own, because moving it would disturb every other
    volume sharing its subsystem.

## Available Parameters

A default in the table below is applied by the operator when it generates a StorageClass from a storage pool. A
hand-written StorageClass that omits the parameter leaves the choice to the control plane.

!!! warning
    `tune2fs_reserved_blocks` is skipped only when it is absent. A value of `0` is not a no-op, it runs
    `tune2fs -m 0` on every volume and removes the reserve that `mkfs` would have kept.

| Parameter Name            | Value Type | Description                                                                                                                                                                                    | Optional | Default |
|---------------------------|------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|---------|
| cluster_id                | string     | Defines the backing cluster id for the storage class. Required unless `zone_cluster_map` or `region_cluster_map` is used.                                                                      | true     |         |
| zone_cluster_map          | string     | JSON map of Kubernetes zone to simplyblock cluster id (for topology-aware multi-cluster provisioning).                                                                                         | true     |         |
| region_cluster_map        | string     | JSON map of Kubernetes region to simplyblock cluster id (for topology-aware multi-cluster provisioning).                                                                                       | true     |         |
| fabric                    | string     | Defines the fabric type to connect to the storage cluster. Valid values are `tcp` and `rdma`.                                                                                                  | true     | `tcp`   |
| csi.storage.k8s.io/fstype | string     | Defines the filesystem to format the logical volume. If not specific, a raw block device is given to the container.                                                                            | true     |         |
| pool_name                 | string     | Defines the simplyblock storage pool name to use.                                                                                                                                              | false    |         |
| max_size                  | string     | Caps the size a logical volume of this storage class can grow to. Accepts size suffixes, for example, `10G`.                                                                                   | true     |         |
| qos_rw_iops               | int        | Defines the maximum IOPS reserved for a logical volume of this storage class. A zero (0) means no maximum.                                                                                     | true     | 0       |
| qos_rw_mbytes             | int        | Defines the maximum total throughput in megabytes reserved for a logical volume of this storage class. A zero (0) means no maximum.                                                            | true     | 0       |
| qos_r_mbytes              | int        | Defines the maximum read throughput in megabytes reserved for a logical volume of this storage class. A zero (0) means no maximum.                                                             | true     | 0       |
| qos_w_mbytes              | int        | Defines the maximum write throughput in megabytes reserved for a logical volume of this storage class. A zero (0) means no maximum.                                                            | true     | 0       |
| compression               | bool       | Defines if the logical volume of this storage class will be stored compressed or not.                                                                                                          | true     | false   |
| encryption                | bool       | Defines if the logical volume of this storage class will be encrypted or not.                                                                                                                  | true     | false   |
| replicate                 | bool       | Defines if the logical volume of this storage class will be replicated or not.                                                                                                                 | true     | false   |
| lvol_priority_class       | int        | Defines the priority class of a logical volume of this storage class.                                                                                                                          | true     | 0       |
| max_namespace_per_subsys  | int        | Defines the number of namespaces per NVMe subsystem.                                                                                                                                           | true     | 1       |
| tune2fs_reserved_blocks   | int        | Reserved-blocks percentage applied through `tune2fs -m` when the volume is staged. Left unset, tune2fs is skipped entirely.                                                                    | true     |         |
| dhchap_node_label         | string     | Node label key carried by the allowed nodes of a DHCHAP pool, restricting volumes of this class to those nodes. Set by the operator from a `StoragePool`'s `dhchap` and `allowedNodes` fields. | true     |         |
