---
title: "Erasure Coding Scheme"
weight: 30100
---

Choosing the appropriate **erasure coding scheme** is crucial when deploying a simplyblock storage cluster, as it
directly impacts **data redundancy, storage efficiency, and overall system performance**. Simplyblock currently supports
the following erasure coding schemes: **1+1**, **2+1**, **4+1**, **1+2**, **2+2**, and **4+2**. Understanding the
trade-offs between redundancy and storage utilization will help determine the best option for your workload. All schemas
have been performance-optimized by specialized algorithms. There is, however, a remaining capacity-to-performance
trade-off.

!!! Info
    Starting from 25.10.1, it is possible to select alternative erasure coding schemas per volume. However, this feature
    is still experimental (technical preview) and not recommended for production. A cluster must provide sufficient
    nodes for the largest schema used in any of the volumes (e.g., 4+2: min. 6 nodes, recommended 7 nodes).

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
- **Raw-to-Effective Ratio:** **200%**
- **Available Storage Capacity:** **50%**
- **Performance Considerations:** Offers **fast recovery and high read performance** due to data mirroring.
- **Best Use Cases:**
    - Workloads requiring **high availability and minimal recovery time**.
    - Applications where **performance is prioritized over storage efficiency**.
    - Requires 3 or more nodes for full redundancy.

### Scheme: 2+1

- **Description:** In the _2+1 scheme_, data is divided into two fragments with one parity fragment, offering a
  balance between performance and storage efficiency.
- **Redundancy Level:** Can tolerate the failure of **one** storage node.
- **Raw-to-Effective Ratio:** **150%**
- **Available Storage Capacity:** **66.6%**
- **Performance Considerations:** For writes of 8K or higher, **lower write amplification** compared to **1+1**, as data is distributed across multiple nodes. This typically results in similar or higher IOPS. However, for small random writes (4K), the write performance is worse than **1+1**. Write latency is somewhat higher than with **1+1**. Read performance is similar to **1+1**, if local node affinity is disabled. With node affinity enabled, read performance is slightly worse (up to 25%). In a degraded state (one node offline / unavailable or failed disk), the performance is worse than with **1+1**. Recovery time to full redundancy from single disk error is slightly higher than with **1+1**.
- **Best Use Cases:**
    - Deployments where **storage efficiency is relevant** without significantly compromising performance.
    - Requires 4 or more nodes for full redundancy.


### Scheme: 4+1

- **Description:** In the _4+1 scheme_, data is divided into four fragments with one parity fragment, offering
  optimal storage efficiency.
- **Redundancy Level:** Can tolerate the failure of **one** storage node.
- **Raw-to-Effective Ratio:** **125%**
- **Available Storage Capacity:** **80%**
- **Performance Considerations:** For writes of 16K or higher, **lower write amplification** compared to **2+1**, as data is distributed across more nodes. This typically results in similar or higher write IOPS. However, for 4-8K random writes, the write performance is typically worse than **2+1**. Write latency is somewhat similar to **2+1**. Read performance is similar to **2+1**, if local node affinity is disabled. With node affinity enabled, read performance is slightly worse (up to 13%). In a degraded state (one node offline / unavailable or failed disk), the performance is worse than with **2+1**. Recovery time to full redundancy from single disk error is slightly higher than with **2+1**.
- **Best Use Cases:**
    - Deployments where **storage efficiency is a priority** without significantly compromising performance.
    - Requires 6 or more nodes for full redundancy.

### Scheme: 1+2

- **Description:** In the _1+2 scheme_, data is replicated twice, effectively creating multiple copies of every data block.
- **Redundancy Level:** Can tolerate the failure of **two** storage nodes.
- **Raw-to-Effective Ratio:** **300%**
- **Available Storage Capacity:** **33.3%**
- **Performance Considerations:** Offers **fast recovery and high read performance** due to data replication, but write performance is lower than with **1+1** in all cases (~33%).
- **Best Use Cases:**
    - Workloads requiring **high redundancy and minimal recovery time**.
    - Applications where **performance is prioritized over storage efficiency**.
    - Requires 4 or more nodes for full redundancy.

### Scheme: 2+2

- **Description:** In the _2+2 scheme_, data is divided into two fragments with two parity fragments, offering a great
  balance between redundancy and storage efficiency.
- **Redundancy Level:** Can tolerate the failure of **two** storage nodes.
- **Raw-to-Effective Ratio:** **200%**
- **Available Storage Capacity:** **50%**
- **Performance Considerations:** Similar to **2+1**, but with higher write latencies and lower effective write IOPS due to higher write amplification.
- **Best Use Cases:**
    - Deployments where **high redundancy and storage efficiency is important** without compromising redundancy.
    - Applications that can tolerate slightly **higher recovery times** compared to **1+2**.
    - Requires 5 or more nodes for full redundancy.
 
### Scheme: 4+2

- **Description:** In the _4+2 scheme_, data is divided into four fragments with two parity fragments, offering a great
  balance between redundancy and storage efficiency.
- **Redundancy Level:** Can tolerate the failure of **two** storage nodes.
- **Raw-to-Effective Ratio:** **150%**
- **Available Storage Capacity:** **66.6%**
- **Performance Considerations:** Similar to **4+1**, but with higher write latencies and lower effective write IOPS due to higher write amplification.
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
