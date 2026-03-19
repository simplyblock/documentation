---
title: "Deployment Preparation"
weight: 20000
---

Proper deployment planning is essential for ensuring the performance, scalability, and resilience of a simplyblock
storage cluster.

Before installation, key factors such as node sizing, storage capacity, and fault tolerance mechanisms should be
carefully evaluated to match workload requirements. This section provides guidance on sizing management nodes and
storage nodes, helping administrators allocate adequate CPU, memory, and disk resources for optimal cluster performance.

Additionally, it explores selectable erasure coding schemes, detailing how different configurations impact storage
efficiency, redundancy, and recovery performance. Other critical considerations, such as network infrastructure,
high-availability strategies, and workload-specific optimizations, are also covered to assist in designing a simplyblock
deployment that meets both operational and business needs.

## Fault Tolerance Level Planning

Simplyblock supports two fault tolerance levels:

- **FT=1 (default):** Each volume has one primary and one secondary node. The cluster tolerates the failure of one
  storage node per volume.
- **FT=2 (dual fault tolerance):** Each volume has one primary and two secondary nodes. The cluster tolerates the
  simultaneous failure of up to two storage nodes per volume.

FT=2 requires a minimum of **four storage nodes** to ensure sufficient capacity for primary and secondary placement.
The fault tolerance level is set at cluster creation time. For details, see
[High Availability and Fault Tolerance](../../architecture/high-availability-fault-tolerance.md).

## S3 Backup Configuration

If backup and recovery to S3 is planned, the following must be prepared before cluster deployment:

- **S3 Bucket:** An S3 bucket (or S3-compatible endpoint such as MinIO) for storing backups. Simplyblock can create
  the bucket automatically if the provided credentials have sufficient permissions.
- **Access Credentials:** An AWS IAM access key and secret key with read/write access to the backup bucket.
- **Custom Endpoint (optional):** For S3-compatible storage providers, the endpoint URL must be specified.
- **CPU Allocation:** Backup operations require dedicated CPU cores on each storage node. Plan for additional CPU cores
  when sizing storage nodes if backups will be enabled.

Backup configuration is applied at the cluster level after deployment. See
[Backup and Recovery](../../architecture/concepts/backup-recovery.md) for the concept overview.

## Replication Planning

For multi-site disaster recovery using cross-cluster replication, the following should be planned:

- **Two independent simplyblock clusters:** A source cluster and a target cluster, typically in different availability
  zones or regions.
- **Network connectivity:** The source and target clusters must have network connectivity between their control planes.
- **Replication mode:** Choose between asynchronous replication (periodic snapshot transfer, small RPO) or synchronous
  replication (real-time mirroring, zero RPO but higher latency).
- **Replication scope:** Decide whether to replicate entire storage pools or individual volumes.

Replication is configured after both clusters are deployed. See
[Replication](../../architecture/concepts/replication.md) for the concept overview.
