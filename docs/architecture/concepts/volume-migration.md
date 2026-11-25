---
title: "Volume Migration"
description: "How simplyblock separates front and back storage, and how the backing logical volume of a volume moves between storage nodes during a migration."
weight: 30700
---

Simplyblock distributes storage across two layers. The front storage, which acts as "docking point" for clients connecting
to volumes remotely via NVMe-oF (TCP, RoCEv2), and the back storage, which serves the actual cluster storage capacity.
The front storage accesses back storage both locally and remotely. Remote access itself uses NVMe-oF.

Volume migration in simplyblock enables the online relocation of logical volumes (front storage or "docking points")
between storage nodes while the volume keeps serving I/O, with a short pause at the cutover. This is possible because
front storage has remote access to all devices in the cluster and thus exists essentially "in memory" only.

Volume migrations are performed automatically based on operator decisions to either pre-serve data locality of workloads or
to balance I/O performance across cluster nodes. This is required since the front storage does the "heavy-lifting" in I/O processing
and runs all the data services. Additionally, volume migration is used to drain nodes in case they need to be removed from the cluster
(hardware replacement, infrastructure modernization).

While most of the volume migrations happen "under the hood," users can also explicitly initiate migrations (e.g., to
move particular, I/O-heavy volumes to particular nodes).

## How Volume Migration Works

When a volume migration is initiated, simplyblock transfers the volume's complete lineage (its entire snapshot chain
and the active volume) from the source node to a target node. Only the front storage is transferred: the logical
volume and snapshot structures that map the volume onto the back storage. The data itself stays where it is in the
distributed back storage and is not copied. The migration runs in the background while the volume continues to serve
I/O through its existing NVMe-oF paths.

The migration process follows these phases:

### 1. Snapshot Copy

All snapshots in the volume's ancestry chain are transferred to the target node, starting from the oldest ancestor.
For each snapshot:

- A corresponding snapshot is created on the target node.
- The snapshot's metadata, which references the snapshot's data in the back storage, is transferred asynchronously.
- The snapshot's parent-child relationships are preserved on the target.

If the volume has secondary nodes configured (for fault tolerance), snapshots are also registered on the target's
secondary node.

### 2. Volume Data Migration

After all snapshots are transferred, the active volume data is migrated:

- A new volume is created on the target node with the same identity (NQN) as the source.
- The final delta of the volume's metadata (changes since the last snapshot) is transferred.
- If secondary nodes are configured, the volume is registered on the target's secondary with NVMe subsystem and
  namespace configuration.

### 3. Cleanup

Once all data has been successfully transferred:

- The source volume and its snapshots are removed from the source node.
- Database records are updated to reflect the new node assignment.
- NVMe-oF paths are updated so clients connect to the target node.

If migration fails at any point, the target-side artifacts are cleaned up and the source volume remains intact.

## Migration Constraints

!!! note "A volume migration is a live migration with a short pause at the cutover"
    No back storage is copied during a volume migration. The data of the volume and its snapshots remains in place,
    distributed across the devices of the cluster, and only the front storage moves to the target node, so a
    migration does not load the cluster with data transfers. The front storage moves while the volume runs: its
    snapshots are copied first, followed by up to three catch-up snapshots until less than 500 MiB has changed. The
    cutover then pauses the I/O of the volume for at most 12 seconds. For a volume that shares its NVMe-oF subsystem
    with others, all paths of the subsystem are made inaccessible first, which adds 2 seconds. The I/O is held during
    the pause, so it waits rather than fails. If node affinity is turned on, the back storage is realigned to the new
    node asynchronously afterward, as part of the background rebalancing (see
    [Data Locality](../storage-performance-and-qos.md#data-locality)).

- **One migration per cluster on Kubernetes:** The Simplyblock Operator runs one volume migration per storage cluster
  at a time. Further migrations wait in `Pending` with an `OperationQueued` event until it has finished.
- **Protection guards:** Volumes undergoing migration are protected from deletion, resizing, and snapshot deletion
  until the migration completes or is canceled.
- **No new snapshots on the source node:** While a migration from a storage node runs, no new snapshot of any volume
  on that node is created. Scheduled snapshots and backups of those volumes are refused until the migration ends.
- **Automatic retry:** Transient failures during migration (such as temporary network issues) are automatically retried.
  The migration resumes from the last successful checkpoint.

## Use Cases

- **Hardware Replacement:** Migrate all volumes off a storage node before decommissioning it.
- **Capacity Rebalancing:** Move volumes from overloaded nodes to nodes with available capacity.
- **Maintenance Windows:** Evacuate a node for firmware updates or OS upgrades, then migrate volumes back.
- **Infrastructure Upgrades:** Move volumes to newer, higher-performance hardware without downtime.

For the operational procedure to migrate volumes, see
[Volume Migration](../../kubernetes/operations/volumes/volume-migration.md) and
[Migrating a Storage Node](../../kubernetes/operations/storage-nodes/migrating-a-storage-node.md).
