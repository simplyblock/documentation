---
title: "Online Cluster Migration"
description: "Move volumes online from one simplyblock cluster to another with migration plans: forecast, dry run, one volume per node, and a short-freeze cutover."
weight: 10525
---

Online cluster migration moves volumes from one simplyblock storage cluster to another while the workloads that use
them keep running. It is built on [asynchronous replication](asynchronous-replication.md) in the `migration` mode: the
volumes are copied to the target cluster while the source keeps serving them, and each volume ends with a short I/O
freeze, the cutover, after which the target cluster serves it. Pods are not restarted, and the PersistentVolumes and
PersistentVolumeClaims stay as they are.

A typical use is replacing a storage cluster, for example, when the storage node group of an EKS cluster moves
to a new Kubernetes version (see [Upgrading EKS](../cluster/eks-upgrade.md)).

Online cluster migration is different from [volume migration](../../../architecture/concepts/volume-migration.md),
which moves a volume between the storage nodes of one cluster, and from
[relocation](../scaling/superclusters.md#relocating-a-volume), which moves a volume between the placement groups of a
supercluster.

## How a Migration Runs

The storage control plane drives every migration through a **migration plan**. A plan holds the volumes to move, the
target storage node chosen for each of them, and their progress. On Kubernetes, the Simplyblock Operator creates and
follows the plan on behalf of a `ReplicationOps` resource.

Every volume of a plan passes through these steps:

1. **Initial copy:** Replication in the `migration` mode starts for the volume, unless it already replicates to the
   target cluster. The first snapshot carries the whole volume to the target cluster.
2. **Catch-up:** Further snapshots on the replication interval carry the data written since.
3. **Convergence:** Once replication is close behind the source, the cutover takes snapshots back to back until a
   round transfers in about two seconds, so that little is left to copy during the freeze.
4. **Preconnect:** The writable copy of the volume is prepared on the target cluster, and the target paths are
   connected on the Kubernetes node that consumes the volume.
5. **Cutover:** The source stops serving the volume, the remaining delta is copied, and the target paths become
   active. Client I/O is held during this freeze and resumes on the target cluster.

While a volume is in the first three steps, its data is still served by the source cluster, and a failure only delays
the migration.

### One Volume per Storage Node

A source storage node migrates one volume at a time, from its first snapshot through its cutover. The other volumes of
the node wait: they take no replication snapshots and transfer nothing until the volume ahead of them has cut over.
Storage nodes progress in parallel. A volume whose cutover failed or was canceled releases the node, so that one
failing volume does not hold up the others.

Volumes are queued largest first, so that the longest copies start early. The members of a consistency group move
together and share one turn.

Transfers and cutovers are also serialized per logical volume store of the source cluster. The volumes of different
logical volume stores cut over in parallel.

### Target Placement

Each volume is assigned to a target storage node when the plan is created. Among the online storage nodes of the
target cluster that are below their subsystem limit, the control plane picks the one with the lowest planned load: the
provisioned size of the volumes on the node plus that of the volumes already headed for it. Ties go to the node with
fewer subsystems. Volumes that already replicate to the target keep their target node, and volumes that share an NVMe
subsystem or a consistency group are placed together.

### The Cutover

The cutover runs as follows:

1. **Prepare:** A writable clone of the last replicated snapshot is created on the target cluster.
2. **Preconnect:** The operator starts a preconnect Job on the Kubernetes node that runs a pod mounting the claim. The
   Job connects the target cluster's paths to the volume's NVMe subsystem, and the operator then signals the control
   plane to proceed. A volume without a running consumer proceeds without a preconnect. The control plane waits up to
   120 seconds for the signal and then proceeds without it.
3. **Fence:** Every reachable path of the source cluster is set to the ANA state `inaccessible`. Client I/O queues on
   the client.
4. **Final delta:** The data written since the last replicated snapshot is copied into the clone on the target
   cluster.
5. **Switch:** The target paths are set to `optimized` on the leading storage node and `non_optimized` on the others.
   The queued I/O drains to the target cluster.

The freeze lasts from the fence to the switch and typically takes a few seconds. A volume written faster than it
replicates freezes for longer, because the convergence stops after at most 12 rounds and the remaining delta is copied
during the freeze.

The cutover is carried out by the storage nodes that lead the logical volume stores on both sides, so it also
completes while a primary storage node is down. While a tertiary node leads the target logical volume store, the
cutover waits. If a node is lost during the freeze, the source paths are restored, the client resumes on the source,
and the cutover is retried.

!!! info
    The cutover relies on the ANA path states of NVMe multipathing. A client without native NVMe multipathing cannot
    switch paths, and the cutover interrupts the I/O of the volume (see
    [EKS Node Images](../../installation/eks.md#node-images)).

## Prerequisites and Limits

- **One control plane:** Both clusters are attached to the same simplyblock control plane and have network
  connectivity to each other.
- **Replication resources:** A `ReplicationPair` from the source to the target cluster and a `ReplicationPolicy` with
  `mode: migration` that references it, as described in [Asynchronous Replication](asynchronous-replication.md).
- **Free capacity on the source:** The snapshot of a volume's initial copy keeps every block that is overwritten while
  the copy runs, up to the volume's used size. A plan is refused when the source cluster is at or above its capacity
  warning threshold. A plan is accepted with a warning when the free capacity of the source is smaller than the used
  size of the selected volumes.
- **Write rate:** A volume converges only while replication outruns the writes of its clients. The forecast reports
  a logical volume store whose volumes are written at 90% of its replication throughput or more as not converging.
  Their cutover does not start until the write rate drops.
- **Encrypted volumes:** Encrypted volumes cannot be migrated. Deleting the source would delete the only copy of the
  key, and replication does not carry the key to the target.
- **Consistency groups:** A consistency group is migrated as a whole. A plan that selects only some of its members
  skips them.
- **Disaster recovery relationships:** A volume that replicates in the `failover` mode is not moved by a selection of
  a whole cluster or pool. A volume that replicates to a third cluster is skipped.
- **Preconnect:** Target paths are connected on one Kubernetes node per volume, the node of the first running pod (by
  name) that mounts the claim.

## Starting a Migration on Kubernetes

A migration is started by a `ReplicationOps` resource with `action: migration`. The `cluster` scope moves every claim
whose volume lives on the source cluster, in every namespace, and enrolls the claims that are not replicated yet under
the migration policy named in `spec.policyRef`.

```yaml title="Example of a migration policy (migration-policy.yaml)"
apiVersion: storage.simplyblock.io/v1alpha1
kind: ReplicationPolicy
metadata:
  name: move-to-new
  namespace: simplyblock
spec:
  pairRef: old-to-new
  mode: migration
  interval: 1m
```

```yaml title="Example of a migration of a whole cluster (migrate-cluster.yaml)"
apiVersion: storage.simplyblock.io/v1alpha1
kind: ReplicationOps
metadata:
  name: migrate-old-cluster
  namespace: simplyblock
spec:
  action: migration
  scope: cluster
  ref: simplyblock-cluster-old
  policyRef: move-to-new
  deleteSource: true
```

```bash title="Starting the migration"
kubectl apply -f migration-policy.yaml
kubectl apply -f migrate-cluster.yaml
```

### Migration Fields

| Field          | Description                                                                                                                                              |
|----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|
| `action`       | `migration`.                                                                                                                                             |
| `scope`        | Which volumes move. See the table below.                                                                                                                 |
| `ref`          | The resource the scope refers to. For the `cluster` scope, the name of the source `StorageCluster`, or its UUID.                                         |
| `policyRef`    | Required for the `cluster` scope and refused for every other scope. Names a `ReplicationPolicy` with `mode: migration` whose pair starts at the source.  |
| `dryRun`       | Publishes the plan and its forecast without enrolling, replicating, or cutting over anything. The operation succeeds once the forecast is in its status. |
| `deleteSource` | Deletes each source volume after its cutover. See [After the Cutover](#after-the-cutover).                                                               |

`policyRef` and `dryRun` are immutable and are only accepted with `action: migration`.

| Scope     | `spec.ref` names a  | Volumes that move                                                                       |
|-----------|---------------------|-----------------------------------------------------------------------------------------|
| `cluster` | `StorageCluster`    | Every bound claim, in any namespace, whose volume lives on the named cluster right now. |
| `target`  | `ReplicationPair`   | Every volume of every policy that references the pair.                                  |
| `policy`  | `ReplicationPolicy` | Every volume attached to the policy.                                                    |
| `volume`  | `ReplicationSlot`   | A single volume.                                                                        |

### Selecting Claims with the Cluster Scope

With the `cluster` scope, the operator decides for every bound claim:

- **Already under the policy:** A claim whose `ReplicationSlot` follows `spec.policyRef` is included.
- **Not replicated:** A claim without a slot and without a replication policy is enrolled. The operator sets the
  `storage.simplyblock.io/replication-policy` annotation on the claim, and a slot is created for it as for any
  annotated claim. A claim outside the policy's namespace is annotated with `<namespace>/<name>` of the policy.
- **Under another policy:** A claim whose slot, annotation, or StorageClass names another policy is skipped and
  never overwritten.
- **Moved away:** A claim whose volume has already left the source cluster is skipped with the detail
  `moved to cluster <id>`.

The plan is created only once every included volume replicates. Until then, the operation stays in the subphase
`Enrolling` or `AwaitingReplication`. A slot in `error` becomes a `failed` result, and a slot that is `failed_over`
is skipped and has to be failed back first.

### Forecasting with a Dry Run

A dry run shows which volumes would move, to which target storage nodes, how much data that is, and how long it is
expected to take, before anything starts.

```yaml title="Example of a dry run (migrate-cluster-dry-run.yaml)"
apiVersion: storage.simplyblock.io/v1alpha1
kind: ReplicationOps
metadata:
  name: migrate-old-cluster-forecast
  namespace: simplyblock
spec:
  action: migration
  scope: cluster
  ref: simplyblock-cluster-old
  policyRef: move-to-new
  dryRun: true
```

```bash title="Reading the forecast of the dry run"
kubectl get replicationops migrate-old-cluster-forecast -n simplyblock \
    -o jsonpath='{.status.forecast}' | jq .
```

## Watching a Migration

The operation stays `Running` until every volume has cut over. It ends in `Succeeded` when every volume moved, and in
`Failed` when any volume did not, with the outcome of each volume kept in `status.results`. The operator reads the
plan every 30 seconds. The wide output adds the forecast time to completion and the convergence verdict.

```bash title="Watching a migration"
kubectl get replicationops -n simplyblock -o wide -w
```

```plain title="Example output of the migration listing"
NAME                  ACTION      SCOPE     REF                       PHASE     SUBPHASE       ETA    CONVERGING   AGE
migrate-old-cluster   migration   cluster   simplyblock-cluster-old   Running   TrackingPlan   5400   true         42m
```

`status.subphase` names the step of the operation:

| Subphase              | Meaning                                                                                         |
|-----------------------|-------------------------------------------------------------------------------------------------|
| `Enrolling`           | Claims were annotated, and their replication slots do not exist yet.                            |
| `AwaitingReplication` | A slot does not replicate yet. The plan is created once every slot does.                        |
| `CreatingPlan`        | The plan is being created in the control plane.                                                 |
| `TrackingPlan`        | The plan runs. `status.planID` names it.                                                        |
| `AwaitingCutover`     | A control plane without migration plans received one cutover per volume, and they are followed. |

### Per-Volume Progress

Each entry of `status.results` carries the slot in `slotRef`, the claim in `pvcRef`, an outcome in `status`
(`pending`, `succeeded`, `skipped`, or `failed`), and a `detail`. For a volume in the plan, it also carries
`targetNodeID`, `bytesRemaining`, `etaSeconds`, and the plan's state of the volume in `state`:

| State          | Meaning                                                                      |
|----------------|------------------------------------------------------------------------------|
| `waiting`      | Another volume of the same source storage node is migrating.                 |
| `replicating`  | The initial copy or the catch-up runs.                                       |
| `queued`       | Caught up, and waiting for the logical volume store's cutover slot.          |
| `converging`   | Taking the back-to-back snapshots that shrink the final delta.               |
| `cutting_over` | The target copy is prepared. The preconnect, the freeze, and the switch run. |
| `done`         | The target cluster serves the volume.                                        |
| `failed`       | The volume did not move. `detail` holds the reason.                          |
| `canceled`     | The cutover was canceled before it started.                                  |
| `skipped`      | The volume was not taken into the plan. `detail` holds the reason.           |

```bash title="Reading the per-volume progress of a migration"
kubectl get replicationops migrate-old-cluster -n simplyblock \
    -o jsonpath='{.status.results}' | jq .
```

### Forecast

`status.forecast` holds the estimate for the whole migration. It is recomputed on every read, because client writes
during the copy add to the data still to transfer.

| Field                   | Description                                                                                     |
|-------------------------|-------------------------------------------------------------------------------------------------|
| `bytesRemaining`        | Data still to be copied across all volumes.                                                     |
| `etaSeconds`            | Forecast time until the last volume has cut over. Unset while the migration does not converge.  |
| `completesAt`           | Forecast completion time. Unset while the migration does not converge.                          |
| `throughputBytesPerSec` | The transfer rate the forecast assumes.                                                         |
| `throughputMeasured`    | `false` while no transfer has completed and a default rate of 200 MiB/s is assumed.             |
| `converging`            | `false` when the volumes of a logical volume store are written about as fast as they replicate. |
| `dirtyBytesPerSec`      | The rate at which clients write to the volumes still being copied.                              |
| `notConvergingLVS`      | The logical volume stores of the source whose volumes are written faster than they replicate.   |

The throughput is measured per logical volume store from the plan's completed transfers. Until a cutover has been
measured, each pending cutover counts as 60 seconds. `status.warnings` lists risks the control plane found when it
created the plan, such as too little free capacity on the source.

### Events

| Reason                 | Emitted on        | Meaning                                                                          |
|------------------------|-------------------|----------------------------------------------------------------------------------|
| `MigrationPlanCreated` | `ReplicationOps`  | The plan was created. The message holds the number of volumes and the forecast.  |
| `MigrationForecast`    | `ReplicationOps`  | A dry run completed with its forecast.                                           |
| `NotConverging`        | `ReplicationOps`  | Clients write faster than replication transfers.                                 |
| `Converging`           | `ReplicationOps`  | Replication outruns the client writes again.                                     |
| `MigrationComplete`    | `ReplicationOps`  | Every volume of the plan has cut over.                                           |
| `Failed`               | `ReplicationOps`  | The operation failed. `status.message` holds the reason.                         |
| `CutoverPending`       | `ReplicationSlot` | The cutover of the volume is prepared and waits for the preconnect.              |
| `PreconnectStarted`    | `ReplicationSlot` | The preconnect Job connects the target paths on the consuming node.              |
| `PreconnectFailed`     | `ReplicationSlot` | The preconnect Job failed. The cutover is held, and the Job is retried.          |
| `LatePreconnect`       | `ReplicationSlot` | The target paths were connected after the switch, because the window was missed. |
| `VolumeMoved`          | `ReplicationSlot` | The slot follows its volume to the cluster that serves it now.                   |

## After the Cutover

Once a volume has cut over, replication of the source volume stops, and its slot reaches `cutover_done`. The
PersistentVolume keeps its volume handle, which still names the source cluster, and the CSI driver follows the
replication relationship to the volume that serves the data.

With `deleteSource: true`, the source volume is deleted after its cutover. The replication snapshots its data sat on
are retired with it: the snapshots taken of it for the migration and, after an earlier migration, the copies it was
cloned from. The control plane deletes each retired snapshot once nothing depends on it anymore. User snapshots are
never retired, and neither is the latest recovery point of a consistency group. A failed delete of the source does
not fail the cutover.

Without `deleteSource`, the source volume and its replication snapshots stay on the source cluster and keep using
capacity there. The source paths stay `inaccessible`.

## Moving Volumes Back

A volume moves back, or on to a further cluster, with another migration in the opposite direction: a `ReplicationPair`
and a migration policy from the cluster that serves the volume now, and a new `ReplicationOps`. The `cluster` scope
locates each claim by where its volume lives now, not by its volume handle. A slot that finished an earlier migration
does not hold the claim, and the claim is enrolled under the new policy.

When a volume returns to the cluster it came from, it takes back its original volume UUID there, so that the volume
handle of the PersistentVolume addresses it directly again. The return does not start replication of its own.

## Canceling a Migration

Deleting a `ReplicationOps` releases its lock but does not stop the plan, which keeps running in the control plane. A
plan is canceled through the control plane, with the plan ID from `status.planID`:

```bash title="Canceling a migration plan"
kubectl -n simplyblock exec -it deploy/simplyblock-admin-control -- \
    {{ cliname }} cluster migrate-cancel <PLAN_ID>
```

A cancel stops every cutover that has not yet prepared its target copy. A cutover that has already prepared it is
left to finish, because stopping it would leave a half-built target. The canceled volumes keep replicating. Removing
the replication policy annotation from their claims stops the replication, as described in
[Changing or Removing the Policy](asynchronous-replication.md#changing-or-removing-the-policy).

## Using the Control Plane Directly

The migration plans can also be managed with the CLI of the control plane and through its API, for example, to move
volumes of a cluster that the operator does not manage.

```bash title="Forecasting, starting, and following a migration with the CLI"
{{ cliname }} cluster migrate <SOURCE_CLUSTER_ID> --target-cluster-id <TARGET_CLUSTER_ID> --dry-run
{{ cliname }} cluster migrate <SOURCE_CLUSTER_ID> --target-cluster-id <TARGET_CLUSTER_ID> --delete-source
{{ cliname }} cluster migrate-list <SOURCE_CLUSTER_ID>
{{ cliname }} cluster migrate-status <PLAN_ID>
```

| Option                | Description                                                                                      |
|-----------------------|--------------------------------------------------------------------------------------------------|
| `--target-cluster-id` | The destination cluster. Required.                                                               |
| `--pool`              | Only the volumes of this storage pool (ID). Without it, every volume of the cluster is selected. |
| `--lvols`             | Only these volumes, as a comma-separated list of IDs.                                            |
| `--delete-source`     | Deletes each source volume once its cutover has completed.                                       |
| `--interval-min`      | Replication interval in minutes for the volumes the plan starts replicating. Defaults to `1`.    |
| `--dry-run`           | Shows the selection, the target storage nodes, and the forecast without starting anything.       |

The API serves the same operations under `/api/v2/clusters/{cluster_id}/migration-plans`, where `cluster_id` is the
source cluster:

| Method   | Path         | Description                                                            |
|----------|--------------|------------------------------------------------------------------------|
| `POST`   | `/`          | Creates a plan. Returns `201`, or `200` with `id: null` for a dry run. |
| `GET`    | `/`          | Lists the plans of the cluster.                                        |
| `GET`    | `/{plan_id}` | Returns a plan with the live state of each volume and the forecast.    |
| `DELETE` | `/{plan_id}` | Cancels a plan. Returns `204`.                                         |

The body of a `POST` takes `target_cluster_id`, `name`, `pool_id`, `lvol_ids`, `delete_source`, `interval_min`, and
`dry_run`. `target_cluster_id` may be left out when the listed volumes already replicate to one cluster. `name` makes
the request idempotent: an unfinished plan of the same name is returned instead of a second plan. Volumes listed in
`lvol_ids` are taken even when they replicate in the `failover` mode, which a selection of a whole cluster or pool
skips.

The plan's `status` is `running`, `done`, `partial` (finished, and some volumes did not move), `failed` (no volume
moved), or `canceled`.
