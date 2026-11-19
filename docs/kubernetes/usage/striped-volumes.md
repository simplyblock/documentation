---
title: "Striped Volumes"
description: "Stripe one simplyblock PersistentVolume across several storage nodes with stripe_width: requirements, configuration, snapshots, clones, expansion, and limitations."
weight: 40090
---

!!! info "Available from 26.4.0-beta6.1"
    Striped volumes require the Simplyblock Operator and Simplyblock CSI 26.4.0-beta6.1 or later.

A striped volume is one PersistentVolume made of several simplyblock logical volumes (members) of equal size, each on a
different storage node of the same cluster. The node that stages the volume attaches every member over NVMe-oF and
combines them into one block device with LVM striping (dm-striped). I/O to the volume is spread across the storage
nodes of its members, instead of being served by the one storage node that leads an ordinary volume.

Striping is meant for a single volume that needs more throughput or IOPS than one storage node delivers, for example,
a large database or analytics volume. A workload with many volumes already spreads across the storage nodes and gains
little from striping.

Striping is off by default and is enabled per StorageClass. A class without `stripe_width`, or with `stripe_width` set
to `0` or `1`, provisions ordinary volumes.

## Requirements

- The cluster has at least as many online storage nodes as the stripe width. Every member is placed on a different
  storage node, and all members of a volume are in one cluster. On a supercluster, one member cluster is chosen for
  the volume, and every member is created there.
- The cluster is not a stretched (synchronously replicated) cluster.
- The volume is used from one worker node at a time (`ReadWriteOnce` or `ReadWriteOncePod`).
- The worker node needs no additional packages. The LVM tools ship with the CSI node plugin.

## Parameters

| StorageClass parameter | `volumeDefaults` field | Description                                                                                                        |
|------------------------|------------------------|--------------------------------------------------------------------------------------------------------------------|
| `stripe_width`         | `stripeWidth`          | Number of members, `2` to `128`. Omitted, `0`, or `1` is an ordinary volume.                                       |
| `stripe_size`          | `stripeSize`           | Amount of data each member takes before the next one does. A power of two from `4Ki` to `1Mi`. Defaults to `64Ki`. |

`stripe_size` is only read when `stripe_width` is `2` or more. The upper bound of 128 is the limit of LVM striping.

A claim whose class asks for more members than the cluster has online storage nodes is refused with `InvalidArgument`
before anything is created, and the claim stays `Pending`.

## Enabling Striping Through a Storage Pool

The operator writes the StorageClass of a pool it manages from the pool's `spec.volumeDefaults`. `stripeWidth` and
`stripeSize` become `stripe_width` and `stripe_size`. An authored class for a pool uses the same parameters (see
[Storage Class](storage-class.md#pool-volume-defaults-and-class-parameters)).

```yaml title="Example of a striped StoragePool (striped-pool.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StoragePool
metadata:
  name: fast
  namespace: simplyblock
spec:
  clusterRef: production
  volumeDefaults:
    stripeWidth: 4
    stripeSize: 64Ki
    filesystem: xfs
```

`spec.volumeDefaults` is immutable, so the stripe width of a pool is fixed when the pool is created. A pool with
another width is a new pool.

The following pools are refused when they are created:

| Pool                                                                                                              | Refused by        |
|-------------------------------------------------------------------------------------------------------------------|-------------------|
| `stripeWidth` above 128                                                                                           | CRD validation    |
| `stripeSize` other than a power of two from `4Ki` to `1Mi`                                                        | CRD validation    |
| `stripeSize` without a `stripeWidth` of 2 or more                                                                 | CRD validation    |
| `stripeWidth` of 2 or more with `enableClientCompression` or `enableClientDeduplication`                          | CRD validation    |
| `stripeWidth` of 2 or more with `enableReplication`                                                               | CRD validation    |
| `stripeWidth` of 2 or more on a stretched cluster                                                                 | Admission webhook |
| `stripeWidth` above the number of storage nodes of the cluster (or of any placement-eligible supercluster member) | Admission webhook |

The storage node count is only checked once the cluster has storage nodes. A pool created together with its cluster
is accepted, and a claim that does not fit is refused when it is provisioned.

## Enabling Striping Through a StorageClass

A StorageClass that is written by hand sets `stripe_width` and, optionally, `stripe_size`.

```yaml title="Example of a striped StorageClass (striped-storageclass.yaml)"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: simplyblock-striped
  labels:
    storage.simplyblock.io/namespace: simplyblock
    storage.simplyblock.io/cluster: production
    storage.simplyblock.io/pool: fast
provisioner: csi.simplyblock.io
parameters:
  cluster_id: <CLUSTER_UUID>
  pool_name: fast
  csi.storage.k8s.io/fstype: xfs
  stripe_width: "4"
  stripe_size: "64Ki"
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

A claim on the class is written like any other claim:

```yaml title="Example of a claim on a striped StorageClass (striped-claim.yaml)"
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: analytics-data
  namespace: team-a
spec:
  storageClassName: simplyblock-striped
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 400Gi
```

For a cluster that is configured directly in the Helm chart (`csiConfig.simplybk` or `multiCluster.clusters`) without
a StoragePool, the chart's StorageClass takes `stripeWidth` and `stripeSize` next to `pool`, with the same bounds.

## How a Striped Volume Is Built

**Members:** The first member carries the claim's volume name (`pvc-<UID>`). Member `i` is named `pvc-<UID>-s<i>`,
for example, `pvc-<UID>-s1` to `pvc-<UID>-s3` for a width of four. The members appear in the control plane as ordinary
logical volumes. The PersistentVolume's volume handle is the handle of the first member with the width appended, for
example, `<CLUSTER_UUID>:<POOL_UUID>:<MEMBER0_UUID>:s4`.

**Placement:** Each member is created on a different online storage node. The first member follows an explicit
placement of the claim (see [Automatic Volume Placement](volume-placement.md)). The other members are distributed
round robin across failure domains, so consecutive members land in different failure domains where the cluster has
them.

**Size:** Each member is the requested size divided by the width, rounded up to a whole GiB. The volume reports the
width multiplied by the member size. LVM keeps a few MiB of each member for its metadata, so the usable size is
slightly below the reported size.

**QoS:** The QoS ceilings of the class are divided evenly across the members (rounded up), so the volume as a whole is
held to the ceilings of the class (see [Defining Quality of Service](quality-of-service.md)).

**Filesystem:** XFS is formatted with the stripe geometry of the volume (`su` is the stripe size, `sw` is the stripe
width). The `xfs_su` and `xfs_sw` class parameters are not used for striped volumes. ext4 and raw block volumes
(`volumeMode: Block`) are supported as well.

Encryption, QoS, `max_namespace_per_subsys`, and placement annotations apply to every member on its own.

## Expanding

A striped volume is expanded like any other volume (see [Expanding](expanding.md)). Every member is resized to the new
size divided by the width, then the node grows the LVM physical volumes, the striped logical volume, and the
filesystem. The volume keeps its width and its stripes.

## Snapshots and Clones

A `VolumeSnapshot` of a striped volume snapshots every member. A snapshot is one object in Kubernetes. In the control
plane, member snapshot `i` is named `<SNAPSHOT_NAME>-s<i>`. A restore or a clone creates every member from the matching
member of the source, and each member of the new volume lands on the storage node of its source member.

The source and the target class must have the same stripe width. Restoring or cloning a striped volume into a class of
another width, into an ordinary class, or an ordinary volume into a striped class, is refused with `InvalidArgument`.

Deleting the volume or a snapshot removes every member.

### I/O Freeze During a Snapshot

simplyblock snapshots each member on its own storage node, and there is no snapshot that is atomic across storage
nodes. To make the member snapshots one crash-consistent image, the CSI driver briefly suspends I/O on the volume while
the members are snapshotted:

1. The node that stages the volume suspends the striped device (`dmsetup suspend`). In-flight I/O completes, new I/O
   waits, and a mounted filesystem is frozen and flushed first.
2. Every member is snapshotted concurrently.
3. The device is resumed.

The suspension lasts as long as the slowest member snapshot. It is bounded by a deadline of 10 seconds, after which the
node resumes the device by itself, even if the CSI controller or the operator is unreachable. A snapshot whose freeze
did not hold for every member is discarded and retried. A clone of a live striped volume is taken under the same
freeze. A restore from a snapshot needs no freeze.

The deadline is set by the environment variable `SPDKCSI_STRIPE_FREEZE_DEADLINE` (a duration such as `5s`) of the CSI
controller. The node caps any deadline at 30 seconds. The `SimplyblockDriver` resource has no field for it.

A striped volume that is not attached anywhere is snapshotted without a freeze. A striped volume attached to more than
one node is not snapshotted (`FailedPrecondition`). If the operator cannot relay the freeze to the node, the snapshot
of an attached striped volume fails with `Unavailable` and is retried, rather than producing an inconsistent image.

!!! note
    While a volume is frozen, LVM commands on its worker node that scan devices may wait until the device is resumed,
    for at most the deadline.

## Failure Behavior

Each member is an ordinary simplyblock logical volume with its own data protection, according to the cluster's
erasure coding scheme, and its own high availability. When a storage node fails, the members it leads fail over to
their secondary nodes like any other volume, and the striped device on the worker node continues through the
members' NVMe-oF paths (see [High Availability and Fault Tolerance](../../architecture/high-availability-fault-tolerance.md)).

A striped volume depends on every member. If a member becomes unavailable beyond what its own protection covers, I/O
to the data stored on that member fails. A wider stripe involves more storage nodes in every volume, but it does not
lower the fault tolerance of each member.

If a member cannot be created during provisioning, every member that was already created is deleted, and the
provisioning is retried.

## Limitations

The following are refused for striped volumes, because each acts on a single logical volume:

| Feature                                                                                 | Refused with                            |
|-----------------------------------------------------------------------------------------|-----------------------------------------|
| [ReadWriteMany volumes](pnfs.md) (`csi.storage.k8s.io/fstype: pnfs`)                    | `InvalidArgument`                       |
| Client-side compression or deduplication (`client_compression`, `client_deduplication`) | `InvalidArgument`                       |
| Replication (`replicate: "true"` and csi-addons volume replication)                     | `InvalidArgument`, `FailedPrecondition` |
| A claim with the consistency group label                                                | `InvalidArgument`                       |
| A stretched (synchronously replicated) cluster                                          | `InvalidArgument`                       |
| csi-addons volume groups                                                                | `FailedPrecondition`                    |
| [Volume group snapshots](snapshotting.md#snapshotting-a-group-of-volumes)               | `FailedPrecondition`                    |
| Restoring or cloning across stripe widths, or between striped and ordinary              | `InvalidArgument`                       |

In addition, striped volumes are not covered by [backups](../operations/data-protection/backup-recovery.md): a
`StorageBackup` of a striped claim is refused, and a backup policy reports an error for it. A `PersistentVolumeOps`
migration or relocation of a striped volume is refused by the admission webhook.
The stripe width of an existing volume cannot be changed.
