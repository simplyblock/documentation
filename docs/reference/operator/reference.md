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
- [storage.simplyblock.io/v1alpha1](#storagesimplyblockiov1alpha1)


## storage.simplyblock.io/v1alpha1

Package v1alpha1 contains API Schema definitions for the simplyblock v1alpha1 API group.

### Resource Types
- [BackupImport](#backupimport)
- [BackupPolicy](#backuppolicy)
- [BackupRestore](#backuprestore)
- [ControlPlane](#controlplane)
- [SnapshotReplication](#snapshotreplication)
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
| `lvolID` _string_ | LvolID is the Simplyblock logical volume UUID that this policy is attached to. |  |  |


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

A BackupPolicy defines retention and scheduling parameters for Simplyblock
backups. To apply a policy to a PVC, annotate the PVC with:

	simplybk/backup-policy: <BackupPolicy-name>

The BackupPolicy must be in the same namespace as the annotated PVC.
The controller attaches and detaches the policy in the Simplyblock backend
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
| `policyID` _string_ | PolicyID is the UUID assigned to this policy by the Simplyblock backend. |  |  |
| `attachedLvols` _[AttachedLvol](#attachedlvol) array_ | AttachedLvols lists the PVCs (and their lvol IDs) currently attached to<br />this policy in the Simplyblock backend. The controller uses this to detect<br />and reconcile annotation additions and removals. |  |  |


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
  sourceSwitchedAt: Time
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
sourceSwitchedAt: Time
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
| `sourceClusterUUID` _string_ | SourceClusterUUID is the UUID of the cluster that originally created the backup.<br />Copied from the referenced StorageBackup's status.sourceClusterUUID.<br />When non-empty, the controller performs source-switch before and after the restore. |  |  |
| `sourceSwitchedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | SourceSwitchedAt records when the target cluster was switched to read from the<br />source cluster's S3 bucket. Cleared once source-switch local completes. |  |  |
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
| `image` _string_ | Image is the container image used for all simplyblock control-plane and<br />storage-node workloads (e.g. quay.io/simplyblock-io/simplyblock:26.2.2).<br />StorageNodeSet CRs that omit spec.clusterImage inherit this value.<br />Must reference one of the trusted registries (quay.io/simplyblock-io, docker.io/simplyblock, public.ecr.aws/simply-block); digest pinning (@sha256:...) is recommended. |  | Pattern: `^($\|(quay\.io/simplyblock-io\|docker\.io/simplyblock\|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]\{64\})?)$` <br />Optional: \{\} <br /> |


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
| `message` _string_ | Message contains a human-readable explanation of the current phase,<br />for example the FDB error returned by the health endpoint. |  |  |
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
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `enabled` _boolean_ | Enabled activates automatic post-migration data realignment for this cluster.<br />Defaults to true. |  | Optional: \{\} <br /> |
| `interval` _[Duration](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#duration-v1-meta)_ | Interval is how often the operator checks whether a realignment is pending<br />(i.e. at least one volume has moved since the last successful realignment) and,<br />if so, triggers it. Explicit triggers (see the<br />simplyblock.io/trigger-realignment annotation) bypass this spacing. Defaults to<br />10m. |  | Optional: \{\} <br /> |


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
| `baseURL` _string_ | BaseURL is the HashiCorp Vault endpoint (e.g. https://vault.example.com:8200). |  | Pattern: `^https?://[a-zA-Z0-9.-]+(:[0-9]\{1,5\})?(/.*)?$` <br /> |


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


#### ReplicationError



ReplicationError stores timestamped error messages



_Appears in:_
- [VolumeReplicationStatus](#volumereplicationstatus)

_Example:_

```yaml
timestamp: Time
message: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `timestamp` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ |  |  |  |
| `message` _string_ |  |  |  |


#### SnapshotReplication



SnapshotReplication is the Schema for the snapshotreplications API





_Example:_

```yaml
apiVersion: storage.simplyblock.io/v1alpha1
kind: SnapshotReplication
metadata:
  name: string
spec:
  sourceCluster: string
  targetCluster: string
  targetPool: string
  sourcePool: string
  timeout: integer
  interval: integer
  action: string
  includeVolumeIDs:
    - string
  excludeVolumeIDs:
    - string
  volumeIDs:
    - string
status:
  configured: boolean
  observedFailbackGeneration: integer
  volumes:
    - volumeID: string
      phase: string
      lastSnapshotID: string
      lastReplicationTime: Time
      replicatedCount: integer
      errors:
        - timestamp: Time
          message: string
  conditions:
    - Condition
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha1` | | |
| `kind` _string_ | `SnapshotReplication` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  | Optional: \{\} <br /> |
| `spec` _[SnapshotReplicationSpec](#snapshotreplicationspec)_ | spec defines the desired state of SnapshotReplication |  | Required: \{\} <br /> |
| `status` _[SnapshotReplicationStatus](#snapshotreplicationstatus)_ | status defines the observed state of SnapshotReplication |  | Optional: \{\} <br /> |


#### SnapshotReplicationSpec



SnapshotReplicationSpec defines the desired state of SnapshotReplication



_Appears in:_
- [SnapshotReplication](#snapshotreplication)

_Example:_

```yaml
sourceCluster: string
targetCluster: string
targetPool: string
sourcePool: string
timeout: integer
interval: integer
action: string
includeVolumeIDs:
  - string
excludeVolumeIDs:
  - string
volumeIDs:
  - string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `sourceCluster` _string_ | Source cluster for the snapshots |  |  |
| `targetCluster` _string_ | Target cluster for replication |  |  |
| `targetPool` _string_ | Target cluster pool for replication |  |  |
| `sourcePool` _string_ | required for failback to a fresh source cluster |  |  |
| `timeout` _integer_ | snapshot replication timeout |  |  |
| `interval` _integer_ | snapshot replication interval in seconds (default: 300sec) |  |  |
| `action` _string_ |  |  | Enum: [failback] <br /> |
| `includeVolumeIDs` _string array_ | Optional: only these volumes are included in failback.<br />If empty, all volumes are candidates unless excluded below. |  |  |
| `excludeVolumeIDs` _string array_ | Optional: volumes to exclude from failback. |  |  |
| `volumeIDs` _string array_ | Optional: list of volumes to replicate. Empty means all volumes |  |  |


#### SnapshotReplicationStatus



SnapshotReplicationStatus defines the observed state of SnapshotReplication.



_Appears in:_
- [SnapshotReplication](#snapshotreplication)

_Example:_

```yaml
configured: boolean
observedFailbackGeneration: integer
volumes:
  - volumeID: string
    phase: string
    lastSnapshotID: string
    lastReplicationTime: Time
    replicatedCount: integer
    errors:
      - timestamp: Time
        message: string
conditions:
  - Condition
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `configured` _boolean_ |  |  |  |
| `observedFailbackGeneration` _integer_ | The metadata.generation value for which failback was last processed. |  |  |
| `volumes` _[VolumeReplicationStatus](#volumereplicationstatus) array_ | Per-volume replication status |  |  |
| `conditions` _[Condition](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#condition-v1-meta) array_ | Conditions provides human-readable status conditions for kubectl get output. |  |  |


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
| `pvcRef` _[PersistentVolumeClaimRef](#persistentvolumeclaimref)_ | PVCRef identifies the PVC whose backing Simplyblock volume should be snapshotted and backed up.<br />Not required when SourceClusterUUID is set (imported backup). |  | Optional: \{\} <br /> |
| `snapshotName` _string_ | SnapshotName optionally overrides the internally-created snapshot name. |  | Optional: \{\} <br /> |
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
| `poolName` _string_ | PoolName is the Simplyblock pool name derived from the CSI volume handle. |  |  |
| `poolUUID` _string_ | PoolUUID is the backend pool UUID. |  |  |
| `lvolID` _string_ | LvolID is the Simplyblock volume UUID. |  |  |
| `lvolName` _string_ | LvolName is the backend logical volume name. |  |  |
| `fsType` _string_ | FSType is the filesystem type of the source PersistentVolume (e.g. "ext4",<br />"xfs"), captured at backup time so a restore can preserve it regardless of<br />which StorageClass the restored PVC ends up using. |  |  |
| `snapshotID` _string_ | SnapshotID is the internally-created snapshot UUID used for the backup request. |  |  |
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
compression: string
encryption: boolean
replicate: boolean
lvolPriorityClass: string
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
| `compression` _string_ | Compression enables compression for logical volumes. | False |  |
| `encryption` _boolean_ | Encryption enables encryption for logical volumes. | false |  |
| `replicate` _boolean_ | Replicate enables replication for logical volumes. | false |  |
| `lvolPriorityClass` _string_ | LvolPriorityClass sets the logical volume priority class. | 0 |  |
| `fabric` _string_ | Fabric is the transport fabric (e.g. tcp). | tcp |  |
| `maxNamespacePerSubsys` _string_ | MaxNamespacePerSubsys limits namespaces per NVMf subsystem. | 1 |  |
| `tune2fsReservedBlocks` _string_ | Tune2fsReservedBlocks sets the ext4 reserved-blocks percentage. Left unset, the node<br />plugin skips tune2fs entirely and mkfs.ext4's own default reserve applies, matching a<br />StorageClass that omits tune2fs_reserved_blocks. A default of "0" here would not be a<br />no-op: it actively runs `tune2fs -m 0` on every volume, since the node plugin only skips<br />the call when the parameter is empty (see stageVolume in the CSI driver), not when it's<br />"0". |  |  |
| `filesystem` _string_ | Filesystem is the filesystem used to format logical volumes of this pool. | ext4 | Enum: [ext4 xfs] <br /> |


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
  haType: string
  isSingleNode: boolean
  strictNodeAntiAffinity: boolean
  qpairCount: integer
  blockSize: integer
  pageSizeInBlocks: integer
  maxQueueSize: integer
  inflightIOThreshold: integer
  fabricType: string
  clientDataIfname: string
  maxFaultTolerance: integer
  nvmfBasePort: integer
  rpcBasePort: integer
  snodeApiPort: integer
  warningThreshold:
    capacity: integer
    provisionedCapacity: integer
  criticalThreshold:
    capacity: integer
    provisionedCapacity: integer
  clientQpairCount: integer
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
    iopsWeight: float
    throughputWeight: float
  enableFailureDomains: boolean
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
  pendingDataRealignment: boolean
  lastDataRealignmentAt: Time
  erasureCodingScheme: string
  lastUpdated: Time
  created: Time
  configured: boolean
  maxFaultTolerance: integer
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
haType: string
isSingleNode: boolean
strictNodeAntiAffinity: boolean
qpairCount: integer
blockSize: integer
pageSizeInBlocks: integer
maxQueueSize: integer
inflightIOThreshold: integer
fabricType: string
clientDataIfname: string
maxFaultTolerance: integer
nvmfBasePort: integer
rpcBasePort: integer
snodeApiPort: integer
warningThreshold:
  capacity: integer
  provisionedCapacity: integer
criticalThreshold:
  capacity: integer
  provisionedCapacity: integer
clientQpairCount: integer
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
  iopsWeight: float
  throughputWeight: float
enableFailureDomains: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `enableNodeAffinity` _boolean_ | EnableNodeAffinity enables node-affinity placement for storage components. |  |  |
| `stripe` _[StripeSpec](#stripespec)_ | StripeSpec configures erasure-coding data/parity chunk counts. |  |  |
| `haType` _string_ | HAType defines the backend high-availability mode. |  |  |
| `isSingleNode` _boolean_ | IsSingleNode enables single-node cluster mode. |  |  |
| `strictNodeAntiAffinity` _boolean_ | StrictNodeAntiAffinity enforces strict anti-affinity between storage nodes. |  |  |
| `qpairCount` _integer_ | QpairCount defines the NVMe queue-pair count used by the cluster. |  |  |
| `blockSize` _integer_ | BlockSize defines the logical block size in bytes. |  |  |
| `pageSizeInBlocks` _integer_ | PageSizeInBlocks defines page size expressed in blocks. |  |  |
| `maxQueueSize` _integer_ | MaxQueueSize defines the maximum backend queue size. |  |  |
| `inflightIOThreshold` _integer_ | InflightIOThreshold defines the inflight I/O threshold. |  |  |
| `fabricType` _string_ | FabricType defines the storage fabric type. |  |  |
| `clientDataIfname` _string_ | ClientDataIfname defines the client data network interface. |  |  |
| `maxFaultTolerance` _integer_ | MaxFaultTolerance defines the maximum tolerated concurrent faults. |  |  |
| `nvmfBasePort` _integer_ | NvmfBasePort defines the base NVMf service port. |  |  |
| `rpcBasePort` _integer_ | RpcBasePort defines the base RPC service port. |  |  |
| `snodeApiPort` _integer_ | SnodeApiPort defines the storage-node API port. |  |  |
| `warningThreshold` _[CapacityThresholdSpec](#capacitythresholdspec)_ | WarningThresholdSpec defines warning-level capacity thresholds. |  |  |
| `criticalThreshold` _[CapacityThresholdSpec](#capacitythresholdspec)_ | CriticalThresholdSpec defines critical-level capacity thresholds. |  |  |
| `clientQpairCount` _integer_ | ClientQpairCount defines client-side queue-pair count. |  |  |
| `backup` _[BackupSpec](#backupspec)_ | Backup specifies the specification for backup to S3 configuration |  |  |
| `hashicorpVaultSettings` _[HashicorpVaultSettings](#hashicorpvaultsettings)_ | HashicorpVaultSettings configures the Vault endpoint used by the cluster for key storage. |  |  |
| `volumeMigrationSettings` _[VolumeMigrationSettings](#volumemigrationsettings)_ | VolumeMigrationSettings controls volume migration for this cluster. |  | Optional: \{\} <br /> |
| `volumeAutoPlacement` _[VolumeAutoPlacementSettings](#volumeautoplacementsettings)_ | VolumeAutoPlacement configures automatic, latency-driven volume rebalancing. When<br />nil/disabled the operator performs only manually-triggered VolumeMigrations. |  | Optional: \{\} <br /> |
| `enableFailureDomains` _boolean_ | EnableFailureDomains opts the cluster into failure-domain mode. When enabled, every<br />storage node must declare a failure-domain group so the control plane can spread<br />erasure-coding chunks across independent fault groups. Immutable once set — failure-<br />domain mode cannot be toggled on a live cluster. |  | Optional: \{\} <br /> |


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
pendingDataRealignment: boolean
lastDataRealignmentAt: Time
erasureCodingScheme: string
lastUpdated: Time
created: Time
configured: boolean
maxFaultTolerance: integer
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
| `pendingDataRealignment` _boolean_ | PendingDataRealignment indicates that at least one volume has been moved since<br />the last successful control-plane data realignment, so a realignment is due on<br />the next DataRealignment.Interval tick. It is persisted so a pending realignment<br />survives an operator restart, and is cleared once a realignment completes<br />successfully. |  | Optional: \{\} <br /> |
| `lastDataRealignmentAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | LastDataRealignmentAt is the time of the last successful control-plane data<br />realignment. It is used to space realignments by DataRealignment.Interval and to<br />avoid re-running at the end of an interval when nothing is pending. |  | Optional: \{\} <br /> |
| `erasureCodingScheme` _string_ | ErasureCodingScheme is the active erasure-coding layout, for example "2x1". |  |  |
| `lastUpdated` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | LastUpdated is the last backend update timestamp.<br />FIXME: Unused for now (API update required?) |  |  |
| `created` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | Created is the backend creation timestamp.<br />FIXME: Unused for now (API update required?) |  |  |
| `configured` _boolean_ | Configured indicates whether initial cluster setup completed. |  |  |
| `maxFaultTolerance` _integer_ | MaxFaultTolerance is the backend-reported maximum number of nodes that can<br />be simultaneously offline (failed, drained, or restarted) without violating<br />the cluster's redundancy guarantees. |  |  |
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
    maxSubsystemCount: integer
    maxSize: string
    spdkImage: string
    spdkProxyImage: string
    corePercentage: integer
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
maxSubsystemCount: integer
maxSize: string
spdkImage: string
spdkProxyImage: string
corePercentage: integer
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
enableCpuTopology: boolean
reservedSystemCPU: string
ubuntuHost: boolean
skipKubeletConfiguration: boolean
failureDomain: integer
expand: boolean
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `maxSubsystemCount` _integer_ | MaxSubsystemCount overrides the maximum number of NVMe-oF subsystems for this node. |  | Optional: \{\} <br /> |
| `maxSize` _string_ | MaxSize overrides the maximum allocatable size of huge pages for this node. |  | Optional: \{\} <br /> |
| `spdkImage` _string_ | SpdkImage overrides the SPDK image for this node (e.g. for phased rollouts). |  | Optional: \{\} <br /> |
| `spdkProxyImage` _string_ | SpdkProxyImage overrides the SPDK proxy image for this node. |  | Optional: \{\} <br /> |
| `corePercentage` _integer_ | CorePercentage overrides the percentage of cores allocated to SPDK for this node (0-99). |  | Optional: \{\} <br /> |
| `spdkSystemMemory` _string_ | SpdkSystemMemory overrides the SPDK huge-page memory allocation for this node<br />(e.g. "4G", "512M"). |  | Pattern: `^[0-9]+(G\|GI\|GB\|GiB\|M\|MI\|MB\|MiB\|g\|gi\|gb\|gib\|m\|mi\|mb\|mib)?$` <br />Optional: \{\} <br /> |
| `journalManager` _[JournalManagerSpec](#journalmanagerspec)_ | JournalManagerSpec overrides journal manager tuning for this node. |  | Optional: \{\} <br /> |
| `pcieAllowList` _string array_ | PcieAllowList overrides the list of PCI addresses allowed for use on this node. |  | Optional: \{\} <br /> |
| `pcieDenyList` _string array_ | PcieDenyList overrides the list of PCI addresses excluded from use on this node. |  | Optional: \{\} <br /> |
| `pcieModel` _string_ | PcieModel overrides the PCI model filter for this node. |  | Optional: \{\} <br /> |
| `driveSizeRange` _string_ | DriveSizeRange overrides the drive size range filter for this node. |  | Optional: \{\} <br /> |
| `deviceNames` _string array_ | DeviceNames explicitly defines the NVMe namespace names to use on this node<br />(e.g. ["nvme0n1","nvme1n1"]). |  | Optional: \{\} <br /> |
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
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `cpu` _integer_ | CPU is the number of SPDK CPU cores allocated to this node. |  | Optional: \{\} <br /> |
| `memory` _string_ | Memory is the SPDK memory allocation reported by the backend. |  | Optional: \{\} <br /> |
| `volumes` _integer_ | Volumes is the current number of logical volumes on this node. |  | Optional: \{\} <br /> |
| `devices` _string_ | Devices is the device summary (online/total) reported by the backend. |  | Optional: \{\} <br /> |


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
  maxSubsystemCount: integer
  maxSize: string
  spdkImage: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
  spdkProxyImage: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
  mgmtIfname: string
  partitions: integer
  journalManager:
    count: integer
    percentPerDevice: integer
  corePercentage: integer
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
      maxSubsystemCount: integer
      maxSize: string
      spdkImage: string
      spdkProxyImage: string
      corePercentage: integer
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
maxSubsystemCount: integer
maxSize: string
spdkImage: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
spdkProxyImage: '^($|(quay\.io/simplyblock-io|docker\.io/simplyblock|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]{64})?)$'
mgmtIfname: string
partitions: integer
journalManager:
  count: integer
  percentPerDevice: integer
corePercentage: integer
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
    maxSubsystemCount: integer
    maxSize: string
    spdkImage: string
    spdkProxyImage: string
    corePercentage: integer
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
| `maxSubsystemCount` _integer_ | MaxSubsystemCount is the maximum number of NVMe-oF subsystems per node. |  |  |
| `maxSize` _string_ | MaxSize is the maximum allocatable size of huge pages. |  |  |
| `spdkImage` _string_ | SpdkImage is the SPDK image reference used by node services.<br />Must reference one of the trusted registries (quay.io/simplyblock-io, docker.io/simplyblock, public.ecr.aws/simply-block); digest pinning (@sha256:...) is recommended. |  | Pattern: `^($\|(quay\.io/simplyblock-io\|docker\.io/simplyblock\|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]\{64\})?)$` <br /> |
| `spdkProxyImage` _string_ | SpdkProxyImage is the SPDK proxy image reference used by node services.<br />Must reference one of the trusted registries (quay.io/simplyblock-io, docker.io/simplyblock, public.ecr.aws/simply-block); digest pinning (@sha256:...) is recommended. |  | Pattern: `^($\|(quay\.io/simplyblock-io\|docker\.io/simplyblock\|public\.ecr\.aws/simply-block)/[a-z0-9][a-z0-9._-]*:[a-zA-Z0-9][a-zA-Z0-9._-]*(@sha256:[a-f0-9]\{64\})?)$` <br /> |
| `mgmtIfname` _string_ | MgmtIfname is the management interface name used by storage nodes. |  |  |
| `partitions` _integer_ | Partitions is the number of partitions created per backend storage device. |  |  |
| `journalManager` _[JournalManagerSpec](#journalmanagerspec)_ | JournalManagerSpec configures journal manager behavior. |  |  |
| `corePercentage` _integer_ | CorePercentage is the percentage of cores to be used for spdk (0-99). |  |  |
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
  maxSubsystemCount: integer
  maxSize: string
  spdkImage: string
  spdkProxyImage: string
  corePercentage: integer
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
    compression: string
    encryption: boolean
    replicate: boolean
    lvolPriorityClass: string
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
  compression: string
  encryption: boolean
  replicate: boolean
  lvolPriorityClass: string
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
    compression: string
    encryption: boolean
    replicate: boolean
    lvolPriorityClass: string
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
  compression: string
  encryption: boolean
  replicate: boolean
  lvolPriorityClass: string
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


#### VolumeAutoPlacementSettings



VolumeAutoPlacementSettings controls the automatic, latency-driven volume rebalancing
behaviour. It is configured under StorageClusterSpec.VolumeAutoPlacement.



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
iopsWeight: float
throughputWeight: float
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `enabled` _boolean_ | Enabled activates automatic rebalancing for this cluster. Defaults to false. |  | Optional: \{\} <br /> |
| `migrationEnabled` _boolean_ | MigrationEnabled controls whether the rebalancer actually creates VolumeMigration<br />CRs. When false the rebalancer still runs every cycle — evaluating load, computing<br />deviations, selecting candidates and emitting metrics — but discards the migrations<br />instead of creating them (dry-run). Defaults to true. |  | Optional: \{\} <br /> |
| `evaluationInterval` _[Duration](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#duration-v1-meta)_ | EvaluationInterval is how often the rebalancer evaluates load. Defaults to 60s. |  | Optional: \{\} <br /> |
| `imbalanceThreshold` _integer_ | ImbalanceThreshold is the minimum latency deviation from baseline (in percent)<br />that a node must exhibit before it is considered a rebalancing source. Defaults to 80. |  | Optional: \{\} <br /> |
| `minHotColdDifferencePct` _integer_ | MinHotColdDifferencePct is the minimum latency-deviation gap (in percentage points)<br />that a candidate target node must be below the hot source node before a migration is<br />performed. Prevents migrating between near-equally-loaded nodes. Defaults to 20. |  | Optional: \{\} <br /> |
| `defaultCoolDownSeconds` _integer_ | DefaultCoolDownSeconds is the cool-down period (seconds) applied to a volume after<br />it has been migrated. Defaults to 600. |  | Optional: \{\} <br /> |
| `maxVolumeMigrationsPerCycle` _integer_ | MaxVolumeMigrationsPerCycle is the maximum number of volumes moved per cycle. Defaults to 10. |  | Optional: \{\} <br /> |
| `storageNodeCandidateCount` _integer_ | StorageNodeCandidateCount is the number of top-loaded nodes evaluated each cycle to<br />find the best migration source. Defaults to 3. |  | Optional: \{\} <br /> |
| `metricsBackend` _[MetricsBackend](#metricsbackend)_ | MetricsBackend selects the data source for I/O metrics. Defaults to "prometheus". |  | Enum: [controlplane prometheus uniform] <br />Optional: \{\} <br /> |
| `prometheusURL` _string_ | PrometheusURL is required when MetricsBackend is "prometheus". |  | Optional: \{\} <br /> |
| `latencyBenchmarkEnabled` _boolean_ | LatencyBenchmarkEnabled enables fio-based NVMe-oF latency measurement via Kubernetes Jobs.<br />Defaults to false; set to true once a RebalancerImage is configured. |  | Optional: \{\} <br /> |
| `latencyBenchmarkInterval` _[Duration](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#duration-v1-meta)_ | LatencyBenchmarkInterval is how often fio benchmark Jobs run against each storage node.<br />Defaults to 5m. |  | Optional: \{\} <br /> |
| `iopsWeight` _float_ | IOPSWeight is the weight applied to per-volume IOPS in the volume IO score. Defaults to 1.0. |  | Optional: \{\} <br /> |
| `throughputWeight` _float_ | ThroughputWeight is the weight applied to per-volume throughput (MB/s) in the volume<br />IO score. Defaults to 0.1. |  | Optional: \{\} <br /> |


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
  sourceNodeUUID: string
  snapsTotal: integer
  snapsMigrated: integer
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
  validationJobName: string
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
sourceNodeUUID: string
snapsTotal: integer
snapsMigrated: integer
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
validationJobName: string
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
| `sourceNodeUUID` _string_ | SourceNodeUUID is the storage node UUID where the volume resided before<br />migration, as reported by the storage API. |  |  |
| `snapsTotal` _integer_ | SnapsTotal is the total number of snapshots to migrate, as reported by the API. |  |  |
| `snapsMigrated` _integer_ | SnapsMigrated is the number of snapshots migrated so far. |  |  |
| `errorMessage` _string_ | ErrorMessage holds the failure reason when Phase is Failed. |  |  |
| `connections` _[MigrationConnection](#migrationconnection) array_ | Connections holds the NVMe-oF connection parameters for the new target-side<br />paths returned by CreateMigration. Used during the Validating phase to<br />establish and verify the paths before calling ContinueMigration. |  |  |
| `validationJobName` _string_ | ValidationJobName is the name of the Job that runs `nvme connect` for each<br />connection path and validates ANA state before ContinueMigration is called.<br />Set during the Validating phase; cleared when the phase advances to Running. |  |  |
| `startedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | StartedAt is the time the migration was submitted to the storage API. |  |  |
| `completedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | CompletedAt is the time the migration finished (successfully or not). |  |  |


#### VolumeReplicationStatus



VolumeReplicationStatus tracks the replication state of an individual volume



_Appears in:_
- [SnapshotReplicationStatus](#snapshotreplicationstatus)

_Example:_

```yaml
volumeID: string
phase: string
lastSnapshotID: string
lastReplicationTime: Time
replicatedCount: integer
errors:
  - timestamp: Time
    message: string
```

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `volumeID` _string_ | Volume ID |  |  |
| `phase` _string_ | Phase is the current replication phase for this volume. |  | Enum: [Pending Running TriggeringTargetReplication WaitingForTargetReplication ReplicatingToSource WaitingForTargetDeletion Completed Failed Paused] <br /> |
| `lastSnapshotID` _string_ | Last snapshot ID replicated for this volume |  |  |
| `lastReplicationTime` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | Timestamp of the last successful replication for this volume |  |  |
| `replicatedCount` _integer_ | Number of snapshots successfully replicated |  |  |
| `errors` _[ReplicationError](#replicationerror) array_ | Optional: list of errors encountered for this volume |  |  |


