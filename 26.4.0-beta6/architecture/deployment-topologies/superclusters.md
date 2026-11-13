---
title: "Superclusters"
description: "Superclusters combine several simplyblock storage clusters into one cluster for Kubernetes, with volumes placed per volume into placement groups."
source: "https://docs.simplyblock.io/latest/architecture/deployment-topologies/superclusters/"
---

# Superclusters

A supercluster combines several simplyblock storage clusters into one cluster as Kubernetes sees it. The clusters it
combines are its [placement groups](../concepts/placement-groups.md). Each placement group is a complete storage cluster
with its own storage nodes, erasure coding scheme, and failure domains. The supercluster adds no data path of its own.
It adds one name that storage pools, StorageClasses, and backup policies refer to, one status rolled up from the
placement groups, and a placement decision that picks the placement group of every new volume.

A supercluster is orthogonal to the storage placement. Its placement groups run
[hyper-converged](hci.md), [disaggregated](disaggregated.md), or as a mix of both, exactly as standalone clusters do.

## Structure

| Component       | Kubernetes resource                                       | Role                                                                                       |
|-----------------|-----------------------------------------------------------|--------------------------------------------------------------------------------------------|
| Supercluster    | `StorageCluster` with `spec.supercluster`                 | The cluster that pools, StorageClasses, and backup policies name. It has no storage nodes. |
| Placement group | `StorageCluster` with `spec.superclusterRef`              | A complete storage cluster that holds the volumes placed in it.                            |
| Storage pool    | `StoragePool` whose `clusterRef` names the supercluster   | One pool, created under the same name in every placement group.                            |
| StorageClass    | `cluster_id` set to the `status.uuid` of the supercluster | Provisions volumes into whichever placement group the placement chooses.                   |

All placement groups of a supercluster are managed by one control plane and live in the same Kubernetes cluster and
namespace as the supercluster. The control plane itself knows no supercluster: it sees the placement groups as
independent clusters. The aggregation is performed by the Simplyblock Operator and the CSI driver.

A volume lives in one placement group for its whole life, unless it is explicitly
[relocated](../concepts/placement-groups.md#moving-a-volume-between-placement-groups). Its volume handle names the
placement group, so every operation after the creation reaches the placement group directly. A placement group keeps
serving its volumes even while the supercluster object is unavailable.

## When to Choose a Supercluster

A supercluster is the deployment model for a fleet that one storage cluster cannot hold:

- **More than 32 storage nodes:** A storage cluster holds at most 32 storage nodes. A larger fleet is split into
  placement groups of near-equal size.
- **Mixed hardware:** Workers whose device class (NVMe devices or Linux block devices), network interfaces, or sizing
  differ cannot share one cluster. Each kind of worker becomes a placement group of its own, with its own erasure
  coding scheme.
- **Several regions:** A Kubernetes cluster stretched over regions gets one placement group per region or more. New
  volumes are placed in the region of their consumer.

A fleet that fits into one storage cluster does not need a supercluster. A `ClusterDeploymentConfig` with a single node
set creates a standalone cluster, as before.

## Sizing and Topology

When a supercluster is drafted by a discovery run, the workers are split into placement groups automatically. Workers
are first separated by what a placement group must share: the region, the network interfaces, and the device class.
Each partition is then split into the smallest number of placement groups that keeps every placement group within 32
storage nodes, and the workers are dealt evenly across them.

| Workers | Storage nodes per worker | Placement groups | Workers per placement group |
|---------|--------------------------|------------------|-----------------------------|
| 20      | 1                        | 1                | 20                          |
| 32      | 1                        | 1                | 32                          |
| 33      | 1                        | 2                | 17, 16                      |
| 40      | 1                        | 2                | 20, 20                      |
| 40      | 2                        | 3                | 14, 13, 13                  |
| 65      | 1                        | 3                | 22, 22, 21                  |

Placement groups of equal size fill at the same rate, take the same share of new volumes, and cost the supercluster
the same share of its capacity when one of them fails.

Three labels of the Kubernetes nodes shape the split:

| Label                                    | Effect                                                                                      |
|------------------------------------------|---------------------------------------------------------------------------------------------|
| `topology.kubernetes.io/region`          | Bounds a placement group. A placement group never spans two regions.                        |
| `topology.kubernetes.io/zone`            | Becomes the failure domain. Every zone is dealt across every placement group of its region. |
| `storage.simplyblock.io/placement-group` | Assigns workers to placement groups by hand. Workers with one value form one group.         |

Dealing the zones across the placement groups forms a grid of failure domains and placement groups, which is
described in [Placement Groups and Failure Domains](../concepts/placement-groups.md#placement-groups-and-failure-domains).
A failure domain label other than the zone, for example, a rack label, can be named for the discovery run.

## Feature Behavior

Every feature that acts on an existing volume runs in the volume's placement group unchanged. The features that act on
the supercluster as a whole are extended to span the placement groups:

| Feature                                | Behavior in a supercluster                                                                           |
|----------------------------------------|------------------------------------------------------------------------------------------------------|
| Volume creation                        | Placed into one placement group by the placement strategy.                                           |
| Expansion, snapshots                   | Run in the volume's placement group.                                                                 |
| Clones and restores from snapshots     | Land in the placement group of the source.                                                           |
| Consistency groups, group snapshots    | All volumes of a group share one placement group.                                                    |
| Storage pools                          | Created in every placement group. A capacity limit is divided among the placement groups.            |
| Backup policies                        | Fanned out to every placement group. A restore through the supercluster is placed like a new volume. |
| Rebalancing, node migration            | Run within each placement group. Nothing is rebalanced between placement groups.                     |
| Capacity thresholds                    | Apply to the combined capacity of the supercluster. Each placement group keeps its own thresholds.   |
| Asynchronous replication               | Not available for a supercluster. Placement groups are named directly.                               |
| Cluster operations (restart, shutdown) | Not available for a supercluster. They run per placement group.                                      |

## Considerations

- **No shared fault tolerance:** The fault tolerance of a volume is that of its placement group. The supercluster
  reports the lowest fault tolerance among its placement groups in `status.maxFaultTolerance`.
- **No automatic balancing between placement groups:** The placement strategy balances new volumes only. Existing
  volumes move between placement groups when they are relocated.
- **One worker per placement group:** A worker runs storage nodes of one placement group only. Sharing a worker
  between placement groups is not supported.
- **No nesting:** A supercluster cannot be a placement group of another supercluster.
- **Membership is fixed:** A cluster becomes a supercluster or a placement group when it is created. An existing
  standalone cluster cannot join a supercluster.

How a supercluster is deployed and grown is described in
[Managing Superclusters](../../kubernetes/operations/scaling/superclusters.md).
