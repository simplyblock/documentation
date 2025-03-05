---
title: "Cloning a Logical Volume"
weight: 30200
---

Cloning a logical Volume (LV) in simplyblock creates a writable, independent copy-on-write clone of an existing volume.
This is useful for scenarios such as testing, staging, backups, and development environments, all while preserving the
original data. Clones can be created quickly and efficiently using the `sbcli` command line interface.

## Prerequisites

- A running simplyblock cluster with an existing logical volume.
- An existing [snapshot](snapshotting.md) of a logical volume.
- `sbcli` installed and configured with access to the simplyblock management API.

## Cloning a Logical Volume

To create a clone of an existing Logical Volume:

```bash
sbcli snapshot clone \
  <SNAPSHOT_UUID> \
  <NEW_VOLUME_NAME>
```

## Verification

After cloning, the new Logical Volume can be listed:

```bash
sbcli lvol list
```

Details of the cloned volume can be retrieved using:

```bash
sbcli lvol get <VOLUME_UUID>
```
