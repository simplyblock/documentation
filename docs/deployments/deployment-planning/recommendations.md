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
