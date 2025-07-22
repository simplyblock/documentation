---
title: System Requirements
weight: 29999
---

The Simplyblock storage nodes run on systems with both _arm_ and _x86_ (_intel_, _amd_) processors and on bare metal as well as virtual machines (compute instances). In case of a virtualized environment, PCIe virtualization pass-through is required for both NVMEs and NICs. They can be deployed both hyper-converged (combined with other workloads) or disaggregated (dedicated hosts or vms for storage).

For production, simplyblock control plane requires three management nodes on _x86_ with a minimum of 4 vcpu (2 cores) and 16 GiB RAM for each of them. Currently, the control plane requires _RHEL/Alma/Rocky 9_. 

Simplyblock requires a minimum of 8 dedicated (not shared) vcpu, 32 GiB of dedicated RAM (not shared with other applications) and  2 x 10 gb/s of network bandwidth per node, which is preferably dedicated to the storage (separate storage _vlan_). In production, Simplyblock requires a HA network for storage traffic (e.g. via LACP, Stacked Switches, MLAG, active/active or active/passive NICs, STP or MSTP) and it is recommended to use a separate NIC, which should also be highly available, for network traffic. Simplyblock requires a TCP/IP network and all storage nodes in a cluster and hosts connected should reside in the same _vlan_ for performance reasons. 

Simplyblock is numa-aware and can run on one or two socket systems. A minimum of one storage node per numa socket has to be deployed per host for production use cases. 
Therefore, if more than one sockets are present on a host, they can only be used for Simplyblock Storage, if each of them has a separate NIC and directly connected NVMEs.

For dedicated storage hosts with  32 or more vcpu (16 or more physical cores) per socket, it is highly recommended to turn off hyper-threading for performance reasons. 

NVMe must support 4KB native block size and should be sized in between 1.9 TiB and 7.68 TiB. While larger NVMEs (32 and 64 TiB) are generally supported, their performance profile and rebuild time are typically not in alignment with high-performance storage and rebuild times are higher. Within a single cluster, all NVMEs must be of the same size. Simplyblock is SSD-vendor agnostic, but recommends NVMEs of the same model within a cluster. This is not a hard requirement, in particular if new (replacement) devices are faster than the installed ones.  

PCIe 3.0 is a minimum requirement and if possible, PCIe 4.0 or higher is recommended.

For maximum performance and depending on the capacity of the NVMEs, a dedicated storage network bandwidth of at least 10 gb/s is recommended per NVME and not more than 10 NVME are recommended per socket. 

A maximum of 10 NVMe is currently supported per storage node.

RAM requirements per node are:
| VM Type                    | RAM      | 
|----------------------------|----------|
| Base*                      | 3 GB     | 
| Per lvol*                  | 0.025 GB | 
| Per TB of cluster storage**| 2 GB     | 

*consumed as huge page memory
*consumed as combined huge page and system memory requirements

## AWS Amazon EC2 Recommendations

Simplyblock can work with local instance storage (local NVMe devices) and Amazon EBS volumes. For performance reasons,
Amazon EBS is not recommended for high-performance clusters.

!!! Critical
    If local NVMe devices are chosen, make sure that the nodes in the cluster are provisioned into a placement group of type _Spread_!

Generally, with AWS, there are three considerations when selecting virtual machine types:

- Minimum requirements of vCPU and RAM
- Locally attached NVMe devices
- Network performance (dedicated and "up to")

Based on those criteria, simplyblock commonly recommends the following virtual machine types for storage nodes:

| VM Type         | vCPU(s) | RAM    | Locally Attached Storage | Network Performance |
|-----------------|---------|--------|--------------------------|---------------------|
| _i4g.8xlarge_   | 32      | 256 GB | 2x 3750 GB               | 18.5 GBit/s         |
| _i4g.16xlarge_  | 64      | 512 GB | 4x 3750 GB               | 37.5 GBit/s         |
| _i3en.6xlarge_  | 24      | 192 GB | 2x 7500 GB               | 25 GBit/s           |
| _i3en.12xlarge_ | 48      | 384 GB | 4x 7500 GB               | 50 GBit/s           |
| _i3en.24xlarge_ | 96      | 768 GB | 8x 7500 GB               | 100 GBit/s          |
| _m5d.4xlarge_   | 16      | 64 GB  | 2x 300 GB                | 10 GBit/s           |
| _i4i.8xlarge_   | 32      | 256 GB | 2x 3750 GB               | 18.75 GBit/s        |
| _i4i.12xlarge_  | 48      | 384 GB | 3x 3750 GB               | 28.12 GBit/s        |


## Google Compute Engine Recommendations

In GCP, physical hosts are highly-shared and sliced into virtual machines. This isn't only true for network CPU, RAM,
and network bandwidth, but also virtualized NVMe devices. Google Compute Engine NVMe devices provide a specific number
of queue pairs (logical connections between the virtual machine and physical NVMe device) depending on the size of the
disk. Hence, separately attached NVMe devices are highly recommended to achieve the required number of queue pairs of
simplyblock.

!!! Critical
    If local NVMe devices are chosen, make sure that the nodes in the cluster are provisioned into a placement group of type _Spread_!

Generally, with GCP, there are three considerations when selecting virtual machine types:

- Minimum requirements of vCPU and RAM
- The size of the locally attached NVMe devices (SSD Storage)
- Network performance

Based on those criteria, simplyblock commonly recommends the following virtual machine types for storage nodes:

| VM Type          | vCPU(s) | RAM    | Additional Local SSD Storage | Network Performance |
|------------------|---------|--------|------------------------------|---------------------|
| _n2-standard-8_  | 8       | 32 GB  | 2x 2500 GB                   | 16 GBit/s           |
| _n2-standard-16_ | 16      | 64 GB  | 2x 2500 GB                   | 32 GBit/s           |
| _n2-standard-32_ | 32      | 128 GB | 4x 2500 GB                   | 32 GBit/s           |
| _n2-standard-48_ | 48      | 192 GB | 4x 2500 GB                   | 50 GBit/s           |
| _n2-standard-48_ | 48      | 192 GB | 4x 2500 GB                   | 50 GBit/s           |
| _n2-standard-64_ | 64      | 256 GB | 6x 2500 GB                   | 75 GBit/s           |
| _n2-standard-80_ | 64      | 320 GB | 8x 2500 GB                   | 100 GBit/s          |

### Attaching an additional Local SSD on Google Compute Engine

The above recommended instance types do not provide NVMe storage by default. It has to specifically be added to the
virtual machine at creation time. It cannot be changed after the virtual machine is created.

To add additional Local SSD Storage to a virtual machine, the operating system section must be selected in the wizard,
then "Add local SSD" must be clicked. Now an additional disk can be added.

!!! warning
     It is important that NVMe is selected as the interface type. SCSI will not work!

![Google Compute Engine wizard screenshot for adding additional local SSDs to a virtual machine](../../assets/images/gcp-wizard-local-ssd.png)

