---
title: System Requirements
weight: 29999
---

!!! info
    In cloud environments including GCP and AWS, instance types are pre-configured. In general,  
    there are no restrictions on instance types as long as these system requirements are met. However, it is highly recommended to
    stay with the [Recommended Cloud Instance Types](cloud-instance-recommendations.md) for production.

    For [hyper-converged](../../architecture/concepts/hyper-
    converged.md) deployments, it is important that node sizing applies to the dedicated 
    resources consumed by simplyblock. Hyper-converged instances must provide enough of resources 
    to satisfy both, simplyblock and other compute demand, including the Kubernetes worker itself and the 
    operating system.

## Hardware Architecture Support

- For the control plane, simplyblock **requires** x86-64 compatible CPUs.
- For the storage plane, simplyblock **supports** x86-64 or ARM64 (AArch64) compatible CPUs.

## Virtualization Support

Both simplyblock storage nodes and control plane nodes can run fully virtualized. It has been tested on plain KVM,
Proxmox, Nitro (AWS EC2) and GCP.

For storage node production deployments, _SR-IOV_ is required for NVMEs and network interfaces (NICs). Furthermore,
dedicated cores must be assigned exclusively to the virtual machines running storage node (no over-provisioning).

## Deployment Models

Two deployment option are supported:

- **Plain Linux**: In this mode (we call it also docker mode), all nodes are deployed to 
  separate hosts (storage nodes: usually bare-metal, control plane: usually VMs).
  Basic Docker knowledge is helpful, but all management is performed within the system via its CLI or API. 

- **Kubernetes**: In Kubernetes, both dis-aggregated deployments (dedicated workers or even clusters for storage nodes) or hyper-converged 
  deployments (combined with compute) are supported. A wide range of Kubernetes distros and OSes are supported.
  Kubernetes Knowledge is required.

The minimum system requirements below concern simplyblock only and must be dedicated to simplyblock.

## Minimum System Requirements

!!! Info
    If the use of erasure coding is intended, DDR5 RAM is recommended for maximum performance. 
    CPUs with large L1 caches will perform better too.

The following minimum system requirements resources must be exclusive to simplyblock and are not available to the host
operating system or other processes. This includes vCPUs, RAM, locally attached virtual or physical NVMe devices,
network bandwidth, and free space on the boot disk.

### Overview

| Node Type      | vCPU(s) | RAM (GB) | Locally Attached Storage | Network Performance | Free Boot Disk | Number of Nodes | 
|----------------|---------|----------|--------------------------|---------------------|----------------|-----------------|
| Storage Node   | 8+      | 6+       | 1x fully dedicated NVMe  | 10 GBit/s           | 10 GB          | 1 (2 for HA)    | 
| Control Plane* | 4       | 16       | -                        | 1 GBit/s            | 35 GB          | 1 (3 for HA)    | 
*Plain Linux Deployment, up to 5 nodes, 1.000 logical volumes, 2.500 snapshots

### Storage Nodes

IOPS performance depends on Storage Node vCPU. The maximum performance will be reached with
32 physical cores per socket. In such a scenario, the deployment will dedicate (isolate) 24 cores to
Simplyblock Data Plane (spdk_80xx containers) and the rest will remain under control of Linux.

!!! Info
    Simplyblock auto-detects NUMA nodes and configures and configures and deploys storage nodes per NUMA node.
    Each NUMA socket requires directly attached NVMe and NIC to deploy a storage node.
    For more information on simplyblock on NUMA, see [NUMA Considerations](numa-considerations.md).

!!! Info
    It is recommended to deploy multiple storage nodes per storage host if
    there are more than 32 cores available per socket.
    During deployment, simplyblock detects the underlying configuration and prepares a configuration file with the
    recommended deployment strategy, including the recommended amount of storage nodes per storage host based on the
    detected configuration. This file is later processed when adding the storage nodes to the storage host.
    Manual changes to the configuration are possible if the proposed configuration is not applicable.

As hyper-converged deployments have to share vCPU, it is recommended to dedicate 8 vCPU per socket
to Simplyblock. For example, on a system with 32 cores (64 vCPU) per socket, this amounts to 
12.5% of vCPU capacity on the host. For very IO-intensive applications, this amount could be increased.

!!! Warning
    On storage nodes, required vCPUs will be automatically isolated from the operating system. No
    kernel-space, user-space processes, or interrupt handler can be scheduled on these vCPUs.

!!! Info
    For RAM, it is required to estimate the expected average logical volumes per node and 
    average raw storage capacity, which can be utilized per node. For example, if each node in 
    a cluster has 100 TiB of raw capacity, this would be the average too. If in a 5 node cluster
    you expect a maximum of 2.500 volumes, the average per node would be 500.

| Unit                                                  | Memory Requirement |
|-------------------------------------------------------|--------------------|
| Fixed amount                                          | 3 GiB              |
| Per logical volume (cluster average per node)         | 25 MiB             |
| % of max. storage capacity (cluster average per node) | 1.5 GiB / TiB      |

!!! Info
    For disaggregated setups, it is recommended to add 50% to these numbers as a reserve. In 
    a purely hyper-converged setup, stay at the requirement.

### Control Plane

 General Control Plane requirements provided above apply to the Plain Linux Deployment.
 For a kubernetes-based control plane, the minimum requirements per replica are:

| Service             | vCPU(s) | RAM (GB) | Disk (GB) |  
|---------------------|---------|----------|-----------|
| Sb-Meta-Database    | 1       | 4        | 5         |  
| Observability Stack | 4       | 8        | 25        | 
| Sb-Web-API          | 1       | 2        | 0.5       | 
| Sb-Services         | 1       | 2        | 0.5       | 

If more than 2.500 volumes or more than 5 storage nodes are attached to the control plane, additional RAM and vCPU
is advised. Also, the disk space for observability should be increased in such a scenario or if
retention of logs and statistics for more than 7 days is required. 

!!! Info
    3 replicas are mandatory for the Key-Value-Store. The WebAPI runs as a Daemonset on all Workers, if no taint is applied.
    The Observability Stack can optionally be replicated and the sb-services run without replication.  


## Hyperthreading

If 32 or more physical cores are available per storage node, it is highly recommended to turn off hyperthreading in the
BIOS or UEFI setup services.

## NVMe Devices

NVMe devices must support 4KB native block size and are recommended to be sized between 1.9 TiB and 7.68 TiB.
Large NVMe devices are supported, but performance per TiB is lower and rebalancing can take longer.

In general, all NVMe used in a single cluster should exhibit a similar performance profile per TB.
Therefore within a single cluster, all NVMe devices are recommended to be of the same size,
but this is not a hard requirement.

Clusters are lightweight, and it is recommended to use different clusters for different type of 
hardware (NVMe, Networking, Compute) with a different performance profile per TiB of Raw Storage. 

!!! Warning
    Simplyblock only works with non-partitioned, exclusive NVMe devices (virtual via SRV-IO or physical) as its backing
    storage.

    Individual NVMe namespaces or partitions cannot be claimed by simplyblock, only dedicated NVMe controllers. 
    
    Devices are not allowed to be mounted under Linux and the entire device will be low-level formatted and
    re-partioned during deployment.
    
    Additionally, devices will be detached from the operating system's control and will no longer show up in _lsblk_
    once simplyblock's storage nodes are running.

!!! Info
    It is required to [Low-Level Format Devices](../../reference/nvme-low-level-format.md) with 4KB block size before
    deploying Simplyblock.

## Network Requirements

In production, simplyblock requires a __redundant network__ for storage traffic (e.g., via LACP, Stacked Switches, MLAG,
active/active or active/passive NICs, STP or MSTP).

Simplyblock implements NVMe over Fabrics (NVMe-oF), specifically NVMe over TCP, and works over any Ethernet
interconnect.

!!! recommendation
    Simplyblock highly recommends NICs with RDMA/ROCEv2 support such as NVIDIA Mellanox network adapters (ConnectX-6 or higher).
    NVIDIA, INTEL and BROADCOM ship those. 

For production, software-defined switches such as Linux Bridge or OVS cannot be used. An interface on top of a Linux
bond over two ports of the NIC(s) or using SRV-IO must be created.

Also, it is recommended to use a separate physical NIC with two ports (bonded) and a highly available network for
management traffic. For management traffic, a 1 GBit/s network is sufficient and a Linux Bridge may be used.

!!! warning
    All storage nodes within a cluster and all hosts accessing storage shall reside within the same hardware VLAN.

    Avoid any gateways, firewalls, or proxies higher than L2 on the network path.

## PCIe Version

The minimum required PCIe standard for NVMe devices is PCIe 3.0. However, PCIe 4.0 or higher is strongly recommended.

## Operating System Requirements (Control Plane, Storage Plane)

__Control plane nodes__, as well as storage nodes in a __plain linux__ deployment, require one of the following
operating systems:

| Operating System               | Versions |
|--------------------------------|----------|
| Alma Linux                     | 9        |
| Rocky Linux                    | 9        |
| Redhat Enterprise Linux (RHEL) | 9        |

In a Hyper-Converged Deployment a broad range of operating systems, which also depend on the kubernetes
distribution, are supported: 

| Operating System               | Versions     |
|--------------------------------|--------------|
| Alma Linux                     | 9, 10        |
| Rocky Linux                    | 9, 10        |
| Redhat Enterprise Linux (RHEL) | 9, 10        |
| Ubuntu                         | 22.04, 24.04 |   
| Debian                         | 12, 13       |
| Talos                          | from 1.6.7   |

The operating system must be on the latest patch-level.


# Operating System Requirements (Initiator)

An initiator is the operating system to which simplyblock logical volumes are attached over the network (NVMe/TCP).

For further information on the requirements of the initiator-side (client-only), see:

- [Linux Distributions and Versions](../../reference/supported-linux-distributions.md)
- [Linux Kernel Versions](../../reference/supported-linux-kernels.md)

# Kubernetes Requirements

For Kubernetes-based deployments, the following Kubernetes environments and distributions are supported:

| Distribution         | Versions        |
|----------------------|-----------------|
| Amazon EKS           | 1.28 and higher |
| Google GKE           | 1.28 and higher |
| K3s                  | 1.29 and higher |
| Kubernetes (vanilla) | 1.28 and higher |
| Talos                | 1.6.7 and higher|
| Openshift            | 4.15 and higher |

# Proxmox Requirements

The Proxmox integration supports any Proxmox installation of version 8.0 and higher.

# OpenStack Requirements

Officially supported is OpenStack from version 25.1 (Epoxy), but support for older versions may
be available on request.


