---
title: "Linux Block Devices (lblk)"
description: "How simplyblock clusters use arbitrary Linux block devices, such as SAS or SATA SSDs and cloud volumes, instead of NVMe PCIe devices."
weight: 30650
---

{{ experimental }}

A simplyblock storage cluster normally onboards storage as NVMe PCIe devices: at deployment, NVMe
controllers are detected on the PCI bus, unbound from the kernel driver, and attached natively to the
Simplyblock Storage Plane Container. The Linux block device mode (`lblk`) is an alternative,
cluster-global device mode that accepts any Linux block device — SAS or SATA SSDs behind an HBA,
virtualized disks (virtio, Xen), or cloud volumes such as Amazon EBS — without requiring NVMe
hardware at all.

!!! warning
    Linux block device support is experimental. It is intended for evaluation, for test environments,
    and for deployments where NVMe devices are unavailable. For production-grade performance, local
    NVMe devices are recommended.

## Device Modes

The device mode is chosen once, at cluster creation, and applies to every storage node in the
cluster:

| Mode | Storage devices | Attachment |
|------|-----------------|------------|
| `nvme` (default) | NVMe PCIe SSDs | SPDK native NVMe driver (kernel driver unbind) |
| `lblk` | Any Linux disk-type block device | SPDK AIO bdev on top of the kernel block layer |

In `lblk` mode, Linux block devices can be selected by their block device name (either allow or deny
lists) or by their serial number at deploy time. The deployment process and cluster operations are
otherwise identical.

Because the devices remain owned by the Linux kernel in `lblk` mode, no kernel driver unbinding takes
place, and no device is ever claimed by the Simplyblock Storage Plane PCI layer.

## Device Eligibility

A block device is eligible for `lblk` onboarding if all of the following hold:

- It is a whole disk — not a partition, and not a special device such as a loop, RAM, CD-ROM, or
  device-mapper device.
- It is not mounted, and no partition of it is mounted.
- It is not held by another subsystem (LVM, MD RAID, or device-mapper).
- It is not the root disk.
- It is not read-only and reports a non-zero size.
- It is unpartitioned. A device with an existing partition table is only accepted if it is explicitly
  force-formatted at node addition, which wipes the partition table and all filesystem signatures.

## Device Identity

NVMe devices are re-identified across reboots and restarts by their PCIe address and serial number.
Linux block device names (`/dev/sdb`, `/dev/xvdc`, ...) are not stable across reboots, so `lblk` mode
uses a serial-first identity: the device serial number (or WWN) is the primary identity, persisted in
the cluster database at node addition. On every node restart, the stored serial is re-resolved
against the live host inventory; the stored device name is only used as a fallback for devices that
expose no serial. A device without any hardware serial receives a stable synthetic identifier at
configuration time.

Renaming — for example, two disks swapping kernel names after a reboot — is therefore harmless: the
devices are matched by serial, and the storage stack is rebuilt on the correct disks.

## Failure Detection and Handling

Device failure handling in `lblk` mode reaches parity with the NVMe path. IO errors on a device are
detected by the storage stack exactly as in NVMe mode and feed the same device state machine:
repeated errors mark the device unavailable, and a device that keeps failing is removed from the
cluster map, with an automatic data migration rebuilding its data from redundancy onto the remaining
devices. A device that disappears from the host — through hot removal or a cloud volume detach — is
detected by inventory sweeps and handled like an NVMe hot-remove event.

Hung IO is covered separately. The SPDK native NVMe driver enforces an IO timeout that converts stuck
IO into failed IO; AIO bdevs have no such timeout, so `lblk` mode adds a control-plane hung-IO
watchdog. Queue-depth sampling detects a device whose IO has made no progress for a sustained window
(30 seconds by default) and marks it unavailable, feeding the same recovery machinery. Kernel-level
SCSI and NVMe timeouts typically convert device stalls into IO errors well before this watchdog
fires; it exists as the safety net for devices that hang without erroring.

## Restrictions

The device mode is cluster-global and deploy-time only: `nvme` and `lblk` devices cannot be mixed
within one cluster, and the mode cannot be changed after cluster creation. `lblk` mode requires
journal-on-device deployment (a dedicated device for the journal); device partitioning is not
supported. Growing a node's device set at restart time is not supported either — see
[Linux Block Device Operations](../../non-kubernetes/operations/lblk-device-operations.md).

SMART health telemetry is not available for AIO-backed devices. Device-level performance depends on
the underlying block device and the kernel block layer, so higher latency than with SPDK-native NVMe
attachment is to be expected.
