---
title: "Replication"
weight: 20200
---

Simplyblock supports cross-cluster replication for multi-site disaster recovery. This section covers the operational
procedures for configuring replication, monitoring status, and performing failover and failback operations.

For the conceptual overview, see [Replication Concepts](../architecture/concepts/replication.md). For the full CRD
field reference, see [Kubernetes CRD Reference](../reference/kubernetes/crds.md#replication).

## Prerequisites

Before configuring replication:

- Two independent simplyblock clusters must be deployed and operational.
- Network connectivity must exist between the clusters' control planes.
- The Simplyblock CSI driver must be installed on the Kubernetes cluster(s) where replication CRDs will be managed.

## Configuring Asynchronous Replication

Asynchronous replication is configured using the `Replication` CRD (`replications.simplyblock.com`, short name: `rpl`).
It periodically transfers snapshots from a source cluster to a target cluster at a configurable interval.

### Creating a Replication Relationship

```yaml title="Replicate all PVCs in a pool"
apiVersion: simplyblock.com/v25.11.1
kind: Rackup
metadata:
  name: dr-replication
  namespace: simplyblock
spec:
  clusterUUID: "<SOURCE_CLUSTER_UUID>"
  targetClusterUUID: "<TARGET_CLUSTER_UUID>"
  pool: "production"
  interval: "300"
```

```yaml title="Replicate a single PVC"
apiVersion: simplyblock.com/v25.11.1
kind: Rackup
metadata:
  name: dr-replication-db
  namespace: simplyblock
spec:
  clusterUUID: "<SOURCE_CLUSTER_UUID>"
  targetClusterUUID: "<TARGET_CLUSTER_UUID>"
  pvc: "postgres-data"
  interval: "60"
```

Apply the CRD:

```bash title="Apply replication CRD"
kubectl apply -f replication.yaml
```

### Spec Fields

| Field              | Type   | Required | Description                                            |
|--------------------|--------|----------|--------------------------------------------------------|
| `clusterUUID`     | string | Yes      | UUID of the source cluster                              |
| `targetClusterUUID`| string | Yes     | UUID of the target cluster                              |
| `pool`            | string |          | Pool name -- all PVCs in this pool are replicated       |
| `pvc`             | string |          | Single PVC name (alternative to `pool`)                 |
| `interval`        | string |          | Replication frequency in seconds (minimum: 60)          |

!!! note
    Specify either `pool` or `pvc`, not both. Pool-level replication covers all PVCs within the pool.

### Monitoring Replication Status

```bash title="List all replications"
kubectl get rpl -n simplyblock
```

The output shows:

```plain
NAME              CLUSTER        TARGETCLUSTER  POOL         PVC   STATUS    BACKLOG   DATABACKLOG   INTERVAL
dr-replication    abc123...      def456...      production         Running   2         15            300
```

| Status Column | Description                                                        |
|---------------|--------------------------------------------------------------------|
| `Running`     | Replication is active and transferring snapshots on schedule        |
| `Stopped`     | Replication has been paused (via `stop` action)                    |
| `Delayed`     | Replication is running but has fallen behind schedule               |
| `Failed`      | Replication has encountered an error                                |

The **backlog** column shows the number of snapshots waiting for or in active replication. The **dataBacklog** column
shows the amount of data in GB pending transfer. These metrics are key indicators of replication health -- a growing
backlog may indicate network or performance issues.

For detailed status:

```bash title="Get full replication status"
kubectl get rpl dr-replication -n simplyblock -o yaml
```

### Stopping and Resuming Replication

To stop an ongoing replication:

```yaml title="Stop replication"
spec:
  action: "stop"
```

```bash
kubectl apply -f replication.yaml
```

To resume a stopped replication:

```yaml title="Resume replication"
spec:
  action: "resume"
```

!!! warning
    When resuming after a stop, all snapshots accumulated during the pause must be transferred. This initial catch-up
    period may take additional time depending on the amount of changed data.

## Configuring Synchronous Replication

Synchronous replication uses the `SyncReplication` CRD (`synchreplications.simplyblock.com`, short name: `srp`).
Unlike asynchronous replication, writes are mirrored in real time, providing zero-RPO guarantees.

```yaml title="Set up synchronous replication for a pool"
apiVersion: simplyblock.com/v25.11.1
kind: Rackup
metadata:
  name: sync-dr
  namespace: simplyblock
spec:
  clusterUUID: "<CLUSTER_UUID>"
  pool: "critical-data"
```

### Spec Fields

| Field          | Type   | Required | Description                                          |
|----------------|--------|----------|------------------------------------------------------|
| `clusterUUID` | string | Yes      | UUID of the cluster                                   |
| `pool`        | string |          | Pool name -- all PVCs in this pool are replicated     |
| `pvc`         | string |          | Single PVC name (alternative to `pool`)               |

!!! info
    Synchronous replication does not have an `interval` field (writes are mirrored in real time) or a
    `targetClusterUUID` field (the target is configured at the cluster level).

### Monitoring Synchronous Replication

```bash title="List synchronous replications"
kubectl get srp -n simplyblock
```

```plain
NAME      CLUSTER     POOL            PVC   STATUS    BACKLOG   DATABACKLOG
sync-dr   abc123...   critical-data         Running   0         0
```

For synchronous replication, the **backlog** field represents the duration of any replication interruption in seconds
(not snapshot count as with async replication). A non-zero backlog indicates the replication was interrupted and data
may need to catch up.

## Failover

Failover switches primary access from the source cluster to the target cluster. Use this when the source cluster is
unavailable or you need to perform planned maintenance.

Both `Replication` and `SyncReplication` CRDs support the `fail-over` action.

```yaml title="Initiate failover"
spec:
  action: "fail-over"
```

```bash title="Apply failover"
kubectl apply -f replication.yaml
```

During failover:

1. **Target PVCs are promoted** from secondary to primary status.
2. **Source PVCs are disconnected** from applications (if the source is still reachable).
3. **Re-provisioning** occurs on the target site -- the same PVCs are mounted on target nodes.
4. **Applications resume** using the CSI driver, which directs I/O to the target cluster.

!!! warning
    After failover with asynchronous replication, any data written to the source cluster since the last successful
    replication cycle will not be available on the target. The data gap equals the replication interval plus any
    accumulated backlog. Synchronous replication has zero data loss.

## Failback

Failback returns primary access to the original source cluster after it has been restored. Both `Replication` and
`SyncReplication` CRDs support the `fail-back` action.

```yaml title="Initiate failback"
spec:
  action: "fail-back"
```

```bash title="Apply failback"
kubectl apply -f replication.yaml
```

The failback process:

1. **Delta Synchronization:** The delta between the most recent snapshot on the primary and the current state on
   the secondary is identified and transferred back to the primary.
2. **Iterative Snapshots:** Multiple rounds of snapshot-based synchronization progressively shrink the remaining delta.
   Each iteration captures a smaller window of changes.
3. **Final Sync:** The PVC on the target is frozen (I/O paused briefly), a final snapshot is taken, and the last
   remaining data is synchronized to the primary.
4. **Re-provisioning:** The PVC is disconnected from the target and re-provisioned on the primary site (either the
   same host or a different host on the primary cluster).

!!! note
    The iterative approach minimizes the final cutover window. By the time the final sync occurs, only the most recent
    changes need to be transferred, keeping the I/O pause as brief as possible.

## Deleting a Replication Relationship

To remove a replication relationship entirely:

```bash title="Delete the replication CRD"
kubectl delete rpl dr-replication -n simplyblock
```

This stops replication, removes the replication configuration, and removes the target PVCs. S3 data or snapshots
already stored on the target cluster are not automatically deleted.
