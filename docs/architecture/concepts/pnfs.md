---
title: "ReadWriteMany (pNFS)"
description: "How simplyblock serves ReadWriteMany volumes through pNFS: a metadata server per storage cluster, direct NVMe-oF data paths, layouts, and takeover."
weight: 30250
---

A simplyblock logical volume is a block device, and a block device carries a filesystem that only one host may mount
at a time. Volumes that several nodes write concurrently (`ReadWriteMany`) are therefore served through parallel NFS
(pNFS), the NFSv4.1 extension that separates file metadata from file data. Each shared volume is backed by simplyblock
logical volumes. A metadata server (MDS) owns its filesystem and answers metadata requests, while clients read and
write the data directly over NVMe-oF, on the same namespaces the metadata server formatted.

Metadata goes through the metadata server, data normally does not. Throughput therefore scales with the number of
clients instead of being capped by a single NFS server, and a shared volume performs close to the same logical volume
attached as a block device. A client that cannot use the direct path falls back to sending its data through the
metadata server (see [Data Path](#data-path)).

The principles of pNFS and how a file is read and written are introduced in
[Distributed File Storage](distributed-file-storage.md). This page describes the components in detail.

pNFS is available on Kubernetes only but not on a legacy Docker-based deployment. Its configuration is described in
[pNFS Volumes](../../kubernetes/usage/pnfs.md).

## Components

A pNFS volume consists of four parts:

- **Logical volumes:** The ordinary simplyblock logical volumes that carry the XFS filesystem. Erasure coding,
  replication, encryption, and QoS apply to them as to any other volume.
- **Metadata server:** One active pod and its standbys per storage cluster. The active pod serves every pNFS volume
  of that cluster.
- **`NFSExport` resource:** One per volume, in the namespace of its PersistentVolumeClaim. It records which metadata
  server serves the volume and the address clients mount.
- **Clients:** The worker nodes that run pods using the volume. Each one attaches the logical volume over NVMe-oF and
  mounts the export over NFSv4.1.

### Metadata Server

The metadata server runs in the operator's namespace as a StatefulSet. One of its pods is the active guest, which
serves the exports. The others are standbys, one by default (`spec.pnfs.mds.standbys`), which are booted and ready to
take over (see [Metadata Server Takeover](#metadata-server-takeover)). No two of the pods run on the same node.

Each pod starts a micro virtual machine under QEMU and KVM, with its own Linux kernel, its own NFS server, and a
read-only root filesystem. The active guest attaches the logical volumes over NVMe/TCP itself, creates the XFS
filesystem on first use, mounts it, and exports it.

Because the NFS server runs inside the guest, no Kubernetes node runs an NFS server, mounts an exported filesystem, or
needs `nfs-utils`. The only requirement on a node hosting a metadata server pod is a usable `/dev/kvm`. The pod is
privileged for that reason, since `/dev/kvm` and `/dev/net/tun` are host device nodes. It uses neither the host
network nor the host PID namespace and mounts no host directory.

The metadata server is created by the operator when the first pNFS volume of a storage cluster is provisioned. It is
not removed when the last pNFS volume of the cluster is deleted.

Each metadata server keeps a state volume of 1 GiB holding the NFS client-recovery database. It is a simplyblock
volume, created through the control plane in the storage pool of the first pNFS volume, not a PersistentVolumeClaim.
Only the active guest connects it, over NVMe/TCP. The database is what allows NFS clients to reclaim their open files
and locks after a takeover or a restart.

### Export Address

All exports of a metadata server share one Kubernetes Service, whose ClusterIP is the address clients mount. The
Service's single endpoint is the active guest's pod IP. When a standby takes over, or the active pod restarts with a
new IP, the endpoint is repointed by the operator. The ClusterIP stays the same, so no client remounts.

Only NFSv4.1 and NFSv4.2 are served, on TCP port 2049. No portmapper and no `rpc.statd` are involved.

## Data Path

A pNFS client asks the metadata server for a layout before it reads or writes a file. A layout describes where the
blocks of a file live on the shared device. Simplyblock uses the pNFS SCSI layout (RFC 8154), which names a block
device and the extents on it. The client then reads and writes those extents directly on its own NVMe-oF attachment of
the logical volume, bypassing the metadata server.

Three conditions have to hold for a client to use a layout:

- The client node has the logical volume attached and can identify it by the namespace's NGUID.
- The client kernel carries the pNFS block layout driver with support for NVMe devices, which it finds through
  `/dev/disk/by-id/nvme-eui.` links.
- The namespace accepts persistent reservations. The metadata server registers a reservation key on it before
  handing out any layout and refuses to hand out layouts when that registration fails.

When any of them do not hold, NFSv4.1 falls back to routing the data through the metadata server. Every byte stays
correct, and the mount keeps working, but throughput is limited by the metadata server. The fallback is silent, which
is why the layout state is checked on the client, as described in
[pNFS Volumes](../../kubernetes/usage/pnfs.md#verifying-the-direct-data-path).

The first layout of every volume is taken by the CSI node plugin right after mounting, by writing and removing a small
probe file. The kernel resolves the device a layout names in the mount namespace of the process that asked for it.
Only the node plugin sees the host's `/dev`, while a pod does not. The device found this way is reused for every later
layout of every pod on that node.

### Durability of Writes

A write layout normally covers unwritten blocks, which are converted to written blocks only when the client commits
the layout. A layout commit lost in a metadata server restart would leave completed writes reading back as zeros.
The guest kernel of the metadata server therefore zeroes the blocks of a write layout when they are allocated, so a
client's write is durable as soon as it has completed on the device. Each such allocation costs one write-zeroes
operation on the volume.

## Provisioning and Lifecycle

A pNFS volume is selected by its StorageClass, through `csi.storage.k8s.io/fstype: pnfs`. The access mode does not
select it: `ReadWriteOnce` and `ReadWriteMany` are both served the same way.

On provisioning, the logical volume is created through the control plane by the CSI driver, followed by the
`NFSExport` resource. The export is then served by the operator. For the first pNFS volume of a storage cluster, the
metadata server is started first. The metadata server attaches the logical volume, formats it with XFS, mounts it,
and exports it, after which the `NFSExport` turns `Ready` and the PersistentVolume is bound. When a pod is scheduled,
the logical volume is attached over NVMe-oF on its node, the export is mounted over NFSv4.1, and the first layout is
taken by the node plugin.

The PersistentVolume keeps the handle of its logical volume. Snapshots and volume expansion therefore address the
logical volume directly:

- **Expansion:** The logical volume is resized, and the XFS filesystem is grown on the metadata server, which holds
  the only mount of it. Clients need no action.
- **Snapshots:** A snapshot of a pNFS volume is an ordinary snapshot of its logical volume. The filesystem is not
  frozen first, but a snapshot is instant and crash-consistent.
- **Deletion:** The export is removed from the metadata server, and the filesystem unmounted before the logical volume
  is deleted.

A pNFS volume cannot be created from a data source (a snapshot or another volume) yet, and it cannot be moved with a
volume migration.

## Metadata Server Takeover

A filesystem may be mounted by exactly one host, so only the active guest mounts and serves the exports. A takeover
moves the active role to a standby. The operator starts one in three cases:

- **Deleted pod:** The active pod is deleted, for example, by a node drain or a rollout. The takeover starts at once.
- **Restarted guest:** The active guest restarted and came back as a standby. The takeover starts at once.
- **Lost active:** The operator has no link session with the active guest, or the guest does not answer. At the same
  time, its pod or its node is not `Ready`, and a standby is up. All of this has to hold for more than 20 seconds
  without interruption. On a lost node, the pod turns not `Ready` only once the node controller marks the node
  `NotReady`, so the takeover starts about the node controller's grace period plus 20 seconds after the node is lost.

The standby with the lowest ordinal that is `Ready` is promoted under a new epoch, which is recorded on the
StatefulSet. The Service endpoint is emptied first. The standby then connects the state volume and every export over
NVMe/TCP and fences each of them with an NVMe persistent reservation: it registers the key of the new epoch, acquires
the reservation as Exclusive Access, Registrants Only, and preempts and aborts the key of every earlier metadata
server. A former active that is partitioned but still running can no longer write to any of the devices. When a fence
fails on any device, nothing is mounted, and the promotion is retried with a backoff.

Once every device is fenced, the guest mounts the state volume and starts its NFS server. The operator points the
Service endpoint at the new active pod and hands the exports over to it, eight at a time. Because the guest connects
the state volume itself, a pod stuck in `Terminating` on a lost node holds nothing the standby needs.

The takeover is reported by events on the `SimplyblockDriver` resource:

| Event               | Cause                                                                                                                |
|---------------------|----------------------------------------------------------------------------------------------------------------------|
| `MDSFailoverHeld`   | The active looks lost, and the takeover waits out the 20-second detection window.                                    |
| `MDSFenced`         | The new active has fenced the state volume and every export.                                                         |
| `MDSPromoted`       | The new active serves every export. A warning when the active was lost. Also emitted on every `NFSExport`.           |
| `MDSFenceFailed`    | A fence failed or was refused, and nothing was mounted. The promotion is retried. Also emitted on every `NFSExport`. |
| `MDSStandbyMissing` | The active looks lost, and no standby is ready to take over.                                                         |
| `MDSDemoted`        | A guest reported the active role under an earlier epoch. Its pod was deleted and restarts as a standby.              |

During a takeover, metadata operations stall on every client. Once the new active serves, clients reconnect to the
unchanged ClusterIP and reclaim their state in the NFS grace period. Pods are not restarted and volumes are not
remounted. The guest's NFS server holds back a client's layouts until its node plugin has taken the first one again.

Before a metadata server pod is stopped on purpose, new requests to its guest are dropped for a few seconds while the
requests already accepted are answered. A request is thus never executed by the old metadata server and then repeated
on the new one.

Clients mount with `soft`, `timeo=100`, and `retrans=2`. The NFS connection carries metadata only, so a metadata
request that is never answered returns an error instead of blocking the calling process indefinitely. An application
can therefore receive `EIO` for a metadata operation when the metadata server stays unavailable longer than these
retries cover.

!!! warning
    Without a standby (`standbys: 0`), or while no standby is running, no takeover can start. A restarted guest is
    then promoted again in place. After the loss of the active's node, the exports of that storage cluster stay
    unserved until the pod stuck in `Terminating` is removed and started again on another node with KVM.

## Security

The NFS server lists the internal IP and the pod CIDR of every Kubernetes node as allowed clients of each export. The
pod CIDR is required because the CNI rewrites a node's traffic to the metadata server pod to an address from that
range. As a consequence, pods themselves are also admitted by the export entry. Exports use `no_root_squash`, so a
container running as root writes as root on the shared filesystem.

The metadata server's guest holds no Kubernetes credential and no control plane secret. Connection details of the
logical volumes are resolved by its pod and passed to the guest. The guest connects to each logical volume under a
host NQN derived from its StatefulSet, which stays stable across restarts.

Network access to the metadata server pods and to the storage cluster's NVMe-oF targets should be restricted to the
cluster's nodes, for example, with NetworkPolicies.
