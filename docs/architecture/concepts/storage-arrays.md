---
title: "Storage Arrays (FC, iSCSI, NVMe-oF)"
description: "How simplyblock runs on LUNs of an existing FC, iSCSI, or NVMe-oF storage array, and which tasks stay with the array and which move to simplyblock."
weight: 30655
---

{{ experimental }}

Simplyblock can run on the LUNs of an existing storage array instead of local NVMe devices. Every storage node's
host is given LUNs over Fibre Channel, iSCSI (also iSER), or NVMe over Fabrics (NVMe/FC, NVMe/TCP, NVMe/RoCE), and
simplyblock uses them as [Linux block devices](linux-block-devices.md). On top of them, it provides its full feature
set: Kubernetes-native volumes, snapshots and clones, QoS, encryption, replication, and disaster recovery.

## How It Works

```plain title="Storage stack on a storage array"
Kubernetes workloads
        │  NVMe/TCP or NVMe/RoCE
Simplyblock storage nodes  (erasure coding, thin provisioning, snapshots, replication)
        │  Linux block devices (lblk mode)
LUNs of each host  (FC, iSCSI, or NVMe-oF)
        │
Storage array  (RAID, thin pool)
```

Each host sees its LUNs as local block devices. The storage cluster runs in `lblk` device mode, which is chosen when
the cluster is created and applies to all of its storage nodes. Every storage node uses only its own host's LUNs, and
simplyblock distributes the data across the LUNs of all hosts as it would across local devices.

## Division of Responsibilities

| Function                                   | Array             | Simplyblock                                                 |
|--------------------------------------------|-------------------|-------------------------------------------------------------|
| Protection against drive failures          | Yes, with RAID 5  | Additional protection through erasure coding                |
| Protection against host or LUN loss        | No                | Yes, with an `n+1` erasure coding scheme and failover paths |
| Thin provisioning                          | Yes, for the LUNs | Yes, for the volumes                                        |
| Snapshots, clones, and copy-on-write       | Not used          | Yes                                                         |
| Replication, backup, and disaster recovery | Not used          | Yes                                                         |
| Encryption                                 | Optional          | Yes, per volume                                             |
| QoS                                        | Not used          | Yes, per volume, pool, and service class                    |

### Data Protection

The array already protects against drive failures. Simplyblock therefore needs only one parity chunk to protect
against the loss of a host, a LUN, or its paths. The recommended layout is RAID 5 in the array and an `n+1` erasure
coding scheme in simplyblock, preferably `4+1`. Together, they tolerate two failures, similar to RAID 6, while
simplyblock adds as little as 25% capacity overhead.

All storage nodes depend on the same array. The array is therefore a shared failure domain: its outage stops the
whole storage cluster. Where several arrays are available, the hosts can be spread across them and the arrays used as
[failure domains](failure-domains.md).

### Thin Provisioning on Two Levels

Thin provisioning applies twice: simplyblock allocates volume capacity only when it is written, and the array
allocates LUN capacity only when simplyblock writes to it. This allows large LUNs at no upfront cost, which avoids
resizing them later. Where LUNs do have to grow, simplyblock takes the new size online, as long as all data LUNs grow
by the same factor, since every device keeps the placement weight of its original size.

Two effects have to be considered:

- **Space is not returned to the array:** Simplyblock reuses capacity freed by deleted volumes and snapshots for new
  data, but it does not release it to the array. The array's allocation of a LUN grows up to the highest capacity
  simplyblock has used on it, including parity.
- **The array pool can run out first:** Simplyblock sees the full size of the LUNs. If the array's thin pool is
  smaller, it can fill up while simplyblock still reports free capacity. Writes then fail on all LUNs at once, which
  takes the cluster offline. The pool of the array must therefore be monitored, or sized for the full LUN capacity.

### Snapshots, Clones, and Disaster Recovery

Snapshots, clones, replication, backups, and disaster recovery are done in simplyblock only. Array snapshots or
array replication of the LUNs are not consistent across the LUNs of all hosts and cannot be used to restore a
simplyblock cluster. They also double the copy-on-write work and the capacity overhead. See
[Snapshots and Clones](snapshots-clones.md) and [Disaster Recovery](../../disaster-recovery/index.md).

### Multipathing

NVMe-oF LUNs are used with the native NVMe multipathing of the Linux kernel, which presents every LUN as one
device. Device-mapper multipath devices (`dm-multipath`) are not accepted as storage devices yet. SCSI LUNs over
Fibre Channel or iSCSI are therefore connected over a single path per host. The loss of that path is handled like a
device failure by simplyblock's erasure coding.

See [Storage Arrays](../../deployment-preparation/storage-arrays.md) for the planning of a deployment.
