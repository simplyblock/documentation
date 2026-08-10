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

| Node Type    | vCPU(s) | RAM (GB)               | Locally Attached Storage          | Network Performance | Free Boot Disk | Number of Nodes  |
|--------------|---------|------------------------|-----------------------------------|---------------------|----------------|------------------|
| Storage Node | 8+      | 6+ DDR4 <sup>(1)       | 2x dedicated NVMe  <sup>(2)</sup> | 10 GBit/s           | 10 GB          | 3 <sup>(3)</sup> |

<span style="font-size: 0.8em;">
<sup>2</sup> Test setups require a minimum of 1 nvme. From 26.3., we support non-nvme device clusters (any SATA or SAS linux block device), this feature is still experimental.<br>
<sup>3</sup> The required number of nodes is only valid for erasure coding scheme 1+1.
</span>

!!! info
    In cloud environments including GCP and AWS, instance types are pre-configured. In general,
    there are no restrictions on instance types as long as these system requirements are met. However, it is highly
    recommended to stay with the [Recommended Cloud Instance Types](cloud-instance-recommendations.md) for production.

    For [hyper-converged](../architecture/concepts/hyper-converged.md) deployments, it is important that node sizing
    applies to the dedicated resources consumed by simplyblock. Hyper-converged instances must provide enough of
    resources to satisfy both, simplyblock and other compute demand, including the Kubernetes worker itself and the
    operating system.

## Sizing Basics

The supported architectures and sizing behavior depend on the deployment model of the simplyblock components.

## Storage Node Requirements

### Storage Node CPU Sizing

IOPS performance depends on Storage Node vCPU. The maximum performance will be reached with
48 physical cores per socket. In such a scenario, the deployment will dedicate (isolate) 40 cores to
simplyblock data plane (spdk_80xx containers) and the rest will remain under control of Linux.

### Storage Node NUMA Placement

Simplyblock auto-detects NUMA nodes. It will configure and deploy storage nodes per NUMA node.

Each NUMA socket requires directly attached NVMe devices and NICs to deploy a storage node.
detected configuration. This file is later processed when adding the storage nodes to the storage host.
Manual changes to the configuration are possible if the proposed configuration is not applicable.

For more information on simplyblock on NUMA, see [NUMA Considerations](numa-considerations.md).

During deployment, simplyblock detects the underlying configuration and prepares a configuration file with the
recommended deployment strategy, including the recommended amount of storage nodes per storage host based on the
### Hyper-Converged Sizing Guidance

As hyper-converged deployments have to share vCPUs, it is recommended to dedicate 15%-20%, but not less than
8 vCPU per socket to simplyblock. For example, on a system with 32 cores (64 vCPU) per socket, this amounts to
12.5% of vCPU capacity per host. For very IO-intensive applications, this amount should be increased.

### Storage Node Isolation Behavior

!!! warning
    On storage nodes, required vCPUs can be isolated from the operating system. No
    kernel-space, user-space processes, or interrupt handler can be scheduled on these vCPUs. 
    On dedicated storage nodes in Non-Kubernetes deployments, the core isolation is performed
    automatically on the host, if this option is chosen at deployment time. In
    Kubernetes, the CPU Manager and Topology Manager are used per default, but core isolation has
    to be opted-in and requires some additional administrator interventation on k8s and the host.
    Core isolation can significantly improve tail latency and performance consistency.

### Storage Node Memory Sizing Formula

For RAM, it is required to define the maximum number of NVMe-oF subsystems per node. This depends on
the assigned vCPUs and networking performance of the node. For each 10 GBit/s of dedicated network bandwidth
it is recommended to use at least 3 subsystems. For each vCPU exceeding 8, it is recommended to use one additional
subsystem. Use the lower of both values (dedicated network bandwidth, vCPUs). A hard limit of max. 75 subsystems per
node applies. See [Limits](../reference/limits.md).

| Unit                                                     | Memory Requirement |
|----------------------------------------------------------|--------------------|
| Fixed amount                                             | 3 GiB              |
| Per subsystem (cluster average per node)                 | 35 MiB             |
| Per TB of storage capacity on the host                   | 0.5 GiB / TiB      |

## Control Plane Requirements

The simplyblock control plane has different hardware requirements depending on the deployment model.

For the control plane, the minimum requirements per replica are 4 vcpu and 8 GiB of 
RAM as well as about 25 GiB of disk space on each of three 3 nodes. 
In Kubernetes, nodes can be workers or kubernetes control plane (OC) nodes. In Non-Kubernetes deployments,
nodes are usually VMs. A minimum of three nodes is required for an HA setup. 

The disk space also accounts for the State Database. In addition, an S3 bucket of at least 50 GB to store
State Database Backups is highly recommended.

!!! important
        3 replicas across 3 nodes are mandatory for the Key-Value-Store. The WebAPI runs as
        a Daemonset on all Workers, if no taint is applied. The Observability Stack can optionally be
        replicated and the sb-services run without replication.

A control plane cluster of the default size as provided below can manage up to 3 nodes and 
18,000 objects (with up to 50% of objects being volumes). For larger deployments, 
increase the resources of the management nodes accordingly. Add 1 vcpu and 2 GB  of RAM as well as 
5 GB of disk space and 5 GB of backup space per managed storage node above 3. 

Additionally, a non-production observability stack can optionally be deployed.
It can be distributed across OC or worker nodes with only one service (Thanos) being replicated. 
In total it requires at least 8 vCPU and 20 GB of RAM as well as 125 GB of disk space.
The requirements for disk space will significantly increase with a custom retention period (>3 days) 
and the number of nodes (>3). 

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

For storage node production deployments, _SR-IOV_ is required for NVMe devices and network interfaces (NICs). Furthermore,
dedicated cores must be assigned exclusively to the virtual machines running storage node (no over-provisioning).

For deployments on Cloud-based platforms, see [cloud-instance recommendations](cloud-instance-recommendations.md).

### Reference Matrix

A full list of the supported architectures can be found in the
[supported environment reference](../reference/supported-linux-distributions.md) page.

## NVMe Device Requirements

### NVMe Capacity and Performance Guidance

NVMe devices must support 4KB native block size or devices that support 512b native block size with
4KB write atomicity.

The NVMe devices are recommended to be sized between 1.9 TiB and 7.68 TiB. Large NVMe devices are supported,
but performance per TiB is lower and rebalancing can take longer.

Clusters are lightweight, and it is recommended to use different clusters for different types of
hardware (NVMe, networking, compute) or with a different performance profile per TiB of raw storage.

!!! info
        From 26.3, Simplyblock also supports non-nvme devices (SATA/SAS linux block devices). This
        feature is still experimental. 

### NVMe Uniformity Recommendations

In general, all NVMe used in a single cluster should exhibit a similar performance profile per TB.
Therefore, within a single cluster, all NVMe devices are recommended to be of the same size,
but this is not a hard requirement.

The same requirement applies to non-nvme devices, if non-nvme clusters are used.

### NVMe Exclusivity Requirements

Simplyblock only works with non-partitioned, exclusive NVMe devices (virtual via SRV-IO or physical) as its backing
storage.

Individual NVMe namespaces or partitions cannot be claimed by simplyblock, only dedicated NVMe controllers.

!!! important
    Devices are not allowed to be mounted under Linux and the entire device will be low-level formatted and
    re-partioned during deployment.

Additionally, devices will be detached from the operating system's control and will no longer show up in _lsblk_
once simplyblock's storage nodes are running.

!!! info
       For non-nvme clusters, block devices will remain attached under Linux. They have to be unmounted and 
       unpartitioned to be used. Partitioned devices can also be force-formatted at deployment time.

### NVMe Formatting Prerequisites

Simplyblock can low-level format NVMe devices with 4KB block size before deploying simplyblock. This is an optional
step. Low-level formatting can also be executed manually.

!!! warning
    Low-level formatting destroys all data on the device. Ensure to back up any important data before formatting, if
    data is still required.

## Network Requirements

### Storage Traffic Network Requirements

In production, simplyblock works with one of two options:

- A **redundant network** for storage traffic (e.g., via LACP, Stacked Switches, MLAG, active/active or active/passive NICs, STP, or MSTP).
- Two separate VLANs per node for storage traffic, connected via two separate NIC ports and switch paths, as well as configured as ***NVMe Multipathing*** (see [Storage Network Multipathing](../non-kubernetes/installation/storage-network-multipathing.md)).
  In such a setup simplyblock still recommend to provide a **redundant network for management traffic**, but it is not obligatory.

For production, software-defined switches such as Linux Bridge or OVS cannot be used. An interface on top of a Linux
bond over two ports of the NIC(s) or using SRV-IO must be created.

### Fabric and Protocol Notes

Simplyblock implements NVMe over Fabrics (NVMe-oF), either NVMe over TCP or NVMe over RoCEv2, and works over any Ethernet
interconnect. The fabric transport layers can be mixed, like cluster internal-traffic on NVMe over RoCEv2 and client to cluster over NVMe over TCP.

!!! info
    NICs with RDMA/ROCEv2 support such as NVIDIA Mellanox network adapters (ConnectX-6 or higher) can be used to deploy ROCEv2 fabrics over standard Ethernet infrastructure.
    The latency and tail-latency of ROCEv2 fabrics is usually significantly lower than in TCP.

### Management Traffic Network Requirements

It is recommended to use a separate physical NIC with two ports (bonded) and a highly available network for
management traffic. For management traffic, a 1 GBit/s network is sufficient and a Linux Bridge may be used.

!!! important "Highly Available Control Plane"
    When simplyblock is deployed with an HA control plane in non-Kubernetes environments, an external load balancer is required to distribute
    requests of users or storage drivers to active control plane nodes. This is required to ensure that the control plane
    is not a single point of failure when one or more management nodes are down.

    For Simplyblock Operator-based deployments, the load balancer is not required, as it is already implemented as
    a Kubernetes Service.

### Layer 2 Constraints and Prohibited Topologies

!!! warning
    Any gateways, firewalls, or proxies higher than L2 on the network path should be avoided for performance reasons.
## Additional Hardware Guidance

### PCIe Version

The minimum required PCIe standard for NVMe devices is PCIe 3.0. However, PCIe 4.0 or higher is strongly recommended.

### Hyperthreading

If 32 or more physical cores are available per storage node, it is recommended to turn off hyperthreading in the
BIOS setup or UEFI services.
