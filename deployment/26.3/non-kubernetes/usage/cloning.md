---
title: "Cloning a Logical Volume"
description: "Cloning a logical Volume (LV) in simplyblock creates a writable, independent copy-on-write clone of an existing volume."
source: "https://docs.simplyblock.io/latest/non-kubernetes/usage/cloning/"
---

# Cloning a Logical Volume

Cloning a logical Volume (LV) in simplyblock creates a writable, independent copy-on-write clone of an existing volume.
This is useful for scenarios such as testing, staging, backups, and development environments, all while preserving the
original data. Clones can be created quickly and efficiently using the `sbctl` command line interface.

## Prerequisites

- A running simplyblock cluster with an existing logical volume.
- An existing [snapshot](snapshotting.md) of a logical volume.
- `sbctl` installed and configured with access to the simplyblock management API.

## Cloning a Logical Volume

To create a clone of an existing Logical Volume:

```bash
sbctl snapshot clone \
  <SNAPSHOT_UUID> \
  <NEW_VOLUME_NAME>
```

## Verification

After cloning, the new Logical Volume can be listed:

```bash
sbctl volume list
```

Details of the cloned volume can be retrieved using:

```bash
sbctl volume get <VOLUME_UUID>
```
