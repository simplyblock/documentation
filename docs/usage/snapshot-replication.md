---
title: "Snapshot Replication"
description: "Configure snapshot-based asynchronous replication between simplyblock clusters for disaster recovery, using CLI or Kubernetes CRDs."
weight: 30500
---

Simplyblock supports snapshot-based asynchronous replication between clusters for disaster recovery and multi-site
data availability. Replication periodically transfers volume snapshots from a source cluster to a target cluster,
enabling recovery from site-level failures.

For the architectural overview, see [Replication Concepts](../architecture/concepts/replication.md).

## Prerequisites

- Two simplyblock clusters (source and target) with network connectivity between them.
- Both clusters must be activated and have storage nodes online.
- Volumes to be replicated must have snapshot capability enabled.

## Kubernetes Setup

On Kubernetes, snapshot replication is managed through the `SimplyBlockSnapshotReplication` CRD provided by the
[Simplyblock Operator](../reference/operator.md).

### Configuring Replication

Create a `SimplyBlockSnapshotReplication` resource on the cluster running the operator:

```yaml title="Example: Snapshot replication"
apiVersion: simplyblock.simplyblock.io/v1alpha1
kind: SimplyBlockSnapshotReplication
metadata:
  name: dr-replication
  namespace: simplyblock
spec:
  sourceClusterName: production
  targetClusterName: dr-site
  intervalSeconds: 300
```

### Spec Fields

| Field                | Type     | Description                                                                        |
|----------------------|----------|------------------------------------------------------------------------------------|
| `sourceClusterName`  | string   | Name of the source cluster. **Required**.                                          |
| `targetClusterName`  | string   | Name of the target cluster. **Required**.                                          |
| `intervalSeconds`    | int      | Replication interval in seconds. Minimum: `60`. Default: `300`.                    |
| `includeVolumeIDs`   | []string | Only replicate these volume UUIDs (optional, default: all replicated volumes).     |
| `excludeVolumeIDs`   | []string | Exclude these volume UUIDs from replication (optional).                            |
| `action`             | string   | Lifecycle action: `failback` to initiate failback after source recovery.           |

### Monitoring Replication Status

The operator tracks replication progress per volume in the CRD status. Check the status with:

```bash
kubectl get simplyblocksnapshotreplication dr-replication -n simplyblock -o yaml
```

The status includes per-volume information such as the last replicated snapshot, replication count, and timestamps.

## Failover

Failover is triggered **automatically** by the operator when the source cluster becomes unavailable:

- The source cluster status is `suspended`, **or**
- All storage nodes in the source cluster are `unreachable`.

When these conditions are met, the operator switches each replicated volume to the target cluster, which begins
serving I/O. No manual action is required.

!!! warning
    Data written to the source cluster after the last successful snapshot replication is not available on the
    target. The data gap equals the replication interval plus any time the replication was behind schedule.

## Failback

After the source cluster is restored, failback can be initiated to synchronize changes made on the target back to
the source and resume normal operations.

Trigger failback by updating the CRD:

```yaml title="Trigger failback"
spec:
  action: failback
```

The failback process:

1. Creates a snapshot on the target and replicates it back to the source.
2. Waits for the transfer to complete.
3. Suspends I/O on the target to capture the final delta.
4. Transfers the last changes to the source.
5. Removes the failover copy from the target.
6. Resumes serving I/O from the source.

Failback supports filtering with `includeVolumeIDs` and `excludeVolumeIDs` for selective volume failback.

!!! note
    The two-phase replication minimizes the I/O freeze window. The first replication transfers the bulk of changes
    while the target is still active. The second replication only transfers the small delta accumulated during the
    first transfer.

## Enabling Replication on Volumes

To include a volume in replication, enable snapshot capability when creating the volume:

```bash
{{ cliname }} volume add --snapshot <VOLUME_NAME> <SIZE> <POOL_NAME>
```

Volumes without a snapshot capability cannot participate in replication.
