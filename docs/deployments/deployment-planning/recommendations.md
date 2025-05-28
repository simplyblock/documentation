---
title: System Recommendations
weight: 29999
---

Simplyblock provides system recommendations for three general types of cluster setups. These types are a
_High Performance_, a _High Density_, and one _Standard_ setup, with the former offering the highest throughput and the
lowest latency, the second providing the highest storage capacity, and the latter providing a great compromise between
the other two.

## Standard Setup

Per storage server:

- 2U server with 2 CPU sockets.
- Each socket is supplied with 128 GB RAM.
- Each CPU offers 32 physical cores.
- 11-12x PCIe 4.0 NVMe devices, up to 8 TB each.
- Dual 100 GBit/s NIC per socket configured as a LAG. Preferably, Mellanox Connect-X for RoCEv2.

One of the NVMe devices per CPU socket could be implemented as an SLC NVMe, while all others should be TLC.

## High-Performance Setup

Per storage server:

- 1U server with 2 CPU sockets.
- Each socket is supplied with 128 GB of RAM.
- Each CPU offers 32 physical cores.
- 4-5x PCIe 4.0 NVMe devices with 3-4 TB capacity each.
- Dual 100 GBit/s NIC per socket configured as a LAG. Preferably, Mellanox Connect-X for RoCEv2.

One of the NVMe devices per CPU socket could be implemented as an SLC NVMe, while all others should be TLC.

## High-Density Setup

Per storage server:

- 2U server with 2 CPU sockets.
- Each socket is supplied with 128 GB of RAM.
- Each CPU offers 32 physical cores.
- 2x PCIe 4.0 SLC NVMe devices with 1 TB capacity each.
- 6x PCIe 4.0 TLC NVMe devices with 4 TB capacity each.
- 16x PCIe 4.0 NVMe devices, up to 120 TB capacity each.
- Dual 100 GBit/s NIC per socket configured as a LAG. Preferably, Mellanox Connect-X for RoCEv2.

## Considerations

For throughput-heavy workloads, the network bandwidth is the bottleneck. Increasing the network bandwidth will
provide better performance.

For IOPS-heavy workloads, the CPU will be the bottleneck. Increasing the number of CPU cores will provide better
performance.

For volume encryption, simplyblock utilizes offloading of the AES encryption into hardware. Intel provides better
offloading capabilities and performance than AMD.

ARM64 CPUs are fully supported on storage nodes and recommended for their high CPU core count.

## AWS Amazon EC2 Recommendations

Simplyblock can work with local instance storage (local NVMe devices) and Amazon EBS volumes. For performance reasons,
Amazon EBS is not recommended for high-performance clusters.

Generally, with AWS, there are three considerations when selecting virtual machine types:

- Minimum requirements of vCPU and RAM
- Locally attached NVMe devices
- Network performance (dedicated and "up to")

Based on those criteria, simplyblock commonly recommends the following virtual machine types for storage nodes:

| VM Type         | vCPU(s) | RAM    | Locally Attached Storage | Network Performance |
|-----------------|---------|--------|--------------------------|---------------------|
| _i3en.2xlarge_  | 8       | 64 GB  | 2x 2500 GB               | Up to 25 GBit/s     |
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

