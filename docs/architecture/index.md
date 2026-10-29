---
title: Architecture
description: "The architecture of simplyblock: its components, performance and QoS, high availability, deployment topologies, and the core concepts of the storage platform."
weight: 10080
---

Simplyblock is a cloud-native, software-defined block storage platform built for high performance, scalability, and
resilience. It serves logical volumes over NVMe/TCP and NVMe/RoCE and is deployed and operated through Kubernetes.

This section explains how simplyblock works internally. Understanding the architecture helps with planning a
deployment, sizing a cluster, and choosing between the available protection and placement options.

| Page                                                                          | Content                                                                                  |
|-------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| [What is Simplyblock?](what-is-simplyblock.md)                                | An overview of the platform and what sets it apart.                                      |
| [Simplyblock Architecture](simplyblock-architecture.md)                       | The operator, the control plane, the CSI driver, and the storage plane.                  |
| [Performance and QoS](storage-performance-and-qos.md)                         | How latency stays low and predictable, data locality, caps, and service classes.         |
| [High Availability and Fault Tolerance](high-availability-fault-tolerance.md) | How volumes stay available through device, node, rack, and site failures.                |
| [Deployment Topologies](deployment-topologies/index.md)                       | Where the control plane and the storage nodes run: hyper-converged, disaggregated, edge. |
| [Concepts](concepts/index.md)                                                 | Logical volumes, snapshots, erasure coding, failure domains, migration, and more.        |
