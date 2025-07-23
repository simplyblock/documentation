---
title: System Requirements
weight: 29999
---

!!! info
    In cloud environments including gcp and aws, instance types are pre-configured. In general,  
    there are no restrictions on instance types as long as these system  requirements and 
    [node sizing requirements](node-sizing.md) are 
    fullfilled by these instance types. For [hyper-converged](../../architecture/concepts/hyper-
    converged.md) deployments,  it is important that node sizing applies to the dedicated 
    resources consumed by Simplyblock. Hyper-converged instances must provide enough of resources 
    to satisfy both Simplyblock and other compute demand including the k8s worker itself and the 
    operating system.

## Hardware Architecture Support

- For the control plane, simplyblock **requires** x86-64 (AMD64 / Intel 64) compatible CPUs.
- For the storage plane, simplyblock **supports** x86-64 (AMD64 / Intel 64) or ARM64 (AArch64) compatible CPUs.

## Virtualization Support

Both Simplyblock storage nodes and control plane nodes can run on virtualization. It has been tested on plain kvm, proxmox, nitro (aws ec2) and gcp. 
For production and storage nodes, _SR-IOV_ is required for NVMEs and NICs and dedicated cores must be exclusively assigned to the VMs (no over-provisioning).

## Deployment Models

Simplyblock allows deployment of storage nodes in [disaggregated](../../architecture/concepts/disaggregated.md) and a [hyper-converged](../../architecture/concepts/hyper-converged.md) setups. The disaggregated setup requires dedicated hosts (bare metal or vm) for the storage nodes. In hyper-converged setup within kubernetes, simplyblock storage nodes are co-located with other workloads on kubernetes workers.
The minimum system requirements below concern simplyblock only and must be dedicated to simplyblock. 

## Minimum System Requirements

The required resources (vcpu, ram, locally attached     
virtual or physical nvme devices, network bandwidth, free space on boot disk) must be exclusively reserved for and dedicated to simplyblock and are not  
available to the underlying operating system or other processes. 

| Node Type       | vCPU(s) | RAM    | Locally Attached Storage | Network Performance | Free Boot Disk | Number of Nodes | 
|-----------------|---------|--------|--------------------------|---------------------|----------------|-----------------|
| Storage Node    | 8       | 32 GB  | 1x fully dedicated NVMe  | 10 GBit/s           | 10 GB          | 3               | 
| Control Plane   | 2       | 16 GB  | NA                       | 1 GBit/s            | 50 GB          | 3               | 

*disaggregated mode

!!! Warning
    On Storage Nodes, the vcpus must be dedicated to Simplyblock and will be isolated from the operating system so that no kernel-space or user-space 
    processes or interrupt handlers can be scheduled on these vcpu. 

!!! Info
    It is possible and recommended to deploy multiple storage nodes per host, if the node has more than one NUMA socket or if there are more than 32 cores  
    available per socket. During deployment, simplyblock detects the underlying configuration and prepares a configuration file with the recommended deployment, 
    including the recommended amount of storage nodes per host based on the detected configuration. This file is later processed when adding the nodes to the host; 
    it can be edited, if the proposed configuration is not applicable.

## Hyperthreading

If 16 or more physical cores are available per storage node, it is highly recommended to turn off hyperthreading in the UEFI.

## NVMEs

NVMe must support 4KB native block size and should be sized in between 1.9 TiB and 7.68 TiB. 
Within a single cluster, all NVMEs must be of the same size.
Simplyblock is SSD-vendor agnostic but recommends NVMe devices of the same vendor and model within a cluster. This is not a hard
requirement, in particular if new (replacement) devices are faster than existing installed ones, but cluster performance converges to devices with lowest performance.

!!! Warning
    Simplyblock only works with non-partitioned entire NVMe devices (virtual via SRV-IO or physical) as back-storage. 
    Individual NVME namespaces or partitions cannot be claimed by Simplyblock, only entire devices! 
    Devices are not allowed to be mounted under Linux and entire devices will be low-level formatted and re-partioned during deployment.
    Devices will be removed from the operating system control and will not show up any longer in _lsblk_ once Simplyblock storage nodes are running.

!!! Info
    It is required to [low-level format devices](../../reference/nvme-low-level-format.md) with 4KB block size before deploying Simplyblock.

## Network

In production, Simplyblock requires a __HA network__ for storage traffic (e.g. via LACP, Stacked Switches, MLAG, active/active or active/passive NICs, STP or MSTP).

Simplyblock implements NVMe over Fabrics (NVMe-oF) working over any Ethernet interconnect.

!!! recommendation
    Simplyblock recommends NVIDIA Mellanox network adapters (ConnectX-6 or higher). 

For production, do not use software-defined switches such as Linux Bridge or OVS. Create an interface on top of a Linux bond over two ports of the NIC(s)  or using SRV-IO. 

Also it is recommended to use a separate physical NIC with two ports (bonded) and a HA network for management traffic; A 1 gb/s network is sufficient and Linux Bridge may be used. 

!!! warning
    All storage nodes within a cluster and all hosts accessing storage  shall reside within the same hardware vlan. Avoid any gateways or proxies higher than L2 on 
    the network path. 

## PCIe Version

PCIe 3.0 is a minimum requirement, and if possible, PCIe 4.0 or higher is recommended.

## NUMA

Simplyblock is numa-aware and can run on one or two socket systems. A minimum of one storage node per NUMA socket has to
be deployed per host for production use cases. Each NUMA socket requires directly attached NVMe and NIC to deploy a storage node.

## Operating System Requirements (control plane, storage nodes)

__control plane nodes__ as well as __storage nodes__ in disaggregated setup require one of the following: __rocky__, __rhel__ or __alma__, all in version __9__ (latest patch-level).

The storage nodes require rocky, rhel or alma 9 in the disaggregated setup.

In the hyper-converged setup, the following operating systems are supported:

| Operating System           | Versions |
|----------------------------|----------|
| Rocky                      | 9, 10    |
| RHEL                       | 9, 10    |
| Alma                       | 9, 10    |

We are planning to support more operating systems, including multiple versions of Ubuntu, Talos and Debian with the next minor release.

# Operating System Requirements (Initiator)

Initiator is the operating system to which Simplyblock nvme volumes is attached over the network (the nvme-tcp client). The following requirements concern initiators:

[Linux Distributions and Versions](../../reference/supported-linux-distributions.md)

[Linux Kernel Versions](../../reference/supported-linux-kernels.md)

# Kubernetes Requirements

| Distribution               | Versions       |
|----------------------------|----------------|
| eks                        | 1.28 and higher|
| gks                        | 1.28 and higher|
| k3s                        | 1.29 and higher|
| k8s (vanilla)              | 1.28 and higher|
| openshift                  | 4.15 and higher|

# ProxMox Requirements

ProxMox is supported from version 8.0 and higher.
