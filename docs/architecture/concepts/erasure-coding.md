---
title: "Erasure Coding"
description: "Erasure coding is a data protection mechanism used in distributed storage systems to enhance fault tolerance and optimize storage efficiency."
weight: 30600
---

Erasure coding is a data protection mechanism used in distributed storage systems to enhance fault tolerance and
optimize storage efficiency. It provides redundancy by dividing data into multiple fragments and encoding it with
additional parity fragments, enabling data recovery in the event of node failures.

Traditional data redundancy methods, such as replication, require multiple full copies of data, leading to significant
storage overhead. Erasure coding improves upon this by using mathematical algorithms to generate parity fragments,
allowing data reconstruction with lower overhead.

The core principle of erasure coding involves breaking data into **k** data fragments and computing **m** parity
fragments. These **k+m** fragments are distributed across multiple storage nodes. The system can recover lost data using
any **k** available fragments, even if up to **m** fragments are missing or corrupted.

In simplyblock, we support **k** values of 1, 2, and 4, as well as **m** values of 0, 1, and 2. It is important to
note that we use distributed erasure coding, in which every chunk of a stripe is stored on a different node. This
way, we not only protect data from drive loss but also ensure data availability in case one or two nodes are not
operational.

Erasure coding has a number of key characteristics:

- **High Fault Tolerance:** Erasure coding can tolerate multiple node failures while allowing full data recovery.
- **Storage Efficiency:** Compared to replication, erasure coding requires less additional storage to achieve similar levels of redundancy.
- **Flexibility:** The parameters **k** and **m** can be adjusted to balance redundancy, performance, and storage overhead.
