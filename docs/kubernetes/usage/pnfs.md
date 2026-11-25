---
title: "ReadWriteMany Volumes"
description: "Provision ReadWriteMany simplyblock volumes on Kubernetes through pNFS: enabling the metadata server, the StorageClass, node requirements, and limitations."
weight: 40080
---

A pNFS volume is a simplyblock volume that pods on several worker nodes read and write at the same time
(`ReadWriteMany`). It carries an XFS filesystem that is shared through NFSv4.1. File metadata goes through a metadata
server, while the data is read and written directly over NVMe-oF on every node that meets the
[client requirements](#requirements). This keeps a shared volume close to the performance of a block volume. The architecture is described in
[ReadWriteMany (pNFS)](../../architecture/concepts/pnfs.md).

A `ReadWriteMany` filesystem is served only by pNFS volumes. A `ReadWriteMany` claim with `volumeMode: Filesystem` on
any other StorageClass is refused. A `ReadWriteMany` claim with `volumeMode: Block` is accepted, and its writers are
coordinated by the application.

## Requirements

**Metadata server nodes:** Every metadata server pod needs a worker node of its own that exposes a usable `/dev/kvm`,
because the metadata server runs in a small virtual machine. With the default of one standby, that is two nodes. On a
virtualized cloud instance, this requires nested virtualization to be enabled on the instance.
The CSI node plugin checks `/dev/kvm` on every node and labels the nodes that pass with
`storage.simplyblock.io/kvm-capable=true`. A label set by hand is left untouched.

**Client nodes:** Every worker node that runs a pod using a pNFS volume needs
a kernel with the pNFS block layout driver (`CONFIG_PNFS_BLOCK`), including its support for NVMe devices: the
driver finds the device a layout names through a `/dev/disk/by-id/nvme-eui.` link, which the CSI node plugin creates. This
is a property of the kernel build, not of its version number. Red Hat Enterprise Linux 9.8 (kernel 5.14.0-687) is
validated. Debian and Ubuntu are not validated yet. No NFS packages are required on the host, because the NFS
client tools ship with the CSI node plugin.

A client node that does not meet the requirements still mounts the volume, but all data is routed through the
metadata server (see [Verifying the Direct Data Path](#verifying-the-direct-data-path)).

## Enabling pNFS

pNFS is enabled by default when the `SimplyblockDriver` is created by the Helm chart. The metadata server is configured
in `spec.pnfs.mds` of the `SimplyblockDriver` resource, or at installation time through the `driver.pnfs.mds`
[Helm values](../../reference/kubernetes/helm-values.md).

A `SimplyblockDriver` created manually, as in an [OperatorHub installation](../installation/openshift.md) or with the
[`empty` profile](../../reference/kubernetes/index.md#operator-only), has to set `spec.pnfs.mds`. An empty object
enables the metadata server with its defaults. Without it, every pNFS volume stays `Pending`.

```yaml title="Example of a SimplyblockDriver with metadata server settings"
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
      standbys: 1
```

One metadata server is started per storage cluster, when the first pNFS volume of that cluster is provisioned. It
consists of an active pod and its standby pods, each on a KVM-capable node of its own. The pods run in the operator's
namespace and must be allowed to run privileged.

| Field               | Description                                                                                                                                                                                                                                                 | Default                                                    |
|---------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------|
| `image`             | Metadata server image.                                                                                                                                                                                                                                      | The image matching the operator release.                   |
| `resources`         | Requests and limits of each metadata server pod, so every standby adds one pod's worth. The virtual machine gets the whole CPU cores of the CPU limit (at least one) and the memory limit less 256Mi.                                                       | CPU limit `2`, memory limit `2Gi`, memory request `512Mi`. |
| `nodeSelector`      | Additional node labels the pods are scheduled by, added to `storage.simplyblock.io/kvm-capable=true`.                                                                                                                                                       | -                                                          |
| `tolerations`       | Tolerations for tainted nodes.                                                                                                                                                                                                                              | -                                                          |
| `standbys`          | Number of standby pods beside the active one, from 0 to 4. Each standby needs another KVM-capable node, and a standby without one stays `Pending` while the active serves. With `0`, no takeover is possible.                                               | `1`                                                        |
| `dataNetwork`       | Storage data network the metadata server is attached to, set as `subnet`, `rangeStart`, and `rangeEnd`. Requires Multus and the whereabouts IPAM plugin. A change rolls the pods one at a time, the standbys first and the active last, through a takeover. | The pod network.                                           |
| `unhealthyDeadline` | Time the metadata server may stay unhealthy before it is restarted. A restart pauses all pNFS volumes of the storage cluster. `0s` disables the restart.                                                                                                    | `90s`                                                      |

A memory limit below `512Mi` is refused.

Without `dataNetwork`, the metadata server reaches the storage nodes through the pod network. This works only when the
nodes forward traffic arriving on their data interfaces, as Talos and K3s do, and OpenShift's OVN-Kubernetes does not
by default. A `dataNetwork` that cannot be attached falls back to the pod network as well: without Multus, the
`MDSDataNetworkUnavailable` event is reported, and without a node on the subnet, the `NoDataNetworkNode` event.

The state volume of each metadata server, which holds the NFS client-recovery database, has a fixed size of 1 GiB. It
is created through the control plane in the storage pool of the first pNFS volume and needs no StorageClass.

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
NAME                                          VOLUME                                                                                        MDS                                                      MDSPOD                                                   PHASE   MDSREADY   AGE
nfsexp-3c81a0f4-1d2b-4e77-9a01-5f6c8b2d0e13   0f2ac1d3-7a51-4c8e-b2e9-6d1f0a3b9c47:production-default:3c81a0f4-1d2b-4e77-9a01-5f6c8b2d0e13   simplyblock-pnfs-mds-0f2ac1d3-7a51-4c8e-b2e-8d3b9c10-0   simplyblock-pnfs-mds-0f2ac1d3-7a51-4c8e-b2e-8d3b9c10-0   Ready   True       12m
```

| Phase        | Meaning                                                                                                   |
|--------------|-----------------------------------------------------------------------------------------------------------|
| `Pending`    | No metadata server serves the volume yet. The events name the reason.                                     |
| `Assembling` | The metadata server is attaching, formatting, and exporting the volume.                                   |
| `Ready`      | The volume can be mounted.                                                                                |
| `Degraded`   | Exporting the volume did not finish within five minutes. The operator takes no further action on its own. |

`MDSREADY` shows whether the metadata server currently serves the volume. It is `False` while clients cannot be
served, and the condition message names the failure. The phase stays `Ready` meanwhile.

The events on the `NFSExport` resource explain a volume that does not become `Ready`:

```bash title="Showing the events of a pNFS export"
kubectl describe nfsexport nfsexp-3c81a0f4-1d2b-4e77-9a01-5f6c8b2d0e13 -n team-a
```

| Event                 | Cause                                                                                                       |
|-----------------------|-------------------------------------------------------------------------------------------------------------|
| `NoMetadataServer`    | `spec.pnfs.mds` is not set on the `SimplyblockDriver`.                                                      |
| `NoKVMCapableNode`    | No node with `storage.simplyblock.io/kvm-capable=true` (and the configured node selector) can take the pod. |
| `MDSStateUnavailable` | The state volume of the metadata server could not be created, found, or recorded.                           |
| `MDSResourcesInvalid` | The memory limit of the metadata server is below `512Mi`.                                                   |
| `MDSUnavailable`      | The metadata server cannot be started. The event message names the cause.                                   |
| `NoAllowedClients`    | No Kubernetes node publishes an internal address, so the volume cannot be exported to any client.           |
| `MDSUnhealthy`        | The volume failed the health check of the metadata server. `MDSREADY` turns `False`.                        |
| `AssembleTimeout`     | The metadata server did not finish exporting the volume in time. The export turns `Degraded`.               |
| `ExportReady`         | The volume is exported and can be mounted.                                                                  |
| `MDSResynced`         | The metadata server restarted and the volume was exported again.                                            |

The metadata server pods run in the operator's namespace. Each one is named `simplyblock-pnfs-mds-` followed by a
shortened form of its storage cluster's UUID and the pod's ordinal. The pod serving a volume is shown in the `MDSPOD`
column of the export list:

```bash title="Listing the metadata server pods"
kubectl get pods -n simplyblock | grep pnfs-mds
```

## Verifying the Direct Data Path

A client that cannot use the direct NVMe-oF path still reads and writes correctly, but through the metadata server,
with much lower throughput. A mount whose data keeps going through the metadata server for five minutes is reported
by a `PNFSDataThroughMDS` warning event on its PersistentVolumeClaim, or on its PersistentVolume when it has no claim.
The data path is also visible in the NFS mount statistics of the worker node, `/proc/self/mountstats`, in two places.

The `nfsv4:` line of a mount shows the layout type the node negotiated. A mount that can use the direct path reports
`pnfs=LAYOUT_SCSI`, and `pnfs=not configured` means that the node's kernel lacks the pNFS block layout driver.

```bash title="Checking the pNFS layout type of the mounts on a worker node"
grep 'pnfs=' /proc/self/mountstats
```

```plain title="Example output for a mount using the SCSI layout"
	nfsv4:	bm0=0xfdffbfff,bm1=0x40f9be3e,bm2=0x60800,acl=0x3,sessions,pnfs=LAYOUT_SCSI
```

`pnfs=LAYOUT_SCSI` alone does not prove that data bypasses the metadata server, because a client that cannot open the
device a layout names falls back without changing it. The per-operation counters of the mount show where the data
goes. While an application writes to the volume, the `LAYOUTGET` count grows, while the `READ` and `WRITE` counts stay
close to zero. Growing `READ` and `WRITE` counts mean that the data is routed through the metadata server.

```bash title="Showing the data and layout operation counters of the mounts on a worker node"
grep -E '^\s+(READ|WRITE|LAYOUTGET|GETDEVICEINFO):' /proc/self/mountstats
```

## Using pNFS Volumes

Pods use a pNFS volume like any other filesystem volume. Concurrent writers on different nodes are coordinated by
NFSv4 byte-range locking, so applications that share files must use file locks as they would on any NFS share.

- **Expansion:** Supported online. The filesystem is grown automatically, and no pod has to be restarted. See
  [Expanding](expanding.md).
- **Snapshots:** Supported. A snapshot is instant and crash-consistent. See [Snapshotting](snapshotting.md).
- **Encryption:** Supported, through the `encryption` parameter of the StorageClass. See
  [Volume Encryption](volume-encryption.md).

When a standby takes over, for example, during a drain of the active's node, file operations on every client pause
until the new active serves. Mounts and pods are kept, and applications continue afterward. The takeover is described
in [Metadata Server Takeover](../../architecture/concepts/pnfs.md#metadata-server-takeover). A metadata server that
stays unavailable for an extended period makes file operations fail with an I/O error.

## Limitations

- A pNFS volume cannot be created from a snapshot or cloned from another volume yet.
- A pNFS volume cannot be moved to another storage node with a volume migration.
- With `standbys: 0`, or while no standby is running, the loss of the node hosting the active metadata server makes
  the pNFS volumes of that storage cluster inaccessible until its pod, stuck in `Terminating`, is removed.
- A container running as root writes as root on the shared filesystem (`no_root_squash`). Access to a shared volume
  is controlled by file ownership and permissions only.
