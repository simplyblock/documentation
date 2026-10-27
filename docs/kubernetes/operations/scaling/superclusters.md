---
title: "Managing Superclusters"
description: "Create, grow, and operate a simplyblock supercluster on Kubernetes: placement groups, storage pools, placement control, and relocating volumes."
weight: 10330
---

A supercluster scales a simplyblock deployment beyond one storage cluster. It combines several storage clusters, its
[placement groups](../../../architecture/concepts/placement-groups.md), into one `StorageCluster` that storage pools
and StorageClasses name, and every new volume is placed into one of the placement groups. The architecture and the
reasons to choose a supercluster are described in
[Superclusters](../../../architecture/deployment-topologies/superclusters.md).

A supercluster is created and grown through `ClusterDeploymentConfig` documents, like a standalone cluster. A document
with more than one node set creates a supercluster, and every node set becomes one placement group.

## Creating a Supercluster

### With a Discovery Run

A discovery run drafts a supercluster on its own when the workers it finds do not fit into one storage cluster: when
they exceed 32 storage nodes, span several regions, or differ in network interfaces or device class. The draft then
holds several node sets, and its `status.message` names the placement groups an approval creates. Node sets of one
tier are numbered, for example, `discovered-1` and `discovered-2`, and carry the region when the tier spans regions,
for example, `discovered-eu-west-1-1`.

The failure domain of each worker is read from the label `topology.kubernetes.io/zone`. A rack or power feed label is
used instead when the discovery run names it in `spec.discover.failureDomainLabel`:

```yaml title="Example of a discovery run with rack labels as failure domains (discover-racks.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: OperatorOps
metadata:
  name: discover-racks
  namespace: simplyblock
spec:
  action: Discover
  discover:
    configName: production
    failureDomainLabel: example.com/rack
```

To decide by hand which workers form a placement group, the workers are labeled with
`storage.simplyblock.io/placement-group` before the discovery run. Workers carrying one value form one node set named
after the value, and the automatic split is skipped for them.

```bash title="Assigning workers to placement groups"
kubectl label node worker-01 worker-02 worker-03 worker-04 \
    storage.simplyblock.io/placement-group=dense
kubectl label node worker-05 worker-06 worker-07 worker-08 \
    storage.simplyblock.io/placement-group=fast
```

The draft reports incomplete topology as findings rather than guessing:

| Finding                         | Meaning                                                                       |
|---------------------------------|-------------------------------------------------------------------------------|
| `TopologyIncomplete`            | Some workers of a partition carry no failure domain label.                    |
| `PlacementGroupLabelIncomplete` | Some workers carry the placement-group label and others do not.               |
| `PlacementGroupInvalid`         | A placement-group value is not usable as a node set name.                     |
| `FailureDomainLayout`           | The failure domain layout of a placement group cannot be activated as listed. |

### By Hand

A document written by hand lists one node set per placement group. The `spec.cluster` block is the template for every
placement group, and its `name` becomes the name of the supercluster. A node set may override the sizing for its own
placement group in `cluster`, which is how placement groups of different hardware are combined.

```yaml title="Example of a supercluster with two placement groups (production.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ClusterDeploymentConfig
metadata:
  name: production
  namespace: simplyblock
spec:
  approved: false
  cluster:
    name: production
    maxSubsystemCount: 50
    vcpuCount: 8
    stripe:
      dataChunks: 2
      parityChunks: 1
    enableFailureDomains: true
  nodeSets:
    - name: dense
      groups:
        - name: zone-a
          failureDomain: zone-a
          workers: [worker-01, worker-02]
          devices:
            nvme: ["0000:01:00.0", "0000:02:00.0"]
        - name: zone-b
          failureDomain: zone-b
          workers: [worker-03, worker-04]
          devices:
            nvme: ["0000:01:00.0", "0000:02:00.0"]
    - name: fast
      cluster:
        vcpuCount: 16
        stripe:
          dataChunks: 1
          parityChunks: 1
      groups:
        - name: zone-a
          failureDomain: zone-a
          workers: [worker-05, worker-06]
          devices:
            nvme: ["0000:01:00.0"]
        - name: zone-b
          failureDomain: zone-b
          workers: [worker-07, worker-08]
          devices:
            nvme: ["0000:01:00.0"]
```

`cluster` on a node set may carry `vcpuCount`, `maxSubsystemCount`, `minHugePagesSize`, `socketsToUse`,
`nodesPerSocket`, and `stripe`. A field left unset takes the value of the template. Overrides are refused on a document
with a single node set, because its template already describes the one cluster it creates.

Within a node set, every group shares one device class and one set of network interfaces. Two node sets may differ in
both. A worker is listed only once in the whole document.

### Validation

Approval checks every node set as a cluster of its own:

| Finding                      | Refused when                                                                                   |
|------------------------------|------------------------------------------------------------------------------------------------|
| `MemberTooLarge`             | A node set holds more than 32 storage nodes (workers times storage nodes per worker).          |
| `MemberNameInvalid`          | The placement group name, `<cluster>-<nodeset>-<suffix>`, is not a DNS label.                  |
| `MemberSpansRegions`         | The workers of a node set carry different `topology.kubernetes.io/region` labels.              |
| `MemberMissingFailureDomain` | With failure domains enabled, a node set lacks a failure domain another one of its region has. |
| `StripeBelowMinimumNodes`    | A node set has fewer storage nodes than its erasure coding scheme requires.                    |

The 32 storage node limit applies to a standalone cluster as well.

### What Gets Created

An approved document with several node sets creates:

- **The supercluster:** A `StorageCluster` named after `spec.cluster.name`, with `spec.supercluster` set. It has no
  storage nodes of its own.
- **One placement group per node set:** A `StorageCluster` named `<cluster>-<nodeset>-<suffix>`, where the suffix is
  three random lowercase letters, for example, `production-dense-kqv`. It names the supercluster in
  `spec.superclusterRef` and creates its storage nodes like any standalone cluster.
- **The default pool and StorageClass of the supercluster:** The pool `<cluster>-default` and the StorageClass
  `simplyblock-<namespace>-<cluster>`, whose volumes are placed across the placement groups.

The placement groups bring up their storage nodes one placement group at a time, and a placement group is activated as
soon as its own storage nodes are `Online`. `status.clusterRef` of the document names the supercluster, and
`status.members` lists the placement groups.

## Inspecting a Supercluster

The `Role` column distinguishes superclusters, placement groups, and standalone clusters. The wide output adds the
number of members and the fault tolerance.

```bash title="Listing the supercluster and its placement groups"
kubectl -n simplyblock get stc -o wide
```

```plain title="Example output of the supercluster listing"
NAME                    PHASE      ROLE             MEMBERS   STEP   STATUS   EC    FTT   UUID                                   AGE
production              Degraded   Supercluster     2                                1     0d6f1b2e-7c41-4f0e-9a51-2b8c3d4e5f60   3d
production-dense-kqv    Online     PlacementGroup                    active   2x1   1     4f0c9a12-3b5d-4e6f-8a7b-9c0d1e2f3a4b   3d
production-fast-mzt     Degraded   PlacementGroup                    active   1x1   1     9b21e3f4-5a6b-4c7d-8e9f-0a1b2c3d4e5f   3d
```

The phase of the supercluster is rolled up from its placement groups:

| Placement groups                                           | Supercluster phase |
|------------------------------------------------------------|--------------------|
| None yet, or any not yet activated                         | `Provisioning`     |
| Every placement group `Online`                             | `Online`           |
| At least one serving and at least one not `Online`         | `Degraded`         |
| None serving, at least one `Suspended`, none `Unavailable` | `Suspended`        |
| None serving, otherwise                                    | `Unavailable`      |

A placement group is serving while it is `Online`, `Degraded`, `Rebalancing`, or `Shrinking`. A placement group that
is rebalancing therefore makes the supercluster `Degraded`.

`status.members` of the supercluster lists every placement group with its UUID, its phase, its capacity, and
`placementEligible`, which states whether new volumes are placed in it. `status.capacity` sums the total, used, and
provisioned bytes of all placement groups.

```bash title="Showing the placement groups of a supercluster"
kubectl -n simplyblock get stc production -o jsonpath='{range .status.members[*]}{.name}{"\t"}{.phase}{"\t"}{.placementEligible}{"\n"}{end}'
```

## Storage Pools and StorageClasses

A `StoragePool` whose `clusterRef` names the supercluster is created in every placement group under the same name. Its
`status.members` lists the backend pool of every placement group with its phase. A placement group that does not yet
hold every pool of the supercluster is not eligible for placement.

A pool's capacity limit applies to the supercluster as a whole and is divided evenly among the placement groups that
accept new volumes. `allowedNodes` applies to every placement group, because a volume can be placed in any of them.

A StorageClass for a pool of the supercluster sets `cluster_id` to the `status.uuid` of the supercluster:

```yaml title="Example of a StorageClass for a supercluster pool (storage-class-production.yaml)"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: production-tenant-a
  labels:
    storage.simplyblock.io/namespace: simplyblock
    storage.simplyblock.io/cluster: production
    storage.simplyblock.io/pool: tenant-a
provisioner: csi.simplyblock.io
parameters:
  cluster_id: "<supercluster status.uuid>"
  pool_name: tenant-a
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

`WaitForFirstConsumer` is recommended. It lets the placement prefer placement groups in the region of the consuming
pod. The placement group chosen for a claim is recorded in the claim's annotation
`storage.simplyblock.io/placement-member`.

Every placement group also has a default pool and StorageClass of its own. Volumes of such a class are created in that
placement group directly, without placement.

## Choosing the Placement Strategy

The placement strategy of the supercluster ranks the eligible placement groups for every new volume:

```yaml title="Example of a supercluster that places by provisioned ratio"
spec:
  supercluster:
    placement:
      strategy: LeastProvisioned
```

| Strategy                          | Places a new volume in the placement group with       |
|-----------------------------------|-------------------------------------------------------|
| `MostAvailableCapacity` (default) | The most free physical capacity.                      |
| `LeastProvisioned`                | The lowest ratio of provisioned to physical capacity. |
| `LeastVolumes`                    | The fewest volumes.                                   |

Besides `spec.supercluster`, a supercluster only accepts `spec.warningThreshold` and `spec.criticalThreshold`, which
apply to its combined capacity. All other settings belong to the placement groups.

## Taking a Placement Group out of Placement

`spec.disablePlacement: true` on a placement group stops new volumes from being placed in it. The volumes already in it
keep working, and its pools and status are unaffected. The supercluster records the change with the event
`MemberPlacementChanged`.

```bash title="Taking a placement group out of placement"
kubectl -n simplyblock patch stc production-dense-kqv \
    --type=merge -p '{"spec":{"disablePlacement":true}}'
```

A placement group also leaves placement on its own while it is not serving, while it lacks a pool of the supercluster,
or while it is above its critical capacity threshold.

## Growing a Supercluster

A growth `ClusterDeploymentConfig` names an existing cluster in `spec.clusterRef`, and what it names decides what is
grown:

| `spec.clusterRef` names | Expansion does                                                              |
|-------------------------|-----------------------------------------------------------------------------|
| The supercluster        | Creates one new placement group per node set.                               |
| A placement group       | Adds the workers of every node set to that placement group, up to 32 nodes. |
| A standalone cluster    | Adds the workers of every node set to that cluster, up to 32 nodes.         |

A document that adds placement groups states their sizing in `spec.cluster`, whose `name` is ignored. Without
`spec.cluster` it is refused with `MemberSizingUnstated`. Its node sets may override the sizing as in a creating
document.

```yaml title="Example of a growth document adding a placement group (grow-production.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ClusterDeploymentConfig
metadata:
  name: grow-production
  namespace: simplyblock
spec:
  approved: false
  clusterRef: production
  cluster:
    maxSubsystemCount: 50
    vcpuCount: 8
    stripe:
      dataChunks: 2
      parityChunks: 1
  nodeSets:
    - name: dense
      groups:
        - name: default
          workers: [worker-09, worker-10, worker-11, worker-12]
          devices:
            nvme: ["0000:01:00.0", "0000:02:00.0"]
```

A new placement group receives every pool of the supercluster before it becomes eligible for placement, and the
supercluster records the event `MemberAdded`. Adding nodes to a placement group follows
[Expanding a Storage Cluster](expanding-storage-cluster.md). The 32 storage node limit counts the nodes the placement
group already has.

## Relocating a Volume

A volume moves to another placement group of its supercluster through a `PersistentVolumeOps` with the action
`Relocate`. The move runs online, and the consuming pods keep running. Volumes that share an NVMe subsystem with the
named volume move with it. The mechanism is described in
[Placement Groups](../../../architecture/concepts/placement-groups.md#moving-a-volume-between-placement-groups).

```yaml title="Example of a relocation to another placement group (relocate-db.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: PersistentVolumeOps
metadata:
  name: relocate-db-0
spec:
  persistentVolumeName: pvc-3f2a1c9e-84b1-4d2e-9f3a-1234abcd5678
  action: Relocate
  relocate:
    targetClusterRef: production-fast-mzt
```

```bash title="Starting and following the relocation"
kubectl apply -f relocate-db.yaml
kubectl get pvops relocate-db-0 -w
```

The target must be another placement group of the same supercluster, and it must not set `disablePlacement`. Admission
refuses encrypted volumes with `EncryptedVolumeNotMovable`, as well as volumes whose claim is in a consistency group.

The operation walks the steps `Validating`, `Replicating`, `Committing`, `AwaitingCutover`, `AttachingPaths`,
`Proceeding`, and `Verifying`, and ends in the phase `Succeeded`. `status.relocate.volumes` lists every volume that
moves, and each moved PersistentVolume is annotated with `storage.simplyblock.io/relocated-to`.

`spec.abort: true` stops the replication and ends the operation in the phase `Aborted`, as long as it has not
reached `Committing`.
From then on, the cutover cannot be undone, and an abort is ignored with the event `RelocationAbortIgnored`.

| Event                  | Meaning                                                                                                                                                         |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `TargetMemberNotReady` | The target placement group does not accept volumes yet. The operation waits in `Validating`.                                                                    |
| `PathAttachHeld`       | A consuming node could not attach the target's paths. The cutover is held and retried.                                                                          |
| `CutoverWithoutPaths`  | The cutover happened while a node lacked the target's paths. Pods on the nodes in `status.relocate.nodesMissingPaths` lose the volume until they are restarted. |
| `HandleUnresolved`     | The volume handle does not resolve to the target after the cutover. The operation fails.                                                                        |

## Monitoring

The supercluster records its events on its own `StorageCluster`:

| Event                        | Type    | Meaning                                                          |
|------------------------------|---------|------------------------------------------------------------------|
| `MemberAdded`                | Normal  | A placement group joined the supercluster.                       |
| `MemberPlacementChanged`     | Normal  | A placement group left placement or returned to it.              |
| `AggregateCapacityThreshold` | Warning | The combined capacity crossed the warning or critical threshold. |
| `AggregateCapacityExhausted` | Warning | No placement group had room for a requested volume.              |

The operator exports the following metrics:

| Metric                                                | Description                                                                     |
|-------------------------------------------------------|---------------------------------------------------------------------------------|
| `simplyblock_supercluster_member_count`               | Placement groups by state: `eligible`, `cordoned`, `notServing`, and `missing`. |
| `simplyblock_supercluster_capacity_bytes`             | The combined `total`, `used`, and `provisioned` bytes.                          |
| `simplyblock_supercluster_placement_decisions_total`  | Volume placements by chosen placement group, or `exhausted`.                    |
| `simplyblock_supercluster_placement_duration_seconds` | Time taken to choose a placement group for a new volume.                        |

`simplyblock_supercluster_placement_decisions_total` shows a skewed placement: one placement group receiving every new
volume while another stays empty. A rising `notServing` count shows a supercluster that runs on fewer placement groups
than it was built with. The combined capacity requires the metrics exporter to be reachable. Without it,
`status.capacity` stays empty.

## Limitations

- **Cluster operations:** A `StorageClusterOps` naming a supercluster fails. Restarts, shutdowns, and starts are run
  on each placement group instead.
- **Removing a placement group:** Removing a placement group together with its volumes is not supported. Before a
  placement group is deleted, every volume in it has to be relocated or deleted. A supercluster cannot be deleted while
  any placement group names it.
- **Shared workers:** A worker serves one placement group only.
- **Pool limits:** A pool of a supercluster carries a capacity limit only, as every pool does.
- **Replication:** A `ReplicationPair` cannot name a supercluster. Placement groups are named directly.
