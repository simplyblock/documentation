---
title: "Erasure Coding Scheme"
weight: 30100
---

Choosing the appropriate **erasure coding scheme** is crucial when deploying a simplyblock storage cluster, as it
directly impacts **data redundancy, storage efficiency, and overall system performance**. Simplyblock currently supports
the following erasure coding schemes: **1+1**, **2+1**, **1+2**, and **2+2**. Understanding the trade-offs between
redundancy and storage utilization will help determine the best option for your workload.

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
- **Storage Efficiency:** **50%** (since each piece of data is fully duplicated, requiring double the storage capacity).
- **Performance Considerations:** Offers **fast recovery and high read performance** due to data mirroring.
- **Best Use Cases:**
    - Workloads requiring **high availability and minimal recovery time**.
    - Applications where **performance is prioritized over storage efficiency**.
    - Small to mid-sized deployments with **limited storage nodes**.

### Scheme: 2+1

- **Description:** In the _2+1 scheme_, data is divided into two fragments with one parity fragment, offering a
  balance between redundancy and storage efficiency.
- **Redundancy Level:** Can tolerate the failure of **one** storage node.
- **Storage Efficiency:** **66%** (since one-third of the total capacity is used for parity).
- **Performance Considerations:** **Lower write amplification** compared to **1+1**, as data is distributed across multiple nodes.
- **Best Use Cases:**
    - Deployments where **storage efficiency is a priority** without significantly compromising redundancy.
    - Applications that can tolerate slightly **higher recovery times** compared to **1+1**.
    - Larger storage clusters where **balanced resource utilization** is necessary.

### Scheme: 1+2

- **Description:** In the _1+2 scheme_, data is replicated twice, effectively creating multiple copies of every data block.
- **Redundancy Level:** Can tolerate the failure of **two** storage nodes.
- **Storage Efficiency:** **33%** (since each piece of data is fully duplicated twice, requiring triples the storage capacity).
- **Performance Considerations:** Offers **fast recovery and high read performance** due to data replication.
- **Best Use Cases:**
    - Workloads requiring **high availability and minimal recovery time**.
    - Applications where **performance is prioritized over storage efficiency**.
    - Small to mid-sized deployments with less perspective on **storage requirements**.

### Scheme: 2+2

- **Description:** In the _2+1 scheme_, data is divided into two fragments with two parity fragments, offering a great
  balance between redundancy and storage efficiency.
- **Redundancy Level:** Can tolerate the failure of **two** storage nodes.
- **Storage Efficiency:** **50%** (since half of the total capacity is used for parity).
- **Performance Considerations:** **Lower write amplification** compared to **1+2**, as data is distributed across multiple nodes.
- **Best Use Cases:**
    - Deployments where **storage efficiency is a priority** without compromising redundancy.
    - Applications that can tolerate slightly **higher recovery times** compared to **1+2**.
    - Larger storage clusters where **resource utilization** is necessary.

## Choosing the Scheme

When selecting an erasure coding scheme for simplyblock, consider the following:

1. **Redundancy Requirements**: If the priority is maximum data protection and quick recovery, **1+1** or **1+2** is ideal. For a
   balance between protection and efficiency, **2+1** or **2+2** is preferred.
2. **Storage Capacity**: **1+1** requires double the storage space, whereas **2+1** provides better storage efficiency. **1+2** requires triple the storage space, whereas **2+2** provides great storage efficiency and fault tolerance.
3. **Performance Needs**: **1+1** and **2+2** offer faster reads and writes due to mirroring, while **2+1** and **2+2** reduce write amplification and optimize for storage usage.
4. **Cluster Size**: **Smaller clusters** benefit from **1+1** or **1+2** due to its simplicity and faster rebuild times, whereas **2+1** and **2+2** are more effective in **larger clusters**.
5. **Recovery Time Objectives (RTOs)**: If minimizing downtime is critical, **1+1** and **1+2** offer near-instant recovery compared to **2+1** and **2+2** which require rebuilding of the lost data from parity information.
