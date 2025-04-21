---
title: "Erasure Coding Scheme"
weight: 30100
---

Choosing the appropriate **erasure coding scheme** is crucial when deploying a simplyblock storage cluster, as it
directly impacts **data redundancy, storage efficiency, and overall system performance**. Simplyblock currently supports
the following erasure coding schemes: **1+1**, **2+1**, **4+1**,  **1+2**, **2+2** and **4+2**. Understanding the trade-offs between
redundancy and storage utilization will help determine the best option for your workload. All schemas have been 
performance-optimized by specialized algorithms, but there is still a remaining capacity-to-performance trade-off.

## Erasure Coding Schemes

Erasure coding (EC) is a **data protection mechanism** that distributes data and parity across multiple storage nodes,
allowing data recovery in case of hardware failures. The notation **k+m** represents:

- **k**: The number of data fragments.
- **m**: The number of parity fragments.

If you need more information on erasure coding, see the dedicated concept page for
[erasure coding](../../architecture/concepts/erasure-coding.md).

### Scheme: 1+1

- **Description:** In the _1+1 scheme_, data is mirrored, effectively creating an exact copy of every data block.
- **Redundancy Level:** Can tolerate the failure of **one** storage node.
- **Raw-to-effective ratio:** **200%** 
- **Performance Considerations:** Offers **fast recovery and high read performance** due to data mirroring.
- **Best Use Cases:**
    - Workloads requiring **high availability and minimal recovery time**.
    - Applications where **performance is prioritized over storage efficiency**.
    - Requires 3 or more nodes for full redundancy.

### Scheme: 2+1

- **Description:** In the _2+1 scheme_, data is divided into two fragments with one parity fragment, offering a
  balance between performance and storage efficiency.
- **Redundancy Level:** Can tolerate the failure of **one** storage node.
- **Raw-to-effective ratio:** **150%** 
- **Performance Considerations:** For writes of 8K or higher, **Lower write amplification** compared to **1+1**, as data is distributed across multiple nodes, typically resulting in similar or better write iops performance. However, for small random writes (4K), the write performance is worse. Write latency somewhat higher than in **1+1**. Read performance is similar to **1+1**, if local node affinity is not enabled and a bit worse (up to 25%) otherwise. In a degraded state (one node offline or unavailable or failed disk), the performance is worse than in **1+1**. Recovery time to full redundancy from single disk error is slightly higher than for **1+1**.
- **Best Use Cases:**
    - Deployments where **storage efficiency is relevant** without significantly compromising performance.
    - Requires 4 or more nodes for full redundancy  


### Scheme: 4+1

- **Description:** In the _4+1 scheme_, data is divided into four fragments with one parity fragment, offering
  optimal storage efficiency.
- **Redundancy Level:** Can tolerate the failure of **one** storage node.
- **Raw-to-effective ratio:** **125%** 
- **Performance Considerations:** For writes of 16K or higher, **Lower write amplification** compared to **2+1**, as data is distributed across more nodes, typically resulting in similar or better write iops performance. However, for 4-8K random writes, the write performance is worse. Write latency somewhat similar as in **2+1**. Read performance is similar to **2+1**, if local node affinity is not enabled and a bit worse (up to 13%) otherwise. In a degraded state (one node offline or unavailable or failed disk), the performance is worse than in **2+1**. Recovery time to full redundancy from single disk error is slightly higher than for **2+1**.
- **Best Use Cases:**
    - Deployments where **storage efficiency is a priority** without significantly compromising performance.
    - Requires 6 or more nodes for full redundancy

### Scheme: 1+2

- **Description:** In the _1+2 scheme_, data is replicated twice, effectively creating multiple copies of every data block.
- **Redundancy Level:** Can tolerate the failure of **two** storage nodes.
- **Raw-to-effective ratio:** **300%** 
- **Performance Considerations:** Offers **fast recovery and high read performance** due to data replication, but write performance is lower than on **1+1** in all cases by about 33%.
- **Best Use Cases:**
    - Workloads requiring **high redundancy and minimal recovery time**.
    - Applications where **performance is prioritized over storage efficiency**.
    - Requires 4 or more nodes for full redundancy.

### Scheme: 2+2

- **Description:** In the _2+2 scheme_, data is divided into two fragments with two parity fragments, offering a great
  balance between redundancy and storage efficiency.
- **Redundancy Level:** Can tolerate the failure of **two** storage nodes.
- **Raw-to-effective ratio:** **200%**
- **Performance Considerations:** Similar to **2+1**, but higher write times (lower effective write iops) due to higher write amplification.
- **Best Use Cases:**
    - Deployments where **high redundancy and storage efficiency is important** without compromising redundancy.
    - Applications that can tolerate slightly **higher recovery times** compared to **1+2**.
    - Requires 5 or more nodes in a cluster.
 
  ### Scheme: 4+2

- **Description:** In the _2+1 scheme_, data is divided into four fragments with two parity fragments, offering a great
  balance between redundancy and storage efficiency.
- **Redundancy Level:** Can tolerate the failure of **two** storage nodes.
- **Raw-to-effective ratio:** **150%**
- **Performance Considerations:** Similar to **4+1**, but higher write times (lower effective write iops)  due to higher write amplification.
- **Best Use Cases:**
    - Deployments where **high redundancy and storage efficiency is a priority**.
    - Requires 7 or more nodes in a cluster.

## Choosing the Scheme

When selecting an erasure coding scheme for simplyblock, consider the following:

1. **Redundancy Requirements**: If the priority is maximum data protection and quick recovery, **1+1** or **1+2** are ideal. For a
   balance between protection and efficiency, **2+1** or **2+2** is preferred.
2. **Storage Capacity**: **1+1** requires double the storage space, whereas **2+1** provides better storage efficiency. **1+2** requires triple the storage space, whereas **2+2** provides great storage efficiency and fault tolerance.
3. **Performance Needs**: **1+1** and **2+2** offer faster reads and writes due to mirroring, while **2+1** and **2+2** reduce write amplification and optimize for storage usage.
4. **Cluster Size**: **Smaller clusters** benefit from **1+1** or **1+2** due to its simplicity and faster rebuild times, whereas **2+1** and **2+2** are more effective in **larger clusters**.
5. **Recovery Time Objectives (RTOs)**: If minimizing downtime is critical, **1+1** and **1+2** offer near-instant recovery compared to **2+1** and **2+2** which require rebuilding of the lost data from parity information.
