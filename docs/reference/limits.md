---
title: "Limits"
description: "Hard object limits and vCPU-dependent resource limits of simplyblock storage nodes and clusters: subsystems, namespaces, objects per node, and sizing rules."
weight: 20140
---

Simplyblock enforces a set of limits per storage node and per cluster. Some are hard limits built into the
control plane; others depend on the node's vCPU count and memory configuration.

## Hard Per-Node Object Limits

| Limit | Value | What it counts |
|-------|------:|----------------|
| Objects per node | 6000 | Logical volumes, clones, and snapshots owned by the node (its logical volume store) |
| NVMe-oF subsystems per node | 75 | Subsystems for which the node is the primary; namespaced volumes sharing one subsystem count as one |
| Namespaces per subsystem | 50 | Volumes (namespaces) sharing one NVMe-oF subsystem |

These limits are enforced on every create path (volume create, snapshot create, clone). When a limit is reached,
the operation fails with an explanatory error, for example:

```plain title="Limit errors"
Object limit reached on lvstore of node <NODE_ID>: 6000 objects (lvols/clones: 4100, snapshots: 1900); the hard limit is 6000 per lvstore
Too many subsystems on node: <NODE_ID>, max subsystems reached: 75
max_namespace_per_subsys=64 exceeds the hard limit of 50 namespaces per subsystem
```

Notes on what counts against the limits:

- Only the **primary** node of a volume is charged. Failover copies on secondary and tertiary nodes do not count
  against those nodes' limits — their resource reservation already provisions for them.
- Deleted objects do not count; objects in creation or deletion still do.
- When volume placement finds no node below its subsystem limit, volume creation fails with
  `No nodes found with enough resources to create the LVol`.

## Configured Subsystem Limit per Node

The 75-subsystem ceiling applies on top of the per-node configured maximum, set at host configuration time:

```bash title="Configure the maximum number of subsystems per node"
{{ cliname }} storage-node configure --max-subsys <N> <FURTHER_OPTIONS>
```

The effective subsystem limit of a node is the **smaller** of `--max-subsys` and 75. The configured value also
drives the node's memory reservation (huge pages), so it should reflect the actually planned number of volumes.
It can be changed later via `{{ cliname }} storage-node restart --max-subsys <N>`.

## Namespaces per Subsystem

By default, simplyblock places each volume in its own NVMe-oF subsystem. Namespaced volumes share a subsystem;
the default maximum is **32 namespaces per subsystem**, configurable per volume at creation time up to the hard
ceiling of 50:

```bash title="Create a namespaced volume with a custom namespace limit"
{{ cliname }} volume add ... --max-namespace-per-subsys <N>   # N ≤ 50
```

When a shared subsystem is full, the next volume automatically starts a new subsystem (which then counts against
the node's subsystem limit).

## vCPU-Dependent Limits

On top of the hard object limits, several resource limits scale with the vCPU count of the storage node:

| Limit | Rule |
|-------|------|
| CPU cores per storage node | At most 64 cores can be assigned to one storage node (SPDK instance). |
| Distribution services per node | Scales with the assigned cores, capped at 12. |
| NVMe-oF buffer pools | Scale with core count and `--max-subsys`; they determine part of the huge-page demand. |
| Huge-page memory | The minimum huge-page memory grows with the core count and the configured maximum number of subsystems. Nodes refuse to start with insufficient huge pages. |
| Storage nodes per host | 1 or 2 (`--nodes-per-socket`), aligned to NUMA sockets. |

In practice, the **memory** derived from vCPU count and `--max-subsys` is the sizing driver: see
[Hardware Requirements](../deployment-preparation/hardware-requirements.md) for the RAM formula per subsystem.

## Cluster-Level Limits and Gates

| Limit | Default | Description |
|-------|--------:|-------------|
| Fault tolerance (FTT) | 1 | 1 or 2, derived from the parity chunks of the erasure coding scheme. |
| Minimum online devices at activation | — | Data chunks + parity chunks + 1. |
| Minimum online nodes for volume creation | — | At least data chunks + parity chunks online nodes. |
| Journal copies (`--ha-jm-count`) | 3 (FTT 1) / 4 (FTT 2) | Failure-domain clusters require 4 even at FTT 1. |
| Minimum volume size | 100 MiB | Smaller volumes are rejected. |
| Provisioning warning (`--prov-cap-warn`) | 250 % | Warning when total provisioned capacity exceeds this ratio of the cluster capacity. |
| Provisioning limit (`--prov-cap-crit`) | 500 % | Volume creation fails beyond this over-provisioning ratio. |
| Utilization warning / critical (`--cap-warn` / `--cap-crit`) | 89 % / 99 % | Alerts on used physical capacity. |
| Storage pool caps (`--pool-max`, `--lvol-max`) | unlimited | Optional per-pool caps for total provisioned size and per-volume size. |
| NVMe/TCP qpairs per volume (`--qpair-count`) | 32 | Cluster-internal queue pair count per volume connection. |
| Client qpairs (`--client-qpair-count`) | 3 | Queue pairs per client connection. |

There is no built-in limit on the number of storage nodes per cluster, clusters per control plane, or storage
pools per cluster.

!!! note
    The hard per-node object limits protect the storage node from memory and metadata overload. They are not
    configurable at runtime. If a workload legitimately needs more objects, distribute it across more storage
    nodes or clusters.
