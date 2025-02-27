---
title: "Network Considerations"
weight: 30200
---

Simplyblock is a distributed storage platform. Hence, it highly relies on a strong network infrastructure for the
performance and reliability of its virtual block storage devices (logical volume). 

## Network Type

Protocol-wise, simplyblock implements
[NVMe over Fabrics (NVMe-oF)](../../important-notes/terminology.md#nvme-of-nvme-over-fabrics), meaning that simplyblock
does not require any specific network infrastructure such as Fibre Channel or Infiniband, but works over commodity
Ethernet interconnects.

For data transmission, simplyblock provides
[NVMe over TCP (NVMe/TCP)](../../important-notes/terminology.md#nvmetcp-nvme-over-tcp) and
[NVMe over RDMA over Converged Ethernet (NVMe/RoCE)](../../important-notes/terminology.md#nvmeroce-nvme-over-rdma-over-converged-ethernet).

## Network Infrastructure

In terms of bandwidth, simplyblock recommends at least 40GBit/s per second interconnects, but higher is better.
Especially with a high number of cluster nodes and logical volumes, simplyblock can easily saturate 200 GBit/s and
more interconnects.

!!! tip "Recommendation"
    Simplyblock recommends NVIDIA Mellanox network adapters. However, every network adapter, including virtual
    ones will work. If using virtual machines, the physical network adapter should be made available to the VM
    using PCI-e passthrough (IOMMU).

Additionally, simplyblock recommends a physically separated storage network or using a VLAN to create a virtually
separated network. This can improve performance and minimize network contention.

!!! tip "Recommendation"
    If VLANs are used, prefer hardware-based VLANs configured in switches over a software-based VLAN with Linux
    bridges.

## Network Configuration

Lastly, simplyblock requires a set of TCP/IP ports to be opened towards specific subnets. The installation
prerequisites for the deployment model of your choice list the required ports. Simplyblock also provides a shell
script to pre-test the most important requirements to ensure a smooth installation.

!!! tip "Recommendation"
    Simplyblock strongly recommends two separate NICs, one for the control plane traffic and one for the storage plane.
    These can be implemented via VLAN. However, we recommend to port-based VLANs configured in the switch over virtual
    VLAN interfaces in Linux.

Additionally, simplyblock strongly recommends to design any network interconnect as a fully redundant connection. All
commonly found solutions to achieve that are supported, including but not limited to LACP and Static LAG configurations,
stacked switches, bonded NICs.

!!! danger
    Simplyblock, internally, always assumes the interconnect to be reliable, failing to provide such an interconnect
    may lead to data loss in failure situations.


