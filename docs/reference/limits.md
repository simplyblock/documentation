---
title: "Limits"
description: "Hard object limits and vCPU-dependent resource limits of simplyblock storage nodes and clusters: subsystems, namespaces, objects per node, and sizing rules."
weight: 20140
---

Simplyblock enforces a set of limits per storage node and per cluster. Some are hard limits built into the
control plane. Others depend on the node's vCPU count and memory configuration.

## Hard Per-Node Object Limits

| Limit                       | Value | What it counts                                                                                      |
|-----------------------------|------:|-----------------------------------------------------------------------------------------------------|
| Objects per node            | 6000  | Logical volumes, clones, and snapshots owned by the node (its logical volume store)                 |
| NVMe-oF subsystems per node | 75    | Subsystems for which the node is the primary. Namespaced volumes sharing one subsystem count as one |
| Namespaces per subsystem    | 50    | Volumes (namespaces) sharing one NVMe-oF subsystem                                                  |

These limits are enforced on every create path (volume create, snapshot create, clone). When a limit is reached,
the operation fails with an explanatory error, for example:

```plain title="Limit errors"
Object limit reached on lvstore of node <NODE_ID>: 6000 objects (lvols/clones: 4100, snapshots: 1900); the hard limit is 6000 per lvstore
Too many subsystems on node: <NODE_ID>, max subsystems reached: 75
max_namespace_per_subsys=64 exceeds the hard limit of 50 namespaces per subsystem
```

Notes on what counts against the limits:

- Only the **primary** node of a volume is charged. Failover copies on secondary and tertiary nodes do not count
  against those nodes' limits, because their resource reservation already provisions for them.
- Deleted objects do not count. Objects in creation or deletion still do.
- When volume placement finds no node below its subsystem limit, volume creation fails with
  `No nodes found with enough resources to create the LVol`.

## Hard Per-Object Limits

Independent of the per-node limits, single objects are bounded in size and in how many dependants they may have:

| Limit                | Value  | Applies to                                            |
|----------------------|-------:|-------------------------------------------------------|
| Volume size          | 70 TiB | Volume creation, resize, and clone with `--size`      |
| Snapshots per volume | 100    | Active (non-deleted) snapshots taken from one volume  |
| Clones per snapshot  | 500    | Active (non-deleted) clones created from one snapshot |

A volume and its snapshots form one blob chain, and every snapshot deepens the chain that reads of that volume
and of its clones must walk. The snapshot and clone limits bound that chain.

```plain title="Per-object limit errors"
Volume size 80.0 TiB exceeds the maximum of 70.0 TiB per volume
Snapshot limit reached for volume <VOLUME_ID>: 100 active snapshots; the hard limit is 100 per volume. Delete snapshots before creating more
Clone limit reached for snapshot <SNAPSHOT_ID>: 500 active clones; the hard limit is 500 per snapshot
```

Notes:

- The volume size limit applies to the **provisioned** size. It does not cap `--max-size`, the growth ceiling of a
  thin-provisioned volume, because the command line and the CSI driver pass a large default there when no value is
  given. Growth is bounded where it happens instead, so a resize beyond the limit is rejected.
- Internal snapshots taken by replication and volume migration are exempt from the snapshot limit, so a volume at
  the limit can still be replicated and migrated. They are transient and removed by the operation that created them.
- Every limit that refuses an operation also raises a warning in the cluster event log, so a volume that silently
  fails to appear can be traced. Repeated refusals of the same limit on the same object are collapsed, because a
  retrying client would otherwise fill the log.

## Configured Subsystem Limit per Node

The 75-subsystem ceiling applies on top of the per-node configured maximum, set at host configuration time:

```bash title="Configure the maximum number of subsystems per node"
{{ cliname }} storage-node configure --max-subsys <N> <FURTHER_OPTIONS>
```

The effective subsystem limit of a node is the **smaller** of `--max-subsys` and 75. The configured value also
drives the node's memory reservation (huge pages), so it should reflect the actually planned number of volumes.
It can be changed later via `{{ cliname }} storage-node restart --max-subsys <N>`.

## Namespaces per Subsystem

By default, simplyblock places each volume in its own NVMe-oF subsystem. Namespaced volumes share a subsystem.
The default maximum is **32 namespaces per subsystem**, configurable per volume at creation time up to the hard
ceiling of 50:

```bash title="Create a namespaced volume with a custom namespace limit"
{{ cliname }} volume add ... --max-namespace-per-subsys <N>   # N ≤ 50
```

When a shared subsystem is full, the next volume automatically starts a new subsystem (which then counts against
the node's subsystem limit).

A shared subsystem belongs to exactly one storage pool. A namespaced volume only ever joins a subsystem whose
volumes all belong to its own pool, and a pool fills one of its subsystems completely before a new one is opened.
Volumes of two different pools therefore never share an NVMe-oF subsystem, which keeps a host connection to one
pool from exposing another pool's namespaces.

## vCPU-Dependent Limits

On top of the hard object limits, several resource limits scale with the vCPU count of the storage node:

| Limit                          | Rule                                                                                                                                                        |
|--------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| CPU cores per storage node     | At most 64 cores can be assigned to one storage node (SPDK instance).                                                                                       |
| Distribution services per node | Scales with the assigned cores, capped at 12.                                                                                                               |
| NVMe-oF buffer pools           | Scale with core count and `--max-subsys`. They determine part of the huge-page demand.                                                                      |
| Huge-page memory               | The minimum huge-page memory grows with the core count and the configured maximum number of subsystems. Nodes refuse to start with insufficient huge pages. |
| Storage nodes per host         | 1 or 2 (`--nodes-per-socket`), aligned to NUMA sockets.                                                                                                     |

In practice, the **memory** derived from vCPU count and `--max-subsys` is the sizing driver: see
[Hardware Requirements](../deployment-preparation/hardware-requirements.md) for the RAM formula per subsystem.

## Cluster-Level Limits and Gates

| Limit                                                        | Default               | Description                                                                         |
|--------------------------------------------------------------|----------------------:|-------------------------------------------------------------------------------------|
| Fault tolerance (FTT)                                        | 1                     | 1 or 2, derived from the parity chunks of the erasure coding scheme.                |
| Minimum online devices at activation                         | —                     | Data chunks + parity chunks + 1.                                                    |
| Minimum online nodes for volume creation                     | —                     | At least data chunks + parity chunks online nodes.                                  |
| Journal copies (`--ha-jm-count`)                             | 3 (FTT 1) / 4 (FTT 2) | Failure-domain clusters require 4 even at FTT 1.                                    |
| Minimum volume size                                          | 100 MiB               | Smaller volumes are rejected.                                                       |
| Provisioning warning (`--prov-cap-warn`)                     | 250 %                 | Warning when total provisioned capacity exceeds this ratio of the cluster capacity. |
| Provisioning limit (`--prov-cap-crit`)                       | 500 %                 | Volume creation fails beyond this over-provisioning ratio.                          |
| Utilization warning / critical (`--cap-warn` / `--cap-crit`) | 89 % / 99 %           | Alerts on used physical capacity.                                                   |
| Storage pool caps (`--pool-max`, `--lvol-max`)               | unlimited             | Optional per-pool caps for total provisioned size and per-volume size.              |
| NVMe/TCP qpairs per volume (`--qpair-count`)                 | 32                    | Cluster-internal queue pair count per volume connection.                            |
| Client qpairs (`--client-qpair-count`)                       | 3                     | Queue pairs per client connection.                                                  |

There is no built-in limit on the number of storage nodes per cluster, clusters per control plane, or storage
pools per cluster.

!!! note
    The hard per-node object limits protect the storage node from memory and metadata overload. They are not
    configurable at runtime. If a workload legitimately needs more objects, distribute it across more storage
    nodes or clusters.
