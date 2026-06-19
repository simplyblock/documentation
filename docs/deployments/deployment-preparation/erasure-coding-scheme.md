---
title: "Erasure Coding Scheme"
description: "Choosing the appropriate erasure coding scheme is crucial when deploying a simplyblock storage cluster, as it directly impacts data redundancy, storage."
weight: 30100
---

Choosing the appropriate **erasure coding scheme** is crucial when deploying a simplyblock storage cluster, as it
directly impacts **data redundancy, storage efficiency, and overall system performance**. Simplyblock currently supports
the following erasure coding schemes: **1+0**, **1+1**, **2+1**, **4+1**, **1+2**, **2+2**, and **4+2**. Understanding the
trade-offs between redundancy and storage utilization will help determine the best option for your workload. All schemas
have been performance-optimized by specialized algorithms. There is, however, a remaining capacity-to-performance
trade-off.

## Erasure Coding Schemes

Erasure coding (EC) is a **data protection mechanism** that distributes data and parity across multiple storage nodes,
allowing data recovery in case of hardware failures. The notation **k+m** represents:

- **k**: The number of data fragments.
- **m**: The number of parity/coding fragments.

If you need more information on erasure coding, see the dedicated concept page for
[erasure coding](../../architecture/concepts/erasure-coding.md).

The table below gives an overview of the supported schemes:

- **FTT** (failures to tolerate) is the number of storage nodes that can fail with no data loss (`m`).
- **Data protection overhead** is the additional raw capacity stored on top of the usable data (e.g. 100% means the
  cluster holds 2× the raw capacity for the usable amount; 0% means no protection).
- **IOPS r/w performance and latency** is a relative rating of read/write IOPS and latency.
- **Minimum nodes** is the number of storage nodes required for full redundancy.

| Schema | FTT | Data protection overhead | IOPS r/w performance & latency | Minimum nodes |
|--------|-----|--------------------------|--------------------------------|---------------|
| 1+0    | 0   | 0%                       | Very good                      | 1             |
| 1+1    | 1   | 100%                     | Excellent                      | 3             |
| 2+1    | 1   | 50%                      | Very good                      | 4             |
| 4+1    | 1   | 25%                      | Very good                      | 6             |
| 1+2    | 2   | 200%                     | Very good                      | 5             |
| 2+2    | 2   | 100%                     | Very good                      | 6             |
| 4+2    | 2   | 50%                      | Very good                      | 8             |

## Choosing the Scheme

When selecting an erasure coding scheme for simplyblock, consider the following:

1. **Redundancy Requirements**: If the priority is maximum data protection and quick recovery, **1+1** or **1+2** are ideal. For a
   balance between protection and efficiency, **2+1** or **2+2** is preferred.
2. **Storage Capacity**: **1+1** requires double the storage space, whereas **2+1** provides better storage efficiency. **1+2** requires triple the storage space, whereas **2+2** provides great storage efficiency and fault tolerance.
3. **Performance Needs**: **1+1** and **2+2** offer faster reads and writes due to mirroring, while **2+1** and **2+2** reduce write amplification and optimize for storage usage.
4. **Cluster Size**: **Smaller clusters** benefit from **1+1** or **1+2** due to its simplicity and faster rebuild times, whereas **2+1** and **2+2** are more effective in **larger clusters**.
5. **Recovery Time Objectives (RTOs)**: If minimizing downtime is critical, **1+1** and **1+2** offer near-instant recovery compared to **2+1** and **2+2** which require rebuilding of the lost data from parity information.
