---
title: Hardware Requirements
description: "Minimum vCPU, RAM, NVMe device, network, and boot disk requirements for simplyblock storage nodes and control plane nodes, per deployment model."
weight: 29989
---

The hardware requirements of a simplyblock cluster are defined per node and per plane. A storage node
is sized by its vCPUs, RAM, locally attached NVMe devices, and network bandwidth. A control plane node
is sized by the number of storage nodes and objects it manages. Beyond those resources, constraints
apply to the CPU architecture, the NVMe devices, and the storage network.

## Minimum System Requirements

The following minimum system requirements resources must be exclusive to simplyblock and are not available to the host
operating system or other processes. This includes vCPUs, RAM, locally attached virtual or physical NVMe devices,
network bandwidth, and free space on the boot disk.

### Overview

| Node Type    | vCPU(s) | RAM (GB) | Locally Attached Storage         | Network Performance | Free Boot Disk | Number of Nodes  |
|--------------|---------|----------|----------------------------------|---------------------|----------------|------------------|
| Storage Node | 8+      | 6+ DDR4  | 2x dedicated NVMe <sup>(1)</sup> | 10 GBit/s           | 10 GB          | 3 <sup>(2)</sup> |

<span style="font-size: 0.8em;">
<sup>1</sup> One NVMe device is sufficient for a test setup, but it is not approved for production. Since Simplyblock 26.3, a cluster can also be deployed on any SATA or SAS Linux block device. See [Linux Block Devices (lblk)](../architecture/concepts/linux-block-devices.md).<br>
<sup>2</sup> The required number of nodes is only valid for erasure coding scheme 1+1.
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

Each NUMA socket requires directly attached NVMe devices and NICs to deploy a storage node. If more
than 32 cores are available per socket, multiple storage nodes per storage host are recommended.

During deployment, simplyblock detects the underlying configuration and prepares a configuration file
with the recommended deployment strategy, including the recommended amount of storage nodes per
storage host based on the detected configuration. This file is later processed when adding the storage
nodes to the storage host. Manual changes to the configuration are possible if the proposed
configuration is not applicable.

For more information on simplyblock on NUMA, see [NUMA Considerations](numa-considerations.md).

### Hyper-Converged Sizing Guidance

As hyper-converged deployments have to share vCPUs, it is recommended to dedicate 15%-20%, but not less than
8 vCPU per socket to simplyblock. For example, on a system with 32 cores (64 vCPU) per socket, this amounts to
12.5% of vCPU capacity per host. For very IO-intensive applications, this amount should be increased.

### Storage Node Isolation Behavior

!!! warning
    On storage nodes, the required vCPUs can be isolated from the operating system. No kernel-space
    process, user-space process, or interrupt handler is then scheduled on those vCPUs. Tail latency
    and performance consistency are improved significantly by that isolation.

    On dedicated storage nodes outside Kubernetes, core isolation is performed automatically on the
    host if that option is chosen at deployment time. In Kubernetes, the CPU Manager and the Topology
    Manager are used by default, but the core isolation itself is opt-in and requires additional
    configuration on both the cluster and the host.

### Storage Node Memory Sizing Formula

For RAM, it is required to define the maximum number of NVMe-oF subsystems per node. This depends on
the assigned vCPUs and networking performance of the node. For each 10 GBit/s of dedicated network bandwidth
it is recommended to use at least 3 subsystems. For each vCPU exceeding 8, it is recommended to use one additional
subsystem. Use the lower of both values (dedicated network bandwidth, vCPUs). A hard limit of 75 subsystems per
node applies. See [Limits](../reference/limits.md).

| Unit                                     | Memory Requirement |
|------------------------------------------|--------------------|
| Fixed amount                             | 3 GiB              |
| Per subsystem (cluster average per node) | 35 MiB             |
| Per TiB of storage capacity on the host  | 0.5 GiB            |

## Control Plane Requirements

The minimum requirements of the simplyblock control plane are 4 vCPU, 8 GiB of RAM, and about 25 GiB
of disk space per replica, on each of three nodes. Three nodes are the minimum for a highly available
setup. In Kubernetes, the replicas are placed on workers or on Kubernetes control plane nodes, while
in non-Kubernetes deployments the nodes are usually virtual machines.

The disk space also accounts for the state database. In addition, an S3 bucket of at least 50 GB is
highly recommended to hold the backups of that database.

!!! important
    Three replicas across three nodes are mandatory for FoundationDB, the key-value store of the
    control plane. The Management API runs as a DaemonSet on all workers, unless a taint is applied.
    The observability stack can optionally be replicated, and the remaining control plane services
    run without replication.

### Control Plane Scaling Triggers

A control plane cluster of that size manages up to three storage nodes and 18,000 objects, of which
up to half can be logical volumes. For larger deployments, the resources of the management nodes are
increased accordingly. Per managed storage node above three, 1 vCPU, 2 GB of RAM, 5 GB of disk space,
and 5 GB of backup space are added.

### Observability Stack Sizing

Additionally, a non-production observability stack can be deployed. It is distributed across
Kubernetes control plane nodes or workers, and Thanos is the only replicated service. In total, at
least 8 vCPU, 20 GB of RAM, and 125 GB of disk space are required. The disk space requirement grows
significantly with a retention period above three days and with more than three nodes.

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
    Since Simplyblock 26.3, storage can also be onboarded from any Linux block device, such as a SATA
    or SAS SSD, instead of an NVMe PCIe device. The device mode is chosen once per cluster, at cluster
    creation. See [Linux Block Devices (lblk)](../architecture/concepts/linux-block-devices.md).

### NVMe Uniformity Recommendations

In general, all NVMe devices used in a single cluster should exhibit a similar performance profile
per TB. Therefore, within a single cluster, all NVMe devices are recommended to be of the same size,
but this is not a hard requirement.

The same recommendation applies to the Linux block devices of a cluster running in `lblk` mode.

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
    In a cluster running in `lblk` mode, the block devices remain attached under Linux. To become
    eligible, they have to be unmounted and unpartitioned. A device that carries a partition table is
    accepted only if it is explicitly force-formatted at node addition.

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
    NICs with RDMA/RoCEv2 support, such as NVIDIA Mellanox network adapters (ConnectX-6 or higher),
    can be used to deploy RoCEv2 fabrics over standard Ethernet infrastructure. Latency and tail
    latency over a RoCEv2 fabric are usually significantly lower than over TCP.

### Management Traffic Network Requirements

It is recommended to use a separate physical NIC with two ports (bonded) and a highly available network for
management traffic. For management traffic, a 1 GBit/s network is sufficient and a Linux Bridge may be used.

!!! important "Highly Available Control Plane"
    In non-Kubernetes environments, an external load balancer is required when simplyblock is deployed
    with an HA control plane. Requests of users or storage drivers are distributed by it to the active
    control plane nodes, so that the control plane is not a single point of failure while one or more
    management nodes are down.

    For Simplyblock Operator-based deployments, the load balancer is not required, as it is already implemented as
    a Kubernetes Service.

### Layer 2 Constraints and Prohibited Topologies

!!! warning
    Any gateway, firewall, or proxy higher than L2 on the network path should be avoided for
    performance reasons.

## Additional Hardware Guidance

### PCIe Version

The minimum required PCIe standard for NVMe devices is PCIe 3.0. However, PCIe 4.0 or higher is strongly recommended.

### Hyperthreading

If 32 or more physical cores are available per storage node, it is recommended to turn off hyperthreading in the
BIOS setup or UEFI services.
