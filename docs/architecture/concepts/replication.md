---
title: "Replication"
weight: 30800
---

Simplyblock supports cross-cluster replication for multi-site disaster recovery and data availability. Replication
ensures that data stored in one simplyblock cluster is continuously or periodically copied to a remote cluster, enabling
recovery from site-level failures with controlled failover and failback workflows.

## Asynchronous Replication

Asynchronous replication periodically transfers snapshots from a source cluster to a target cluster. This mode
prioritizes efficiency and minimal performance impact on the source cluster, at the cost of a small recovery point
gap (the time since the last replicated snapshot).

Key characteristics:

- **Snapshot-Based:** Replication transfers volume snapshots at configurable intervals (minimum 60 seconds).
- **Incremental:** Only data changed since the last replicated snapshot is transferred.
- **Pool or Volume Scope:** Replication can be configured for an entire storage pool or individual volumes (PVCs in
  Kubernetes).
- **Backlog Tracking:** The system tracks replication backlog -- the number of snapshots and amount of data waiting
  to be transferred -- for monitoring and alerting.

Asynchronous replication is suitable for disaster recovery scenarios where a small recovery point objective (RPO) of
minutes is acceptable.

## Synchronous Replication

Synchronous replication mirrors write operations to the target cluster in real time, ensuring that the target is always
an exact copy of the source. This mode provides a zero-RPO guarantee but incurs higher latency and network overhead.

Key characteristics:

- **Real-Time Mirroring:** Every write to the source is confirmed only after it has been written to the target.
- **Zero RPO:** No data is lost in a failover scenario.
- **Higher Latency:** Write latency increases due to the round-trip to the remote cluster.

Synchronous replication is suitable for critical workloads where no data loss is acceptable, such as financial
transactions or compliance-sensitive applications.

## Failover

Failover is the process of switching primary access from the source cluster to the target cluster when the source
becomes unavailable. During failover:

1. The target cluster's replicated volumes are promoted from secondary to primary.
2. Applications are redirected to the target cluster (via Kubernetes CSI driver or manual reconnection).
3. The target cluster begins serving I/O for the affected volumes.

Failover can be triggered manually through the Kubernetes CRD or CLI when a disaster is detected.

## Failback

Failback is the process of returning primary access to the original source cluster after it has been restored. This
involves synchronizing any changes made on the target cluster back to the source:

1. **Delta Synchronization:** The system identifies changes made on the target since failover and transfers them to the
   source.
2. **Iterative Snapshots:** Multiple rounds of snapshot-based synchronization progressively reduce the delta.
3. **Final Sync:** A brief freeze on the target volume ensures the last remaining changes are captured and transferred.
4. **Promotion:** The source cluster's volumes are promoted back to primary, and applications are redirected.

This process minimizes downtime during failback by reducing the final synchronization window to only the most recent
changes.

## Kubernetes Integration

In Kubernetes environments, replication is managed through Custom Resource Definitions (CRDs):

- **`Replication`:** Defines an asynchronous replication relationship between two clusters, including source and target
  cluster UUIDs, replication scope (pool or PVC), and frequency.
- **`SyncReplication`:** Defines a synchronous replication relationship with real-time mirroring.

Failover and failback operations are triggered by updating the CRD's action field. The CSI driver handles the
underlying volume promotion, path updates, and application reconnection.

For operational procedures including setting up replication, performing failover, and executing failback, see
[Replication Operations](../../maintenance-operations/replication.md).
