---
title: "ReadWriteMany Volumes"
description: "Provision ReadWriteMany simplyblock volumes on Kubernetes through pNFS: enabling the metadata server, the StorageClass, node requirements, and limitations."
weight: 40080
---

{{ experimental }}

A pNFS volume is a simplyblock volume that pods on several worker nodes read and write at the same time
(`ReadWriteMany`). It carries an XFS filesystem that is shared through NFSv4.1. File metadata goes through a metadata
server, while the data is read and written directly over NVMe-oF, which keeps a shared volume close to the
performance of a block volume. The architecture is described in
[ReadWriteMany (pNFS)](../../architecture/concepts/pnfs.md).

`ReadWriteMany` is served only by pNFS volumes. A `ReadWriteMany` claim on any other StorageClass is refused,
including a claim with `volumeMode: Block`.

## Requirements

**Metadata server nodes:** At least one worker node must expose a usable `/dev/kvm`, because the metadata server runs
in a small virtual machine. On a cloud instance, this requires nested virtualization to be enabled on the instance.
The CSI node plugin checks `/dev/kvm` on every node and labels the nodes that pass with
`storage.simplyblock.io/kvm-capable=true`. A label set by hand is left untouched.

**Client nodes:** Every worker node that runs a pod using a pNFS volume needs a kernel with the pNFS block layout
driver (`CONFIG_PNFS_BLOCK`) and support for identifying NVMe namespaces to it (the `nvme_get_unique_id` function).
This is a property of the kernel build, not of its version number. Red Hat Enterprise Linux 9.8 (kernel
5.14.0-687) qualifies, while Red Hat Enterprise Linux 9.5 (kernel 5.14.0-503) does not. Red Hat-based distributions
are validated. Debian and Ubuntu are not validated yet. No NFS packages are required on the host, because the NFS
client tools ship with the CSI node plugin.

A client node that does not meet the requirements still mounts the volume, but all data is routed through the
metadata server (see [Verifying the Direct Data Path](#verifying-the-direct-data-path)).

## Enabling pNFS

pNFS is enabled on the `SimplyblockDriver` resource, by setting `spec.pnfs.mds`. Without it, every pNFS volume waits
in `Pending`. An empty object enables the metadata server with its defaults.

```yaml title="Example of a SimplyblockDriver with pNFS enabled"
apiVersion: storage.simplyblock.io/v1alpha2
kind: SimplyblockDriver
metadata:
  name: simplyblock
  namespace: simplyblock
spec:
  # ... other fields ...
  pnfs:
    mds:
      resources:
        limits:
          cpu: "2"
          memory: 2Gi
      stateSize: 1Gi
```

```bash title="Enabling pNFS with default settings"
kubectl patch simplyblockdriver simplyblock -n simplyblock \
    --type merge \
    -p '{"spec":{"pnfs":{"mds":{}}}}'
```

One metadata server is started per storage cluster, when the first pNFS volume of that cluster is provisioned. Its
pod runs in the operator's namespace and must be allowed to run privileged.

| Field                   | Description                                                                                                                                                   | Default                                                    |
|-------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------|
| `image`                 | Metadata server image.                                                                                                                                        | The image matching the operator release.                   |
| `resources`             | Requests and limits of the metadata server pod. The virtual machine gets the whole CPU cores of the CPU limit (at least one) and the memory limit less 256Mi. | CPU limit `2`, memory limit `2Gi`, memory request `512Mi`. |
| `nodeSelector`          | Additional node labels the pod is scheduled by, added to `storage.simplyblock.io/kvm-capable=true`.                                                           | -                                                          |
| `tolerations`           | Tolerations for tainted nodes.                                                                                                                                | -                                                          |
| `stateSize`             | Size of the state disk holding the NFS client-recovery database.                                                                                              | `1Gi`                                                      |
| `stateStorageClassName` | StorageClass of the state disk. It must be a simplyblock StorageClass and must not be a pNFS class. Only read when the metadata server is first created.      | A class created per storage cluster.                       |

A memory limit below `512Mi` is refused.

Without `stateStorageClassName`, a StorageClass named `simplyblock-<CLUSTER_UUID>-pnfs-mds-state` is created for each
storage cluster. It is derived from an existing simplyblock StorageClass of that cluster without its QoS limits, and
it is reserved for the metadata server: a PersistentVolumeClaim using it in any other namespace is refused.

## Creating a pNFS StorageClass

A StorageClass provisions pNFS volumes when it sets `csi.storage.k8s.io/fstype` to `pnfs`. The value selects the
volume type, not a filesystem: the volume is always formatted with XFS. A storage pool's default StorageClass is never
a pNFS class, so the class is written by an administrator, with the labels and parameters described in
[Storage Class](storage-class.md#authoring-a-storageclass-for-a-pool).

```yaml title="Example of a pNFS StorageClass (pnfs-storageclass.yaml)"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: simplyblock-shared
  labels:
    storage.simplyblock.io/namespace: simplyblock
    storage.simplyblock.io/cluster: production
    storage.simplyblock.io/pool: production-default
provisioner: csi.simplyblock.io
parameters:
  cluster_id: <CLUSTER_UUID>
  pool_name: production-default
  csi.storage.k8s.io/fstype: pnfs
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

QoS limits and `encryption` apply to pNFS volumes as to block volumes.

## Provisioning a pNFS Volume

A PersistentVolumeClaim on a pNFS class requests `ReadWriteMany` or `ReadWriteOnce`. `ReadOnlyMany` and
`volumeMode: Block` are refused.

```yaml title="Example of a ReadWriteMany PersistentVolumeClaim (shared-data.yaml)"
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared-data
  namespace: team-a
spec:
  storageClassName: simplyblock-shared
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 100Gi
```

The claim stays `Pending` until the volume is exported. For the first pNFS volume of a storage cluster, this includes
starting the metadata server. Every pod referencing the claim then mounts the same filesystem, on any worker node.

## Checking the Export State

Every pNFS volume has an `NFSExport` resource in the namespace of its claim, named `nfsexp-<VOLUME_UUID>`. Its phase
shows whether the volume can be mounted.

```bash title="Listing the pNFS exports of a namespace"
kubectl get nfsexports -n team-a
```

```plain title="Example output of the export list"
NAME                                          VOLUME                                                                                        MDS                                                      MDSPOD                                                   PHASE   AGE
nfsexp-3c81a0f4-1d2b-4e77-9a01-5f6c8b2d0e13   0f2ac1d3-7a51-4c8e-b2e9-6d1f0a3b9c47:production-default:3c81a0f4-1d2b-4e77-9a01-5f6c8b2d0e13   simplyblock-pnfs-mds-0f2ac1d3-7a51-4c8e-b2e-8d3b9c10-0   simplyblock-pnfs-mds-0f2ac1d3-7a51-4c8e-b2e-8d3b9c10-0   Ready   12m
```

| Phase        | Meaning                                                                                                   |
|--------------|-----------------------------------------------------------------------------------------------------------|
| `Pending`    | No metadata server serves the volume yet. The events name the reason.                                     |
| `Assembling` | The metadata server is attaching, formatting, and exporting the volume.                                   |
| `Ready`      | The volume can be mounted.                                                                                |
| `Degraded`   | Exporting the volume did not finish within five minutes. The operator takes no further action on its own. |

The events on the `NFSExport` resource explain a volume that does not become `Ready`:

```bash title="Showing the events of a pNFS export"
kubectl describe nfsexport nfsexp-3c81a0f4-1d2b-4e77-9a01-5f6c8b2d0e13 -n team-a
```

| Event                 | Cause                                                                                                       |
|-----------------------|-------------------------------------------------------------------------------------------------------------|
| `NoMetadataServer`    | `spec.pnfs.mds` is not set on the `SimplyblockDriver`.                                                      |
| `NoKVMCapableNode`    | No node with `storage.simplyblock.io/kvm-capable=true` (and the configured node selector) can take the pod. |
| `MDSStateUnavailable` | No StorageClass qualifies for the state disk, or the state disk did not bind.                               |
| `MDSResourcesInvalid` | The memory limit of the metadata server is below `512Mi`.                                                   |
| `AssembleTimeout`     | The metadata server did not finish exporting the volume in time. The export turns `Degraded`.               |
| `ExportReady`         | The volume is exported and can be mounted.                                                                  |
| `MDSResynced`         | The metadata server restarted and the volume was exported again.                                            |

The metadata server pods run in the operator's namespace. Each one is named `simplyblock-pnfs-mds-` followed by a
shortened form of its storage cluster's UUID:

```bash title="Listing the metadata server pods"
kubectl get pods -n simplyblock | grep pnfs-mds
```

## Verifying the Direct Data Path

A client that cannot use the direct NVMe-oF path still reads and writes correctly, but through the metadata server,
with much lower throughput. Nothing in Kubernetes reports this. Whether a node uses the direct path is shown in the
NFS mount statistics of the node, where a pNFS mount using the direct path reports `pnfs=LAYOUT_SCSI`.

```bash title="Checking the pNFS layout type of the mounts on a worker node"
grep 'pnfs=' /proc/self/mountstats
```

```plain title="Example output for a mount using the direct data path"
	nfsv4:	bm0=0xfdffbfff,bm1=0x40f9be3e,bm2=0x60800,acl=0x3,sessions,pnfs=LAYOUT_SCSI
```

`pnfs=not configured` means that the node's kernel does not meet the
[client requirements](#requirements).

## Using pNFS Volumes

Pods use a pNFS volume like any other filesystem volume. Concurrent writers on different nodes are coordinated by
NFSv4 byte-range locking, so applications that share files must use file locks as they would on any NFS share.

- **Expansion:** Supported online. The filesystem is grown automatically, and no pod has to be restarted. See
  [Expanding](expanding.md).
- **Snapshots:** Supported. A snapshot is instant and crash-consistent. See [Snapshotting](snapshotting.md).
- **Encryption:** Supported, through the `encryption` parameter of the StorageClass. See
  [Volume Encryption](volume-encryption.md).

When the metadata server restarts, for example, during a node drain, file operations on every client pause until it
serves again. Mounts and pods are kept, and applications continue afterward. A metadata server that stays unavailable
for an extended period makes file operations fail with an I/O error.

## Limitations

- A pNFS volume cannot be created from a snapshot or cloned from another volume yet.
- A pNFS volume cannot be moved to another storage node with a volume migration.
- Each storage cluster has a single metadata server. While the node hosting it is lost and the pod is stuck in
  `Terminating`, the pNFS volumes of that storage cluster cannot be accessed.
- A container running as root writes as root on the shared filesystem (`no_root_squash`). Access to a shared volume
  is controlled by file ownership and permissions only.
