---
title: "Erasure Coding Scheme"
weight: 30100
---

Choosing the appropriate **erasure coding scheme** is crucial when deploying a simplyblock storage cluster, as it
directly impacts **data redundancy, storage efficiency, and overall system performance**. Simplyblock currently supports
the following erasure coding schemes: **1+1**, **2+1**, **4+1**,  **1+2**, **2+2** and **4+2**. Understanding the trade-offs between
redundancy and storage utilization will help determine the best option for your workload. All schemas have been 
performance-optimized by optimized algorithms, but there is still a remaining capacity-to-performance trade-off.

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
    - Small to mid-sized deployments with **limited storage nodes**.

### Scheme: 2+1

- **Description:** In the _2+1 scheme_, data is divided into two fragments with one parity fragment, offering a
  balance between redundancy and storage efficiency.
- **Redundancy Level:** Can tolerate the failure of **one** storage node.
- **Raw-to-effective ratio:** **150%** 
- **Performance Considerations:** **Lower write amplification** compared to **1+1**, as data is distributed across multiple nodes.
- **Best Use Cases:**
    - Deployments where **storage efficiency is a priority** without significantly compromising redundancy.
    - Slight degradation of read performance compared to **1+1**
    - Degradation of write IOPS performance compared to **1+1** only in the case of small writes (4K). Latency can degrade by about 50% in that case.
    - Both read and write performance are impacted in case of degraded cluster (node outage).   
    - Larger storage clusters where **balanced resource utilization** is necessary.

### Scheme: 4+1

- **Description:** In the _2+1 scheme_, data is divided into four fragments with one parity fragment, offering
  optimal storage efficiency.
- **Redundancy Level:** Can tolerate the failure of **one** storage node.
- **Raw-to-effective ratio:** **125%** 
- **Performance Considerations:** **Lower write amplification** compared to **1+1**, as data is distributed across multiple nodes.
- **Best Use Cases:**
    - Deployments where **storage efficiency is a priority** without significantly compromising redundancy.
    - Degradation of write IOPS performance compared to **1+1** only in the case of smaller writes (<16K). Latency can degrade by about 50% in that case.
    - Both read and write performance are more strongly impacted in case of degraded cluster (node outage).   
    - Larger storage clusters where **balanced resource utilization** is necessary.

### Scheme: 1+2

- **Description:** In the _1+2 scheme_, data is replicated twice, effectively creating multiple copies of every data block.
- **Redundancy Level:** Can tolerate the failure of **two** storage nodes.
- **Raw-to-effective ratio:** **300%** 
- **Performance Considerations:** Offers **fast recovery and high read performance** due to data replication.
- **Best Use Cases:**
    - Workloads requiring **highest availability and minimal recovery time**.
    - Applications where **performance is prioritized over storage efficiency**.
    - Read performance comparable to **1+1**, write performance reduced by 1/3 (three times write amplifiction instead of 2).
    - Small to mid-sized deployments with less perspective on **storage requirements**.

### Scheme: 2+2

- **Description:** In the _2+1 scheme_, data is divided into two fragments with two parity fragments, offering a great
  balance between redundancy and storage efficiency.
- **Redundancy Level:** Can tolerate the failure of **two** storage nodes.
- **Raw-to-effective ratio:** **200%**
- **Performance Considerations:** **Lower write amplification** compared to **1+2**, as data is distributed across multiple nodes.
- **Best Use Cases:**
    - Deployments where **storage efficiency is a priority** without compromising redundancy.
    - Applications that can tolerate slightly **higher recovery times** compared to **1+2**.
    - Larger storage clusters where **resource utilization** is necessary.
 
  ### Scheme: 4+2

- **Description:** In the _2+1 scheme_, data is divided into four fragments with two parity fragments, offering a great
  balance between redundancy and storage efficiency.
- **Redundancy Level:** Can tolerate the failure of **two** storage nodes.
- **Raw-to-effective ratio:** **150%**
- **Performance Considerations:** **Lower write amplification** compared to **1+2**, as data is distributed across multiple nodes.
- **Best Use Cases:**
    - Deployments where **high redundancy and storage efficiency is a priority**.
    - Degradation of write IOPS performance compared to **1+1** only in the case of smaller writes (<16K). Latency can degrade by about 50% in that case.
    - Both read and write performance are more strongly impacted in case of degraded cluster (node outage).   
    - Larger storage clusters where **balanced resource utilization** is necessary.

## Choosing the Scheme

When selecting an erasure coding scheme for simplyblock, consider the following:

1. **Redundancy Requirements**: If the priority is maximum data protection and quick recovery, **1+1** or **1+2** is ideal. For a
   balance between protection and efficiency, **2+1** or **2+2** is preferred.
2. **Storage Capacity**: **1+1** requires double the storage space, whereas **2+1** provides better storage efficiency. **1+2** requires triple the storage space, whereas **2+2** provides great storage efficiency and fault tolerance.
3. **Performance Needs**: **1+1** and **2+2** offer faster reads and writes due to mirroring, while **2+1** and **2+2** reduce write amplification and optimize for storage usage.
4. **Cluster Size**: **Smaller clusters** benefit from **1+1** or **1+2** due to its simplicity and faster rebuild times, whereas **2+1** and **2+2** are more effective in **larger clusters**.
5. **Recovery Time Objectives (RTOs)**: If minimizing downtime is critical, **1+1** and **1+2** offer near-instant recovery compared to **2+1** and **2+2** which require rebuilding of the lost data from parity information.
