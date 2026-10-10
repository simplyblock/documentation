---
title: "ReadWriteMany (pNFS)"
description: "How simplyblock serves ReadWriteMany volumes through pNFS: a metadata server per storage cluster, direct NVMe-oF data paths, layouts, and restarts."
weight: 30250
---

{{ experimental }}

A simplyblock logical volume is a block device, and a block device carries a filesystem that only one host may mount
at a time. Volumes that several nodes write concurrently (`ReadWriteMany`) are therefore served through parallel NFS
(pNFS), the NFSv4.1 extension that separates file metadata from file data. One logical volume backs each shared
volume. A metadata server (MDS) owns its filesystem and answers metadata requests, while every client reads and writes
the data directly over NVMe-oF, on the same namespace the metadata server formatted.

Metadata goes through the metadata server, data does not. Throughput therefore scales with the number of clients
instead of being capped by a single NFS server, and a shared volume performs close to the same logical volume attached
as a block device.

pNFS is available on Kubernetes only but not on a legacy Docker-based deployment. Its configuration is described in
[pNFS Volumes](../../kubernetes/usage/pnfs.md).

## Components

A pNFS volume consists of four parts:

- **Logical volume:** One or multiple ordinary simplyblock logical volume(s), carrying an XFS filesystem. Erasure
  coding, replication, encryption, and QoS apply to it as to any other volume.
- **Metadata server:** One pod per storage cluster, serving every pNFS volume of that cluster.
- **`NFSExport` resource:** One per volume, in the namespace of its PersistentVolumeClaim. It records which metadata
  server serves the volume and the address clients mount.
- **Clients:** The worker nodes that run pods using the volume. Each one attaches the logical volume over NVMe-oF and
  mounts the export over NFSv4.1.

### Metadata Server

The metadata server runs in the operator's namespace as a StatefulSet of one replica. Its pod starts a micro virtual
machine under QEMU and KVM, with its own Linux kernel, its own NFS server, and a read-only root filesystem. The guest
attaches the logical volumes over NVMe/TCP itself, creates the XFS filesystem on first use, mounts it, and exports it.

Because the NFS server runs inside the guest, no Kubernetes node runs an NFS server, mounts an exported filesystem, or
needs `nfs-utils`. The only requirement on the node hosting the metadata server is a usable `/dev/kvm`. The pod is
privileged for that reason, since `/dev/kvm` and `/dev/net/tun` are host device nodes. It uses neither the host
network nor the host PID namespace and mounts no host directory.

The metadata server is created by the operator when the first pNFS volume of a storage cluster is provisioned. It is
not removed when the last pNFS volume of the cluster is deleted.

Each metadata server keeps a small state disk, itself a simplyblock volume, holding the NFS client-recovery database.
That database is what allows NFS clients to reclaim their open files and locks after the metadata server restarts, on
the same worker node or on any other.

### Export Address

Every export is fronted by a Kubernetes Service of its own, whose ClusterIP is the address clients mount. The
Service's single endpoint is the metadata server pod's IP. When the pod restarts and receives a new IP, the endpoint
is repointed by the operator. The ClusterIP stays the same, so no client remounts.

Only NFSv4.1 and NFSv4.2 are served, on TCP port 2049. No portmapper and no `rpc.statd` are involved.

## Data Path

A pNFS client asks the metadata server for a layout before it reads or writes a file. A layout describes where the
blocks of a file live on the shared device. Simplyblock uses the pNFS SCSI layout (RFC 8154), which names a block
device and the extents on it. The client then reads and writes those extents directly on its own NVMe-oF attachment of
the logical volume, bypassing the metadata server.

Three conditions have to hold for a client to use a layout:

- The client node has the logical volume attached and can identify it by the namespace's NGUID.
- The client kernel carries the pNFS block layout driver and can derive a unique ID from an NVMe namespace.
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

## Metadata Server Restarts

A filesystem may be mounted by exactly one host, so a pNFS volume has exactly one metadata server and no standby. When
the metadata server pod is deleted, evicted, or fails, the StatefulSet starts it again, on the same node or on another
node with KVM. The new guest boots, the operator assembles every export of the storage cluster again with unchanged
paths and file handles, and the Service endpoints are repointed to the new pod.

During that time, metadata operations stall on every client. Once the metadata server serves again, clients reconnect
to the unchanged ClusterIP and reclaim their state in the NFS grace period. Pods are not restarted and volumes are not
remounted. The guest's NFS server holds back a client's layouts until its node plugin has taken the first one again.

Before a metadata server is stopped on purpose, new requests to it are dropped for a few seconds while the requests
already accepted are answered. A request is thus never executed by the old metadata server and then repeated on the
new one.

Clients mount with `soft`, `timeo=100`, and `retrans=2`. The NFS connection carries metadata only, so a metadata
request that is never answered returns an error instead of blocking the calling process indefinitely. An application
can therefore receive `EIO` for a metadata operation when the metadata server stays unavailable longer than these
retries cover.

!!! warning
    The metadata server is a single instance per storage cluster. Fencing a metadata server whose node is partitioned
    but still running is not implemented. While a node hosting the metadata server is lost and its pod stays
    `Terminating`, no replacement is started, and the exports of that storage cluster are unserved until the pod is
    removed.

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
