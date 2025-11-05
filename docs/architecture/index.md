---
title: Architecture
weight: 10100
---

Simplyblock is a cloud-native, software-defined storage platform designed for high performance, scalability, and
resilience. It provides NVMe over TCP (NVMe/TCP) and NVMe over RDMA (ROCEv2) block storage, enabling efficient data
access across distributed environments. Understanding the architecture, key concepts, and common terminology is
essential for effectively deploying and managing simplyblock in various infrastructure setups, including Kubernetes
clusters, virtualized environments, and bare-metal deployments. This documentation provides a comprehensive overview
of simplyblock’s internal architecture, the components that power it, and the best practices for integrating it into
your storage infrastructure.

This section covers several critical topics, including the architecture of simplyblock, core concepts such as Logical
Volumes (LVs), Storage Nodes, and Management Nodes, as well as Quality of Service (QoS) mechanisms and redundancy
strategies. Additionally, we define common terminology used throughout the documentation to ensure clarity and
consistency. Readers will also find guidelines on document conventions, such as formatting, naming standards, and
command syntax, which help maintain uniformity across all technical content.

Simplyblock is an evolving platform, and community contributions play a vital role in improving its documentation.
Whether you are a developer, storage administrator, or end user, your insights and feedback are valuable. This section
provides details on how to contribute to the documentation, report issues, suggest improvements, and submit pull
requests. By working together, we can ensure that simplyblock’s documentation remains accurate, up-to-date, and
beneficial for all users.