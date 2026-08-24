---
title: "Asynchronous Replication"
description: "Configure snapshot-based asynchronous replication between simplyblock clusters with the ReplicationPair, ReplicationPolicy, and ReplicationOps resources."
weight: 10520
---

Simplyblock replicates volumes between two storage clusters by transferring copy-on-write snapshots at a fixed
interval. For each interval, a snapshot is taken on the source cluster and replicated into the target cluster, where
the snapshots form an incremental chain. On Kubernetes, replication is declared through custom resources, and every
backend call is issued by the Simplyblock Operator.

For the architecture background, see [Replication Concepts](../../../architecture/concepts/replication.md).

## Scope and Prerequisites

Asynchronous replication with controlled failover and failback is a Kubernetes-only feature, managed by the
Simplyblock Operator.

Both clusters have to be represented by a `StorageCluster` resource in the same namespace as the replication
resources, which means both are attached to the same simplyblock control plane. A cluster is referenced by the name
of its `StorageCluster`, and its UUID has to be reported in `status.uuid` before replication can be configured.
Cross-namespace references are not supported. Both clusters have to be active with their storage nodes online, and
the two clusters need network interconnectivity.

!!! note
    For multi-site setups, such as disaster recovery or offsite failover, a distributed control plane is highly
    recommended. A typical setup is two management nodes on the main site and three management nodes on the failover
    site, so that quorum is maintained during a site failure.

## Resource Model

Replication is split across four resources. The first two are created by an administrator, the third is created by
the operator, and the fourth is created to trigger an operation.

| Resource            | Short name | Cardinality            | Purpose                                                                   |
|---------------------|------------|------------------------|---------------------------------------------------------------------------|
| `ReplicationPair`   | `relpair`  | One per cluster pair   | Declares the source and the target cluster of a replication relationship. |
| `ReplicationPolicy` | `repl`     | One per schedule       | Sets the cadence, the mode, and the snapshot retention of a pair.         |
| `ReplicationSlot`   | `relslot`  | One per replicated PVC | Holds the live per-volume replication state. Created by the operator.     |
| `ReplicationOps`    | `replops`  | One per operation      | Triggers a failover or a failback and records its outcome.                |

A pair is reusable. Several policies can reference the same pair to replicate between the same two clusters with
different schedules or retention.

## Declaring the Cluster Pair

A `ReplicationPair` names the local cluster and the remote cluster. Creating it provisions the replication target on
the backend, and deleting it tears that target down.

```yaml title="Example of a ReplicationPair between two clusters (replication-pair.yaml)"
apiVersion: storage.simplyblock.io/v1alpha1
kind: ReplicationPair
metadata:
  name: site-a-to-site-b
  namespace: simplyblock
spec:
  sourceCluster: simplyblock-cluster
  targetCluster: simplyblock-cluster-dr
```

```bash title="Creating the replication pair"
kubectl apply -f replication-pair.yaml
```

The pair is usable once `status.ready` is `true`, at which point the UUID of the backend replication target is
recorded in `status.backendTargetID`.

```bash title="Checking the state of the replication pairs"
kubectl get replicationpair -n simplyblock
```

```plain title="Example output of the replication pair listing"
NAME               SOURCE                TARGET                   READY   AGE
site-a-to-site-b   simplyblock-cluster   simplyblock-cluster-dr   true     2m
```

`spec.targetCluster` is immutable. Replicating to a different cluster requires a new `ReplicationPair`.

## Defining a Replication Policy

A `ReplicationPolicy` couples a pair to a schedule and a retention rule. It is the resource that volumes are attached
to.

```yaml title="Example of a ReplicationPolicy for disaster recovery (replication-policy.yaml)"
apiVersion: storage.simplyblock.io/v1alpha1
kind: ReplicationPolicy
metadata:
  name: dr-policy
  namespace: simplyblock
spec:
  pairRef: site-a-to-site-b
  mode: failover
  interval: 5m
  snapshotRetention: 3
```

```bash title="Creating the replication policy"
kubectl apply -f replication-policy.yaml
```

The policy waits for its pair to become ready before the backend policy is created. Once `status.ready` is `true`,
the backend policy UUID is held in `status.backendPolicyID`, and `status.slotCount` reports how many volumes are
currently attached.

```bash title="Checking the state of the replication policies"
kubectl get replicationpolicy -n simplyblock
```

```plain title="Example output of the replication policy listing"
NAME        PAIR               MODE       INTERVAL   READY   SLOTS   AGE
dr-policy   site-a-to-site-b   failover   5m         true    4       2m
```

### Policy Fields

| Field               | Type     | Default    | Description                                                                                            |
|---------------------|----------|------------|--------------------------------------------------------------------------------------------------------|
| `pairRef`           | string   | -          | Name of the `ReplicationPair` in the same namespace. Required.                                         |
| `mode`              | string   | `failover` | `failover` keeps the target a read-only standby. `migration` prepares a planned cutover to the target. |
| `interval`          | duration | `5m`       | How often a replication snapshot is taken. Rounded to whole minutes, with one minute as the minimum.   |
| `snapshotRetention` | int      | `3`        | Minimum number of snapshots retained on the target. The lowest accepted value is `2`.                  |

An interval that cannot be parsed as a duration falls back to five minutes.

## Selecting the Volumes to Replicate

A volume is opted into replication by the `storage.simplyblock.io/replication-policy` annotation, which names a
`ReplicationPolicy` in the namespace of the PVC. The annotation is read from the PVC and from its StorageClass, and
the annotation on the PVC wins when both carry one. Annotating the StorageClass therefore replicates every volume
provisioned from it, while annotating a single PVC replicates only that volume.

```yaml title="Example of a StorageClass that replicates every volume it provisions"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: simplyblock-dr
  annotations:
    storage.simplyblock.io/replication-policy: dr-policy
provisioner: csi.simplyblock.io
```

```bash title="Opting a single PVC into a replication policy"
kubectl annotate pvc my-pvc -n simplyblock \
    storage.simplyblock.io/replication-policy=dr-policy
```

The annotation is honored on a new PVC and on an already-bound one. A `ReplicationSlot` is created as soon as the PVC
is `Bound` and the named policy is ready, and it is named `<policy>-<pvc>`. The slot is owned by its PVC, so deleting
the PVC deletes the slot and stops replication for that volume.

!!! note
    The `replicate` StorageClass parameter is unrelated to this mechanism. It is a backend volume property and does
    not attach a volume to a `ReplicationPolicy`. See
    [Storage Class: Available Parameters](../../usage/storage-class.md#available-parameters).

### Changing or Removing the Policy

Pointing the annotation at a different policy is carried out as a detach followed by a fresh attach, which means the
new target receives a full copy of the volume. The existing slot is deleted first, and the replacement slot is
created once the detach has completed.

Removing the annotation stops replication. The replication snapshots are deleted on both the source and the target,
and the slot is removed afterward.

```bash title="Removing a PVC from replication"
kubectl annotate pvc my-pvc -n simplyblock \
    storage.simplyblock.io/replication-policy-
```

## Replication Slots

One `ReplicationSlot` exists per replicated volume and carries the state of that volume. The slot records the volume
handle of the source volume in `spec.volumeID`, in the form `<clusterUUID>:<poolUUID>:<volumeUUID>`.

```bash title="Listing the replication slots of a namespace"
kubectl get replicationslot -n simplyblock
```

```plain title="Example output of the replication slot listing"
NAME                POLICY      PVC       STATE         DIRECTION   AGE
dr-policy-my-pvc    dr-policy   my-pvc    replicating   source      4m
dr-policy-logs      dr-policy   logs      replicating   source      4m
```

`status.direction` states which side of the relationship the local cluster holds, so a slot reads `source` under
normal replication and `target` after a failover.

### Slot States

| State             | Description                                                                                   |
|-------------------|-----------------------------------------------------------------------------------------------|
| `replicating`     | Steady state. Snapshots are taken and transferred on the policy's interval.                   |
| `cutover_pending` | A planned cutover has been prepared on the backend and is awaiting its commit.                |
| `cutover_done`    | The cutover has completed.                                                                    |
| `failed_over`     | The volume is served by the target cluster. `status.targetNQN` carries the NQN on the target. |
| `detaching`       | Replication is being stopped and the replication snapshots are being deleted on both sides.   |
| `error`           | A backend call failed. `status.message` holds the reason, and the attach is retried.          |
| `attaching`       | Legacy state, only seen on slots created by earlier operator versions.                        |

An attach is synchronous on the backend, so a new slot reaches `replicating` directly rather than passing through an
intermediate state.

## Monitoring Replication

While a slot is replicating, the operator polls the backend every 60 seconds and records the timestamp of the last
successful snapshot in `status.lastReplicatedAt`. After a failed backend call, the poll backs off to 30 seconds.

```bash title="Reading the replication state of a single volume"
kubectl get replicationslot dr-policy-my-pvc -n simplyblock \
    -o jsonpath='{.status}' | jq .
```

```bash title="Watching the replication lag across all volumes of a namespace"
kubectl get replicationslot -n simplyblock \
    -o custom-columns=NAME:.metadata.name,STATE:.status.state,LAST:.status.lastReplicatedAt
```

A state change that originates on the backend, such as a cutover or an externally triggered failover, is picked up by
the same poll and reflected into the slot.

## Failover

A failover is never performed automatically. It is triggered by creating a `ReplicationOps` resource with
`action: failover`, which covers both the unplanned failover of a lost site and the planned cutover of a `migration`
policy.

```bash title="Failing over every volume of a policy to the target cluster"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha1
kind: ReplicationOps
metadata:
  name: failover-dr-policy
  namespace: simplyblock
spec:
  action: failover
  scope: policy
  ref: dr-policy
EOF
```

Every affected slot is moved to `failed_over` with `direction: target`, and the UUID of the volume on the target
cluster is recorded per volume in `status.results`.

!!! warning
    Data written on the source after the last successful replication snapshot is not present on the target. The data
    gap is at least the configured replication interval, plus any replication lag.

### Failover Scopes

`spec.scope` decides which volumes are affected, and `spec.ref` names the resource that the scope refers to.

| Scope    | `spec.ref` names a  | Effect                                                            |
|----------|---------------------|-------------------------------------------------------------------|
| `target` | `ReplicationPair`   | Fails over every volume of every policy that references the pair. |
| `policy` | `ReplicationPolicy` | Fails over every volume attached to that policy.                  |
| `volume` | `ReplicationSlot`   | Fails over a single volume. Exactly one slot has to match.        |

A `spec.ref` that does not resolve to a resource of the matching kind is rejected by a validating webhook when the
`ReplicationOps` is created. An operation that has reached `Succeeded` or `Failed` is never run again, so a repeat,
or a correction, requires a new `ReplicationOps` resource.

Only one operation may run against a policy at a time, tracked in `ReplicationPolicy.status.activeOpsRef`. A
`target`-scoped operation locks its pair instead, tracked in `ReplicationPair.status.activeOpsRef`. A second
operation waits for the lock rather than failing.

## Failback

Once the original source cluster is available again, the volumes are returned to it by a `ReplicationOps` resource
with `action: failback`. Reverse replication is started for each volume and then committed, which restores
`direction: source` and returns the slot to `replicating`.

```bash title="Failing back every volume of a policy to the source cluster"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha1
kind: ReplicationOps
metadata:
  name: failback-dr-policy
  namespace: simplyblock
spec:
  action: failback
  scope: policy
  ref: dr-policy
EOF
```

`spec.sourceClusterID` selects the cluster to recover to and is only read for a failback. Left unset, the volumes
return to their original source cluster.

A failback is only supported for the `policy` and the `volume` scope. A `target`-scoped failback is rejected and the
operation fails, so a pair-wide failback is performed one policy at a time.

!!! important
    Failback holds a short freeze while the final delta is transferred and the volume is cut back. For production
    workloads, a maintenance window should be planned.

Unlike a failover, a failback reports per-volume outcomes independently. A volume that fails is recorded as `failed`
in `status.results` while the remaining volumes continue, and the operation as a whole ends in `Failed`.

### Tracking an Operation

```bash title="Watching a replication operation"
kubectl get replicationops -n simplyblock -w
```

```plain title="Example output of the replication operation listing"
NAME                 ACTION     SCOPE    REF         PHASE       SUBPHASE               AGE
failover-dr-policy   failover   policy   dr-policy   Succeeded                          3m
failback-dr-policy   failback   policy   dr-policy   Running     CommittingFailback     8s
```

`status.phase` moves from `Pending` through `Running` to `Succeeded` or `Failed`, and `status.subphase` names the
step within `Running`: `TriggeringFailover`, `TriggeringTargetFailover`, `UpdatingSlotStatuses`, `StartingFailback`,
or `CommittingFailback`. The per-volume outcome is held in `status.results`, where each entry carries the slot it
belongs to, a status of `succeeded`, `skipped`, or `failed`, and a detail message.

```bash title="Reading the per-volume outcome of an operation"
kubectl get replicationops failover-dr-policy -n simplyblock \
    -o jsonpath='{.status.results}' | jq .
```

## Deletion Order

The resources are torn down in the reverse order of their creation, and the operator blocks a deletion that would
break that order.

A `ReplicationPolicy` cannot be removed while any `ReplicationSlot` still references it, so the volumes have to be
detached first, either by removing the annotation or by deleting their PVCs. A `ReplicationPair` cannot be removed
while any `ReplicationPolicy` still references it. Once the last policy is gone, the backend replication target is
deleted with the pair.

## Events

The operator emits Kubernetes events on the affected resources. Useful reasons to filter on:

| Reason              | Emitted on        | Meaning                                                  |
|---------------------|-------------------|----------------------------------------------------------|
| `Replicating`       | `ReplicationSlot` | The volume is attached and replicating.                  |
| `CutoverPending`    | `ReplicationSlot` | A planned cutover is awaiting its commit.                |
| `FailedOver`        | `ReplicationSlot` | The volume is now served by the target cluster.          |
| `Detached`          | `ReplicationSlot` | Replication was stopped for the volume.                  |
| `Error`             | `ReplicationSlot` | A backend call for the volume failed.                    |
| `FailoverSucceeded` | `ReplicationOps`  | A failover completed for every affected volume.          |
| `FailbackSucceeded` | `ReplicationOps`  | A failback completed for every affected volume.          |
| `Failed`            | `ReplicationOps`  | The operation failed. `status.message` holds the reason. |

```bash title="Streaming replication events of a namespace"
kubectl get events -n simplyblock --watch \
    --field-selector reason=FailedOver
```
