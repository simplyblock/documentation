---
title: "Asynchronous Replication"
description: "Asynchronous replication between simplyblock clusters: disaster recovery, cross-cluster volume migration, failover, and failback."
weight: 20045
---

Simplyblock replicates volumes between two storage clusters by taking copy-on-write snapshots at regular intervals
and transferring them to the target cluster. On top of this mechanism, two workflows are available per volume:

- **Disaster recovery** (`failover` mode): the target cluster holds a continuously updated copy. If the source
  cluster is lost, the volume is materialized on the target and clients reconnect there.
- **Cross-cluster volume migration** (`migration` mode): a planned, online move of a volume to another cluster.
  The remaining delta is transferred under a brief I/O freeze, and the client fails over to the target paths
  without a disconnect.

For the architecture background, see [Replication Concepts](../../architecture/concepts/replication.md). For
Kubernetes environments, where replication is managed through the `SnapshotReplication` resource, see
[Asynchronous Replication on Kubernetes](../../kubernetes/operations/asynchronous-replication.md).

## Prerequisites

- **Both clusters are managed by the same control plane.** The first cluster is created with
  `{{ cliname }} cluster create`. The second is attached to the same control plane with `{{ cliname }} cluster add`.
- The storage nodes of the source cluster can reach the storage nodes of the target cluster over the storage
  network: replication transfers data directly between the nodes over NVMe-oF.
- Both clusters are activated, and both have an active storage pool.

!!! note
    For multi-site setups, distribute the management nodes of the control plane across the sites so that the
    control plane survives a site failure.

## Configuring the Replication Target

Replication is configured per source cluster and points at one target cluster and pool:

```bash title="Assign the replication target cluster"
{{ cliname }} cluster add-replication <SOURCE_CLUSTER_ID> <TARGET_CLUSTER_ID> \
  --target-pool <TARGET_POOL> [--timeout <SECONDS>]
```

If `--target-pool` is omitted, the first active pool of the target cluster is used. For bidirectional protection,
run the command once in each direction.

## Enabling Replication on a Volume

```bash title="Start replication for a volume"
{{ cliname }} volume replication-start <VOLUME_ID> \
  [--replication-cluster-id <TARGET_CLUSTER_ID>] \
  [--mode failover|migration] \
  [--interval-min <MINUTES>]
```

- `--mode failover` (default): asynchronous disaster recovery. The target volume is only materialized on
  failover.
- `--mode migration`: planned cutover. The target subsystem is pre-created up front (inaccessible), and the
  volume is cut over on an explicit commit.
- `--interval-min <N>`: take an internal replication snapshot every `N` minutes (the first one immediately).
  `0` disables interval snapshots. Only user-created snapshots then replicate.

Every snapshot of a replicated volume (interval-based or user-created) is queued for transfer to the target
cluster. Snapshots that were taken before replication was enabled are transferred as well. The achievable recovery
point (RPO) is roughly the snapshot interval plus the transfer time.

A volume can also opt into replication at creation time with `{{ cliname }} volume add ... --replicate`, using
the cluster's configured replication target. Mode and interval are then set with a subsequent
`replication-start`.

To take an immediate replication snapshot outside the interval:

```bash title="Trigger an immediate replication snapshot"
{{ cliname }} volume replication-trigger <VOLUME_ID>
```

## Monitoring

```bash title="Replication progress of one volume"
{{ cliname }} volume replication-info <VOLUME_ID>
```

The output shows the last snapshot, the last completed replication and its duration, the number of replicated
snapshots, the **time lag**, and the outstanding backlog (count and bytes of not-yet-replicated snapshots). The
time lag is the age of the newest point-in-time that exists on the target, which is the actual RPO. A volume is
caught up when the outstanding count is zero.

```bash title="All replication tasks of a cluster"
{{ cliname }} volume replication-status <CLUSTER_ID>
```

## Cross-Cluster Volume Migration

A planned, online migration of a volume to another cluster combines `migration` mode with an explicit commit:

```bash title="Step 1: Replicate the volume in migration mode"
{{ cliname }} volume replication-start <VOLUME_ID> \
  --replication-cluster-id <TARGET_CLUSTER_ID> \
  --mode migration --interval-min 1
```

Wait until `{{ cliname }} volume replication-info <VOLUME_ID>` reports an outstanding count of zero, then:

```bash title="Step 2: Commit the cutover"
{{ cliname }} volume replication-commit <VOLUME_ID>
```

The commit takes a final snapshot to minimize the delta, builds the target volume on the last replicated
snapshot (with the **same NQN and namespace ID** as the source), exposes it as inaccessible, and queues the final
cutover task. The cutover freezes source I/O, transfers the residual delta, and flips the ANA states so that the
client fails over to the target paths without a disconnect.

!!! important
    For an interruption-free cutover, the client must already hold the target paths when the ANA states flip.
    Retrieve the connection strings of the target volume right after `replication-commit` and run the
    `nvme connect` commands on the client before the cutover task completes. Because source and target expose the
    same NQN and namespace ID, the new paths join the existing multipath device.

Since continuous replication keeps the backlog small, the final freeze only covers the residual delta, typically
a fraction of a second to a few seconds.

## Failover (Disaster Recovery)

If the source cluster is lost, a replicated volume is materialized on the target cluster from the last
successfully replicated snapshot. This is currently exposed through the management API:

```bash title="Fail a volume over to the target cluster"
curl -X POST -H "Authorization: <CLUSTER_ID> <CLUSTER_SECRET>" \
  https://<CONTROL_PLANE>/api/v2/clusters/<CLUSTER_ID>/storage-pools/<POOL_ID>/volumes/<VOLUME_ID>/replicate_lvol
```

The response contains the volume's NQN, namespace ID, and the connection strings on the target cluster. The NQN
and namespace ID are identical to the source volume, so clients reconnect to the returned addresses and continue
with the same device identity.

!!! warning
    Data written on the source after the last successfully replicated snapshot is not available on the target.
    The data gap is at most the replication interval plus the replication lag. Check
    `volume replication-info` to see the effective lag. Unlike the planned cutover, a failover interrupts I/O:
    workloads must reconnect (and typically restart) against the target paths.

## Failback

After a failover, the volume can be moved back to a source cluster:

```bash title="Configure the failback"
{{ cliname }} volume replication-failback <VOLUME_ID> [--source-cluster-id <CLUSTER_ID>]
```

- **Recovered original source** (omit `--source-cluster-id`): snapshots that already exist on the original source
  are recognized, and only the delta written since the failover is replicated back.
- **Fresh source cluster** (pass a different cluster id): the full volume is replicated to the new cluster.

Failback uses the same mechanism as cross-cluster migration: once the backlog is caught up, complete the failback
with `{{ cliname }} volume replication-commit <VOLUME_ID>`. The same client-connect rule applies for an
interruption-free cutback.

## Stopping Replication and Cleaning Up

```bash title="Stop replication for a volume"
{{ cliname }} volume replication-stop <VOLUME_ID>
```

Stopping cancels the pending replication tasks of the volume and disables further snapshots from replicating. The
already replicated snapshots on the target are kept. They can be removed individually without touching the source
snapshot:

```bash title="Delete only the replicated copy of a snapshot"
{{ cliname }} snapshot delete-replication-only <SNAPSHOT_ID>
```

The replication status of individual snapshots is available with
`{{ cliname }} snapshot replication-status <CLUSTER_ID>` and `{{ cliname }} snapshot list --with-details`.
