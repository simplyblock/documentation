---
title: "High Availability and Fault Tolerance"
description: "High Availability and Fault Tolerance: Simplyblock is designed to provide enterprise-grade high availability (HA) and fault tolerance for enterprise and."
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
simplyblock storage clusters deliver the reliability and resiliency required for critical, high-demand workloads in
modern distributed environments.

### 1. Distributed Erasure Coding

Simplyblock protects data using distributed erasure coding, which ensures that data is striped across multiple
storage nodes along with parity fragments. This provides:

- **Redundancy**: Data can be reconstructed even if one or more nodes fail, depending on the configured erasure coding
  scheme (such as _1+1_, _1+2_, _2+1_, or _2+2_).
- **Efficiency**: Storage overhead is minimized compared to full replication while maintaining strong fault tolerance.
- **Automatic Rebuilds**: In the event of node or disk failures, missing data is rebuilt automatically using parity
  information stored across the cluster.

!!! important
    Simplyblock provides support for so-called stretch clusters. This deployment topology adds disaster recovery
    across failure domains (such as racks, cabinets, or sites) to improve protection from failed drives and
    single-site high availability. This is achieved with minimum protection overhead.

    For example, if a cluster is span across 6 racks, it is possible to protect from a single entire rack
    outage and a concurrent node outage on another rack or drive failures on any other node with an storage
    overhead of just 50%.

### 2. Multipathing with Primary and Secondary Nodes

Simplyblock supports NVMe-over-Fabrics (NVMe-oF) multipathing to provide path redundancy between clients and
storage:

- **Primary and Secondary Paths**: Each logical volume (LV) is accessible through both a primary node and one or
  more secondary nodes.
- **Automatic Failover**: If the primary node becomes unavailable, traffic is automatically redirected to a secondary
  node with minimal disruption.
- **Load Balancing**: Multipathing also distributes I/O across available paths to optimize performance and reliability.

The number of secondary node paths is automatically configured based on the selected erasure coding scheme.

Any erasure coding scheme with a parity level of _1_ (`1+1`, `2+1`, `4+1`) has a single secondary path, while schemes
with a parity level of _2_ (`1+2`, `2+2`, `4+2`) have two secondary paths.

The number of secondary paths defines how many storage nodes can be lost at the same time without impacting the
availability of the logical volume.

### 3. Redundant Control Plane and Storage Plane

To ensure cluster-wide availability, simplyblock operates with full redundancy in both its control plane and
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
- Seamless failover and recovery from node, network, or disk failures.
- Efficient use of storage capacity while ensuring redundancy through erasure coding.
- Continuous operation during maintenance and upgrade procedures.

### 4. Asynchronous Replication (new)

This new feature allows to protect data stored in a cluster from a site disaster with only 60 seconds of RPO, if 
bandwidth and/or latency between sites do not allow for stretch clusters. 

The feature can be enabled selectively on a per-volume level at volume create time or later on; it requires the
control plane to be distributed across two sites, serving one single-site storage cluster on each site.

On disaster fail-over, workloads have to be restarted to reconnect after as short loss of IO  to the now 
automatically redirected paths; Fail-back considers two scenarios:
- old site cannot be recovered, a fresh storage cluster is redeployed. All data will be replicated back to the
original site into the fresh cluster and ultimately fail-back is possible without io interrupt by rolling over the
NVMe-oF connections.
- old site can be recovered; in this scenario, only the delta between old and new sites will be replicated back
and again, ultimately fail-back is possible without io interrupt by rolling over the
NVMe-oF connections.

The feature also allows monitoring of active and completed replications and generally to control the backlog.

### 5. Backup/Restore (new)

This new feature requires an S3-compatible backup store such as minio or aws S3. It comes with backup policy (retention)
management and auto-backup. It is very storage and time-efficient as delta-snapshots are used to recurringly store only
changed data of volumes. The number and timing of individual generations of the backup can be controlled. 
Older versions can be auto-merged into full backups. Backups can be restored:
- using the latest or older generations of data
- into the same storage cluster or a different storage cluster
- managing encyrpted data via self-contained, encyrpted keys and an external KMS

### 6. Synchronous Replication (outlook)

This planned feature will enable two-site synchronous replication with strong consistency within a single cluster
without using the stretch feature. It comes at a higher data protection overhead, but in return treats two parts of
the cluster (one on each site) with independent erasure coding, increasing the overall degree of data protection.







