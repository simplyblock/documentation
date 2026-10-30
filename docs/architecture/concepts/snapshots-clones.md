---
title: "Snapshots and Clones"
description: "Simplyblock snapshots capture a volume instantly with copy-on-write, and clones turn any snapshot into a writable volume without copying data."
weight: 30500
---

Snapshots and clones both capture the state of a volume at a point in time. A snapshot is a read-only record of that
state, used for protection and recovery. A clone is a new, writable volume that starts from a snapshot.

## Volume Snapshots

A snapshot is taken instantly and holds the read-only (frozen) state of the volume at that moment. Afterward, the
volume continues with copy-on-write semantics: new writes go to new blocks, and the blocks the snapshot references
are kept unchanged.

The snapshots of a volume form a chain ordered in time, in which each snapshot references only the data that
changed since its predecessor. Snapshots are deleted independently of each other, and their data is kept as long as
a later snapshot or a clone still needs it.

Key characteristics of volume snapshots include:

- **Instant and space-efficient:** No data is copied when a snapshot is taken. Snapshots share their blocks with
  the volume and with each other.
- **Basis for data protection:** Snapshots are what backups to S3 and replication to another cluster transfer,
  incrementally from one snapshot to the next.
- **Consistency groups:** The volumes of an application, for example, the data and log volumes of a database, can
  form a consistency group. A group snapshot captures all of them at the same instant (crash-consistent), and the
  group is replicated and failed over together.
- **Bounded chains:** Every snapshot deepens the chain that reads of the volume and its clones walk. A volume
  therefore has at most 100 active snapshots (see [Limits](../../reference/limits.md)).
- **Copy-on-write without data copies:** With page copy, the first write to a block after a snapshot does not copy
  the snapshot's data. The back storage records a reference instead and merges the data back when the snapshot is
  deleted (see [Snapshot Copy-on-Write](snapshot-copy-on-write.md)).

## Volume Clones

A clone is a writable volume created from a snapshot. It shares all blocks with the snapshot and allocates new
capacity only for the data written to it afterward. Restoring a snapshot means creating a clone of it, which
leaves the original volume and its snapshot untouched.

Key characteristics of volume clones include:

- **Instant:** A clone is available immediately, whatever the size of the volume, because no data is copied.
- **Writable and independent:** Changes to a clone do not affect the source volume or the snapshot, and the other
  way round.
- **Space-efficient:** A clone consumes capacity only for the data that differs from its snapshot.
- **Typical uses:** Restores, test and development environments, staging, and sandboxes for analytics or
  upgrades. A snapshot can have up to 500 active clones.

On Kubernetes, snapshots are `VolumeSnapshot` and `VolumeGroupSnapshot` objects, and clones are claims that name a
snapshot or another claim as their data source. See [Snapshotting](../../kubernetes/usage/snapshotting.md) and
[Cloning](../../kubernetes/usage/cloning.md).
