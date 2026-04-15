---
title: "Trimming a Filesystem"
description: "Trimming a Filesystem: Filesystem trimming is the process of informing the underlying storage system about unused blocks, allowing simplyblock to reclaim and."
weight: 20090
---

Filesystem trimming is the process of informing the underlying storage system about unused blocks, allowing simplyblock
to reclaim and optimize storage space. This is particularly important when using thin-provisioned Logical Volumes (LVs)
in simplyblock, as it helps maintain efficient resource utilization and reduces unnecessary storage consumption over
time.

## What Trimming Does in Simplyblock

In a thin-provisioned setup, deleting files in the filesystem does not automatically reclaim capacity on the storage
backend. Trimming notifies the storage stack that blocks are no longer in use and can be released by simplyblock.

The effectiveness of reclaim depends on the filesystem, kernel support, and mount configuration.

## Prerequisites

Before trimming:

- Ensure the volume is mounted and you know the correct mountpoint.
- Ensure required filesystem tools are available on the node.
- Run trim operations with sufficient privileges.
- Prefer running large trim jobs during low I/O periods in production environments.

## When to Trim

Trimming should be performed:

- After large file deletions.
- As part of regular maintenance to keep storage optimized.
- Following data migration or cleanup tasks.

For regular maintenance, periodic trim scheduling (for example, via systemd timers such as `fstrim.timer`) is
recommended where operationally appropriate.

## How to Trim

Trimming must be executed within the filesystem inside the mounted volume. The specific command depends on the
filesystem type. Below are common examples:

=== "ext4"
    ```bash title="Trimming an ext4 filesystem"
    fstrim -v /mount/point
    ```

=== "XFS"
    ```bash title="Trimming an XFS filesystem"
    xfs_fsr -v /mount/point
    ```

## Verification

After trimming:

- Confirm the command output reports completed trim activity for the expected mountpoint.
- Verify reclaimed capacity through your monitoring workflow (CLI metrics and dashboards).
- If reclaim appears lower than expected, re-check mountpoint, filesystem type, and timing of backend metric updates.

## Common Pitfalls

- Trimming the wrong mountpoint or an unmounted path.
- Expecting immediate visible reclaimed capacity in all dashboards and counters.
- Assuming all filesystems and environments behave identically for discard/reclaim behavior.

## Related References

- [Accessing I/O Stats ({{ cliname }})](../maintenance-operations/monitoring/io-stats.md)
- [Logical Volume Conditions](../maintenance-operations/monitoring/lvol-conditions.md)
- [Provisioning with Linux](../usage/baremetal/index.md)
- [Provisioning with Simplyblock CSI](../usage/simplyblock-csi/provisioning.md)
