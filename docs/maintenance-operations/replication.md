---
title: "Replication"
weight: 20200
---

Simplyblock supports snapshot-based replication between clusters for multi-site disaster recovery. This section covers
the operational procedures for configuring replication, monitoring status, and performing failover and failback.

For the conceptual overview, see [Replication Concepts](../architecture/concepts/replication.md). For the full CRD
specification, see [Kubernetes CRD Reference](../reference/kubernetes/crds.md#simplyblocksnapshotreplication).

## Prerequisites

Before configuring replication:

- Two independent simplyblock clusters must be deployed and operational.
- Network connectivity must exist between the clusters' control planes and storage nodes.
- The simplyblock operator ([simplyblock-manager](https://github.com/simplyblock/simplyblock-manager)) must be
  deployed in the Kubernetes cluster.

## Setting Up Replication

### Using the Kubernetes Operator

Create a `SimplyBlockSnapshotReplication` CRD:

```yaml title="snapshot-replication.yaml"
apiVersion: simplyblock.simplyblock.io/v1alpha1
kind: SimplyBlockSnapshotReplication
metadata:
  name: dr-replication
  namespace: simplyblock
spec:
  sourceCluster: prod-cluster
  targetCluster: dr-cluster
  targetPool: dr-pool
  interval: 300
  timeout: 600
```

```bash title="Apply the replication CRD"
kubectl apply -f snapshot-replication.yaml
```

The operator will:

1. Resolve the source and target cluster UUIDs and authenticate with both.
2. Configure the source cluster's replication target via the management API.
3. Begin periodic snapshot replication for all volumes with replication enabled.

### Using the CLI

Replication can also be configured via the CLI:

```bash title="Configure replication between clusters"
{{ cliname }} cluster add-replication <SOURCE_CLUSTER_ID> <TARGET_CLUSTER_ID> [--timeout <SECONDS>] [--target-pool <POOL_ID>]
```

```bash title="Enable replication on a volume"
{{ cliname }} volume replication-start <VOLUME_ID>
```

```bash title="Create a volume with replication enabled"
{{ cliname }} volume add <POOL_ID> <NAME> <SIZE> --replicate
```

## Managing Replication

### Monitoring Status

Using kubectl:

```bash title="Check replication status"
kubectl get simplyblocksnapshotreplications -n simplyblock -o yaml
```

The status section shows per-volume replication details:

- **phase:** `Pending`, `Running`, `Completed`, `Failed`, or `Paused`
- **lastSnapshotID:** UUID of the last successfully replicated snapshot
- **lastReplicationTime:** Timestamp of the last successful replication
- **replicatedCount:** Total number of snapshots replicated
- **errors:** Any error messages with timestamps

Using the CLI:

```bash title="Check replication task status"
{{ cliname }} volume replication-status <CLUSTER_ID>
```

```bash title="List replication tasks for a volume"
{{ cliname }} snapshot replication-status <CLUSTER_ID>
```

### Manually Triggering Replication

To trigger an immediate replication cycle (instead of waiting for the interval):

```bash title="Trigger replication now"
{{ cliname }} volume replication-trigger <VOLUME_ID>
```

### Stopping Replication

```bash title="Stop replication for a volume"
{{ cliname }} volume replication-stop <VOLUME_ID>
```

This sets `do_replicate=false` on the volume. Existing replicated snapshots on the target are retained.

## Failover

Failover is **automatic**. The operator continuously monitors the source cluster and detects failover conditions:

- Source cluster status is `suspended`, **and**
- All source storage nodes are `unreachable`.

When both conditions are met, the operator triggers full volume replication to the target cluster. Target volumes
become primary and serve I/O. No manual intervention is required.

!!! warning
    After failover, data written since the last successful replication cycle is lost. The data gap equals the
    replication interval plus any accumulated delay. For a 300-second interval, expect up to 5 minutes of data loss
    in the worst case.

## Failback

After the source cluster is restored, failback returns primary access to the source. Failback is **manual** -- you
must explicitly trigger it.

### Verify Source Recovery

Before triggering failback, ensure the source cluster is active:

```bash title="Check source cluster status"
{{ cliname }} cluster list
```

The source cluster must show `active` status.

### Trigger Failback

Update the replication CRD with the failback action:

```yaml title="Trigger failback"
apiVersion: simplyblock.simplyblock.io/v1alpha1
kind: SimplyBlockSnapshotReplication
metadata:
  name: dr-replication
  namespace: simplyblock
spec:
  sourceCluster: prod-cluster
  targetCluster: dr-cluster
  targetPool: dr-pool
  action: failback
```

```bash title="Apply failback"
kubectl apply -f snapshot-replication.yaml
```

### Selective Failback

To fail back only specific volumes, use include/exclude filters:

```yaml title="Fail back specific volumes"
spec:
  action: failback
  includeVolumeIDs:
    - "volume-uuid-1"
    - "volume-uuid-2"
```

```yaml title="Fail back all except specific volumes"
spec:
  action: failback
  excludeVolumeIDs:
    - "volume-uuid-to-skip"
```

### Failback Process

For each volume, the operator performs the following steps:

1. Triggers snapshot replication on the target cluster (target-to-source direction).
2. Waits for the replication task to complete (timeout: 10 minutes).
3. Suspends the target volume to freeze I/O.
4. Triggers a second replication to capture the final delta.
5. Waits for completion.
6. Deletes the target volume.
7. Notifies the source cluster to resume.

!!! note
    The two-phase approach minimizes downtime. The first replication runs while the target is still serving I/O. Only
    the brief final sync requires a freeze.

## Deleting a Replication Relationship

To remove the replication configuration:

```bash title="Delete the replication CRD"
kubectl delete simplyblocksnapshotreplication dr-replication -n simplyblock
```

The operator's finalizer ensures clean removal of the backend configuration. Replicated snapshots already on the
target cluster are not automatically deleted.
