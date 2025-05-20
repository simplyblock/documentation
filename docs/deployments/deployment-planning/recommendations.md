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
