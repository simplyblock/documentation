---
title: "Removing a Logical Volume"
weight: 30400
---

Removing a logical Volume (LV) in simplyblock permanently deletes the volume and its associated data from the cluster.
This operation is performed using the `{{ variables.cliname }}` command line interface. Care should be taken to verify
that the volume is no longer in use and that backups are in place if needed.

While deleting a logical volume is a straightforward operation, it must be executed carefully to avoid accidental
data loss. Always ensure that the volume is no longer needed before removal.

!!! danger
    This action is **irreversible**. Once a logical volume is deleted, all data stored on it is permanently lost, except
    a snapshot or snapshot chain exists.

## Prerequisites

- A running simplyblock cluster with `{{ variables.cliname }}` configured.
- Ensure the Logical Volume is not mounted or in active use.
- Verify that data stored on the volume is no longer required or has been backed up.

## Deleting a Logical Volume

To remove a Logical Volume:

```bash
{{ variables.cliname }} volume delete <VOLUME_UUID> [--force]
```

### Parameters

- `--force`: Optional parameter to force the deletion of the logical volume

## Verification

To confirm that the volume has been successfully deleted:

```bash
{{ variables.cliname }} volume list
```

Verify that the volume no longer appears in the list of active logical volumes.

!!! warning
    If snapshots or snapshot chains of the logical volume exist, the internal storage is not reclaimed until all of the
    snapshots are deleted as well.
