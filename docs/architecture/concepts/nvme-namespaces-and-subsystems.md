---
title: NVMe Namespaces And Subsystems
description: "How simplyblock exposes volumes as NVMe namespaces in NVMe-oF subsystems, and when several volumes should share one subsystem."
weight: 30190
---

A host reaches an NVMe-oF volume through two entities: a subsystem, which the host connects to, and a namespace,
which holds the data.

## Subsystems

An NVMe-oF subsystem is the entity a host connects to over the fabric (TCP or RDMA). It is roughly the equivalent
of an NVMe controller and exposes one or more namespaces. A subsystem is identified by its worldwide unique NVMe
Qualified Name (NQN). In simplyblock, the NQN contains the cluster ID and, after `:lvol:`, the ID of the volume:

```plain title="Example NQN"
nqn.2023-02.io.simplyblock:136012a7-f386-4091-ae0f-4e763059e9c8:lvol:6809b758-1c73-451f-810c-210c18d6aa14
```

To connect, a host needs the NQN and the addresses of the storage nodes. The CSI driver and the Proxmox and
OpenStack drivers do this automatically. Each subsystem uses its own queue pairs, each backed by a network
connection, such as a TCP socket. More queue pairs make a volume faster, but cost resources on the storage node and
the host.

## Namespaces

A namespace is the block storage region that holds the data, the NVMe equivalent of a SCSI LUN. It has a namespace
ID (NSID), a size, a block format, and a UUID. Each namespace of a subsystem appears on the host as its own block
device, which is formatted with a filesystem or used for raw block I/O:

```plain title="Example host devices of a shared subsystem"
/dev/nvme0n1
/dev/nvme0n2
```

## Sharing a Subsystem

By default, every simplyblock volume gets a subsystem of its own. Volumes can also share a subsystem, with up to 50
namespaces per subsystem. All namespaces of a subsystem share its network connections.

| Layout                        | Suited for                                                                               |
|-------------------------------|------------------------------------------------------------------------------------------|
| One namespace per subsystem   | A few performance-critical volumes, each with its own connections                        |
| Many namespaces per subsystem | Many smaller volumes, which would otherwise exceed the subsystem limit of a storage node |

The number of namespaces per subsystem is a setting of the storage pool, so different layouts use different
storage pools and StorageClasses (see [Namespace Volumes](../../kubernetes/usage/storage-class.md#namespace-volumes)).
Shared subsystems are aligned with the storage pools: volumes of different pools never share a subsystem. The
subsystem and namespace limits are listed in [Limits](../../reference/limits.md).
