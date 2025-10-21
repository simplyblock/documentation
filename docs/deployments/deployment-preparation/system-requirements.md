---
title: System Requirements
weight: 29999
---

!!! info
    In cloud environments including GCP and AWS, instance types are pre-configured. In general,  
    there are no restrictions on instance types as long as these system requirements and
    [Node Sizing Requirements](node-sizing.md) are met. However, it is highly recommended to
    stay with the [Recommended Cloud Instance Types](cloud-instance-recommendations.md).

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

- **Plain Linx**: In plain Linux mode, Storage Nodes are currently only deployed dis-aggregated (to separate storage hosts or VMs).
  To operate Simplyblock under Plain Linux Deployment, basic knowledge on Docker is required, but all
  management is performed within the system via its CLI or API. This deployment option requires 
  separate VMs for the control plane and a Rocky/RHEL/Alma-based Linux.
- **Kubernetes**: In Kubernetes, both dis-aggregated deployments (dedicated workers or even clusters for storage nodes) or hyper-converged 
  deployments (combined with compute) are supported. A wide range of Kubernetes distros and OSes are supported.
  Knowledge on administration of Kubernetes is required.

  
The minimum system requirements below concern simplyblock only and must be dedicated to simplyblock.

## Minimum System Requirements

!!! Info
    If the use of erasure coding is intended, DDR5 RAM is recommended for maximum performance. 
    CPUs with large L1 caches will perform better too.

The following minimum system requirements resources must be exclusive to simplyblock and are not available to the host
operating system or other processes. This includes vCPUs, RAM, locally attached virtual or physical NVMe devices,
network bandwidth, and free space on the boot disk.

| Node Type     | vCPU(s) | RAM   | Locally Attached Storage | Network Performance | Free Boot Disk | Number of Nodes | 
|---------------|---------|-------|--------------------------|---------------------|----------------|-----------------|
| Storage Node  | 8       | 32 GB | 1x fully dedicated NVMe  | 10 GBit/s           | 10 GB          | 1 (2 for HA)    | 
| Control Plane | 2       | 16 GB | -                        | 1 GBit/s            | 50 GB          | 1 (3 for HA)    | 

 Control Plane can also be co-deployed with storage nodes to the same workers or hosts in Kubernetes.
 In such a deployment, resource requirements spread out across multiple workers in the cluster.
 If you have at least three worker nodes, assume a minimum of 6 GB of extra RAM per worker and 25GB of 
 free disk space per worker for the control plane. Minimum requirements per replica:

| Service                       | vCPU | RAM (GB) | Disk (GB) |                                                                                                                      |
|-------------------------------|------|----------|-----------|
| Key-Value Store               |  1   |    4     |  5        |
| Observability Stack           |  4   |    8     |  25       | 
| Web-API (daemonset)           |  1   |    2     |  0.5      |
| sb-services                   |  1   |    2     |  0.5      |

!!! Info
    3 replicas are mandatory for the Key-Value-Store. The WebAPI runs as a Daemonset on all Workers, if no taint is applied.
    The Observability Stack can optionally be replicated and the sb-services run without replication.  

!!! Warning
    On storage nodes, the vCPUs must be dedicated to simplyblock and will be isolated from the operating system. No
    kernel-space, user-space processes, or interrupt handler can be scheduled on these vCPUs.

!!! Info
    It is recommended to deploy multiple storage nodes per storage host if the host has more than one NUMA socket, or if
    there are more than 32 cores available per socket.

    During deployment, simplyblock detects the underlying configuration and prepares a configuration file with the
    recommended deployment strategy, including the recommended amount of storage nodes per storage host based on the
    detected configuration. This file is later processed when adding the storage nodes to the storage host. 
    
    Manual changes to the configuration are possible if the proposed configuration is not applicable.

## Hyperthreading

If 32 or more physical cores are available per storage node, it is highly recommended to turn off hyperthreading in the
BIOS or UEFI setup services.

## NVMe Devices

NVMe devices must support 4KB native block size and should be sized between 1.9 TiB and 7.68 TiB.

Within a single cluster, all NVMe devices must be of the same size.

Simplyblock is SSD-vendor agnostic but recommends using NVMe devices of the only one vendor and model within a single
cluster. While this is not a hard requirement, it is highly recommended.

If new (replacement) devices are faster than existing installed ones, cluster performance converges to devices with the
lowest performance.

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

## NUMA

Simplyblock is NUMA-aware and can run on one or more NUMA socket systems. A minimum of one storage node per NUMA socket
has to be deployed per host for production use cases.

Each NUMA socket requires directly attached NVMe and NIC to deploy a storage node.

For more information on simplyblock on NUMA, see [NUMA Considerations](numa-considerations.md).

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


