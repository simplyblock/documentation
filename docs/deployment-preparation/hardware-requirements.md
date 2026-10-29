---
title: "Hardware and Storage Devices"
description: "Minimum hardware of simplyblock storage nodes, supported CPU architectures and virtualization, and the requirements for NVMe devices and Linux block devices."
weight: 29989
---

This page lists the minimum hardware of a storage node and the requirements for its CPU and storage devices. How many
vCPUs and how much memory a node needs beyond the minimum is described in [Sizing](sizing.md), and the network in
[Network](network.md).

## Minimum System Requirements

The following resources must be exclusive to simplyblock and are not available to the host operating system or other
processes:

| Node Type    | vCPU(s) | RAM (GB) | Storage Devices                  | Network Performance | Free Boot Disk | Number of Nodes  |
|--------------|---------|----------|----------------------------------|---------------------|----------------|------------------|
| Storage Node | 8+      | 6+ DDR4  | 2x dedicated NVMe <sup>(1)</sup> | 10 GBit/s           | 10 GB          | 3 <sup>(2)</sup> |

<span style="font-size: 0.8em;">
<sup>1</sup> One NVMe device is sufficient for a test setup, but it is not approved for production. Linux block
devices and storage array LUNs can be used instead of NVMe devices (see below).<br>
<sup>2</sup> The required number of nodes is only valid for erasure coding scheme 1+1. See
[Fault Tolerance and Erasure Coding](erasure-coding-scheme.md).
</span>

!!! note "Edge clusters"
    A storage node of an [edge cluster](../architecture/deployment-topologies/edge-clusters.md) needs at least
    3 vCPUs and 3 GB of RAM. An edge cluster has one storage node (cluster mode `Single`, any erasure-coding
    scheme with one data device per chunk, for example, 2+1 on three devices) or two storage nodes (cluster mode
    `Dual`, erasure coding 1+1).

In public clouds, instance types are pre-configured. Any instance type that meets these requirements can be used, but
the recommended instance types for [EKS](../kubernetes/installation/eks.md#instance-types) and
[GKE](../kubernetes/installation/gke.md#machine-types) are preferred for production.

## CPU and Platform Compatibility

The control plane and the storage plane run on **x86-64 (Intel / AMD)** and **ARM64 (AArch64)** CPUs. The supported
operating systems and kernels are listed in the
[supported Linux distributions](../reference/supported-linux-distributions.md) reference.

Storage nodes and control plane nodes can run fully virtualized. Simplyblock has been tested on plain KVM, Proxmox,
Nitro (AWS EC2), and GCP. For production storage nodes in virtual machines, SR-IOV is required for NVMe devices and
network interfaces, and dedicated cores must be assigned exclusively to the virtual machines (no over-provisioning).

### Virtualization Support for pNFS

This requirement applies only when [pNFS volumes](../kubernetes/usage/pnfs.md) are used.

The pNFS metadata server runs in a micro virtual machine, so at least one Kubernetes worker node must expose a usable
`/dev/kvm`. On bare metal, this requires the CPU virtualization extensions (Intel VT-x or AMD-V) to be enabled in the
firmware. On a virtual machine, including a cloud instance, it requires nested virtualization. QEMU's software
emulation is not used as a fallback.

Qualifying nodes are detected by the CSI node plugin and labeled with `storage.simplyblock.io/kvm-capable=true`. At
least two such nodes are recommended so that the metadata server can be rescheduled when its node is drained.

## Storage Devices

A storage cluster uses one class of devices, chosen at creation: NVMe devices, which simplyblock attaches natively, or
Linux block devices, which stay attached under Linux.

### NVMe Devices

- **Block size:** NVMe devices must support a 4 KB native block size, or a 512 B native block size with 4 KB write
  atomicity. Devices are formatted to 4 KB with `enableDriveFormat` in the deployment document, which destroys all
  data on them.
- **Size:** Devices between 1.9 TiB and 7.68 TiB are recommended. Larger devices are supported, but the performance
  per TiB is lower and rebalancing takes longer.
- **Uniformity:** All devices of a cluster should have a similar performance profile per TB, ideally the same size.
  Different types of hardware are better placed in separate clusters, which are lightweight.
- **Exclusivity:** Simplyblock claims whole NVMe controllers, physical or virtual through SR-IOV. Individual
  namespaces or partitions cannot be claimed. The devices must not be mounted, and they disappear from `lsblk` once
  the storage node runs.
- **PCIe:** PCIe 3.0 is the minimum, and PCIe 4.0 or higher is strongly recommended.

### Linux Block Devices and Storage Arrays

Any Linux block device can be used instead of NVMe devices, such as SAS or SATA SSDs, partitions, cloud volumes, or
the LUNs of a storage array. The devices remain attached under Linux and have to be unmounted and unpartitioned. The
same uniformity recommendation applies. See
[Linux Block Devices](../architecture/concepts/linux-block-devices.md) and [Storage Arrays](storage-arrays.md).

!!! note "Edge clusters"
    Edge clusters often use Linux block devices or partitions of a disk shared with the operating system. The rules
    for partitions (at most one partition per disk, equal sizes recommended, explicit selection) are described in
    [Linux Block Devices](../architecture/concepts/linux-block-devices.md#partitions).
