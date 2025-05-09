---
title: "High Availability and Fault Tolerance"
weight: 20200
---

Simplyblock is designed to provide enterprise-grade high availability (HA) and fault tolerance for enterprise and
cloud-native storage environments. Through a combination of distributed architecture and advanced data protection
mechanisms, simplyblock ensures continuous data access, resilience against failures, and minimal service disruption.
Fault tolerance is embedded at multiple levels of the system, from data redundancy to control plane and storage path
resilience.

## Fault Tolerance and High Availability Mechanisms

Simplyblock’s architecture provides robust fault tolerance and high availability by combining distributed erasure
coding, multipath access with failover, and redundant management and storage planes. These capabilities ensure that
Simplyblock storage clusters deliver the reliability and resiliency required for critical, high-demand workloads in
modern distributed environments.

### 1. Distributed Erasure Coding

Simplyblock protects data using distributed erasure coding, which ensures that data is striped across multiple
storage nodes along with parity fragments. This provides:

- **Redundancy**: Data can be reconstructed even if one or more nodes fail, depending on the configured erasure coding
  scheme (such as _1+1_, _1+2_, _2+1_, or _2+2_).
- **Efficiency**: Storage overhead is minimized compared to full replication while maintaining strong fault tolerance.
- **Automatic Rebuilds**: In the event of node or disk failures, missing data is rebuilt automatically using parity
  information stored across the cluster.

### 2. Multipathing with Primary and Secondary Nodes

Simplyblock supports NVMe-over-Fabrics (NVMe-oF) multipathing to provide path redundancy between clients and
storage:

- **Primary and Secondary Paths**: Each Logical Volume (LV) is accessible through both a primary node and one secondary node.
- **Automatic Failover**: If the primary node becomes unavailable, traffic is automatically redirected to a secondary
  node with minimal disruption.

Multipathing is based on ANA (asynchronous namespace access), an concept defined in the nvme standard, which allows the
definition of optimized and non-optimized paths.

Simplyblock also supports multipathing via the older Linux DM (Device Mapper) MPIO. This can be useful, if the operating system 
does not have nvme multipathing compiled into its kernel, as it is the case with Amazon Linux 2 and Amazon Linux 2023.

### 3. Redundant Control Plane and Storage Plane

To ensure cluster-wide availability, Simplyblock operates with full redundancy in both its control plane and
storage plane:

- **Control Plane (Management Nodes)**:
    - Deployed as a highly available set of management nodes, typically in a quorum-based configuration.
    - Responsible for cluster health, topology management, and coordination.
    - Remains operational even if one or more management nodes fail.

- **Storage Plane (Storage Nodes)**:
    - Storage services are distributed across multiple storage nodes.
    - Data and workloads are automatically rebalanced and protected in case of node or device failures.
    - Failures are handled transparently with automatic recovery processes.

## Benefits of Simplyblock’s High Availability Design

- No single point of failure across the control plane, storage plane, and data paths.
- Seamless fail over and recovery from node, network, or disk failures.
- Efficient use of storage capacity while ensuring redundancy through erasure coding.
- Continuous operation during maintenance and upgrade procedures.

