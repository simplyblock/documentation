---
title: "Volume Migration"
weight: 30700
---

Volume migration in simplyblock enables the online relocation of logical volumes between storage nodes without service
interruption. This is essential for planned maintenance, hardware replacement, capacity rebalancing, and infrastructure
modernization.

As simplyblock back storage is entirely distributed, volume migration does not require actual data movement! In fact, only
meta-data and extent headers are updated. 

## How Volume Migration Works

When a volume migration is initiated, simplyblock transfers the volume's complete data lineage -- including its entire
snapshot chain and the active volume data -- from the source node to a target node. The migration runs in the background
while the volume continues to serve I/O through its existing NVMe-oF paths.

The migration process follows these phases:

### 1. Snapshot Copy

All snapshots in the volume's ancestry chain are transferred to the target node, starting from the oldest ancestor.
For each snapshot:

- A corresponding snapshot is created on the target node.
- Data is transferred asynchronously using block-level copy operations.
- The snapshot's parent-child relationships are preserved on the target.

If the volume has secondary nodes configured (for fault tolerance), snapshots are also registered on the target's
secondary node.

### 2. Volume Data Migration

After all snapshots are transferred, the active volume data is migrated:

- A new volume is created on the target node with the same identity (NQN) as the source.
- The final data delta (changes since the last snapshot) is transferred.
- If secondary nodes are configured, the volume is registered on the target's secondary with NVMe subsystem and
  namespace configuration.

### 3. Cleanup

Once all data has been successfully transferred:

- The source volume and its snapshots are removed from the source node.
- Database records are updated to reflect the new node assignment.
- NVMe-oF paths are updated so clients connect to the target node.

If migration fails at any point, the target-side artifacts are cleaned up and the source volume remains intact.

## Migration Constraints

- **One migration per source node:** Only one volume migration can run on a given source node at a time. This is
  required to maintain snapshot consistency during the transfer.
- **Protection guards:** Volumes undergoing migration are protected from deletion, resizing, and snapshot deletion
  until the migration completes or is cancelled.
- **Automatic retry:** Transient failures during migration (such as temporary network issues) are automatically retried.
  The migration resumes from the last successful checkpoint.

## Use Cases

- **Hardware Replacement:** Migrate all volumes off a storage node before decommissioning it.
- **Capacity Rebalancing:** Move volumes from overloaded nodes to nodes with available capacity.
- **Maintenance Windows:** Evacuate a node for firmware updates or OS upgrades, then migrate volumes back.
- **Infrastructure Upgrades:** Move volumes to newer, higher-performance hardware without downtime.

For the operational procedure to migrate volumes, see
[Migrating a Storage Node](../../maintenance-operations/migrating-storage-node.md).
