---
title: "Deployment Planning"
weight: 20000
---

Proper deployment planning is essential for ensuring the performance, scalability, and resilience of a simplyblock
storage cluster.

Before installation, key factors such as node sizing, storage capacity, and fault tolerance mechanisms should be
carefully evaluated to match workload requirements. This section provides guidance on sizing management nodes and
storage nodes, helping administrators allocate adequate CPU, memory, and disk resources for optimal cluster performance.

Additionally, it explores selectable erasure coding schemes, detailing how different configurations impact storage
efficiency, redundancy, and recovery performance. Other critical considerations, such as network infrastructure, high
availability strategies, and workload-specific optimizations, are also covered to assist in designing a simplyblock
deployment that meets both operational and business needs.

## System Recommendations

Simplyblock provides system recommendations for three general types of cluster setups. These types are a
_High Performance_, a _High Density_, and one _Standard_ setup, with the former offering the highest throughput and
lowest latency, the second providing highest storage capacity, and the latter providing a great compromise between the
other two.

### Standard Setup

Per storage server:

- 2U server with 2 CPU sockets.
- Each socket supplied with 128 GB RAM.
- Each CPU offering 32 physical cores.
- 11-12x PCIe 4.0 NVMe devices, up to 8 TB each.
- Dual 100 GBit/s NIC per socket configured as a LAG. Preferably Mellanox Connect-X for RoCEv2.

One of the NVMe devices per CPU socket could be implemented as a SLC NVMe, while all other should be TLC.

### High Performance Setup

Per storage server:

- 1U server with 2 CPU sockets.
- Each socket supplied with 128 GB RAM.
- Each CPU offering 32 physical cores.
- 4-5x PCIe 4.0 NVMe devices with 3-4 TB capacity each.
- Dual 100 GBit/s NIC per socket configured as a LAG. Preferably Mellanox Connect-X for RoCEv2.

One of the NVMe devices per CPU socket could be implemented as a SLC NVMe, while all other should be TLC.

### High Density Setup

Per storage server:

- 2U server with 2 CPU sockets.
- Each socket supplied with 128 GB RAM.
- Each CPU offering 32 physical cores.
- 2x PCIe 4.0 SLC NVMe devices with 1 TB capacity each.
- 6x PCIe 4.0 TLC NVMe devices with 4 TB capacity each.
- 16x PCIe 4.0 NVMe devices, up to 120 TB capacity each.
- Dual 100 GBit/s NIC per socket configured as a LAG. Preferably Mellanox Connect-X for RoCEv2.

### Considerations

For throughput-heavy workloads, the network bandwidth is the bottleneck. Increasing the network bandwidth will
provide better performance.

For IOPS-heavy workloads, the CPU will be the bottleneck. Increasing the number of CPU cores will provide better
performance.

For volume encryption, simplyblock utilizes offloading of the AES encryption into hardware. Intel provides better
offloading capabilities and performance than AMD.

ARM64 CPUs are fully supported on storage nodes and recommended for their high CPU core count.
