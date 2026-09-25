---
title: "Storage Class"
description: "How simplyblock StorageClasses are assigned to a StoragePool by labels, how pool volumeDefaults map to class parameters, and which parameters the CSI driver reads."
weight: 30400
---

A Kubernetes StorageClass defines the way dynamic storage provisioning is handled within a cluster. When a
PersistentVolumeClaim (PVC) references a StorageClass, Kubernetes provisions a PersistentVolume (PV) according to the
class's parameters. With simplyblock, a StorageClass draws from one `StoragePool` of one `StorageCluster`, and its
parameters describe the volumes the CSI driver creates in that pool: QoS ceilings, encryption, filesystem, and more.

## How Simplyblock Uses StorageClass

The CSI driver `csi.simplyblock.io` reads the class parameters at volume creation and asks the simplyblock control
plane for a logical volume in the named cluster and pool. Kubernetes does not allow the parameters of a StorageClass
to change after creation, so the settings of a class hold for every volume provisioned from it.

A class and a pool are joined by three labels on the class. All three are required, because a pool name is only unique
within one namespace and one cluster:

| Label                              | Value                                     |
|------------------------------------|-------------------------------------------|
| `storage.simplyblock.io/namespace` | Namespace of the `StoragePool`.           |
| `storage.simplyblock.io/cluster`   | Name of the `StorageCluster` of the pool. |
| `storage.simplyblock.io/pool`      | Name of the `StoragePool`.                |

A pool may have any number of classes, and each class may be named freely. The pool lists the classes assigned to it
in `status.storageClassNames`.

## StorageClass Created by a Storage Pool

The operator writes exactly one StorageClass itself: the class of a cluster's default pool `<cluster>-default`, named
`simplyblock-<namespace>-<cluster>`. It carries the three labels and the label
`storage.simplyblock.io/managed-by=storagecluster`, uses `volumeBindingMode: WaitForFirstConsumer`,
`reclaimPolicy: Delete`, and `allowVolumeExpansion: true`, and is not marked as the default class of the Kubernetes
cluster. Its name is recorded in the pool's `status.defaultStorageClassName`.

The class is written once. When it is deleted, it is not recreated. When a class of that name already exists and is
not the operator's, the pool gets no default class and a `StorageClassNameTaken` event is emitted.

## Authoring a StorageClass for a Pool

For every other pool, the StorageClass is written by an administrator. It carries the three labels, `cluster_id`
(the `StorageCluster.status.uuid`), and `pool_name`, and the parameters that correspond to the pool's volume defaults.

```yaml title="Example of a StoragePool and its authored StorageClass (tenant-a.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StoragePool
metadata:
  name: tenant-a
  namespace: simplyblock
spec:
  clusterRef: production
  limits:
    capacity: 10T
    iops: 200000
  volumeDefaults:
    iops: 20000
    throughput:
      readWrite: 512
    filesystem: xfs
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: tenant-a-fast
  labels:
    storage.simplyblock.io/namespace: simplyblock
    storage.simplyblock.io/cluster: production
    storage.simplyblock.io/pool: tenant-a
provisioner: csi.simplyblock.io
parameters:
  cluster_id: <CLUSTER_UUID>
  pool_name: tenant-a
  max_iops: "20000"
  max_mbytes_per_sec: "512"
  csi.storage.k8s.io/fstype: xfs
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

```bash title="Reading the cluster UUID for cluster_id"
kubectl get storagecluster production -n simplyblock -o jsonpath='{.status.uuid}'
```

A class without the labels still provisions volumes, but the pool does not know about it. Such a class is not listed
in `status.storageClassNames`, and it cannot be chosen when the operator needs a class for a pool, for example, for a
[restored backup](../operations/data-protection/backup-recovery.md#restoring-a-backup).

## Pool Volume Defaults and Class Parameters

`StoragePool.spec.volumeDefaults` states what every volume of the pool is created with. The block is immutable once
set, because the parameters of a StorageClass are. A pool with different defaults is a new pool. The operator writes
the defaults of the default pool into its class with the mapping below, and an authored class for a pool uses the same
keys:

| `volumeDefaults` field      | StorageClass parameter      |
|-----------------------------|-----------------------------|
| `iops`                      | `max_iops`                  |
| `throughput.readWrite`      | `max_mbytes_per_sec`        |
| `throughput.read`           | `max_read_mbytes_per_sec`   |
| `throughput.write`          | `max_write_mbytes_per_sec`  |
| `enableEncryption`          | `encryption`                |
| `enableCompression`         | `compression`               |
| `enableClientCompression`   | `client_compression`        |
| `enableClientDeduplication` | `client_deduplication`      |
| `enableReplication`         | `replicate`                 |
| `maxNamespacesPerSubsystem` | `max_namespace_per_subsys`  |
| `priorityClass`             | `priority_class`            |
| `filesystem`                | `csi.storage.k8s.io/fstype` |
| `fabric`                    | `fabric`                    |
| `tune2fsReservedBlocks`     | `tune2fs_reserved_blocks`   |
| `enableDHCHAP`              | `dhchap_node_selector`      |

`filesystem` defaults to `xfs`. For `enableDHCHAP`, the parameter value is the node label key of the pool's allowed
nodes, `storage.simplyblock.io/storage-pool.<POOL_UUID>`, and it is only written when `allowedNodes` is non-empty (see
[Host Authentication and Encryption](../operations/security/authentication-encryption.md)).

!!! note
    `compression`, `replicate`, and `priority_class` are written into the class for completeness. The CSI driver
    does not forward them when it creates a volume.

## StorageClass Parameters

The erasure coding schema (the number of data and parity chunks per stripe) is set once at cluster creation and
applies to all volumes in the cluster. It cannot be configured per volume or through a StorageClass. See the
[Erasure Coding Configuration](../../deployment-preparation/erasure-coding-scheme.md) for more details.

See [Defining Quality of Service](quality-of-service.md) for QoS limits and their per-claim overrides.

## Namespace Volumes

For a definition of namespace volumes, as well as the advantages and disadvantages of NVMe namespaces versus NVMe
subsystems, see [Logical Volumes](../../architecture/concepts/logical-volumes.md).

Namespace volumes are enabled through `max_namespace_per_subsys` alone. A value above one makes every volume of the
storage class a namespace volume, sharing an NVMe subsystem with up to `<n>` siblings. At the default of one, each
volume receives its own subsystem.

!!! warning
    A namespace volume cannot be migrated or rebalanced on its own, because moving it would disturb every other
    volume sharing its subsystem.

## Available Parameters

The parameters below are read by the CSI driver. A parameter that is omitted leaves the choice to the control plane,
for example, the cluster's fabric or no QoS ceiling.

!!! warning
    `tune2fs_reserved_blocks` is skipped only when it is absent. A value of `0` is not a no-op, it runs
    `tune2fs -m 0` on every volume and removes the reserve that `mkfs` would have kept.

| Parameter Name            | Value Type | Description                                                                                                                                         |
|---------------------------|------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| cluster_id                | string     | UUID of the backing storage cluster. Required unless `zone_cluster_map` or `region_cluster_map` is used.                                            |
| zone_cluster_map          | string     | JSON map of Kubernetes zone to simplyblock cluster UUID (for topology-aware multi-cluster provisioning).                                            |
| region_cluster_map        | string     | JSON map of Kubernetes region to simplyblock cluster UUID (for topology-aware multi-cluster provisioning).                                          |
| pool_name                 | string     | Name of the simplyblock storage pool. Required.                                                                                                     |
| fabric                    | string     | Fabric type to connect to the storage cluster, `tcp` or `rdma`. Defaults to the cluster's fabric.                                                   |
| csi.storage.k8s.io/fstype | string     | Filesystem to format the logical volume with. If not specified, a raw block device is given to the container.                                       |
| max_size                  | string     | Caps the size a logical volume of this storage class can grow to. Accepts size suffixes, for example, `10G`.                                        |
| max_iops                  | int        | Maximum read and write IOPS of a volume. `0` means no maximum.                                                                                      |
| max_mbytes_per_sec        | int        | Maximum read and write throughput of a volume, in MB/s. `0` means no maximum.                                                                       |
| max_read_mbytes_per_sec   | int        | Maximum read throughput of a volume, in MB/s. `0` means no maximum.                                                                                 |
| max_write_mbytes_per_sec  | int        | Maximum write throughput of a volume, in MB/s. `0` means no maximum.                                                                                |
| encryption                | bool       | Whether the volumes of this storage class are encrypted. Defaults to `false`.                                                                       |
| client_compression        | bool       | Compresses each volume on the consuming node (VDO). The volume is pinned to a node that can run dm-vdo.                                             |
| client_deduplication      | bool       | Deduplicates each volume on the consuming node (VDO). The volume is pinned to a node that can run dm-vdo.                                           |
| max_namespace_per_subsys  | int        | Number of namespaces per NVMe subsystem. Defaults to `1`.                                                                                           |
| tune2fs_reserved_blocks   | int        | Reserved-blocks percentage applied through `tune2fs -m` when an ext4 volume is staged. Left unset, tune2fs is skipped entirely.                     |
| dhchap_node_selector      | string     | Node label key of the allowed nodes of a DHCHAP pool. The PersistentVolume's node affinity is restricted to nodes with that label set to `allowed`. |

### Legacy Parameter Keys

StorageClasses written for earlier operator versions keep working, because their parameters cannot be changed. The
following older keys are still read. When a class carries both spellings of one ceiling, the new key wins.

| Legacy parameter | Current parameter          |
|------------------|----------------------------|
| `qos_rw_iops`    | `max_iops`                 |
| `qos_rw_mbytes`  | `max_mbytes_per_sec`       |
| `qos_r_mbytes`   | `max_read_mbytes_per_sec`  |
| `qos_w_mbytes`   | `max_write_mbytes_per_sec` |

The parameter name `dhchap_node_label`, which appeared in earlier documentation, is not read. A DHCHAP class names
the node label through `dhchap_node_selector`.

The per-pool StorageClass `simplyblock-<namespace>-<cluster>-<pool>` that earlier operator versions generated for
every pool is no longer created. Such classes keep provisioning, and new pools get authored classes.
