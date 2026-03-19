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

- **Primary and Secondary Paths**: Each Logical Volume (LV) is accessible through both a primary node and one or
  more secondary nodes.
- **Automatic Failover**: If the primary node becomes unavailable, traffic is automatically redirected to a secondary
  node with minimal disruption.
- **Load Balancing**: Multipathing also distributes I/O across available paths to optimize performance and reliability.

#### Dual Fault Tolerance (FT=2)

Simplyblock supports configuring clusters with **dual fault tolerance**, which assigns **two secondary nodes** per
logical volume instead of one. This enables the cluster to tolerate the simultaneous failure of up to two storage nodes
without data unavailability.

With FT=2 enabled:

- **Two Secondary Paths**: Each logical volume is registered on two separate secondary nodes in addition to the primary,
  providing three independent access paths.
- **ANA State Tiering**: Simplyblock uses Asymmetric Namespace Access (ANA) to manage path priorities. The primary node
  is set to the **optimized** state, while the two secondary nodes are configured with **non-optimized** states. This
  ensures clients prefer the primary path for I/O while maintaining instant failover to either secondary.
- **Cascading Failover**: If the primary node fails, one of the secondary nodes takes over. If that secondary also
  fails, the remaining secondary continues to serve I/O.
- **Automatic Recovery**: When failed nodes return, they are automatically reintegrated and their ANA state is restored.

Dual fault tolerance is configured at cluster creation time and applies to all logical volumes within the cluster. It
requires a minimum of four storage nodes (one primary and two secondaries per volume, plus capacity for rebalancing).

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

### 4. Live Volume Migration

Simplyblock supports online migration of logical volumes between storage nodes without service interruption. This
enables planned maintenance, hardware replacement, and cluster rebalancing while maintaining continuous data access.

During migration, the volume’s entire snapshot chain and data are transferred to a target node in the background.
Clients continue to access the volume through the existing NVMe-oF paths throughout the process. Once migration
completes, the volume’s primary and secondary paths are updated transparently. For more details, see
[Volume Migration](concepts/volume-migration.md).

### 5. Backup and Recovery to S3

Simplyblock provides snapshot-based backup to Amazon S3 (or S3-compatible storage), enabling off-cluster disaster
recovery. Backups are incremental and chain-aware, meaning only changed data since the last backup is transferred.
Restoring from backup creates a new volume with the full data lineage reconstructed from the S3 backup chain.

For more details, see [Backup and Recovery](concepts/backup-recovery.md).

### 6. Cross-Cluster Replication

Simplyblock supports both asynchronous and synchronous replication between clusters for multi-site disaster recovery.
Asynchronous replication periodically transfers snapshots to a remote cluster, while synchronous replication mirrors
writes in real time. Both modes support controlled failover and failback workflows to switch primary access between
sites.

For more details, see [Replication](concepts/replication.md).

## Benefits of Simplyblock’s High Availability Design

- No single point of failure across the control plane, storage plane, and data paths.
- Seamless failover and recovery from node, network, or disk failures.
- Efficient use of storage capacity while ensuring redundancy through erasure coding.
- Continuous operation during maintenance and upgrade procedures.
- Dual fault tolerance (FT=2) for environments requiring survival of two simultaneous node failures.
- Live volume migration for non-disruptive hardware maintenance and cluster rebalancing.
- Off-cluster backup to S3 for disaster recovery beyond the storage cluster.
- Cross-cluster replication for multi-site availability and disaster recovery.

