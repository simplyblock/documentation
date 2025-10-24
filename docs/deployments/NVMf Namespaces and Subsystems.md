
To connect to a storage volume, both locally and via NVMe-oF, you need a subsystem and a namespace.

An NVMe-oF subsystem is the exported entity that the host connects to over the fabric (RDMA, TCP).
A subsystem is identified by its unique worldwide name (NQN) and can be roughly seen as a 
controller, which exposes and connects one or multiple namespaces (actual volumes) to hosts. 

The NQN of a subsystem can contain the namespace uuid and is worldwide unique. 
In Simplyblock it looks as follows (the last part behind :lvol:<uuid> indicates the namespace representing the volume):

`qn.2023-02.io.simplyblock:136012a7-f386-4091-ae0f-4e763059e9c8:lvol:6809b758-1c73-451f-810c-210c18d6aa14`

Together with the IP address, the fully-qualified subystem address has to be given to connect, but 
In Simplyblock this process is either automated (CSI, OpenStack or Proxmox) or guided (plain linux attach).

It’s roughly equivalent to an NVMe controller complex — a logical device that can contain one or more namespaces.

Now subsystems are backed by multiple queue pairs, each of which is backed by a network connection such as a TCP socket.
More queue pairs require more resources from the cluster but make the volumes faster.

Namespacess on the other side are actual block storage regions that hold user data.
It’s the NVMe analog of a “LUN” in SCSI — the thing that actually stores and serves data blocks.
It has an NSID, size ond block format and UUID.

When a host connects to the subsystem, each namespace appears as a separate block device:

/dev/nvme0n1
/dev/nvme0n2

All namespaces on the same subsystem use the same network connections to transfer IO.

It’s what you would use for:

Creating a filesystem (e.g., mkfs.ext4 /dev/nvme0n1)
Raw block I/O (e.g., via fio, dd, or SPDK bdevs)
So the namespace is the thing you actually read and write data to.

!!! Info
    In simplyblock you can define how many namespace volumes are to be created for a particular
    subsystem. This allows sharing of subystems by Linux block devices (e.g. nvme0nX), where each of the them
    is less performance critical. In Kubernetes, to use different relationships (e.g. 1:10) between subsystem 
    and namespace, different storage classes are required.

To manually create volumes with multiple namespaces per subsystem, use:

```sbctl lvol add lvol01 100G pool01 --max-namespace-per-subsys 10```

This adds a new subsystem with a namespace and allows up to 9 more namespaces on this volume.
To add new namespaces to the same subsystem, use:

```sbctl lvol add lvol02 100G --uuid <UUID>```







