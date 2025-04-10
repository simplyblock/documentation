---
title: "Expanding a Logical Volume"
weight: 30300
---

# Resizing (Expanding) a Logical Volume with sbcli

## Overview

Resizing a logical Volume (LV) in simplyblock allows additional capacity to be allocated without downtime, ensuring
workloads have sufficient storage as demand grows. The `{{ variables.cliname }}` command line interface is used to expand the size of an
existing Logical Volume in a simple and efficient manner.

## Prerequisites

- A running simplyblock cluster with a valid logical volume.
- `{{ variables.cliname }}` installed and configured with access to the simplyblock management API.

## Expanding a Logical Volume

To increase the size of an existing logical volume:

```bash
{{ variables.cliname }} volume resize \
  <VOLUME_UUID> \
  <NEW_SIZE>
```

## Verification

After resizing, confirm the new volume size:

```bash
{{ variables.cliname }} volume get <VOLUME_UUID>
```

## Resize the Filesystem (If Required)

Certain filesystems, such as ext4, may require growing the filesystem after the underlying volume has been expanded.

### For `ext4` filesystems:

```bash
resize2fs /dev/nvmeXnY
```

### For `xfs` filesystems:

```bash
xfs_growfs /mount/point
```

## Shrinking a Volume

Theoretically it is possible to shrink a volume. It can, however, create issues with certain filesystems. When a volume
needs to be shrunk, it is recommended to create a snapshot and restore it onto a new volume.
