---
title: "Placement Groups"
description: "How a simplyblock supercluster places each volume in one placement group, what stays inside a placement group, and how volumes move between them."
weight: 30760
---

A placement group is one of the storage clusters that make up a [supercluster](../deployment-topologies/superclusters.md).
Each placement group is a complete simplyblock storage cluster with its own storage nodes, erasure coding scheme,
failure domains, and storage pools. What makes it a placement group is its membership: new volumes provisioned through
the supercluster are placed in exactly one of its placement groups, and the choice is made per volume at creation.

In the Kubernetes API, a placement group is a `StorageCluster` that names its supercluster in `spec.superclusterRef`.
It reports `status.role: PlacementGroup`, while a cluster outside any supercluster reports `Standalone`. The
supercluster itself refers to its placement groups as members, for example, in `status.members`.

## Why Placement Groups Exist

A simplyblock storage cluster holds at most 32 storage nodes. The limit bounds the exposure of a cluster to concurrent
failures. The fault tolerance of a cluster is set by its erasure coding scheme and does not grow with the node count,
while the probability that more nodes fail at once than the scheme tolerates grows with every node added.

A fleet larger than 32 storage nodes is therefore split into several clusters. As placement groups of one
supercluster, these clusters are presented to Kubernetes as a single cluster: one set of storage pools, one
StorageClass, and one status. The data path is unchanged. A volume's data lives in one placement group, and no data is
striped, mirrored, or erasure-coded across placement groups. The failure of a placement group affects only the volumes
placed in it.

Placement groups also separate hardware that cannot share a cluster. Workers in different regions, workers whose
network interfaces differ, and workers with different device classes (NVMe devices and
[Linux block devices](linux-block-devices.md)) each form placement groups of their own. Each placement group can carry
its own sizing and its own erasure coding scheme.

## Placement Groups and Failure Domains

Failure domains are a property of a placement group, as of any storage cluster. Data, journal copies, and failover
paths are spread across the [failure domains](failure-domains.md) of the placement group the volume lives in.

When a supercluster is drafted from the Kubernetes topology, every failure domain is spread over every placement group
of its region. Failure domains and placement groups then form a grid: the loss of one failure domain removes some
storage nodes from every placement group, and all storage nodes from none of them. Each placement group survives the
loss within the limits of its erasure coding scheme, and a zone outage degrades every placement group a little instead
of taking one of them down entirely.

A placement group never spans two regions. Every write is striped synchronously across the storage nodes of one
placement group, so a placement group spanning regions would put inter-region latency into every write.

## Placing a Volume

A volume is placed when it is created, by the Simplyblock Operator, on request of the CSI driver. The CSI driver asks
for a placement whenever the `cluster_id` of a StorageClass names a supercluster rather than a cluster. The chosen
placement group is written into the volume handle, so every later operation on the volume reaches the placement group
directly, without consulting the supercluster.

The placement group is chosen in the following order:

1. **Earlier placement:** A volume that was placed before, for example, by a creation that timed out and is retried,
   keeps its placement group. The placement is recorded on the PersistentVolumeClaim before the volume is created, so
   a retry never creates a second volume in another placement group.
2. **Consistency group:** A volume whose claim carries the `storage.simplyblock.io/consistency-group` label goes to
   the placement group that already holds the group. The first volume of a group is placed like any other volume, and
   its placement group becomes the group's.
3. **Eligibility:** Only placement groups that accept new volumes are considered. A placement group accepts volumes
   when it is serving (`Online`, `Degraded`, `Rebalancing`, or `Shrinking`), holds every storage pool of the
   supercluster, and does not set `spec.disablePlacement`.
4. **Topology:** When the scheduler passes a topology preference, placement groups in the preferred region are tried
   first, then those in any region the volume is allowed in. A volume is placed outside these regions only when none
   of them has room. Placement groups without region labels match every region.
5. **Capacity:** Placement groups without enough free capacity for the requested size, and placement groups above
   their own critical capacity threshold, are dropped. The free capacity accounts for volumes placed since the last
   capacity reading, so a burst of new volumes is spread instead of landing in the placement group that was emptiest a
   minute ago.
6. **Strategy:** The remaining placement groups are ranked by the placement strategy of the supercluster. Placement
   groups that rank equally are chosen between at random.

| Strategy                          | Picks the placement group with                        |
|-----------------------------------|-------------------------------------------------------|
| `MostAvailableCapacity` (default) | The most free physical capacity.                      |
| `LeastProvisioned`                | The lowest ratio of provisioned to physical capacity. |
| `LeastVolumes`                    | The fewest volumes.                                   |

When no placement group is left, the volume creation fails with `ResourceExhausted`, and the reason every placement
group was dropped is part of the error. The supercluster records the event `AggregateCapacityExhausted`.

## What Stays Inside a Placement Group

Once placed, a volume behaves exactly as a volume of a standalone cluster. Every feature that acts on an existing
volume runs inside its placement group:

- **Expansion:** A volume is expanded in place. When its placement group is full, the expansion fails even if other
  placement groups have room.
- **Snapshots and clones:** A snapshot is taken in the placement group of its volume. A clone, and a volume restored
  from a snapshot, land in the placement group of their source, whatever the placement strategy would choose.
- **Consistency groups:** All volumes of a consistency group share one placement group. A label added to an existing
  claim whose group lives in another placement group is refused with the event `ConsistencyGroupInAnotherCluster`.
- **Shared subsystems:** Volumes that share an NVMe subsystem share a placement group and move together.
- **Rebalancing and node migration:** [Automatic rebalancing](automatic-rebalancing.md) and
  [volume migration](volume-migration.md) run within one placement group. Volumes are never rebalanced between
  placement groups automatically.

Storage pools span the supercluster. A pool of a supercluster exists once in every placement group under the same
name, so one StorageClass reaches the pool in whichever placement group a volume is placed. The capacity limit of a
pool applies to the pool as a whole and is divided evenly among the placement groups that accept new volumes.

## Moving a Volume Between Placement Groups

A volume moves to another placement group of the same supercluster only on request, through a `PersistentVolumeOps`
resource with the action `Relocate`. The move is online: the consuming pods keep running, and the volume keeps its
NVMe subsystem name and namespace ID.

A relocation copies the volume into the target placement group with cross-cluster replication in migration mode. Once
the copy is in sync, the cutover is committed. Before the target serves the volume, its paths are attached on every
Kubernetes node that consumes the volume. The ANA states then flip, which makes the target's paths optimized and the
source's paths inaccessible, and the source volume is deleted afterward. The volumes of one subsystem move together
and are cut over one at a time.

The volume handle of a PersistentVolume is immutable and keeps naming the source placement group. The moved
PersistentVolume is therefore annotated with `storage.simplyblock.io/relocated-to`, and the CSI driver follows the
annotation for staging, expansion, snapshots, clones, and deletion.

The procedure is described in [Managing Superclusters](../../kubernetes/operations/scaling/superclusters.md#relocating-a-volume).

## Known limitations

The following volumes cannot be relocated:

- **Encrypted volumes:** A move would delete the volume's data encryption key with the source. They are refused with
  `EncryptedVolumeNotMovable`.
- **Members of a consistency group:** Moving one volume off the group's logical volume store breaks the group.
- **Volumes outside a supercluster:** Moving a volume between unrelated clusters is a matter of
  [asynchronous replication](../../kubernetes/operations/data-protection/asynchronous-replication.md).
