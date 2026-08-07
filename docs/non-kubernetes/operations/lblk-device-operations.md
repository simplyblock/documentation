---
title: "Linux Block Device Operations"
description: "Operating lblk-mode clusters: node restarts with serial-based device resolution, adding block devices to a node, and handling failed devices."
weight: 20090
---

{{ experimental }}

Day-2 operations specific to clusters in the Linux block device mode (`lblk`) are described below.
Concepts and deployment are described under
[Linux Block Devices (lblk)](../../architecture/concepts/linux-block-devices.md) and
[Deploy with Linux Block Devices](../installation/linux-block-devices.md).

## Node Restarts

No `lblk`-specific handling is required for a node restart. On restart, the node's configured devices are
re-resolved serial-first against the live host inventory: kernel device names may have changed across
a reboot (for example, `/dev/sdb` and `/dev/sdc` swapping), and the devices are still matched
correctly by their persisted serial numbers. The AIO bdevs and the storage stack above them are then
rebuilt exactly as recorded in the cluster database.

A configured device that is missing from the host at restart is marked removed (the same semantics
as a missing NVMe controller), and the standard failed-device data migration is triggered.

!!! info
    The `--ssd-pcie` option of `storage-node restart`, by which new devices are added during a
    restart, is not supported on `lblk`-mode clusters and is rejected.

## Adding Devices to a Storage Node

Growing a node's device set is performed by reconfiguring and re-adding the node, not at restart
time:

1. Attach the new block devices to the host.
2. Remove the storage node from the cluster. Its data is migrated to the remaining nodes, as with any
   [node replacement](replacing-storage-node.md).
3. Re-run the configuration with a selection that includes the new devices:

    ```bash title="Reconfiguring the node with an extended device selection"
    sudo {{ cliname }} storage-node configure --lblk --blk-names sdb,sdc,sdd --max-lvol 50
    ```

4. Re-add the node to the cluster. The node joins with the extended device set, and data is
   redistributed onto it by the automatic rebalancing.

Cluster capacity can alternatively be extended by
[adding a new storage node](scaling/index.md) with its own devices.

## Failed Devices

Device failures are handled by the same machinery as in NVMe mode. A device producing IO errors is
marked unavailable and, after the retry budget is exhausted, marked failed. The cluster map is
updated, and the affected data is rebuilt from redundancy by a data migration. A device whose IO
hangs without erroring is caught by the `lblk` hung-IO watchdog (roughly 30 seconds of zero progress
with outstanding IO) and driven through the same unavailable, restart, and failed path. A device that
disappears from the host, through hot removal or a cloud volume detach, is detected and treated like
an NVMe hot-remove.

To replace a failed device, a replacement device is attached to the host, followed by the
[Adding Devices](#adding-devices-to-a-storage-node) procedure. Alternatively, the whole node is
replaced, following [Replacing a Storage Node](replacing-storage-node.md).

!!! info
    SMART health information is not available for AIO-backed devices. Device health checks
    (`storage-node check-device`) are limited to liveness and IO statistics.
