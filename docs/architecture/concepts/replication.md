---
title: "Replication"
description: "Asynchronous replication between simplyblock clusters for multi-site disaster recovery, continuously transferring volume snapshots to a target cluster."
weight: 30800
---

Simplyblock supports asynchronous replication between clusters for multi-site disaster recovery and data
availability. Snapshots of the volumes on a source cluster are transferred continuously to a remote target cluster.
After a site-level failure, the volumes are switched over to the target, and the switch is reversed once the source
cluster has been recovered.

## Snapshot Replication

Snapshot replication periodically transfers volume snapshots from a source cluster to a target cluster. Each replication
cycle creates a new snapshot on the source and transfers it to the target, building an incremental snapshot chain on
both sides.

Key characteristics:

- **Snapshot-Based:** Replication transfers volume snapshots at configurable intervals (minimum 60 seconds, default 300
  seconds).
- **Incremental:** Snapshots are chained on the target. Each replicated snapshot references its predecessor, enabling
  efficient copy-on-write storage.
- **Per-Volume Scope:** Replication is enabled per volume. Volumes of the same cluster can replicate to different
  target clusters, and under different schedules.
- **Per-Volume Tracking:** The replication state of every volume is tracked separately, including the timestamp of its
  last replicated snapshot and the direction of its relationship.
- **Automatic Task Management:** Each replication cycle creates a background task that handles the data transfer
  asynchronously. The next cycle is only triggered once the previous task has completed.

Snapshot replication is suitable for disaster recovery scenarios where a recovery point objective (RPO) of minutes is
acceptable. It can also be used for local and global CDN-like data distribution processes or for the site migration of
clusters.

!!! info
    Basic remote snapshot replication is available on any platform via CLI/API, but full asynchronous replication
    with failover and failback is only available on Kubernetes.

## Replication Relationships

A replication relationship is described by three layers, and each of them is configured separately.

- **The cluster pair** names the source and the target cluster. It provisions the replication target on the backend
  and is reusable, so several schedules can replicate between the same two clusters.
- **The policy** carries the cadence, the snapshot retention, and the mode of a pair. A `failover` policy keeps the
  target a read-only standby for disaster recovery, while a `migration` policy prepares a planned cutover to the
  target cluster.
- **The slot** exists once per replicated volume. It holds the live state of that volume and the direction of its
  relationship, which states whether the local cluster currently serves the volume or holds the replica.

A volume is enrolled by naming a policy, either for a whole storage class or for a single volume. Both clusters have
to be attached to the same control plane, since the relationship is resolved against the clusters it knows.

## Replication Architecture

The replication system involves three components:

1. **Simplyblock Operator** ([Simplyblock Operator](https://github.com/simplyblock/simplyblock-operator){:target="_blank" rel="noopener"}): A Kubernetes
   operator that reconciles the replication resources into control plane calls. It attaches and detaches volumes,
   tracks their state, and carries out the failover and failback operations that are requested of it.

2. **Control Plane** (sbcli): The simplyblock management API handles the actual snapshot creation, data transfer via
   NVMe-oF connections, and snapshot chain management on both source and target clusters.

3. **Data Plane** (SPDK): The storage nodes perform block-level data transfer using `bdev_lvol_transfer` RPC calls
   over NVMe-oF connections between clusters.

## Failover

Failover is never started by the operator on its own. Cluster state alone does not distinguish a lost site from a
transient outage, so the switch is requested explicitly. A request covers a single volume, every volume of one policy,
or every volume replicating to one target cluster.

The request results in a one-time volume switch for each affected volume, which provides access to the full volume on
the target cluster via new NVMe-oF paths. The target volumes become primary and begin serving I/O. The RPO is based on
the latest completed snapshot replication.

!!! warning
    After failover, any data written to the source cluster since the last successful snapshot replication will not be
    available on the target. The data gap equals the replication interval plus any time the replication was behind
    schedule.

## Failback

In case the source cluster is entirely lost, it is possible to replicate all data back to a fresh cluster at the origin or
any other site by setting up the replication path toward this new cluster. This is not a true "failback" but handled
as a new replication.

Failback refers to the option to replicate the delta accumulated in the target cluster back to the source in case the
source cluster can be recovered at origin (e.g., after temporary outage or maintenance action). Like a failover, it is
requested explicitly, and the volumes it covers are selected by the scope of the request.

Failback runs in two phases per volume:

1. **Reverse replication:** A snapshot is taken on the target and replicated back to the source, transferring the bulk
   of the changes that accumulated while the target was serving I/O.
2. **Commit:** The volume is frozen, the remaining delta is transferred, and the volume is handed back to the source
   cluster, which resumes serving it as primary.

!!! note
    The two phases minimize the I/O freeze window. The first phase transfers the bulk of the changes while the target
    is still active. The second phase only needs to transfer the small delta accumulated during the first transfer.

## Kubernetes Integration

On Kubernetes, every layer of a replication relationship is a custom resource, and a failover or a failback is
requested by creating a one-shot operation resource. For those resources, their fields, and the annotation that
enrolls a volume, see
[Asynchronous Replication](../../kubernetes/operations/data-protection/asynchronous-replication.md).
