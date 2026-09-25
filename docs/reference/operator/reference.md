---
title: "Simplyblock Operator Reference"
description: "Reference for Simplyblock Operator Custom Resource Definitions (CRDs)."
weight: 20091
---

<!--
This file is generated. Do not edit it by hand.
Run scripts/operator-reference-gen.sh from the documentation repository.
-->

# API Reference

## Packages
- [metrics.simplyblock.io/v1alpha2](#metricssimplyblockiov1alpha2)
- [storage.simplyblock.io/v1alpha1](#storagesimplyblockiov1alpha1)
- [storage.simplyblock.io/v1alpha2](#storagesimplyblockiov1alpha2)


## metrics.simplyblock.io/v1alpha2

The metrics.simplyblock.io/v1alpha2 group: read-only measurements of
simplyblock objects, served by the operator's aggregated API server rather
than stored as custom resources.

It is a separate group from storage.simplyblock.io because the two are served
by different machinery and answer different questions. A kind in the storage
group is a custom resource: it is persisted in etcd, it has a spec a user
writes, and a controller reconciles it. A kind here is a sample: it is
computed on demand from the control-plane cache when a client asks for it, it
is never written, and it is gone the moment the process restarts. Mixing the
two in one group would put a resource that cannot be applied, watched, or
backed up beside seventeen that can.

This mirrors how core Kubernetes splits metrics.k8s.io from the workload
groups, and for the same reason.

v1alpha2 is the group's only version. Both kinds are new, so neither has an
older spelling to convert from, and the group starts where the CRD redesign
leaves the storage group rather than at a version that would exist only for
symmetry. That is also what keeps the aggregated API server's internal version
an alias: each Go type is registered under this version and under the internal
one, so every conversion the codec performs is a copy of a type into itself.

The kinds here are served by an aggregated API server, so no CustomResource-
Definition describes them and `+kubebuilder:skip` keeps the CRD generator out
of this package. Deepcopy generation still runs: the kinds are runtime.Objects
like any other.

The aggregated API server also needs OpenAPI v3 definitions for everything it
serves: since server-side apply went GA, InstallAPIGroup refuses a group
without them. So openapi-gen runs over this package too and writes
zz_generated.openapi.go, which is also what makes `kubectl explain` work.


### Resource Types
- [LogicalVolumeMetrics](#logicalvolumemetrics)
- [StorageClusterMetrics](#storageclustermetrics)
- [StorageDeviceMetrics](#storagedevicemetrics)
- [StorageNodeMetrics](#storagenodemetrics)
- [StoragePoolMetrics](#storagepoolmetrics)





#### LogicalVolumeMetrics













#### StorageClusterMetrics













#### StorageDeviceMetrics













#### StorageNodeMetrics













#### StoragePoolMetrics












## storage.simplyblock.io/v1alpha1

Package v1alpha1 contains API Schema definitions for the simplyblock v1alpha1 API group.

### Resource Types
- [BackupImport](#backupimport)
- [BackupPolicy](#backuppolicy)
- [BackupRestore](#backuprestore)
- [ControlPlane](#controlplane)
- [ReplicationOps](#replicationops)
- [ReplicationPair](#replicationpair)
- [ReplicationPolicy](#replicationpolicy)
- [ReplicationSlot](#replicationslot)
- [StorageBackup](#storagebackup)
- [StorageCluster](#storagecluster)
- [StorageClusterOps](#storageclusterops)
- [StorageNode](#storagenode)
- [StorageNodeOps](#storagenodeops)
- [StorageNodeSet](#storagenodeset)
- [StoragePool](#storagepool)
- [Task](#task)
- [VolumeMigration](#volumemigration)



#### AttachedLvol



AttachedLvol records a single PVC-to-lvol attachment managed by this policy.



_Appears in:_
- [BackupPolicyStatus](#backuppolicystatus)

_Example:_

```yaml
pvcName: string
pvcNamespace: string
lvolID: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `pvcName` _string_ | PVCName is the name of the PVC. |  |  |
| `pvcNamespace` _string_ | PVCNamespace is the namespace of the PVC. |  |  |
| `lvolID` _string_ | LvolID is the simplyblock logical volume UUID that this policy is attached to. |  |  |


#### BackupCredentialsSecretRef







_Appears in:_
- [BackupSpec](#backupspec)

_Example:_

```yaml
name: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `name` _string_ | Name is the name of the Secret in the same namespace as the cluster CR. |  |  |


#### BackupImport



BackupImport imports a completed backup from a source cluster into a target cluster,
creating a StorageBackup CR that can be referenced by a BackupRestore.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha1
kind: BackupImport
metadata:
  name: string
spec:
  sourceClusterName: string
  sourceBackupID: '^[a-zA-Z0-9_-]{1,128}$'
  targetClusterName: string
status:
  phase: string
  message: string
  sourceClusterUUID: string
  targetClusterUUID: string
  importedBackupID: string
  storageBackupRef: string
  completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha1` | | |
| `kind` _string_ | `BackupImport` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  | Optional: \{\} <br /> |
| `spec` _[BackupImportSpec](#backupimportspec)_ | spec defines the desired state of BackupImport |  | Required: \{\} <br /> |
| `status` _[BackupImportStatus](#backupimportstatus)_ | status defines the observed state of BackupImport |  | Optional: \{\} <br /> |


#### BackupImportSpec



BackupImportSpec defines the desired state of BackupImport.



_Appears in:_
- [BackupImport](#backupimport)

_Example:_

```yaml
sourceClusterName: string
sourceBackupID: '^[a-zA-Z0-9_-]{1,128}$'
targetClusterName: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `sourceClusterName` _string_ | SourceClusterName is the StorageCluster CR name of the cluster that owns the backup. |  |  |
| `sourceBackupID` _string_ | SourceBackupID is the UUID of the backup on the source cluster to import. |  | Pattern: `^[a-zA-Z0-9_-]\{1,128\}$` <br /> |
| `targetClusterName` _string_ | TargetClusterName is the StorageCluster CR name of the cluster to import into. |  |  |


#### BackupImportStatus



BackupImportStatus defines the observed state of BackupImport.



_Appears in:_
- [BackupImport](#backupimport)

_Example:_

```yaml
phase: string
message: string
sourceClusterUUID: string
targetClusterUUID: string
importedBackupID: string
storageBackupRef: string
completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _string_ | Phase is the high-level lifecycle shown in kubectl output. |  |  |
| `message` _string_ | Message contains the latest reconciliation detail or error. |  |  |
| `sourceClusterUUID` _string_ | SourceClusterUUID is the resolved UUID of the source cluster. |  |  |
| `targetClusterUUID` _string_ | TargetClusterUUID is the resolved UUID of the target cluster. |  |  |
| `importedBackupID` _string_ | ImportedBackupID is the backup UUID after successful import into the target cluster. |  |  |
| `storageBackupRef` _string_ | StorageBackupRef is the name of the StorageBackup CR created in the target namespace<br />after a successful import. This CR can be referenced directly in a BackupRestore. |  |  |
| `completedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | CompletedAt is when the import completed. |  |  |


#### BackupPolicy



BackupPolicy is the Schema for the backuppolicies API.

A BackupPolicy defines retention and scheduling parameters for simplyblock
backups. To apply a policy to a PVC, annotate the PVC with:

	simplyblock.io/backup-policy: <BackupPolicy-name>

The deprecated simplybk/backup-policy annotation is still honoured for
backwards compatibility; when both are set, simplyblock.io/backup-policy
takes precedence.

The BackupPolicy must be in the same namespace as the annotated PVC.
The controller attaches and detaches the policy in the simplyblock backend
whenever the annotation is added or removed.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha1
kind: BackupPolicy
metadata:
  name: string
spec:
  clusterName: string
  maxVersions: integer
  maxAge: '^[1-9]\d*[mhdw]$'
  schedule: '^(\d+[mhdw],\d+)( +\d+[mhdw],\d+)*$'
status:
  phase: string
  message: string
  clusterUUID: string
  policyID: string
  attachedLvols:
    - pvcName: string
      pvcNamespace: string
      lvolID: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha1` | | |
| `kind` _string_ | `BackupPolicy` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  | Optional: \{\} <br /> |
| `spec` _[BackupPolicySpec](#backuppolicyspec)_ | spec defines the desired state of BackupPolicy |  | Required: \{\} <br /> |
| `status` _[BackupPolicyStatus](#backuppolicystatus)_ | status defines the observed state of BackupPolicy |  | Optional: \{\} <br /> |


#### BackupPolicySpec



BackupPolicySpec defines the desired state of BackupPolicy.



_Appears in:_
- [BackupPolicy](#backuppolicy)

_Example:_

```yaml
clusterName: string
maxVersions: integer
maxAge: '^[1-9]\d*[mhdw]$'
schedule: '^(\d+[mhdw],\d+)( +\d+[mhdw],\d+)*$'
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `clusterName` _string_ | ClusterName is the target storage cluster name. |  |  |
| `maxVersions` _integer_ | MaxVersions is the maximum number of completed backup versions to retain.<br />When exceeded, the oldest backup is merged into the second-oldest. |  | Optional: \{\} <br /> |
| `maxAge` _string_ | MaxAge is the maximum age of backups to retain (e.g. "7d", "12h", "30m").<br />Backups older than this are merged. Accepts m, h, d, w suffixes. |  | Pattern: `^[1-9]\d*[mhdw]$` <br />Optional: \{\} <br /> |
| `schedule` _string_ | Schedule defines the tiered backup schedule as a space-separated list of<br />interval,keep_count pairs (e.g. "15m,4 60m,11 24h,7").<br />Intervals must be strictly increasing. Supported units: m, h, d, w. |  | Pattern: `^(\d+[mhdw],\d+)( +\d+[mhdw],\d+)*$` <br />Optional: \{\} <br /> |


#### BackupPolicyStatus



BackupPolicyStatus defines the observed state of BackupPolicy.



_Appears in:_
- [BackupPolicy](#backuppolicy)

_Example:_

```yaml
phase: string
message: string
clusterUUID: string
policyID: string
attachedLvols:
  - pvcName: string
    pvcNamespace: string
    lvolID: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _string_ | Phase is the high-level lifecycle state of the policy. |  |  |
| `message` _string_ | Message contains the latest reconciliation detail or error. |  |  |
| `clusterUUID` _string_ | ClusterUUID is the resolved backend cluster UUID. |  |  |
| `policyID` _string_ | PolicyID is the UUID assigned to this policy by the simplyblock backend. |  |  |
| `attachedLvols` _[AttachedLvol](#attachedlvol) array_ | AttachedLvols lists the PVCs (and their lvol IDs) currently attached to<br />this policy in the simplyblock backend. The controller uses this to detect<br />and reconcile annotation additions and removals. |  |  |


#### BackupRef



BackupRef identifies the StorageBackup to restore from, scoped to the same namespace.



_Appears in:_
- [BackupRestoreSpec](#backuprestorespec)

_Example:_

```yaml
name: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `name` _string_ | Name is the StorageBackup resource name. |  |  |


#### BackupRestore



BackupRestore is the Schema for the backuprestores API.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha1
kind: BackupRestore
metadata:
  name: string
spec:
  clusterName: string
  backupRef:
    name: string
  targetPool: string
  targetNode: string
  pvcTemplate:
    metadata:
      name: string
    spec: PersistentVolumeClaimSpec
status:
  phase: string
  message: string
  clusterUUID: string
  backupID: string
  sourceLvolID: string
  fsType: string
  poolName: string
  poolUUID: string
  restoredLvolID: string
  pvName: string
  pvcName: string
  pvcNamespace: string
  sourceClusterUUID: string
  startedAt: Time
  completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha1` | | |
| `kind` _string_ | `BackupRestore` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  | Optional: \{\} <br /> |
| `spec` _[BackupRestoreSpec](#backuprestorespec)_ | spec defines the desired state of BackupRestore |  | Required: \{\} <br /> |
| `status` _[BackupRestoreStatus](#backuprestorestatus)_ | status defines the observed state of BackupRestore |  | Optional: \{\} <br /> |


#### BackupRestoreSpec



BackupRestoreSpec defines the desired state of BackupRestore.



_Appears in:_
- [BackupRestore](#backuprestore)

_Example:_

```yaml
clusterName: string
backupRef:
  name: string
targetPool: string
targetNode: string
pvcTemplate:
  metadata:
    name: string
  spec: PersistentVolumeClaimSpec
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `clusterName` _string_ | ClusterName is the target storage cluster name. |  |  |
| `backupRef` _[BackupRef](#backupref)_ | BackupRef references the StorageBackup resource to restore from. |  |  |
| `targetPool` _string_ | TargetPool overrides the pool to restore into.<br />Defaults to the source backup's pool. |  | Optional: \{\} <br /> |
| `targetNode` _string_ | TargetNode is the UUID of the storage node to restore onto.<br />Defaults to the node that originally held the backup. |  | Optional: \{\} <br /> |
| `pvcTemplate` _[PVCTemplate](#pvctemplate)_ | PVCTemplate describes the PVC to create once the restore completes. |  |  |


#### BackupRestoreStatus



BackupRestoreStatus defines the observed state of BackupRestore.



_Appears in:_
- [BackupRestore](#backuprestore)

_Example:_

```yaml
phase: string
message: string
clusterUUID: string
backupID: string
sourceLvolID: string
fsType: string
poolName: string
poolUUID: string
restoredLvolID: string
pvName: string
pvcName: string
pvcNamespace: string
sourceClusterUUID: string
startedAt: Time
completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _string_ | Phase is the high-level lifecycle shown in kubectl output. |  |  |
| `message` _string_ | Message contains the latest reconciliation detail or error. |  |  |
| `clusterUUID` _string_ | ClusterUUID is the backend cluster UUID. |  |  |
| `backupID` _string_ | BackupID is the backend backup UUID being restored. |  |  |
| `sourceLvolID` _string_ | SourceLvolID is the original logical volume UUID that was backed up. |  |  |
| `fsType` _string_ | FSType is the filesystem type of the original source volume, copied from<br />the referenced StorageBackup's status.fsType. Set on the restored<br />PersistentVolume so it mounts with the same filesystem it was backed up<br />with, instead of the CSI driver's default. |  |  |
| `poolName` _string_ | PoolName is the pool the restore was issued against. |  |  |
| `poolUUID` _string_ | PoolUUID is the backend pool UUID. |  |  |
| `restoredLvolID` _string_ | RestoredLvolID is the UUID of the newly-created logical volume. |  |  |
| `pvName` _string_ | PVName is the name of the PersistentVolume created by the controller. |  |  |
| `pvcName` _string_ | PVCName is the name of the PersistentVolumeClaim created from pvcTemplate. |  |  |
| `pvcNamespace` _string_ | PVCNamespace is the namespace of the created PVC. |  |  |
| `sourceClusterUUID` _string_ | SourceClusterUUID is the UUID of the cluster that originally created the backup.<br />Copied from the referenced StorageBackup's status.sourceClusterUUID. When non-empty<br />and different from ClusterUUID, the controller resolves that cluster's backup<br />credentials and sends them with the restore request, since the backup's bucket may<br />not be this cluster's own. |  |  |
| `startedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | StartedAt is when the backend restore task was accepted. |  |  |
| `completedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | CompletedAt is when the PVC became bound. |  |  |


#### BackupSpec







_Appears in:_
- [StorageClusterSpec](#storageclusterspec)

_Example:_

```yaml
localEndpoint: '^https?://[a-zA-Z0-9.-]+(:[0-9]{1,5})?(/.*)?$'
snapshotBackups: boolean
withCompression: boolean
secondaryTarget: integer
localTesting: boolean
credentialsSecretRef:
  name: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `localEndpoint` _string_ |  |  | Pattern: `^https?://[a-zA-Z0-9.-]+(:[0-9]\{1,5\})?(/.*)?$` <br /> |
| `snapshotBackups` _boolean_ |  |  | Optional: \{\} <br /> |
| `withCompression` _boolean_ |  |  | Optional: \{\} <br /> |
| `secondaryTarget` _integer_ |  |  | Optional: \{\} <br /> |
| `localTesting` _boolean_ |  |  | Optional: \{\} <br /> |
| `credentialsSecretRef` _[BackupCredentialsSecretRef](#backupcredentialssecretref)_ | CredentialsSecretRef points to the Secret holding access_key_id and secret_access_key. |  |  |


#### BaselineColdStartPolicy

_Underlying type:_ _string_

BaselineColdStartPolicy selects what happens for a node that has fewer than
BaselineMinSamples samples in the rolling window (e.g., a freshly onboarded node, or
shortly after the probe sidecar starts).

_Validation:_
- Enum: [defer partialWindow]

_Appears in:_
- [VolumeAutoPlacementSettings](#volumeautoplacementsettings)

| Field | Description |
| --- | --- |
| `defer` | BaselineColdStartDefer omits an under-sampled node from the evaluation cycle: it is<br />neither a migration source nor a target until it has accumulated BaselineMinSamples<br />samples. Avoids acting on a noisy baseline.<br /> |
| `partialWindow` | BaselineColdStartPartialWindow computes the baseline from whatever samples exist,<br />accepting a noisier baseline early on so rebalancing engages sooner. This is the default.<br /> |


#### BaselineStrategy

_Underlying type:_ _string_

BaselineStrategy selects how the per-node latency baseline (the denominator of the
rebalancing deviation signal) is derived.

_Validation:_
- Enum: [benchmark rollingWindow]

_Appears in:_
- [VolumeAutoPlacementSettings](#volumeautoplacementsettings)

| Field | Description |
| --- | --- |
| `benchmark` | BaselineStrategyBenchmark uses the one-shot fio measurement taken by the baseline<br />Job on a fresh cluster and frozen on the StorageNode CR status. Simple but tends to<br />read too low, because an idle cluster is far faster than a loaded one — every loaded<br />node then shows a large deviation.<br /> |
| `rollingWindow` | BaselineStrategyRollingWindow derives the baseline from a rolling window of the<br />probe-sidecar latency series in Prometheus, using a robust outlier-rejecting<br />estimator. Reflects each node's actual recent operating latency rather than an idle<br />measurement. This is the default.<br /> |


#### CapacityThresholdSpec







_Appears in:_
- [StorageClusterSpec](#storageclusterspec)

_Example:_

```yaml
capacity: integer
provisionedCapacity: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `capacity` _integer_ | Capacity defines the absolute capacity threshold value. |  |  |
| `provisionedCapacity` _integer_ | ProvisionedCapacity defines the provisioned-capacity threshold value. |  |  |


#### ControlPlane



ControlPlane is a singleton resource (one per namespace, named "simplyblock")
that reflects the readiness of the simplyblock control plane. It is created
automatically by the Helm chart and should not be created or deleted manually.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha1
kind: ControlPlane
metadata:
  name: string
spec:
  image: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
status:
  phase: string
  message: string
  lastChecked: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha1` | | |
| `kind` _string_ | `ControlPlane` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  | Optional: \{\} <br /> |
| `spec` _[ControlPlaneSpec](#controlplanespec)_ |  |  | Optional: \{\} <br /> |
| `status` _[ControlPlaneStatus](#controlplanestatus)_ |  |  | Optional: \{\} <br /> |


#### ControlPlaneSpec



ControlPlaneSpec holds configuration for the singleton ControlPlane resource
created by the Helm chart.



_Appears in:_
- [ControlPlane](#controlplane)

_Example:_

```yaml
image: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `image` _string_ | Image is the container image used for all simplyblock control-plane and<br />storage-node workloads (e.g., `quay.io/simplyblock-io/simplyblock:26.2.2`).<br />StorageNodeSet CRs that omit spec.clusterImage inherit this value.<br />Must reference one of the trusted registries (`quay.io/simplyblock-io`,<br />`docker.io/simplyblock`, `public.ecr.aws/simply-block`). Digest pinning<br />(@sha256:...) is recommended. |  | Pattern: `^($\|(quay\.io/simplyblock-io\|docker\.io/simplyblock\|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]\{64\})?)$` <br />Optional: \{\} <br /> |


#### ControlPlaneStatus



ControlPlaneStatus reflects the observed readiness of the simplyblock
control plane (FDB + management API).



_Appears in:_
- [ControlPlane](#controlplane)

_Example:_

```yaml
phase: string
message: string
lastChecked: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _string_ | Phase is Initializing while the control plane is not yet healthy,<br />and Ready once the FDB health check passes. |  | Enum: [Initializing Ready] <br /> |
| `message` _string_ | Message contains a human-readable explanation of the current phase,<br />for example, the FDB error returned by the health endpoint. |  |  |
| `lastChecked` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | LastChecked is the timestamp of the most recent FDB health probe. |  |  |


#### DataRealignmentSettings



DataRealignmentSettings controls the periodic, post-migration control-plane data
realignment. After one or more volumes have been moved the operator asks the
control plane to re-align its internal data structures to the new placement,
restoring fault-tolerance (FTT) and node-affinity guarantees.



_Appears in:_
- [VolumeMigrationSettings](#volumemigrationsettings)

_Example:_

```yaml
enabled: boolean
interval: Duration
minMoves: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `enabled` _boolean_ | Enabled activates automatic post-migration data realignment for this cluster.<br />Defaults to true. |  | Optional: \{\} <br /> |
| `interval` _[Duration](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#duration-v1-meta)_ | Interval is how often the operator checks whether a realignment is pending<br />(i.e., at least one volume has moved since the last successful realignment) and,<br />if so, triggers it. Explicit triggers (see the<br />simplyblock.io/trigger-realignment annotation) bypass this spacing. Defaults to<br />10m.<br />Note that this is a floor on the spacing between realignment *requests*, not a<br />ceiling on how long one takes: a realignment blocks all volume migrations for as<br />long as the control plane needs, which on a busy cluster has been measured at<br />tens of minutes. An interval shorter than that means the next realignment is<br />requested as soon as the previous one finishes and any volume has moved, which is<br />what MinMoves exists to damp. |  | Optional: \{\} <br /> |
| `minMoves` _integer_ | MinMoves is how many volume moves must accumulate before a realignment is<br />triggered. Defaults to 1: every completed migration schedules a realignment.<br />Raise it to batch. Because the control plane refuses new migrations while a<br />realignment runs, a value of 1 makes the two alternate — one migration completes,<br />a realignment follows and blocks migrations until it is done. On a cluster where<br />realignment takes tens of minutes that is most of the available time, so a run<br />that migrates continuously spends the majority of it waiting. A higher value<br />trades realignment promptness (data structures stay unaligned for longer, so<br />fault-tolerance and node-affinity guarantees are restored later) for migration<br />throughput.<br />Explicit triggers (the simplyblock.io/trigger-realignment annotation) ignore this<br />threshold, so a drain or node removal still realigns immediately. |  | Minimum: 1 <br />Optional: \{\} <br /> |


#### DrainOpsSpec



DrainOpsSpec configures the drain workflow for action=remove.



_Appears in:_
- [StorageNodeOpsSpec](#storagenodeopsspec)

_Example:_

```yaml
systemVolumeFilterRegex: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `systemVolumeFilterRegex` _string_ | SystemVolumeFilterRegex is a Go regular expression matched against backend<br />volume names. Matching volumes are treated as system volumes: excluded from<br />drain migration and deleted inline during the Verifying phase.<br />Defaults to "^sb-fio-baseline-.*". |  | Optional: \{\} <br /> |


#### HashicorpVaultSettings



HashicorpVaultSettings configures the HashiCorp Vault endpoint the cluster uses to store keys.



_Appears in:_
- [StorageClusterSpec](#storageclusterspec)

_Example:_

```yaml
baseURL: '^https?://[a-zA-Z0-9.-]+(:[0-9]{1,5})?(/.*)?$'
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `baseURL` _string_ | BaseURL is the HashiCorp Vault endpoint (e.g., https://vault.example.com:8200). |  | Pattern: `^https?://[a-zA-Z0-9.-]+(:[0-9]\{1,5\})?(/.*)?$` <br /> |


#### JournalManagerSpec



JournalManagerSpec defines journal manager tuning parameters.



_Appears in:_
- [StorageNodeOverrides](#storagenodeoverrides)
- [StorageNodeSetSpec](#storagenodesetspec)

_Example:_

```yaml
count: integer
percentPerDevice: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `count` _integer_ | Count is the number of journal managers to configure. |  |  |
| `percentPerDevice` _integer_ | PercentPerDevice is the journal manager capacity percentage per device. |  |  |


#### MetricsBackend

_Underlying type:_ _string_

MetricsBackend selects the NodeMetricsProvider implementation.

_Validation:_
- Enum: [controlplane prometheus uniform]

_Appears in:_
- [VolumeAutoPlacementSettings](#volumeautoplacementsettings)

| Field | Description |
| --- | --- |
| `controlplane` |  |
| `prometheus` |  |
| `uniform` | MetricsBackendUniform returns IOPS=1 for every node, disabling<br />IOPS-based scoring while keeping capacity/volume-count balancing active.<br /> |


#### MigrationConnection



MigrationConnection holds the NVMe-oF connection parameters for one path
on the migration target node, as returned by the storage API's CreateMigration.
All fields are passed verbatim to `nvme connect` in the validation Job.



_Appears in:_
- [VolumeMigrationStatus](#volumemigrationstatus)

_Example:_

```yaml
nqn: string
ip: string
port: integer
transport: string
nrIoQueues: integer
reconnectDelay: integer
ctrlLossTmo: integer
fastIOFailTmo: integer
keepAliveTmo: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `nqn` _string_ |  |  |  |
| `ip` _string_ |  |  |  |
| `port` _integer_ |  |  |  |
| `transport` _string_ |  |  |  |
| `nrIoQueues` _integer_ |  |  |  |
| `reconnectDelay` _integer_ |  |  |  |
| `ctrlLossTmo` _integer_ |  |  |  |
| `fastIOFailTmo` _integer_ |  |  |  |
| `keepAliveTmo` _integer_ |  |  |  |


#### NodeDrainState



NodeDrainState tracks the upgrade-drain coordination state for a single worker node.



_Appears in:_
- [StorageNodeSetStatus](#storagenodesetstatus)

_Example:_

```yaml
hostname: string
phase: string
startedAt: Time
message: string
activeNodeUUID: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `hostname` _string_ | Hostname is the Kubernetes node name. |  |  |
| `phase` _string_ | Phase is the current drain coordination phase. |  | Enum: [detected shutdown_called draining restart_called complete failed] <br /> |
| `startedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | StartedAt is when drain coordination began for this node. |  |  |
| `message` _string_ | Message provides additional status detail or error information. |  |  |
| `activeNodeUUID` _string_ | ActiveNodeUUID is the backend UUID of the storage node currently being shut<br />down or restarted. Used to sequence through multiple NUMA-socket nodes on<br />the same worker one at a time during drain coordination. |  |  |


#### NodeLatencyMetrics



NodeLatencyMetrics holds fio-measured 4K NVMe-oF latency for a single backend storage node.
The benchmark volume NQN and connection details are derived at runtime from the node UUID
and the cluster NQN — they are not stored here.



_Appears in:_
- [StorageNodeSetStatus](#storagenodesetstatus)
- [StorageNodeStatus](#storagenodestatus)

_Example:_

```yaml
nodeUUID: string
baselineP50NS: integer
baselineP99NS: integer
baselineMeasuredAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `nodeUUID` _string_ | NodeUUID is the backend storage node UUID. |  |  |
| `baselineP50NS` _integer_ | BaselineP50NS is the p50 write latency (nanoseconds) from the initial empty-cluster benchmark. |  |  |
| `baselineP99NS` _integer_ | BaselineP99NS is the p99 write latency (nanoseconds) from the initial empty-cluster benchmark. |  |  |
| `baselineMeasuredAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | BaselineMeasuredAt is when the baseline was established. |  |  |


#### NodeLoadMetrics



NodeLoadMetrics holds the latency deviation state for a single storage node.



_Appears in:_
- [RebalancingMetrics](#rebalancingmetrics)

_Example:_

```yaml
nodeUUID: string
latencyDeviationPct: float
volumeCount: integer
lastUpdated: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `nodeUUID` _string_ |  |  |  |
| `latencyDeviationPct` _float_ |  |  |  |
| `volumeCount` _integer_ |  |  |  |
| `lastUpdated` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ |  |  |  |


#### NodeRollingRestartSpec



NodeRollingRestartSpec configures the node-rolling-restart action behaviour.



_Appears in:_
- [StorageClusterOpsSpec](#storageclusteropsspec)

_Example:_

```yaml
refreshSNodeAPI: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `refreshSNodeAPI` _boolean_ | RefreshSNodeAPI restarts the storage-node DaemonSet pod on each node<br />after the backend node is shut down and before it is restarted, ensuring<br />the latest image is running before the node comes back online. |  | Optional: \{\} <br /> |


#### NodeRollingRestartStatus



NodeRollingRestartStatus tracks in-progress state for the node-rolling-restart action.
All fields are persisted in the StorageClusterOps status so the reconciler
can resume after a requeue or operator restart.



_Appears in:_
- [StorageClusterOpsStatus](#storageclusteropsstatus)

_Example:_

```yaml
pendingNodes:
  - string
processedNodes:
  - string
nodePhase: string
phaseTriggered: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `pendingNodes` _string array_ | PendingNodes is the ordered list of node UUIDs still to be restarted. |  |  |
| `processedNodes` _string array_ | ProcessedNodes is the list of node UUIDs already restarted. |  |  |
| `nodePhase` _string_ | NodePhase is the current step for the node being restarted:<br />"snode-refresh" \| "snode-refresh-wait" \| "shutting-down" \| "restarting" \| "rebalancing" |  |  |
| `phaseTriggered` _boolean_ | PhaseTriggered indicates the API call for the current NodePhase was already sent. |  |  |


#### NodeStatus







_Appears in:_
- [StorageNodeSetStatus](#storagenodesetstatus)

_Example:_

```yaml
uuid: string
health: boolean
status: string
cpu: integer
memory: string
volumes: integer
rpcPort: integer
lvolPort: integer
nvmfPort: integer
devices: string
uptime: string
hostname: string
mgmtIp: string
postedAt: Time
failureDomain: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `uuid` _string_ | UUID is the backend node UUID. |  |  |
| `health` _boolean_ | Health indicates whether health checks are currently passing. |  |  |
| `status` _string_ | Status is the backend lifecycle state for the node. |  |  |
| `cpu` _integer_ | CPU is the reported CPU allocation/count for the node. |  |  |
| `memory` _string_ | Memory is the reported memory value. |  |  |
| `volumes` _integer_ | Volumes is the current logical volume count. |  |  |
| `rpcPort` _integer_ | RpcPort is the node RPC service port. |  |  |
| `lvolPort` _integer_ | LvolPort is the logical-volume subsystem port. |  |  |
| `nvmfPort` _integer_ | NvmfPort is the NVMf service port. |  |  |
| `devices` _string_ | Devices is the backend summary of devices on this node. |  |  |
| `uptime` _string_ | Uptime is the reported node uptime value. |  |  |
| `hostname` _string_ | Hostname is the Kubernetes node hostname. |  |  |
| `mgmtIp` _string_ | MgmtIp is the management IP address for the node. |  |  |
| `postedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | PostedAt is when the storage-node add request was sent. Used to detect<br />timeout without blocking the reconcile goroutine. |  |  |
| `failureDomain` _integer_ | FailureDomain is the effective failure-domain group index for this node,<br />reflected from spec.nodeConfigs[hostname].failureDomain or spec.nodeFailureDomains[hostname].<br />Zero means unset. |  | Optional: \{\} <br /> |


#### PVCTemplate



PVCTemplate describes the PVC the controller will create once the restore completes.



_Appears in:_
- [BackupRestoreSpec](#backuprestorespec)

_Example:_

```yaml
metadata:
  name: string
spec: PersistentVolumeClaimSpec
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `metadata` _[PVCTemplateMetadata](#pvctemplatemetadata)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  | Optional: \{\} <br /> |
| `spec` _[PersistentVolumeClaimSpec](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#persistentvolumeclaimspec-v1-core)_ | Spec follows core PersistentVolumeClaimSpec.<br />spec.resources.requests.storage must be >= the backup size. |  |  |


#### PVCTemplateMetadata



PVCTemplateMetadata describes the PVC metadata fields the controller honors.



_Appears in:_
- [PVCTemplate](#pvctemplate)

_Example:_

```yaml
name: string
labels:
  string: string
annotations:
  string: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `name` _string_ |  |  | Optional: \{\} <br /> |
| `labels` _object (keys:string, values:string)_ |  |  | Optional: \{\} <br /> |
| `annotations` _object (keys:string, values:string)_ |  |  | Optional: \{\} <br /> |


#### PersistentVolumeClaimRef







_Appears in:_
- [StorageBackupSpec](#storagebackupspec)

_Example:_

```yaml
name: string
namespace: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `name` _string_ | Name is the PVC name. |  |  |
| `namespace` _string_ | Namespace overrides the backup resource namespace for the PVC lookup. |  |  |


#### RebalancingMetrics



RebalancingMetrics is written by the VolumeRebalancerReconciler each evaluation cycle.



_Appears in:_
- [StorageClusterStatus](#storageclusterstatus)

_Example:_

```yaml
avgDeviationPct: float
maxDeviationPct: float
hottestNodeUUID: string
coolestNodeUUID: string
imbalancePercent: float
lastEvaluatedAt: Time
lastMigrationAt: Time
nodeMetrics:
  - nodeUUID: string
    latencyDeviationPct: float
    volumeCount: integer
    lastUpdated: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `avgDeviationPct` _float_ | AvgDeviationPct is the mean latency deviation across all nodes. |  |  |
| `maxDeviationPct` _float_ | MaxDeviationPct is the highest per-node latency deviation (used as ImbalancePercent). |  |  |
| `hottestNodeUUID` _string_ |  |  |  |
| `coolestNodeUUID` _string_ |  |  |  |
| `imbalancePercent` _float_ |  |  |  |
| `lastEvaluatedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ |  |  |  |
| `lastMigrationAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ |  |  |  |
| `nodeMetrics` _[NodeLoadMetrics](#nodeloadmetrics) array_ |  |  |  |


#### ReplicationOps



ReplicationOps is a one-shot user-driven CR for imperative replication operations:
failover (planned or unplanned) and failback. The operator drives the backend calls
to completion and records per-volume outcomes in status.results. Only one ReplicationOps
may be active per ReplicationPolicy at a time, enforced via ReplicationPolicy.status.activeOpsRef.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha1
kind: ReplicationOps
metadata:
  name: string
spec:
  action: string
  scope: string
  ref: string
  sourceClusterID: string
  deleteSource: boolean
status:
  phase: string
  subphase: string
  message: string
  startedAt: Time
  completedAt: Time
  results:
    - slotRef: string
      status: string
      detail: string
      targetLvolID: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha1` | | |
| `kind` _string_ | `ReplicationOps` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  |  |
| `spec` _[ReplicationOpsSpec](#replicationopsspec)_ |  |  |  |
| `status` _[ReplicationOpsStatus](#replicationopsstatus)_ |  |  |  |




#### ReplicationOpsResult



ReplicationOpsResult holds the outcome for a single volume in a ReplicationOps.



_Appears in:_
- [ReplicationOpsStatus](#replicationopsstatus)

_Example:_

```yaml
slotRef: string
status: string
detail: string
targetLvolID: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `slotRef` _string_ | SlotRef is the name of the ReplicationSlot CR. |  |  |
| `status` _string_ | Status is the outcome for this volume. |  | Enum: [succeeded skipped failed] <br /> |
| `detail` _string_ | Detail is an optional human-readable note (error message or skip reason). |  | Optional: \{\} <br /> |
| `targetLvolID` _string_ | TargetLvolID is the UUID of the volume on the target cluster (failover only). |  | Optional: \{\} <br /> |




#### ReplicationOpsSpec



ReplicationOpsSpec defines the desired state of a ReplicationOps.



_Appears in:_
- [ReplicationOps](#replicationops)

_Example:_

```yaml
action: string
scope: string
ref: string
sourceClusterID: string
deleteSource: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `action` _string_ | Action is the operation to perform. Immutable.<br />failover:  unplanned — promote target clone, source may be down.<br />failback:  restore source as primary after a prior failover.<br />migration: planned cutover — calls replication_commit per volume; both clusters stay up.<br />           State progression: replicating → cutover_pending → cutover_done. |  | Enum: [failover failback migration] <br />Required: \{\} <br /> |
| `scope` _string_ | Scope controls which volumes are affected. Immutable.<br />target: all volumes across every policy that uses the named ReplicationPair.<br />policy: all volumes managed by the named ReplicationPolicy CR.<br />volume: a single ReplicationSlot (planned or unplanned per-volume operation). |  | Enum: [target policy volume] <br />Required: \{\} <br /> |
| `ref` _string_ | Ref is the name of the resource identified by Scope:<br />a ReplicationPair name for scope=target,<br />a ReplicationPolicy name for scope=policy,<br />or a ReplicationSlot name for scope=volume. Immutable. |  | Required: \{\} <br /> |
| `sourceClusterID` _string_ | SourceClusterID is used for failback only. Omit to recover to the original source. |  | Optional: \{\} <br /> |
| `deleteSource` _boolean_ | DeleteSource instructs the backend to delete the old volume after a<br />successful cutover. For migration it deletes the original source volume;<br />for failback it deletes the failed-over volume on the target cluster. |  | Optional: \{\} <br /> |


#### ReplicationOpsStatus



ReplicationOpsStatus holds the observed state of a ReplicationOps.



_Appears in:_
- [ReplicationOps](#replicationops)

_Example:_

```yaml
phase: string
subphase: string
message: string
startedAt: Time
completedAt: Time
results:
  - slotRef: string
    status: string
    detail: string
    targetLvolID: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _string_ | Phase is the current lifecycle phase of this operation. |  | Enum: [Pending Running Succeeded Failed] <br />Optional: \{\} <br /> |
| `subphase` _string_ | Subphase describes what the operation is currently doing within the phase<br />(e.g. "TriggeringFailover", "UpdatingSlotStatuses", "ReleasingLock"). |  | Optional: \{\} <br /> |
| `message` _string_ | Message is a human-readable description of the current phase. |  | Optional: \{\} <br /> |
| `startedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | StartedAt is when the operation began. |  | Optional: \{\} <br /> |
| `completedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | CompletedAt is when the operation finished (successfully or not). |  | Optional: \{\} <br /> |
| `results` _[ReplicationOpsResult](#replicationopsresult) array_ | Results holds a per-volume summary of the operation outcome. |  | Optional: \{\} <br /> |


#### ReplicationPair



ReplicationPair defines the source and target clusters for a replication relationship.
It is reusable configuration — multiple ReplicationPolicies may reference the same pair
to replicate volumes between the same two clusters with different schedules or retention.
The operator ensures the corresponding backend ReplicationTarget exists and stores its ID
in status.backendTargetID for use by ReplicationPolicy resources.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha1
kind: ReplicationPair
metadata:
  name: string
spec:
  sourceCluster: string
  targetCluster: string
status:
  ready: boolean
  backendTargetID: string
  message: string
  conditions:
    - Condition
  activeOpsRef: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha1` | | |
| `kind` _string_ | `ReplicationPair` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  |  |
| `spec` _[ReplicationPairSpec](#replicationpairspec)_ |  |  |  |
| `status` _[ReplicationPairStatus](#replicationpairstatus)_ |  |  |  |


#### ReplicationPairSpec



ReplicationPairSpec defines the source and target clusters for a replication relationship.



_Appears in:_
- [ReplicationPair](#replicationpair)

_Example:_

```yaml
sourceCluster: string
targetCluster: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `sourceCluster` _string_ | SourceCluster is the name of the local StorageCluster (the replication source). |  | Required: \{\} <br /> |
| `targetCluster` _string_ | TargetCluster is the name or UUID of the remote cluster (the replication target).<br />Immutable after creation. |  | Required: \{\} <br /> |


#### ReplicationPairStatus



ReplicationPairStatus holds the observed state of a ReplicationPair.



_Appears in:_
- [ReplicationPair](#replicationpair)

_Example:_

```yaml
ready: boolean
backendTargetID: string
message: string
conditions:
  - Condition
activeOpsRef: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `ready` _boolean_ | Ready is true when the backend ReplicationTarget has been created and is available. |  | Optional: \{\} <br /> |
| `backendTargetID` _string_ | BackendTargetID is the UUID of the backend ReplicationTarget resource. |  | Optional: \{\} <br /> |
| `message` _string_ | Message provides a human-readable description of the current state. |  | Optional: \{\} <br /> |
| `conditions` _[Condition](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#condition-v1-meta) array_ | Conditions holds standard Kubernetes condition types. |  | Optional: \{\} <br /> |
| `activeOpsRef` _string_ | ActiveOpsRef is the name of the ReplicationOps currently holding the<br />target-scope lock on this pair. Only one scope=target ReplicationOps may<br />be active per pair at a time. |  | Optional: \{\} <br /> |


#### ReplicationPolicy



ReplicationPolicy defines the replication schedule and retention for volumes replicated
between the clusters defined by a ReplicationPair.
A StorageClass or PVC references a policy via the storage.simplyblock.io/replication-policy
annotation. The operator automatically creates one ReplicationSlot per bound PVC.
Deletion is blocked while any ReplicationSlots reference this policy.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha1
kind: ReplicationPolicy
metadata:
  name: string
spec:
  pairRef: string
  mode: string
  interval: string
  snapshotRetention: integer
status:
  ready: boolean
  backendPolicyID: string
  slotCount: integer
  activeOpsRef: string
  conditions:
    - Condition
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha1` | | |
| `kind` _string_ | `ReplicationPolicy` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  |  |
| `spec` _[ReplicationPolicySpec](#replicationpolicyspec)_ |  |  |  |
| `status` _[ReplicationPolicyStatus](#replicationpolicystatus)_ |  |  |  |


#### ReplicationPolicySpec



ReplicationPolicySpec defines the desired replication schedule and retention.



_Appears in:_
- [ReplicationPolicy](#replicationpolicy)

_Example:_

```yaml
pairRef: string
mode: string
interval: string
snapshotRetention: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `pairRef` _string_ | PairRef is the name of the ReplicationPair that defines the source and target clusters.<br />Multiple ReplicationPolicies may reference the same pair with different schedules. |  | Required: \{\} <br /> |
| `mode` _string_ | Mode controls replication semantics.<br />failover: target is a DR standby; volumes are read-only on the target.<br />migration: planned online cutover to the target cluster. | failover | Enum: [failover migration] <br />Optional: \{\} <br /> |
| `interval` _string_ | Interval is how often a replication snapshot is taken (e.g. "5m", "1h"). | 5m | Optional: \{\} <br /> |
| `snapshotRetention` _integer_ | SnapshotRetention is the minimum number of snapshots to retain on the target. | 3 | Minimum: 2 <br />Optional: \{\} <br /> |


#### ReplicationPolicyStatus



ReplicationPolicyStatus holds the observed state of a ReplicationPolicy.



_Appears in:_
- [ReplicationPolicy](#replicationpolicy)

_Example:_

```yaml
ready: boolean
backendPolicyID: string
slotCount: integer
activeOpsRef: string
conditions:
  - Condition
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `ready` _boolean_ | Ready is true when the backend ReplicationPolicy has been created. |  | Optional: \{\} <br /> |
| `backendPolicyID` _string_ | BackendPolicyID is the UUID of the backend ReplicationPolicy resource. |  | Optional: \{\} <br /> |
| `slotCount` _integer_ | SlotCount is the number of ReplicationSlot CRs currently managed by this policy. |  | Optional: \{\} <br /> |
| `activeOpsRef` _string_ | ActiveOpsRef is the name of the currently running ReplicationOps CR.<br />Empty when no operation is in progress. |  | Optional: \{\} <br /> |
| `conditions` _[Condition](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#condition-v1-meta) array_ | Conditions holds standard Kubernetes condition types. |  | Optional: \{\} <br /> |


#### ReplicationSlot



ReplicationSlot tracks the live replication state for a single PVC.
One ReplicationSlot is created per PVC by the PVCAnnotationWatcher controller when
a PVC references a ReplicationPolicy via annotation. It is owned by its PVC, so
deleting the PVC cascades deletion and triggers a backend detach via the slot finalizer.
The ReplicationSlot reconciler drives all backend calls: attach, monitor, cutover,
failover, and detach.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha1
kind: ReplicationSlot
metadata:
  name: string
spec:
  policyRef: string
  pvcRef: string
  volumeID: string
status:
  state: string
  direction: string
  sourceLvolID: string
  targetLvolID: string
  targetNQN: string
  lastReplicatedAt: Time
  message: string
  conditions:
    - Condition
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha1` | | |
| `kind` _string_ | `ReplicationSlot` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  |  |
| `spec` _[ReplicationSlotSpec](#replicationslotspec)_ |  |  |  |
| `status` _[ReplicationSlotStatus](#replicationslotstatus)_ |  |  |  |




#### ReplicationSlotSpec



ReplicationSlotSpec defines the identity of a per-volume replication slot.



_Appears in:_
- [ReplicationSlot](#replicationslot)

_Example:_

```yaml
policyRef: string
pvcRef: string
volumeID: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `policyRef` _string_ | PolicyRef is the name of the ReplicationPolicy governing this slot. Immutable. |  | Required: \{\} <br /> |
| `pvcRef` _string_ | PVCRef is the name of the PVC being replicated. Immutable. |  | Required: \{\} <br /> |
| `volumeID` _string_ | VolumeID is the backend lvol UUID of the source volume. Immutable.<br />Format: "<clusterUUID>:<poolUUID>:<volumeUUID>" |  | Required: \{\} <br /> |




#### ReplicationSlotStatus



ReplicationSlotStatus holds the observed state of a ReplicationSlot.



_Appears in:_
- [ReplicationSlot](#replicationslot)

_Example:_

```yaml
state: string
direction: string
sourceLvolID: string
targetLvolID: string
targetNQN: string
lastReplicatedAt: Time
message: string
conditions:
  - Condition
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `state` _string_ | State is the current replication state for this slot. |  | Enum: [attaching replicating cutover_pending cutover_done failed_over detaching error] <br />Optional: \{\} <br /> |
| `direction` _string_ | Direction is which side of the replication relationship this cluster holds. |  | Enum: [source target] <br />Optional: \{\} <br /> |
| `sourceLvolID` _string_ | SourceLvolID is the UUID of the source volume on the source cluster. |  | Optional: \{\} <br /> |
| `targetLvolID` _string_ | TargetLvolID is the UUID of the replicated volume on the target cluster. |  | Optional: \{\} <br /> |
| `targetNQN` _string_ | TargetNQN is the NVMe NQN on the target cluster (populated after failover). |  | Optional: \{\} <br /> |
| `lastReplicatedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | LastReplicatedAt is the timestamp of the last successful replication snapshot. |  | Optional: \{\} <br /> |
| `message` _string_ | Message provides a human-readable description of the current state. |  | Optional: \{\} <br /> |
| `conditions` _[Condition](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#condition-v1-meta) array_ | Conditions holds standard Kubernetes condition types. |  | Optional: \{\} <br /> |


#### StorageBackup



StorageBackup is the Schema for the storagebackups API.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageBackup
metadata:
  name: string
spec:
  clusterName: string
  pvcRef:
    name: string
    namespace: string
  snapshotName: string
  sourceClusterUUID: string
status:
  phase: string
  apiStatus: string
  message: string
  clusterUUID: string
  pvcNamespace: string
  pvName: string
  poolName: string
  poolUUID: string
  lvolID: string
  lvolName: string
  fsType: string
  snapshotID: string
  snapshotName: string
  sourceClusterUUID: string
  backupID: string
  s3ID: integer
  nodeID: string
  prevBackupID: string
  size: integer
  allowedHosts:
    - 'map[string]string'
  createdAt: Time
  completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha1` | | |
| `kind` _string_ | `StorageBackup` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  | Optional: \{\} <br /> |
| `spec` _[StorageBackupSpec](#storagebackupspec)_ | spec defines the desired state of StorageBackup |  | Required: \{\} <br /> |
| `status` _[StorageBackupStatus](#storagebackupstatus)_ | status defines the observed state of StorageBackup |  | Optional: \{\} <br /> |


#### StorageBackupSpec



StorageBackupSpec defines the desired state of StorageBackup.



_Appears in:_
- [StorageBackup](#storagebackup)

_Example:_

```yaml
clusterName: string
pvcRef:
  name: string
  namespace: string
snapshotName: string
sourceClusterUUID: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `clusterName` _string_ | ClusterName is the target storage cluster name. |  |  |
| `pvcRef` _[PersistentVolumeClaimRef](#persistentvolumeclaimref)_ | PVCRef identifies the PVC whose backing simplyblock volume should be snapshotted and backed up.<br />Not required when SourceClusterUUID is set (imported backup). |  | Optional: \{\} <br /> |
| `snapshotName` _string_ | SnapshotName optionally overrides the snapshot name the operator would otherwise choose. |  | Optional: \{\} <br /> |
| `sourceClusterUUID` _string_ | SourceClusterUUID, when non-empty, marks this StorageBackup as imported from another cluster.<br />The StorageBackup controller will not create snapshots or backups for imported resources.<br />Set by the BackupImport controller; do not set manually. |  | Optional: \{\} <br /> |


#### StorageBackupStatus



StorageBackupStatus defines the observed state of StorageBackup.



_Appears in:_
- [StorageBackup](#storagebackup)

_Example:_

```yaml
phase: string
apiStatus: string
message: string
clusterUUID: string
pvcNamespace: string
pvName: string
poolName: string
poolUUID: string
lvolID: string
lvolName: string
fsType: string
snapshotID: string
snapshotName: string
sourceClusterUUID: string
backupID: string
s3ID: integer
nodeID: string
prevBackupID: string
size: integer
allowedHosts:
  - 'map[string]string'
createdAt: Time
completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _string_ | Phase is the high-level backup lifecycle shown in kubectl output. |  |  |
| `apiStatus` _string_ | APIStatus is the raw status returned by the backup API. |  |  |
| `message` _string_ | Message contains the latest reconciliation detail or error. |  |  |
| `clusterUUID` _string_ | ClusterUUID is the backend cluster UUID. |  |  |
| `pvcNamespace` _string_ | PVCNamespace is the resolved PVC namespace. |  |  |
| `pvName` _string_ | PVName is the bound PV name. |  |  |
| `poolName` _string_ | PoolName is the simplyblock pool name derived from the CSI volume handle. |  |  |
| `poolUUID` _string_ | PoolUUID is the backend pool UUID. |  |  |
| `lvolID` _string_ | LvolID is the simplyblock volume UUID. |  |  |
| `lvolName` _string_ | LvolName is the backend logical volume name. |  |  |
| `fsType` _string_ | FSType is the filesystem type of the source PersistentVolume ("ext4," "XFS"),<br />captured at backup time so a restore can preserve it regardless of<br />which StorageClass the restored PVC ends up using. |  |  |
| `snapshotID` _string_ | SnapshotID is the UUID of the snapshot the operator created used for the backup request. |  |  |
| `snapshotName` _string_ | SnapshotName is the snapshot name used for the backup request. |  |  |
| `sourceClusterUUID` _string_ | SourceClusterUUID is set for imported backups; identifies the cluster that originally<br />created the backup. When non-empty and different from the restore target cluster UUID,<br />BackupRestore will automatically perform source-switch operations around the restore. |  |  |
| `backupID` _string_ | BackupID is the backend backup UUID. |  |  |
| `s3ID` _integer_ | S3ID is the backend S3 object identifier. |  |  |
| `nodeID` _string_ | NodeID is the source storage node UUID. |  |  |
| `prevBackupID` _string_ | PrevBackupID links the previous backup in the chain. |  |  |
| `size` _integer_ | Size is the backup size in bytes. |  |  |
| `allowedHosts` _object array_ | AllowedHosts contains the allowed host metadata returned by the backup API. |  |  |
| `createdAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | CreatedAt is when the backup was created. |  |  |
| `completedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | CompletedAt is when the backup completed. |  |  |


#### StorageClassParameters



StorageClassParameters defines the default StorageClass parameter values for volumes in this pool.
These are passed as-is to the CSI driver when the StorageClass is created.
cluster_id and pool_name are always set automatically and cannot be overridden here.

IMPORTANT: StorageClass Parameters are immutable in the Kubernetes API, so this whole field
is immutable once set (see StoragePoolSpec.StorageClassParameters) — there's no supported way
to change a pool's StorageClass defaults after the pool is created. Create a new StoragePool
instead.



_Appears in:_
- [StoragePoolSpec](#storagepoolspec)

_Example:_

```yaml
qosRwIops: string
qosRwMbytes: string
qosRMbytes: string
qosWMbytes: string
encryption: boolean
fabric: string
maxNamespacePerSubsys: string
tune2fsReservedBlocks: string
filesystem: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `qosRwIops` _string_ | QosRwIops sets the read/write IOPS limit (0 = unlimited). | 0 |  |
| `qosRwMbytes` _string_ | QosRwMbytes sets the read/write throughput limit in MB/s (0 = unlimited). | 0 |  |
| `qosRMbytes` _string_ | QosRMbytes sets the read throughput limit in MB/s (0 = unlimited). | 0 |  |
| `qosWMbytes` _string_ | QosWMbytes sets the write throughput limit in MB/s (0 = unlimited). | 0 |  |
| `encryption` _boolean_ | Encryption enables encryption for logical volumes. | false |  |
| `fabric` _string_ | Fabric is the transport fabric, for example, TCP. | tcp |  |
| `maxNamespacePerSubsys` _string_ | MaxNamespacePerSubsys limits namespaces per NVMf subsystem. | 1 |  |
| `tune2fsReservedBlocks` _string_ | Tune2fsReservedBlocks sets the ext4 reserved-blocks percentage. Left unset, the node<br />plugin skips tune2fs entirely and mkfs.ext4's own default reserve applies, matching a<br />StorageClass that omits tune2fs_reserved_blocks. A default of `0` here would not be a<br />no-op: it actively runs `tune2fs -m 0` on every volume, since the node plugin only skips<br />the call when the parameter is empty (see stageVolume in the CSI driver), not when it is<br />`0`. |  |  |
| `filesystem` _string_ | Filesystem is the filesystem used to format logical volumes of this pool. | xfs | Enum: [ext4 xfs] <br /> |


#### StorageCluster



StorageCluster is the Schema for the storageclusters API





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageCluster
metadata:
  name: string
spec:
  enableNodeAffinity: boolean
  stripe:
    dataChunks: integer
    parityChunks: integer
  fabricType: string
  clientDataIfname: string
  nvmfBasePort: integer
  rpcBasePort: integer
  snodeApiPort: integer
  maxConcurrentWorkerRestarts: integer
  maxSubsystemCount: integer
  maxHugePagesSize: string
  vcpuCount: integer
  warningThreshold:
    capacity: integer
    provisionedCapacity: integer
  criticalThreshold:
    capacity: integer
    provisionedCapacity: integer
  backup:
    localEndpoint: '^https?://[a-zA-Z0-9.-]+(:[0-9]{1,5})?(/.*)?$'
    snapshotBackups: boolean
    withCompression: boolean
    secondaryTarget: integer
    localTesting: boolean
    credentialsSecretRef:
      name: string
  hashicorpVaultSettings:
    baseURL: '^https?://[a-zA-Z0-9.-]+(:[0-9]{1,5})?(/.*)?$'
  volumeMigrationSettings:
    enabled: boolean
    rebalancerImage: string
    dataRealignment:
      enabled: boolean
      interval: Duration
      minMoves: integer
  volumeAutoPlacement:
    enabled: boolean
    migrationEnabled: boolean
    evaluationInterval: Duration
    imbalanceThreshold: integer
    minHotColdDifferencePct: integer
    defaultCoolDownSeconds: integer
    maxVolumeMigrationsPerCycle: integer
    storageNodeCandidateCount: integer
    metricsBackend: MetricsBackend
    prometheusURL: string
    latencyBenchmarkEnabled: boolean
    latencyBenchmarkInterval: Duration
    baselineStrategy: BaselineStrategy
    baselineWindow: Duration
    baselineColdStart: BaselineColdStartPolicy
    baselineMinSamples: integer
    baselineOutlierK: float
    iopsWeight: float
    throughputWeight: float
  enableFailureDomains: boolean
  enableChecksumValidation: boolean
  enableAtomic4kWrites: boolean
status:
  uuid: string
  phase: string
  subPhase: string
  clusterName: string
  mgmtNodes: integer
  storageNodes: integer
  nqn: string
  status: string
  rebalancing: boolean
  volumeMoveGeneration: integer
  realignedGeneration: integer
  lastDataRealignmentAt: Time
  erasureCodingScheme: string
  lastUpdated: Time
  created: Time
  configured: boolean
  maxFaultTolerance: integer
  maxConcurrentWorkerRestarts: integer
  activeOpsRef: string
  rebalancingMetrics:
    avgDeviationPct: float
    maxDeviationPct: float
    hottestNodeUUID: string
    coolestNodeUUID: string
    imbalancePercent: float
    lastEvaluatedAt: Time
    lastMigrationAt: Time
    nodeMetrics:
      - nodeUUID: string
        latencyDeviationPct: float
        volumeCount: integer
        lastUpdated: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha1` | | |
| `kind` _string_ | `StorageCluster` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  | Optional: \{\} <br /> |
| `spec` _[StorageClusterSpec](#storageclusterspec)_ | spec defines the desired state of StorageCluster |  | Required: \{\} <br /> |
| `status` _[StorageClusterStatus](#storageclusterstatus)_ | status defines the observed state of StorageCluster |  | Optional: \{\} <br /> |


#### StorageClusterOps



StorageClusterOps is a one-shot operational CR targeting a single SimplyblocksStorageCluster.
Analogous to a Kubernetes Job — it drives a cluster-level operation (activate, expand,
shutdown, restart, node-rolling-restart) to completion and records the result. Only one
StorageClusterOps can be active per cluster at a time.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageClusterOps
metadata:
  name: string
spec:
  clusterRef: string
  action: string
  nodeRollingRestart:
    refreshSNodeAPI: boolean
status:
  phase: StorageClusterOpsPhase
  triggered: boolean
  message: string
  startedAt: Time
  completedAt: Time
  nodeRollingRestartStatus:
    pendingNodes:
      - string
    processedNodes:
      - string
    nodePhase: string
    phaseTriggered: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha1` | | |
| `kind` _string_ | `StorageClusterOps` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  |  |
| `spec` _[StorageClusterOpsSpec](#storageclusteropsspec)_ |  |  |  |
| `status` _[StorageClusterOpsStatus](#storageclusteropsstatus)_ |  |  |  |


#### StorageClusterOpsPhase

_Underlying type:_ _string_

StorageClusterOpsPhase is the lifecycle phase of a StorageClusterOps.

_Validation:_
- Enum: [Pending Running Succeeded Failed]

_Appears in:_
- [StorageClusterOpsStatus](#storageclusteropsstatus)

| Field | Description |
| --- | --- |
| `Pending` |  |
| `Running` |  |
| `Succeeded` |  |
| `Failed` |  |


#### StorageClusterOpsSpec



StorageClusterOpsSpec defines the desired state of a StorageClusterOps.



_Appears in:_
- [StorageClusterOps](#storageclusterops)

_Example:_

```yaml
clusterRef: string
action: string
nodeRollingRestart:
  refreshSNodeAPI: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `clusterRef` _string_ | ClusterRef is the name of the target SimplyblocksStorageCluster. Immutable. |  | Required: \{\} <br /> |
| `action` _string_ | Action is the operation to perform. Immutable. |  | Enum: [activate expand shutdown start restart node-rolling-restart] <br />Required: \{\} <br /> |
| `nodeRollingRestart` _[NodeRollingRestartSpec](#noderollingrestartspec)_ | NodeRollingRestart configures behaviour specific to the node-rolling-restart action.<br />Ignored for all other actions. |  | Optional: \{\} <br /> |


#### StorageClusterOpsStatus



StorageClusterOpsStatus holds the observed state of a StorageClusterOps.



_Appears in:_
- [StorageClusterOps](#storageclusterops)

_Example:_

```yaml
phase: StorageClusterOpsPhase
triggered: boolean
message: string
startedAt: Time
completedAt: Time
nodeRollingRestartStatus:
  pendingNodes:
    - string
  processedNodes:
    - string
  nodePhase: string
  phaseTriggered: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _[StorageClusterOpsPhase](#storageclusteropsphase)_ | Phase is the high-level lifecycle phase. |  | Enum: [Pending Running Succeeded Failed] <br />Optional: \{\} <br /> |
| `triggered` _boolean_ | Triggered indicates the backend POST has been sent for this operation.<br />Guards against duplicate backend calls on retry. |  | Optional: \{\} <br /> |
| `message` _string_ | Message is a human-readable description of the current state or failure reason. |  | Optional: \{\} <br /> |
| `startedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | StartedAt is when the operation began. |  | Optional: \{\} <br /> |
| `completedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | CompletedAt is when the operation finished (successfully or not). |  | Optional: \{\} <br /> |
| `nodeRollingRestartStatus` _[NodeRollingRestartStatus](#noderollingrestartstatus)_ | NodeRollingRestartStatus tracks per-node progress for the node-rolling-restart action.<br />Nil for all other actions. |  | Optional: \{\} <br /> |


#### StorageClusterSpec



StorageClusterSpec defines the desired state of StorageCluster



_Appears in:_
- [StorageCluster](#storagecluster)

_Example:_

```yaml
enableNodeAffinity: boolean
stripe:
  dataChunks: integer
  parityChunks: integer
fabricType: string
clientDataIfname: string
nvmfBasePort: integer
rpcBasePort: integer
snodeApiPort: integer
maxConcurrentWorkerRestarts: integer
maxSubsystemCount: integer
maxHugePagesSize: string
vcpuCount: integer
warningThreshold:
  capacity: integer
  provisionedCapacity: integer
criticalThreshold:
  capacity: integer
  provisionedCapacity: integer
backup:
  localEndpoint: '^https?://[a-zA-Z0-9.-]+(:[0-9]{1,5})?(/.*)?$'
  snapshotBackups: boolean
  withCompression: boolean
  secondaryTarget: integer
  localTesting: boolean
  credentialsSecretRef:
    name: string
hashicorpVaultSettings:
  baseURL: '^https?://[a-zA-Z0-9.-]+(:[0-9]{1,5})?(/.*)?$'
volumeMigrationSettings:
  enabled: boolean
  rebalancerImage: string
  dataRealignment:
    enabled: boolean
    interval: Duration
    minMoves: integer
volumeAutoPlacement:
  enabled: boolean
  migrationEnabled: boolean
  evaluationInterval: Duration
  imbalanceThreshold: integer
  minHotColdDifferencePct: integer
  defaultCoolDownSeconds: integer
  maxVolumeMigrationsPerCycle: integer
  storageNodeCandidateCount: integer
  metricsBackend: MetricsBackend
  prometheusURL: string
  latencyBenchmarkEnabled: boolean
  latencyBenchmarkInterval: Duration
  baselineStrategy: BaselineStrategy
  baselineWindow: Duration
  baselineColdStart: BaselineColdStartPolicy
  baselineMinSamples: integer
  baselineOutlierK: float
  iopsWeight: float
  throughputWeight: float
enableFailureDomains: boolean
enableChecksumValidation: boolean
enableAtomic4kWrites: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `enableNodeAffinity` _boolean_ | EnableNodeAffinity enables node-affinity placement for storage components. |  | Optional: \{\} <br /> |
| `stripe` _[StripeSpec](#stripespec)_ | StripeSpec configures erasure-coding data/parity chunk counts. |  |  |
| `fabricType` _string_ | FabricType defines the storage fabric type. |  |  |
| `clientDataIfname` _string_ | ClientDataIfname defines the client data network interface. |  |  |
| `nvmfBasePort` _integer_ | NvmfBasePort defines the base NVMf service port. |  |  |
| `rpcBasePort` _integer_ | RpcBasePort defines the base RPC service port. |  |  |
| `snodeApiPort` _integer_ | SnodeApiPort defines the storage-node API port. |  |  |
| `maxConcurrentWorkerRestarts` _integer_ | MaxConcurrentWorkerRestarts is the maximum number of Kubernetes worker nodes the operator<br />may drain and restart simultaneously. The effective concurrency applied by the drain<br />coordinator is min(MaxConcurrentWorkerRestarts, MaxFaultTolerance).<br />Defaults to 1 when unset. |  | Minimum: 1 <br />Optional: \{\} <br /> |
| `maxSubsystemCount` _integer_ | MaxSubsystemCount is the maximum number of NVMe-oF subsystems per storage<br />node. Applies to every storage node in the cluster. Required: it sizes huge<br />pages, and a node that receives no value fails config generation outright<br />rather than falling back to a default. |  | Maximum: 75 <br />Minimum: 10 <br />Required: \{\} <br /> |
| `maxHugePagesSize` _string_ | MaxHugePagesSize is the maximum allocatable size of huge pages on each<br />storage node, for example, `100G` or `1T`. A bare number is interpreted as GB. It is<br />a floor, not a cap: the effective huge-page allocation is the larger of this<br />value and the minimum the node's device and subsystem count requires. When<br />omitted the computed minimum is used. |  | Optional: \{\} <br /> |
| `vcpuCount` _integer_ | VCPUCount is the number of vCPUs allocated to SPDK on each storage node.<br />This is an explicit core count, not a percentage. Required: the core layout<br />it produces must match across the cluster, so it is stated rather than left<br />to a per-node heuristic.<br />The floor is 4 rather than a hardware limit: a node must carry one core<br />beyond this budget for the system, and the control plane's core layout<br />assigns no NVMe-oF poller core at all for a 2-vCPU budget. |  | Minimum: 4 <br />Required: \{\} <br /> |
| `warningThreshold` _[CapacityThresholdSpec](#capacitythresholdspec)_ | WarningThresholdSpec defines warning-level capacity thresholds. |  |  |
| `criticalThreshold` _[CapacityThresholdSpec](#capacitythresholdspec)_ | CriticalThresholdSpec defines critical-level capacity thresholds. |  |  |
| `backup` _[BackupSpec](#backupspec)_ | Backup specifies the specification for backup to S3 configuration |  |  |
| `hashicorpVaultSettings` _[HashicorpVaultSettings](#hashicorpvaultsettings)_ | HashicorpVaultSettings configures the Vault endpoint used by the cluster for key storage. |  |  |
| `volumeMigrationSettings` _[VolumeMigrationSettings](#volumemigrationsettings)_ | VolumeMigrationSettings controls volume migration for this cluster. |  | Optional: \{\} <br /> |
| `volumeAutoPlacement` _[VolumeAutoPlacementSettings](#volumeautoplacementsettings)_ | VolumeAutoPlacement configures automatic, latency-driven volume rebalancing. When<br />nil/disabled the operator performs only manually triggered VolumeMigrations. |  | Optional: \{\} <br /> |
| `enableFailureDomains` _boolean_ | EnableFailureDomains opts the cluster into failure-domain mode. When enabled, every<br />storage node must declare a failure-domain group so the control plane can spread<br />erasure-coding chunks across independent fault groups. Immutable once set — failure-<br />domain mode cannot be toggled on a live cluster. |  | Optional: \{\} <br /> |
| `enableChecksumValidation` _boolean_ | EnableChecksumValidation enables inline CRC checksum validation on every I/O for<br />silent-data-error protection. Immutable once set: the backend bakes the checksum method<br />into each device's bdev_alceml_create call at cluster-create time and never re-applies<br />it. | false | Optional: \{\} <br /> |
| `enableAtomic4kWrites` _boolean_ | EnableAtomic4kWrites declares that devices guarantee 4K write atomicity even with a<br /><4K logical block size (e.g., AWS NVMe is 512B but atomic at 4K), letting checksum<br />fallback mode run on them despite the data plane's normal >=4K block-size requirement.<br />Only meaningful when EnableChecksumValidation is true. Cannot be changed after cluster<br />creation. | false | Optional: \{\} <br /> |


#### StorageClusterStatus



StorageClusterStatus defines the observed state of StorageCluster.



_Appears in:_
- [StorageCluster](#storagecluster)

_Example:_

```yaml
uuid: string
phase: string
subPhase: string
clusterName: string
mgmtNodes: integer
storageNodes: integer
nqn: string
status: string
rebalancing: boolean
volumeMoveGeneration: integer
realignedGeneration: integer
lastDataRealignmentAt: Time
erasureCodingScheme: string
lastUpdated: Time
created: Time
configured: boolean
maxFaultTolerance: integer
maxConcurrentWorkerRestarts: integer
activeOpsRef: string
rebalancingMetrics:
  avgDeviationPct: float
  maxDeviationPct: float
  hottestNodeUUID: string
  coolestNodeUUID: string
  imbalancePercent: float
  lastEvaluatedAt: Time
  lastMigrationAt: Time
  nodeMetrics:
    - nodeUUID: string
      latencyDeviationPct: float
      volumeCount: integer
      lastUpdated: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `uuid` _string_ | UUID is the backend cluster UUID. |  |  |
| `phase` _string_ | Phase tracks the cluster creation lifecycle to prevent concurrent reconcilers<br />from creating duplicate clusters. Set to "creation" while a creation is in<br />progress and cleared once the cluster UUID is persisted. |  |  |
| `subPhase` _string_ | SubPhase tracks the step within the current Phase. Reserved for future<br />sub-state machine expansion; currently only "creating" is used. |  |  |
| `clusterName` _string_ | ClusterName is the resolved backend cluster name. |  |  |
| `mgmtNodes` _integer_ | MgmtNodes is the number of management nodes.<br />FIXME: Unused for now (API update required?) |  |  |
| `storageNodes` _integer_ | StorageNodes is the number of storage nodes.<br />FIXME: Unused for now (API update required?) |  |  |
| `nqn` _string_ | NQN is the cluster NVM subsystem qualified name. |  |  |
| `status` _string_ | Status is the backend-reported lifecycle status. |  |  |
| `rebalancing` _boolean_ | Rebalancing indicates whether cluster rebalancing is currently active. |  |  |
| `volumeMoveGeneration` _integer_ | VolumeMoveGeneration counts completed volume moves. Every migration that reaches<br />Completed increments it, and nothing else writes it, so it only ever grows. |  | Optional: \{\} <br /> |
| `realignedGeneration` _integer_ | RealignedGeneration is the VolumeMoveGeneration that the last successfully<br />requested realignment covers. A realignment is outstanding while<br />VolumeMoveGeneration exceeds it.<br />This is recorded from the value read *before* the request is sent, because that<br />is what the realignment can actually account for: a migration completing while<br />the request is in flight raises VolumeMoveGeneration past it and so correctly<br />leaves another realignment outstanding, instead of being swallowed by the one<br />already running. |  | Optional: \{\} <br /> |
| `lastDataRealignmentAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | LastDataRealignmentAt is the time of the last successful control-plane data<br />realignment. It is used to space realignments by DataRealignment.Interval and to<br />avoid re-running at the end of an interval when nothing is pending. |  | Optional: \{\} <br /> |
| `erasureCodingScheme` _string_ | ErasureCodingScheme is the active erasure-coding layout, for example, `2x1`. |  |  |
| `lastUpdated` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | LastUpdated is the last backend update timestamp.<br />FIXME: Unused for now (API update required?) |  |  |
| `created` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | Created is the backend creation timestamp.<br />FIXME: Unused for now (API update required?) |  |  |
| `configured` _boolean_ | Configured indicates whether initial cluster setup completed. |  |  |
| `maxFaultTolerance` _integer_ | MaxFaultTolerance is the backend-reported maximum number of nodes that can<br />be simultaneously offline (failed, drained, or restarted) without violating<br />the cluster's redundancy guarantees. |  |  |
| `maxConcurrentWorkerRestarts` _integer_ | MaxConcurrentWorkerRestarts is the effective concurrent-restart limit applied<br />by the drain coordinator: min(spec.MaxConcurrentWorkerRestarts, MaxFaultTolerance).<br />Defaults to 1. Exposed here so controllers and tooling can read a single<br />authoritative value without re-computing it. |  | Optional: \{\} <br /> |
| `activeOpsRef` _string_ | ActiveOpsRef is the name of the currently active ClusterOps on this cluster.<br />Empty when no operation is in progress. |  | Optional: \{\} <br /> |
| `rebalancingMetrics` _[RebalancingMetrics](#rebalancingmetrics)_ | RebalancingMetrics is updated by the auto-rebalancer each evaluation cycle. |  | Optional: \{\} <br /> |


#### StorageNode



StorageNode is the Schema for a single backend storage node instance.
One StorageNode CR exists per (workerNode, socketIndex) pair and is owned
by the parent StorageNodeSet.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNode
metadata:
  name: string
spec:
  storageNodeSetRef: string
  workerNode: string
  socketId: string
  nodeIndex: integer
  socketIndex: integer
  overrides:
    spdkImage: string
    spdkProxyImage: string
    spdkSystemMemory: '^[0-9]+(G|GI|GB|GiB|M|MI|MB|MiB|g|gi|gb|gib|m|mi|mb|mib)?$'
    journalManager:
      count: integer
      percentPerDevice: integer
    pcieAllowList:
      - string
    pcieDenyList:
      - string
    pcieModel: string
    driveSizeRange: string
    deviceNames:
      - string
    enableLblk: boolean
    blkNames:
      - string
    blkNamesExclude:
      - string
    blkSerials:
      - string
    lblkJournalPercent: integer
    blkForceFormat: boolean
    enableCpuTopology: boolean
    reservedSystemCPU: string
    ubuntuHost: boolean
    skipKubeletConfiguration: boolean
    failureDomain: integer
    expand: boolean
status:
  uuid: string
  status: string
  health: boolean
  hostname: string
  uptime: string
  resources:
    cpu: integer
    memory: string
    volumes: integer
    devices: string
    capacity:
      totalBytes: integer
      usedBytes: integer
      sampledAt: Time
  ports:
    management: string
    nvmeof: integer
    lvol: integer
    rpc: integer
  postedAt: Time
  activeOpsRef: string
  latencyMetrics:
    nodeUUID: string
    baselineP50NS: integer
    baselineP99NS: integer
    baselineMeasuredAt: Time
  failureDomain: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha1` | | |
| `kind` _string_ | `StorageNode` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  |  |
| `spec` _[StorageNodeSpec](#storagenodespec)_ |  |  |  |
| `status` _[StorageNodeStatus](#storagenodestatus)_ |  |  |  |


#### StorageNodeCapacity



StorageNodeCapacity is a node's storage occupancy, as the control plane last
measured it.

It carries the same two numbers as a device's capacity, because a node's is
the sum of its devices' and a reader comparing the two should not have to
reconcile different shapes. It is written only when the reading has moved
materially: a sample that changed by a few blocks is not worth an etcd write,
and writing every sample would make the reconciler retrigger itself on its
own status update.



_Appears in:_
- [StorageNodeResources](#storagenoderesources)

_Example:_

```yaml
totalBytes: integer
usedBytes: integer
sampledAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `totalBytes` _integer_ | TotalBytes is the storage the node's devices provide. |  | Minimum: 0 <br />Optional: \{\} <br /> |
| `usedBytes` _integer_ | UsedBytes is what they currently hold. |  | Minimum: 0 <br />Optional: \{\} <br /> |
| `sampledAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | SampledAt is when the control plane took the reading. It is not when the<br />object was written, and it may be considerably older if metrics<br />collection has stopped. |  | Optional: \{\} <br /> |


#### StorageNodeOps



StorageNodeOps is a one-shot operational CR targeting a single StorageNode.
Analogous to a Kubernetes Job — it drives an action (shutdown, restart, suspend,
resume, remove/drain) to completion and records the result. Only one
StorageNodeOps can be active per StorageNode at a time.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeOps
metadata:
  name: string
spec:
  storageNodeRef: string
  action: string
  targetWorkerNode: string
  force: boolean
  reattachVolume: boolean
  newSsdPcie:
    - string
  drain:
    systemVolumeFilterRegex: string
status:
  phase: StorageNodeOpsPhase
  subPhase: StorageNodeOpsSubPhase
  message: string
  volumesMigrated: integer
  volumesPending: integer
  triggered: boolean
  startedAt: Time
  completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha1` | | |
| `kind` _string_ | `StorageNodeOps` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  |  |
| `spec` _[StorageNodeOpsSpec](#storagenodeopsspec)_ |  |  |  |
| `status` _[StorageNodeOpsStatus](#storagenodeopsstatus)_ |  |  |  |


#### StorageNodeOpsPhase

_Underlying type:_ _string_

StorageNodeOpsPhase is the lifecycle phase of a StorageNodeOps.

_Validation:_
- Enum: [Pending Running Succeeded Failed]

_Appears in:_
- [StorageNodeOpsStatus](#storagenodeopsstatus)

| Field | Description |
| --- | --- |
| `Pending` |  |
| `Running` |  |
| `Succeeded` |  |
| `Failed` |  |


#### StorageNodeOpsSpec



StorageNodeOpsSpec defines the desired state of a StorageNodeOps.



_Appears in:_
- [StorageNodeOps](#storagenodeops)

_Example:_

```yaml
storageNodeRef: string
action: string
targetWorkerNode: string
force: boolean
reattachVolume: boolean
newSsdPcie:
  - string
drain:
  systemVolumeFilterRegex: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `storageNodeRef` _string_ | StorageNodeRef is the name of the target StorageNode. Immutable. |  | Required: \{\} <br /> |
| `action` _string_ | Action is the operation to perform. Immutable. |  | Enum: [shutdown restart suspend resume remove migrate] <br />Required: \{\} <br /> |
| `targetWorkerNode` _string_ | TargetWorkerNode is the Kubernetes worker hostname the storage node is<br />relocated onto. Required (and only used) when action=migrate.<br />A migration is NOT a drain/remove: the storage node keeps its backend UUID<br />and its partition / logical-volume assignments follow it. The operator<br />issues a control-plane restart pointed at the target host's<br />storage-node-api (node_address), waits for the node to come back online<br />there, then /promotes it (starting a rebalance) and re-points the<br />StorageNode's spec.workerNode and the owning StorageNodeSet.workerNodes<br />from the source worker to this one. No fresh storage node is provisioned<br />and no VolumeMigration CRs are created. Immutable. |  | Optional: \{\} <br /> |
| `force` _boolean_ | Force enables forced execution where the backend supports it. |  | Optional: \{\} <br /> |
| `reattachVolume` _boolean_ | ReattachVolume reattaches volumes during the node restart.<br />Applicable when action=restart or action=migrate. |  | Optional: \{\} <br /> |
| `newSsdPcie` _string array_ | NewSsdPcie lists additional NVMe PCIe addresses to bind on the target host<br />during a migration. Passed through to the control-plane restart as<br />new_ssd_pcie. Only applicable when action=migrate. |  | Optional: \{\} <br /> |
| `drain` _[DrainOpsSpec](#drainopsspec)_ | Drain configures the drain workflow. Only applicable when action=remove. |  | Optional: \{\} <br /> |


#### StorageNodeOpsStatus



StorageNodeOpsStatus holds the observed state of a StorageNodeOps.



_Appears in:_
- [StorageNodeOps](#storagenodeops)

_Example:_

```yaml
phase: StorageNodeOpsPhase
subPhase: StorageNodeOpsSubPhase
message: string
volumesMigrated: integer
volumesPending: integer
triggered: boolean
startedAt: Time
completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _[StorageNodeOpsPhase](#storagenodeopsphase)_ | Phase is the high-level lifecycle phase. |  | Enum: [Pending Running Succeeded Failed] <br />Optional: \{\} <br /> |
| `subPhase` _[StorageNodeOpsSubPhase](#storagenodeopssubphase)_ | SubPhase tracks the active drain step when action=remove and phase=Running. |  | Enum: [Validating Suspending Migrating Verifying Removing Preparing Restarting Promoting] <br />Optional: \{\} <br /> |
| `message` _string_ | Message is a human-readable description of the current state or failure reason. |  | Optional: \{\} <br /> |
| `volumesMigrated` _integer_ | VolumesMigrated is the count of volumes successfully migrated (drain only). |  | Optional: \{\} <br /> |
| `volumesPending` _integer_ | VolumesPending is the count of volumes awaiting migration (drain only). |  | Optional: \{\} <br /> |
| `triggered` _boolean_ | Triggered indicates the backend action POST has been sent (used during<br />Suspending to avoid duplicate POSTs across reconcile iterations). |  | Optional: \{\} <br /> |
| `startedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | StartedAt is when the operation began. |  | Optional: \{\} <br /> |
| `completedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | CompletedAt is when the operation finished (successfully or not). |  | Optional: \{\} <br /> |


#### StorageNodeOpsSubPhase

_Underlying type:_ _string_

StorageNodeOpsSubPhase is the active sub-phase during a running op: the drain
steps when action=remove, and the Preparing → Migrating → Promoting steps when
action=migrate.

_Validation:_
- Enum: [Validating Suspending Migrating Verifying Removing Preparing Restarting Promoting]

_Appears in:_
- [StorageNodeOpsStatus](#storagenodeopsstatus)

| Field | Description |
| --- | --- |
| `Validating` |  |
| `Suspending` |  |
| `Migrating` |  |
| `Verifying` |  |
| `Removing` |  |
| `Preparing` | StorageNodeOpsSubPhasePreparing marks that a migrate op is preparing the<br />target worker: cloning per-node config, labeling it into the storage<br />plane, and waiting until its storage-node-api pod is Ready and its per-pod<br />DNS name is published in the EndpointSlice — the precondition for the<br />control-plane restart to resolve node_address.<br /> |
| `Restarting` | StorageNodeOpsSubPhaseRestarting marks that a migrate op has issued the<br />control-plane restart and confirmed the node entered in_restart; it is<br />now waiting for the node to come back online on the target host. The<br />restart is asynchronous, so the op only advances to Promoting after the<br />node has left online (restart started) and returned to online (restart<br />finished) — issuing /promote earlier races the in-flight restart's node<br />writes and leaves the relocated devices stuck in "new".<br /> |
| `Promoting` | StorageNodeOpsSubPhasePromoting marks that a migrate op has issued the<br />control-plane /promote for the relocated node (guards against re-promoting).<br /> |


#### StorageNodeOverrides



StorageNodeOverrides holds per-node configuration that overrides the parent
StorageNodeSet fleet defaults for a specific worker node. Populated by the
StorageNodeSetReconciler from StorageNodeSet.spec.nodeConfigs[workerNode] on
every reconcile. The StorageNodeSet is the single source of truth — users
should not edit this struct directly on the StorageNode.

Fields here mirror the configurable (non-immutable, non-infrastructure) fields
of StorageNodeSetSpec. When a field is set here it takes precedence over the
fleet default; when omitted the fleet default applies.



_Appears in:_
- [StorageNodeSetSpec](#storagenodesetspec)
- [StorageNodeSpec](#storagenodespec)

_Example:_

```yaml
spdkImage: string
spdkProxyImage: string
spdkSystemMemory: '^[0-9]+(G|GI|GB|GiB|M|MI|MB|MiB|g|gi|gb|gib|m|mi|mb|mib)?$'
journalManager:
  count: integer
  percentPerDevice: integer
pcieAllowList:
  - string
pcieDenyList:
  - string
pcieModel: string
driveSizeRange: string
deviceNames:
  - string
enableLblk: boolean
blkNames:
  - string
blkNamesExclude:
  - string
blkSerials:
  - string
lblkJournalPercent: integer
blkForceFormat: boolean
enableCpuTopology: boolean
reservedSystemCPU: string
ubuntuHost: boolean
skipKubeletConfiguration: boolean
failureDomain: integer
expand: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `spdkImage` _string_ | SpdkImage overrides the SPDK image for this node (e.g. for phased rollouts). |  | Optional: \{\} <br /> |
| `spdkProxyImage` _string_ | SpdkProxyImage overrides the SPDK proxy image for this node. |  | Optional: \{\} <br /> |
| `spdkSystemMemory` _string_ | SpdkSystemMemory overrides the SPDK huge-page memory allocation for this node<br />(e.g. "4G", "512M"). |  | Pattern: `^[0-9]+(G\|GI\|GB\|GiB\|M\|MI\|MB\|MiB\|g\|gi\|gb\|gib\|m\|mi\|mb\|mib)?$` <br />Optional: \{\} <br /> |
| `journalManager` _[JournalManagerSpec](#journalmanagerspec)_ | JournalManagerSpec overrides journal manager tuning for this node. |  | Optional: \{\} <br /> |
| `pcieAllowList` _string array_ | PcieAllowList overrides the list of PCI addresses allowed for use on this node. |  | Optional: \{\} <br /> |
| `pcieDenyList` _string array_ | PcieDenyList overrides the list of PCI addresses excluded from use on this node. |  | Optional: \{\} <br /> |
| `pcieModel` _string_ | PcieModel overrides the PCI model filter for this node. |  | Optional: \{\} <br /> |
| `driveSizeRange` _string_ | DriveSizeRange overrides the drive size range filter for this node. |  | Optional: \{\} <br /> |
| `deviceNames` _string array_ | DeviceNames explicitly defines the NVMe namespace names to use on this node<br />(e.g. ["nvme0n1","nvme1n1"]). |  | Optional: \{\} <br /> |
| `enableLblk` _boolean_ | EnableLblk overrides whether this node uses lblk devices instead of NVMe.<br />Only meaningful when the cluster's spec.deviceMode is "lblk." |  | Optional: \{\} <br /> |
| `blkNames` _string array_ | BlkNames overrides the block-device kernel-name selector for this node.<br />Immutable once set, including unset-to-set (see StorageNodeSetSpec.BlkNames). |  | MaxItems: 64 <br />Optional: \{\} <br /> |
| `blkNamesExclude` _string array_ | BlkNamesExclude overrides the kernel-name exclusion selector for this node.<br />Immutable once set (see BlkNames). |  | MaxItems: 64 <br />Optional: \{\} <br /> |
| `blkSerials` _string array_ | BlkSerials overrides the block-device serial/WWN selector for this node.<br />Immutable once set (see BlkNames). |  | MaxItems: 64 <br />Optional: \{\} <br /> |
| `lblkJournalPercent` _integer_ | LblkJournalPercent overrides the lblk journal-partition capacity percentage for<br />this node. |  | Optional: \{\} <br /> |
| `blkForceFormat` _boolean_ | BlkForceFormat overrides whether partitioned lblk devices are force-wiped<br />(wipefs) to become eligible whole-disk devices on this node. |  | Optional: \{\} <br /> |
| `enableCpuTopology` _boolean_ | EnableCpuTopology overrides topology-aware CPU handling for this node. |  | Optional: \{\} <br /> |
| `reservedSystemCPU` _string_ | ReservedSystemCPU overrides the CPUs reserved for system workloads on this node. |  | Optional: \{\} <br /> |
| `ubuntuHost` _boolean_ | UbuntuHost overrides the Ubuntu host OS flag for this node. |  | Optional: \{\} <br /> |
| `skipKubeletConfiguration` _boolean_ | SkipKubeletConfiguration overrides whether kubelet configuration changes are<br />skipped for this node. |  | Optional: \{\} <br /> |
| `failureDomain` _integer_ | FailureDomain is the failure-domain group index (≥ 0) for this node.<br />Required when the parent StorageCluster has enableFailureDomains=true.<br />Overrides StorageNodeSet.spec.nodeFailureDomains[workerNode] when both are set. |  | Minimum: 0 <br />Optional: \{\} <br /> |
| `expand` _boolean_ | Expand marks this node as a cluster-expansion add. When true the backend<br />node-add endpoint receives expand=true, triggering rebalancing behaviour<br />appropriate for in-place cluster growth. Overrides StorageNodeSet.spec.expand. |  | Optional: \{\} <br /> |


#### StorageNodePorts



StorageNodePorts groups the network port and address fields reported by the backend.



_Appears in:_
- [StorageNodeStatus](#storagenodestatus)

_Example:_

```yaml
management: string
nvmeof: integer
lvol: integer
rpc: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `management` _string_ | Management is the management IP address of the node. |  | Optional: \{\} <br /> |
| `nvmeof` _integer_ | NvmeOf is the NVMe-oF fabric port. |  | Optional: \{\} <br /> |
| `lvol` _integer_ | Lvol is the logical-volume subsystem port. |  | Optional: \{\} <br /> |
| `rpc` _integer_ | Rpc is the RPC/management API port. |  | Optional: \{\} <br /> |


#### StorageNodeResources



StorageNodeResources groups compute and storage resource fields reported by the backend.



_Appears in:_
- [StorageNodeStatus](#storagenodestatus)

_Example:_

```yaml
cpu: integer
memory: string
volumes: integer
devices: string
capacity:
  totalBytes: integer
  usedBytes: integer
  sampledAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `cpu` _integer_ | CPU is the number of SPDK CPU cores allocated to this node. |  | Optional: \{\} <br /> |
| `memory` _string_ | Memory is the SPDK memory allocation reported by the backend. |  | Optional: \{\} <br /> |
| `volumes` _integer_ | Volumes is the current number of logical volumes on this node. |  | Optional: \{\} <br /> |
| `devices` _string_ | Devices is the device summary (online/total) reported by the backend. |  | Optional: \{\} <br /> |
| `capacity` _[StorageNodeCapacity](#storagenodecapacity)_ | Capacity is how much of the node's storage is in use, summed over its<br />devices. It is a measurement rather than a declaration, so it is absent<br />until something has measured it, and it lags reality by the interval at<br />which the control plane's metrics are scraped. |  | Optional: \{\} <br /> |


#### StorageNodeSet



StorageNodeSet is the Schema for the storagenodesets API





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeSet
metadata:
  name: string
spec:
  clusterName: string
  clusterImage: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
  spdkImage: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
  spdkProxyImage: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
  mgmtIfname: string
  enableJournalDevice: boolean
  journalManager:
    count: integer
    percentPerDevice: integer
  pcieAllowList:
    - string
  pcieDenyList:
    - string
  pcieModel: string
  driveSizeRange: string
  socketsToUse:
    - string
  nodesPerSocket: integer
  dataIfname:
    - string
  workerNodes:
    - string
  openShiftCluster: boolean
  openShiftMachineConfigPool: string
  deviceNames:
    - string
  enableLblk: boolean
  blkNames:
    - string
  blkNamesExclude:
    - string
  blkSerials:
    - string
  lblkJournalPercent: integer
  blkForceFormat: boolean
  ubuntuHost: boolean
  skipKubeletConfiguration: boolean
  forceFormat4K: boolean
  enableCpuTopology: boolean
  reservedSystemCPU: string
  spdkSystemMemory: '^[0-9]+(G|GI|GB|GiB|M|MI|MB|MiB|g|gi|gb|gib|m|mi|mb|mib)?$'
  tolerations:
    - Toleration
  maxParallelNodeAdds: integer
  containerResources: ResourceRequirements
  initContainerResources: ResourceRequirements
  imagePullPolicy: PullPolicy
  nodeFailureDomains:
    string: integer
  expand: boolean
  nodeConfigs:
    string:
      spdkImage: string
      spdkProxyImage: string
      spdkSystemMemory: '^[0-9]+(G|GI|GB|GiB|M|MI|MB|MiB|g|gi|gb|gib|m|mi|mb|mib)?$'
      journalManager:
        count: integer
        percentPerDevice: integer
      pcieAllowList:
        - string
      pcieDenyList:
        - string
      pcieModel: string
      driveSizeRange: string
      deviceNames:
        - string
      enableLblk: boolean
      blkNames:
        - string
      blkNamesExclude:
        - string
      blkSerials:
        - string
      lblkJournalPercent: integer
      blkForceFormat: boolean
      enableCpuTopology: boolean
      reservedSystemCPU: string
      ubuntuHost: boolean
      skipKubeletConfiguration: boolean
      failureDomain: integer
      expand: boolean
status:
  totalNodes: integer
  onlineNodes: integer
  offlineNodes: integer
  suspendedNodes: integer
  creatingNodes: integer
  removedNodes: integer
  nodes:
    - uuid: string
      health: boolean
      status: string
      cpu: integer
      memory: string
      volumes: integer
      rpcPort: integer
      lvolPort: integer
      nvmfPort: integer
      devices: string
      uptime: string
      hostname: string
      mgmtIp: string
      postedAt: Time
      failureDomain: integer
  drainCoordination:
    - hostname: string
      phase: string
      startedAt: Time
      message: string
      activeNodeUUID: string
  pendingNodeAdds:
    string: Time
  schedulingFailedWorkers:
    string: boolean
  latencyMetrics:
    - nodeUUID: string
      baselineP50NS: integer
      baselineP99NS: integer
      baselineMeasuredAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha1` | | |
| `kind` _string_ | `StorageNodeSet` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  | Optional: \{\} <br /> |
| `spec` _[StorageNodeSetSpec](#storagenodesetspec)_ | spec defines the desired state of StorageNodeSet |  | Required: \{\} <br /> |
| `status` _[StorageNodeSetStatus](#storagenodesetstatus)_ | status defines the observed state of StorageNodeSet |  | Optional: \{\} <br /> |


#### StorageNodeSetSpec



StorageNodeSetSpec defines the desired state of StorageNodeSet



_Appears in:_
- [StorageNodeSet](#storagenodeset)

_Example:_

```yaml
clusterName: string
clusterImage: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
spdkImage: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
spdkProxyImage: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
mgmtIfname: string
enableJournalDevice: boolean
journalManager:
  count: integer
  percentPerDevice: integer
pcieAllowList:
  - string
pcieDenyList:
  - string
pcieModel: string
driveSizeRange: string
socketsToUse:
  - string
nodesPerSocket: integer
dataIfname:
  - string
workerNodes:
  - string
openShiftCluster: boolean
openShiftMachineConfigPool: string
deviceNames:
  - string
enableLblk: boolean
blkNames:
  - string
blkNamesExclude:
  - string
blkSerials:
  - string
lblkJournalPercent: integer
blkForceFormat: boolean
ubuntuHost: boolean
skipKubeletConfiguration: boolean
forceFormat4K: boolean
enableCpuTopology: boolean
reservedSystemCPU: string
spdkSystemMemory: '^[0-9]+(G|GI|GB|GiB|M|MI|MB|MiB|g|gi|gb|gib|m|mi|mb|mib)?$'
tolerations:
  - Toleration
maxParallelNodeAdds: integer
containerResources: ResourceRequirements
initContainerResources: ResourceRequirements
imagePullPolicy: PullPolicy
nodeFailureDomains:
  string: integer
expand: boolean
nodeConfigs:
  string:
    spdkImage: string
    spdkProxyImage: string
    spdkSystemMemory: '^[0-9]+(G|GI|GB|GiB|M|MI|MB|MiB|g|gi|gb|gib|m|mi|mb|mib)?$'
    journalManager:
      count: integer
      percentPerDevice: integer
    pcieAllowList:
      - string
    pcieDenyList:
      - string
    pcieModel: string
    driveSizeRange: string
    deviceNames:
      - string
    enableLblk: boolean
    blkNames:
      - string
    blkNamesExclude:
      - string
    blkSerials:
      - string
    lblkJournalPercent: integer
    blkForceFormat: boolean
    enableCpuTopology: boolean
    reservedSystemCPU: string
    ubuntuHost: boolean
    skipKubeletConfiguration: boolean
    failureDomain: integer
    expand: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `clusterName` _string_ | ClusterName is the target storage cluster name. |  |  |
| `clusterImage` _string_ | ClusterImage is the container image used for storage-node workloads.<br />Must reference one of the trusted registries (quay.io/simplyblock-io, docker.io/simplyblock, public.ecr.aws/simply-block); digest pinning (@sha256:...) is recommended. |  | Pattern: `^($\|(quay\.io/simplyblock-io\|docker\.io/simplyblock\|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]\{64\})?)$` <br /> |
| `spdkImage` _string_ | SpdkImage is the SPDK image reference used by node services.<br />Must reference one of the trusted registries (quay.io/simplyblock-io, docker.io/simplyblock, public.ecr.aws/simply-block); digest pinning (@sha256:...) is recommended. |  | Pattern: `^($\|(quay\.io/simplyblock-io\|docker\.io/simplyblock\|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]\{64\})?)$` <br /> |
| `spdkProxyImage` _string_ | SpdkProxyImage is the SPDK proxy image reference used by node services.<br />Must reference one of the trusted registries (quay.io/simplyblock-io, docker.io/simplyblock, public.ecr.aws/simply-block); digest pinning (@sha256:...) is recommended. |  | Pattern: `^($\|(quay\.io/simplyblock-io\|docker\.io/simplyblock\|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]\{64\})?)$` <br /> |
| `mgmtIfname` _string_ | MgmtIfname is the management interface name used by storage nodes. |  |  |
| `enableJournalDevice` _boolean_ | EnableJournalDevice dedicates a whole NVMe device to the journal manager<br />instead of carving a journal partition out of every storage device. When<br />true the smallest device on the node becomes the journal device, and the<br />remaining devices are used whole; when false (the default) each device is<br />GPT-partitioned into a journal slice plus a storage slice. |  |  |
| `journalManager` _[JournalManagerSpec](#journalmanagerspec)_ | JournalManagerSpec configures journal manager behavior. |  |  |
| `pcieAllowList` _string array_ | PcieAllowList is the list of PCI addresses allowed for use. |  |  |
| `pcieDenyList` _string array_ | PcieDenyList is the list of PCI addresses excluded from use. |  |  |
| `pcieModel` _string_ | PcieModel filters devices by PCI model. |  |  |
| `driveSizeRange` _string_ | DriveSizeRange filters devices by size range. |  |  |
| `socketsToUse` _string array_ | SocketsToUse restricts deployment to selected NUMA sockets. |  |  |
| `nodesPerSocket` _integer_ | NodesPerSocket defines how many storage nodes are created per NUMA socket. |  |  |
| `dataIfname` _string array_ | DataIfname lists data-plane network interfaces. |  |  |
| `workerNodes` _string array_ | WorkerNodes is the set of Kubernetes worker nodes to manage. |  | MaxItems: 200 <br /> |
| `openShiftCluster` _boolean_ | OpenShiftCluster indicates OpenShift-specific behavior should be enabled. |  |  |
| `openShiftMachineConfigPool` _string_ | OpenShiftMachineConfigPool is the name of the MachineConfigPool that storage nodes belong to.<br />Generated MachineConfig resources will carry the machineconfiguration.openshift.io/role label<br />set to this value. Defaults to "worker" when unset. |  |  |
| `deviceNames` _string array_ | DeviceNames explicitly defines a comma separated list of nvme namespace names like nvme0n1,nvme1n1... |  |  |
| `enableLblk` _boolean_ | EnableLblk selects lblk devices instead of NVMe for this fleet. Only meaningful<br />when the cluster's spec.deviceMode is "lblk"; mutually exclusive with the NVMe<br />PCIe selectors below. |  | Optional: \{\} <br /> |
| `blkNames` _string array_ | BlkNames selects block devices by kernel name (e.g., sdb, sdc) when EnableLblk is<br />set. Empty selects every eligible whole disk. At most one of BlkNames,<br />BlkNamesExclude, BlkSerials may be set. Immutable once set — including unset-to-set,<br />since the backend (node_configure.py) silently ignores a selector change on an<br />already-provisioned node. |  | MaxItems: 64 <br />Optional: \{\} <br /> |
| `blkNamesExclude` _string array_ | BlkNamesExclude excludes block devices by kernel name when EnableLblk is set.<br />Immutable once set (see BlkNames). |  | MaxItems: 64 <br />Optional: \{\} <br /> |
| `blkSerials` _string array_ | BlkSerials selects block devices by serial number or WWN when EnableLblk is set —<br />stable across device-name changes, unlike BlkNames. Immutable once set (see<br />BlkNames). |  | MaxItems: 64 <br />Optional: \{\} <br /> |
| `lblkJournalPercent` _integer_ | LblkJournalPercent is the journal-partition capacity percentage, used when the<br />smallest selected lblk device is a partition. Ignored for whole disks; backend<br />defaults to 3. |  | Optional: \{\} <br /> |
| `blkForceFormat` _boolean_ | BlkForceFormat wipes partition tables and filesystem signatures (wipefs) from<br />partitioned lblk devices so they become eligible whole-disk devices. Destructive —<br />only set this when reusing a disk whose old data is no longer needed. |  | Optional: \{\} <br /> |
| `ubuntuHost` _boolean_ | UbuntuHost indicates the node host OS is Ubuntu. |  |  |
| `skipKubeletConfiguration` _boolean_ | SkipKubeletConfiguration skips kubelet configuration changes. |  |  |
| `forceFormat4K` _boolean_ | ForceFormat4K forces 4K blocksize formatting of the NVMe device where supported. |  |  |
| `enableCpuTopology` _boolean_ | EnableCpuTopology enables topology-aware CPU handling. |  |  |
| `reservedSystemCPU` _string_ | ReservedSystemCPU defines CPUs reserved for system workloads. |  |  |
| `spdkSystemMemory` _string_ | SpdkSystemMemory is the amount of memory reserved for SPDK system use (e.g. "4G", "512M").<br />When omitted the backend default is used. |  | Pattern: `^[0-9]+(G\|GI\|GB\|GiB\|M\|MI\|MB\|MiB\|g\|gi\|gb\|gib\|m\|mi\|mb\|mib)?$` <br /> |
| `tolerations` _[Toleration](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#toleration-v1-core) array_ | Tolerations configures pod tolerations for storage-node pods. |  |  |
| `maxParallelNodeAdds` _integer_ | MaxParallelNodeAdds limits how many non-FDB worker nodes can be in the<br />add process simultaneously. Defaults to 1 (fully sequential).<br />FDB workers are always sequential regardless of this setting. | 1 | Minimum: 1 <br /> |
| `containerResources` _[ResourceRequirements](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#resourcerequirements-v1-core)_ | ContainerResources sets CPU and memory requests/limits for the main storage-node container.<br />When omitted no limits are enforced, which preserves the previous behaviour. |  |  |
| `initContainerResources` _[ResourceRequirements](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#resourcerequirements-v1-core)_ | InitContainerResources sets CPU and memory requests/limits for the init container.<br />When omitted no limits are enforced. |  |  |
| `imagePullPolicy` _[PullPolicy](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#pullpolicy-v1-core)_ | ImagePullPolicy controls when the container image is pulled. Defaults to IfNotPresent. |  | Enum: [Always Never IfNotPresent] <br /> |
| `nodeFailureDomains` _object (keys:string, values:integer)_ | NodeFailureDomains assigns each worker node to a failure-domain group (integer ≥ 0).<br />Required when the referenced StorageCluster has enableFailureDomains=true.<br />Keys are Kubernetes worker node names; values are the failure-domain group index.<br />Each node in the same physical failure domain (rack, AZ, power unit) should share<br />the same group index so the control plane can spread erasure-coding chunks across<br />independent fault groups. |  | Optional: \{\} <br /> |
| `expand` _boolean_ | Expand indicates that storage nodes added from this StorageNodeSet are being<br />added to expand an already-active cluster. When true the backend node-add<br />endpoint receives expand=true, which triggers the appropriate rebalancing<br />behaviour for in-place cluster growth. |  | Optional: \{\} <br /> |
| `nodeConfigs` _object (keys:string, values:[StorageNodeOverrides](#storagenodeoverrides))_ | NodeConfigs allows per-worker-node configuration overrides keyed by the<br />Kubernetes worker node name. Entries are propagated to the corresponding<br />StorageNode.spec.overrides by the StorageNodeReconciler on every reconcile.<br />The StorageNodeSet is the single source of truth for all per-node config,<br />including failure domain assignment via nodeConfigs[worker].failureDomain. |  | MaxProperties: 200 <br />Optional: \{\} <br /> |


#### StorageNodeSetStatus



StorageNodeSetStatus defines the observed state of StorageNodeSet.



_Appears in:_
- [StorageNodeSet](#storagenodeset)

_Example:_

```yaml
totalNodes: integer
onlineNodes: integer
offlineNodes: integer
suspendedNodes: integer
creatingNodes: integer
removedNodes: integer
nodes:
  - uuid: string
    health: boolean
    status: string
    cpu: integer
    memory: string
    volumes: integer
    rpcPort: integer
    lvolPort: integer
    nvmfPort: integer
    devices: string
    uptime: string
    hostname: string
    mgmtIp: string
    postedAt: Time
    failureDomain: integer
drainCoordination:
  - hostname: string
    phase: string
    startedAt: Time
    message: string
    activeNodeUUID: string
pendingNodeAdds:
  string: Time
schedulingFailedWorkers:
  string: boolean
latencyMetrics:
  - nodeUUID: string
    baselineP50NS: integer
    baselineP99NS: integer
    baselineMeasuredAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `totalNodes` _integer_ | TotalNodes is the total number of owned StorageNode CRs. |  | Optional: \{\} <br /> |
| `onlineNodes` _integer_ | OnlineNodes is the count of StorageNode CRs with status "online". |  | Optional: \{\} <br /> |
| `offlineNodes` _integer_ | OfflineNodes is the count of StorageNode CRs with status "offline". |  | Optional: \{\} <br /> |
| `suspendedNodes` _integer_ | SuspendedNodes is the count of StorageNode CRs with status "suspended". |  | Optional: \{\} <br /> |
| `creatingNodes` _integer_ | CreatingNodes is the count of StorageNode CRs with status "in_creation". |  | Optional: \{\} <br /> |
| `removedNodes` _integer_ | RemovedNodes is the count of StorageNode CRs with status "removed". |  | Optional: \{\} <br /> |
| `nodes` _[NodeStatus](#nodestatus) array_ | Nodes is the observed state of each managed storage node. |  |  |
| `drainCoordination` _[NodeDrainState](#nodedrainstate) array_ | DrainCoordination tracks the upgrade-drain state per worker node. |  |  |
| `pendingNodeAdds` _object (keys:string, values:[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta))_ | PendingNodeAdds records the timestamp when a node-add POST was sent for<br />each worker hostname. Entries are removed only when all socket nodes for<br />that worker come online. This is the authoritative guard against duplicate<br />POSTs — it is a separate map field so patches to Status.Nodes never<br />inadvertently delete it. |  |  |
| `schedulingFailedWorkers` _object (keys:string, values:boolean)_ | SchedulingFailedWorkers tracks worker hostnames whose SPDK pod experienced<br />a FailedScheduling event during node add. Used to emit a recovery event<br />when the node subsequently comes online. |  |  |
| `latencyMetrics` _[NodeLatencyMetrics](#nodelatencymetrics) array_ | LatencyMetrics holds per-backend-node fio-measured latency data for rebalancing decisions. |  |  |


#### StorageNodeSpec



StorageNodeSpec defines the desired state of a StorageNode.



_Appears in:_
- [StorageNode](#storagenode)

_Example:_

```yaml
storageNodeSetRef: string
workerNode: string
socketId: string
nodeIndex: integer
socketIndex: integer
overrides:
  spdkImage: string
  spdkProxyImage: string
  spdkSystemMemory: '^[0-9]+(G|GI|GB|GiB|M|MI|MB|MiB|g|gi|gb|gib|m|mi|mb|mib)?$'
  journalManager:
    count: integer
    percentPerDevice: integer
  pcieAllowList:
    - string
  pcieDenyList:
    - string
  pcieModel: string
  driveSizeRange: string
  deviceNames:
    - string
  enableLblk: boolean
  blkNames:
    - string
  blkNamesExclude:
    - string
  blkSerials:
    - string
  lblkJournalPercent: integer
  blkForceFormat: boolean
  enableCpuTopology: boolean
  reservedSystemCPU: string
  ubuntuHost: boolean
  skipKubeletConfiguration: boolean
  failureDomain: integer
  expand: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `storageNodeSetRef` _string_ | StorageNodeSetRef is the name of the owning StorageNodeSet. Immutable. |  | Required: \{\} <br /> |
| `workerNode` _string_ | WorkerNode is the Kubernetes node hostname this StorageNode runs on.<br />Users may not change it directly — it is re-pointed only by the operator<br />during a node migration (StorageNodeOps action=migrate). The<br />StorageNode validating webhook rejects user-driven changes to this field. |  | Required: \{\} <br /> |
| `socketId` _string_ | SocketID is the NUMA socket identifier from spec.socketsToUse (e.g. "0", "1"). Immutable. |  | Optional: \{\} <br /> |
| `nodeIndex` _integer_ | NodeIndex is the per-socket node index (0..nodesPerSocket-1). Immutable. |  | Optional: \{\} <br /> |
| `socketIndex` _integer_ | SocketIndex is the global ordinal (socketPosition × nodesPerSocket + nodeIndex).<br />Used internally by the operator to select the correct backend node from the<br />RPC-port-sorted list in pollUUIDFromBackend. Immutable. |  | Optional: \{\} <br /> |
| `overrides` _[StorageNodeOverrides](#storagenodeoverrides)_ | Overrides holds per-node configuration propagated from<br />StorageNodeSet.spec.nodeConfigs[workerNode] on every reconcile. |  | Optional: \{\} <br /> |


#### StorageNodeStatus



StorageNodeStatus holds the observed state of a StorageNode.



_Appears in:_
- [StorageNode](#storagenode)

_Example:_

```yaml
uuid: string
status: string
health: boolean
hostname: string
uptime: string
resources:
  cpu: integer
  memory: string
  volumes: integer
  devices: string
  capacity:
    totalBytes: integer
    usedBytes: integer
    sampledAt: Time
ports:
  management: string
  nvmeof: integer
  lvol: integer
  rpc: integer
postedAt: Time
activeOpsRef: string
latencyMetrics:
  nodeUUID: string
  baselineP50NS: integer
  baselineP99NS: integer
  baselineMeasuredAt: Time
failureDomain: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `uuid` _string_ | UUID is the backend storage node UUID. Set once after node-add completes. |  | Optional: \{\} <br /> |
| `status` _string_ | Status is the backend-reported node status (e.g. online, suspended, offline). |  | Optional: \{\} <br /> |
| `health` _boolean_ | Health is the backend-reported node health flag. |  | Optional: \{\} <br /> |
| `hostname` _string_ | Hostname is the node hostname as reported by the backend. |  | Optional: \{\} <br /> |
| `uptime` _string_ | Uptime is the node uptime as reported by the backend. |  | Optional: \{\} <br /> |
| `resources` _[StorageNodeResources](#storagenoderesources)_ | Resources groups compute and storage resource metrics. |  | Optional: \{\} <br /> |
| `ports` _[StorageNodePorts](#storagenodeports)_ | Ports groups network connectivity fields (addresses and ports). |  | Optional: \{\} <br /> |
| `postedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | PostedAt is the timestamp when the node-add POST was sent.<br />Used as a provisioning guard against duplicate POSTs. |  | Optional: \{\} <br /> |
| `activeOpsRef` _string_ | ActiveOpsRef is the name of the currently active StorageNodeOps CR targeting<br />this node. Empty when no operation is in progress. Used for mutual exclusion. |  | Optional: \{\} <br /> |
| `latencyMetrics` _[NodeLatencyMetrics](#nodelatencymetrics)_ | LatencyMetrics holds the fio-measured baseline NVMe-oF latency for this node,<br />used by the volume rebalancer to make data-placement decisions. |  | Optional: \{\} <br /> |
| `failureDomain` _integer_ | FailureDomain is the effective failure-domain group index for this node<br />as reported by the backend (≥ 0). Nil when the backend has not assigned one. |  | Optional: \{\} <br /> |


#### StoragePool



StoragePool is the Schema for the storagepools API





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha1
kind: StoragePool
metadata:
  name: string
spec:
  clusterName: string
  status: string
  capacityLimit: string
  logicalVolumeMaxSize: string
  dhchap: boolean
  allowedNodes:
    - string
  qos:
    iops: integer
    throughput:
      read: integer
      readWrite: integer
      write: integer
  action: string
  storageClassParameters:
    qosRwIops: string
    qosRwMbytes: string
    qosRMbytes: string
    qosWMbytes: string
    encryption: boolean
    fabric: string
    maxNamespacePerSubsys: string
    tune2fsReservedBlocks: string
    filesystem: string
status:
  uuid: string
  status: string
  qos:
    host: string
    iops: integer
    throughput:
      read: integer
      readWrite: integer
      write: integer
  allowedNodes:
    - string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha1` | | |
| `kind` _string_ | `StoragePool` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  | Optional: \{\} <br /> |
| `spec` _[StoragePoolSpec](#storagepoolspec)_ | spec defines the desired state of StoragePool |  | Required: \{\} <br /> |
| `status` _[StoragePoolStatus](#storagepoolstatus)_ | status defines the observed state of StoragePool |  | Optional: \{\} <br /> |


#### StoragePoolQoSSpec



StoragePoolQoSSpec defines pool QosSpec limits.



_Appears in:_
- [StoragePoolSpec](#storagepoolspec)

_Example:_

```yaml
iops: integer
throughput:
  read: integer
  readWrite: integer
  write: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `iops` _integer_ | IOPS is the IOPS limit for the pool. |  |  |
| `throughput` _[StoragePoolQoSThroughputSpec](#storagepoolqosthroughputspec)_ | Throughput contains throughput limits for the pool. |  |  |


#### StoragePoolQoSStatus



StoragePoolQoSStatus defines observed pool QosSpec values.



_Appears in:_
- [StoragePoolStatus](#storagepoolstatus)

_Example:_

```yaml
host: string
iops: integer
throughput:
  read: integer
  readWrite: integer
  write: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `host` _string_ | Host is the backend host handling pool QosSpec enforcement. |  |  |
| `iops` _integer_ | IOPS is the observed/configured IOPS value. |  |  |
| `throughput` _[StoragePoolQoSThroughputStatus](#storagepoolqosthroughputstatus)_ | Throughput contains observed/configured throughput values. |  |  |


#### StoragePoolQoSThroughputSpec



StoragePoolQoSThroughputSpec defines throughput QosSpec limits in MiB/s.



_Appears in:_
- [StoragePoolQoSSpec](#storagepoolqosspec)

_Example:_

```yaml
read: integer
readWrite: integer
write: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `read` _integer_ | Read is the read throughput limit for the pool. |  |  |
| `readWrite` _integer_ | ReadWrite is the combined read/write throughput limit for the pool. |  |  |
| `write` _integer_ | Write is the write throughput limit for the pool. |  |  |


#### StoragePoolQoSThroughputStatus



StoragePoolQoSThroughputStatus defines observed throughput QosSpec values in MiB/s.



_Appears in:_
- [StoragePoolQoSStatus](#storagepoolqosstatus)

_Example:_

```yaml
read: integer
readWrite: integer
write: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `read` _integer_ | Read is the observed/configured read throughput value. |  |  |
| `readWrite` _integer_ | ReadWrite is the observed/configured combined read/write throughput value. |  |  |
| `write` _integer_ | Write is the observed/configured write throughput value. |  |  |


#### StoragePoolSpec



StoragePoolSpec defines the desired state of StoragePool

A pool created with dhchap: true and no allowedNodes could never enforce them: its
StorageClass only gets dhchap_node_selector when allowedNodes is non-empty at creation,
and StorageClass parameters are immutable. Changing a non-empty allowedNodes stays allowed.



_Appears in:_
- [StoragePool](#storagepool)

_Example:_

```yaml
clusterName: string
status: string
capacityLimit: string
logicalVolumeMaxSize: string
dhchap: boolean
allowedNodes:
  - string
qos:
  iops: integer
  throughput:
    read: integer
    readWrite: integer
    write: integer
action: string
storageClassParameters:
  qosRwIops: string
  qosRwMbytes: string
  qosRMbytes: string
  qosWMbytes: string
  encryption: boolean
  fabric: string
  maxNamespacePerSubsys: string
  tune2fsReservedBlocks: string
  filesystem: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `clusterName` _string_ | ClusterName is the target storage cluster name. |  |  |
| `status` _string_ | Status is an optional desired-status hint for backend workflows.<br />FIXME: Unused for now |  |  |
| `capacityLimit` _string_ | CapacityLimit is the maximum aggregate capacity that can be allocated from this pool.<br />This maps to sbctl pool add --pool-max. Use sizes like 20M, 20G, or 0 for unlimited. |  |  |
| `logicalVolumeMaxSize` _string_ | LogicalVolumeMaxSize is the maximum size allowed for any single logical volume<br />created in this pool. This maps to sbctl pool add --lvol-max. Use sizes like<br />20M, 20G, or 0 for unlimited. |  |  |
| `dhchap` _boolean_ | DHCHAP enables DH-HMAC-CHAP key generation for the pool. Authentication is only<br />enforced when allowedNodes is non-empty. Also controls whether the StoragePool's StorageClass<br />gets an allowedTopologies restriction, which — like StorageClass Parameters — is<br />immutable in the Kubernetes API, hence this field is immutable too. | false |  |
| `allowedNodes` _string array_ | AllowedNodes is the list of Kubernetes worker node names allowed to access volumes<br />in this pool. The operator resolves each node name to a deterministic NQN derived<br />from the node's UID: nqn.2014-08.io.simplyblock:uuid:<node-uid>.<br />The CSI node uses the same formula so no manual NQN management is required. |  |  |
| `qos` _[StoragePoolQoSSpec](#storagepoolqosspec)_ | QosSpec defines QosSpec limits for the pool. |  |  |
| `action` _string_ | Action triggers an imperative pool operation.<br />FIXME: Unused for now |  |  |
| `storageClassParameters` _[StorageClassParameters](#storageclassparameters)_ | StorageClassParameters sets default StorageClass parameter values for volumes in this pool.<br />Immutable: the underlying StorageClass's Parameters/AllowedTopologies cannot be patched in<br />the Kubernetes API once created, so there is no supported way to change these after the<br />fact. Create a new StoragePool to provision volumes with different settings. | \{  \} |  |


#### StoragePoolStatus



StoragePoolStatus defines the observed state of StoragePool.



_Appears in:_
- [StoragePool](#storagepool)

_Example:_

```yaml
uuid: string
status: string
qos:
  host: string
  iops: integer
  throughput:
    read: integer
    readWrite: integer
    write: integer
allowedNodes:
  - string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `uuid` _string_ | UUID is the backend pool UUID. |  |  |
| `status` _string_ | Status is the backend lifecycle status. |  |  |
| `qos` _[StoragePoolQoSStatus](#storagepoolqosstatus)_ | QoS contains observed/configured QoS values. |  |  |
| `allowedNodes` _string array_ | AllowedNodes lists the Kubernetes node names currently registered on the backend. |  |  |


#### StripeSpec



StripeSpec is the erasure-coding layout. The rule is the hub type's, declared
here as well because the apiserver validates the version an apply was written
in: a scheme the control plane refuses would otherwise reach the cluster
through this version and be refused by the cluster create instead.



_Appears in:_
- [StorageClusterSpec](#storageclusterspec)

_Example:_

```yaml
dataChunks: integer
parityChunks: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `dataChunks` _integer_ | DataChunks defines the number of data chunks in the erasure-coding layout. |  |  |
| `parityChunks` _integer_ | ParityChunks defines the number of parity chunks in the erasure-coding layout. |  |  |


#### Task



Task is the Schema for the tasks API





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha1
kind: Task
metadata:
  name: string
spec:
  clusterName: string
  taskID: string
  subtasks: boolean
status:
  tasks:
    - uuid: string
      taskType: string
      taskStatus: string
      taskResult: string
      canceled: boolean
      parentTask: string
      startedAt: Time
      retried: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha1` | | |
| `kind` _string_ | `Task` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  | Optional: \{\} <br /> |
| `spec` _[TaskSpec](#taskspec)_ | spec defines the desired state of Task |  | Required: \{\} <br /> |
| `status` _[TaskStatus](#taskstatus)_ | status defines the observed state of Task |  | Optional: \{\} <br /> |


#### TaskEntry







_Appears in:_
- [TaskStatus](#taskstatus)

_Example:_

```yaml
uuid: string
taskType: string
taskStatus: string
taskResult: string
canceled: boolean
parentTask: string
startedAt: Time
retried: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `uuid` _string_ | UUID is the backend task UUID. |  |  |
| `taskType` _string_ | TaskType is the backend task function/type name. |  |  |
| `taskStatus` _string_ | TaskStatus is the backend lifecycle status for the task. |  |  |
| `taskResult` _string_ | TaskResult is the backend result payload/message. |  |  |
| `canceled` _boolean_ | Canceled indicates whether the task was canceled. |  |  |
| `parentTask` _string_ | ParentTask is the parent task UUID when this task is a subtask.<br />FIXME: Unused for now |  |  |
| `startedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | StartedAt is the backend-reported task start timestamp.<br />FIXME: Unused for now |  |  |
| `retried` _integer_ | Retried is the number of retry attempts made for the task. |  |  |


#### TaskSpec



TaskSpec defines the desired state of Task



_Appears in:_
- [Task](#task)

_Example:_

```yaml
clusterName: string
taskID: string
subtasks: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `clusterName` _string_ | ClusterName is the target storage cluster name. |  |  |
| `taskID` _string_ | TaskID filters results to a specific backend task when set. |  |  |
| `subtasks` _boolean_ | Subtasks includes related child subtasks when supported by the backend.<br />FIXME: Unused for now |  |  |


#### TaskStatus



TaskStatus defines the observed state of Task.



_Appears in:_
- [Task](#task)

_Example:_

```yaml
tasks:
  - uuid: string
    taskType: string
    taskStatus: string
    taskResult: string
    canceled: boolean
    parentTask: string
    startedAt: Time
    retried: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `tasks` _[TaskEntry](#taskentry) array_ | Tasks is the currently reported task list for the query scope. |  |  |


#### ValidationJob



ValidationJob is one NVMe path-validation Job and the worker node it runs on.
The node is a consumer of some volume in the migrated subsystem — the volume named
in the spec, or one of its siblings sharing the same NVMe subsystem.



_Appears in:_
- [VolumeMigrationStatus](#volumemigrationstatus)

_Example:_

```yaml
node: string
jobName: string
succeeded: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `node` _string_ | Node is the Kubernetes node name the Job is pinned to. |  |  |
| `jobName` _string_ | JobName is the name of the Job object in the VolumeMigration's namespace. |  |  |
| `succeeded` _boolean_ | Succeeded records that this node's validation passed. It is kept because the<br />Job's own existence is not a reliable record: Jobs are reaped, and re-reading a<br />reaped Job would otherwise look like "never validated" and start it again. |  | Optional: \{\} <br /> |


#### VolumeAutoPlacementSettings



VolumeAutoPlacementSettings controls the automatic, latency-driven volume rebalancing
behavior. It is configured under StorageClusterSpec.VolumeAutoPlacement.



_Appears in:_
- [StorageClusterSpec](#storageclusterspec)

_Example:_

```yaml
enabled: boolean
migrationEnabled: boolean
evaluationInterval: Duration
imbalanceThreshold: integer
minHotColdDifferencePct: integer
defaultCoolDownSeconds: integer
maxVolumeMigrationsPerCycle: integer
storageNodeCandidateCount: integer
metricsBackend: MetricsBackend
prometheusURL: string
latencyBenchmarkEnabled: boolean
latencyBenchmarkInterval: Duration
baselineStrategy: BaselineStrategy
baselineWindow: Duration
baselineColdStart: BaselineColdStartPolicy
baselineMinSamples: integer
baselineOutlierK: float
iopsWeight: float
throughputWeight: float
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `enabled` _boolean_ | Enabled activates automatic rebalancing for this cluster. Defaults to false. |  | Optional: \{\} <br /> |
| `migrationEnabled` _boolean_ | MigrationEnabled controls whether the rebalancer actually creates VolumeMigration<br />CRs. When false the rebalancer still runs every cycle — evaluating load, computing<br />deviations, selecting candidates and emitting metrics — but discards the migrations<br />instead of creating them (dry-run). Defaults to true. |  | Optional: \{\} <br /> |
| `evaluationInterval` _[Duration](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#duration-v1-meta)_ | EvaluationInterval is how often the rebalancer evaluates load. Defaults to 60s. |  | Optional: \{\} <br /> |
| `imbalanceThreshold` _integer_ | ImbalanceThreshold is the minimum latency deviation from baseline (in percent)<br />that a node must exhibit before it is considered a rebalancing source. Defaults to 80. |  | Optional: \{\} <br /> |
| `minHotColdDifferencePct` _integer_ | MinHotColdDifferencePct is the minimum latency-deviation gap (in percentage points)<br />that a candidate target node must be below the hot source node before a migration is<br />performed. Prevents migrating between near-equally loaded nodes. Defaults to 20. |  | Optional: \{\} <br /> |
| `defaultCoolDownSeconds` _integer_ | DefaultCoolDownSeconds is the cool-down period (seconds) applied to a volume after<br />it has been migrated. Defaults to 600. |  | Optional: \{\} <br /> |
| `maxVolumeMigrationsPerCycle` _integer_ | MaxVolumeMigrationsPerCycle is the maximum number of volumes moved per cycle. Defaults to 10. |  | Optional: \{\} <br /> |
| `storageNodeCandidateCount` _integer_ | StorageNodeCandidateCount is the number of top-loaded nodes evaluated each cycle to<br />find the best migration source. Defaults to 3. |  | Optional: \{\} <br /> |
| `metricsBackend` _[MetricsBackend](#metricsbackend)_ | MetricsBackend selects the data source for I/O metrics. Defaults to `prometheus`. |  | Enum: [controlplane prometheus uniform] <br />Optional: \{\} <br /> |
| `prometheusURL` _string_ | PrometheusURL is required when MetricsBackend is `prometheus`. |  | Optional: \{\} <br /> |
| `latencyBenchmarkEnabled` _boolean_ | LatencyBenchmarkEnabled enables fio-based NVMe-oF latency measurement via Kubernetes Jobs.<br />Defaults to false; set to true once a RebalancerImage is configured. |  | Optional: \{\} <br /> |
| `latencyBenchmarkInterval` _[Duration](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#duration-v1-meta)_ | LatencyBenchmarkInterval is how often fio benchmark Jobs run against each storage node.<br />It also sets the step of the rolling-window baseline query (the cadence at which the<br />probe sidecar publishes latency samples). Defaults to 5m. |  | Optional: \{\} <br /> |
| `baselineStrategy` _[BaselineStrategy](#baselinestrategy)_ | BaselineStrategy selects how the per-node latency baseline is derived. Defaults to<br />"rollingWindow" (robust estimate over BaselineWindow of the Prometheus latency series);<br />"benchmark" uses the frozen one-shot fio measurement instead. |  | Enum: [benchmark rollingWindow] <br />Optional: \{\} <br /> |
| `baselineWindow` _[Duration](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#duration-v1-meta)_ | BaselineWindow is the look-back window used by the "rollingWindow" strategy. Defaults to 6h. |  | Optional: \{\} <br /> |
| `baselineColdStart` _[BaselineColdStartPolicy](#baselinecoldstartpolicy)_ | BaselineColdStart selects what happens for a node with fewer than BaselineMinSamples<br />samples in the window. Defaults to "partialWindow" (compute from available samples);<br />"defer" skips the node until enough samples exist. |  | Enum: [defer partialWindow] <br />Optional: \{\} <br /> |
| `baselineMinSamples` _integer_ | BaselineMinSamples is the number of samples below which a node is considered<br />under-sampled (see BaselineColdStart). Defaults to 6. |  | Optional: \{\} <br /> |
| `baselineOutlierK` _float_ | BaselineOutlierK is the Hampel-identifier threshold: a sample is rejected as an outlier<br />when it lies more than k·1.4826·MAD from the window median. Lower is more aggressive.<br />Defaults to 3.0. |  | Optional: \{\} <br /> |
| `iopsWeight` _float_ | IOPSWeight is the weight applied to per-volume IOPS in the volume I/O score. Defaults to 1.0. |  | Optional: \{\} <br /> |
| `throughputWeight` _float_ | ThroughputWeight is the weight applied to per-volume throughput (MB/s) in the volume<br />I/O score. Defaults to 0.1. |  | Optional: \{\} <br /> |


#### VolumeMigration



VolumeMigration triggers a storage-node migration for a single PersistentVolume.
Create a VolumeMigration to move a volume's backing logical volume to a different
storage node. The controller resolves the PV to a logical volume UUID, submits the
migration via the storage API, and tracks progress until completion or failure.
Set spec.abort=true to cancel an in-progress migration.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha1
kind: VolumeMigration
metadata:
  name: string
spec:
  pvName: string
  targetNodeUUID: string
  abort: boolean
status:
  phase: VolumeMigrationPhase
  migrationUUID: string
  clusterUUID: string
  volumeUUID: string
  poolUUID: string
  subsystemNQN: string
  sourceNodeUUID: string
  memberCount: integer
  errorMessage: string
  connections:
    - nqn: string
      ip: string
      port: integer
      transport: string
      nrIoQueues: integer
      reconnectDelay: integer
      ctrlLossTmo: integer
      fastIOFailTmo: integer
      keepAliveTmo: integer
  validationJobs:
    - node: string
      jobName: string
      succeeded: boolean
  deferredSince: Time
  startedAt: Time
  completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha1` | | |
| `kind` _string_ | `VolumeMigration` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  |  |
| `spec` _[VolumeMigrationSpec](#volumemigrationspec)_ |  |  |  |
| `status` _[VolumeMigrationStatus](#volumemigrationstatus)_ |  |  |  |


#### VolumeMigrationPhase

_Underlying type:_ _string_

VolumeMigrationPhase describes the lifecycle state of a VolumeMigration.



_Appears in:_
- [VolumeMigrationStatus](#volumemigrationstatus)

| Field | Description |
| --- | --- |
| `Pending` | VolumeMigrationPhasePending means the migration has been accepted but not<br />yet submitted to the storage API.<br /> |
| `Validating` | VolumeMigrationPhaseValidating means CreateMigration has been called and<br />the operator is validating the new NVMe-oF connection paths on the target<br />node before calling ContinueMigration.<br /> |
| `Running` | VolumeMigrationPhaseRunning means ContinueMigration has been called and<br />the data migration is in progress.<br /> |
| `Completed` | VolumeMigrationPhaseCompleted means the migration finished successfully.<br /> |
| `Failed` | VolumeMigrationPhaseFailed means the migration finished with an error.<br /> |
| `Aborted` | VolumeMigrationPhaseAborted means the migration was cancelled via spec.abort.<br /> |


#### VolumeMigrationSettings



VolumeMigrationSettings carries cluster-level settings for volume migration.
Automatic load-based rebalancing is configured separately via
StorageClusterSpec.VolumeAutoPlacement, keeping the manual-migration controls
separate from the rebalancing policy.



_Appears in:_
- [StorageClusterSpec](#storageclusterspec)

_Example:_

```yaml
enabled: boolean
rebalancerImage: string
dataRealignment:
  enabled: boolean
  interval: Duration
  minMoves: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `enabled` _boolean_ | Enabled turns on volume migration for this cluster. When false, the operator<br />will not act on VolumeMigration resources for this cluster. Defaults to true. |  | Optional: \{\} <br /> |
| `rebalancerImage` _string_ | RebalancerImage is the container image used for the volume-migration path<br />validation Job and the rebalancer latency/baseline Jobs. The image must include<br />nvme-cli (and, for rebalancing, fio + jq). |  | Optional: \{\} <br /> |
| `dataRealignment` _[DataRealignmentSettings](#datarealignmentsettings)_ | DataRealignment configures the periodic control-plane data realignment that<br />runs after volumes have been moved. Realignment re-aligns the cluster's internal<br />data structures to the current volume placement so fault-tolerance (FTT) and<br />node-affinity guarantees are preserved. It applies to *all* volume moves —<br />auto-rebalancing, manual VolumeMigrations, and drain/removal-triggered moves —<br />so it lives here rather than under AutoRebalancing. Enabled by default. |  | Optional: \{\} <br /> |


#### VolumeMigrationSpec



VolumeMigrationSpec defines the desired state of a VolumeMigration.



_Appears in:_
- [VolumeMigration](#volumemigration)

_Example:_

```yaml
pvName: string
targetNodeUUID: string
abort: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `pvName` _string_ | PVName is the name of the PersistentVolume whose backing logical volume<br />should be migrated. The PV must be provisioned by the simplyblock CSI driver. |  | MinLength: 1 <br /> |
| `targetNodeUUID` _string_ | TargetNodeUUID is the UUID of the storage node that should host the<br />volume after migration. |  | MinLength: 1 <br /> |
| `abort` _boolean_ | Abort requests cancellation of an in-progress migration. Set to true to<br />cancel; the phase will transition to Aborted once the backend confirms. |  | Optional: \{\} <br /> |


#### VolumeMigrationStatus



VolumeMigrationStatus defines the observed state of a VolumeMigration.



_Appears in:_
- [VolumeMigration](#volumemigration)

_Example:_

```yaml
phase: VolumeMigrationPhase
migrationUUID: string
clusterUUID: string
volumeUUID: string
poolUUID: string
subsystemNQN: string
sourceNodeUUID: string
memberCount: integer
errorMessage: string
connections:
  - nqn: string
    ip: string
    port: integer
    transport: string
    nrIoQueues: integer
    reconnectDelay: integer
    ctrlLossTmo: integer
    fastIOFailTmo: integer
    keepAliveTmo: integer
validationJobs:
  - node: string
    jobName: string
    succeeded: boolean
deferredSince: Time
startedAt: Time
completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _[VolumeMigrationPhase](#volumemigrationphase)_ | Phase is the current lifecycle phase of the migration. |  | Enum: [Pending Validating Running Completed Failed Aborted] <br /> |
| `migrationUUID` _string_ | MigrationUUID is the identifier returned by the storage API when the<br />migration was submitted. Used for polling and cancellation. |  |  |
| `clusterUUID` _string_ | ClusterUUID is the storage cluster UUID resolved from the PV. |  |  |
| `volumeUUID` _string_ | VolumeUUID is the logical volume UUID resolved from the PV's CSI volume handle. |  |  |
| `poolUUID` _string_ | PoolUUID is the storage pool UUID that contains the volume. |  |  |
| `subsystemNQN` _string_ | SubsystemNQN is the NQN of the volume's NVMe subsystem, resolved from the<br />storage API when the migration is submitted. The migration is addressed by<br />it, and every volume sharing the subsystem moves with it. |  |  |
| `sourceNodeUUID` _string_ | SourceNodeUUID is the storage node UUID where the volume resided before<br />migration, as reported by the storage API. |  |  |
| `memberCount` _integer_ | MemberCount is the number of volumes (namespaces) in the migrated<br />subsystem, as reported by the storage API. More than one means the<br />migration moves sibling volumes along with this one. |  |  |
| `errorMessage` _string_ | ErrorMessage holds the failure reason when Phase is Failed. |  |  |
| `connections` _[MigrationConnection](#migrationconnection) array_ | Connections holds the NVMe-oF connection parameters for the new target-side<br />paths returned by CreateMigration. Used during the Validating phase to<br />establish and verify the paths before calling ContinueMigration, and again to<br />release them if the migration never cuts over.<br />These are the parameters the paths are actually connected with, not verbatim<br />what CreateMigration answered: ctrlLossTmo is replaced with the value every<br />path in this system uses, because a target path becomes the volume's data path<br />at cutover. The rest is passed through. |  |  |
| `validationJobs` _[ValidationJob](#validationjob) array_ | ValidationJobs are the Jobs that run `nvme connect` for each connection path<br />and validate ANA state before ContinueMigration is called — one per worker<br />node that consumes a volume of the migrated subsystem. A subsystem migrates<br />as a unit, so every consuming node must have the new paths before cutover;<br />all of these Jobs must succeed. Set during the Validating phase; cleared when<br />the phase advances to Running. |  |  |
| `deferredSince` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | DeferredSince is when the storage API first refused to accept this migration<br />because the cluster was busy with work that ends on its own (a data realignment<br />or another node migration). While set, the migration is being retried and has<br />not started. It bounds the retrying: past a fixed window the migration fails<br />rather than waiting forever. Cleared once the migration is submitted. |  |  |
| `startedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | StartedAt is the time the migration was submitted to the storage API. |  |  |
| `completedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | CompletedAt is the time the migration finished (successfully or not). |  |  |



## storage.simplyblock.io/v1alpha2

Package v1alpha2 is the storage version of the simplyblock API group and the
shape every controller reads. It holds two kinds of type, which differ in
whether anything converts into them.

A kind the CRD redesign renamed a property on has a v1alpha1 spoke: this
package declares the settled names, v1alpha1 keeps the names that shipped, and
the conversion webhook translates between them, so no reconciler has to know
that an older spelling exists. Those types implement conversion.Hub and
nothing else; the spoke side lives beside the older types, in
api/v1alpha1/*_conversion.go, and
operator/docs/designs/crd-redesign/design-property-renames.md is the inventory
of what moved and why.

A kind the redesign introduces has no spoke and needs no Hub: it was never
published under v1alpha1, so there is no older shape to convert from and its
CRD declares one version.


### Resource Types
- [ClusterDeploymentConfig](#clusterdeploymentconfig)
- [ControlPlane](#controlplane)
- [ControlPlaneOps](#controlplaneops)
- [OperatorOps](#operatorops)
- [PersistentVolumeOps](#persistentvolumeops)
- [SimplyblockDriver](#simplyblockdriver)
- [StorageBackup](#storagebackup)
- [StorageBackupOps](#storagebackupops)
- [StorageBackupPolicy](#storagebackuppolicy)
- [StorageCluster](#storagecluster)
- [StorageClusterOps](#storageclusterops)
- [StorageDevice](#storagedevice)
- [StorageDeviceOps](#storagedeviceops)
- [StorageNode](#storagenode)
- [StorageNodeOps](#storagenodeops)
- [StoragePool](#storagepool)
- [StoragePoolOps](#storagepoolops)
- [VolumeGroupSnapshotOps](#volumegroupsnapshotops)



#### AttachedClaim



AttachedClaim is one claim the policy currently covers, in Kubernetes terms
rather than in the control plane's.



_Appears in:_
- [StorageBackupPolicyStatus](#storagebackuppolicystatus)

_Example:_

```yaml
name: string
persistentVolumeName: string
lvolID: string
attachedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `name` _string_ | Name is the PersistentVolumeClaim's name in this namespace. |  | Required: \{\} <br /> |
| `persistentVolumeName` _string_ | PersistentVolumeName is the volume behind it. |  | Optional: \{\} <br /> |
| `lvolID` _string_ | LvolID is the logical volume the control plane attached the policy to. It<br />is what a detach addresses, and it is recorded per claim so that a claim<br />rebound onto a new volume is detached from the old one rather than<br />silently left attached. |  | Optional: \{\} <br /> |
| `attachedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | AttachedAt is when the claim started matching the selector. |  | Optional: \{\} <br /> |


#### BackupCopy



BackupCopy is the copy itself: what it is, what it cost, and what it depends
on.



_Appears in:_
- [StorageBackupStatus](#storagebackupstatus)

_Example:_

```yaml
backupID: string
s3ID: integer
size: integer
previousBackupID: string
startedAt: Time
completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `backupID` _string_ | BackupID is the control plane's identifier for the copy. |  | Optional: \{\} <br /> |
| `s3ID` _integer_ | S3ID is the object behind the copy in the store. The appendix does not<br />list it and §5.2 names it, and it is what somebody reconciling a bill<br />against a bucket listing matches on. |  | Optional: \{\} <br /> |
| `size` _integer_ | Size is the copy's size in bytes, which is what a bill tracks. |  | Minimum: 0 <br />Optional: \{\} <br /> |
| `previousBackupID` _string_ | PreviousBackupID names the backup this one is incremental against, where<br />the control plane reports one. It makes the chain legible, which matters<br />because deleting a backup another depends on is not obviously safe. |  | Optional: \{\} <br /> |
| `startedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | StartedAt and CompletedAt bound how long the copy took. They are the<br />backup's own reported interval rather than transitions the operator<br />observed, because the stream coalesces and a small backup can be complete<br />before the operator ever saw it start. |  | Optional: \{\} <br /> |
| `completedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ |  |  | Optional: \{\} <br /> |


#### BackupSource



BackupSource is what the volume was when the copy was taken. It is written
once and never updated: the pool a volume was in when it was backed up is a
fact about the backup, and rewriting it when the volume moves would destroy
the only record of where the data came from. A restore reads it to know what
it is restoring.



_Appears in:_
- [StorageBackupStatus](#storagebackupstatus)

_Example:_

```yaml
claimName: string
claimNamespace: string
persistentVolumeName: string
poolName: string
poolUUID: string
lvolID: string
lvolName: string
fsType: string
snapshotID: string
snapshotName: string
nodeID: string
clusterUUID: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `claimName` _string_ | ClaimName and ClaimNamespace are the PersistentVolumeClaim the copy was<br />taken from. They are the pair a user recognizes, and the reason the claim<br />rather than the volume is the printed column. |  | Optional: \{\} <br /> |
| `claimNamespace` _string_ |  |  | Optional: \{\} <br /> |
| `persistentVolumeName` _string_ | PersistentVolumeName is the PV that was copied. |  | Optional: \{\} <br /> |
| `poolName` _string_ | PoolName and PoolUUID are the StoragePool the volume was in. A restore<br />names its own target pool rather than defaulting to this one, because a<br />backup discovered from a shared store may name a pool this cluster does<br />not have. |  | Optional: \{\} <br /> |
| `poolUUID` _string_ |  |  | Optional: \{\} <br /> |
| `lvolID` _string_ | LvolID and LvolName identify the logical volume that was copied. |  | Optional: \{\} <br /> |
| `lvolName` _string_ |  |  | Optional: \{\} <br /> |
| `fsType` _string_ | FSType is the filesystem the volume was formatted with, which a restore<br />needs in order to produce a mountable claim. |  | Optional: \{\} <br /> |
| `snapshotID` _string_ | SnapshotID and SnapshotName identify the snapshot the backup was taken<br />from. |  | Optional: \{\} <br /> |
| `snapshotName` _string_ |  |  | Optional: \{\} <br /> |
| `nodeID` _string_ | NodeID is the storage node the copy was read from. The appendix does not<br />list it and §1 counts it among the twenty-two, and it belongs to the<br />source rather than to the copy: it says which machine held the data, which<br />is what somebody correlating a backup against a node failure needs. |  | Optional: \{\} <br /> |
| `clusterUUID` _string_ | ClusterUUID is the cluster the volume lived in, which differs from the<br />backup's own cluster when another cluster wrote it. |  | Optional: \{\} <br /> |


#### BackupSpec



BackupSpec parameterizes the Backup action and is ignored by the others.



_Appears in:_
- [ControlPlaneOpsSpec](#controlplaneopsspec)

_Example:_

```yaml
blobStore: string
backupName: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `blobStore` _string_ | BlobStore is the destination, in the form the FoundationDBBackup CRD takes<br />it. The operator copies it through rather than interpreting it, since the<br />backup is the FoundationDB operator's to perform. |  | Required: \{\} <br /> |
| `backupName` _string_ | BackupName is the FoundationDBBackup to create or trigger. Absent uses the<br />one already configured for the cluster, and fails when there is none and<br />no name to create. |  | Optional: \{\} <br /> |


#### BackupStoreSpec



BackupStoreSpec is the S3 location a cluster's backups live in, and the
credentials to reach it. It is a location and nothing else: how backups are
taken and what they contain are the control plane's, and this block only says
where they go. It is both the target copies are written to and the inventory
the operator walks to produce StorageBackup objects.

The whole block is mutable. A cluster can be created without a store and
given one later, and what changes when it changes is which backups have
objects, since the object set is derived from the location rather than
accumulated.



_Appears in:_
- [ClusterTemplate](#clustertemplate)
- [StorageClusterSpec](#storageclusterspec)

_Example:_

```yaml
endpoint: '^https?://[a-zA-Z0-9.-]+(:[0-9]{1,5})?(/.*)?$'
bucket: string
prefix: string
region: string
credentialsSecretRef: LocalObjectReference
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `endpoint` _string_ | Endpoint is the S3 endpoint, for example, https://s3.example.com. |  | Pattern: `^https?://[a-zA-Z0-9.-]+(:[0-9]\{1,5\})?(/.*)?$` <br />Required: \{\} <br /> |
| `bucket` _string_ | Bucket is the bucket backups are written to and read from. |  | Required: \{\} <br /> |
| `prefix` _string_ | Prefix narrows the store to one key prefix, so that several clusters can<br />share a bucket without each walking the others' backups. |  | Optional: \{\} <br /> |
| `region` _string_ | Region is the bucket's region, for endpoints that do not imply one. |  | Optional: \{\} <br /> |
| `credentialsSecretRef` _[LocalObjectReference](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#localobjectreference-v1-core)_ | CredentialsSecretRef names the Secret holding the access key and the<br />secret key. It is a reference rather than the values, because a spec is<br />readable by anybody who can read the object. |  | Required: \{\} <br /> |


#### BaselineColdStartPolicy

_Underlying type:_ _string_

BaselineColdStartPolicy selects what happens to a node with fewer than
BaselineMinSamples samples in the window: a freshly onboarded node, or one
whose probe sidecar has just started.

_Validation:_
- Enum: [Defer PartialWindow]

_Appears in:_
- [VolumeAutoPlacementSettings](#volumeautoplacementsettings)

| Field | Description |
| --- | --- |
| `Defer` | BaselineColdStartDefer omits an under-sampled node from the cycle: it is<br />neither a migration source nor a target until it has accumulated enough<br />samples, which avoids acting on a noisy baseline.<br /> |
| `PartialWindow` | BaselineColdStartPartialWindow computes the baseline from whatever<br />samples exist, accepting a noisier baseline early on so that rebalancing<br />engages sooner. It is the default.<br /> |


#### BaselineStrategy

_Underlying type:_ _string_

BaselineStrategy selects how the per-node latency baseline, the denominator
of the rebalancing deviation signal, is derived.

_Validation:_
- Enum: [Benchmark RollingWindow]

_Appears in:_
- [VolumeAutoPlacementSettings](#volumeautoplacementsettings)

| Field | Description |
| --- | --- |
| `Benchmark` | BaselineStrategyBenchmark uses the one-shot fio measurement taken on a<br />fresh cluster and frozen on the node's status. It is simple and tends to<br />read too low, because an idle cluster is far faster than a loaded one and<br />every loaded node then shows a large deviation.<br /> |
| `RollingWindow` | BaselineStrategyRollingWindow derives the baseline from a rolling window<br />of the probe sidecar's latency series, using an outlier-rejecting<br />estimator. It reflects each node's recent operating latency rather than<br />an idle measurement, and is the default.<br /> |


#### CancelTaskSpec



CancelTaskSpec parameterizes the CancelTask action.



_Appears in:_
- [StorageClusterOpsSpec](#storageclusteropsspec)

_Example:_

```yaml
taskID: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `taskID` _string_ | TaskID names the entry of StorageCluster.status.tasks to cancel, by the<br />control plane's identifier for it rather than by its position in the<br />list. |  | Required: \{\} <br /> |


#### CapacityThresholdSpec



CapacityThresholdSpec is one capacity alarm level, as a figure for used
capacity and one for provisioned capacity.



_Appears in:_
- [StorageClusterSpec](#storageclusterspec)

_Example:_

```yaml
capacity: integer
provisionedCapacity: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `capacity` _integer_ | Capacity is the used-capacity threshold. |  | Optional: \{\} <br /> |
| `provisionedCapacity` _integer_ | ProvisionedCapacity is the provisioned-capacity threshold. |  | Optional: \{\} <br /> |


#### ClusterDeploymentConfig



ClusterDeploymentConfig is a whole simplyblock deployment written down as one
reviewable document: the environment, the cluster, and the node sets with
their workers, interfaces, and devices. An administrator reviews it, approves
it, and the operator expands it into a StorageCluster and its StorageNodes.

It is ephemeral. Everything the expansion produces is self-describing, so the
document can be edited or deleted once it has been expanded, and nothing reads
it afterward.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha2
kind: ClusterDeploymentConfig
metadata:
  name: string
spec:
  approved: boolean
  environment: KubernetesEnvironment
  hostOS:
    distro: '^[a-z0-9][a-z0-9._-]*$'
    family: HostOSFamily
  edgeCluster: boolean
  clusterRef: string
  cluster:
    name: string
    maxSubsystemCount: integer
    vcpuCount: integer
    minHugePagesSize: string
    enableDriveFormat: boolean
    enableJournalDevice: boolean
    socketsToUse:
      - string
    nodesPerSocket: integer
    initContainerResources: ResourceRequirements
    tolerations:
      - Toleration
    containerResources: ResourceRequirements
    nodeProvisioningBudget: integer
    enableChecksumValidation: boolean
    enableAtomicity4K: boolean
    stripe:
      dataChunks: integer
      parityChunks: integer
    fabricType: string
    openshift:
      machineConfigPool: '^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
    ports:
      nvmf: integer
      rpc: integer
      nodeAgent: integer
    enableFailureDomains: boolean
    enableNodeAffinity: boolean
    backup:
      endpoint: '^https?://[a-zA-Z0-9.-]+(:[0-9]{1,5})?(/.*)?$'
      bucket: string
      prefix: string
      region: string
      credentialsSecretRef: LocalObjectReference
    kms:
      vault:
        endpoint: '^https?://[a-zA-Z0-9.-]+(:[0-9]{1,5})?(/.*)?$'
  images:
    nodeAgent:
      image: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
      imagePullPolicy: PullPolicy
    spdk:
      image: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
      imagePullPolicy: PullPolicy
    spdkProxy:
      image: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
      imagePullPolicy: PullPolicy
  nodeSets:
    - name: string
      groups:
        - name: string
          workers:
            - string
          mgmtInterface: string
          dataInterfaces:
            - string
          devices:
            nvme:
              - '^[0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F]$'
            block:
              - '^/dev/[a-zA-Z0-9._/-]+$'
          failureDomain: '^[a-zA-Z0-9]([-_.a-zA-Z0-9]*[a-zA-Z0-9])?$'
          spdkSystemMemory: '^[0-9]+(G|GI|GB|GiB|M|MI|MB|MiB|g|gi|gb|gib|m|mi|mb|mib)?$'
          reservedSystemCPU: '^[0-9]+(-[0-9]+)?(,[0-9]+(-[0-9]+)?)*$'
          journalManager:
            count: integer
            percentPerDevice: integer
status:
  phase: ClusterDeploymentConfigPhase
  step: KubeSnapshot
  clusterRef: string
  nodeRefs:
    - string
  message: string
  observedGeneration: integer
  expansionStartedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha2` | | |
| `kind` _string_ | `ClusterDeploymentConfig` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  |  |
| `spec` _[ClusterDeploymentConfigSpec](#clusterdeploymentconfigspec)_ |  |  |  |
| `status` _[ClusterDeploymentConfigStatus](#clusterdeploymentconfigstatus)_ |  |  |  |


#### ClusterDeploymentConfigPhase

_Underlying type:_ _string_

ClusterDeploymentConfigPhase is where the operator has got to with this
document.

_Validation:_
- Enum: [Draft Expanding Expanded Failed]

_Appears in:_
- [ClusterDeploymentConfigStatus](#clusterdeploymentconfigstatus)

| Field | Description |
| --- | --- |
| `Draft` | ClusterDeploymentConfigPhaseDraft is an unapproved document. It is<br />validated on every reconcile and expanded on none.<br /> |
| `Expanding` | ClusterDeploymentConfigPhaseExpanding is an approved document being<br />turned into a cluster and its nodes.<br /> |
| `Expanded` | ClusterDeploymentConfigPhaseExpanded is a document whose objects exist.<br /> |
| `Failed` | ClusterDeploymentConfigPhaseFailed is a document the expansion refused or<br />could not finish.<br /> |


#### ClusterDeploymentConfigSpec



ClusterDeploymentConfigSpec is a whole simplyblock deployment as one
reviewable document.

The third rule is the device class one. A document describes one cluster and a
cluster is built out of one class of backend storage, so every group of every
node set names the same member of its DeviceSelection. The expansion reads the
class off them and stamps it onto the cluster it creates, which is why the
document carries no field for it.



_Appears in:_
- [ClusterDeploymentConfig](#clusterdeploymentconfig)

_Example:_

```yaml
approved: boolean
environment: KubernetesEnvironment
hostOS:
  distro: '^[a-z0-9][a-z0-9._-]*$'
  family: HostOSFamily
edgeCluster: boolean
clusterRef: string
cluster:
  name: string
  maxSubsystemCount: integer
  vcpuCount: integer
  minHugePagesSize: string
  enableDriveFormat: boolean
  enableJournalDevice: boolean
  socketsToUse:
    - string
  nodesPerSocket: integer
  initContainerResources: ResourceRequirements
  tolerations:
    - Toleration
  containerResources: ResourceRequirements
  nodeProvisioningBudget: integer
  enableChecksumValidation: boolean
  enableAtomicity4K: boolean
  stripe:
    dataChunks: integer
    parityChunks: integer
  fabricType: string
  openshift:
    machineConfigPool: '^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
  ports:
    nvmf: integer
    rpc: integer
    nodeAgent: integer
  enableFailureDomains: boolean
  enableNodeAffinity: boolean
  backup:
    endpoint: '^https?://[a-zA-Z0-9.-]+(:[0-9]{1,5})?(/.*)?$'
    bucket: string
    prefix: string
    region: string
    credentialsSecretRef: LocalObjectReference
  kms:
    vault:
      endpoint: '^https?://[a-zA-Z0-9.-]+(:[0-9]{1,5})?(/.*)?$'
images:
  nodeAgent:
    image: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
    imagePullPolicy: PullPolicy
  spdk:
    image: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
    imagePullPolicy: PullPolicy
  spdkProxy:
    image: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
    imagePullPolicy: PullPolicy
nodeSets:
  - name: string
    groups:
      - name: string
        workers:
          - string
        mgmtInterface: string
        dataInterfaces:
          - string
        devices:
          nvme:
            - '^[0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F]$'
          block:
            - '^/dev/[a-zA-Z0-9._/-]+$'
        failureDomain: '^[a-zA-Z0-9]([-_.a-zA-Z0-9]*[a-zA-Z0-9])?$'
        spdkSystemMemory: '^[0-9]+(G|GI|GB|GiB|M|MI|MB|MiB|g|gi|gb|gib|m|mi|mb|mib)?$'
        reservedSystemCPU: '^[0-9]+(-[0-9]+)?(,[0-9]+(-[0-9]+)?)*$'
        journalManager:
          count: integer
          percentPerDevice: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `approved` _boolean_ | Approved is the review gate. A document is expanded only once it is set,<br />and is validated but otherwise inert before that, which is what makes<br />reviewing a wrong document safe.<br />It is defaulted and serialized rather than omitted when false, and the<br />two are the same requirement read twice. A reviewer has to see the gate<br />they are being asked to open, and the rules above have to find the field<br />they read: a bool omitted when false is a key the apiserver never stores,<br />so a rule reading it fails rather than reading false, and the first rule<br />guarding approval denied every approval there could ever be. The has()<br />guards are what carry documents written before the default existed. | false | Optional: \{\} <br /> |
| `environment` _[KubernetesEnvironment](#kubernetesenvironment)_ | Environment is the Kubernetes distribution this deployment targets. It is a<br />shorthand the expansion spends: it sets enableKubeletConfiguration,<br />enableCpuTopology, and openShiftCluster on the cluster the document<br />produces, after which nothing reads it again. The worker's host OS is not<br />among them and is stated in hostOS, because a distribution decides what<br />Kubernetes does to a machine and not which packages the machine has. |  | Enum: [Vanilla OpenShift Rancher K3s Talos] <br />Optional: \{\} <br /> |
| `hostOS` _[HostOSSpec](#hostosspec)_ | HostOS is the operating system the workers run, which decides what the<br />host itself offers rather than what Kubernetes does to it. The expansion<br />spends the distro on StorageCluster.spec.storageNodes.ubuntuHost and<br />carries the family for the reviewer reading the document. |  | Optional: \{\} <br /> |
| `edgeCluster` _boolean_ | EdgeCluster states that this is an edge deployment. An edge deployment<br />differs from a datacenter one in topology and scale rather than in kind,<br />so it is the same StorageCluster with fewer, smaller nodes. |  | Optional: \{\} <br /> |
| `clusterRef` _string_ | ClusterRef names an existing StorageCluster this document adds nodes to.<br />Absent means the document creates the cluster in Cluster. Setting it to a<br />cluster that does not exist, or leaving it absent when one already does,<br />is refused rather than reconciled.<br />The maximum is what a StorageCluster name may be and not the 253 an object<br />name may be: a reference between the two names nothing that can exist<br />(design-api-upgrade.md §19.4). |  | MaxLength: 63 <br />Optional: \{\} <br /> |
| `cluster` _[ClusterTemplate](#clustertemplate)_ | Cluster is the StorageCluster to create. Ignored when ClusterRef is set. |  | Optional: \{\} <br /> |
| `images` _[DeploymentImages](#deploymentimages)_ | Images are the container images this deployment pins. Unstated, each field<br />the expansion would write keeps its own default. |  | Optional: \{\} <br /> |
| `nodeSets` _[NodeSet](#nodeset) array_ | NodeSets are the nodes the deployment is made of.<br />The upper bound is what makes the device-class rule above estimable: the<br />API server costs a CEL rule against the largest value the schema permits,<br />and a list with no bound is costed as unbounded, which the rule's nested<br />all() then multiplies past the budget. |  | MaxItems: 64 <br />MinItems: 1 <br />Required: \{\} <br /> |


#### ClusterDeploymentConfigStatus



ClusterDeploymentConfigStatus is the observed state of the document.



_Appears in:_
- [ClusterDeploymentConfig](#clusterdeploymentconfig)

_Example:_

```yaml
phase: ClusterDeploymentConfigPhase
step: KubeSnapshot
clusterRef: string
nodeRefs:
  - string
message: string
observedGeneration: integer
expansionStartedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _[ClusterDeploymentConfigPhase](#clusterdeploymentconfigphase)_ | Phase is the operator's own view of the document. |  | Enum: [Draft Expanding Expanded Failed] <br />Optional: \{\} <br /> |
| `step` _[KubeSnapshot](https://github.com/simplyblock/simplyblock-operator/blob/main/atlas-lib/statemachine/kubernetes.go)_ | Step is the position of the expansion machine within Expanding. |  | Optional: \{\} <br /> |
| `clusterRef` _string_ | ClusterRef names the StorageCluster the expansion produced or added to. It<br />is a record rather than a dependency: nothing resolves it after expansion,<br />which is what makes the document safe to delete. |  | Optional: \{\} <br /> |
| `nodeRefs` _string array_ | NodeRefs names the StorageNode objects the expansion created, for the same<br />reason. |  | Optional: \{\} <br /> |
| `message` _string_ | Message is the reason the phase is what it is: one sentence, replaced as<br />the document moves, and never a log. On a Draft it is what validation<br />found, which is what a reviewer reads before approving. |  | Optional: \{\} <br /> |
| `observedGeneration` _integer_ | ObservedGeneration is the generation the rest of this status was computed<br />from, so a stale status can be told from a current one. |  | Optional: \{\} <br /> |
| `expansionStartedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | ExpansionStartedAt is when the expansion machine was born, which is the<br />first reconcile after the document was approved. A document may sit as a<br />draft for as long as a review takes, so this is not creationTimestamp and<br />the difference is the whole point: how long a deployment takes is measured<br />from the moment somebody said yes.<br />It is the start of §9.2's expansion_duration_seconds. A histogram needs an<br />instant that survives the operator restarting mid-expansion, which nothing<br />in memory and no step deadline supplies. |  | Optional: \{\} <br /> |




#### ClusterPortsSpec



ClusterPortsSpec is where a cluster's storage nodes listen.

The three are one block here and three fields on the StorageCluster, which is
the one place the document deliberately does not mirror the cluster's shape.
They are the same decision taken once — which ports this deployment's nodes
bind — and a reviewer reads them together or not at all, where the cluster
carries them flat because that is what shipped.

Every member is immutable on the cluster: a node binds its ports when it
starts and the control plane hands them out from the bases it was given at
cluster create, so the document is the only place any of them can be stated.

Each carries the control plane's own default, so a document that names the
block shows a reviewer the three numbers a cluster will actually run with
rather than three blanks they would have to know the backend to fill in.



_Appears in:_
- [ClusterTemplate](#clustertemplate)

_Example:_

```yaml
nvmf: integer
rpc: integer
nodeAgent: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `nvmf` _integer_ | NVMf is the base of the NVMe-oF port range every node binds. It expands<br />into StorageCluster.spec.nvmfBasePort. | 4420 | Maximum: 65535 <br />Minimum: 1024 <br />Optional: \{\} <br /> |
| `rpc` _integer_ | Rpc is the base of the RPC port range every node binds. It expands into<br />StorageCluster.spec.rpcBasePort. | 8080 | Maximum: 65535 <br />Minimum: 1024 <br />Optional: \{\} <br /> |
| `nodeAgent` _integer_ | NodeAgent is the port each node's agent API listens on. It expands into<br />StorageCluster.spec.snodeApiPort, and it is named for the component<br />rather than for that field: the agent is what spec.images.nodeAgent pins<br />and what the storage-node DaemonSet runs. | 50001 | Maximum: 65535 <br />Minimum: 1024 <br />Optional: \{\} <br /> |


#### ClusterTask



ClusterTask is one asynchronous job the control plane is running, as of the
last frame of the task stream. It is a window rather than a record: a task
that reaches a terminal outcome leaves status.tasks, and what remains of it
is an event.

It carries what the control plane's own TaskDTO carries and nothing more.
The design's Appendix A also declares a progress figure and a creation date,
and that schema has neither, so both are absent rather than declared and
never written (design-crd-model.md §7.9). Their absence is what makes the
list's order the control plane's own rather than newest first.



_Appears in:_
- [StorageClusterStatus](#storageclusterstatus)

_Example:_

```yaml
id: string
type: string
status: string
retry: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `id` _string_ | ID is the control plane's identifier, and it is how a CancelTask<br />operation names the task. A position in the list is not an identity,<br />because the next frame may order it differently. |  | Required: \{\} <br /> |
| `type` _string_ | Type is what kind of job it is, in the control plane's own spelling for<br />the reason design-crd-model.md §7.8 gives: the value is the backend's<br />rather than this group's. |  | Optional: \{\} <br /> |
| `status` _string_ | Status is the control plane's own status string, and it is why this entry<br />carries no phase: the operator adds nothing to what the backend reports.<br />Its values are new, running, suspended, and done, of which only the<br />first three appear here. |  | Optional: \{\} <br /> |
| `retry` _integer_ | Retry is how many times the control plane has restarted this task. It is<br />the one number that separates a task that is slow from one that is<br />failing, and it is the closest thing the schema has to progress. |  | Minimum: 0 <br />Optional: \{\} <br /> |


#### ClusterTemplate



ClusterTemplate is the StorageCluster the expansion creates, where it creates
one. It carries the layout fields a cluster cannot change later, so that a
reviewer sees them before the cluster exists rather than after.



_Appears in:_
- [ClusterDeploymentConfigSpec](#clusterdeploymentconfigspec)

_Example:_

```yaml
name: string
maxSubsystemCount: integer
vcpuCount: integer
minHugePagesSize: string
enableDriveFormat: boolean
enableJournalDevice: boolean
socketsToUse:
  - string
nodesPerSocket: integer
initContainerResources: ResourceRequirements
tolerations:
  - Toleration
containerResources: ResourceRequirements
nodeProvisioningBudget: integer
enableChecksumValidation: boolean
enableAtomicity4K: boolean
stripe:
  dataChunks: integer
  parityChunks: integer
fabricType: string
openshift:
  machineConfigPool: '^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
ports:
  nvmf: integer
  rpc: integer
  nodeAgent: integer
enableFailureDomains: boolean
enableNodeAffinity: boolean
backup:
  endpoint: '^https?://[a-zA-Z0-9.-]+(:[0-9]{1,5})?(/.*)?$'
  bucket: string
  prefix: string
  region: string
  credentialsSecretRef: LocalObjectReference
kms:
  vault:
    endpoint: '^https?://[a-zA-Z0-9.-]+(:[0-9]{1,5})?(/.*)?$'
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `name` _string_ | Name is the StorageCluster's name, and is therefore held to what such a<br />name may be rather than to what an object name may be. A longer value is a<br />document the API server accepts and a CreatingCluster step that can never<br />succeed, since the cluster it would write is one the API server refuses<br />(design-api-upgrade.md §19.4). |  | MaxLength: 63 <br />Required: \{\} <br /> |
| `maxSubsystemCount` _integer_ | MaxSubsystemCount is the maximum number of NVMe-oF subsystems each storage<br />node of this cluster serves. Required, because the StorageCluster's own<br />field is, and no StorageNode carries a copy of it. |  | Maximum: 75 <br />Minimum: 10 <br />Required: \{\} <br /> |
| `vcpuCount` _integer_ | VCPUCount is the number of vCPUs allocated to SPDK on each storage node of<br />this cluster. It is stated here and nowhere below, because the control<br />plane assumes it uniform across a cluster's nodes; CreatingNodes copies it<br />into every StorageNode.spec.config.sizing it writes. Required, because the<br />StorageCluster's own field is.<br />The floor is 4 rather than a hardware limit: a node must carry one core<br />beyond this budget for the system, and the control plane's core layout<br />assigns no NVMe-oF poller core at all for a 2-vCPU budget. |  | Minimum: 4 <br />Required: \{\} <br /> |
| `minHugePagesSize` _string_ | MinHugePagesSize is the smallest huge-page allocation each storage node of<br />this cluster makes: 100G or 1T, where a bare number is gigabytes. Like<br />VCPUCount it is the cluster's and is copied onto every node the expansion<br />writes. Omitted, each node uses the computed minimum. |  | MaxLength: 32 <br />Optional: \{\} <br /> |
| `enableDriveFormat` _boolean_ | EnableDriveFormat formats every device the document names before a storage<br />node takes it, which is how a drive carrying anything already is made<br />usable.<br />It says what is wanted rather than how, because the how differs by device<br />class: an NVMe device is formatted to a 4K block size, and a logical block<br />device has its signatures wiped. One field covers both, so a document does<br />not have to know which class the expansion will resolve it to.<br />It is on the document rather than defaulted further down because it is<br />destructive and the document is what somebody approves. A reviewer reading<br />a draft has to see that the drives it lists will be formatted, and be able<br />to strike it before approving; the cluster's own field is immutable once<br />the cluster exists, so a default nobody saw could not be undone either. |  | Optional: \{\} <br /> |
| `enableJournalDevice` _boolean_ | EnableJournalDevice dedicates the smallest NVMe device on each of this<br />deployment's workers to the journal manager, instead of carving a journal<br />partition out of every device.<br />It is here rather than on a node set because it is immutable on the cluster<br />it lands on, for the reason SocketsToUse is: the on-disk layout a fleet was<br />built with is not one a later document can vary. It also costs a drive of<br />capacity per node, which is a trade a reviewer approves rather than one a<br />default makes for them. |  | Optional: \{\} <br /> |
| `socketsToUse` _string array_ | SocketsToUse restricts the deployment to selected NUMA sockets, and empty<br />means socket 0 alone. With NodesPerSocket it decides how many storage nodes<br />each worker runs, so a group of two workers on a two-socket layout expands<br />to four nodes.<br />It is here rather than on a node set because it is immutable on the cluster<br />it lands on: the layout a fleet was built with is not one a later document<br />can vary, and a reviewer should see it before the cluster exists. |  | MaxItems: 16 <br />items:MaxLength: 16 <br />Optional: \{\} <br /> |
| `nodesPerSocket` _integer_ | NodesPerSocket is how many storage nodes run per NUMA socket. See<br />SocketsToUse, which it multiplies. |  | Maximum: 8 <br />Minimum: 1 <br />Optional: \{\} <br /> |
| `initContainerResources` _[ResourceRequirements](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#resourcerequirements-v1-core)_ | InitContainerResources sizes both of the storage node's init containers,<br />and expands into the cluster's own spec.storageNodes.initContainerResources.<br />They are sized apart from the container because they do a different job<br />and are gone before it starts: one writes the node's env file and the<br />other runs node_configure.py once, so what they need is a short burst<br />rather than the footprint of a process that runs for the node's life.<br />Stating either half replaces both, as with containerResources, and it is<br />a pointer for the same reason. |  | Optional: \{\} <br /> |
| `tolerations` _[Toleration](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#toleration-v1-core) array_ | Tolerations are what the storage-node pods tolerate, and they expand into<br />the cluster's own spec.storageNodes.tolerations.<br />A fleet that dedicates machines to storage taints them, which is what<br />keeps everything else off. The DaemonSet that lands on those machines has<br />to tolerate the taint or it schedules nowhere, and a document that could<br />not say so described a deployment that does not start: the correction was<br />an edit to the cluster the document had just created, on a field the<br />document owns everywhere else.<br />A growth document states none. It names a cluster rather than describing<br />one, and that cluster already carries what its storage nodes tolerate. |  | MaxItems: 32 <br />Optional: \{\} <br /> |
| `containerResources` _[ResourceRequirements](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#resourcerequirements-v1-core)_ | ContainerResources sizes the storage-node container, and expands into the<br />cluster's own spec.storageNodes.containerResources.<br />The container it sizes is the node's management API rather than SPDK,<br />which runs in a pod of its own: what outgrows the default is a node<br />answering for many subsystems, not a node moving more data. It is on the<br />document because a deployment is where a fleet's sizing is decided, and<br />a cluster written from a document that could not say so had to be edited<br />afterward on a field the document owns everywhere else.<br />Stating either half replaces both. The defaults apply to a cluster that<br />states neither requests nor limits, so a document stating requests alone<br />produces a container with no limits rather than one with the default<br />limits, and a memory limit is what has the kubelet evict a leaking agent<br />rather than losing the worker.<br />It is a pointer because a resource block is a struct, and a struct with<br />omitempty is serialized whether or not anything is in it: as a value,<br />every document a discovery run writes would carry an empty<br />containerResources that says nothing and that a reviewer has to decide<br />about. |  | Optional: \{\} <br /> |
| `nodeProvisioningBudget` _integer_ | NodeProvisioningBudget is how many workers the expansion may have in the<br />node-add process at once. It expands into the cluster's own<br />spec.storageNodes.nodeProvisioningBudget, whose meaning it shares: the cap<br />is counted by distinct worker, so a two-socket host spends one of the<br />budget, and a worker hosting a FoundationDB pod is sequential whatever the<br />budget says.<br />It is on the document because a document is what states the size of a<br />deployment, and a deployment of thirty workers added one at a time is the<br />difference between an afternoon and a week. Omitted, the cluster's default<br />of one applies, which is the serial behavior. |  | Minimum: 1 <br />Optional: \{\} <br /> |
| `enableChecksumValidation` _boolean_ | EnableChecksumValidation turns on inline CRC validation of every I/O, for<br />silent-data-error protection.<br />It is on the document because it is immutable on the cluster it lands on:<br />the backend bakes the checksum method into each device when the cluster is<br />created and never re-applies it, so a cluster created without this is one<br />nobody can turn it on for. A deployment that wants its data checked has to<br />say so here or not at all. |  | Optional: \{\} <br /> |
| `enableAtomicity4K` _boolean_ | EnableAtomicity4K enforces 4K write atomicity on every device this<br />deployment names, which is what lets checksum validation run on devices<br />whose logical block size is under the data plane's 4K minimum.<br />It is the route to checked I/O on a device that cannot be reformatted: a<br />logical block device's block size is fixed by the drive, and some NVMe<br />devices offer no 4K format either. Where a device can be reformatted,<br />EnableDriveFormat is the other route and this is unnecessary.<br />It is an enforcement because the question is often unanswerable. A SATA<br />drive presenting 512-byte logical blocks over a 4K physical sector reports<br />512 and nothing more, and a kernel older than 6.11 publishes no atomic<br />write attributes at all. Where a device does answer, the storage node's<br />report carries it, and a reviewer approves this against that rather than<br />against a vendor's datasheet -- because enforcing a guarantee the hardware<br />does not keep is how a torn write becomes a checksum that silently<br />disagrees with it.<br />It means nothing unless EnableChecksumValidation is set, which is the<br />cluster's own rule and is left to the cluster to enforce. |  | Optional: \{\} <br /> |
| `stripe` _[StripeSpec](#stripespec)_ | Stripe is the erasure-coding layout. |  | Optional: \{\} <br /> |
| `fabricType` _string_ | FabricType is the storage fabric. |  | MaxLength: 32 <br />Optional: \{\} <br /> |
| `openshift` _[OpenShiftSpec](#openshiftspec)_ | OpenShift is what this deployment states because it runs on OpenShift. It<br />expands into StorageCluster.spec.storageNodes.openshift, whose shape it<br />shares, and it is read only for a document whose environment is<br />OpenShift: the environment is what says which distribution this is, and<br />the block is what that distribution needs said beyond it. |  | Optional: \{\} <br /> |
| `ports` _[ClusterPortsSpec](#clusterportsspec)_ | Ports are where this cluster's storage nodes listen. Unstated, and for<br />each member left unstated, the cluster's own defaults decide. |  | Optional: \{\} <br /> |
| `enableFailureDomains` _boolean_ | EnableFailureDomains opts the cluster into failure-domain mode, in which<br />every group must label the fault group its workers belong to. |  | Optional: \{\} <br /> |
| `enableNodeAffinity` _boolean_ | EnableNodeAffinity has the data plane serve an erasure-coded volume's I/O<br />from the local node's own devices where it can, before crossing the<br />network.<br />It is not Kubernetes affinity, and the name is the one place this API<br />invites that reading: nothing about it schedules a pod, labels a worker,<br />or places a volume's primary node. The control plane carries it into the<br />cluster map it pushes to each node, where it sets the local node's index,<br />and what changes is which copy of a chunk is read.<br />design-primary-node-placement.md §"EnableNodeAffinity is unrelated to<br />Tier 1" is the longer account, and the co-location of a workload with its<br />primary node is the separate mechanism described there.<br />It is on the document because it is immutable on the cluster: the control<br />plane takes it at cluster create and never re-applies it, so this is the<br />only moment it can be set at all. |  | Optional: \{\} <br /> |
| `backup` _[BackupStoreSpec](#backupstorespec)_ | Backup is where this cluster's backups live, and it expands into<br />StorageCluster.spec.backup unchanged.<br />It is here for the reason KMS is: the expansion creates the cluster and<br />its own reconciler reads it back on the next pass, so a store stated on<br />the document is present at the cluster's creation rather than patched in<br />afterward by whoever remembers. Unlike most of what this template<br />carries, the field it fills is mutable, so a document that states none<br />costs nothing permanent — a cluster can be given a store whenever there<br />is one to give.<br />The Secret it names is not resolved at admission. It is a core object a<br />deployment legitimately creates alongside the document or after it, and<br />the cluster's own creation is where its absence is reported. |  | Optional: \{\} <br /> |
| `kms` _[KMSSpec](#kmsspec)_ | KMS selects where the cluster stores volume encryption keys. It is here<br />rather than left to be set on the StorageCluster afterward because the<br />expansion's own reconciler reads it back off that object on the very next<br />pass, before anything external could patch it in; stating it on the<br />document is what makes it present at the cluster's creation rather than a<br />race with one. |  | Optional: \{\} <br /> |


#### ControlPlane



ControlPlane is the simplyblock control plane for one Kubernetes cluster:
FoundationDB together with the management API, either installed by the
operator or already existing. It is a singleton named `simplyblock`, and it is
the root of the ownership spine: nothing else in this API group reconciles
meaningfully before it reports Available.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha2
kind: ControlPlane
metadata:
  name: string
spec:
  source:
    local:
      image: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
      imagePullPolicy: PullPolicy
      foundationDB:
        replicas: integer
        storageClassName: string
        resources: ResourceRequirements
      replicas: integer
      resources: ResourceRequirements
      tolerations:
        - Toleration
      nodeSelector:
        string: string
      tls:
        enableTLS: boolean
        enableMutualTLS: boolean
        provider: ControlPlaneTLSProvider
    managed:
      endpoint: '^https?://[a-zA-Z0-9.-]+(:[0-9]{1,5})?(/.*)?$'
      credentialsSecretRef: LocalObjectReference
      caBundleSecretRef: LocalObjectReference
status:
  phase: ControlPlanePhase
  step: KubeSnapshot
  endpoint: string
  version: string
  lastChecked: Time
  components:
    - name: string
      desired: integer
      ready: integer
      essential: boolean
  activeOpsRef: string
  message: string
  observedGeneration: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha2` | | |
| `kind` _string_ | `ControlPlane` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  | Optional: \{\} <br /> |
| `spec` _[ControlPlaneSpec](#controlplanespec)_ |  |  | Optional: \{\} <br /> |
| `status` _[ControlPlaneStatus](#controlplanestatus)_ |  |  | Optional: \{\} <br /> |


#### ControlPlaneComponentStatus



ControlPlaneComponentStatus is one workload of a managed control plane and how
much of it is running. The phase is the worst verdict across these and the
readiness probe, and only an essential component at zero ready can make it
Unavailable.



_Appears in:_
- [ControlPlaneStatus](#controlplanestatus)

_Example:_

```yaml
name: string
desired: integer
ready: integer
essential: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `name` _string_ | Name is the workload's name, as applied. |  | Required: \{\} <br /> |
| `desired` _integer_ | Desired is how many replicas the component should have. For the component<br />carrying its own operator it is that resource's own count, because a<br />FoundationDBCluster reports quorum rather than replicas. |  | Minimum: 0 <br />Optional: \{\} <br /> |
| `ready` _integer_ | Ready is how many of them are. |  | Minimum: 0 <br />Optional: \{\} <br /> |
| `essential` _boolean_ | Essential states whether this component at zero ready makes the control<br />plane Unavailable rather than Degraded. It is decided by the table in<br />§4.3 rather than by a user, and it is reported here so that a phase can be<br />explained without reading the operator's source. |  | Optional: \{\} <br /> |


#### ControlPlaneOps



ControlPlaneOps is a single operation performed against the control plane. It
runs to a terminal phase and stays afterward as the audit record of what was
done, with which parameters, and how it ended. Only one may be active per
control plane at a time, which the entity's status.activeOpsRef enforces.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha2
kind: ControlPlaneOps
metadata:
  name: string
spec:
  controlPlaneRef: string
  action: ControlPlaneOpsAction
  abort: boolean
  upgrade:
    image: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
  restart:
    components:
      - string
  backup:
    blobStore: string
    backupName: string
status:
  phase: ControlPlaneOpsPhase
  step: KubeSnapshot
  message: string
  backupRef: string
  observedGeneration: integer
  startedAt: Time
  completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha2` | | |
| `kind` _string_ | `ControlPlaneOps` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  |  |
| `spec` _[ControlPlaneOpsSpec](#controlplaneopsspec)_ |  |  |  |
| `status` _[ControlPlaneOpsStatus](#controlplaneopsstatus)_ |  |  |  |


#### ControlPlaneOpsAction

_Underlying type:_ _string_

ControlPlaneOpsAction is the operation a ControlPlaneOps performs. Every
action acts on what the operator installed, so every action requires a managed
control plane, and the validating webhook of §6 rejects an operation naming an
managed one at creation rather than letting it be created and fail.

_Validation:_
- Enum: [Restart Upgrade Backup]

_Appears in:_
- [ControlPlaneOpsSpec](#controlplaneopsspec)

| Field | Description |
| --- | --- |
| `Restart` | ControlPlaneOpsActionRestart recycles a wedged workload. Its scope is<br />spec.restart.components, and an empty list recycles the whole control<br />plane.<br /> |
| `Upgrade` | ControlPlaneOpsActionUpgrade moves the control plane to a new version and<br />verifies afterward that the version it reports is the one asked for.<br /> |
| `Backup` | ControlPlaneOpsActionBackup asks FoundationDB for a backup outside<br />whatever schedule exists. It asks rather than implements: the snapshot is<br />the FoundationDB operator's to take.<br /> |


#### ControlPlaneOpsPhase

_Underlying type:_ _string_

ControlPlaneOpsPhase is the operation's own progress.

_Validation:_
- Enum: [Pending Running Succeeded Failed Aborted]

_Appears in:_
- [ControlPlaneOpsStatus](#controlplaneopsstatus)

| Field | Description |
| --- | --- |
| `Pending` | ControlPlaneOpsPhasePending is an operation waiting for its target's lock.<br /> |
| `Running` | ControlPlaneOpsPhaseRunning is an operation holding the lock and working.<br /> |
| `Succeeded` | ControlPlaneOpsPhaseSucceeded is a finished operation that did what it<br />said.<br /> |
| `Failed` | ControlPlaneOpsPhaseFailed is a finished operation that did not.<br /> |
| `Aborted` | ControlPlaneOpsPhaseAborted is an operation stopped on request, whose<br />unwind has finished.<br /> |


#### ControlPlaneOpsSpec



ControlPlaneOpsSpec is one operation to perform against the control plane.

Everything except spec.abort is frozen once the object is admitted, which is
what makes the status an audit of the request that ran rather than of whatever
the object says now. The parameters are consumed several steps apart:
Preflight reads spec.upgrade.image and Applying writes it, and Draining reads
spec.restart.components before Restarting recycles them. An edit in between
produces an operation that checked one thing and did another.

The rules are declared here rather than as +k8s:immutable on each field.
controller-gen emits that marker's rules in an order that varies between runs
once a type carries several, and it freezes a block whole; what has to be
frozen is each block's presence together with its contents.



_Appears in:_
- [ControlPlaneOps](#controlplaneops)

_Example:_

```yaml
controlPlaneRef: string
action: ControlPlaneOpsAction
abort: boolean
upgrade:
  image: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
restart:
  components:
    - string
backup:
  blobStore: string
  backupName: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `controlPlaneRef` _string_ | ControlPlaneRef names the ControlPlane this operation acts on, in this<br />object's own namespace. The operation never owns its target, because<br />deleting the record of an operation must not delete the control plane it<br />operated on. |  | Required: \{\} <br /> |
| `action` _[ControlPlaneOpsAction](#controlplaneopsaction)_ | Action is the operation to perform. Immutable, so that the status describes<br />the operation that ran. |  | Enum: [Restart Upgrade Backup] <br />Required: \{\} <br /> |
| `abort` _boolean_ | Abort asks a running operation to stop at its next step and unwind. It is<br />the one field of this spec an update may change, because it is the one that<br />is meant to be set after the operation started. Whether an abort is<br />expressible from the current step is declared by that action's graph rather<br />than checked here. |  | Optional: \{\} <br /> |
| `upgrade` _[UpgradeSpec](#upgradespec)_ | Upgrade parameterizes action Upgrade and is ignored by the others. |  | Optional: \{\} <br /> |
| `restart` _[RestartSpec](#restartspec)_ | Restart parameterizes action Restart and is ignored by the others. |  | Optional: \{\} <br /> |
| `backup` _[BackupSpec](#backupspec)_ | Backup parameterizes action Backup and is ignored by the others. |  | Optional: \{\} <br /> |


#### ControlPlaneOpsStatus



ControlPlaneOpsStatus is the observed state of one control-plane operation.



_Appears in:_
- [ControlPlaneOps](#controlplaneops)

_Example:_

```yaml
phase: ControlPlaneOpsPhase
step: KubeSnapshot
message: string
backupRef: string
observedGeneration: integer
startedAt: Time
completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _[ControlPlaneOpsPhase](#controlplaneopsphase)_ | Phase is the operation's own progress. |  | Enum: [Pending Running Succeeded Failed Aborted] <br />Optional: \{\} <br /> |
| `step` _[KubeSnapshot](https://github.com/simplyblock/simplyblock-operator/blob/main/atlas-lib/statemachine/kubernetes.go)_ | Step is the position of the running action's state machine. It is<br />persisted before the side effect that step performs. The rule repeats the<br />ControlPlaneOpsStep enum because a marker cannot reach a field of the<br />shared snapshot type. |  | Optional: \{\} <br /> |
| `message` _string_ | Message is the reason the phase is what it is: one sentence, replaced as<br />the operation moves, and never a log. |  | Optional: \{\} <br /> |
| `backupRef` _string_ | BackupRef names the FoundationDBBackup a Backup run created or triggered.<br />The operation does not own it, because deleting the record of a backup<br />must not delete the backup's configuration. |  | Optional: \{\} <br /> |
| `observedGeneration` _integer_ | ObservedGeneration is the generation the rest of this status was computed<br />from, so a stale status can be told from a current one. |  | Optional: \{\} <br /> |
| `startedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | StartedAt is when the operation acquired its target's lock. |  | Optional: \{\} <br /> |
| `completedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | CompletedAt is when it reached a terminal phase. |  | Optional: \{\} <br /> |




#### ControlPlanePhase

_Underlying type:_ _string_

ControlPlanePhase is where the operator has got to with this control plane.

_Validation:_
- Enum: [Installing Available Degraded Unavailable]

_Appears in:_
- [ControlPlaneStatus](#controlplanestatus)

| Field | Description |
| --- | --- |
| `Installing` | ControlPlanePhaseInstalling is a control plane that has not worked yet.<br /> |
| `Available` | ControlPlanePhaseAvailable is one whose readiness probe passes and whose<br />workload pods are settled.<br /> |
| `Degraded` | ControlPlanePhaseDegraded is one whose readiness probe passes while a<br />management API or FoundationDB pod is restarting. It answers every<br />request, so nothing holds on it and it exists to be read by a person. A<br />control plane the operator does not manage never reaches it, because the<br />operator owns no pods there to watch.<br /> |
| `Unavailable` | ControlPlanePhaseUnavailable is one whose readiness probe fails: it<br />worked and stopped, which is a different situation from one that never<br />started, and it is what downstream controllers hold on. The word claims<br />only what the probe observed, since a failing probe cannot tell a crashed<br />process from a wedged one or from a partition.<br /> |


#### ControlPlaneSource



ControlPlaneSource selects whether this cluster hosts its control plane or is
managed by one elsewhere. Exactly one member is set, which is what makes the
two modes siblings rather than two unrelated top-level fields, and which
member it is cannot change afterward.

Both rules are declared here rather than on the field that carries the block,
for two separate reasons.

The immutability is the interesting one. What is frozen is the choice between
the two modes and not the block, because the members have to stay editable:
changing spec.source.local.image is an ordinary edit, and it is what a
ControlPlaneOps upgrade performs. Spelling it +k8s:immutable on the field
would emit self == oldSelf over the whole struct, which freezes the image with
it and makes that operation impossible to complete.

The placement is the dull one. controller-gen v0.21.0 emits a single field's
marker-derived rules and its injected immutability rule into one list in an
order that varies between runs, so a field carrying both produces a CRD that
differs from itself and a drift check that fails at random. Two rules of the
same kind on a type are emitted in source order.



_Appears in:_
- [ControlPlaneSpec](#controlplanespec)

_Example:_

```yaml
local:
  image: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
  imagePullPolicy: PullPolicy
  foundationDB:
    replicas: integer
    storageClassName: string
    resources: ResourceRequirements
  replicas: integer
  resources: ResourceRequirements
  tolerations:
    - Toleration
  nodeSelector:
    string: string
  tls:
    enableTLS: boolean
    enableMutualTLS: boolean
    provider: ControlPlaneTLSProvider
managed:
  endpoint: '^https?://[a-zA-Z0-9.-]+(:[0-9]{1,5})?(/.*)?$'
  credentialsSecretRef: LocalObjectReference
  caBundleSecretRef: LocalObjectReference
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `local` _[LocalControlPlane](#localcontrolplane)_ | Local is a control plane the operator installs. |  | Optional: \{\} <br /> |
| `managed` _[ManagedControlPlane](#managedcontrolplane)_ | Managed is a control plane that already exists. |  | Optional: \{\} <br /> |


#### ControlPlaneSpec



ControlPlaneSpec is the desired state of the simplyblock control plane for one
namespace.



_Appears in:_
- [ControlPlane](#controlplane)

_Example:_

```yaml
source:
  local:
    image: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
    imagePullPolicy: PullPolicy
    foundationDB:
      replicas: integer
      storageClassName: string
      resources: ResourceRequirements
    replicas: integer
    resources: ResourceRequirements
    tolerations:
      - Toleration
    nodeSelector:
      string: string
    tls:
      enableTLS: boolean
      enableMutualTLS: boolean
      provider: ControlPlaneTLSProvider
  managed:
    endpoint: '^https?://[a-zA-Z0-9.-]+(:[0-9]{1,5})?(/.*)?$'
    credentialsSecretRef: LocalObjectReference
    caBundleSecretRef: LocalObjectReference
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `source` _[ControlPlaneSource](#controlplanesource)_ | Source selects whether this cluster hosts its control plane or is managed<br />by one elsewhere. Switching a live deployment between the two is not a<br />reconfiguration, because the clusters and their volumes live in the<br />FoundationDB behind the old one, so which mode is chosen is frozen at<br />creation. What is inside the chosen mode stays editable.<br />Both rules are declared on ControlPlaneSource rather than here. See the<br />type for why. |  | Required: \{\} <br /> |


#### ControlPlaneStatus



ControlPlaneStatus is the observed state of the control plane.



_Appears in:_
- [ControlPlane](#controlplane)

_Example:_

```yaml
phase: ControlPlanePhase
step: KubeSnapshot
endpoint: string
version: string
lastChecked: Time
components:
  - name: string
    desired: integer
    ready: integer
    essential: boolean
activeOpsRef: string
message: string
observedGeneration: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _[ControlPlanePhase](#controlplanephase)_ | Phase is the operator's own view of the control plane. |  | Enum: [Installing Available Degraded Unavailable] <br />Optional: \{\} <br /> |
| `step` _[KubeSnapshot](https://github.com/simplyblock/simplyblock-operator/blob/main/atlas-lib/statemachine/kubernetes.go)_ | Step is the position of the installation machine within Installing. The<br />rule repeats the ControlPlaneStep enum because a marker cannot reach a<br />field of the shared snapshot type. |  | Optional: \{\} <br /> |
| `endpoint` _string_ | Endpoint is the resolved management API base URL, derived in the local<br />case and echoed in the managed one. It is what every controller in the<br />operator reads to reach the control plane, so that one object answers<br />where it is. |  | Optional: \{\} <br /> |
| `version` _string_ | Version is the version the management API reports. |  | Optional: \{\} <br /> |
| `lastChecked` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | LastChecked is when the readiness probe last ran. |  | Optional: \{\} <br /> |
| `components` _[ControlPlaneComponentStatus](#controlplanecomponentstatus) array_ | Components is the per-component readiness the phase is derived from<br />(§4.3), one entry per workload the managed install applies. It is empty<br />for a remote control plane, which has no components the operator owns.<br />Without it a Degraded phase says that something is wrong and not what. |  | Optional: \{\} <br /> |
| `activeOpsRef` _string_ | ActiveOpsRef names the ControlPlaneOps currently allowed to act on this<br />control plane. Empty when none is running. |  | Optional: \{\} <br /> |
| `message` _string_ | Message is the reason the phase is what it is: one sentence, replaced as<br />the control plane moves, and never a log. On a failed probe it is the<br />control plane's own error rather than a paraphrase of it. |  | Optional: \{\} <br /> |
| `observedGeneration` _integer_ | ObservedGeneration is the generation the rest of this status was computed<br />from, so a stale status can be told from a current one. |  | Optional: \{\} <br /> |




#### ControlPlaneTLS



ControlPlaneTLS is how a control plane this operator installs serves, and what
it requires of the clients that reach it.

The field names are DriverTLS's, because they are the same three decisions
about the same connection seen from its two ends, and a reader who knows one
should not have to learn the other. What differs is the default: the CSI
driver's fields were added to describe deployments that already existed and
default off, and these default on. An installed control plane holds every
cluster definition, node registration, and volume record, and is reached over
the pod network by the operator, the CSI driver, and the metrics scrape alike,
so plaintext is a decision to state rather than the state a deployment lands
in by leaving the block out.



_Appears in:_
- [LocalControlPlane](#localcontrolplane)

_Example:_

```yaml
enableTLS: boolean
enableMutualTLS: boolean
provider: ControlPlaneTLSProvider
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `enableTLS` _boolean_ | EnableTLS serves the management API over TLS. Unset is on. | true | Optional: \{\} <br /> |
| `enableMutualTLS` _boolean_ | EnableMutualTLS additionally requires a caller to present a certificate<br />of its own, rather than reaching the control plane anonymously over the<br />encrypted connection EnableTLS alone provides. Ignored when EnableTLS is<br />false, the same as on DriverTLS. Unset is on. | true | Optional: \{\} <br /> |
| `provider` _[ControlPlaneTLSProvider](#controlplanetlsprovider)_ | Provider issues the serving certificate. | cert-manager | Enum: [cert-manager OpenShift] <br />Optional: \{\} <br /> |


#### ControlPlaneTLSProvider

_Underlying type:_ _string_

ControlPlaneTLSProvider is who issues the control plane's serving certificate.

The two values are each product's own spelling rather than this group's
PascalCase, because they are not this group's words: they are what
internal/utils/tls.go already matches on and what the control-plane image
reads out of SB_TLS_PROVIDER.

_Validation:_
- Enum: [cert-manager OpenShift]

_Appears in:_
- [ControlPlaneTLS](#controlplanetls)

| Field | Description |
| --- | --- |
| `cert-manager` | ControlPlaneTLSCertManager issues through cert-manager, from the CA the<br />deployment's ClusterIssuer mints.<br /> |
| `OpenShift` | ControlPlaneTLSOpenShift issues through the OpenShift service CA, which<br />signs from a Service annotation rather than from an object of its own.<br /> |


#### CreatorReference



CreatorReference names the object that created a PersistentVolumeOps.

It exists because a cluster-scoped object cannot be owned by a namespaced
one: Kubernetes treats such a reference as unresolvable and garbage-collects
the dependent. Core Kubernetes has the same situation twice and answers it
the same way — a PersistentVolume names its claim through spec.claimRef and a
VolumeSnapshotContent names its snapshot through spec.volumeSnapshotRef, both
with a UID — and that shape carries over here unchanged
(design-persistentvolumeops.md §11.1).



_Appears in:_
- [PersistentVolumeOpsSpec](#persistentvolumeopsspec)

_Example:_

```yaml
kind: string
namespace: string
name: string
uid: UID
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `kind` _string_ | Kind is the creating object's kind, which is StorageNodeOps for a drain. |  | Required: \{\} <br /> |
| `namespace` _string_ | Namespace is where the creator lives. |  | Required: \{\} <br /> |
| `name` _string_ | Name is the creator's object name. |  | Required: \{\} <br /> |
| `uid` _[UID](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#uid-types-pkg)_ | UID is what makes the reference address one creator rather than one name:<br />a creator deleted and recreated under the same name must not inherit the<br />fan-out it did not issue, and cascade a delete over it. |  | Required: \{\} <br /> |


#### DataRealignmentSettings



DataRealignmentSettings tunes the post-migration control-plane data
realignment, which re-aligns the control plane's internal structures to where
volumes now are and restores the fault-tolerance and node-affinity guarantees
a move invalidated.

Whether it runs at all is StorageClusterSpec.DisableDataRealignment, a field
of the spec rather than of this block: a toggle named for its subject repeats
itself when the subject is also its parent.



_Appears in:_
- [VolumeMigrationSettings](#volumemigrationsettings)

_Example:_

```yaml
interval: Duration
minMoves: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `interval` _[Duration](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#duration-v1-meta)_ | Interval is a floor on the spacing between realignment requests, and not<br />a ceiling on how long one takes: a realignment blocks every volume<br />migration for as long as the control plane needs, measured at tens of<br />minutes on a loaded cluster. The trigger annotation bypasses it. Defaults<br />to 10m. |  | Optional: \{\} <br /> |
| `minMoves` _integer_ | MinMoves is how many volume moves accumulate before a realignment is<br />requested. It defaults to 1, which makes migration and realignment<br />alternate, and is the field to raise in order to batch: a higher value<br />trades how promptly the structures are realigned for migration<br />throughput. The trigger annotation bypasses it. |  | Minimum: 1 <br />Optional: \{\} <br /> |


#### DeploymentImages



DeploymentImages is every image a deployment pins, in one block.

All three are software that runs on a storage node, which is what the slot
names say and what an earlier spelling of the first one hid. They are together
rather than each beside the object it configures because pinning images is one
decision taken once: an air-gapped installation overrides all three against its
own registry, and a reviewer reading the document has one place to check what
this deployment will run. The expansion is what spends them on two different
objects, since the three fields they land on are not all on the same kind.

The control plane's own image is not here. A ClusterDeploymentConfig creates a
StorageCluster and its StorageNodes and neither creates nor adopts the
ControlPlane, so a slot for it would be a field the expansion has nowhere to
write. It is ControlPlane.spec.source.local.image, and the CSI driver's is
SimplyblockDriver.spec.image.



_Appears in:_
- [ClusterDeploymentConfigSpec](#clusterdeploymentconfigspec)

_Example:_

```yaml
nodeAgent:
  image: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
  imagePullPolicy: PullPolicy
spdk:
  image: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
  imagePullPolicy: PullPolicy
spdkProxy:
  image: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
  imagePullPolicy: PullPolicy
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `nodeAgent` _[ImageSpec](#imagespec)_ | NodeAgent is the image the storage-node DaemonSet runs: the agent the<br />control plane drives a worker through, and the two init containers that<br />configure the host before it starts. The expansion writes it to<br />StorageCluster.spec.storageNodes, which is where the retired<br />StorageNodeSet.spec.clusterImage went.<br />It is the same artifact the control plane itself runs, which is why<br />spec.storageNodes.image defaults to the ControlPlane singleton's: the agent<br />and the tasks that call it are one codebase, and version skew between them<br />is what breaks a node add.<br />It is spent only where the document creates the cluster. A document that<br />names an existing one in ClusterRef adds nodes to a DaemonSet that is<br />already running under an image the cluster states, and this slot is ignored<br />the same way Cluster is. |  | Optional: \{\} <br /> |
| `spdk` _[ImageSpec](#imagespec)_ | SPDK is the SPDK image, which the expansion writes onto every<br />StorageNode.spec.config it creates rather than onto the cluster: the field<br />is per node so that a later rollout can walk the fleet one machine at a<br />time, and a document states the fleet's starting point. |  | Optional: \{\} <br /> |
| `spdkProxy` _[ImageSpec](#imagespec)_ | SPDKProxy is the SPDK proxy image, written per node for the reason SPDK is. |  | Optional: \{\} <br /> |


#### DeviceCapacity



DeviceCapacity is how big the device is. It carries no used size and no
sample time, because a physical device cannot be resized: the number is a
property of the hardware, it is written when the device is discovered, and
nothing rewrites it. A device reporting a different size is a different
device, which arrives as its own object.

What the device holds is the number that moves, and it is served from
metrics.simplyblock.io as StorageDeviceMetrics rather than published here. A
reading that changes continuously is not desired state, and keeping it in a
status would write etcd on every sample and wake every watcher of the kind
for it.



_Appears in:_
- [StorageDeviceStatus](#storagedevicestatus)

_Example:_

```yaml
totalBytes: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `totalBytes` _integer_ | TotalBytes is the device's usable size, as the control plane reports it<br />with the device. |  | Minimum: 0 <br />Optional: \{\} <br /> |


#### DeviceFilter



DeviceFilter narrows what a discovery run reports as a candidate device. It is
an input to discovery and never appears in the document discovery writes: a
ClusterDeploymentConfig carries the explicit list the filter produced, not the
rule that produced it.

The filters come in two sets, one per device class, and a run scans one class.
The two rules below reject the set belonging to the class this run is not
scanning, because a filter that will never be applied is one an administrator
reads as having narrowed a draft that was never narrowed.



_Appears in:_
- [DiscoverSpec](#discoverspec)

_Example:_

```yaml
enableLogicalBlockDevices: boolean
enablePartitionedDevices: boolean
pcieAllowList:
  - string
pcieDenyList:
  - string
pcieModel: string
blockAllowList:
  - '^/dev/[a-zA-Z0-9._/-]+$'
blockDenyList:
  - '^/dev/[a-zA-Z0-9._/-]+$'
driveSizeRange: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `enableLogicalBlockDevices` _boolean_ | EnableLogicalBlockDevices scans a worker's available logical block devices<br />instead of its available NVMe devices. It selects the class rather than<br />adding one, because the draft a run writes describes one cluster and a<br />cluster is built out of one class. Unset scans NVMe, so that upgrading to<br />26.4 does not change what a discovery run reports. |  | Optional: \{\} <br /> |
| `enablePartitionedDevices` _boolean_ | EnablePartitionedDevices reports devices carrying a partition table<br />alongside the available ones, for the administrator who knows the table is<br />stale and intends to hand the device over anyway. It is the only one of the<br />three availability conditions that can be waived: a mounted or otherwise<br />busy device is never reported, because simplyblock taking it would corrupt<br />whatever is using it. |  | Optional: \{\} <br /> |
| `pcieAllowList` _string array_ | PcieAllowList restricts candidates to these PCI addresses. This and the two<br />PCI filters below narrow the NVMe class alone, because a logical block<br />device has no PCI address to match, so setting any of them on a run that<br />scans the block class is rejected by the rule on this type. |  | Optional: \{\} <br /> |
| `pcieDenyList` _string array_ | PcieDenyList excludes these PCI addresses. On a fleet that is uniform<br />about which slot holds the boot device, this is what keeps that device out<br />of every group of every draft. |  | Optional: \{\} <br /> |
| `pcieModel` _string_ | PcieModel restricts candidates to devices whose PCI model string matches. |  | Optional: \{\} <br /> |
| `blockAllowList` _string array_ | BlockAllowList restricts candidates to these device paths ("/dev/sdb").<br />This and BlockDenyList are the block class's half of the filter, and they<br />require EnableLogicalBlockDevices for the same reason the PCI filters<br />forbid it. |  | items:Pattern: `^/dev/[a-zA-Z0-9._/-]+$` <br />Optional: \{\} <br /> |
| `blockDenyList` _string array_ | BlockDenyList excludes these device paths. On a fleet that boots from<br />/dev/sda, this is the one entry that keeps the root disk out of every group<br />of every draft. |  | items:Pattern: `^/dev/[a-zA-Z0-9._/-]+$` <br />Optional: \{\} <br /> |
| `driveSizeRange` _string_ | DriveSizeRange restricts candidates by size ("100G-2T"). Unlike the<br />per-class filters, it applies to whichever class the run is scanning. |  | Optional: \{\} <br /> |


#### DeviceHardware



DeviceHardware identifies the part. These are what somebody walking into a
datacenter with a failed drive needs, and none of them is recoverable from the
control plane's device id alone. Every field is optional, because which ones a
device has depends on how it is attached.

The design's devicePath is absent: the control plane reports no host path for
a device, only the NVMe controller it hangs off, so the field would never be
populated. NVMeController carries what is actually reported.



_Appears in:_
- [StorageDeviceStatus](#storagedevicestatus)

_Example:_

```yaml
pciAddress: string
serialNumber: string
model: string
nvmeController: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `pciAddress` _string_ | PCIAddress is the device's address on the host ("0000:5e:00.0"), where it<br />has one. A logical block device may not: the address can belong to the<br />controller it hangs off rather than to the device. |  | Optional: \{\} <br /> |
| `serialNumber` _string_ | SerialNumber is what is printed on the drive. |  | Optional: \{\} <br /> |
| `model` _string_ | Model is the manufacturer's model string. |  | Optional: \{\} <br /> |
| `nvmeController` _string_ | NVMeController is the controller the device is served through, in the<br />control plane's spelling. |  | Optional: \{\} <br /> |


#### DeviceSelection



DeviceSelection is the explicit list of storage devices a group's workers hand
to simplyblock. It carries no filter of any kind: a document whose meaning
depends on what the hardware turns out to be is not a document a reviewer can
approve, so filtering happens in the discovery run that produces the list and
what lands here is the result. It expands to the matching fields of
StorageNode.spec.config, which carry the same meanings.

One member and not both. A cluster is built out of one class of backend
storage, so a group hands over NVMe devices or logical block devices, and the
rule below is the half of that a single group can be checked against. That
every group of the document agrees is the spec's rule.



_Appears in:_
- [NodeGroup](#nodegroup)

_Example:_

```yaml
nvme:
  - '^[0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F]$'
block:
  - '^/dev/[a-zA-Z0-9._/-]+$'
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `nvme` _string array_ | NVMe names NVMe devices by PCI address ("0000:5e:00.0"). |  | MaxItems: 128 <br />items:MaxLength: 32 <br />items:Pattern: `^[0-9a-fA-F]\{4\}:[0-9a-fA-F]\{2\}:[0-9a-fA-F]\{2\}\.[0-9a-fA-F]$` <br />Optional: \{\} <br /> |
| `block` _string array_ | Block names logical block devices by path ("/dev/sdb"). It expands into the<br />same config.deviceNames as NVMe, which takes a PCI address and a device<br />path in one list. It is the alternative to NVMe rather than a companion of<br />it: the two classes are not mixed within a cluster. |  | MaxItems: 128 <br />items:MaxLength: 255 <br />items:Pattern: `^/dev/[a-zA-Z0-9._/-]+$` <br />Optional: \{\} <br /> |


#### DiscoverSpec



DiscoverSpec parameterizes the Discover action.

Which workers a run inspects is stated one of two ways and never both: by name
in Workers, or by label in NodeSelector. They are exclusive rather than
intersected because the intersection of a name list and a label selector is a
question nobody asks deliberately, and reading one as narrowing the other
would make a run inspect fewer machines than either field says.



_Appears in:_
- [OperatorOpsSpec](#operatoropsspec)

_Example:_

```yaml
configName: string
workers:
  - string
nodeSelector:
  string: string
tolerations:
  - Toleration
enableControlPlaneNodes: boolean
deviceFilter:
  enableLogicalBlockDevices: boolean
  enablePartitionedDevices: boolean
  pcieAllowList:
    - string
  pcieDenyList:
    - string
  pcieModel: string
  blockAllowList:
    - '^/dev/[a-zA-Z0-9._/-]+$'
  blockDenyList:
    - '^/dev/[a-zA-Z0-9._/-]+$'
  driveSizeRange: string
clusterRef: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `configName` _string_ | ConfigName is the ClusterDeploymentConfig to write. Absent generates one<br />from the run's timestamp, so that a second discovery never overwrites the<br />first, which may have been reviewed and corrected. |  | Optional: \{\} <br /> |
| `workers` _string array_ | Workers are the workers to inspect, by node name.<br />It is the answer to inspecting two named machines, which a label selector<br />can only express by labeling them first: a selector's entries are ANDed,<br />so two hostnames in one selector match nothing at all.<br />A named worker that does not exist, or that is declined for one of the<br />reasons any worker is declined, is reported by the same event the selector<br />path reports it by. Naming a worker is a statement about which machines to<br />consider, not a claim that each of them will be used. |  | MaxItems: 128 <br />items:MaxLength: 253 <br />Optional: \{\} <br /> |
| `nodeSelector` _object (keys:string, values:string)_ | NodeSelector restricts which workers are inspected. Empty inspects every<br />schedulable worker, and it is exclusive with Workers. |  | Optional: \{\} <br /> |
| `tolerations` _[Toleration](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#toleration-v1-core) array_ | Tolerations are what the probe pods tolerate, and what the draft states<br />for the storage nodes it proposes.<br />A probe is pinned to its worker with spec.nodeName rather than scheduled<br />onto it, which bypasses the scheduler and not the taints: a NoSchedule<br />taint still keeps the pod off, and a NoExecute taint evicts one that<br />landed. A fleet that dedicates machines to storage taints them, so a run<br />against one that tolerates nothing inspects nothing.<br />They reach the draft as well, because the taints a run was allowed to<br />probe through are the taints the cluster it proposes has to live with.<br />Stating them in one place is what keeps a reviewer from approving a<br />document whose DaemonSet schedules nowhere. |  | MaxItems: 32 <br />Optional: \{\} <br /> |
| `enableControlPlaneNodes` _boolean_ | EnableControlPlaneNodes lets the run consider machines that run the API<br />server and etcd.<br />It is off by default because a storage node is a data path, and putting one<br />on an etcd host is a placement almost nobody intends. The approval gate is a<br />poor place to catch it: a fifty-worker draft is not a document anybody reads<br />closely enough to spot three control-plane nodes in it. A combined three-node<br />or single-node deployment is the case that wants it, and those are set up<br />deliberately.<br />There is no field beside it for infrastructure nodes, because those are used<br />without asking: an OpenShift infra node is the tier a cluster's own<br />infrastructure runs on, and simplyblock storage is infrastructure. A fleet<br />with disks in its infra nodes meant those disks to be the storage, so a draft<br />proposes them ahead of the workers rather than leaving them out. |  | Optional: \{\} <br /> |
| `deviceFilter` _[DeviceFilter](#devicefilter)_ | DeviceFilter narrows which of an inspected worker's devices reach the<br />draft. Empty reports every device the worker advertises, including the one<br />it boots from, which is what the approval gate then has to catch. |  | Optional: \{\} <br /> |
| `clusterRef` _string_ | ClusterRef names an existing StorageCluster the draft grows rather than<br />creates. It is copied to the draft's own clusterRef, so that re-running<br />discovery after an expansion produces a growth document naming the same<br />cluster.<br />Bounded at what a StorageCluster name may be, since a longer value names<br />nothing that can exist (design-api-upgrade.md §19.4). |  | MaxLength: 63 <br />Optional: \{\} <br /> |


#### DrainStatus



DrainStatus is the drain's progress over the volumes on the node being removed.
Neither field takes omitempty: zero is meaningful for both, and a field that
disappears at zero makes "nothing to move" and "not yet counted" the same wire
value.



_Appears in:_
- [StorageNodeOpsStatus](#storagenodeopsstatus)

_Example:_

```yaml
volumesTotal: integer
volumesMigrated: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `volumesTotal` _integer_ | VolumesTotal is the number of PV-managed volumes the drain has to move,<br />written once at the end of Validating and not modified afterward. |  | Minimum: 0 <br /> |
| `volumesMigrated` _integer_ | VolumesMigrated is how many of them have completed. |  | Minimum: 0 <br /> |


#### DriverTLS



DriverTLS configures whether this deployment's two plugins reach the
control plane over TLS. Unset (every field at its zero value) is a
plaintext data path, which is what every deployment measured before this
field existed ran as — the chart rendered `simplyblock.tlsEnv`,
`simplyblock.tlsVolumeMount`, and `simplyblock.clientTlsVolume`
unconditionally on both plugins, gated on the same three Helm values these
fields replace.

The client-certificate Secret each plugin mounts is not named here: it is
`<object name>-csi-controller-client-tls` and
`<object name>-csi-node-client-tls`, the same names
operator/internal/controllers/driver/names.go derives for every other
object, and the same ones this chart's controlplane_certificates.yaml
already writes for cert-manager. A field naming them again would be a
second place for the two to disagree.



_Appears in:_
- [SimplyblockDriverSpec](#simplyblockdriverspec)

_Example:_

```yaml
enableTLS: boolean
enableMutualTLS: boolean
provider: DriverTLSProvider
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `enableTLS` _boolean_ | EnableTLS turns on TLS between both plugins and the control plane. | false | Optional: \{\} <br /> |
| `enableMutualTLS` _boolean_ | EnableMutualTLS additionally requires each plugin to present a client<br />certificate, rather than dialing the control plane anonymously over<br />the encrypted connection EnableTLS alone provides. Ignored when<br />EnableTLS is false, the same as the Helm value it replaces. | false | Optional: \{\} <br /> |
| `provider` _[DriverTLSProvider](#drivertlsprovider)_ | Provider selects where the CA bundle (and, with EnableMutualTLS, the<br />client certificate) comes from. Required reading whenever EnableTLS is<br />true: the two providers mount a differently shaped volume, and neither<br />shape can be inferred from anything else on this object. | cert-manager | Enum: [OpenShift cert-manager] <br />Optional: \{\} <br /> |


#### DriverTLSProvider

_Underlying type:_ _string_

DriverTLSProvider is where the TLS certificate on this connection comes
from. The values are not this group's to spell: OpenShift and cert-manager
are the two products, and the operator's own internal/utils package already
carries these exact strings for the control plane's own SB_TLS_PROVIDER, so
a driver and a control plane in the same namespace agree on the same word
without a translation table between them.

_Validation:_
- Enum: [OpenShift cert-manager]

_Appears in:_
- [DriverTLS](#drivertls)

| Field | Description |
| --- | --- |
| `OpenShift` | DriverTLSProviderOpenShift is OpenShift's service-ca operator: a<br />ConfigMap carrying the cluster CA, and a Secret an administrator<br />provisions for each plugin's client certificate.<br /> |
| `cert-manager` | DriverTLSProviderCertManager is cert-manager: a ClusterIssuer already<br />installed by this chart mints a Certificate per plugin, and the Secret<br />it writes carries the CA bundle alongside the client keypair.<br /> |


#### FoundationDBSpec



FoundationDBSpec is the sizing of the FoundationDB the operator installs.



_Appears in:_
- [LocalControlPlane](#localcontrolplane)

_Example:_

```yaml
replicas: integer
storageClassName: string
resources: ResourceRequirements
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `replicas` _integer_ | Replicas is the number of coordinators. Three is the smallest count that<br />survives one loss, which is why it is the default. | 3 | Minimum: 1 <br />Optional: \{\} <br /> |
| `storageClassName` _string_ | StorageClassName is the class the coordinators' volumes are provisioned<br />from. It cannot be a class this operator provides, because the control<br />plane has to exist before any simplyblock volume can. |  | Optional: \{\} <br /> |
| `resources` _[ResourceRequirements](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#resourcerequirements-v1-core)_ | Resources sets requests and limits for the coordinator pods. |  | Optional: \{\} <br /> |


#### HostOSFamily

_Underlying type:_ _string_

HostOSFamily is the packaging tradition a Linux distribution belongs to.

It is the coarse half of what a host OS is, and the half most decisions are
actually about: what differs between Ubuntu and Debian is rarely what a
storage node needs, and what differs between Ubuntu and Rocky always is.
There is no member for a host with no package manager: Talos and Flatcar are
not a family with no name, they are machines where the question does not
arise, and a document describing one leaves the family unstated.

_Validation:_
- Enum: [Debian RedHat SUSE Alpine Arch]

_Appears in:_
- [HostOSSpec](#hostosspec)

| Field | Description |
| --- | --- |
| `Debian` |  |
| `RedHat` |  |
| `SUSE` |  |
| `Alpine` |  |
| `Arch` |  |


#### HostOSSpec



HostOSSpec is the operating system a deployment's workers run.

It is a fact about the machines rather than about Kubernetes, which is why it
is stated here and not derived from spec.environment: a fleet on OpenShift
runs Red Hat Enterprise Linux CoreOS, and a fleet on K3s runs whatever its
administrator installed. A discovery run fills it in from what the probes
read, and fills it in only when every worker agrees, so a document that
states one is a document whose fleet is uniform.



_Appears in:_
- [ClusterDeploymentConfigSpec](#clusterdeploymentconfigspec)

_Example:_

```yaml
distro: '^[a-z0-9][a-z0-9._-]*$'
family: HostOSFamily
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `distro` _string_ | Distro is the distribution's os-release ID, lowercase and verbatim:<br />`ubuntu`, `rocky`, `rhel`, `talos`. It is what the expansion reads. |  | MaxLength: 63 <br />Pattern: `^[a-z0-9][a-z0-9._-]*$` <br />Optional: \{\} <br /> |
| `family` _[HostOSFamily](#hostosfamily)_ | Family is the packaging tradition Distro belongs to. A discovery run<br />concludes it from the distribution itself, or from the distributions its<br />os-release says it is built on, which is what places a derivative this<br />product has never heard of. It is left unstated for a host with no<br />package manager. |  | Enum: [Debian RedHat SUSE Alpine Arch] <br />Optional: \{\} <br /> |


#### ImageSpec



ImageSpec is one container image and when to pull it, which is the pair every
image in this product is stated as.

Both members are optional so that each can be stated without the other: an
air-gapped deployment overrides the image and keeps the policy, and a
development one keeps the image and pins the policy to IfNotPresent so a tag
rebuilt in place is not picked up mid-deployment.



_Appears in:_
- [DeploymentImages](#deploymentimages)

_Example:_

```yaml
image: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
imagePullPolicy: PullPolicy
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `image` _string_ | Image is the repository and tag, optionally digest-pinned. An empty value<br />is not written downstream, so the field it would fill keeps its own<br />default rather than being overridden with nothing.<br />The registry set is the one every image field in this API is held to,<br />which is what keeps a reviewed document from naming a build nobody<br />published. |  | Pattern: `^($\|(quay\.io/simplyblock-io\|docker\.io/simplyblock\|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]\{64\})?)$` <br />Optional: \{\} <br /> |
| `imagePullPolicy` _[PullPolicy](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#pullpolicy-v1-core)_ | ImagePullPolicy is when that image is pulled. It defaults to Always,<br />because every image this product ships by default is a moving tag and a<br />node brought up after a release otherwise runs what its kubelet held. | Always | Enum: [Always Never IfNotPresent] <br />Optional: \{\} <br /> |


#### JournalManagerSpec



JournalManagerSpec tunes the journal managers on one storage node.



_Appears in:_
- [NodeGroup](#nodegroup)
- [StorageNodeConfig](#storagenodeconfig)

_Example:_

```yaml
count: integer
percentPerDevice: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `count` _integer_ | Count is the number of journal managers to configure. |  | Minimum: 1 <br />Optional: \{\} <br /> |
| `percentPerDevice` _integer_ | PercentPerDevice is the share of each device given to the journal. |  | Maximum: 100 <br />Minimum: 1 <br />Optional: \{\} <br /> |


#### KMSSpec



KMSSpec selects where the cluster stores volume encryption keys. It is a
block with one member per provider so that the providers are siblings, which
is what makes choosing between them expressible.



_Appears in:_
- [ClusterTemplate](#clustertemplate)
- [StorageClusterSpec](#storageclusterspec)

_Example:_

```yaml
vault:
  endpoint: '^https?://[a-zA-Z0-9.-]+(:[0-9]{1,5})?(/.*)?$'
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `vault` _[VaultKMS](#vaultkms)_ | Vault stores keys in HashiCorp Vault. |  | Optional: \{\} <br /> |


#### KubernetesEnvironment

_Underlying type:_ _string_

KubernetesEnvironment is the distribution a deployment targets. The values are
the distributions' own names, which is the exception design-crd-model.md §7.8
carries for a word this group did not invent.

_Validation:_
- Enum: [Vanilla OpenShift Rancher K3s Talos]

_Appears in:_
- [ClusterDeploymentConfigSpec](#clusterdeploymentconfigspec)
- [OperatorOpsStatus](#operatoropsstatus)

| Field | Description |
| --- | --- |
| `Vanilla` |  |
| `OpenShift` |  |
| `Rancher` |  |
| `K3s` |  |
| `Talos` |  |


#### LocalControlPlane



LocalControlPlane is a control plane this cluster hosts, installed and owned
by the operator. Its objects carry a controller reference to the ControlPlane,
so the ownership spine starts at a real edge rather than at a Helm release.



_Appears in:_
- [ControlPlaneSource](#controlplanesource)

_Example:_

```yaml
image: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
imagePullPolicy: PullPolicy
foundationDB:
  replicas: integer
  storageClassName: string
  resources: ResourceRequirements
replicas: integer
resources: ResourceRequirements
tolerations:
  - Toleration
nodeSelector:
  string: string
tls:
  enableTLS: boolean
  enableMutualTLS: boolean
  provider: ControlPlaneTLSProvider
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `image` _string_ | Image is the management API and control-plane image.<br />Must reference one of the trusted registries (`quay.io/simplyblock-io`,<br />`docker.io/simplyblock`, `public.ecr.aws/simply-block`); digest pinning<br />(@sha256:...) is recommended. |  | Pattern: `^($\|(quay\.io/simplyblock-io\|docker\.io/simplyblock\|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]\{64\})?)$` <br />Required: \{\} <br /> |
| `imagePullPolicy` _[PullPolicy](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#pullpolicy-v1-core)_ | ImagePullPolicy controls when that image is pulled. | IfNotPresent | Enum: [Always Never IfNotPresent] <br />Optional: \{\} <br /> |
| `foundationDB` _[FoundationDBSpec](#foundationdbspec)_ | FoundationDB sizes the FoundationDB the management API stores its state in. |  | Optional: \{\} <br /> |
| `replicas` _integer_ | Replicas is the number of management API instances. Two is what the chart<br />ships and what the phases assume: a single instance makes Degraded<br />unreachable for this component and every restart an outage (§5.1). | 2 | Minimum: 1 <br />Optional: \{\} <br /> |
| `resources` _[ResourceRequirements](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#resourcerequirements-v1-core)_ | Resources sets requests and limits for the management API pods. |  | Optional: \{\} <br /> |
| `tolerations` _[Toleration](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#toleration-v1-core) array_ | Tolerations are applied to every pod the operator installs for the control<br />plane. |  | Optional: \{\} <br /> |
| `nodeSelector` _object (keys:string, values:string)_ | NodeSelector pins every pod the operator installs for the control plane.<br />It is a selector rather than an affinity term because that is what the<br />chart it replaces took, and a deployment migrating off the chart has the<br />value already written down. |  | Optional: \{\} <br /> |
| `tls` _[ControlPlaneTLS](#controlplanetls)_ | TLS is how this control plane serves and what it asks of its callers.<br />The block is defaulted to its own zero value rather than left absent, so<br />that the field defaults inside it are applied to an object that does not<br />mention TLS at all. | \{  \} | Optional: \{\} <br /> |


#### ManagedControlPlane



ManagedControlPlane is a control plane somewhere else, which this cluster's
storage is managed by rather than hosting. The operator installs nothing and
owns nothing here: it resolves the endpoint, probes it, and reports.

The word is about what manages the storage clusters rather than about who
runs the operator. A deployment in this mode registers its clusters with a
control plane it does not host, so the fleet is administered from there.



_Appears in:_
- [ControlPlaneSource](#controlplanesource)

_Example:_

```yaml
endpoint: '^https?://[a-zA-Z0-9.-]+(:[0-9]{1,5})?(/.*)?$'
credentialsSecretRef: LocalObjectReference
caBundleSecretRef: LocalObjectReference
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `endpoint` _string_ | Endpoint is the management API's base URL. It is validated against the<br />same outbound-URL guard every other outbound endpoint in this group uses,<br />so a loopback or link-local address is rejected. |  | Pattern: `^https?://[a-zA-Z0-9.-]+(:[0-9]\{1,5\})?(/.*)?$` <br />Required: \{\} <br /> |
| `credentialsSecretRef` _[LocalObjectReference](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#localobjectreference-v1-core)_ | CredentialsSecretRef names a Secret in this namespace holding the bearer<br />token the operator authenticates with. It is a reference rather than a<br />field because a token in a spec is a token in every `kubectl get -o yaml`.<br />Absent means the endpoint is reached without one, which is the in-cluster<br />case: a control plane the Helm chart installed answers on a ClusterIP<br />Service in this namespace and does not require a token for the readiness<br />read. Naming a Secret that does not exist stays an error, because naming<br />one is a statement that the control plane needs it. |  | Optional: \{\} <br /> |
| `caBundleSecretRef` _[LocalObjectReference](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#localobjectreference-v1-core)_ | CABundleSecretRef names a Secret holding the CA certificate the endpoint<br />is verified against. Absent means the system trust store. |  | Optional: \{\} <br /> |


#### MetricsBackend

_Underlying type:_ _string_

MetricsBackend selects where the rebalancer reads a node's I/O load from.
The values are PascalCase, as every enum this group defines is; v1alpha1
spelled them lowercase and the conversion maps between the two.

_Validation:_
- Enum: [ControlPlane Prometheus Uniform]

_Appears in:_
- [VolumeAutoPlacementSettings](#volumeautoplacementsettings)

| Field | Description |
| --- | --- |
| `ControlPlane` |  |
| `Prometheus` |  |
| `Uniform` | MetricsBackendUniform reports IOPS=1 for every node, which disables<br />IOPS-based scoring while leaving capacity and volume-count balancing<br />active.<br /> |


#### MigrateSpec



MigrateSpec parameterizes the Migrate action and is ignored by the others.

A migration is not a removal followed by an add: the node keeps its backend
UUID, its partitions, and its logical-volume assignments, and what changes is
the machine the SPDK process runs on. No PersistentVolumeOps is created.



_Appears in:_
- [StorageNodeOpsSpec](#storagenodeopsspec)

_Example:_

```yaml
targetWorkerNode: string
newSsdPcie:
  - string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `targetWorkerNode` _string_ | TargetWorkerNode is the Kubernetes worker the node is relocated onto. |  | Required: \{\} <br /> |
| `newSsdPcie` _string array_ | NewSsdPcie lists additional NVMe PCI addresses to bind on the target host,<br />passed through to the control-plane restart as new_ssd_pcie and merged into<br />the node's effective allow list so they survive a later rebuild. |  | Optional: \{\} <br /> |


#### MigrateVolumeSpec



MigrateVolumeSpec parameterizes the Migrate action.



_Appears in:_
- [PersistentVolumeOpsSpec](#persistentvolumeopsspec)

_Example:_

```yaml
targetNodeRef:
  namespace: string
  name: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `targetNodeRef` _[StorageNodeReference](#storagenodereference)_ | TargetNodeRef locates the StorageNode to move the volume's backing<br />logical volume to. It names the Kubernetes object rather than the backend<br />UUID, so that a migration can be written by hand without looking one up;<br />the controller resolves the UUID from the node's status. The node's<br />cluster must be the volume's, which the webhook checks rather than the<br />type, because that is a fact about two other objects.<br />The marker sits on the reference rather than on its fields, so the pair<br />is immutable together and a target cannot be half-changed into a name in<br />one cluster and a namespace in another. |  | Required: \{\} <br /> |


#### MigrationConnection



MigrationConnection is one NVMe-oF path the migration published on the
target.

The connect parameters travel with the address because the path is connected
on a consuming host rather than here, and what is recorded has to be the
connect that will actually be made: the host attaches every path with the
same controller-loss timeout the CSI driver uses, which is not the hour the
control plane answers with, and a record of the control plane's answer would
describe a connect nobody performs.



_Appears in:_
- [MigrationStatus](#migrationstatus)

_Example:_

```yaml
nqn: string
address: string
port: integer
transport: string
nrIOQueues: integer
reconnectDelaySeconds: integer
ctrlLossTimeoutSeconds: integer
fastIOFailTimeoutSeconds: integer
keepAliveTimeoutSeconds: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `nqn` _string_ | NQN is the subsystem the target answers this path for. |  | Optional: \{\} <br /> |
| `address` _string_ | Address and Port are where it answers. |  | Optional: \{\} <br /> |
| `port` _integer_ |  |  | Optional: \{\} <br /> |
| `transport` _string_ | Transport is the fabric, which is TCP. |  | Optional: \{\} <br /> |
| `nrIOQueues` _integer_ |  |  | Optional: \{\} <br /> |
| `reconnectDelaySeconds` _integer_ |  |  | Optional: \{\} <br /> |
| `ctrlLossTimeoutSeconds` _integer_ | CtrlLossTimeoutSeconds and FastIOFailTimeoutSeconds are pointers because<br />zero is a choice ("fail I/O immediately") rather than a missing value. |  | Optional: \{\} <br /> |
| `fastIOFailTimeoutSeconds` _integer_ |  |  | Optional: \{\} <br /> |
| `keepAliveTimeoutSeconds` _integer_ |  |  | Optional: \{\} <br /> |


#### MigrationStatus



MigrationStatus is everything about the migration rather than about the
operation. It is durable working state: a controller that restarts mid-copy
reads it to find the backend migration it started and the Jobs it has to
clean up (design-crd-model.md §3.1).



_Appears in:_
- [PersistentVolumeOpsStatus](#persistentvolumeopsstatus)

_Example:_

```yaml
migrationUUID: string
clusterUUID: string
poolUUID: string
volumeUUID: string
subsystemNQN: string
sourceNodeUUID: string
targetNodeUUID: string
continuedAt: Time
memberCount: integer
connections:
  - nqn: string
    address: string
    port: integer
    transport: string
    nrIOQueues: integer
    reconnectDelaySeconds: integer
    ctrlLossTimeoutSeconds: integer
    fastIOFailTimeoutSeconds: integer
    keepAliveTimeoutSeconds: integer
validationJobs:
  - namespace: string
    name: string
    node: string
    succeeded: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `migrationUUID` _string_ | MigrationUUID is the control plane's identifier for the copy. |  | Optional: \{\} <br /> |
| `clusterUUID` _string_ | ClusterUUID, PoolUUID, and VolumeUUID are the three parts of the volume's<br />CSI volume handle, recorded so that later steps address the backend<br />without re-reading the PersistentVolume, and so that a failed operation<br />says which volume it was working on after the volume is gone. |  | Optional: \{\} <br /> |
| `poolUUID` _string_ |  |  | Optional: \{\} <br /> |
| `volumeUUID` _string_ |  |  | Optional: \{\} <br /> |
| `subsystemNQN` _string_ | SubsystemNQN is the volume's NVMe-oF subsystem, which is what the<br />migration is addressed by: the control plane migrates a subsystem rather<br />than one volume inside it. |  | Optional: \{\} <br /> |
| `sourceNodeUUID` _string_ | SourceNodeUUID is where the volume was before the move, recorded so that<br />a failure says what it was and not only what it was going to be. |  | Optional: \{\} <br /> |
| `targetNodeUUID` _string_ | TargetNodeUUID is the backend identifier resolved from<br />spec.migrate.targetNodeRef, recorded so the later steps address the<br />target without resolving the node object again. |  | Optional: \{\} <br /> |
| `continuedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | ContinuedAt is when this operation asked the control plane to start the<br />copy, written before the call rather than after it.<br />The order is what makes the request at-most-once, and that is the point.<br />A repeated continue is the shape that has lost writes here: a read<br />timeout on a call that had in fact committed made the operator retry a<br />transfer, and the retry copied nothing while the source was unfrozen. So<br />a recorded continue is never issued again, and an operation that crashed<br />between this write and the call waits out its step's deadline instead —<br />a rare stall, against a silent data loss. |  | Optional: \{\} <br /> |
| `memberCount` _integer_ | MemberCount is how many volumes the migrated NVMe-oF subsystem holds, as<br />the control plane reports it. More than one member means the sibling<br />volumes move along with the named one, so the count is both the<br />operation's blast radius and the term the copy's deadline scales by. |  | Minimum: 0 <br />Optional: \{\} <br /> |
| `connections` _[MigrationConnection](#migrationconnection) array_ | Connections are the paths the migration published on the target.<br />Verifying confirms none of them is left connected. |  | Optional: \{\} <br /> |
| `validationJobs` _[ValidationJob](#validationjob) array_ | ValidationJobs are the Jobs started to check those paths. |  | Optional: \{\} <br /> |


#### NodeGroup



NodeGroup is a set of workers that share one configuration, which is what
makes ten identical machines one entry rather than ten.



_Appears in:_
- [NodeSet](#nodeset)

_Example:_

```yaml
name: string
workers:
  - string
mgmtInterface: string
dataInterfaces:
  - string
devices:
  nvme:
    - '^[0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F]$'
  block:
    - '^/dev/[a-zA-Z0-9._/-]+$'
failureDomain: '^[a-zA-Z0-9]([-_.a-zA-Z0-9]*[a-zA-Z0-9])?$'
spdkSystemMemory: '^[0-9]+(G|GI|GB|GiB|M|MI|MB|MiB|g|gi|gb|gib|m|mi|mb|mib)?$'
reservedSystemCPU: '^[0-9]+(-[0-9]+)?(,[0-9]+(-[0-9]+)?)*$'
journalManager:
  count: integer
  percentPerDevice: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `name` _string_ | Name identifies the group within its node set, for a reader and for the<br />events a validation failure emits. |  | MaxLength: 253 <br />Required: \{\} <br /> |
| `workers` _string array_ | Workers are the Kubernetes worker hostnames in this group. |  | MaxItems: 200 <br />MinItems: 1 <br />Required: \{\} <br />items:MaxLength: 253 <br /> |
| `mgmtInterface` _string_ | MgmtInterface is the management network interface the storage nodes bind. |  | MaxLength: 63 <br />Optional: \{\} <br /> |
| `dataInterfaces` _string array_ | DataInterfaces are the data-plane network interfaces. |  | MaxItems: 32 <br />items:MaxLength: 63 <br />Optional: \{\} <br /> |
| `devices` _[DeviceSelection](#deviceselection)_ | Devices selects the storage devices every worker in the group uses. |  | Optional: \{\} <br /> |
| `failureDomain` _string_ | FailureDomain is the label of the fault group every worker in this group<br />belongs to ("rack-b"), which is usually the name of the rack, zone, or<br />power feed they share. Discovery seeds it from topology.kubernetes.io/zone<br />and leaves it unset where the Kubernetes API carries no topology, which<br />holds provisioning with a clear reason rather than guessing. It expands<br />into StorageNode.spec.config.failureDomain, whose shape it shares. |  | MaxLength: 63 <br />Pattern: `^[a-zA-Z0-9]([-_.a-zA-Z0-9]*[a-zA-Z0-9])?$` <br />Optional: \{\} <br /> |
| `spdkSystemMemory` _string_ | SpdkSystemMemory is the memory the control plane starts SPDK with on these<br />nodes. |  | MaxLength: 32 <br />Pattern: `^[0-9]+(G\|GI\|GB\|GiB\|M\|MI\|MB\|MiB\|g\|gi\|gb\|gib\|m\|mi\|mb\|mib)?$` <br />Optional: \{\} <br /> |
| `reservedSystemCPU` _string_ | ReservedSystemCPU is the CPU set held back from SPDK for the system on<br />these nodes, as a core list such as 0,1 or 0-3.<br />It is a group's rather than the cluster's because it names core ids, and a<br />group is what a document calls the workers that share their hardware: 0,1<br />on a sixteen-core worker and 0,1 on a ninety-six-core worker are different<br />fractions of the machine. It expands into<br />StorageNode.spec.config.reservedSystemCPU, whose shape it shares, and a<br />group that states none leaves the cluster's fleet-wide value to decide.<br />On OpenShift it reaches the kubelet through a KubeletConfig for the<br />machine config pool, which is the cluster's, so groups that disagree there<br />are writing over one another's pool configuration. |  | MaxLength: 63 <br />Pattern: `^[0-9]+(-[0-9]+)?(,[0-9]+(-[0-9]+)?)*$` <br />Optional: \{\} <br /> |
| `journalManager` _[JournalManagerSpec](#journalmanagerspec)_ | JournalManager tunes the journal managers on these nodes. |  | Optional: \{\} <br /> |


#### NodeLatencyMetrics



NodeLatencyMetrics is the fio-measured 4K NVMe-oF write latency of one backend
storage node, which is the denominator of the rebalancer's deviation signal.

It is a node's reading and it lives on the node. The retired StorageNodeSet
collected one entry per node in a fleet-wide list, which made every node's
measurement a write to one object shared by all of them.



_Appears in:_
- [StorageNodeStatus](#storagenodestatus)

_Example:_

```yaml
nodeUUID: string
baselineP50NS: integer
baselineP99NS: integer
baselineMeasuredAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `nodeUUID` _string_ | NodeUUID is the backend storage node the reading was taken against. It is<br />carried beside the reading rather than inferred from status.uuid, because a<br />baseline measured against one backend node stops describing the slot once a<br />replacement fills it. |  | Required: \{\} <br /> |
| `baselineP50NS` _integer_ | BaselineP50NS is the p50 write latency, in nanoseconds, of the initial<br />empty-cluster benchmark. |  | Minimum: 0 <br />Optional: \{\} <br /> |
| `baselineP99NS` _integer_ | BaselineP99NS is the p99 write latency, in nanoseconds, of the same<br />benchmark. |  | Minimum: 0 <br />Optional: \{\} <br /> |
| `baselineMeasuredAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | BaselineMeasuredAt is when the baseline was established. |  | Optional: \{\} <br /> |


#### NodeLoadMetrics



NodeLoadMetrics is one storage node's latency deviation, as the last
evaluation cycle measured it.



_Appears in:_
- [RebalancingMetrics](#rebalancingmetrics)

_Example:_

```yaml
nodeUUID: string
latencyDeviationPct: float
volumeCount: integer
lastUpdated: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `nodeUUID` _string_ |  |  |  |
| `latencyDeviationPct` _float_ |  |  |  |
| `volumeCount` _integer_ |  |  |  |
| `lastUpdated` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ |  |  |  |


#### NodeSet



NodeSet is the organizational grouping of a deployment, usually a rack: the
workers a document adds or grows together. It carries no sizing, because sizing
is uniform across a cluster and is stated once in ClusterTemplate.



_Appears in:_
- [ClusterDeploymentConfigSpec](#clusterdeploymentconfigspec)

_Example:_

```yaml
name: string
groups:
  - name: string
    workers:
      - string
    mgmtInterface: string
    dataInterfaces:
      - string
    devices:
      nvme:
        - '^[0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F]$'
      block:
        - '^/dev/[a-zA-Z0-9._/-]+$'
    failureDomain: '^[a-zA-Z0-9]([-_.a-zA-Z0-9]*[a-zA-Z0-9])?$'
    spdkSystemMemory: '^[0-9]+(G|GI|GB|GiB|M|MI|MB|MiB|g|gi|gb|gib|m|mi|mb|mib)?$'
    reservedSystemCPU: '^[0-9]+(-[0-9]+)?(,[0-9]+(-[0-9]+)?)*$'
    journalManager:
      count: integer
      percentPerDevice: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `name` _string_ | Name is the node set's name. It is copied to StorageNode.spec.nodeSet, so<br />that a node can be traced back to the part of the document that produced<br />it. |  | MaxLength: 253 <br />Required: \{\} <br /> |
| `groups` _[NodeGroup](#nodegroup) array_ | Groups are the sets of workers sharing one configuration. |  | MaxItems: 64 <br />MinItems: 1 <br />Required: \{\} <br /> |


#### OpenShiftSpec



OpenShiftSpec is what a deployment onto OpenShift states beyond what every
distribution states.

Its presence is the statement. A cluster carrying the block runs on OpenShift
and one without it does not, which is why there is no boolean beside it: a
block naming a machine-config pool on a cluster that also said it was not
OpenShift was expressible before and meant nothing.



_Appears in:_
- [ClusterTemplate](#clustertemplate)
- [StorageNodesSpec](#storagenodesspec)

_Example:_

```yaml
machineConfigPool: '^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `machineConfigPool` _string_ | MachineConfigPool names a machine-config role the storage nodes' own pool<br />inherits from, beyond the worker role it always inherits.<br />It is not the pool the nodes end up in, which the description it carried<br />before said and which cost a reader the reboot they were trying to avoid.<br />Adding a node creates a pool of its own, storage-<cluster>, and moves the<br />node into it; a node belongs to exactly one custom pool, so whatever<br />machine configuration its previous pool carried is lost unless that<br />pool's role is named here for the new one to select as well. The default<br />is the role every pool already selects, which is what makes it a no-op<br />for a fleet whose workers are ordinary workers. | worker | MaxLength: 253 <br />Pattern: `^[a-z0-9]([-a-z0-9]*[a-z0-9])?$` <br />Optional: \{\} <br /> |


#### OperatorOps



OperatorOps is a single operation performed against the operator itself,
which today means a discovery run that writes a ClusterDeploymentConfig. It
runs to a terminal phase and stays afterward as the audit record.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha2
kind: OperatorOps
metadata:
  name: string
spec:
  action: OperatorOpsAction
  abort: boolean
  discover:
    configName: string
    workers:
      - string
    nodeSelector:
      string: string
    tolerations:
      - Toleration
    enableControlPlaneNodes: boolean
    deviceFilter:
      enableLogicalBlockDevices: boolean
      enablePartitionedDevices: boolean
      pcieAllowList:
        - string
      pcieDenyList:
        - string
      pcieModel: string
      blockAllowList:
        - '^/dev/[a-zA-Z0-9._/-]+$'
      blockDenyList:
        - '^/dev/[a-zA-Z0-9._/-]+$'
      driveSizeRange: string
    clusterRef: string
status:
  phase: OperatorOpsPhase
  step: KubeSnapshot
  configRef: string
  workers:
    - string
  environment: KubernetesEnvironment
  message: string
  observedGeneration: integer
  startedAt: Time
  completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha2` | | |
| `kind` _string_ | `OperatorOps` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  |  |
| `spec` _[OperatorOpsSpec](#operatoropsspec)_ |  |  |  |
| `status` _[OperatorOpsStatus](#operatoropsstatus)_ |  |  |  |


#### OperatorOpsAction

_Underlying type:_ _string_

OperatorOpsAction is the operation an OperatorOps performs.

The field stays with one value in it. Every Ops kind in this group is
dispatched on spec.action, so a kind that left its single action implicit
would be the one kind whose shape has to change the day it gains a second.

_Validation:_
- Enum: [Discover]

_Appears in:_
- [OperatorOpsSpec](#operatoropsspec)

| Field | Description |
| --- | --- |
| `Discover` |  |


#### OperatorOpsPhase

_Underlying type:_ _string_

OperatorOpsPhase is the operation's own progress.

_Validation:_
- Enum: [Pending Running Succeeded Failed Aborted]

_Appears in:_
- [OperatorOpsStatus](#operatoropsstatus)

| Field | Description |
| --- | --- |
| `Pending` |  |
| `Running` |  |
| `Succeeded` |  |
| `Failed` |  |
| `Aborted` |  |


#### OperatorOpsSpec



OperatorOpsSpec is one operation to perform against the operator itself.

It carries no target reference. Every other Ops kind in this group names the
entity it acts on; this one acts on the operator process, which is not a
resource in this API group, and the absent field is the signal.



_Appears in:_
- [OperatorOps](#operatorops)

_Example:_

```yaml
action: OperatorOpsAction
abort: boolean
discover:
  configName: string
  workers:
    - string
  nodeSelector:
    string: string
  tolerations:
    - Toleration
  enableControlPlaneNodes: boolean
  deviceFilter:
    enableLogicalBlockDevices: boolean
    enablePartitionedDevices: boolean
    pcieAllowList:
      - string
    pcieDenyList:
      - string
    pcieModel: string
    blockAllowList:
      - '^/dev/[a-zA-Z0-9._/-]+$'
    blockDenyList:
      - '^/dev/[a-zA-Z0-9._/-]+$'
    driveSizeRange: string
  clusterRef: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `action` _[OperatorOpsAction](#operatoropsaction)_ | Action is the operation to perform. |  | Enum: [Discover] <br />Required: \{\} <br /> |
| `abort` _boolean_ | Abort asks a running operation to stop at its next step and unwind.<br />Whether an abort is expressible from the current step is declared by that<br />action's graph rather than checked here. Discovery changes nothing, so an<br />aborted run leaves behind at most the config it had already written. |  | Optional: \{\} <br /> |
| `discover` _[DiscoverSpec](#discoverspec)_ | Discover parameterizes action Discover. |  | Optional: \{\} <br /> |


#### OperatorOpsStatus



OperatorOpsStatus is the observed state of one operator operation.



_Appears in:_
- [OperatorOps](#operatorops)

_Example:_

```yaml
phase: OperatorOpsPhase
step: KubeSnapshot
configRef: string
workers:
  - string
environment: KubernetesEnvironment
message: string
observedGeneration: integer
startedAt: Time
completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _[OperatorOpsPhase](#operatoropsphase)_ | Phase is the operation's own progress. |  | Enum: [Pending Running Succeeded Failed Aborted] <br />Optional: \{\} <br /> |
| `step` _[KubeSnapshot](https://github.com/simplyblock/simplyblock-operator/blob/main/atlas-lib/statemachine/kubernetes.go)_ | Step is the position of the running action's state machine. |  | Optional: \{\} <br /> |
| `configRef` _string_ | ConfigRef names the ClusterDeploymentConfig a Discover run wrote. |  | Optional: \{\} <br /> |
| `workers` _string array_ | Workers are the workers this run is inspecting, decided once in<br />Inspecting so that a node joining the cluster mid-run does not change<br />what the run is about. |  | Optional: \{\} <br /> |
| `environment` _[KubernetesEnvironment](#kubernetesenvironment)_ | Environment is the Kubernetes distribution Inspecting concluded, which<br />Writing copies into the draft. It is recorded here as well so that a run<br />that failed later still says what it found. |  | Enum: [Vanilla OpenShift Rancher K3s Talos] <br />Optional: \{\} <br /> |
| `message` _string_ | Message is the reason the phase is what it is: one sentence, replaced as<br />the operation moves, and never a log. |  | Optional: \{\} <br /> |
| `observedGeneration` _integer_ | ObservedGeneration is the generation the rest of this status was computed<br />from, so a stale status can be told from a current one. |  | Optional: \{\} <br /> |
| `startedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | StartedAt is when the operation started. |  | Optional: \{\} <br /> |
| `completedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | CompletedAt is when it reached a terminal phase. |  | Optional: \{\} <br /> |




#### PersistentVolumeOps



PersistentVolumeOps is a single operation performed against one
PersistentVolume. It is the one Ops kind in this group whose target is a core
Kubernetes type rather than a kind this group defines, so it locks its target
with an annotation rather than a status field, is cluster-scoped because its
target is, cannot be owned by the namespaced operation that created it, and
derives its cluster, pool, and volume from the volume's CSI handle rather
than being told.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha2
kind: PersistentVolumeOps
metadata:
  name: string
spec:
  persistentVolumeName: string
  action: PersistentVolumeOpsAction
  abort: boolean
  migrate:
    targetNodeRef:
      namespace: string
      name: string
  creatorRef:
    kind: string
    namespace: string
    name: string
    uid: UID
status:
  phase: PersistentVolumeOpsPhase
  step: KubeSnapshot
  migration:
    migrationUUID: string
    clusterUUID: string
    poolUUID: string
    volumeUUID: string
    subsystemNQN: string
    sourceNodeUUID: string
    targetNodeUUID: string
    continuedAt: Time
    memberCount: integer
    connections:
      - nqn: string
        address: string
        port: integer
        transport: string
        nrIOQueues: integer
        reconnectDelaySeconds: integer
        ctrlLossTimeoutSeconds: integer
        fastIOFailTimeoutSeconds: integer
        keepAliveTimeoutSeconds: integer
    validationJobs:
      - namespace: string
        name: string
        node: string
        succeeded: boolean
  deferredSince: Time
  message: string
  observedGeneration: integer
  startedAt: Time
  completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha2` | | |
| `kind` _string_ | `PersistentVolumeOps` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  |  |
| `spec` _[PersistentVolumeOpsSpec](#persistentvolumeopsspec)_ |  |  |  |
| `status` _[PersistentVolumeOpsStatus](#persistentvolumeopsstatus)_ |  |  |  |


#### PersistentVolumeOpsAction

_Underlying type:_ _string_

PersistentVolumeOpsAction is the operation a PersistentVolumeOps performs.
The kind is named for its target rather than for the action so that carrying
a second one later would not rename it; it carries one, and no second one is
planned (design-persistentvolumeops.md §4.1).

_Validation:_
- Enum: [Migrate]

_Appears in:_
- [PersistentVolumeOpsSpec](#persistentvolumeopsspec)

| Field | Description |
| --- | --- |
| `Migrate` | PersistentVolumeOpsActionMigrate moves the volume's backing logical<br />volume to a different storage node.<br /> |


#### PersistentVolumeOpsPhase

_Underlying type:_ _string_

PersistentVolumeOpsPhase is the operation's own progress. Succeeded rather
than the registered kind's Completed, so that every Ops kind in this group
reports the same five phases and an alert on completion matches one value.

_Validation:_
- Enum: [Pending Running Succeeded Failed Aborted]

_Appears in:_
- [PersistentVolumeOpsStatus](#persistentvolumeopsstatus)

| Field | Description |
| --- | --- |
| `Pending` | PersistentVolumeOpsPhasePending is an operation waiting for the volume's<br />lock, or holding nothing yet.<br /> |
| `Running` | PersistentVolumeOpsPhaseRunning is an operation holding the lock and<br />working.<br /> |
| `Succeeded` | PersistentVolumeOpsPhaseSucceeded is a finished operation that did what<br />it said.<br /> |
| `Failed` | PersistentVolumeOpsPhaseFailed is a finished operation that did not.<br /> |
| `Aborted` | PersistentVolumeOpsPhaseAborted is an operation stopped on request, or<br />stopped because its volume went away, whose unwind has finished.<br /> |


#### PersistentVolumeOpsSpec



PersistentVolumeOpsSpec is one operation to perform against one
PersistentVolume.

The rule keeps the action and its parameter block in agreement, which is a
statement about this object alone and so belongs on the type rather than in
the webhook.



_Appears in:_
- [PersistentVolumeOps](#persistentvolumeops)

_Example:_

```yaml
persistentVolumeName: string
action: PersistentVolumeOpsAction
abort: boolean
migrate:
  targetNodeRef:
    namespace: string
    name: string
creatorRef:
  kind: string
  namespace: string
  name: string
  uid: UID
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `persistentVolumeName` _string_ | PersistentVolumeName names the PersistentVolume this operation acts on.<br />It is a name rather than a reference because a PersistentVolume is<br />cluster-scoped, and it names the volume rather than the claim because a<br />claim can be deleted while its volume is retained — under a Retain<br />reclaim policy the logical volume still occupies capacity on a node that<br />may be draining, and is still worth moving. |  | Required: \{\} <br /> |
| `action` _[PersistentVolumeOpsAction](#persistentvolumeopsaction)_ | Action is the operation to perform. Immutable: an operation that changed<br />what it was doing halfway through would have a status describing neither. |  | Enum: [Migrate] <br />Required: \{\} <br /> |
| `abort` _boolean_ | Abort asks a running operation to stop at its next step and unwind. It is<br />expressible from Validating and Migrating and not from Verifying, which<br />the action's graph declares rather than this field: once the copy has<br />finished, the volume has moved and there is nothing to undo. |  | Optional: \{\} <br /> |
| `migrate` _[MigrateVolumeSpec](#migratevolumespec)_ | Migrate parameterizes action Migrate. |  | Optional: \{\} <br /> |
| `creatorRef` _[CreatorReference](#creatorreference)_ | CreatorRef names the object that created this one, and that object's<br />finalizer is what aborts and deletes this one when it goes. Absent on an<br />operation written by hand, which has no creator to cascade from.<br />Immutable, because an operation changing whose fan-out it belongs to<br />would change who cascades over it. |  | Optional: \{\} <br /> |


#### PersistentVolumeOpsStatus



PersistentVolumeOpsStatus is the observed state of one volume operation.



_Appears in:_
- [PersistentVolumeOps](#persistentvolumeops)

_Example:_

```yaml
phase: PersistentVolumeOpsPhase
step: KubeSnapshot
migration:
  migrationUUID: string
  clusterUUID: string
  poolUUID: string
  volumeUUID: string
  subsystemNQN: string
  sourceNodeUUID: string
  targetNodeUUID: string
  continuedAt: Time
  memberCount: integer
  connections:
    - nqn: string
      address: string
      port: integer
      transport: string
      nrIOQueues: integer
      reconnectDelaySeconds: integer
      ctrlLossTimeoutSeconds: integer
      fastIOFailTimeoutSeconds: integer
      keepAliveTimeoutSeconds: integer
  validationJobs:
    - namespace: string
      name: string
      node: string
      succeeded: boolean
deferredSince: Time
message: string
observedGeneration: integer
startedAt: Time
completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _[PersistentVolumeOpsPhase](#persistentvolumeopsphase)_ | Phase is the operation's own progress. |  | Enum: [Pending Running Succeeded Failed Aborted] <br />Optional: \{\} <br /> |
| `step` _[KubeSnapshot](https://github.com/simplyblock/simplyblock-operator/blob/main/atlas-lib/statemachine/kubernetes.go)_ | Step is the position of the running action's state machine, as the shared<br />statemachine.KubeSnapshot. It is persisted before the side effect that<br />step performs. The rule is what an Enum marker would do if a marker could<br />reach a field of a shared type. |  | Optional: \{\} <br /> |
| `migration` _[MigrationStatus](#migrationstatus)_ | Migration is everything about the migration rather than about the<br />operation. |  | Optional: \{\} <br /> |
| `deferredSince` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | DeferredSince is when the operation was first held — behind another<br />operation's lock, or behind a control plane that is not accepting<br />migrations yet. It is what the auto-rebalancer reads to decide whether a<br />migration has waited long enough to give up on, and it is in status<br />rather than in memory because the operator may restart and an observer<br />needs to see that the operation is waiting and since when. |  | Optional: \{\} <br /> |
| `message` _string_ | Message is the reason the phase is what it is: one sentence, replaced as<br />the operation moves, and never a log. |  | Optional: \{\} <br /> |
| `observedGeneration` _integer_ | ObservedGeneration is the generation the rest of this status was computed<br />from, so a stale status can be told from a current one. |  | Optional: \{\} <br /> |
| `startedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | StartedAt is when the operation began. |  | Optional: \{\} <br /> |
| `completedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | CompletedAt is when it reached a terminal phase. |  | Optional: \{\} <br /> |




#### PoolLimits



PoolLimits are the ceilings the pool as a whole is held to. They are the
pool's budget rather than a volume's: a volume's own defaults are in
StoragePoolSpec.VolumeDefaults, and the two use the same units so that a
reader can compare them.



_Appears in:_
- [StoragePoolSpec](#storagepoolspec)

_Example:_

```yaml
capacity: string
maxVolumeSize: string
iops: integer
throughput:
  read: integer
  write: integer
  readWrite: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `capacity` _string_ | Capacity is the total capacity the pool may allocate, written the way an<br />administrator writes one: `10T`, `500G`. Empty is unlimited. |  | Optional: \{\} <br /> |
| `maxVolumeSize` _string_ | MaxVolumeSize is the largest single logical volume the pool will create.<br />Empty is unlimited. |  | Optional: \{\} <br /> |
| `iops` _integer_ | IOPS is the pool-wide ceiling on operations per second, both directions<br />together. Zero is unlimited, which is the control plane's own convention<br />for these values. |  | Minimum: 0 <br />Optional: \{\} <br /> |
| `throughput` _[ThroughputLimits](#throughputlimits)_ | Throughput is the pool-wide throughput ceiling. |  | Optional: \{\} <br /> |


#### PoolLimitsStatus



PoolLimitsStatus is what the control plane reports the pool's ceilings
actually are, which is not necessarily what Limits asked for.



_Appears in:_
- [StoragePoolStatus](#storagepoolstatus)

_Example:_

```yaml
host: string
iops: integer
throughput:
  read: integer
  write: integer
  readWrite: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `host` _string_ | Host is the backend host enforcing the pool's QoS. |  | Optional: \{\} <br /> |
| `iops` _integer_ | IOPS is the combined ceiling the control plane is enforcing. |  | Optional: \{\} <br /> |
| `throughput` _[ThroughputLimits](#throughputlimits)_ | Throughput is the throughput ceiling the control plane is enforcing. |  | Optional: \{\} <br /> |


#### ProvisioningSlot



StorageClusterStatus is the observed state of one backend cluster.
ProvisioningSlot is one worker's hold on the cluster's node-add concurrency,
held from the moment its add is posted until the node has a backend UUID or
has given up.



_Appears in:_
- [StorageClusterStatus](#storageclusterstatus)

_Example:_

```yaml
worker: string
node: string
takenAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `worker` _string_ | Worker is the Kubernetes node the add was posted for, and it is what the<br />cap counts. |  |  |
| `node` _string_ | Node is the StorageNode object that took the slot. A release removes only<br />the entry naming its own object, which is what keeps a node from freeing<br />somebody else's slot, and a slot whose object is gone is reaped. |  |  |
| `takenAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | TakenAt is when the slot was taken, so a hold that outlives its node's<br />deadlines is visible in the object rather than only in the events. |  | Optional: \{\} <br /> |


#### RebalancingMetrics



RebalancingMetrics is written by the auto-rebalancer each evaluation cycle.



_Appears in:_
- [StorageClusterStatus](#storageclusterstatus)

_Example:_

```yaml
avgDeviationPct: float
maxDeviationPct: float
hottestNodeUUID: string
coolestNodeUUID: string
imbalancePercent: float
lastEvaluatedAt: Time
lastMigrationAt: Time
nodeMetrics:
  - nodeUUID: string
    latencyDeviationPct: float
    volumeCount: integer
    lastUpdated: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `avgDeviationPct` _float_ | AvgDeviationPct is the mean latency deviation across the cluster's nodes. |  |  |
| `maxDeviationPct` _float_ | MaxDeviationPct is the highest per-node latency deviation, which is what<br />ImbalancePercent reports. |  |  |
| `hottestNodeUUID` _string_ |  |  |  |
| `coolestNodeUUID` _string_ |  |  |  |
| `imbalancePercent` _float_ |  |  |  |
| `lastEvaluatedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ |  |  |  |
| `lastMigrationAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ |  |  |  |
| `nodeMetrics` _[NodeLoadMetrics](#nodeloadmetrics) array_ |  |  |  |


#### RemoveSpec



RemoveSpec parameterizes the Remove action and is ignored by the others.



_Appears in:_
- [StorageNodeOpsSpec](#storagenodeopsspec)

_Example:_

```yaml
systemVolumeFilterRegex: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `systemVolumeFilterRegex` _string_ | SystemVolumeFilterRegex matches backend volume names that are system<br />volumes: excluded from the drain's migration and deleted during<br />verification rather than blocking it. | ^sb-fio-baseline-.* | Optional: \{\} <br /> |


#### RestartSpec



RestartSpec parameterizes the Restart action and is ignored by the others.



_Appears in:_
- [ControlPlaneOpsSpec](#controlplaneopsspec)

_Example:_

```yaml
components:
  - string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `components` _string array_ | Components names the workloads to recycle, from the table in §4.3. Empty<br />recycles the whole control plane. Naming only components that table marks<br />non-essential skips the drain, because recycling them interrupts nothing. |  | Optional: \{\} <br /> |


#### RestoreOpsSpec



RestoreOpsSpec carries the parameters of the Restore action.



_Appears in:_
- [VolumeGroupSnapshotOpsSpec](#volumegroupsnapshotopsspec)

_Example:_

```yaml
namePrefix: string
storageClassName: string
consistencyGroup: string
enablePartialRestore: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `namePrefix` _string_ | NamePrefix prefixes every restored claim's name:<br /><namePrefix>-<source PVC name>, the source name read from the member<br />snapshot's spec.source.persistentVolumeClaimName. Defaults to the<br />operation's own name. |  | Optional: \{\} <br /> |
| `storageClassName` _string_ | StorageClassName is the class every restored claim requests. When empty,<br />each claim inherits the class of its member snapshot's source claim, and<br />the restore fails for a member whose source claim no longer exists. |  | Optional: \{\} <br /> |
| `consistencyGroup` _string_ | ConsistencyGroup labels every restored claim with<br />storage.simplyblock.io/consistency-group: <value>, so the clones form a<br />new group at provisioning under the mandatory placement rule. Empty<br />leaves the clones as independent, mutually consistent volumes. |  | Optional: \{\} <br /> |
| `enablePartialRestore` _boolean_ | EnablePartialRestore restores the members an incomplete generation still<br />has instead of failing the operation. Off by default: an incomplete<br />generation fails, naming the missing members. |  | Optional: \{\} <br /> |


#### RestoreSpec



RestoreSpec parameterizes the Restore action.

It carries no size, no access mode, and no volume mode, which the registered
BackupRestore took as a whole PersistentVolumeClaim template. All three are
facts about the backup rather than choices: a restored volume is the size of
the copy, and asking for a different one is either a truncation or a lie. The
controller reads the size off status.backup.size and mounts the filesystem
status.source.fsType records.



_Appears in:_
- [StorageBackupOpsSpec](#storagebackupopsspec)

_Example:_

```yaml
claimName: string
targetPool: string
claimLabels:
  string: string
claimAnnotations:
  string: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `claimName` _string_ | ClaimName is the PersistentVolumeClaim to create. It must not already<br />exist: a restore that adopted an existing claim would replace a running<br />workload's data with the backup's. |  | Required: \{\} <br /> |
| `targetPool` _string_ | TargetPool is the StoragePool to restore into. It is required rather than<br />defaulted: a backup found in the store may have been written by another<br />cluster, so status.source.poolName names a pool this cluster need not<br />have, and which pool a volume lands in is a tenancy and QoS decision<br />nobody should make by omission. |  | Required: \{\} <br /> |
| `claimLabels` _object (keys:string, values:string)_ | ClaimLabels and ClaimAnnotations are applied to the created claim, so that<br />a restored volume can be selected by a policy or an application the same<br />way its original was.<br />Immutable with the rest of the block. The claim is written at the last<br />step, so a value edited while the operation waited for its volume would<br />produce a claim built from inputs the admitted and audited operation never<br />carried, which is the audit record disagreeing with what happened. |  | Optional: \{\} <br /> |
| `claimAnnotations` _object (keys:string, values:string)_ |  |  | Optional: \{\} <br /> |


#### RestoredMemberStatus



RestoredMemberStatus records one member snapshot and the claim restored
from it.



_Appears in:_
- [VolumeGroupSnapshotOpsStatus](#volumegroupsnapshotopsstatus)

_Example:_

```yaml
volumeSnapshotName: string
persistentVolumeClaimName: string
bound: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `volumeSnapshotName` _string_ | VolumeSnapshotName is the member VolumeSnapshot the claim restores from. |  |  |
| `persistentVolumeClaimName` _string_ | PersistentVolumeClaimName is the restored claim. |  |  |
| `bound` _boolean_ | Bound reports whether the restored claim has bound. |  | Optional: \{\} <br /> |


#### RollingRestartSpec



RollingRestartSpec parameterizes the RollingRestart action.



_Appears in:_
- [StorageClusterOpsSpec](#storageclusteropsspec)

_Example:_

```yaml
refreshSNodeAPI: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `refreshSNodeAPI` _boolean_ | RefreshSNodeAPI restarts each node's storage-node DaemonSet pod between<br />its shutdown and its restart, so the latest image is running when the<br />node returns. |  | Optional: \{\} <br /> |


#### RollingRestartStatus



RollingRestartStatus is the walk's position over the cluster's nodes. Where
the machine has got to within the node currently being restarted is
status.step, and neither field is complete without the other.



_Appears in:_
- [StorageClusterOpsStatus](#storageclusteropsstatus)

_Example:_

```yaml
nodes:
  - string
nodeIndex: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `nodes` _string array_ | Nodes is the ordered list of storage node UUIDs this action covers,<br />written once when the walk starts and not modified afterward, so a node<br />added mid-walk is not restarted and one removed mid-walk is skipped when<br />the walk reaches it. |  | Optional: \{\} <br /> |
| `nodeIndex` _integer_ | NodeIndex is the position in Nodes of the node being restarted. Advancing<br />the walk increments it, and the walk is complete when it reaches<br />len(Nodes).<br />No omitempty: zero is a valid index, and a field that disappears at zero<br />makes "the first node" and "unset" the same wire value. |  | Minimum: 0 <br /> |


#### SidecarImages



SidecarImages overrides the CSI sidecar images this deployment runs. An unset
field takes the version this operator release ships, which is the combination
it was tested against, and the fields exist so that a pin a Helm release made
survives the adoption of that release's deployment.

Every field carries the registry pattern Image carries. The node plugin is
privileged and mounts /dev, /sys, and the kubelet's plugin directory from the
host, so a sidecar beside it runs with the same access.



_Appears in:_
- [SimplyblockDriverSpec](#simplyblockdriverspec)

_Example:_

```yaml
provisioner: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
attacher: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
resizer: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
snapshotter: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
healthMonitor: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
nodeDriverRegistrar: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `provisioner` _string_ | Provisioner is csi-provisioner, on the controller plugin. |  | Pattern: `^($\|(quay\.io/simplyblock-io\|docker\.io/simplyblock\|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]\{64\})?)$` <br />Optional: \{\} <br /> |
| `attacher` _string_ | Attacher is csi-attacher, on the controller plugin. |  | Pattern: `^($\|(quay\.io/simplyblock-io\|docker\.io/simplyblock\|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]\{64\})?)$` <br />Optional: \{\} <br /> |
| `resizer` _string_ | Resizer is csi-resizer, on the controller plugin. |  | Pattern: `^($\|(quay\.io/simplyblock-io\|docker\.io/simplyblock\|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]\{64\})?)$` <br />Optional: \{\} <br /> |
| `snapshotter` _string_ | Snapshotter is csi-snapshotter, on the controller plugin. It is this<br />driver's sidecar and not the cluster's snapshot-controller, whose image<br />is not overridable here because that component belongs to the cluster. |  | Pattern: `^($\|(quay\.io/simplyblock-io\|docker\.io/simplyblock\|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]\{64\})?)$` <br />Optional: \{\} <br /> |
| `healthMonitor` _string_ | HealthMonitor is csi-external-health-monitor-controller, on the<br />controller plugin. |  | Pattern: `^($\|(quay\.io/simplyblock-io\|docker\.io/simplyblock\|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]\{64\})?)$` <br />Optional: \{\} <br /> |
| `nodeDriverRegistrar` _string_ | NodeDriverRegistrar is node-driver-registrar, on the node plugin. |  | Pattern: `^($\|(quay\.io/simplyblock-io\|docker\.io/simplyblock\|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]\{64\})?)$` <br />Optional: \{\} <br /> |


#### SimplyblockDriver



SimplyblockDriver is the deployment of simplyblock's CSI driver: the node
plugin, the controller plugin, their RBAC, and the core CSIDriver registration
they produce. It is named for the brand rather than the interface because
CSIDriver is already a kind in core storage.k8s.io/v1, and the two are not the
same object: the core kind is the cluster's registration record, and this one
is the deployment that produces it.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha2
kind: SimplyblockDriver
metadata:
  name: string
spec:
  image: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
  imagePullPolicy: PullPolicy
  driverName: string
  controllerReplicas: integer
  nodeSelector:
    string: string
  tolerations:
    - Toleration
  controllerNodeSelector:
    string: string
  controllerTolerations:
    - Toleration
  controllerResources: ResourceRequirements
  nodeResources: ResourceRequirements
  sidecarImages:
    provisioner: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
    attacher: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
    resizer: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
    snapshotter: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
    healthMonitor: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
    nodeDriverRegistrar: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
  enableServiceAccountAuth: boolean
  enableVolumeSnapshots: boolean
  tls:
    enableTLS: boolean
    enableMutualTLS: boolean
    provider: DriverTLSProvider
status:
  phase: SimplyblockDriverPhase
  snapshotSupport: SnapshotSupportOrigin
  origin: SimplyblockDriverOrigin
  version: string
  nodesReady: integer
  nodesTotal: integer
  controllerReady: boolean
  message: string
  observedGeneration: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha2` | | |
| `kind` _string_ | `SimplyblockDriver` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  |  |
| `spec` _[SimplyblockDriverSpec](#simplyblockdriverspec)_ |  |  |  |
| `status` _[SimplyblockDriverStatus](#simplyblockdriverstatus)_ |  |  |  |


#### SimplyblockDriverOrigin

_Underlying type:_ _string_

SimplyblockDriverOrigin is where the running deployment came from. Every
cluster upgraded from a chart install reads Adopted, because the chart had
applied the objects before this kind existed.

_Validation:_
- Enum: [Created Adopted]

_Appears in:_
- [SimplyblockDriverStatus](#simplyblockdriverstatus)

| Field | Description |
| --- | --- |
| `Created` | SimplyblockDriverOriginCreated is a deployment whose objects the operator<br />applied from nothing.<br /> |
| `Adopted` | SimplyblockDriverOriginAdopted is a deployment the operator took over in<br />place, taking field ownership from Helm and removing the release's<br />metadata once the handover was verified.<br /> |


#### SimplyblockDriverPhase

_Underlying type:_ _string_

SimplyblockDriverPhase is where the operator has got to with the CSI driver.
Installing covers the applies of §4.1, and the three values after it are
decided by what the node plugins and the controller plugin report (§4.2).

_Validation:_
- Enum: [Installing Ready Degraded Unavailable]

_Appears in:_
- [SimplyblockDriverStatus](#simplyblockdriverstatus)

| Field | Description |
| --- | --- |
| `Installing` | SimplyblockDriverPhaseInstalling is a deployment whose objects are not all<br />applied yet.<br /> |
| `Ready` | SimplyblockDriverPhaseReady is every plugin pod serving.<br /> |
| `Degraded` | SimplyblockDriverPhaseDegraded is a node plugin restarting while the<br />controller plugin still provisions, which strands one worker's volumes<br />rather than the namespace's.<br /> |
| `Unavailable` | SimplyblockDriverPhaseUnavailable is a controller plugin that is not<br />running, which is when provisioning stops.<br /> |


#### SimplyblockDriverSpec



SimplyblockDriverSpec is the CSI driver deployment: the node plugin, the
controller plugin, their RBAC, and the CSIDriver registration they produce.



_Appears in:_
- [SimplyblockDriver](#simplyblockdriver)

_Example:_

```yaml
image: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
imagePullPolicy: PullPolicy
driverName: string
controllerReplicas: integer
nodeSelector:
  string: string
tolerations:
  - Toleration
controllerNodeSelector:
  string: string
controllerTolerations:
  - Toleration
controllerResources: ResourceRequirements
nodeResources: ResourceRequirements
sidecarImages:
  provisioner: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
  attacher: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
  resizer: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
  snapshotter: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
  healthMonitor: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
  nodeDriverRegistrar: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
enableServiceAccountAuth: boolean
enableVolumeSnapshots: boolean
tls:
  enableTLS: boolean
  enableMutualTLS: boolean
  provider: DriverTLSProvider
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `image` _string_ | Image is the CSI driver image, used by both plugins. Unset takes the<br />operator's own registry and tag with the CSI driver's repository, so a<br />deployment that states nothing runs the driver belonging to the operator<br />reconciling it, which is the pairing the release was tested as. |  | Pattern: `^($\|(quay\.io/simplyblock-io\|docker\.io/simplyblock\|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]\{64\})?)$` <br />Optional: \{\} <br /> |
| `imagePullPolicy` _[PullPolicy](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#pullpolicy-v1-core)_ | ImagePullPolicy controls when that image is pulled. It defaults to Always<br />because the default Image is a moving tag: it follows the operator's own,<br />and a development build's tag is rebuilt in place. IfNotPresent against a<br />tag that moved leaves the workers that already pulled it running the old<br />plugin and the workers that had not running the new one, which is the<br />skew of §5 inside one deployment and invisible from the object. | Always | Enum: [Always Never IfNotPresent] <br />Optional: \{\} <br /> |
| `driverName` _string_ | DriverName is the CSI driver name a StorageClass provisions with. Every<br />PersistentVolume the driver created records it in spec.csi.driver and<br />every VolumeAttachment records it too, so changing it orphans every volume<br />in the namespace rather than renaming anything. | csi.simplyblock.io | Optional: \{\} <br /> |
| `controllerReplicas` _integer_ | ControllerReplicas is the number of controller-plugin instances. | 1 | Minimum: 1 <br />Optional: \{\} <br /> |
| `nodeSelector` _object (keys:string, values:string)_ | NodeSelector restricts which workers run the node plugin. Empty means<br />every schedulable worker, which is the usual case: a node that cannot<br />attach a volume cannot run a workload that needs one. |  | Optional: \{\} <br /> |
| `tolerations` _[Toleration](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#toleration-v1-core) array_ | Tolerations are applied to the node plugin, which usually needs to run<br />where workloads run rather than where the operator does. |  | Optional: \{\} <br /> |
| `controllerNodeSelector` _object (keys:string, values:string)_ | ControllerNodeSelector and ControllerTolerations place the controller<br />plugin. The unprefixed pair above is the node plugin's, because that<br />placement decides which workers can attach a volume, and this pair is<br />ordinary pod placement for the one workload that provisions them. |  | Optional: \{\} <br /> |
| `controllerTolerations` _[Toleration](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#toleration-v1-core) array_ |  |  | Optional: \{\} <br /> |
| `controllerResources` _[ResourceRequirements](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#resourcerequirements-v1-core)_ | ControllerResources and NodeResources set requests and limits for the two<br />plugins. Unset enforces no limits. |  | Optional: \{\} <br /> |
| `nodeResources` _[ResourceRequirements](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#resourcerequirements-v1-core)_ |  |  | Optional: \{\} <br /> |
| `sidecarImages` _[SidecarImages](#sidecarimages)_ | SidecarImages overrides the six CSI sidecars, one field each. Unset takes<br />the version this operator release ships. |  | Optional: \{\} <br /> |
| `enableServiceAccountAuth` _boolean_ | EnableServiceAccountAuth makes both plugins authenticate to the management<br />API with their pod's Kubernetes service-account token instead of the<br />static cluster secret. The control plane has to list those accounts in<br />SB_K8S_ADMIN_SERVICE_ACCOUNTS for it to work, which is why this is a<br />deployment-wide switch rather than a per-plugin one. | false | Optional: \{\} <br /> |
| `enableVolumeSnapshots` _boolean_ | EnableVolumeSnapshots decides whether snapshot support is part of this<br />deployment: the VolumeSnapshotClass for DriverName, and the CRDs and a<br />controller where the cluster serves neither. False applies none of them. | true | Optional: \{\} <br /> |
| `tls` _[DriverTLS](#drivertls)_ | TLS configures whether both plugins reach the control plane over TLS.<br />Unset is plaintext, the shape every deployment ran before this field<br />existed, so adoption of a deployment already running TLS needs this to<br />already agree with what the plugins are configured for — see<br />adoption.go's tlsAdoptionMismatch — rather than reading it off a live<br />object the way spec.driverName's default cannot be. |  | Optional: \{\} <br /> |


#### SimplyblockDriverStatus



SimplyblockDriverStatus is the observed state of the CSI driver deployment.



_Appears in:_
- [SimplyblockDriver](#simplyblockdriver)

_Example:_

```yaml
phase: SimplyblockDriverPhase
snapshotSupport: SnapshotSupportOrigin
origin: SimplyblockDriverOrigin
version: string
nodesReady: integer
nodesTotal: integer
controllerReady: boolean
message: string
observedGeneration: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _[SimplyblockDriverPhase](#simplyblockdriverphase)_ | Phase is the operator's own view of the deployment. |  | Enum: [Installing Ready Degraded Unavailable] <br />Optional: \{\} <br /> |
| `snapshotSupport` _[SnapshotSupportOrigin](#snapshotsupportorigin)_ | SnapshotSupport is whether the cluster already had snapshot support or the<br />operator installed it, which is what says whether other drivers depend on<br />what this one applied. |  | Enum: [Detected Installed] <br />Optional: \{\} <br /> |
| `origin` _[SimplyblockDriverOrigin](#simplyblockdriverorigin)_ | Origin is whether the first reconcile created this deployment's objects<br />or met ones it did not create. It is decided once and never revised,<br />because what it records is where the running deployment came from rather<br />than what the controller did most recently. |  | Enum: [Created Adopted] <br />Optional: \{\} <br /> |
| `version` _string_ | Version is the version the deployed driver reports, published so that a<br />skew against ControlPlane.status.version is visible on one screen. |  | Optional: \{\} <br /> |
| `nodesReady` _integer_ | NodesReady is how many workers run a ready node plugin, and NodesTotal how<br />many are expected to. Neither takes omitempty: zero ready plugins is the<br />condition worth seeing. |  | Minimum: 0 <br /> |
| `nodesTotal` _integer_ |  |  | Minimum: 0 <br /> |
| `controllerReady` _boolean_ | ControllerReady is whether the controller plugin is serving. |  | Optional: \{\} <br /> |
| `message` _string_ | Message is the reason the phase is what it is: one sentence, replaced as<br />the deployment moves, and never a log. |  | Optional: \{\} <br /> |
| `observedGeneration` _integer_ | ObservedGeneration is the generation the rest of this status was computed<br />from, so a stale status can be told from a current one. |  | Optional: \{\} <br /> |


#### SnapshotSupportOrigin

_Underlying type:_ _string_

SnapshotSupportOrigin is where the cluster's snapshot support came from.

_Validation:_
- Enum: [Detected Installed]

_Appears in:_
- [SimplyblockDriverStatus](#simplyblockdriverstatus)

| Field | Description |
| --- | --- |
| `Detected` | SnapshotSupportOriginDetected is a cluster that already served<br />snapshot.storage.k8s.io/v1, so the operator applied no CRDs and no<br />controller.<br /> |
| `Installed` | SnapshotSupportOriginInstalled is a cluster where the operator applied<br />them. They are cluster-scoped and shared, so they carry no controller<br />reference and outlive this object (§4.1).<br /> |


#### StorageBackup



StorageBackup is one point-in-time copy of one volume that exists in a
cluster's store.

Objects are created by the operator from what the store holds and are never
written by a user: creating one by hand would claim a backup exists that the
store does not hold, and deleting one would hide a backup that is still there
and still restorable. Deleting the object never deletes the copy.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageBackup
metadata:
  name: string
spec:
  clusterRef: string
  backupID: string
status:
  phase: StorageBackupPhase
  apiStatus: string
  clusterID: string
  backup:
    backupID: string
    s3ID: integer
    size: integer
    previousBackupID: string
    startedAt: Time
    completedAt: Time
  source:
    claimName: string
    claimNamespace: string
    persistentVolumeName: string
    poolName: string
    poolUUID: string
    lvolID: string
    lvolName: string
    fsType: string
    snapshotID: string
    snapshotName: string
    nodeID: string
    clusterUUID: string
  activeOpsRef: string
  message: string
  observedGeneration: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha2` | | |
| `kind` _string_ | `StorageBackup` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  | Optional: \{\} <br /> |
| `spec` _[StorageBackupSpec](#storagebackupspec)_ | spec identifies the backup this object reports on |  | Required: \{\} <br /> |
| `status` _[StorageBackupStatus](#storagebackupstatus)_ | status defines the observed state of StorageBackup |  | Optional: \{\} <br /> |


#### StorageBackupOps



StorageBackupOps is a single operation performed against one StorageBackup. It
runs to a terminal phase and stays afterward as the audit record of what was
restored, into which pool, and how it ended.

The claim a restore produces is not owned by the operation and outlives it:
nobody restores a backup in order to keep a StorageBackupOps, so deleting the
audit record must not delete the recovered volume.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageBackupOps
metadata:
  name: string
spec:
  clusterRef: string
  backupRef: string
  action: StorageBackupOpsAction
  abort: boolean
  restore:
    claimName: string
    targetPool: string
    claimLabels:
      string: string
    claimAnnotations:
      string: string
status:
  phase: StorageBackupOpsPhase
  step: KubeSnapshot
  clusterID: string
  backupID: string
  restoredLvolID: string
  poolUUID: string
  persistentVolumeName: string
  claimName: string
  message: string
  observedGeneration: integer
  startedAt: Time
  completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha2` | | |
| `kind` _string_ | `StorageBackupOps` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  | Optional: \{\} <br /> |
| `spec` _[StorageBackupOpsSpec](#storagebackupopsspec)_ | spec defines the operation to perform |  | Required: \{\} <br /> |
| `status` _[StorageBackupOpsStatus](#storagebackupopsstatus)_ | status defines the observed state of StorageBackupOps |  | Optional: \{\} <br /> |


#### StorageBackupOpsAction

_Underlying type:_ _string_

StorageBackupOpsAction is the operation a StorageBackupOps performs. Restore
acts on a StorageBackup, which is every backup in the cluster's store.

_Validation:_
- Enum: [Restore]

_Appears in:_
- [StorageBackupOpsSpec](#storagebackupopsspec)

| Field | Description |
| --- | --- |
| `Restore` |  |


#### StorageBackupOpsPhase

_Underlying type:_ _string_

StorageBackupOpsPhase is the operation's own progress. It is the same small
set every Ops kind in the group carries: Pending before the operation holds
its target's lock, Running while it works, and three terminal values.

_Validation:_
- Enum: [Pending Running Succeeded Failed Aborted]

_Appears in:_
- [StorageBackupOpsStatus](#storagebackupopsstatus)

| Field | Description |
| --- | --- |
| `Pending` |  |
| `Running` |  |
| `Succeeded` |  |
| `Failed` |  |
| `Aborted` |  |


#### StorageBackupOpsSpec



StorageBackupOpsSpec is one operation to perform against a backup.



_Appears in:_
- [StorageBackupOps](#storagebackupops)

_Example:_

```yaml
clusterRef: string
backupRef: string
action: StorageBackupOpsAction
abort: boolean
restore:
  claimName: string
  targetPool: string
  claimLabels:
    string: string
  claimAnnotations:
    string: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `clusterRef` _string_ | ClusterRef names the StorageCluster the operation runs against.<br />Bounded at what a StorageCluster name may be, since a longer value names<br />nothing that can exist (design-api-upgrade.md §19.4). |  | MaxLength: 63 <br />Required: \{\} <br /> |
| `backupRef` _string_ | BackupRef names the StorageBackup this operation acts on, in this<br />namespace. Required, since Restore is the only action and every backup in<br />the store has an object. |  | Required: \{\} <br /> |
| `action` _[StorageBackupOpsAction](#storagebackupopsaction)_ | Action is the operation to perform. |  | Enum: [Restore] <br />Required: \{\} <br /> |
| `abort` _boolean_ | Abort asks a running operation to stop at its next step and unwind. It is<br />the one field of this spec that may be edited after the object is created,<br />because it is the one thing about an operation that can legitimately be<br />decided after it started.<br />A restore cannot be aborted once it has created a logical volume, and the<br />action's graph declares that rather than this field: an abort arriving<br />later is reported as an illegal transition while the operation runs on,<br />rather than leaving the work half undone. |  | Optional: \{\} <br /> |
| `restore` _[RestoreSpec](#restorespec)_ | Restore parameterizes action Restore. |  | Optional: \{\} <br /> |


#### StorageBackupOpsStatus



StorageBackupOpsStatus is the observed state of one backup operation.



_Appears in:_
- [StorageBackupOps](#storagebackupops)

_Example:_

```yaml
phase: StorageBackupOpsPhase
step: KubeSnapshot
clusterID: string
backupID: string
restoredLvolID: string
poolUUID: string
persistentVolumeName: string
claimName: string
message: string
observedGeneration: integer
startedAt: Time
completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _[StorageBackupOpsPhase](#storagebackupopsphase)_ | Phase is the operation's own progress. |  | Enum: [Pending Running Succeeded Failed Aborted] <br />Optional: \{\} <br /> |
| `step` _[KubeSnapshot](https://github.com/simplyblock/simplyblock-operator/blob/main/atlas-lib/statemachine/kubernetes.go)_ | Step is the position of the running action's state machine. It is<br />persisted before the side effect that step performs. The closed set is a<br />CEL rule rather than an Enum marker because a marker cannot reach a field<br />whose type is declared in another module. |  | Optional: \{\} <br /> |
| `clusterID` _string_ | ClusterID is the backend cluster the operation ran against. |  | Optional: \{\} <br /> |
| `backupID` _string_ | BackupID is the copy the restore read from, recorded so the operation says<br />what it restored after the object list has moved on. |  | Optional: \{\} <br /> |
| `restoredLvolID` _string_ | RestoredLvolID is the logical volume the control plane created. It is<br />written before the claim, so a restarted Binding step knows what it is<br />binding. |  | Optional: \{\} <br /> |
| `poolUUID` _string_ | PoolUUID is the backend identifier of spec.restore.targetPool, resolved<br />once at Validating. |  | Optional: \{\} <br /> |
| `persistentVolumeName` _string_ | PersistentVolumeName is the PV the operation wrote for the restored<br />volume. |  | Optional: \{\} <br /> |
| `claimName` _string_ | ClaimName is the PersistentVolumeClaim a Restore produced. It is written<br />before the claim is created rather than after, because the claim carries<br />no owner reference back: a restarted Binding step recognizes its own work<br />by this name together with the storage.simplyblock.io/restored-by label on<br />the claim, and refuses a claim of the right name that carries neither. |  | Optional: \{\} <br /> |
| `message` _string_ | Message is the reason the phase is what it is: one sentence, replaced as<br />the operation moves, and never a log. |  | Optional: \{\} <br /> |
| `observedGeneration` _integer_ | ObservedGeneration is the generation the rest of this status was computed<br />from. On this kind it advances at most twice, and the second advance is<br />precisely the signal that spec.abort has been observed. |  | Optional: \{\} <br /> |
| `startedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | StartedAt is when the operation acquired its target's lock. |  | Optional: \{\} <br /> |
| `completedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | CompletedAt is when it reached a terminal phase. |  | Optional: \{\} <br /> |




#### StorageBackupPhase

_Underlying type:_ _string_

StorageBackupPhase is where the operator has got to with this backup.
Available is the terminal success rather than Succeeded, because a backup is
not an operation: what matters afterward is that the copy can be restored, not
that the copying finished.

_Validation:_
- Enum: [Pending Creating Available Failed]

_Appears in:_
- [StorageBackupStatus](#storagebackupstatus)

| Field | Description |
| --- | --- |
| `Pending` |  |
| `Creating` |  |
| `Available` |  |
| `Failed` |  |


#### StorageBackupPolicy



StorageBackupPolicy schedules and retains the backups of the claims it
selects. It is the only thing that decides a backup is taken; the copies
themselves are the control plane's, are pruned by its retention, and reach
Kubernetes as StorageBackup objects the operator discovers.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageBackupPolicy
metadata:
  name: string
spec:
  clusterRef: string
  claimSelector: LabelSelector
  schedule: '^(\d+[mhdw],\d+)( +\d+[mhdw],\d+)*$'
  maxVersions: integer
  maxAge: '^[1-9]\d*[mhdw]$'
status:
  phase: StorageBackupPolicyPhase
  clusterID: string
  policyID: string
  attachedClaims:
    - name: string
      persistentVolumeName: string
      lvolID: string
      attachedAt: Time
  lastBackupAt: Time
  message: string
  observedGeneration: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha2` | | |
| `kind` _string_ | `StorageBackupPolicy` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  | Optional: \{\} <br /> |
| `spec` _[StorageBackupPolicySpec](#storagebackuppolicyspec)_ | spec defines the desired state of StorageBackupPolicy |  | Required: \{\} <br /> |
| `status` _[StorageBackupPolicyStatus](#storagebackuppolicystatus)_ | status defines the observed state of StorageBackupPolicy |  | Optional: \{\} <br /> |


#### StorageBackupPolicyPhase

_Underlying type:_ _string_

StorageBackupPolicyPhase is where the operator has got to with this policy.

_Validation:_
- Enum: [Pending Active Failed]

_Appears in:_
- [StorageBackupPolicyStatus](#storagebackuppolicystatus)

| Field | Description |
| --- | --- |
| `Pending` |  |
| `Active` |  |
| `Failed` |  |


#### StorageBackupPolicySpec



StorageBackupPolicySpec schedules and retains the backups of the claims it
selects. The operator reconciles it into the control plane and reports what
the control plane did; it does not run the schedule itself, because a backup
schedule that stopped when the operator was down would be one nobody could
rely on.



_Appears in:_
- [StorageBackupPolicy](#storagebackuppolicy)

_Example:_

```yaml
clusterRef: string
claimSelector: LabelSelector
schedule: '^(\d+[mhdw],\d+)( +\d+[mhdw],\d+)*$'
maxVersions: integer
maxAge: '^[1-9]\d*[mhdw]$'
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `clusterRef` _string_ | ClusterRef names the StorageCluster whose backup target this policy writes<br />to.<br />Bounded at what a StorageCluster name may be, since a longer value names<br />nothing that can exist (design-api-upgrade.md §19.4). |  | MaxLength: 63 <br />Required: \{\} <br /> |
| `claimSelector` _[LabelSelector](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#labelselector-v1-meta)_ | ClaimSelector selects the PersistentVolumeClaims this policy backs up. An<br />absent selector selects nothing, which is deliberate: the cost of backing<br />up too much is silent and recurring, and the cost of backing up too little<br />is an error somebody sees. The controller reports an inert policy with a<br />SelectorEmpty event rather than refusing it. |  | Optional: \{\} <br /> |
| `schedule` _string_ | Schedule is the tiered schedule the control plane runs the policy on, as a<br />space-separated list of interval,keep_count pairs ("15m,4 60m,11 24h,7").<br />Intervals must be strictly increasing, and the supported units are m, h,<br />d, and w.<br />Immutable, and that is a property of the control plane rather than a<br />choice. design-storagebackup.md §10 lists a PUT that applies a changed<br />schedule, and the v2 API offers no such endpoint: it creates, deletes,<br />attaches, and detaches a policy and nothing else. A mutable field the<br />operator cannot reconcile would leave the declaration and the backups<br />actually being taken permanently disagreeing, with the object still<br />reporting Active, so the schedule is fixed at creation until the endpoint<br />exists. Changing one means replacing the policy. |  | Pattern: `^(\d+[mhdw],\d+)( +\d+[mhdw],\d+)*$` <br />Optional: \{\} <br /> |
| `maxVersions` _integer_ | MaxVersions is how many backups of one claim to keep. Zero means no limit<br />by count. Immutable, for the reason Schedule is. |  | Minimum: 0 <br />Optional: \{\} <br /> |
| `maxAge` _string_ | MaxAge is how long to keep a backup ("30d," "720h"). Empty means no limit<br />by age. Retention is enforced by the control plane, not here. Immutable,<br />for the reason Schedule is. |  | Pattern: `^[1-9]\d*[mhdw]$` <br />Optional: \{\} <br /> |


#### StorageBackupPolicyStatus



StorageBackupPolicyStatus is the observed state of the policy.



_Appears in:_
- [StorageBackupPolicy](#storagebackuppolicy)

_Example:_

```yaml
phase: StorageBackupPolicyPhase
clusterID: string
policyID: string
attachedClaims:
  - name: string
    persistentVolumeName: string
    lvolID: string
    attachedAt: Time
lastBackupAt: Time
message: string
observedGeneration: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _[StorageBackupPolicyPhase](#storagebackuppolicyphase)_ | Phase is the operator's own view of this policy. |  | Enum: [Pending Active Failed] <br />Optional: \{\} <br /> |
| `clusterID` _string_ | ClusterID is the backend cluster the policy was created in. |  | Optional: \{\} <br /> |
| `policyID` _string_ | PolicyID is the control plane's identifier for the policy. |  | Optional: \{\} <br /> |
| `attachedClaims` _[AttachedClaim](#attachedclaim) array_ | AttachedClaims are the claims the policy currently covers. Detaching one<br />stops new backups being taken and deletes none of the existing ones. |  | Optional: \{\} <br /> |
| `lastBackupAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | LastBackupAt is when the control plane last completed a backup under this<br />policy, and it is what an age alert is computed from. |  | Optional: \{\} <br /> |
| `message` _string_ | Message is the reason the phase is what it is: one sentence, replaced as<br />the policy moves, and never a log. |  | Optional: \{\} <br /> |
| `observedGeneration` _integer_ | ObservedGeneration is the generation the rest of this status was computed<br />from, so a stale status can be told from a current one. |  | Optional: \{\} <br /> |


#### StorageBackupSpec



StorageBackupSpec is the identity of one backup the operator found in a
cluster's store, and nothing else. The object is created by the operator and
by nobody else (§5.1), so there is no request here to carry.



_Appears in:_
- [StorageBackup](#storagebackup)

_Example:_

```yaml
clusterRef: string
backupID: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `clusterRef` _string_ | ClusterRef names the StorageCluster whose store this backup was found in.<br />With BackupID it is the whole of this object's identity.<br />Bounded at what a StorageCluster name may be, since a longer value names<br />nothing that can exist (design-api-upgrade.md §19.4). |  | MaxLength: 63 <br />Required: \{\} <br /> |
| `backupID` _string_ | BackupID is the identifier the store holds the backup under, and what a<br />restore addresses. It is the store's identifier rather than a name this<br />operator assigns, so the same backup is the same object however many<br />clusters have the location configured. |  | Required: \{\} <br /> |


#### StorageBackupStatus



StorageBackupStatus is the observed state of one backup, in three groups: the
copy, what the volume was, and the operator's own view.



_Appears in:_
- [StorageBackup](#storagebackup)

_Example:_

```yaml
phase: StorageBackupPhase
apiStatus: string
clusterID: string
backup:
  backupID: string
  s3ID: integer
  size: integer
  previousBackupID: string
  startedAt: Time
  completedAt: Time
source:
  claimName: string
  claimNamespace: string
  persistentVolumeName: string
  poolName: string
  poolUUID: string
  lvolID: string
  lvolName: string
  fsType: string
  snapshotID: string
  snapshotName: string
  nodeID: string
  clusterUUID: string
activeOpsRef: string
message: string
observedGeneration: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _[StorageBackupPhase](#storagebackupphase)_ | Phase is the operator's own view of this backup. |  | Enum: [Pending Creating Available Failed] <br />Optional: \{\} <br /> |
| `apiStatus` _string_ | APIStatus is the control plane's own lifecycle string, in the control<br />plane's spelling, which is why it carries no Enum here. It is what keeps<br />the states the four-value phase folds together — merging, deleting —<br />legible. |  | Optional: \{\} <br /> |
| `clusterID` _string_ | ClusterID is the backend cluster whose stream this backup was last<br />observed on. The appendix does not list it, and the mirror cannot work<br />without it: an object outliving its backup has to say which scope's<br />silence is authoritative before it may be deleted, and spec.clusterRef<br />names a Kubernetes object rather than a backend one. It is the same field,<br />for the same reason, that StorageDevice carries<br />(design-storagedevice.md §5.1). |  | Optional: \{\} <br /> |
| `backup` _[BackupCopy](#backupcopy)_ | Backup is the copy itself. |  | Optional: \{\} <br /> |
| `source` _[BackupSource](#backupsource)_ | Source is what the volume was when the copy was taken. |  | Optional: \{\} <br /> |
| `activeOpsRef` _string_ | ActiveOpsRef names the StorageBackupOps currently allowed to act on this<br />backup. Empty when none is running. |  | Optional: \{\} <br /> |
| `message` _string_ | Message is the reason the phase is what it is: one sentence, replaced as<br />the backup moves, and never a log. |  | Optional: \{\} <br /> |
| `observedGeneration` _integer_ | ObservedGeneration is the generation the rest of this status was computed<br />from, so a stale status can be told from a current one. On this kind it<br />moves at most once, since every spec field is fixed when the object is<br />created. |  | Optional: \{\} <br /> |


#### StorageCluster



StorageCluster is one simplyblock backend cluster. It owns the storage nodes
beneath it, the pools carved out of it, and the Kubernetes workload its nodes
run as.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageCluster
metadata:
  name: string
spec:
  maxSubsystemCount: integer
  vcpuCount: integer
  minHugePagesSize: string
  stripe:
    dataChunks: integer
    parityChunks: integer
  fabricType: string
  clientDataIfname: string
  nvmfBasePort: integer
  rpcBasePort: integer
  snodeApiPort: integer
  enableFailureDomains: boolean
  enableNodeAffinity: boolean
  enableChecksumValidation: boolean
  enableAtomicity4K: boolean
  deviceClass: StorageClusterDeviceClass
  kms:
    vault:
      endpoint: '^https?://[a-zA-Z0-9.-]+(:[0-9]{1,5})?(/.*)?$'
  warningThreshold:
    capacity: integer
    provisionedCapacity: integer
  criticalThreshold:
    capacity: integer
    provisionedCapacity: integer
  maxConcurrentWorkerRestarts: integer
  storageNodes:
    image: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
    imagePullPolicy: PullPolicy
    mgmtInterface: string
    dataInterfaces:
      - string
    socketsToUse:
      - string
    nodesPerSocket: integer
    nodeProvisioningBudget: integer
    enableJournalDevice: boolean
    enableFormat4K: boolean
    enableBlockFormat: boolean
    enableCpuTopology: boolean
    reservedSystemCPU: string
    enableKubeletConfiguration: boolean
    ubuntuHost: boolean
    openshift:
      machineConfigPool: '^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
    tolerations:
      - Toleration
    containerResources: ResourceRequirements
    initContainerResources: ResourceRequirements
  backup:
    endpoint: '^https?://[a-zA-Z0-9.-]+(:[0-9]{1,5})?(/.*)?$'
    bucket: string
    prefix: string
    region: string
    credentialsSecretRef: LocalObjectReference
  disableDataRealignment: boolean
  enableVolumeAutoPlacement: boolean
  volumeMigrationSettings:
    rebalancerImage: string
    dataRealignment:
      interval: Duration
      minMoves: integer
  volumeAutoPlacement:
    disableMigration: boolean
    evaluationInterval: Duration
    imbalanceThreshold: integer
    minHotColdDifferencePct: integer
    defaultCoolDownSeconds: integer
    maxVolumeMigrationsPerCycle: integer
    storageNodeCandidateCount: integer
    metricsBackend: MetricsBackend
    prometheusURL: string
    enableLatencyBenchmark: boolean
    latencyBenchmarkInterval: Duration
    baselineStrategy: BaselineStrategy
    baselineWindow: Duration
    baselineColdStart: BaselineColdStartPolicy
    baselineMinSamples: integer
    baselineOutlierK: float
    iopsWeight: float
    throughputWeight: float
status:
  phase: StorageClusterPhase
  step: KubeSnapshot
  uuid: string
  clusterName: string
  nqn: string
  erasureCodingScheme: string
  status: string
  configured: boolean
  rebalancing: boolean
  maxFaultTolerance: integer
  maxConcurrentWorkerRestarts: integer
  volumeMoveGeneration: integer
  realignedGeneration: integer
  lastDataRealignmentAt: Time
  tasks:
    - id: string
      type: string
      status: string
      retry: integer
  provisioningSlots:
    - worker: string
      node: string
      takenAt: Time
  activeOpsRef: string
  rebalancingMetrics:
    avgDeviationPct: float
    maxDeviationPct: float
    hottestNodeUUID: string
    coolestNodeUUID: string
    imbalancePercent: float
    lastEvaluatedAt: Time
    lastMigrationAt: Time
    nodeMetrics:
      - nodeUUID: string
        latencyDeviationPct: float
        volumeCount: integer
        lastUpdated: Time
  message: string
  observedGeneration: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha2` | | |
| `kind` _string_ | `StorageCluster` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  |  |
| `spec` _[StorageClusterSpec](#storageclusterspec)_ |  |  |  |
| `status` _[StorageClusterStatus](#storageclusterstatus)_ |  |  |  |


#### StorageClusterDeviceClass

_Underlying type:_ _string_

StorageClusterDeviceClass is the class of backend storage a cluster is built
out of. The values are the two classes simplyblock accepts, spelled as the
standards that name them are, which is the exception design-crd-model.md §7.8
carries for a word this group did not invent.

_Validation:_
- Enum: [NVMe LogicalBlock]

_Appears in:_
- [StorageClusterSpec](#storageclusterspec)

| Field | Description |
| --- | --- |
| `NVMe` | StorageClusterDeviceClassNVMe is a cluster whose nodes hand over NVMe<br />devices, named by PCI address.<br /> |
| `LogicalBlock` | StorageClusterDeviceClassLogicalBlock is a cluster whose nodes hand over<br />logical block devices, named by path. The backend accepts them from 26.4.<br /> |


#### StorageClusterOps



StorageClusterOps is a single operation performed against one StorageCluster.
It runs to a terminal phase and stays afterward as the audit record of what
was done, to which cluster, with which parameters, and how it ended. Only one
operation acts on a cluster at a time; a second is admitted, waits at
Pending, and runs when the lock frees.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageClusterOps
metadata:
  name: string
spec:
  clusterRef: string
  action: StorageClusterOpsAction
  abort: boolean
  cancelTask:
    taskID: string
  rollingRestart:
    refreshSNodeAPI: boolean
status:
  phase: StorageClusterOpsPhase
  step: KubeSnapshot
  message: string
  rollingRestart:
    nodes:
      - string
    nodeIndex: integer
  observedGeneration: integer
  startedAt: Time
  completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha2` | | |
| `kind` _string_ | `StorageClusterOps` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  |  |
| `spec` _[StorageClusterOpsSpec](#storageclusteropsspec)_ |  |  |  |
| `status` _[StorageClusterOpsStatus](#storageclusteropsstatus)_ |  |  |  |


#### StorageClusterOpsAction

_Underlying type:_ _string_

StorageClusterOpsAction is the operation a StorageClusterOps performs. The
values are PascalCase, as every enum in the group is; v1alpha1 spelled them
lowercase and hyphenated, and the conversion maps between the two.

_Validation:_
- Enum: [Activate Expand Shutdown Start Restart RollingRestart CancelTask]

_Appears in:_
- [StorageClusterOpsSpec](#storageclusteropsspec)

| Field | Description |
| --- | --- |
| `Activate` |  |
| `Expand` |  |
| `Shutdown` |  |
| `Start` |  |
| `Restart` |  |
| `RollingRestart` |  |
| `CancelTask` | StorageClusterOpsActionCancelTask is the one action whose target is<br />inside the cluster: it names a task of the cluster's status.tasks by its<br />control-plane ID.<br /> |


#### StorageClusterOpsPhase

_Underlying type:_ _string_

StorageClusterOpsPhase is the operation's own progress. Aborted is terminal
and distinct from Failed, because a canceled operation did not go wrong.

_Validation:_
- Enum: [Pending Running Succeeded Failed Aborted]

_Appears in:_
- [StorageClusterOpsStatus](#storageclusteropsstatus)

| Field | Description |
| --- | --- |
| `Pending` | StorageClusterOpsPhasePending: the operation holds no lock and has<br />issued nothing. It is both where an operation starts and where it waits<br />behind another one's lock.<br /> |
| `Running` | StorageClusterOpsPhaseRunning: the operation holds the lock and its<br />first side effect may have been issued.<br /> |
| `Succeeded` |  |
| `Failed` |  |
| `Aborted` | StorageClusterOpsPhaseAborted: the operation was called off. A rolling<br />restart holding on a degraded cluster is the one operation an<br />administrator has a reason to stop, and stopping it is not a failure.<br /> |


#### StorageClusterOpsSpec



StorageClusterOpsSpec is one operation to perform against one StorageCluster.



_Appears in:_
- [StorageClusterOps](#storageclusterops)

_Example:_

```yaml
clusterRef: string
action: StorageClusterOpsAction
abort: boolean
cancelTask:
  taskID: string
rollingRestart:
  refreshSNodeAPI: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `clusterRef` _string_ | ClusterRef names the StorageCluster this operation acts on. The operation<br />never owns its target, because deleting the record of an operation must<br />not delete the cluster it operated on.<br />Bounded at what a StorageCluster name may be, since a longer value names<br />nothing that can exist (design-api-upgrade.md §19.4). |  | MaxLength: 63 <br />Required: \{\} <br /> |
| `action` _[StorageClusterOpsAction](#storageclusteropsaction)_ | Action is the operation to perform. |  | Enum: [Activate Expand Shutdown Start Restart RollingRestart CancelTask] <br />Required: \{\} <br /> |
| `abort` _boolean_ | Abort asks a running operation to stop at its next step and unwind.<br />Whether an abort is expressible from the current step is declared by that<br />action's graph rather than checked here. |  | Optional: \{\} <br /> |
| `cancelTask` _[CancelTaskSpec](#canceltaskspec)_ | CancelTask parameterizes action CancelTask and is ignored by the others. |  | Optional: \{\} <br /> |
| `rollingRestart` _[RollingRestartSpec](#rollingrestartspec)_ | RollingRestart parameterizes action RollingRestart and is ignored by the<br />others. |  | Optional: \{\} <br /> |


#### StorageClusterOpsStatus



StorageClusterOpsStatus is the observed state of one cluster operation.



_Appears in:_
- [StorageClusterOps](#storageclusterops)

_Example:_

```yaml
phase: StorageClusterOpsPhase
step: KubeSnapshot
message: string
rollingRestart:
  nodes:
    - string
  nodeIndex: integer
observedGeneration: integer
startedAt: Time
completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _[StorageClusterOpsPhase](#storageclusteropsphase)_ | Phase is the operation's own progress. |  | Enum: [Pending Running Succeeded Failed Aborted] <br />Optional: \{\} <br /> |
| `step` _[KubeSnapshot](https://github.com/simplyblock/simplyblock-operator/blob/main/atlas-lib/statemachine/kubernetes.go)_ | Step is the position of the running action's state machine, as the shared<br />statemachine.KubeSnapshot. The rule is what an Enum marker would do if a<br />marker could reach a field of a shared type. |  | Optional: \{\} <br /> |
| `message` _string_ | Message is the reason the phase is what it is: one sentence, replaced as<br />the operation moves, and never a log. |  | Optional: \{\} <br /> |
| `rollingRestart` _[RollingRestartStatus](#rollingrestartstatus)_ | RollingRestart is the walk's position, set only for action<br />RollingRestart. |  | Optional: \{\} <br /> |
| `observedGeneration` _integer_ | ObservedGeneration is the generation the rest of this status was computed<br />from, so a stale status can be told from a current one. |  | Optional: \{\} <br /> |
| `startedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | StartedAt is when the operation acquired its target's lock. |  | Optional: \{\} <br /> |
| `completedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | CompletedAt is when it reached a terminal phase. |  | Optional: \{\} <br /> |




#### StorageClusterPhase

_Underlying type:_ _string_

StorageClusterPhase is where the operator has got to with this cluster. The
first two values are the operator's own creation path; the rest are its
reading of the lifecycle status.status carries in the control plane's own
spelling.

_Validation:_
- Enum: [Pending Creating Provisioning Activating Online Degraded Unavailable Suspended]

_Appears in:_
- [StorageClusterStatus](#storageclusterstatus)

| Field | Description |
| --- | --- |
| `Pending` | StorageClusterPhasePending: the object exists and nothing has been<br />claimed for it yet.<br /> |
| `Creating` | StorageClusterPhaseCreating: the creation machine is running.<br /> |
| `Provisioning` | StorageClusterPhaseProvisioning: the cluster exists in the control plane<br />and is being built up — its first nodes are joining, or an expansion is<br />adding more. It is not serving and there is nothing wrong with it, which<br />is the distinction Unavailable cannot carry.<br /> |
| `Activating` | StorageClusterPhaseActivating: the control plane is activating the<br />cluster.<br />It is a phase of its own rather than part of Provisioning because it is<br />not only the last step of a deployment: an expansion ends in one, and so<br />does recovering from a suspension, long after anything was being built.<br /> |
| `Online` | StorageClusterPhaseOnline: the control plane reports the cluster active<br />and serving.<br /> |
| `Degraded` | StorageClusterPhaseDegraded: serving, with less than the redundancy it<br />was built for.<br /> |
| `Unavailable` | StorageClusterPhaseUnavailable: not serving, and not because anybody<br />asked.<br />It is what is left once the statuses that mean something has been asked<br />for are read as themselves, which is what keeps it worth reporting: a<br />cluster in this phase is one whose status this operator has no reading<br />for, rather than every cluster that is not currently serving.<br /> |
| `Suspended` | StorageClusterPhaseSuspended: shut down deliberately, which is where a<br />Shutdown operation leaves it.<br /> |


#### StorageClusterSpec



StorageClusterSpec is the desired state of one simplyblock backend cluster.



_Appears in:_
- [StorageCluster](#storagecluster)

_Example:_

```yaml
maxSubsystemCount: integer
vcpuCount: integer
minHugePagesSize: string
stripe:
  dataChunks: integer
  parityChunks: integer
fabricType: string
clientDataIfname: string
nvmfBasePort: integer
rpcBasePort: integer
snodeApiPort: integer
enableFailureDomains: boolean
enableNodeAffinity: boolean
enableChecksumValidation: boolean
enableAtomicity4K: boolean
deviceClass: StorageClusterDeviceClass
kms:
  vault:
    endpoint: '^https?://[a-zA-Z0-9.-]+(:[0-9]{1,5})?(/.*)?$'
warningThreshold:
  capacity: integer
  provisionedCapacity: integer
criticalThreshold:
  capacity: integer
  provisionedCapacity: integer
maxConcurrentWorkerRestarts: integer
storageNodes:
  image: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
  imagePullPolicy: PullPolicy
  mgmtInterface: string
  dataInterfaces:
    - string
  socketsToUse:
    - string
  nodesPerSocket: integer
  nodeProvisioningBudget: integer
  enableJournalDevice: boolean
  enableFormat4K: boolean
  enableBlockFormat: boolean
  enableCpuTopology: boolean
  reservedSystemCPU: string
  enableKubeletConfiguration: boolean
  ubuntuHost: boolean
  openshift:
    machineConfigPool: '^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
  tolerations:
    - Toleration
  containerResources: ResourceRequirements
  initContainerResources: ResourceRequirements
backup:
  endpoint: '^https?://[a-zA-Z0-9.-]+(:[0-9]{1,5})?(/.*)?$'
  bucket: string
  prefix: string
  region: string
  credentialsSecretRef: LocalObjectReference
disableDataRealignment: boolean
enableVolumeAutoPlacement: boolean
volumeMigrationSettings:
  rebalancerImage: string
  dataRealignment:
    interval: Duration
    minMoves: integer
volumeAutoPlacement:
  disableMigration: boolean
  evaluationInterval: Duration
  imbalanceThreshold: integer
  minHotColdDifferencePct: integer
  defaultCoolDownSeconds: integer
  maxVolumeMigrationsPerCycle: integer
  storageNodeCandidateCount: integer
  metricsBackend: MetricsBackend
  prometheusURL: string
  enableLatencyBenchmark: boolean
  latencyBenchmarkInterval: Duration
  baselineStrategy: BaselineStrategy
  baselineWindow: Duration
  baselineColdStart: BaselineColdStartPolicy
  baselineMinSamples: integer
  baselineOutlierK: float
  iopsWeight: float
  throughputWeight: float
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `maxSubsystemCount` _integer_ | MaxSubsystemCount is the maximum number of NVMe-oF subsystems per storage<br />node. It is the cluster's and no node carries a copy: every node's<br />configuration is generated from this field, so changing it reaches the<br />nodes that already exist as each of them next restarts.<br />Required: it sizes huge pages, and a node that receives no value fails<br />config generation outright rather than falling back to a default. |  | Maximum: 75 <br />Minimum: 10 <br />Required: \{\} <br /> |
| `vcpuCount` _integer_ | VCPUCount is the number of vCPUs allocated to SPDK on each storage node,<br />as an explicit core count rather than a percentage. Unlike<br />MaxSubsystemCount it is stamped onto a node when the node is created,<br />because it describes the host that node runs on. Required: the core<br />layout it produces must match across the cluster in steady state, so it<br />is stated rather than left to a per-node heuristic.<br />The floor is 4 rather than a hardware limit: a node must carry one core<br />beyond this budget for the system, and the control plane's core layout<br />assigns no NVMe-oF poller core at all for a 2-vCPU budget. |  | Minimum: 4 <br />Required: \{\} <br /> |
| `minHugePagesSize` _string_ | MinHugePagesSize is the smallest huge-page allocation each storage node<br />makes, as a size string such as 100G or 1T, where a bare number is<br />gigabytes. It is a floor and not a limit: the effective allocation is the<br />larger of this value and the minimum the node's device and subsystem<br />count requires, so simplyblock takes more when it needs more. Omitted,<br />the computed minimum is used. |  | Optional: \{\} <br /> |
| `stripe` _[StripeSpec](#stripespec)_ | Stripe is the erasure-coding layout every volume in the cluster is<br />written with. It describes on-disk layout, so it cannot change under a<br />live cluster. |  | Optional: \{\} <br /> |
| `fabricType` _string_ | FabricType is the storage fabric the cluster serves volumes over. It<br />describes on-wire layout, so it cannot change under a live cluster. |  | Optional: \{\} <br /> |
| `clientDataIfname` _string_ | ClientDataIfname is the network interface clients reach the data plane<br />on. It is mutable: the control plane reads it on every connect rather than<br />once at cluster-add, so an edit moves the next attach onto the named<br />interface. |  | Optional: \{\} <br /> |
| `nvmfBasePort` _integer_ | NvmfBasePort is the base of the NVMe-oF port range every node binds.<br />The default is the control plane's own, which is what it applies to a<br />cluster that sends none, so the field states the number the cluster<br />actually runs with rather than leaving a reader to know the backend. | 4420 | Maximum: 65535 <br />Minimum: 1024 <br />Optional: \{\} <br /> |
| `rpcBasePort` _integer_ | RpcBasePort is the base of the RPC port range every node binds. Its<br />default is the control plane's, as NvmfBasePort's is. | 8080 | Maximum: 65535 <br />Minimum: 1024 <br />Optional: \{\} <br /> |
| `snodeApiPort` _integer_ | SnodeApiPort is the port each node's storage-node API listens on. Its<br />default is the control plane's, as NvmfBasePort's is. | 50001 | Maximum: 65535 <br />Minimum: 1024 <br />Optional: \{\} <br /> |
| `enableFailureDomains` _boolean_ | EnableFailureDomains opts the cluster into failure-domain mode, where<br />every node must label the fault group it belongs to so the control plane<br />can spread erasure-coding chunks across independent ones. |  | Optional: \{\} <br /> |
| `enableNodeAffinity` _boolean_ | EnableNodeAffinity has the data plane serve an erasure-coded volume's I/O<br />from the local node's own devices where it can, before crossing the<br />network.<br />It is not Kubernetes affinity, and the name is the one place this API<br />invites that reading: nothing about it schedules a pod, labels a worker,<br />or places a volume's primary node. The control plane carries it into the<br />cluster map it pushes to each node, where it sets the local node's index,<br />and what changes is which copy of a chunk is read.<br />design-primary-node-placement.md §"EnableNodeAffinity is unrelated to<br />Tier 1" is the longer account, and the co-location of a workload with its<br />primary node is the separate mechanism described there. |  | Optional: \{\} <br /> |
| `enableChecksumValidation` _boolean_ | EnableChecksumValidation turns on inline CRC validation of every I/O, for<br />silent-data-error protection. The backend bakes the checksum method into<br />each device at cluster-create time and never re-applies it, so it cannot<br />change under a live cluster. | false | Optional: \{\} <br /> |
| `enableAtomicity4K` _boolean_ | EnableAtomicity4K enforces 4K write atomicity on devices that report a<br />smaller logical block size, which lets checksum fallback mode run on them<br />despite the data plane's usual 4K minimum.<br />It is an enforcement rather than a reading, and that is what it is for.<br />A device may complete a 4K write whole across a power failure and have no<br />way to say so: a SATA drive presenting 512-byte logical blocks over a 4K<br />physical sector reports 512 and nothing else, and a kernel older than 6.11<br />publishes no atomic write attributes at all, so the fleet it runs on<br />cannot be asked. Where the hardware can answer, the storage node's report<br />carries what it said; where it cannot, this is how an administrator states<br />what they know and the cluster proceeds on it.<br />Which is why it is the setting that loses data when it is wrong. An<br />enforced guarantee the hardware does not keep is a torn write under a<br />checksum that disagrees with it, so it is approved against the devices'<br />own report where one exists.<br />It means nothing unless EnableChecksumValidation is set, and it cannot<br />change under a live cluster. | false | Optional: \{\} <br /> |
| `deviceClass` _[StorageClusterDeviceClass](#storageclusterdeviceclass)_ | DeviceClass is the class of backend storage every node in this cluster<br />hands over: NVMe devices named by PCI address, or logical block devices<br />named by path. A cluster is built out of one of them, because an<br />erasure-coding stripe placed across both is written and rebuilt at the<br />slower class's rate. It describes on-disk layout, so it cannot change<br />under a live cluster, and it defaults to NVMe because that is the only<br />class the backend accepted before 26.4. | NVMe | Enum: [NVMe LogicalBlock] <br /> |
| `kms` _[KMSSpec](#kmsspec)_ | KMS selects where the cluster stores volume encryption keys. Switching<br />providers on a live cluster is at least as unsupportable as changing one<br />provider's endpoint, which is why the whole block is immutable rather<br />than its members. |  | Optional: \{\} <br /> |
| `warningThreshold` _[CapacityThresholdSpec](#capacitythresholdspec)_ | WarningThreshold is the capacity level at which the cluster warns. |  | Optional: \{\} <br /> |
| `criticalThreshold` _[CapacityThresholdSpec](#capacitythresholdspec)_ | CriticalThreshold is the capacity level at which the cluster alarms. |  | Optional: \{\} <br /> |
| `maxConcurrentWorkerRestarts` _integer_ | MaxConcurrentWorkerRestarts caps how many Kubernetes workers the operator<br />may drain and restart at once. The effective value is the smaller of this<br />and status.maxFaultTolerance, published as<br />status.maxConcurrentWorkerRestarts so tooling reads one authoritative<br />number rather than recomputing it. | 1 | Minimum: 1 <br />Optional: \{\} <br /> |
| `storageNodes` _[StorageNodesSpec](#storagenodesspec)_ | StorageNodes is the Kubernetes workload the cluster's storage nodes run<br />as, and the cluster owns every object in it by controller reference: a<br />cluster deleted takes its DaemonSet, Services, certificate, and per-node<br />ConfigMap with it. One workload serves the whole cluster, because growth is<br />nodes rather than sets and what differs between hardware generations is per<br />node already. |  | Optional: \{\} <br /> |
| `backup` _[BackupStoreSpec](#backupstorespec)_ | Backup is the S3 location this cluster's backups live in, and it is both<br />the target copies are written to and the inventory the operator walks to<br />produce StorageBackup objects. Mutable: a cluster that has never had a<br />store gains one by acquiring the field, and every backup already in that<br />bucket becomes visible. |  | Optional: \{\} <br /> |
| `disableDataRealignment` _boolean_ | DisableDataRealignment turns off the post-migration data realignment,<br />which runs by default. It is spelled as a disable because the behavior it<br />governs is on: realignment restores the fault-tolerance and node-affinity<br />guarantees every volume move invalidates, so a cluster that says nothing<br />gets them back rather than silently accumulating unaligned structures.<br />Turning it off is for a cluster migrating continuously, where a run that<br />blocks migrations for tens of minutes costs more than the delay in<br />realigning; volumeMigrationSettings.dataRealignment.minMoves is the<br />gentler answer to the same problem.<br />It is a field of the spec rather than of the block it governs, because<br />volumeMigrationSettings.dataRealignment.disableDataRealignment says the<br />same word twice. There is no DisableVolumeMigration beside it: migration<br />cannot be turned off, since a drain, a rebalance, and a device<br />replacement are all performed by moving volumes. |  | Optional: \{\} <br /> |
| `enableVolumeAutoPlacement` _boolean_ | EnableVolumeAutoPlacement turns on automatic, latency-driven rebalancing. |  | Optional: \{\} <br /> |
| `volumeMigrationSettings` _[VolumeMigrationSettings](#volumemigrationsettings)_ | VolumeMigrationSettings controls how volume migration and the<br />post-migration realignment behave, not whether they happen. It is<br />separate from volumeAutoPlacement because realignment applies to every<br />volume move, whatever asked for it. |  | Optional: \{\} <br /> |
| `volumeAutoPlacement` _[VolumeAutoPlacementSettings](#volumeautoplacementsettings)_ | VolumeAutoPlacement configures automatic, latency-driven rebalancing. |  | Optional: \{\} <br /> |


#### StorageClusterStatus







_Appears in:_
- [StorageCluster](#storagecluster)

_Example:_

```yaml
phase: StorageClusterPhase
step: KubeSnapshot
uuid: string
clusterName: string
nqn: string
erasureCodingScheme: string
status: string
configured: boolean
rebalancing: boolean
maxFaultTolerance: integer
maxConcurrentWorkerRestarts: integer
volumeMoveGeneration: integer
realignedGeneration: integer
lastDataRealignmentAt: Time
tasks:
  - id: string
    type: string
    status: string
    retry: integer
provisioningSlots:
  - worker: string
    node: string
    takenAt: Time
activeOpsRef: string
rebalancingMetrics:
  avgDeviationPct: float
  maxDeviationPct: float
  hottestNodeUUID: string
  coolestNodeUUID: string
  imbalancePercent: float
  lastEvaluatedAt: Time
  lastMigrationAt: Time
  nodeMetrics:
    - nodeUUID: string
      latencyDeviationPct: float
      volumeCount: integer
      lastUpdated: Time
message: string
observedGeneration: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _[StorageClusterPhase](#storageclusterphase)_ | Phase is the operator's own view of this cluster. |  | Enum: [Pending Creating Provisioning Activating Online Degraded Unavailable Suspended] <br />Optional: \{\} <br /> |
| `step` _[KubeSnapshot](https://github.com/simplyblock/simplyblock-operator/blob/main/atlas-lib/statemachine/kubernetes.go)_ | Step is the position of the creation machine, as the shared<br />statemachine.KubeSnapshot. The rule is what an Enum marker would do if a<br />marker could reach a field of a shared type. |  | Optional: \{\} <br /> |
| `uuid` _string_ | UUID is the backend cluster UUID. Empty means the cluster has not been<br />created or adopted, and non-empty means steady state. |  | Optional: \{\} <br /> |
| `clusterName` _string_ | ClusterName is the resolved backend name. |  | Optional: \{\} <br /> |
| `nqn` _string_ | NQN is the cluster subsystem qualified name. |  | Optional: \{\} <br /> |
| `erasureCodingScheme` _string_ | ErasureCodingScheme is the active layout, rendered as ndcs, an x, and<br />npcs: a two-plus-one cluster reads 2x1. |  | Optional: \{\} <br /> |
| `status` _string_ | Status is the lifecycle the control plane reports, and its values are the<br />control plane's, which is why they are neither PascalCase nor constrained<br />by an Enum here. |  | Optional: \{\} <br /> |
| `configured` _boolean_ | Configured records that initial setup completed. |  | Optional: \{\} <br /> |
| `rebalancing` _boolean_ | Rebalancing is the control plane's report that a rebalance is in<br />progress, which is one of the two conditions that hold a node operation. |  | Optional: \{\} <br /> |
| `maxFaultTolerance` _integer_ | MaxFaultTolerance is how many nodes may be simultaneously offline without<br />violating redundancy, as the control plane reports it. |  | Optional: \{\} <br /> |
| `maxConcurrentWorkerRestarts` _integer_ | MaxConcurrentWorkerRestarts is the effective limit, the smaller of<br />spec.maxConcurrentWorkerRestarts and maxFaultTolerance. |  | Optional: \{\} <br /> |
| `volumeMoveGeneration` _integer_ | VolumeMoveGeneration is incremented by every migration reaching its<br />successful terminal phase and by nothing else, so it only grows. |  | Optional: \{\} <br /> |
| `realignedGeneration` _integer_ | RealignedGeneration is the generation the last successfully requested<br />realignment covers. A realignment is outstanding while<br />volumeMoveGeneration exceeds it. The value recorded is the one read<br />before the request was sent, which is what that realignment can actually<br />account for: a migration completing while the request is in flight raises<br />volumeMoveGeneration past it and correctly leaves another realignment<br />outstanding. |  | Optional: \{\} <br /> |
| `lastDataRealignmentAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | LastDataRealignmentAt is when a realignment was last requested, and it is<br />what the configured interval spaces requests against. |  | Optional: \{\} <br /> |
| `tasks` _[ClusterTask](#clustertask) array_ | Tasks are the control plane's running and pending jobs, capped at twenty<br />and in the order the control plane reports them: its TaskDTO carries no<br />creation date, so newest-first is not orderable from what is on the wire<br />(design-storagecluster.md §12.1). Completed and canceled tasks are not<br />here: they leave the list and become events, so the length tracks<br />concurrency rather than history. |  | MaxItems: 20 <br />Optional: \{\} <br /> |
| `provisioningSlots` _[ProvisioningSlot](#provisioningslot) array_ | ProvisioningSlots are the workers whose node add is outstanding. The list<br />is the metadata of the Provisioning phase, and it is also the mutex that<br />caps concurrent adds at spec.storageNodes.nodeProvisioningBudget.<br />It is one list on one object because that is what makes taking a slot<br />atomic. A node takes one with an optimistic-locked patch of this field, so<br />exactly one node wins a given resourceVersion and every other is told to<br />count again. A slot recorded per node could not do that: six objects carry<br />six resourceVersions, and two nodes reading a cold cache would both see the<br />same one free and both take it.<br />A worker rather than an object is what holds a slot, because one POST adds<br />every socket of a worker and a two-socket host must consume one slot. |  | MaxItems: 64 <br />Optional: \{\} <br /> |
| `activeOpsRef` _string_ | ActiveOpsRef names the StorageClusterOps currently allowed to operate on<br />this cluster. Empty when none is running. |  | Optional: \{\} <br /> |
| `rebalancingMetrics` _[RebalancingMetrics](#rebalancingmetrics)_ | RebalancingMetrics is written by the auto-rebalancer each evaluation<br />cycle. |  | Optional: \{\} <br /> |
| `message` _string_ | Message is the reason the phase is what it is: one sentence, replaced as<br />the cluster moves, and never a log. |  | Optional: \{\} <br /> |
| `observedGeneration` _integer_ | ObservedGeneration is the generation the rest of this status was computed<br />from, so a stale status can be told from a current one. |  | Optional: \{\} <br /> |




#### StorageDevice



StorageDevice is one storage backend device belonging to one storage node. It
is the bottom of the ownership spine and the narrowest thing an operation can
target.

Objects are created by the operator from what the control plane reports and
are never written by a user: the device's existence follows from the node
having it, and which devices a node uses is decided in the node's own spec.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageDevice
metadata:
  name: string
spec:
  nodeRef: string
  deviceID: string
status:
  phase: StorageDevicePhase
  deviceStatus: string
  role: StorageDeviceRole
  capacity:
    totalBytes: integer
  hardware:
    pciAddress: string
    serialNumber: string
    model: string
    nvmeController: string
  clusterID: string
  nodeID: string
  activeOpsRef: string
  message: string
  observedGeneration: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha2` | | |
| `kind` _string_ | `StorageDevice` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  | Optional: \{\} <br /> |
| `spec` _[StorageDeviceSpec](#storagedevicespec)_ | spec identifies the mirrored control-plane device |  | Required: \{\} <br /> |
| `status` _[StorageDeviceStatus](#storagedevicestatus)_ | status defines the observed state of the device |  | Optional: \{\} <br /> |


#### StorageDeviceOps



StorageDeviceOps is a single operation performed against one StorageDevice.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageDeviceOps
metadata:
  name: string
spec:
  deviceRef: string
  action: StorageDeviceOpsAction
  abort: boolean
status:
  phase: StorageDeviceOpsPhase
  step: KubeSnapshot
  deviceStatusBefore: string
  message: string
  observedGeneration: integer
  startedAt: Time
  completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha2` | | |
| `kind` _string_ | `StorageDeviceOps` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  |  |
| `spec` _[StorageDeviceOpsSpec](#storagedeviceopsspec)_ |  |  |  |
| `status` _[StorageDeviceOpsStatus](#storagedeviceopsstatus)_ |  |  |  |


#### StorageDeviceOpsAction

_Underlying type:_ _string_

StorageDeviceOpsAction is the operation a StorageDeviceOps performs.

There is no Add: a device that appears is discovered (§5.1). There is no bare
Remove either: a removal is a step of Replace and of Migrate, and taking a
device out of the data path without replacing it is Fail (§6.4).

_Validation:_
- Enum: [Restart]

_Appears in:_
- [StorageDeviceOpsSpec](#storagedeviceopsspec)

| Field | Description |
| --- | --- |
| `Restart` | StorageDeviceOpsActionRestart is the action the kind exists for:<br />recycling one device rather than its node.<br /> |
| `SelfTest` | TODO(storagedeviceops): EXTERNAL DEPENDENCY — the four actions below wait<br />on control-plane verbs the v2 API does not offer. It serves restart,<br />remove, and reset where design-storagedevice.md §7 asks for seven, and<br />remove buys no action on its own: it is a step of Replace and of Migrate,<br />and both also need the adopt call that names the device arriving.<br />	SelfTest  POST /api/v2/clusters/\{c\}/storage-nodes/\{n\}/devices/\{d\}/self-test<br />	          runs the device's own self-test and reports the verdict, with<br />	          the short or extended mode in the body.<br />	Fail      POST .../devices/\{d\}/fail<br />	          takes a device out of the data path and leaves it in the slot,<br />	          so the cluster rebuilds its redundancy elsewhere and stops<br />	          reading from a device somebody has judged untrustworthy.<br />	Replace   POST .../devices/adopt<br />	          names the device that arrived; the removal verb exists and the<br />	          pairing is what makes the arrival identifiable.<br />	Migrate   POST .../devices/\{d\}/detach, and the adopt above accepting a<br />	          device WITH ITS CONTENTS. An adopt that can only take an empty<br />	          device turns Migrate into two Replaces and a full rebuild,<br />	          which is what §6.2 gives as the action's reason to exist. This<br />	          is the row whose absence removes an action rather than<br />	          degrading it.<br />The constants are declared and absent from the Enum marker above, so the<br />names exist where the reason does while an object naming one is refused at<br />admission rather than accepted and failed.<br /> |
| `Fail` |  |
| `Replace` |  |
| `Migrate` |  |


#### StorageDeviceOpsPhase

_Underlying type:_ _string_

StorageDeviceOpsPhase is the operation's own progress.

_Validation:_
- Enum: [Pending Running Succeeded Failed Aborted]

_Appears in:_
- [StorageDeviceOpsStatus](#storagedeviceopsstatus)

| Field | Description |
| --- | --- |
| `Pending` |  |
| `Running` |  |
| `Succeeded` |  |
| `Failed` |  |
| `Aborted` |  |


#### StorageDeviceOpsSpec



StorageDeviceOpsSpec is one operation to perform against one StorageDevice.



_Appears in:_
- [StorageDeviceOps](#storagedeviceops)

_Example:_

```yaml
deviceRef: string
action: StorageDeviceOpsAction
abort: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `deviceRef` _string_ | DeviceRef names the StorageDevice this operation acts on, in this<br />operation's own namespace. The operation never owns its target, because<br />deleting the record of an operation must not delete the device record it<br />operated on. |  | MaxLength: 253 <br />Required: \{\} <br /> |
| `action` _[StorageDeviceOpsAction](#storagedeviceopsaction)_ | Action is the operation to perform. |  | Enum: [Restart] <br />Required: \{\} <br /> |
| `abort` _boolean_ | Abort asks a running operation to stop at its next step and unwind.<br />Restart can be aborted before its call is issued and not after: a restart<br />the control plane has accepted is one nothing can recall, so the graph<br />declares where the edge exists rather than this field promising one. |  | Optional: \{\} <br /> |


#### StorageDeviceOpsStatus



StorageDeviceOpsStatus is the observed state of one device operation.



_Appears in:_
- [StorageDeviceOps](#storagedeviceops)

_Example:_

```yaml
phase: StorageDeviceOpsPhase
step: KubeSnapshot
deviceStatusBefore: string
message: string
observedGeneration: integer
startedAt: Time
completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _[StorageDeviceOpsPhase](#storagedeviceopsphase)_ | Phase is the operation's own progress. |  | Enum: [Pending Running Succeeded Failed Aborted] <br />Optional: \{\} <br /> |
| `step` _[KubeSnapshot](https://github.com/simplyblock/simplyblock-operator/blob/main/atlas-lib/statemachine/kubernetes.go)_ | Step is the position of the running action's state machine. It is<br />persisted before the side effect that step performs. |  | Optional: \{\} <br /> |
| `deviceStatusBefore` _string_ | DeviceStatusBefore is what the control plane reported the device's status<br />to be when the operation took its lock, so a wait can tell the device<br />coming back from its never having gone. |  | Optional: \{\} <br /> |
| `message` _string_ | Message is the reason the phase is what it is: one sentence, replaced as<br />the operation moves, and never a log. |  | Optional: \{\} <br /> |
| `observedGeneration` _integer_ | ObservedGeneration is the generation the rest of this status was computed<br />from, so a stale status can be told from a current one. |  | Optional: \{\} <br /> |
| `startedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | StartedAt is when the operation acquired its target's lock. |  | Optional: \{\} <br /> |
| `completedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | CompletedAt is when it reached a terminal phase. |  | Optional: \{\} <br /> |




#### StorageDevicePhase

_Underlying type:_ _string_

StorageDevicePhase is the operator's own view of a device. Degraded and Failed
are deliberately distinct: a degraded device is serving and should not be,
while a failed one is not serving and the cluster is running with less
redundancy than it thinks until it is replaced.

_Validation:_
- Enum: [Online Degraded Unknown Removed Failed]

_Appears in:_
- [StorageDeviceStatus](#storagedevicestatus)

| Field | Description |
| --- | --- |
| `Online` |  |
| `Degraded` |  |
| `Unknown` | StorageDevicePhaseUnknown is a device whose node cannot be reached, so its<br />state is not observable rather than bad. A terminal phase is not<br />overwritten by it.<br /> |
| `Removed` |  |
| `Failed` |  |


#### StorageDeviceRole

_Underlying type:_ _string_

StorageDeviceRole is what the device carries. It is decided when the node is
created, by spec.storageNodes.enableJournalDevice, and it is what makes one
device's failure worse than another's.

_Validation:_
- Enum: [Storage Journal]

_Appears in:_
- [StorageDeviceStatus](#storagedevicestatus)

| Field | Description |
| --- | --- |
| `Storage` |  |
| `Journal` |  |


#### StorageDeviceSpec



StorageDeviceSpec identifies the device this object reports on, and carries
nothing else. Everything a user could change about a device is on the node, so
a spec field here would be a second place to set the same thing.



_Appears in:_
- [StorageDevice](#storagedevice)

_Example:_

```yaml
nodeRef: string
deviceID: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `nodeRef` _string_ | NodeRef names the StorageNode this device belongs to. The node owns this<br />object by controller reference, so deleting the node deletes its devices. |  | Required: \{\} <br /> |
| `deviceID` _string_ | DeviceID is the control plane's identifier for the device. With NodeRef it<br />is the whole of this object's identity. |  | Required: \{\} <br /> |


#### StorageDeviceStatus



StorageDeviceStatus is everything observed about the device.



_Appears in:_
- [StorageDevice](#storagedevice)

_Example:_

```yaml
phase: StorageDevicePhase
deviceStatus: string
role: StorageDeviceRole
capacity:
  totalBytes: integer
hardware:
  pciAddress: string
  serialNumber: string
  model: string
  nvmeController: string
clusterID: string
nodeID: string
activeOpsRef: string
message: string
observedGeneration: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _[StorageDevicePhase](#storagedevicephase)_ | Phase is the operator's own view of the device. |  | Enum: [Online Degraded Unknown Removed Failed] <br />Optional: \{\} <br /> |
| `deviceStatus` _string_ | DeviceStatus is the control plane's own string, in the control plane's<br />spelling, which is why it carries no Enum here. |  | Optional: \{\} <br /> |
| `role` _[StorageDeviceRole](#storagedevicerole)_ | Role is what the device carries. |  | Enum: [Storage Journal] <br />Optional: \{\} <br /> |
| `capacity` _[DeviceCapacity](#devicecapacity)_ | Capacity is how big the device is. What it holds is served as<br />StorageDeviceMetrics instead. |  | Optional: \{\} <br /> |
| `hardware` _[DeviceHardware](#devicehardware)_ | Hardware identifies the part. |  | Optional: \{\} <br /> |
| `clusterID` _string_ | ClusterID and NodeID are the backend ids of the stream this device was<br />last observed on. They are recorded because an object outliving its device<br />has to say which scope's absence would be authoritative before the mirror<br />may delete it; the object's own spec names Kubernetes objects rather than<br />backend ones, so it cannot answer that on its own. |  | Optional: \{\} <br /> |
| `nodeID` _string_ |  |  | Optional: \{\} <br /> |
| `activeOpsRef` _string_ | ActiveOpsRef names the StorageDeviceOps currently allowed to act on this<br />device, and is empty when none is. It is the operation lock every entity<br />of this group carries, and until StorageDeviceOps exists nothing takes it,<br />so the field is present and always empty. Declaring it now is what lets a<br />reader tell "no operation is running" from "this kind cannot say," and it<br />keeps the lock out of the change that introduces the operations. |  | Optional: \{\} <br /> |
| `message` _string_ | Message is the reason the phase is what it is: one sentence, replaced as<br />the device moves, and never a log. |  | Optional: \{\} <br /> |
| `observedGeneration` _integer_ | ObservedGeneration is the generation the rest of this status was computed<br />from. On this kind it moves at most once, since every spec field is fixed<br />when the object is created. |  | Optional: \{\} <br /> |


#### StorageNode



StorageNode is one backend storage node: one SPDK process bound to one NUMA
socket of one Kubernetes worker. One object exists per (workerNode, slot) pair,
owned by the StorageCluster it belongs to.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageNode
metadata:
  name: string
spec:
  clusterRef: string
  nodeSet: string
  workerNode: string
  socketId: string
  nodeIndex: integer
  slot: integer
  config:
    sizing:
      vcpuCount: integer
      minHugePagesSize: string
    spdkImage: string
    spdkImagePullPolicy: PullPolicy
    spdkProxyImage: string
    spdkProxyImagePullPolicy: PullPolicy
    spdkSystemMemory: '^[0-9]+(G|GI|GB|GiB|M|MI|MB|MiB|g|gi|gb|gib|m|mi|mb|mib)?$'
    reservedSystemCPU: '^[0-9]+(-[0-9]+)?(,[0-9]+(-[0-9]+)?)*$'
    journalManager:
      count: integer
      percentPerDevice: integer
    deviceNames:
      - '^([0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F]|/dev/[a-zA-Z0-9._/-]+|[a-zA-Z0-9._-]+)$'
    pcieAllowList:
      - string
    pcieDenyList:
      - string
    pcieModel: string
    driveSizeRange: string
    failureDomain: '^[a-zA-Z0-9]([-_.a-zA-Z0-9]*[a-zA-Z0-9])?$'
    expand: boolean
status:
  phase: StorageNodePhase
  step: KubeSnapshot
  uuid: string
  status: string
  health: boolean
  hostname: string
  uptime: string
  resources:
    cpu: integer
    memory: string
    volumes: integer
    devices:
      online: integer
      total: integer
    capacity:
      totalBytes: integer
      usedBytes: integer
      sampledAt: Time
  ports:
    management: string
    nvmeof: integer
    lvol: integer
    rpc: integer
  failureDomain: string
  activeOpsRef: string
  latencyMetrics:
    nodeUUID: string
    baselineP50NS: integer
    baselineP99NS: integer
    baselineMeasuredAt: Time
  message: string
  observedGeneration: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha2` | | |
| `kind` _string_ | `StorageNode` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  |  |
| `spec` _[StorageNodeSpec](#storagenodespec)_ |  |  |  |
| `status` _[StorageNodeStatus](#storagenodestatus)_ |  |  |  |


#### StorageNodeCapacity



StorageNodeCapacity is a node's storage occupancy, as the control plane last
measured it.

It carries the same two numbers as a device's capacity, because a node's is the
sum of its devices' and a reader comparing the two should not have to reconcile
different shapes. It is written only when the reading has moved materially: a
sample that changed by a few blocks is not worth an etcd write, and writing
every sample would make the reconciler retrigger itself on its own status
update.



_Appears in:_
- [StorageNodeResources](#storagenoderesources)

_Example:_

```yaml
totalBytes: integer
usedBytes: integer
sampledAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `totalBytes` _integer_ | TotalBytes is the storage the node's devices provide. |  | Minimum: 0 <br />Optional: \{\} <br /> |
| `usedBytes` _integer_ | UsedBytes is what they currently hold. |  | Minimum: 0 <br />Optional: \{\} <br /> |
| `sampledAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | SampledAt is when the control plane took the reading. It is not when the<br />object was written, and it may be considerably older if metrics collection<br />has stopped. |  | Optional: \{\} <br /> |


#### StorageNodeConfig



StorageNodeConfig is a storage node's complete configuration, copied from the
ClusterDeploymentConfig entry that produced the node. It is a copy rather than a
projection, because that document is ephemeral and nothing reads it once the
node exists.

Most of it is immutable: by marker where a field has no legitimate writer, and
by the validating webhook where it has exactly one.



_Appears in:_
- [StorageNodeSpec](#storagenodespec)

_Example:_

```yaml
sizing:
  vcpuCount: integer
  minHugePagesSize: string
spdkImage: string
spdkImagePullPolicy: PullPolicy
spdkProxyImage: string
spdkProxyImagePullPolicy: PullPolicy
spdkSystemMemory: '^[0-9]+(G|GI|GB|GiB|M|MI|MB|MiB|g|gi|gb|gib|m|mi|mb|mib)?$'
reservedSystemCPU: '^[0-9]+(-[0-9]+)?(,[0-9]+(-[0-9]+)?)*$'
journalManager:
  count: integer
  percentPerDevice: integer
deviceNames:
  - '^([0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F]|/dev/[a-zA-Z0-9._/-]+|[a-zA-Z0-9._-]+)$'
pcieAllowList:
  - string
pcieDenyList:
  - string
pcieModel: string
driveSizeRange: string
failureDomain: '^[a-zA-Z0-9]([-_.a-zA-Z0-9]*[a-zA-Z0-9])?$'
expand: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `sizing` _[StorageNodeSizing](#storagenodesizing)_ | Sizing is what this node's huge pages and core layout were sized from.<br />Writable by the operator alone. |  | Required: \{\} <br /> |
| `spdkImage` _string_ | SpdkImage overrides the SPDK image the control plane starts for this node,<br />which is what makes a phased image rollout expressible per node. |  | Optional: \{\} <br /> |
| `spdkImagePullPolicy` _[PullPolicy](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#pullpolicy-v1-core)_ | SpdkImagePullPolicy controls when that image is pulled, and defaults to<br />Always because the images this product ships are moving tags.<br />The control plane starts the SPDK pod, not the operator, and its<br />spdk_process_start takes no pull policy: the pod template it renders writes<br />Always itself. So a node states the policy here and the node-add call does<br />not yet carry it, which is a gap the control plane closes rather than this<br />kind. Stating anything but Always is therefore recorded and not yet obeyed. | Always | Enum: [Always Never IfNotPresent] <br />Optional: \{\} <br /> |
| `spdkProxyImage` _string_ | SpdkProxyImage overrides the SPDK proxy image for this node. |  | Optional: \{\} <br /> |
| `spdkProxyImagePullPolicy` _[PullPolicy](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#pullpolicy-v1-core)_ | SpdkProxyImagePullPolicy controls when that image is pulled. It is stated<br />apart from SpdkImagePullPolicy because a node may pin the proxy and follow<br />the SPDK image, and it carries the same not-yet-spent caveat: the template<br />the control plane renders writes Always for both containers. | Always | Enum: [Always Never IfNotPresent] <br />Optional: \{\} <br /> |
| `spdkSystemMemory` _string_ | SpdkSystemMemory is the memory the control plane starts this node's SPDK<br />with, as a size string such as 4G or 512M. It carries no immutability<br />marker, because a node whose device count grew legitimately needs it<br />raised, and the webhook that guards spec.config is what decides who may<br />raise it. |  | Pattern: `^[0-9]+(G\|GI\|GB\|GiB\|M\|MI\|MB\|MiB\|g\|gi\|gb\|gib\|m\|mi\|mb\|mib)?$` <br />Optional: \{\} <br /> |
| `reservedSystemCPU` _string_ | ReservedSystemCPU is the CPU set held back from SPDK for the system, as a<br />core list such as 0,1 or 0-3.<br />It is per node and not per cluster because it names core ids: 0,1 on a<br />sixteen-core worker and 0,1 on a ninety-six-core worker are different<br />fractions of the machine, and a fleet whose groups differ in core count<br />has no one list that is right for all of them.<br />StorageCluster.spec.storageNodes.reservedSystemCPU is the fleet's value,<br />which the pod carries as an environment variable, and this overrides it<br />for the node that states it.<br />On OpenShift the value reaches the kubelet through a KubeletConfig for<br />the machine config pool rather than through the node alone, so nodes<br />sharing a pool that disagree are writing over one another's pool<br />configuration. It carries no immutability marker, because the CPUs a<br />machine holds back are a tuning decision rather than a layout one, and<br />the webhook that guards spec.config is what decides who may retune<br />them. |  | MaxLength: 63 <br />Pattern: `^[0-9]+(-[0-9]+)?(,[0-9]+(-[0-9]+)?)*$` <br />Optional: \{\} <br /> |
| `journalManager` _[JournalManagerSpec](#journalmanagerspec)_ | JournalManager tunes the journal manager count and per-device capacity<br />share for this node. Immutable: both are on-disk layout, fixed when the<br />devices were partitioned. |  | Optional: \{\} <br /> |
| `deviceNames` _string array_ | DeviceNames names the devices to use. An entry is a PCI address<br />("0000:5e:00.0") or a device path ("/dev/sdb,") which are the two classes<br />simplyblock accepts as backend storage, and a bare name ("nvme0n1") is read<br />as a path under /dev. One list carries both spellings, and every entry is of<br />the class its cluster declares in StorageCluster.spec.deviceClass: a list<br />mixing the two, or naming the class the cluster is not, is rejected by the<br />StorageNode validating webhook. Set explicitly, it overrides every filter<br />below. Immutable: it selects which physical devices the node owns. |  | items:Pattern: `^([0-9a-fA-F]\{4\}:[0-9a-fA-F]\{2\}:[0-9a-fA-F]\{2\}\.[0-9a-fA-F]\|/dev/[a-zA-Z0-9._/-]+\|[a-zA-Z0-9._-]+)$` <br />Optional: \{\} <br /> |
| `pcieAllowList` _string array_ | PcieAllowList selects devices by PCI address. It is the one device field a<br />migration writes, merging spec.migrate.newSsdPcie into it so devices added<br />on the target host survive a later rebuild, so it is guarded by the<br />StorageNode validating webhook rather than by a marker. This and the two<br />PCI filters below belong to an NVMe cluster: the webhook rejects them on a<br />cluster whose deviceClass is LogicalBlock, because a logical block device<br />has no PCI address to match. |  | Optional: \{\} <br /> |
| `pcieDenyList` _string array_ | PcieDenyList excludes devices by PCI address. |  | Optional: \{\} <br /> |
| `pcieModel` _string_ | PcieModel filters devices by PCI model string. |  | Optional: \{\} <br /> |
| `driveSizeRange` _string_ | DriveSizeRange filters devices by size. |  | Optional: \{\} <br /> |
| `failureDomain` _string_ | FailureDomain is the label of the fault group this node belongs to<br />such as rack-b, naming the physical grouping it shares with its peers rather<br />than indexing it. Required when the cluster has enableFailureDomains set,<br />and provisioning is held with a FailureDomainMissing event until it is<br />present. Immutable once set, which is what makes it fillable later and then<br />frozen: chunk placement was computed from it.<br />The value takes the shape of a Kubernetes label value, because that is what<br />it is seeded from where a cluster carries topology labels at all. |  | MaxLength: 63 <br />Pattern: `^[a-zA-Z0-9]([-_.a-zA-Z0-9]*[a-zA-Z0-9])?$` <br />Optional: \{\} <br /> |
| `expand` _boolean_ | Expand marks this node as an addition to an already-active cluster, which<br />the control plane reads as a request to rebalance onto it rather than to<br />treat it as part of an initial layout. Immutable once set: it describes how<br />the node joined rather than what it is. |  | Optional: \{\} <br /> |


#### StorageNodeDevices



StorageNodeDevices counts the NVMe devices on a node and how many of them are
online. It is a summary rather than an inventory: per-device capacity, health,
and conditions belong to StorageDevice.

Neither field takes omitempty. Zero online devices is the condition worth
seeing, and a field that disappears at zero would report it as nothing at all. A
node the control plane has not reported on is the absent parent instead.



_Appears in:_
- [StorageNodeResources](#storagenoderesources)

_Example:_

```yaml
online: integer
total: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `online` _integer_ | Online is how many of the node's devices the control plane reports as<br />usable. |  | Minimum: 0 <br /> |
| `total` _integer_ | Total is how many devices the node has. |  | Minimum: 0 <br /> |


#### StorageNodeOps



StorageNodeOps is a single operation performed against one StorageNode. It runs
to a terminal phase and stays afterward as the audit record of what was done, to
which node, with which parameters, and how it ended.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageNodeOps
metadata:
  name: string
spec:
  nodeRef: string
  action: StorageNodeOpsAction
  abort: boolean
  force: boolean
  reattachVolume: boolean
  migrate:
    targetWorkerNode: string
    newSsdPcie:
      - string
  remove:
    systemVolumeFilterRegex: string
status:
  phase: StorageNodeOpsPhase
  step: KubeSnapshot
  message: string
  drain:
    volumesTotal: integer
    volumesMigrated: integer
  observedGeneration: integer
  startedAt: Time
  completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha2` | | |
| `kind` _string_ | `StorageNodeOps` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  |  |
| `spec` _[StorageNodeOpsSpec](#storagenodeopsspec)_ |  |  |  |
| `status` _[StorageNodeOpsStatus](#storagenodeopsstatus)_ |  |  |  |


#### StorageNodeOpsAction

_Underlying type:_ _string_

StorageNodeOpsAction is the operation a StorageNodeOps performs. Values are
PascalCase, which is the casing every enum this API group defines carries;
v1alpha1 spelled them lowercase, and the conversion maps between the two.

_Validation:_
- Enum: [Shutdown Restart Suspend Resume Remove Migrate HostMaintenance]

_Appears in:_
- [StorageNodeOpsSpec](#storagenodeopsspec)

| Field | Description |
| --- | --- |
| `Shutdown` |  |
| `Restart` |  |
| `Suspend` |  |
| `Resume` |  |
| `Remove` |  |
| `Migrate` |  |
| `HostMaintenance` | StorageNodeOpsActionHostMaintenance takes a node down deliberately so that<br />its Kubernetes worker can be drained and rebooted, then brings it back. The<br />operator raises it when it sees the worker cordoned, and a user creating<br />one by hand behaves identically.<br /> |


#### StorageNodeOpsPhase

_Underlying type:_ _string_

StorageNodeOpsPhase is the operation's own progress. Aborted is terminal and
distinct from Failed, because a canceled operation did not go wrong.

_Validation:_
- Enum: [Pending Running Succeeded Failed Aborted]

_Appears in:_
- [StorageNodeOpsStatus](#storagenodeopsstatus)

| Field | Description |
| --- | --- |
| `Pending` | StorageNodeOpsPhasePending: the operation holds no lock and has issued<br />nothing.<br /> |
| `Running` | StorageNodeOpsPhaseRunning: it holds its node's lock and its first side<br />effect may have been issued.<br /> |
| `Succeeded` |  |
| `Failed` |  |
| `Aborted` | StorageNodeOpsPhaseAborted: called off rather than gone wrong. A drain an<br />administrator stops after an hour reported as Failed would sit in the same<br />bucket as one the control plane rejected.<br /> |


#### StorageNodeOpsSpec



StorageNodeOpsSpec is one operation to perform against one StorageNode.



_Appears in:_
- [StorageNodeOps](#storagenodeops)

_Example:_

```yaml
nodeRef: string
action: StorageNodeOpsAction
abort: boolean
force: boolean
reattachVolume: boolean
migrate:
  targetWorkerNode: string
  newSsdPcie:
    - string
remove:
  systemVolumeFilterRegex: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `nodeRef` _string_ | NodeRef names the StorageNode this operation acts on. The operation never<br />owns its target, because deleting the record of an operation must not delete<br />the node it operated on. |  | Required: \{\} <br /> |
| `action` _[StorageNodeOpsAction](#storagenodeopsaction)_ | Action is the operation to perform. |  | Enum: [Shutdown Restart Suspend Resume Remove Migrate HostMaintenance] <br />Required: \{\} <br /> |
| `abort` _boolean_ | Abort asks a running operation to stop at its next step and unwind. It is<br />the only mutable field on this spec, because it is the only thing about an<br />operation that can legitimately be decided after it started. Whether an<br />abort is expressible from the current step is declared by that action's<br />graph rather than checked here. |  | Optional: \{\} <br /> |
| `force` _boolean_ | Force passes the control plane's force flag where the action supports it.<br />Migrate defaults it to true, because the control plane rejects a non-forced<br />restart of a node that is not already offline. |  | Optional: \{\} <br /> |
| `reattachVolume` _boolean_ | ReattachVolume asks the control plane to reattach this node's volumes as<br />part of a restart. Applies to Restart, Migrate, and HostMaintenance. |  | Optional: \{\} <br /> |
| `migrate` _[MigrateSpec](#migratespec)_ | Migrate parameterizes action Migrate and is ignored by the others. |  | Optional: \{\} <br /> |
| `remove` _[RemoveSpec](#removespec)_ | Remove parameterizes action Remove and is ignored by the others. |  | Optional: \{\} <br /> |


#### StorageNodeOpsStatus



StorageNodeOpsStatus is the observed state of one node operation.



_Appears in:_
- [StorageNodeOps](#storagenodeops)

_Example:_

```yaml
phase: StorageNodeOpsPhase
step: KubeSnapshot
message: string
drain:
  volumesTotal: integer
  volumesMigrated: integer
observedGeneration: integer
startedAt: Time
completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _[StorageNodeOpsPhase](#storagenodeopsphase)_ | Phase is the operation's own progress. |  | Enum: [Pending Running Succeeded Failed Aborted] <br />Optional: \{\} <br /> |
| `step` _[KubeSnapshot](https://github.com/simplyblock/simplyblock-operator/blob/main/atlas-lib/statemachine/kubernetes.go)_ | Step is the position of the running action's state machine, as the shared<br />statemachine.KubeSnapshot. The rule is what an Enum marker would do if a<br />marker could reach a field of a shared type. |  | Optional: \{\} <br /> |
| `message` _string_ | Message is the reason the phase is what it is: one sentence, replaced as the<br />operation moves, and never a log. |  | Optional: \{\} <br /> |
| `drain` _[DrainStatus](#drainstatus)_ | Drain is the drain's progress over the node's volumes, set only for action<br />Remove. |  | Optional: \{\} <br /> |
| `observedGeneration` _integer_ | ObservedGeneration is the generation the rest of this status was computed<br />from, so a stale status can be told from a current one. |  | Optional: \{\} <br /> |
| `startedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | StartedAt is when the operation acquired its target's lock. |  | Optional: \{\} <br /> |
| `completedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | CompletedAt is when it reached a terminal phase. |  | Optional: \{\} <br /> |




#### StorageNodePhase

_Underlying type:_ _string_

StorageNodePhase is where the operator has got to with this node. The first two
values are the operator's own provisioning path; the rest are its reading of the
lifecycle status.status carries in the control plane's own spelling.

_Validation:_
- Enum: [Pending Provisioning Online Removing Offline Degraded Failed]

_Appears in:_
- [StorageNodeStatus](#storagenodestatus)

| Field | Description |
| --- | --- |
| `Pending` | StorageNodePhasePending: the object exists and no slot has been claimed<br />for it yet.<br /> |
| `Provisioning` | StorageNodePhaseProvisioning: the provisioning machine is running.<br /> |
| `Online` | StorageNodePhaseOnline: the control plane reports the node online and<br />carrying its share.<br /> |
| `Removing` | StorageNodePhaseRemoving: a StorageNodeOps with action Remove is draining<br />it.<br /> |
| `Offline` | StorageNodePhaseOffline: out of service and reachable, which is where<br />Shutdown, Suspend, and a host maintenance window leave it.<br /> |
| `Degraded` | StorageNodePhaseDegraded: serving with less than its devices, which is the<br />node-level half of what StorageDevice reports per device.<br /> |
| `Failed` | StorageNodePhaseFailed: unreachable, timed out, or provisioning that will<br />not complete.<br /> |


#### StorageNodePorts



StorageNodePorts groups the addresses and ports a node listens on.



_Appears in:_
- [StorageNodeStatus](#storagenodestatus)

_Example:_

```yaml
management: string
nvmeof: integer
lvol: integer
rpc: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `management` _string_ | Management is the management IP address of the node. |  | Optional: \{\} <br /> |
| `nvmeof` _integer_ | The NVMe-oF fabric port. |  | Optional: \{\} <br /> |
| `lvol` _integer_ | Lvol is the logical-volume subsystem port. |  | Optional: \{\} <br /> |
| `rpc` _integer_ | Rpc is the RPC and management API port. |  | Optional: \{\} <br /> |


#### StorageNodeReference



StorageNodeReference locates a StorageNode from a cluster-scoped object.

Every other reference in this API group is a bare string, which works because
both objects are namespaced and a name means the same namespace. A
cluster-scoped object has no namespace for a bare name to mean, and two
clusters in two namespaces may each hold a node called worker-3, so this one
carries both — for the same reason pv.spec.claimRef does in core Kubernetes.



_Appears in:_
- [MigrateVolumeSpec](#migratevolumespec)

_Example:_

```yaml
namespace: string
name: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `namespace` _string_ | Namespace is where the StorageNode lives, which is the namespace of the<br />StorageCluster that owns it. |  | Required: \{\} <br /> |
| `name` _string_ | Name is the StorageNode object's name. |  | Required: \{\} <br /> |


#### StorageNodeResources



StorageNodeResources groups the compute and storage figures the control plane
reports for a node.



_Appears in:_
- [StorageNodeStatus](#storagenodestatus)

_Example:_

```yaml
cpu: integer
memory: string
volumes: integer
devices:
  online: integer
  total: integer
capacity:
  totalBytes: integer
  usedBytes: integer
  sampledAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `cpu` _integer_ | CPU is the number of SPDK cores allocated to this node. |  | Optional: \{\} <br /> |
| `memory` _string_ | Memory is the SPDK memory allocation the control plane reports. |  | Optional: \{\} <br /> |
| `volumes` _integer_ | Volumes is the current number of logical volumes on this node. |  | Optional: \{\} <br /> |
| `devices` _[StorageNodeDevices](#storagenodedevices)_ | Devices summarizes the node's NVMe devices. Absent until the control plane<br />has reported, which is what tells a node that has not reported from one that<br />genuinely has no devices. |  | Optional: \{\} <br /> |
| `capacity` _[StorageNodeCapacity](#storagenodecapacity)_ | Capacity is how much of the node's storage is in use, summed over its<br />devices. It is a measurement rather than a declaration, so it is absent<br />until something has measured it, and it lags reality by the interval at<br />which the control plane's metrics are scraped. |  | Optional: \{\} <br /> |


#### StorageNodeSizing



StorageNodeSizing is what this node's SPDK core layout and huge-page floor were
sized from. It is stamped from StorageCluster.spec when the node is created and
is equal across the fleet in steady state; a rolling hardware upgrade is what
makes two nodes differ, and only for as long as the roll takes. The StorageNode
validating webhook admits a change from the operator and rejects it from
everyone else, because unmanaged divergence is what stops the control plane
placing erasure-coding chunks evenly.

The cluster's maxSubsystemCount is not copied in here. It bounds how many
volumes a node can serve rather than describing the host the node runs on, so
it is the same for every node of a cluster and is read from the cluster when the
node's configuration is generated.



_Appears in:_
- [StorageNodeConfig](#storagenodeconfig)

_Example:_

```yaml
vcpuCount: integer
minHugePagesSize: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `vcpuCount` _integer_ | VCPUCount is the number of vCPUs allocated to SPDK on this node, as an<br />explicit core count rather than a percentage. |  | Minimum: 4 <br />Required: \{\} <br /> |
| `minHugePagesSize` _string_ | MinHugePagesSize is the smallest huge-page allocation this node makes, as a<br />size string such as 100G or 1T, where a bare number is gigabytes. It is a<br />floor rather than a limit: the effective allocation is the larger of this<br />value and the minimum the node's device and subsystem count requires. |  | Optional: \{\} <br /> |


#### StorageNodeSpec



StorageNodeSpec is the desired state of one backend storage node, meaning one
SPDK process bound to one NUMA socket of one Kubernetes worker.



_Appears in:_
- [StorageNode](#storagenode)

_Example:_

```yaml
clusterRef: string
nodeSet: string
workerNode: string
socketId: string
nodeIndex: integer
slot: integer
config:
  sizing:
    vcpuCount: integer
    minHugePagesSize: string
  spdkImage: string
  spdkImagePullPolicy: PullPolicy
  spdkProxyImage: string
  spdkProxyImagePullPolicy: PullPolicy
  spdkSystemMemory: '^[0-9]+(G|GI|GB|GiB|M|MI|MB|MiB|g|gi|gb|gib|m|mi|mb|mib)?$'
  reservedSystemCPU: '^[0-9]+(-[0-9]+)?(,[0-9]+(-[0-9]+)?)*$'
  journalManager:
    count: integer
    percentPerDevice: integer
  deviceNames:
    - '^([0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F]|/dev/[a-zA-Z0-9._/-]+|[a-zA-Z0-9._-]+)$'
  pcieAllowList:
    - string
  pcieDenyList:
    - string
  pcieModel: string
  driveSizeRange: string
  failureDomain: '^[a-zA-Z0-9]([-_.a-zA-Z0-9]*[a-zA-Z0-9])?$'
  expand: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `clusterRef` _string_ | ClusterRef names the StorageCluster this node belongs to. The cluster also<br />owns this object by controller reference, so deleting the cluster deletes<br />its nodes.<br />Bounded at what a StorageCluster name may be, since a longer value names<br />nothing that can exist (design-api-upgrade.md §19.4). |  | MaxLength: 63 <br />Required: \{\} <br /> |
| `nodeSet` _string_ | NodeSet is the name of the group in ClusterDeploymentConfig.nodeSets[] this<br />node was declared under. It is a label rather than a reference: nothing is<br />fetched by it, and it exists so that a node can be traced back to the<br />document that produced it. |  | Optional: \{\} <br /> |
| `workerNode` _string_ | WorkerNode is the Kubernetes worker hostname this node runs on. It is not<br />marked immutable, because a migration re-points it, but the StorageNode<br />validating webhook rejects any change made by an identity outside the<br />operator's namespace. |  | Required: \{\} <br /> |
| `socketId` _string_ | SocketID is the NUMA socket this node is bound to, as declared in the node<br />set's socket list, so 0 or 1. With NodeIndex it decomposes Slot into the<br />pair a person reads; nothing but a print column consumes either.<br />It is not marked immutable, because where a node sits is a fact about the<br />host it runs on and a relocation moves it: the target worker's free socket<br />is not necessarily the source's. The StorageNode validating webhook<br />rejects a change made by an identity outside the operator's namespace,<br />which is the same treatment WorkerNode takes and for the same reason. |  | Optional: \{\} <br /> |
| `nodeIndex` _integer_ | NodeIndex is the position among the nodes sharing this socket, in<br />0..nodesPerSocket-1. See SocketID, whose guard it shares. |  | Minimum: 0 <br />Optional: \{\} <br /> |
| `slot` _integer_ | Slot is which storage-node slot on this worker the object occupies, counted<br />from zero. A worker runs one node per socket per nodesPerSocket, and the<br />slot is the position among them. It is the identity the operator keys on:<br />the topology label the CSI driver reads is<br />storage.simplyblock.io/storage-node-uuid.<clusterUUID>.<slot>, and the slot<br />outlives the node filling it, because only the UUID behind it changes when a<br />node is replaced or relocated. |  | Minimum: 0 <br />Optional: \{\} <br /> |
| `config` _[StorageNodeConfig](#storagenodeconfig)_ | Config is this node's complete configuration, copied from the<br />ClusterDeploymentConfig entry that produced it. It is a copy rather than a<br />projection, because that document is ephemeral: nothing reads it once the<br />node exists, deleting it changes nothing, and editing it reaches only nodes<br />created afterward. |  | Required: \{\} <br /> |


#### StorageNodeStatus



StorageNodeStatus is the observed state of one storage node.



_Appears in:_
- [StorageNode](#storagenode)

_Example:_

```yaml
phase: StorageNodePhase
step: KubeSnapshot
uuid: string
status: string
health: boolean
hostname: string
uptime: string
resources:
  cpu: integer
  memory: string
  volumes: integer
  devices:
    online: integer
    total: integer
  capacity:
    totalBytes: integer
    usedBytes: integer
    sampledAt: Time
ports:
  management: string
  nvmeof: integer
  lvol: integer
  rpc: integer
failureDomain: string
activeOpsRef: string
latencyMetrics:
  nodeUUID: string
  baselineP50NS: integer
  baselineP99NS: integer
  baselineMeasuredAt: Time
message: string
observedGeneration: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _[StorageNodePhase](#storagenodephase)_ | Phase is the operator's own view of this node, and the field its<br />provisioning branches on. |  | Enum: [Pending Provisioning Online Removing Offline Degraded Failed] <br />Optional: \{\} <br /> |
| `step` _[KubeSnapshot](https://github.com/simplyblock/simplyblock-operator/blob/main/atlas-lib/statemachine/kubernetes.go)_ | Step is the position of the provisioning machine, as the shared<br />statemachine.KubeSnapshot. The rule is what an Enum marker would do if a<br />marker could reach a field of a shared type. |  | Optional: \{\} <br /> |
| `uuid` _string_ | UUID is the backend node UUID. Empty means the node has neither been<br />provisioned nor adopted, and non-empty means steady state. |  | Optional: \{\} <br /> |
| `status` _string_ | Status is the lifecycle the control plane reports: online, suspended,<br />offline, in_creation, in_restart, in_shutdown, unreachable, or timeout. The<br />values are the control plane's, which is why they are neither PascalCase nor<br />constrained by an Enum here. |  | Optional: \{\} <br /> |
| `health` _boolean_ | Health is the health flag the control plane reports. |  | Optional: \{\} <br /> |
| `hostname` _string_ | Hostname is the node hostname as the control plane reports it. |  | Optional: \{\} <br /> |
| `uptime` _string_ | Uptime is the node uptime as the control plane reports it. |  | Optional: \{\} <br /> |
| `resources` _[StorageNodeResources](#storagenoderesources)_ | Resources groups the reported compute and storage figures. |  | Optional: \{\} <br /> |
| `ports` _[StorageNodePorts](#storagenodeports)_ | Ports groups the reported addresses and ports. |  | Optional: \{\} <br /> |
| `failureDomain` _string_ | FailureDomain is the failure-domain label the control plane actually<br />assigned, which is not necessarily the one spec.config.failureDomain<br />requested. |  | Optional: \{\} <br /> |
| `activeOpsRef` _string_ | ActiveOpsRef names the StorageNodeOps currently allowed to touch this node.<br />Empty when none is running. |  | Optional: \{\} <br /> |
| `latencyMetrics` _[NodeLatencyMetrics](#nodelatencymetrics)_ | LatencyMetrics holds the fio-measured NVMe-oF baseline the volume<br />rebalancer reads. |  | Optional: \{\} <br /> |
| `message` _string_ | Message is the reason the phase is what it is: one sentence, replaced as the<br />node moves, and never a log. |  | Optional: \{\} <br /> |
| `observedGeneration` _integer_ | ObservedGeneration is the generation the rest of this status was computed<br />from, so a stale status can be told from a current one. |  | Optional: \{\} <br /> |




#### StorageNodesSpec



StorageNodesSpec is the Kubernetes workload every storage node in the cluster
runs as: a DaemonSet, a headless Service and its EndpointSlices, a serving
certificate, a ServiceAccount, and the ConfigMap the init container reads its
per-node configuration out of.

Every field here is cluster-uniform by construction, because a DaemonSet is one
object for every node it schedules and its pod template cannot differ per node.
What can differ is in StorageNode.spec.config: the two images, the SPDK system
memory, and the sizing block, which are per node precisely so that an image
rollout and a hardware re-size can walk the fleet one machine at a time.



_Appears in:_
- [StorageClusterSpec](#storageclusterspec)

_Example:_

```yaml
image: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
imagePullPolicy: PullPolicy
mgmtInterface: string
dataInterfaces:
  - string
socketsToUse:
  - string
nodesPerSocket: integer
nodeProvisioningBudget: integer
enableJournalDevice: boolean
enableFormat4K: boolean
enableBlockFormat: boolean
enableCpuTopology: boolean
reservedSystemCPU: string
enableKubeletConfiguration: boolean
ubuntuHost: boolean
openshift:
  machineConfigPool: '^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
tolerations:
  - Toleration
containerResources: ResourceRequirements
initContainerResources: ResourceRequirements
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `image` _string_ | Image is the storage-node container image. Defaults to the ControlPlane<br />singleton's spec.image when unset, so a deployment states the version once. |  | Pattern: `^($\|(quay\.io/simplyblock-io\|docker\.io/simplyblock\|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]\{64\})?)$` <br />Optional: \{\} <br /> |
| `imagePullPolicy` _[PullPolicy](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#pullpolicy-v1-core)_ | ImagePullPolicy controls when that image is pulled. It defaults to Always<br />for the reason SimplyblockDriver's does: the images this product ships are<br />moving tags, so a node brought up after a release that kept IfNotPresent<br />would run whatever its kubelet already held. The workload builder has<br />always meant this and falls back to Always for an unset policy, a fallback<br />the schema default means it never reaches. | Always | Enum: [Always Never IfNotPresent] <br />Optional: \{\} <br /> |
| `mgmtInterface` _string_ | MgmtInterface is the management network interface storage nodes bind. |  | Optional: \{\} <br /> |
| `dataInterfaces` _string array_ | DataInterfaces are the data-plane network interfaces. |  | Optional: \{\} <br /> |
| `socketsToUse` _string array_ | SocketsToUse restricts deployment to selected NUMA sockets. Empty means<br />socket 0 alone. |  | Optional: \{\} <br /> |
| `nodesPerSocket` _integer_ | NodesPerSocket is how many storage nodes run per NUMA socket. | 1 | Minimum: 1 <br />Optional: \{\} <br /> |
| `nodeProvisioningBudget` _integer_ | NodeProvisioningBudget limits how many workers may be in the node-add<br />process at once, counted by distinct worker rather than by object so that a<br />two-socket host consumes one slot. Workers hosting a FoundationDB pod are<br />always sequential regardless of this value, because a node add reboots the<br />host and two simultaneous FoundationDB reboots reduce the control plane's<br />own fault tolerance. | 1 | Minimum: 1 <br />Optional: \{\} <br /> |
| `enableJournalDevice` _boolean_ | EnableJournalDevice dedicates the smallest NVMe device on each node to the<br />journal manager, instead of carving a journal partition out of every<br />device. |  | Optional: \{\} <br /> |
| `enableFormat4K` _boolean_ | EnableFormat4K formats NVMe devices to a 4K block size where the device<br />supports it. |  | Optional: \{\} <br /> |
| `enableBlockFormat` _boolean_ | EnableBlockFormat wipes the partition tables and filesystem signatures<br />from this cluster's logical block devices, so that a disk carrying<br />something already becomes one a storage node can take.<br />It is the block class's half of the document's enableDriveFormat, and a<br />separate field because it is a separate operation on a separate channel:<br />EnableFormat4K is a reformat the control plane performs at node-add, and<br />this is a wipefs node_configure.py performs on the worker before the node<br />is added at all. A block device's block size is fixed by the drive, so<br />there is no reformat to ask for, and an NVMe controller is handed to SPDK<br />whole, so there are no signatures to wipe. Neither operation is available<br />in the other's class.<br />Destructive, and immutable for the reason the other is: it describes what<br />was done to the disks a fleet was built on. |  | Optional: \{\} <br /> |
| `enableCpuTopology` _boolean_ | EnableCpuTopology turns on topology-aware CPU assignment. |  | Optional: \{\} <br /> |
| `reservedSystemCPU` _string_ | ReservedSystemCPU is the CPU set held back from SPDK for system workloads. |  | Optional: \{\} <br /> |
| `enableKubeletConfiguration` _boolean_ | EnableKubeletConfiguration lets the storage node apply the kubelet<br />configuration changes it needs. Off by default, which is the behavior the<br />retired skipKubeletConfiguration expressed by being set. |  | Optional: \{\} <br /> |
| `ubuntuHost` _boolean_ | UbuntuHost states that the worker's host OS is Ubuntu, which changes how<br />the node configures huge pages and the kernel modules it loads. |  | Optional: \{\} <br /> |
| `openshift` _[OpenShiftSpec](#openshiftspec)_ | OpenShift is what this deployment states because it runs on OpenShift,<br />and its presence is that statement. See OpenShiftSpec. |  | Optional: \{\} <br /> |
| `tolerations` _[Toleration](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#toleration-v1-core) array_ | Tolerations are applied to the storage-node pods. |  | Optional: \{\} <br /> |
| `containerResources` _[ResourceRequirements](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#resourcerequirements-v1-core)_ | ContainerResources sets requests and limits for the storage-node container.<br />Unset enforces no limits. |  | Optional: \{\} <br /> |
| `initContainerResources` _[ResourceRequirements](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#resourcerequirements-v1-core)_ | InitContainerResources does the same for the init container. |  | Optional: \{\} <br /> |


#### StoragePool



StoragePool carves a StorageCluster into a unit with its own capacity limit
and QoS ceilings, and it is what a StorageClass is assigned to. It is
therefore the join between the storage administrator's world and the
application developer's, a join held together by three labels, an opaque
parameter map, and a finalizer rather than by the API.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha2
kind: StoragePool
metadata:
  name: string
spec:
  clusterRef: string
  allowedNodes:
    - string
  limits:
    capacity: string
    maxVolumeSize: string
    iops: integer
    throughput:
      read: integer
      write: integer
      readWrite: integer
  volumeDefaults:
    iops: integer
    throughput:
      read: integer
      write: integer
      readWrite: integer
    filesystem: string
    enableCompression: boolean
    enableClientCompression: boolean
    enableClientDeduplication: boolean
    enableEncryption: boolean
    enableReplication: boolean
    enableDHCHAP: boolean
    priorityClass: string
    fabric: string
    maxNamespacesPerSubsystem: integer
    tune2fsReservedBlocks: string
status:
  phase: StoragePoolPhase
  uuid: string
  status: string
  storageClassNames:
    - string
  defaultStorageClassName: string
  limits:
    host: string
    iops: integer
    throughput:
      read: integer
      write: integer
      readWrite: integer
  allowedNodes:
    - string
  activeOpsRef: string
  message: string
  observedGeneration: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha2` | | |
| `kind` _string_ | `StoragePool` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  |  |
| `spec` _[StoragePoolSpec](#storagepoolspec)_ |  |  |  |
| `status` _[StoragePoolStatus](#storagepoolstatus)_ |  |  |  |


#### StoragePoolOps



StoragePoolOps is a single operation performed against one StoragePool.
Analogous to a Kubernetes Job: it drives an action to completion and records
the result, and only one StoragePoolOps may be active per StoragePool at a
time, which the pool's status.activeOpsRef enforces.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha2
kind: StoragePoolOps
metadata:
  name: string
spec:
  poolRef: string
  action: StoragePoolOpsAction
  abort: boolean
status:
  phase: StoragePoolOpsPhase
  step: KubeSnapshot
  message: string
  observedGeneration: integer
  startedAt: Time
  completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha2` | | |
| `kind` _string_ | `StoragePoolOps` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  |  |
| `spec` _[StoragePoolOpsSpec](#storagepoolopsspec)_ |  |  |  |
| `status` _[StoragePoolOpsStatus](#storagepoolopsstatus)_ |  |  |  |


#### StoragePoolOpsAction

_Underlying type:_ _string_

StoragePoolOpsAction is the operation a StoragePoolOps performs. The kind
holds one action and that action is provisional: nothing implements it and
nothing depends on it. It is declared because the motivation is real and
cheaper to keep than to rediscover, not because it is work in progress.

_Validation:_
- Enum: [Rebalance]

_Appears in:_
- [StoragePoolOpsSpec](#storagepoolopsspec)

| Field | Description |
| --- | --- |
| `Rebalance` | StoragePoolOpsActionRebalance moves the pool's volumes off nodes<br />spec.allowedNodes no longer lists. It is a fan-out of PersistentVolumeOps<br />rather than a backend call: the control plane has no pool-granularity<br />rebalance and does not need one, because moving a volume is already an<br />operation this group has. The decision is the pool's and only the<br />execution is per-volume, which is why the action lives on this kind.<br /> |


#### StoragePoolOpsPhase

_Underlying type:_ _string_

StoragePoolOpsPhase is the operation's own progress.

_Validation:_
- Enum: [Pending Running Succeeded Failed Aborted]

_Appears in:_
- [StoragePoolOpsStatus](#storagepoolopsstatus)

| Field | Description |
| --- | --- |
| `Pending` | StoragePoolOpsPhasePending is an operation waiting for its target's lock.<br /> |
| `Running` | StoragePoolOpsPhaseRunning is an operation holding the lock and working.<br /> |
| `Succeeded` | StoragePoolOpsPhaseSucceeded is a finished operation that did what it said.<br /> |
| `Failed` | StoragePoolOpsPhaseFailed is a finished operation that did not.<br /> |
| `Aborted` | StoragePoolOpsPhaseAborted is an operation stopped on request, whose<br />unwind has finished.<br /> |


#### StoragePoolOpsSpec



StoragePoolOpsSpec is one operation to perform against one StoragePool.



_Appears in:_
- [StoragePoolOps](#storagepoolops)

_Example:_

```yaml
poolRef: string
action: StoragePoolOpsAction
abort: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `poolRef` _string_ | PoolRef names the StoragePool this operation acts on, in this object's own<br />namespace. The operation never owns its target, because deleting the<br />record of an operation must not delete the pool it operated on. |  | Required: \{\} <br /> |
| `action` _[StoragePoolOpsAction](#storagepoolopsaction)_ | Action is the operation to perform. Immutable: an operation that changed<br />what it was doing halfway through would have a status describing neither. |  | Enum: [Rebalance] <br />Required: \{\} <br /> |
| `abort` _boolean_ | Abort asks a running operation to stop at its next step and unwind. |  | Optional: \{\} <br /> |


#### StoragePoolOpsStatus



StoragePoolOpsStatus is the observed state of one pool operation.



_Appears in:_
- [StoragePoolOps](#storagepoolops)

_Example:_

```yaml
phase: StoragePoolOpsPhase
step: KubeSnapshot
message: string
observedGeneration: integer
startedAt: Time
completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _[StoragePoolOpsPhase](#storagepoolopsphase)_ | Phase is the operation's own progress. |  | Enum: [Pending Running Succeeded Failed Aborted] <br />Optional: \{\} <br /> |
| `step` _[KubeSnapshot](https://github.com/simplyblock/simplyblock-operator/blob/main/atlas-lib/statemachine/kubernetes.go)_ | Step is the position of the running action's state machine. It is<br />persisted before the side effect that step performs. The rule repeats the<br />StoragePoolOpsStep enum because a marker cannot reach a field of the<br />shared snapshot type. |  | Optional: \{\} <br /> |
| `message` _string_ | Message is the reason the phase is what it is: one sentence, replaced as<br />the operation moves, and never a log. |  | Optional: \{\} <br /> |
| `observedGeneration` _integer_ | ObservedGeneration is the generation the rest of this status was computed<br />from, so a stale status can be told from a current one. |  | Optional: \{\} <br /> |
| `startedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | StartedAt is when the operation acquired its target's lock. |  | Optional: \{\} <br /> |
| `completedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | CompletedAt is when it reached a terminal phase. |  | Optional: \{\} <br /> |




#### StoragePoolPhase

_Underlying type:_ _string_

StoragePoolPhase is where the operator has got to with this pool.

_Validation:_
- Enum: [Pending Ready Deleting]

_Appears in:_
- [StoragePoolStatus](#storagepoolstatus)

| Field | Description |
| --- | --- |
| `Pending` | StoragePoolPhasePending is a pool that has no backend UUID yet, whether<br />because its cluster is not finished or because the create has not landed.<br /> |
| `Ready` | StoragePoolPhaseReady is a pool the control plane has created and that<br />volumes can be provisioned from.<br /> |
| `Deleting` | StoragePoolPhaseDeleting is a pool being torn down, which may be held for<br />a long time behind an assigned class or a bound volume.<br /> |


#### StoragePoolSpec



StoragePoolSpec is the desired state of one tenancy unit within a cluster.



_Appears in:_
- [StoragePool](#storagepool)

_Example:_

```yaml
clusterRef: string
allowedNodes:
  - string
limits:
  capacity: string
  maxVolumeSize: string
  iops: integer
  throughput:
    read: integer
    write: integer
    readWrite: integer
volumeDefaults:
  iops: integer
  throughput:
    read: integer
    write: integer
    readWrite: integer
  filesystem: string
  enableCompression: boolean
  enableClientCompression: boolean
  enableClientDeduplication: boolean
  enableEncryption: boolean
  enableReplication: boolean
  enableDHCHAP: boolean
  priorityClass: string
  fabric: string
  maxNamespacesPerSubsystem: integer
  tune2fsReservedBlocks: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `clusterRef` _string_ | ClusterRef names the StorageCluster this pool is carved out of, in this<br />pool's own namespace. The cluster owns this object by controller<br />reference, so deleting the cluster deletes its pools, held behind each<br />pool's own finalizer while classes are assigned or volumes are bound.<br />Immutable from creation: which cluster a pool is in is its identity.<br />The maximum is what a StorageCluster name may be rather than what a<br />reference may be: a longer value names nothing that can exist, and the<br />reference is immutable, so admitting one creates a pool whose only<br />remedy is deletion (design-api-upgrade.md §19.4). |  | MaxLength: 63 <br />Required: \{\} <br /> |
| `allowedNodes` _string array_ | AllowedNodes restricts which hosts may carry this pool's volumes, by<br />Kubernetes Node name. Empty means every node in the cluster. Narrowing it<br />stops new volumes landing on the removed nodes and leaves the existing<br />ones where they are.<br />The list is left exactly as authored: a name that no longer resolves is<br />dropped from Status.AllowedNodes rather than pruned from here, so a node<br />removed for maintenance and added back under the same name returns to the<br />pools that named it without anybody re-authoring them. |  | Optional: \{\} <br /> |
| `limits` _[PoolLimits](#poollimits)_ | Limits are the ceilings the pool as a whole is held to. Mutable: raising a<br />pool's capacity is an ordinary operation the control plane supports, and it<br />does not touch any StorageClass. |  | Optional: \{\} <br /> |
| `volumeDefaults` _[VolumeDefaults](#volumedefaults)_ | VolumeDefaults are what every volume in the pool is created with.<br />Immutable once set, because StorageClass.parameters is immutable in the<br />Kubernetes API: a pool whose defaults changed would have a class the<br />operator cannot update. Changing them means creating a new pool. |  | Optional: \{\} <br /> |


#### StoragePoolStatus



StoragePoolStatus is the observed state of one pool.



_Appears in:_
- [StoragePool](#storagepool)

_Example:_

```yaml
phase: StoragePoolPhase
uuid: string
status: string
storageClassNames:
  - string
defaultStorageClassName: string
limits:
  host: string
  iops: integer
  throughput:
    read: integer
    write: integer
    readWrite: integer
allowedNodes:
  - string
activeOpsRef: string
message: string
observedGeneration: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _[StoragePoolPhase](#storagepoolphase)_ | Phase is the operator's own view of this pool. |  | Enum: [Pending Ready Deleting] <br />Optional: \{\} <br /> |
| `uuid` _string_ | UUID is the backend pool UUID. Empty means the pool has not been created,<br />and it is the field the controller branches on. |  | Optional: \{\} <br /> |
| `status` _string_ | Status is the lifecycle the control plane reports, in the control plane's<br />own spelling, which is why it carries no Enum here. |  | Optional: \{\} <br /> |
| `storageClassNames` _string array_ | StorageClassNames are the classes assigned to this pool, found by the<br />three storage.simplyblock.io labels a class carries. Empty means no class<br />draws from this pool yet, which is a valid state and what a freshly<br />created cluster's default pool has before anybody writes one. Publishing<br />it is what makes the assignment readable from the pool, and what a<br />deletion is held on. |  | Optional: \{\} <br /> |
| `defaultStorageClassName` _string_ | DefaultStorageClassName is the class the operator wrote for the default<br />pool, set on that pool only. It records that the class was created, so a<br />class missing while this is set was deleted deliberately and is not<br />written again. |  | Optional: \{\} <br /> |
| `limits` _[PoolLimitsStatus](#poollimitsstatus)_ | Limits is what the control plane reports the ceilings to be. |  | Optional: \{\} <br /> |
| `allowedNodes` _string array_ | AllowedNodes is Spec.AllowedNodes resolved against the Node objects that<br />exist, which is what the control plane's host list and the per-pool node<br />labels are derived from. An empty list here is not the same as an absent<br />Spec.AllowedNodes: absent means every node, and empty after resolution<br />means the pool can place nothing. |  | Optional: \{\} <br /> |
| `activeOpsRef` _string_ | ActiveOpsRef names the StoragePoolOps currently allowed to act on this<br />pool. Empty when none is running. |  | Optional: \{\} <br /> |
| `message` _string_ | Message is the reason the phase is what it is: one sentence, replaced as<br />the pool moves, and never a log. |  | Optional: \{\} <br /> |
| `observedGeneration` _integer_ | ObservedGeneration is the generation the rest of this status was computed<br />from, so a stale status can be told from a current one. |  | Optional: \{\} <br /> |


#### StripeSpec



StripeSpec is the erasure-coding layout: how many data chunks a stripe
carries and how many parity chunks protect them.

The pair is one of the seven schemes simplyblock supports, and the rule below
is the same set the control plane holds in SUPPORTED_ERASURE_CODING_SCHEMES.
It is stated here as well because the control plane's refusal arrives at the
cluster create, which is several steps and — for a cluster a deployment config
produced — one irreversible approval after the apply that stated the scheme.

Each scheme also has a storage-node count below which it must not be used,
which is ndcs+npcs nodes to place a stripe across plus one spare per tolerated
failure to rebuild onto: 1 for 1+0, 3 for 1+1, 4 for 2+1, 6 for 4+1, 5 for
1+2, 6 for 2+2, and 8 for 4+2. That is not expressible here, because the nodes
are objects of their own and a cluster is created before any of them exists.
It is answered by the deployment config's validation, by its approval webhook,
and by the cluster's activation gate.



_Appears in:_
- [ClusterTemplate](#clustertemplate)
- [StorageClusterSpec](#storageclusterspec)

_Example:_

```yaml
dataChunks: integer
parityChunks: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `dataChunks` _integer_ | DataChunks is the number of data chunks per stripe (ndcs). |  | Minimum: 1 <br />Optional: \{\} <br /> |
| `parityChunks` _integer_ | ParityChunks is the number of parity chunks per stripe (npcs), and<br />therefore how many chunk losses a stripe survives. |  | Minimum: 0 <br />Optional: \{\} <br /> |


#### ThroughputLimits



ThroughputLimits are throughput ceilings in megabytes per second. The unit is
the field's rather than the value's, which is why the class keys these reach
spell it out: a parameter map has no type to carry it.



_Appears in:_
- [PoolLimits](#poollimits)
- [PoolLimitsStatus](#poollimitsstatus)
- [VolumeDefaults](#volumedefaults)

_Example:_

```yaml
read: integer
write: integer
readWrite: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `read` _integer_ | Read is the read-only ceiling, written as max_read_mbytes_per_sec. |  | Minimum: 0 <br />Optional: \{\} <br /> |
| `write` _integer_ | Write is the write-only ceiling, written as max_write_mbytes_per_sec. |  | Minimum: 0 <br />Optional: \{\} <br /> |
| `readWrite` _integer_ | ReadWrite is the ceiling on both directions together, written as<br />max_mbytes_per_sec. It is not an access mode, which is the confusion the<br />older class key qos_rw_mbytes invited. |  | Minimum: 0 <br />Optional: \{\} <br /> |


#### UpgradeSpec



UpgradeSpec parameterizes the Upgrade action and is ignored by the others.



_Appears in:_
- [ControlPlaneOpsSpec](#controlplaneopsspec)

_Example:_

```yaml
image: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `image` _string_ | Image is the version to move to. It replaces<br />ControlPlane.spec.source.managed.image when the operation succeeds, so the<br />entity keeps describing what is running. |  | Pattern: `^($\|(quay\.io/simplyblock-io\|docker\.io/simplyblock\|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]\{64\})?)$` <br />Required: \{\} <br /> |


#### ValidationJob



ValidationJob is one Job started to check a path is reachable from one node.

It is tracked so that Verifying can delete every Job the operation started,
including after a restart. The namespace is recorded for the same reason
spec.migrate.targetNodeRef carries one: a Job is namespaced and this object
is not, so a name alone would not locate it.



_Appears in:_
- [MigrationStatus](#migrationstatus)

_Example:_

```yaml
namespace: string
name: string
node: string
succeeded: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `namespace` _string_ |  |  | Required: \{\} <br /> |
| `name` _string_ |  |  | Required: \{\} <br /> |
| `node` _string_ | Node is the worker the Job is pinned to, which is a node consuming one of<br />the migrated subsystem's volumes. |  | Optional: \{\} <br /> |
| `succeeded` _boolean_ | Succeeded records a node whose paths were checked and found ready, so a<br />restart does not run the check again on a node that already passed and<br />whose Job its own TTL may already have reaped. |  | Optional: \{\} <br /> |


#### VaultKMS



VaultKMS configures the HashiCorp Vault key store.



_Appears in:_
- [KMSSpec](#kmsspec)

_Example:_

```yaml
endpoint: '^https?://[a-zA-Z0-9.-]+(:[0-9]{1,5})?(/.*)?$'
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `endpoint` _string_ | Endpoint is the Vault endpoint, for example, https://vault.example.com:8200.<br />Rejected unless it resolves to an external address. |  | Pattern: `^https?://[a-zA-Z0-9.-]+(:[0-9]\{1,5\})?(/.*)?$` <br />Required: \{\} <br /> |


#### VolumeAutoPlacementSettings



VolumeAutoPlacementSettings configures automatic, latency-driven volume
rebalancing. Whether it runs at all is
StorageClusterSpec.EnableVolumeAutoPlacement.



_Appears in:_
- [StorageClusterSpec](#storageclusterspec)

_Example:_

```yaml
disableMigration: boolean
evaluationInterval: Duration
imbalanceThreshold: integer
minHotColdDifferencePct: integer
defaultCoolDownSeconds: integer
maxVolumeMigrationsPerCycle: integer
storageNodeCandidateCount: integer
metricsBackend: MetricsBackend
prometheusURL: string
enableLatencyBenchmark: boolean
latencyBenchmarkInterval: Duration
baselineStrategy: BaselineStrategy
baselineWindow: Duration
baselineColdStart: BaselineColdStartPolicy
baselineMinSamples: integer
baselineOutlierK: float
iopsWeight: float
throughputWeight: float
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `disableMigration` _boolean_ | DisableMigration stops the rebalancer creating PersistentVolume<br />migrations while leaving every other part of a cycle running: load is<br />evaluated, deviations are computed, candidates are selected, and metrics<br />are emitted, and the migrations are discarded rather than created. It is<br />the dry run, and it is spelled as a disable because the behavior it<br />governs is on by default. |  | Optional: \{\} <br /> |
| `evaluationInterval` _[Duration](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#duration-v1-meta)_ | EvaluationInterval is how often the rebalancer evaluates load. Defaults<br />to 60s. |  | Optional: \{\} <br /> |
| `imbalanceThreshold` _integer_ | ImbalanceThreshold is the latency deviation from baseline, in percent, a<br />node must exceed before it is considered a rebalancing source. Defaults<br />to 80. |  | Optional: \{\} <br /> |
| `minHotColdDifferencePct` _integer_ | MinHotColdDifferencePct is how far below the hot source, in percentage<br />points of deviation, a candidate target must be before a volume is moved.<br />It is what stops a migration between two near-equally loaded nodes.<br />Defaults to 20. |  | Optional: \{\} <br /> |
| `defaultCoolDownSeconds` _integer_ | DefaultCoolDownSeconds is how long a volume is left alone after it has<br />been migrated. Defaults to 600. |  | Optional: \{\} <br /> |
| `maxVolumeMigrationsPerCycle` _integer_ | MaxVolumeMigrationsPerCycle caps how many volumes one cycle moves.<br />Defaults to 10. |  | Optional: \{\} <br /> |
| `storageNodeCandidateCount` _integer_ | StorageNodeCandidateCount is how many of the most loaded nodes are<br />evaluated each cycle to find the best source. Defaults to 3. |  | Optional: \{\} <br /> |
| `metricsBackend` _[MetricsBackend](#metricsbackend)_ | MetricsBackend selects the source of I/O metrics. Defaults to Prometheus. |  | Enum: [ControlPlane Prometheus Uniform] <br />Optional: \{\} <br /> |
| `prometheusURL` _string_ | PrometheusURL is required when MetricsBackend is Prometheus. |  | Optional: \{\} <br /> |
| `enableLatencyBenchmark` _boolean_ | EnableLatencyBenchmark turns on fio-based NVMe-oF latency measurement<br />through Kubernetes Jobs. It is off unless a RebalancerImage is<br />configured. |  | Optional: \{\} <br /> |
| `latencyBenchmarkInterval` _[Duration](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#duration-v1-meta)_ | LatencyBenchmarkInterval is how often those Jobs run against each storage<br />node. It also sets the step of the rolling-window baseline query, which<br />is the cadence at which the probe sidecar publishes samples. Defaults to<br />5m. |  | Optional: \{\} <br /> |
| `baselineStrategy` _[BaselineStrategy](#baselinestrategy)_ | BaselineStrategy selects how the per-node baseline is derived. Defaults<br />to RollingWindow. |  | Enum: [Benchmark RollingWindow] <br />Optional: \{\} <br /> |
| `baselineWindow` _[Duration](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#duration-v1-meta)_ | BaselineWindow is the look-back the RollingWindow strategy reduces.<br />Defaults to 6h. |  | Optional: \{\} <br /> |
| `baselineColdStart` _[BaselineColdStartPolicy](#baselinecoldstartpolicy)_ | BaselineColdStart selects what happens to an under-sampled node. Defaults<br />to PartialWindow. |  | Enum: [Defer PartialWindow] <br />Optional: \{\} <br /> |
| `baselineMinSamples` _integer_ | BaselineMinSamples is the sample count below which a node counts as<br />under-sampled. Defaults to 6. |  | Optional: \{\} <br /> |
| `baselineOutlierK` _float_ | BaselineOutlierK is the Hampel-identifier threshold: a sample is rejected<br />when it lies more than k·1.4826·MAD from the window median, so a lower<br />value rejects more. Defaults to 3.0. |  | Optional: \{\} <br /> |
| `iopsWeight` _float_ | IOPSWeight weights per-volume IOPS in the volume I/O score. Defaults to<br />1.0. |  | Optional: \{\} <br /> |
| `throughputWeight` _float_ | ThroughputWeight weights per-volume throughput, in MB/s, in the volume<br />I/O score. Defaults to 0.1. |  | Optional: \{\} <br /> |


#### VolumeDefaults



VolumeDefaults are the defaults every volume in the pool is created with. They
are what a StorageClass assigned to this pool is expected to carry in its
parameters, which is how they reach the CSI driver, and the whole block is
immutable once set for that reason: StorageClass.parameters is immutable in
the Kubernetes API, so a pool whose defaults changed would have a class the
operator cannot update and a spec that no longer describes it.



_Appears in:_
- [StoragePoolSpec](#storagepoolspec)

_Example:_

```yaml
iops: integer
throughput:
  read: integer
  write: integer
  readWrite: integer
filesystem: string
enableCompression: boolean
enableClientCompression: boolean
enableClientDeduplication: boolean
enableEncryption: boolean
enableReplication: boolean
enableDHCHAP: boolean
priorityClass: string
fabric: string
maxNamespacesPerSubsystem: integer
tune2fsReservedBlocks: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `iops` _integer_ | IOPS is each volume's ceiling on operations per second, both directions<br />together. Zero is unlimited. It is written into the class as max_iops. |  | Minimum: 0 <br />Optional: \{\} <br /> |
| `throughput` _[ThroughputLimits](#throughputlimits)_ | Throughput is each volume's throughput ceiling, in megabytes per second. |  | Optional: \{\} <br /> |
| `filesystem` _string_ | Filesystem is what a volume is formatted with. The values are the kernel's<br />names for filesystems, which is why they are not recased: this group did<br />not invent the words. | xfs | Enum: [ext4 xfs] <br />Optional: \{\} <br /> |
| `enableCompression` _boolean_ | EnableCompression compresses logical volumes. |  | Optional: \{\} <br /> |
| `enableClientCompression` _boolean_ | EnableClientCompression compresses each volume on the node that consumes<br />it (VDO), before a write ever reaches the wire, rather than on the storage<br />node. Distinct from EnableCompression, and independent of<br />EnableClientDeduplication: either, both, or neither may be set. A volume<br />requesting this is pinned to a node whose kernel can run dm-vdo. |  | Optional: \{\} <br /> |
| `enableClientDeduplication` _boolean_ | EnableClientDeduplication deduplicates each volume on the node that<br />consumes it (VDO), independent of EnableClientCompression. It carries a<br />significant fixed RAM cost per volume for VDO's index, so it is meant for<br />the pools where duplicate data is actually expected (VM images, container<br />layers, backup targets) rather than enabled by default. |  | Optional: \{\} <br /> |
| `enableEncryption` _boolean_ | EnableEncryption encrypts logical volumes, using the key store the cluster<br />names in its own spec. |  | Optional: \{\} <br /> |
| `enableReplication` _boolean_ | EnableReplication replicates logical volumes. |  | Optional: \{\} <br /> |
| `enableDHCHAP` _boolean_ | EnableDHCHAP authenticates NVMe-oF connections to this pool's volumes.<br />Authentication is only enforced when AllowedNodes is non-empty, because<br />the generated class gets its node selector from that list and a class's<br />parameters cannot be edited afterward. |  | Optional: \{\} <br /> |
| `priorityClass` _string_ | PriorityClass is the logical-volume priority class the control plane<br />places with. |  | Optional: \{\} <br /> |
| `fabric` _string_ | Fabric is the storage fabric a volume is served over, defaulting to the<br />cluster's. |  | Optional: \{\} <br /> |
| `maxNamespacesPerSubsystem` _integer_ | MaxNamespacesPerSubsystem caps how many namespaces share one NVMe-oF<br />subsystem. |  | Minimum: 1 <br />Optional: \{\} <br /> |
| `tune2fsReservedBlocks` _string_ | Tune2fsReservedBlocks is the reserved-block percentage passed to tune2fs<br />on an ext4 volume. Empty means the filesystem's own default, which is not<br />the same as `0`: the node plugin skips the call entirely when this is<br />empty, and runs `tune2fs -m 0` when it is `0`. |  | Optional: \{\} <br /> |


#### VolumeGroupSnapshotOps



VolumeGroupSnapshotOps is a one-shot operation on a VolumeGroupSnapshot,
analogous to a Kubernetes Job: it drives its action to completion, records
the result, and is then inert. The Restore action creates one
PersistentVolumeClaim per member snapshot of the target's generation and
waits for every claim to bind.





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha2
kind: VolumeGroupSnapshotOps
metadata:
  name: string
spec:
  volumeGroupSnapshotRef: string
  action: VolumeGroupSnapshotOpsAction
  restore:
    namePrefix: string
    storageClassName: string
    consistencyGroup: string
    enablePartialRestore: boolean
status:
  phase: VolumeGroupSnapshotOpsPhase
  step:
    state: VolumeGroupSnapshotOpsStep
    deadline: Time
  message: string
  observedGeneration: integer
  membersExpected: integer
  membersBound: integer
  members:
    - volumeSnapshotName: string
      persistentVolumeClaimName: string
      bound: boolean
  startedAt: Time
  completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha2` | | |
| `kind` _string_ | `VolumeGroupSnapshotOps` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  |  |
| `spec` _[VolumeGroupSnapshotOpsSpec](#volumegroupsnapshotopsspec)_ |  |  |  |
| `status` _[VolumeGroupSnapshotOpsStatus](#volumegroupsnapshotopsstatus)_ |  |  |  |


#### VolumeGroupSnapshotOpsAction

_Underlying type:_ _string_

VolumeGroupSnapshotOpsAction is the operation to perform on the target.

_Validation:_
- Enum: [Restore]

_Appears in:_
- [VolumeGroupSnapshotOpsSpec](#volumegroupsnapshotopsspec)

| Field | Description |
| --- | --- |
| `Restore` | VolumeGroupSnapshotOpsActionRestore restores every member of the target's<br />generation into a new PersistentVolumeClaim.<br /> |


#### VolumeGroupSnapshotOpsPhase

_Underlying type:_ _string_

VolumeGroupSnapshotOpsPhase is the lifecycle phase of the operation.

_Validation:_
- Enum: [Pending Running Succeeded Failed]

_Appears in:_
- [VolumeGroupSnapshotOpsStatus](#volumegroupsnapshotopsstatus)

| Field | Description |
| --- | --- |
| `Pending` |  |
| `Running` |  |
| `Succeeded` |  |
| `Failed` |  |


#### VolumeGroupSnapshotOpsSpec



VolumeGroupSnapshotOpsSpec defines the requested operation. The whole spec is
immutable: the object is a request.



_Appears in:_
- [VolumeGroupSnapshotOps](#volumegroupsnapshotops)

_Example:_

```yaml
volumeGroupSnapshotRef: string
action: VolumeGroupSnapshotOpsAction
restore:
  namePrefix: string
  storageClassName: string
  consistencyGroup: string
  enablePartialRestore: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `volumeGroupSnapshotRef` _string_ | VolumeGroupSnapshotRef names the VolumeGroupSnapshot, in this namespace,<br />the operation acts on. Resolved at admission: a create naming a<br />VolumeGroupSnapshot that does not exist is rejected. |  | Required: \{\} <br /> |
| `action` _[VolumeGroupSnapshotOpsAction](#volumegroupsnapshotopsaction)_ | Action is the operation to perform. |  | Enum: [Restore] <br />Required: \{\} <br /> |
| `restore` _[RestoreOpsSpec](#restoreopsspec)_ | Restore carries the parameters of the Restore action. Ignored for any<br />other action. |  | Optional: \{\} <br /> |


#### VolumeGroupSnapshotOpsStatus



VolumeGroupSnapshotOpsStatus holds the observed state of the operation.



_Appears in:_
- [VolumeGroupSnapshotOps](#volumegroupsnapshotops)

_Example:_

```yaml
phase: VolumeGroupSnapshotOpsPhase
step:
  state: VolumeGroupSnapshotOpsStep
  deadline: Time
message: string
observedGeneration: integer
membersExpected: integer
membersBound: integer
members:
  - volumeSnapshotName: string
    persistentVolumeClaimName: string
    bound: boolean
startedAt: Time
completedAt: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _[VolumeGroupSnapshotOpsPhase](#volumegroupsnapshotopsphase)_ | Phase is the high-level lifecycle phase. |  | Enum: [Pending Running Succeeded Failed] <br />Optional: \{\} <br /> |
| `step` _[VolumeGroupSnapshotOpsStepSnapshot](#volumegroupsnapshotopsstepsnapshot)_ | Step is the durable position of the action's state machine. |  | Optional: \{\} <br /> |
| `message` _string_ | Message is the reason the phase is what it is: one sentence, replaced as<br />the phase moves. |  | Optional: \{\} <br /> |
| `observedGeneration` _integer_ | ObservedGeneration is the spec generation this status was computed from. |  | Optional: \{\} <br /> |
| `membersExpected` _integer_ | MembersExpected is the member count of the target generation. |  | Optional: \{\} <br /> |
| `membersBound` _integer_ | MembersBound is how many restored claims have bound. |  | Optional: \{\} <br /> |
| `members` _[RestoredMemberStatus](#restoredmemberstatus) array_ | Members records each member snapshot and its restored claim. |  | Optional: \{\} <br /> |
| `startedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | StartedAt is when the operation began. |  | Optional: \{\} <br /> |
| `completedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | CompletedAt is when the operation finished, successfully or not. |  | Optional: \{\} <br /> |


#### VolumeGroupSnapshotOpsStep

_Underlying type:_ _string_

VolumeGroupSnapshotOpsStep is one step of a running operation. The enum is the
union of every action's steps. Which steps belong to which action is declared
by the action's state-machine graph rather than by this type.

_Validation:_
- Enum: [Validating CreatingClaims WaitingForBind]

_Appears in:_
- [VolumeGroupSnapshotOpsStepSnapshot](#volumegroupsnapshotopsstepsnapshot)

| Field | Description |
| --- | --- |
| `Validating` |  |
| `CreatingClaims` |  |
| `WaitingForBind` |  |


#### VolumeGroupSnapshotOpsStepSnapshot



VolumeGroupSnapshotOpsStepSnapshot is the durable position of the action's
state machine: the step and the deadline it expires at.



_Appears in:_
- [VolumeGroupSnapshotOpsStatus](#volumegroupsnapshotopsstatus)

_Example:_

```yaml
state: VolumeGroupSnapshotOpsStep
deadline: Time
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `state` _[VolumeGroupSnapshotOpsStep](#volumegroupsnapshotopsstep)_ |  |  | Enum: [Validating CreatingClaims WaitingForBind] <br />Optional: \{\} <br /> |
| `deadline` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ |  |  | Optional: \{\} <br /> |


#### VolumeMigrationSettings



VolumeMigrationSettings controls how volume migration and the post-migration
realignment behave, not whether they happen. It is separate from
VolumeAutoPlacementSettings because realignment applies to every volume move,
whether it came from the auto-rebalancer, a manual migration, or a drain, so
it cannot sit under the rebalancing policy that is only one of its three
sources.

There is no switch here. Migration cannot be turned off: a drain, a
rebalance, and a device replacement are all performed by moving volumes.



_Appears in:_
- [StorageClusterSpec](#storageclusterspec)

_Example:_

```yaml
rebalancerImage: string
dataRealignment:
  interval: Duration
  minMoves: integer
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `rebalancerImage` _string_ | RebalancerImage is the container image the migration path-validation Job<br />and the rebalancer's latency and baseline Jobs run. It must carry<br />nvme-cli, and for rebalancing also fio and jq. |  | Optional: \{\} <br /> |
| `dataRealignment` _[DataRealignmentSettings](#datarealignmentsettings)_ | DataRealignment tunes the post-migration realignment. |  | Optional: \{\} <br /> |


