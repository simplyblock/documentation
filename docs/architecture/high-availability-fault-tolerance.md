---
title: "High Availability and Fault Tolerance"
description: "How simplyblock keeps volumes available through device, node, rack, and site failures: erasure coding, failover paths, the write journal, and replication."
weight: 20200
---

Simplyblock protects data and keeps volumes available at every level, from a single device up to a whole site. No
component is a single point of failure: data, data paths, the storage nodes, and the control plane are all
redundant, and failures are handled automatically.

## Protection at a Glance

| Failure                             | Protection                                                                                     | Section                                                         |
|-------------------------------------|------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| Device                              | Erasure coding, automatic detection of failing devices, and rebuild onto the remaining devices | [Device Failures](#device-failures)                             |
| Storage node                        | Erasure coding across nodes, and failover to a secondary (and tertiary) path                   | [Node Failures](#node-failures)                                 |
| Rack, cabinet, or availability zone | Failure domains, which spread data, journal copies, and failover paths across the domains      | [Failure Domains](#failure-domains)                             |
| Control plane                       | Replicated management services and database. The control plane is not in the I/O path          | [Control Plane](#control-plane)                                 |
| Storage cluster or site             | Asynchronous replication to another cluster, and backups to S3                                 | [Protection Beyond One Cluster](#protection-beyond-one-cluster) |

## Erasure Coding

Every stripe of data is split into data chunks and protected by parity chunks, written as `data+parity`, for
example, `2+1` or `4+2`. Each chunk of a stripe is stored on a different storage node, so the parity count is the
number of nodes (or devices) that can fail at the same time without data loss:

- **One parity chunk** (`1+1`, `2+1`, `4+1`) tolerates one failure.
- **Two parity chunks** (`1+2`, `2+2`, `4+2`) tolerate two failures.

Erasure coding needs far less extra capacity than keeping full copies. For example, `4+2` tolerates two failures
with 50% overhead, while three full copies would need 200%. See [Erasure Coding](concepts/erasure-coding.md) for the
supported schemes.

## Device Failures

The control plane watches every device and reacts before a failing device slows down or endangers the cluster:

- **Detection:** A device that returns I/O errors to a quorum of the other nodes is excluded cluster-wide, even if
  its own controller still reports it healthy. Devices are also checked through their SMART data, and devices whose
  latency falls behind the rest of the cluster are flagged as slow (see
  [Device Health](../kubernetes/operations/monitoring/device-health.md)).
- **Continued service:** Reads of the missing data are reconstructed from the remaining chunks, so volumes keep
  serving I/O.
- **Rebuild:** When a device is failed, its data is rebuilt from parity onto the remaining devices of the cluster
  (failure migration), which restores full redundancy without a replacement device (see
  [Automatic Rebalancing](concepts/automatic-rebalancing.md)). A device that was only briefly unavailable is
  re-admitted automatically and catches up.

## Node Failures

Each logical volume is reachable over several NVMe-oF paths, one per storage node that serves it:

- **Primary:** Serves the I/O of the volume. Its path is the optimized one.
- **Secondary:** Holds a ready copy of the volume's metadata. Its path is non-optimized and takes over when the
  primary fails.
- **Tertiary:** A second standby with two parity chunks, so that the volume survives two node failures.

The host's NVMe multipathing uses the optimized path and switches to a standby path within seconds when the primary
fails, without any intervention (NVMe asymmetric namespace access, ANA). Because erasure coding places the data
chunks on other nodes, the new primary reads and writes the same data. When the failed node returns, it catches up
and takes its role back.

Writes are recorded in a distributed, high-availability write journal with copies on several nodes before they are
acknowledged, so a failover continues from a consistent state.

Storage nodes can also be connected through several independent storage networks, each in its own VLAN. Every path
is then available on every network, which multiplies the paths (for example, four connections with one failover
path and two networks). This is an alternative to link aggregation (LACP, MLAG).

### Small Clusters

A regular cluster needs at least three storage nodes. Smaller clusters, for example, at edge locations, are
supported with their own trade-offs (see [Edge Clusters](deployment-topologies/edge-clusters.md)):

- **One node:** Protects against device failures through erasure coding across the devices of the node, but not
  against the loss of the node itself.
- **Two nodes:** Each node takes over the volumes of the other. An arbiter decides which node keeps serving when the
  two lose contact, and the hosts of the other node are fenced, so a volume never has two writers.

## Failure Domains

Storage nodes can be grouped into [failure domains](concepts/failure-domains.md), such as racks, cabinets, or
availability zones. Simplyblock then spreads data chunks, journal copies, and failover paths across the domains, so
the cluster keeps serving I/O through the loss of a whole domain. With two parity chunks and enough domains, it also
survives one further node or device failure in another domain.

For example, a cluster spread across six racks with `4+2` survives the loss of one entire rack together with a node
or drive failure in another rack, at a capacity overhead of 50%.

## Control Plane

The control plane runs as replicated pods: the management API with two replicas by default, and a FoundationDB
database with three or five coordinators. It survives the loss of a single pod or Kubernetes worker.

The control plane is not in the I/O path. Volumes keep serving I/O while it is unavailable. Only management
operations and automated recovery wait until it is back.

## Protection Beyond One Cluster

Erasure coding and failover protect against failures inside one storage cluster. Against the loss of a whole
cluster or site, simplyblock offers:

- **Asynchronous replication:** Volumes are replicated to a second storage cluster at an interval of one minute or
  more, sending only the changes since the last cycle. Volumes of a consistency group are replicated together. A
  failover promotes the replicated state on the target, and a failback returns to the original cluster after only
  the changes have been sent back. See [Asynchronous Replication](../kubernetes/operations/data-protection/asynchronous-replication.md).
- **Online cluster migration:** Volumes are moved to another cluster while their workloads keep running, with a
  short I/O freeze at the cutover. See
  [Online Cluster Migration](../kubernetes/operations/data-protection/online-cluster-migration.md).
- **Backups to S3:** Volumes are backed up incrementally to an S3-compatible object store, on a schedule with
  retention, and can be restored into the same or another cluster. See
  [Backup and Recovery](../kubernetes/operations/data-protection/backup-recovery.md).
- **Disaster recovery for applications:** Whole applications, their volumes together with their Kubernetes objects,
  are protected across sites with planned and unplanned failover. See
  [Disaster Recovery](../disaster-recovery/index.md).

!!! info "Coming soon"
    Synchronous replication with no data loss (RPO of zero) will be provided by a storage cluster stretched across
    two sites in metro distance. See
    [Deployment Architectures](../deployment-preparation/deployment-architectures.md#metro-stretched-storage-cluster-with-synchronous-replication).
