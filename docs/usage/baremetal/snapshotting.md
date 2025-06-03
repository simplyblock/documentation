---
title: "Snapshotting a Logical Volume"
weight: 30100
---

Snapshots in simplyblock provide point-in-time copies of logical Volumes (LVs), allowing for backup, recovery, or
cloning operations without impacting the active workload. Snapshots can be created using the `{{ cliname }}`
command line interface to protect critical data or enable development and testing environments based on production data.

## Prerequisites

- A running simplyblock cluster with an existing logical volume.
- `{{ cliname }}` installed and configured with access to the simplyblock management API.

## Creating a Snapshot

To create a snapshot of an existing Logical Volume:

```bash
{{ cliname }} snapshot add \
  <VOLUME_UUID> \
  <SNAPSHOT_NAME>
```

## Verification

After creation, the snapshot can be listed:

```bash
{{ cliname }} snapshot list
```
