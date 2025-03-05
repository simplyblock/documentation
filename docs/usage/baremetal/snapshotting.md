---
title: "Snapshotting a Logical Volume"
weight: 30100
---

# Creating a Snapshot of a Logical Volume with sbcli

## Overview

Snapshots in simplyblock provide point-in-time copies of logical Volumes (LVs), allowing for backup, recovery, or
cloning operations without impacting the active workload. Snapshots can be created using the `sbcli` command line
interface to protect critical data or enable development and testing environments based on production data.

## Prerequisites

- A running simplyblock cluster with an existing logical volume.
- `sbcli` installed and configured with access to the simplyblock management API.

## Creating a Snapshot

To create a snapshot of an existing Logical Volume:

```bash
sbcli snapshot add \
  <VOLUME_UUID> \
  <SNAPSHOT_NAME>
```

## Verification

After creation, the snapshot can be listed:

```bash
sbcli snapshot list
```
