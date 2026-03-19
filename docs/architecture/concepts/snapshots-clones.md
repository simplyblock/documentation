---
title: "Snapshots and Clones"
weight: 30500
---

Volume snapshots and volume clones are essential data management features in distributed storage systems that enable
data protection, recovery, and replication. While both techniques involve capturing the state of a volume at a specific
point in time, they serve distinct purposes and operate using different mechanisms.

## Volume Snapshots

A volume snapshot is a read-only, point-in-time copy of a storage volume. It preserves the state of the volume at the
moment the snapshot is taken, allowing users to restore data or create new volumes based on the captured state.
Snapshots are typically implemented using copy-on-write (COW) or redirect-on-write (ROW) techniques, minimizing storage
overhead and improving efficiency.

Key characteristics of volume snapshots include:

- **Space Efficiency:** Snapshots share common data blocks with the original volume, requiring minimal additional
  storage.
- **Fast Creation:** As snapshots do not duplicate data immediately, they can be created almost instantaneously.
- **Versioning and Recovery:** Users can revert a volume to a previous state using snapshots, aiding in disaster
  recovery and data protection.
- **Performance Considerations:** While snapshots are efficient, excessive snapshot accumulation can impact performance
  due to metadata overhead and fragmentation.

## Volume Clones

A volume clone is a writable, independent copy of a storage volume, created from either an existing volume or a
snapshot. Unlike snapshots, clones are fully functional duplicates that can operate as separate storage entities.

Key characteristics of volume clones include:

- **Writable and Independent:** Clones can be modified without affecting the original volume.
- **Use Case for Testing and Development:** Clones are commonly used for staging environments, testing, and application
  sandboxing.
- **Storage Overhead:** Unlike snapshots, clones may require additional storage capacity to accommodate changes made
  after cloning.
- **Immediate Availability:** A clone provides an instant copy of the original volume, avoiding long data copying
  processes.

## Snapshot Chains

Simplyblock organizes snapshots into ordered chains that represent the history of a volume over time. Each snapshot
references its parent (the previous snapshot in the chain), forming an ancestry chain from the most recent snapshot back
to the original volume state.

Key aspects of snapshot chains:

- **Ancestry Tracking:** Each snapshot maintains a reference to its parent via a `snap_ref_id`, enabling the system to
  reconstruct the complete history of changes.
- **Shared Snapshots:** When a volume is cloned from a snapshot, that snapshot becomes shared between the original
  volume and the clone. Shared snapshots are protected from deletion as long as any volume depends on them.
- **Reference Counting:** Simplyblock tracks how many clones depend on each snapshot. A snapshot cannot be deleted while
  it has active references.

Snapshot chains are central to several advanced features:

- **Backup to S3:** Backups follow the snapshot ancestry chain, ensuring incremental backups only transfer data changed
  since the last backed-up snapshot. See [Backup and Recovery](backup-recovery.md).
- **Volume Migration:** During live migration, the entire snapshot chain is transferred to the target node to preserve
  full data lineage. See [Volume Migration](volume-migration.md).
- **Replication:** Snapshot-based replication sends snapshots to remote clusters, maintaining the chain structure across
  sites. See [Replication](replication.md).
