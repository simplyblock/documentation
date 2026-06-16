---
title: "Volume Migration"
weight: 30700
---

Simplyblock distributes storage across two layers: the front storage, which acts as "docking point" for clients connecting 
to volumes remotely via NVMe-oF (tcp, rocev2), and the back storage, which serves the actual cluster storage capacity. 
Front storage accesses back storage both locally and remotely, by itself using NVMe-oF.

Volume migration in simplyblock enables the online relocation of logical volumes (front storage or "docking points") 
between storage nodes without service interruption and almost instantly. This is possible, because front storage has
remote access to all devices in the cluster and thus exists essentially "in memory" only. 

Volume migration is performed automatically based on operator decisions to either pre-serve data locality of workloads or 
to to balance IO performance across cluster nodes (as the front storage does the "heavy-lifting" in IO processing and runs all
the data services). It is also used to drain nodes in case they need to be removed from the cluster (hardware replacement, infrastructure
modernization).

While most of the volume migrations happen "under the hood", users can also explicitely initiate migrations, e.g. to 
move particular, IO-heavy volumes to particular nodes.

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
