---
title: Hardware Requirements
description: "Hardware Requirements: In cloud environments including GCP and AWS, instance types are pre-configured."
weight: 29989
---

## Minimum System Requirements

The following minimum system requirements resources must be exclusive to simplyblock and are not available to the host
operating system or other processes. This includes vCPUs, RAM, locally attached virtual or physical NVMe devices,
network bandwidth, and free space on the boot disk.

### Overview

| Node Type                 | vCPU(s) | RAM (GB)  | Locally Attached Storage | Network Performance | Free Boot Disk | Number of Nodes | 
|---------------------------|---------|-----------|--------------------------|---------------------|----------------|-----------------|
| Control Plane<sup>*</sup> | 4       | 16 DDR4+* | -                        | 1 GBit/s            | 35 GB          | 3 for HA        | 
| Storage Node              | 8+      | 6+ DDR4+  | 1x dedicated NVMe        | 10 GBit/s           | 10 GB          | 3 for HA        | 

<sup>*</sup> Simplyblock highly recommends DDR5 memory on storage nodes for optimal performance.

## Sizing Basics

The supported architectures and sizing behavior depend on the deployment model of the simplyblock components.

## Storage Node Requirements

### Storage Node CPU Sizing

IOPS performance depends on Storage Node vCPU. The maximum performance will be reached with
32 physical cores per socket. In such a scenario, the deployment will dedicate (isolate) 24 cores to
simplyblock data plane (spdk_80xx containers) and the rest will remain under control of Linux.

### Storage Node NUMA Placement

Simplyblock auto-detects NUMA nodes. It will configure and deploy storage nodes per NUMA node.

Each NUMA socket requires directly attached NVMe devices and NICs to deploy a storage node.
For more information on simplyblock on NUMA, see [NUMA Considerations](numa-considerations.md).

It is recommended to deploy multiple storage nodes per storage host if there are more than 32 cores available
per socket.

During deployment, simplyblock detects the underlying configuration and prepares a configuration file with the
recommended deployment strategy, including the recommended amount of storage nodes per storage host based on the
detected configuration. This file is later processed when adding the storage nodes to the storage host.
Manual changes to the configuration are possible if the proposed configuration is not applicable.

### Hyper-Converged Sizing Guidance

As hyper-converged deployments have to share vCPUs, it is recommended to dedicate 8 vCPU per socket
to simplyblock. For example, on a system with 32 cores (64 vCPU) per socket, this amounts to
12.5% of vCPU capacity per host. For very IO-intensive applications, this amount should be increased.

### Storage Node Isolation Behavior

!!! warning
    On storage nodes, required vCPUs will be automatically isolated from the operating system. No
    kernel-space, user-space processes, or interrupt handler can be scheduled on these vCPUs.

### Storage Node Memory Sizing Formula

For RAM, it is required to estimate the expected average number of logical volumes per node, as well as the
average raw storage capacity, which can be utilized per node. For example, if each node in
a cluster has 100 TiB of raw capacity, this would be the average too. In a 5-node cluster,
with a maximum of 2,500 logical volumes, the average per node would be 500.

For storage nodes, simplyblock highly recommends DDR5 memory for optimal performance.

| Unit                                                     | Memory Requirement |
|----------------------------------------------------------|--------------------|
| Fixed amount                                             | 3 GiB              |
| Per logical volume (cluster average per node)            | 25 MiB             |
| % of maximum storage capacity (cluster average per node) | 1.5 GiB / TiB      |

!!! info
    For disaggregated setups, it is recommended to add 50% to these numbers as a reserve. In
    a purely hyper-converged setup, stay at the requirement.

## Control Plane Requirements

### Control Plane Baseline (Linux)

General control plane requirements provided above apply to the plain linux deployment. A control plane cluster of this
size can manage up to 5 nodes, 1,000 logical volumes, and 2,500 snapshots. For larger deployments, increase the
resources of the management nodes accordingly. 

### Control Plane Baseline (Kubernetes)

For a Kubernetes-based control plane, the minimum requirements per replica are:

| Service                    | vCPU(s) | RAM (GB) | Disk (GB) |
|----------------------------|---------|----------|-----------|
| Simplyblock Meta-Database  | 1       | 4        | 5         |
| Observability Stack        | 4       | 8        | 25        |
| Simplyblock Web-API        | 1       | 2        | 0.5       |
| Other Simplyblock Services | 1       | 2        | 0.5       |

### Control Plane Scaling Triggers

If more than 2,500 volumes or more than 5 storage nodes are attached to the control plane, additional RAM and vCPU
are advised. Also, the required observability disk space must be increased, if retention of logs and statistics for
more than 7 days is required.

### Control Plane Replication Notes

!!! info
    3 replicas are mandatory for the Key-Value-Store. The WebAPI runs as a Daemonset on all Workers, if no taint is applied.
    The Observability Stack can optionally be replicated and the sb-services run without replication.

## CPU & Platform Compatibility

### Supported Architectures by Plane

For the control plane, simplyblock always supports **x86-64 (Intel / AMD)** compatible CPUs. If deployed
to Kubernetes, it also supports **ARM64 (AArch64)** compatible CPUs.

For the storage plane, simplyblock always supports **x86-64 (Intel / AMD)** and **ARM64 (AArch64)** compatible CPUs.

### Deployment Model Compatibility

Simplyblock supports the most common system architectures, as well as plain Linux and Kubernetes-based
(hyper-converged and disaggregated) installation.

Both simplyblock storage nodes and control plane nodes can run fully virtualized. It has been tested on plain KVM,
Proxmox, Nitro (AWS EC2) and GCP.

For storage node production deployments, _SR-IOV_ is required for NVMEs and network interfaces (NICs). Furthermore,
dedicated cores must be assigned exclusively to the virtual machines running storage node (no over-provisioning).

For deployments on Cloud-based platforms, see [cloud-instance recommendations](cloud-instance-recommendations.md).

### Reference Matrix

A full list of the supported architectures can be found in the
[supported environment reference](../../reference/supported-linux-distributions.md) page.

## NVMe Device Requirements

### NVMe Capacity and Performance Guidance

NVMe devices must support 4KB native block size and are recommended to be sized between 1.9 TiB and 7.68 TiB.
Large NVMe devices are supported, but performance per TiB is lower and rebalancing can take longer.

Clusters are lightweight, and it is recommended to use different clusters for different types of
hardware (NVMe, networking, compute) or with a different performance profile per TiB of raw storage.

### NVMe Uniformity Recommendations

In general, all NVMe used in a single cluster should exhibit a similar performance profile per TB.
Therefore, within a single cluster, all NVMe devices are recommended to be of the same size,
but this is not a hard requirement.

### NVMe Exclusivity Requirements

Simplyblock only works with non-partitioned, exclusive NVMe devices (virtual via SRV-IO or physical) as its backing
storage.

Individual NVMe namespaces or partitions cannot be claimed by simplyblock, only dedicated NVMe controllers.

!!! important
    Devices are not allowed to be mounted under Linux and the entire device will be low-level formatted and
    re-partioned during deployment.

Additionally, devices will be detached from the operating system's control and will no longer show up in _lsblk_
once simplyblock's storage nodes are running.

### NVMe Formatting Prerequisites

It is required to [Low-Level Format Devices](../../reference/nvme-low-level-format.md) with 4KB block size before
deploying simplyblock.

!!! warning
    Low-level formatting destroys all data on the device. Ensure to back up any important data before formatting, if
    data is still required.

## Network Requirements

### Storage Traffic Network Requirements

In production, simplyblock requires a **redundant network** for storage traffic (e.g., via LACP, Stacked Switches, MLAG,
active/active or active/passive NICs, STP, or MSTP).

For production, software-defined switches such as Linux Bridge or OVS cannot be used. An interface on top of a Linux
bond over two ports of the NIC(s) or using SRV-IO must be created.

### Fabric and Protocol Notes

Simplyblock implements NVMe over Fabrics (NVMe-oF), specifically NVMe over TCP, and works over any Ethernet
interconnect.

!!! recommendation
    Simplyblock highly recommends NICs with RDMA/ROCEv2 support such as NVIDIA Mellanox network adapters (ConnectX-6 or higher).
    Those network adapters are available from brands such as NVIDIA, Intel, and Broadcom.

### Management Traffic Network Requirements

It is recommended to use a separate physical NIC with two ports (bonded) and a highly available network for
management traffic. For management traffic, a 1 GBit/s network is sufficient and a Linux Bridge may be used.

### Layer 2 Constraints and Prohibited Topologies

!!! warning
    All storage nodes within a cluster and all hosts accessing storage shall reside within the same hardware VLAN.

    Avoid any gateways, firewalls, or proxies higher than L2 on the network path.

## Additional Hardware Guidance

### PCIe Version

The minimum required PCIe standard for NVMe devices is PCIe 3.0. However, PCIe 4.0 or higher is strongly recommended.

### Hyperthreading

If 32 or more physical cores are available per storage node, it is highly recommended to turn off hyperthreading in the
BIOS or UEFI setup services.
