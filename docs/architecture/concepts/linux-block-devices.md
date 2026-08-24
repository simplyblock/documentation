---
title: "Linux Block Devices (lblk)"
description: "How simplyblock clusters use arbitrary Linux block devices, such as SAS or SATA SSDs and cloud volumes, instead of NVMe PCIe devices."
weight: 30650
---

{{ experimental }}

Storage is onboarded by a simplyblock storage cluster as NVMe PCIe devices by default. At deployment,
NVMe controllers are detected on the PCI bus, unbound from the kernel driver, and attached natively to
the simplyblock storage plane container.

The Linux block device mode (`lblk`) is an alternative, cluster-global device mode. In it, any Linux
block device is accepted and no NVMe hardware is required at all: SAS or SATA SSDs behind an HBA,
virtualized disks (virtio, Xen), or cloud volumes such as Amazon EBS.

!!! warning
    Linux block device support is experimental. It is intended for evaluation, for test environments,
    and for deployments where NVMe devices are unavailable. For production-grade performance, local
    NVMe devices are recommended.

## Device Modes

The device mode is chosen once, at cluster creation, and applies to every storage node in the
cluster:

| Mode             | Storage devices                  | Attachment                                     |
|------------------|----------------------------------|------------------------------------------------|
| `nvme` (default) | NVMe PCIe SSDs                   | SPDK native NVMe driver (kernel driver unbind) |
| `lblk`           | Any Linux disk-type block device | SPDK AIO bdev on top of the kernel block layer |

In `lblk` mode, devices can be selected at deploy time by their block device name (through an allow
list or a deny list) or by their serial number. The deployment process and cluster operations are
otherwise identical.

Because the devices remain owned by the Linux kernel in `lblk` mode, no kernel driver unbinding takes
place, and no device is ever claimed by the simplyblock storage plane PCI layer.

## Device Eligibility

A block device is eligible for `lblk` onboarding if all of the following hold:

- It is a whole disk (not a partition, and not a special device such as a loop, RAM, CD-ROM, or
  device-mapper device).
- It is not mounted, and no partition of it is mounted.
- It is not held by another subsystem (LVM, MD RAID, or device-mapper).
- It is not the root disk.
- It is not read-only and reports a non-zero size.
- It is unpartitioned. A device with an existing partition table is only accepted if it is explicitly
  force-formatted at node addition, which wipes the partition table and all filesystem signatures.

## Device Identity

NVMe devices are re-identified across reboots and restarts by their PCIe address and serial number.
Linux block device names (`/dev/sdb`, `/dev/xvdc`) are not stable across reboots, so a serial-first
identity is used in `lblk` mode instead.

The primary identity is the device serial number (or WWN), persisted in the cluster database at node
addition and re-resolved against the live host inventory on every node restart. The stored device
name serves only as a fallback for devices that expose no serial, and a device without any hardware
serial is given a stable synthetic identifier at configuration time.

Renaming is therefore harmless. Two disks that swap kernel names after a reboot are still matched by
serial, and the storage stack is rebuilt on the correct disks.

## Failure Detection and Handling

Device failure handling in `lblk` mode is at parity with the NVMe path. I/O errors on a device are
detected by the storage stack exactly as in NVMe mode and are fed into the same device state machine:
a device is marked unavailable after repeated errors, and a device that keeps failing is removed from
the cluster map, with its data rebuilt from redundancy onto the remaining devices by an automatic data
migration. A device that disappears from the host, through hot removal or a cloud volume detach, is
detected by inventory sweeps and handled like an NVMe hot-remove event.

Hung I/O is handled separately. An I/O timeout is enforced by the SPDK native NVMe driver, by which
stuck I/O is converted into failed I/O, but AIO bdevs have no such timeout. A control-plane hung-IO
watchdog is therefore added in `lblk` mode: a device whose I/O has made no progress for a sustained
window (30 seconds by default) is detected by queue-depth sampling and marked unavailable, entering
the same recovery machinery. The watchdog is the safety net for devices that hang without erroring,
because device stalls are typically converted into I/O errors by kernel-level SCSI and NVMe timeouts
well before it fires.

## Restrictions

The device mode is cluster-global and deploy-time only: `nvme` and `lblk` devices cannot be mixed
within one cluster, and the mode cannot be changed after cluster creation. In `lblk` mode,
journal-on-device deployment (a dedicated device for the journal) is required. Device partitioning is
not supported, and neither is growing a node's device set at restart time (see
[Linux Block Device Operations](../../non-kubernetes/operations/storage-nodes/lblk-device-operations.md)).

SMART health telemetry is not available for AIO-backed devices. Device-level performance depends on
the underlying block device and the kernel block layer, so higher latency than with SPDK-native NVMe
attachment is to be expected.
