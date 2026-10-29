---
title: Architecture
description: "Architecture: Simplyblock is a cloud-native, software-defined storage platform designed for high performance, scalability, and resilience."
weight: 10080
---

Simplyblock is a cloud-native, software-defined storage platform designed for high performance, scalability, and
resilience. It provides NVMe over TCP (NVMe/TCP) and NVMe over RDMA (ROCEv2) block storage, enabling efficient data
access across distributed environments.

!!! Info
    In addition to NVMe-over-Fabric block storage, Simplyblock now also provides high-performance file and object storage (S3).
    All storage interfaces are built over the same distributed, high-performance, scale-out storage platform with the 
    same capabilities for data protection, distributed erasure coding, security, encryption, asynchronous or synchronous 
    replication and disaster recovery, built-in backup and restore - including automated cyber-attack recovery- and optional    
    compression and deduplication. Because the high-speed data path is decoupled from the meta-data path for file- and 
    object storage, the performance (latency, IOPS and throughput) is similar to the native block storage performance. 

Understanding the architecture, key concepts, and common terminology is
essential for effectively deploying and managing simplyblock across different infrastructure setups, including
Kubernetes clusters, virtualized environments, and bare-metal deployments. This documentation provides a comprehensive
overview of simplyblock's internal architecture, the components that power it, and recommended practices for
integrating it into an existing storage infrastructure.

This section covers several critical topics, including the architecture of simplyblock, core concepts such as Logical
Volumes (LVs), Storage Nodes, and Management Nodes, as well as Quality of Service (QoS) mechanisms and redundancy
strategies. In addition, it defines common terminology used throughout the documentation to ensure clarity and
consistency. Readers will also find guidance on documentation conventions, such as formatting, naming standards, and
command syntax, which help maintain consistency across technical content.

Simplyblock is an evolving platform, and community contributions play an important role in improving its documentation.
Feedback from developers, storage administrators, and end users alike is valuable. This section also provides
details on how to contribute to the documentation, report issues, suggest improvements, and submit pull requests.
Every contribution helps keep the simplyblock documentation accurate, current, and useful for all users.
