---
title: "Storage Arrays"
description: "Plan a simplyblock deployment on FC, iSCSI, or NVMe-oF storage array LUNs: LUN layout per host, RAID and erasure coding, thin pools, and multipathing."
weight: 30150
---

Simplyblock can be deployed on the LUNs of an existing Fibre Channel, iSCSI, or NVMe-oF storage array instead of
local NVMe devices. The architecture and the division of tasks between the array and simplyblock are described in
[Storage Arrays](../architecture/concepts/storage-arrays.md). This page lists what has to be prepared.

## Recommended Array Configuration

- **RAID level:** RAID 5 for the LUNs. Together with an `n+1` erasure coding scheme in simplyblock, this tolerates
  two failures, similar to RAID 6.
- **Thin provisioning:** Thin LUNs are recommended. The array's thin pool must either be sized for the full capacity
  of all LUNs or be monitored with an alert well before it fills up, since a full pool fails the writes of all LUNs
  at once.
- **Data services:** Array snapshots, array replication, and array-side deduplication or compression are not used
  for simplyblock LUNs. Snapshots and disaster recovery are done in simplyblock. Volumes encrypted by simplyblock do
  not deduplicate or compress on the array.
- **Shared failure domain:** All hosts depend on the array. With several arrays, the hosts are spread evenly across
  them, and each array becomes a [failure domain](../architecture/concepts/failure-domains.md).

## LUN Layout per Host

Every host that runs a storage node gets its own LUNs, which are not shared with any other host:

| LUN       | Count     | Size                                                                                                                  |
|-----------|-----------|-----------------------------------------------------------------------------------------------------------------------|
| Data LUNs | 1 or more | Large and equal in size, on all hosts. Thin LUNs are sized for the expected growth, so that they never need resizing. |

No separate journal LUN is required. When the storage node is configured, simplyblock partitions the smallest LUN of
the host (or its only one) into a journal partition and a data partition. The journal partition takes 3% of the
host's LUN capacity by default, at least 2 GiB, and the rest of that LUN carries data like every other LUN. This
layout requires one storage node per host.

Because the array's RAID already protects the LUN, a journal on the same LUN as data is sufficient. In addition,
every write is journaled on other storage nodes as well, so the journal survives the loss of a host or its LUN.

!!! info "Dedicated journal LUN"
    A small dedicated journal LUN can still be used instead, with `enableJournalDevice` (see
    [Storage Array LUNs](../kubernetes/installation/k8s-storage-plane.md#storage-array-luns)). The smallest LUN of
    each host is then the journal and carries no data.

!!! important
    LUNs cannot be resized after a storage node uses them, and a LUN cannot be added to a running storage node yet.
    Capacity is added with new storage nodes and their LUNs (see
    [Operating on Storage Arrays](../kubernetes/operations/cluster/storage-arrays.md#adding-capacity)). Large thin
    LUNs avoid the need for either.

## Erasure Coding Scheme

The array protects against drive failures, so an `n+1` scheme is sufficient. The scheme is chosen once, at cluster
creation:

| Scheme | Capacity overhead in simplyblock | Minimum hosts |
|--------|----------------------------------|---------------|
| `1+1`  | 100%                             | 3             |
| `2+1`  | 50%                              | 4             |
| `4+1`  | 25%                              | 6             |

See [Erasure Coding Scheme](erasure-coding-scheme.md) for the general guidance.

## Host Connectivity

- **NVMe-oF arrays (NVMe/FC, NVMe/TCP, NVMe/RoCE):** Native NVMe multipathing of the Linux kernel is used, which
  presents every LUN as one device, for example, `/dev/nvme1n1`.
- **SCSI arrays (FC, iSCSI, iSER):** Device-mapper multipath devices are not accepted as storage devices yet. Each LUN
  is connected over a single path per host, and `multipathd` must not claim it (for example, through a blacklist
  entry for its WWID). A path loss is handled by simplyblock's erasure coding like a device failure.
- **Networks:** The SAN or array network is kept separate from the simplyblock storage network, so that array I/O
  and simplyblock I/O do not compete for the same links.
- **Persistent names:** LUNs are selected by persistent names, such as `/dev/disk/by-id/wwn-<WWN>` or
  `/dev/disk/by-id/nvme-eui.<EUI>`, never by kernel names such as `/dev/sdb`.

## Eligibility

Every LUN has to be eligible as a Linux block device: not mounted, not partitioned, not used by LVM, MD RAID, or
device-mapper, and not the root disk. See
[Linux Block Devices](../architecture/concepts/linux-block-devices.md#device-eligibility).

SMART health data is not available for array LUNs. The health of the drives is monitored by the array.
