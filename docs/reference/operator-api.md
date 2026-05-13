---
title: "Simplyblock Operator API Reference"
description: "Generated API reference for Simplyblock operator Custom Resource Definitions (CRDs)."
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
- [Pool](#pool)
- [SnapshotReplication](#snapshotreplication)
- [StorageBackup](#storagebackup)
- [StorageCluster](#storagecluster)
- [StorageNode](#storagenode)
- [Task](#task)



#### ActionStatus







_Appears in:_
- [StorageClusterStatus](#storageclusterstatus)
- [StorageNodeStatus](#storagenodestatus)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `action` _string_ | Action is the requested action name. |  |  |
| `nodeUUID` _string_ | NodeUUID is the target node UUID for the action. |  |  |
| `state` _string_ |  |  |  |
| `message` _string_ | Message is a human-readable action result or error. |  |  |
| `updatedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | UpdatedAt is the timestamp of the last status transition. |  |  |
| `observedGeneration` _integer_ | ObservedGeneration is the resource generation observed by this status. |  |  |
| `triggered` _boolean_ | Triggered indicates whether the underlying backend action has been fired. |  |  |


#### AttachedLvol



AttachedLvol records a single PVC-to-lvol attachment managed by this policy.



_Appears in:_
- [BackupPolicyStatus](#backuppolicystatus)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `pvcName` _string_ | PVCName is the name of the PVC. |  |  |
| `pvcNamespace` _string_ | PVCNamespace is the namespace of the PVC. |  |  |
| `lvolID` _string_ | LvolID is the Simplyblock logical volume UUID that this policy is attached to. |  |  |


#### BackupCredentialsSecretRef







_Appears in:_
- [BackupSpec](#backupspec)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `name` _string_ | Name is the name of the Secret in the same namespace as the cluster CR. |  |  |


#### BackupImport



BackupImport imports a completed backup from a source cluster into a target cluster,
creating a StorageBackup CR that can be referenced by a BackupRestore.





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

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `sourceClusterName` _string_ | SourceClusterName is the StorageCluster CR name of the cluster that owns the backup. |  |  |
| `sourceBackupID` _string_ | SourceBackupID is the UUID of the backup on the source cluster to import. |  |  |
| `targetClusterName` _string_ | TargetClusterName is the StorageCluster CR name of the cluster to import into. |  |  |


#### BackupImportStatus



BackupImportStatus defines the observed state of BackupImport.



_Appears in:_
- [BackupImport](#backupimport)

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

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `clusterName` _string_ | ClusterName is the target storage cluster name. |  |  |
| `maxVersions` _integer_ | MaxVersions is the maximum number of completed backup versions to retain.<br />When exceeded, the oldest backup is merged into the second-oldest. |  | Optional: \{\} <br /> |
| `maxAge` _string_ | MaxAge is the maximum age of backups to retain (e.g. "7d", "12h", "30m").<br />Backups older than this are merged. Accepts m, h, d, w suffixes. |  | Optional: \{\} <br /> |
| `schedule` _string_ | Schedule defines the tiered backup schedule as a space-separated list of<br />interval,keep_count pairs (e.g. "15m,4 60m,11 24h,7").<br />Intervals must be strictly increasing. Supported units: m, h, d, w. |  | Optional: \{\} <br /> |


#### BackupPolicyStatus



BackupPolicyStatus defines the observed state of BackupPolicy.



_Appears in:_
- [BackupPolicy](#backuppolicy)

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

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `name` _string_ | Name is the StorageBackup resource name. |  |  |


#### BackupRestore



BackupRestore is the Schema for the backuprestores API.





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

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _string_ | Phase is the high-level lifecycle shown in kubectl output. |  |  |
| `message` _string_ | Message contains the latest reconciliation detail or error. |  |  |
| `clusterUUID` _string_ | ClusterUUID is the backend cluster UUID. |  |  |
| `backupID` _string_ | BackupID is the backend backup UUID being restored. |  |  |
| `sourceLvolID` _string_ | SourceLvolID is the original logical volume UUID that was backed up. |  |  |
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

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `localEndpoint` _string_ |  |  |  |
| `snapshotBackups` _boolean_ |  |  | Optional: \{\} <br /> |
| `withCompression` _boolean_ |  |  | Optional: \{\} <br /> |
| `secondaryTarget` _integer_ |  |  | Optional: \{\} <br /> |
| `localTesting` _boolean_ |  |  | Optional: \{\} <br /> |
| `credentialsSecretRef` _[BackupCredentialsSecretRef](#backupcredentialssecretref)_ | CredentialsSecretRef points to the Secret holding access_key_id and secret_access_key. |  |  |


#### CapacityThresholdSpec







_Appears in:_
- [StorageClusterSpec](#storageclusterspec)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `capacity` _integer_ | Capacity defines the absolute capacity threshold value. |  |  |
| `provisionedCapacity` _integer_ | ProvisionedCapacity defines the provisioned-capacity threshold value. |  |  |


#### ControlPlane



ControlPlane is a singleton resource (one per namespace, named "simplyblock")
that reflects the readiness of the simplyblock control plane. It is created
automatically by the Helm chart and should not be created or deleted manually.





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

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `image` _string_ | Image is the container image used for all simplyblock control-plane and<br />storage-node workloads (e.g. quay.io/simplyblock-io/simplyblock:26.2.2).<br />StorageNode CRs that omit spec.clusterImage inherit this value. |  | Optional: \{\} <br /> |


#### ControlPlaneStatus



ControlPlaneStatus reflects the observed readiness of the simplyblock
control plane (FDB + management API).



_Appears in:_
- [ControlPlane](#controlplane)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `phase` _string_ | Phase is Initializing while the control plane is not yet healthy,<br />and Ready once the FDB health check passes. |  | Enum: [Initializing Ready] <br /> |
| `message` _string_ | Message contains a human-readable explanation of the current phase,<br />for example the FDB error returned by the health endpoint. |  |  |
| `lastChecked` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | LastChecked is the timestamp of the most recent FDB health probe. |  |  |


#### JournalManagerSpec



JournalManagerSpec defines journal manager tuning parameters.



_Appears in:_
- [StorageNodeSpec](#storagenodespec)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `count` _integer_ | Count is the number of journal managers to configure. |  |  |
| `percentPerDevice` _integer_ | PercentPerDevice is the journal manager capacity percentage per device. |  |  |


#### NodeDrainState



NodeDrainState tracks the upgrade-drain coordination state for a single worker node.



_Appears in:_
- [StorageNodeStatus](#storagenodestatus)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `hostname` _string_ | Hostname is the Kubernetes node name. |  |  |
| `phase` _string_ | Phase is the current drain coordination phase. |  | Enum: [detected shutdown_called draining restart_called complete failed] <br /> |
| `startedAt` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | StartedAt is when drain coordination began for this node. |  |  |
| `message` _string_ | Message provides additional status detail or error information. |  |  |
| `activeNodeUUID` _string_ | ActiveNodeUUID is the backend UUID of the storage node currently being shut<br />down or restarted. Used to sequence through multiple NUMA-socket nodes on<br />the same worker one at a time during drain coordination. |  |  |


#### NodeRecycleSpec



NodeRecycleSpec configures the node-recycle action behaviour.



_Appears in:_
- [StorageClusterSpec](#storageclusterspec)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `refreshSNodeAPI` _boolean_ | RefreshSNodeAPI restarts the storage-node DaemonSet pod on each node<br />before shutting it down, ensuring the latest image is running. |  |  |


#### NodeRecycleStatus



NodeRecycleStatus tracks in-progress state for the node-recycle action.
All fields are persisted in CR status so the reconciler can resume after a requeue.



_Appears in:_
- [StorageClusterStatus](#storageclusterstatus)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `pendingNodes` _string array_ | PendingNodes is the ordered list of node UUIDs still to be recycled. |  |  |
| `processedNodes` _string array_ | ProcessedNodes is the list of node UUIDs already recycled. |  |  |
| `nodePhase` _string_ | NodePhase is the current step for the node being recycled:<br />"snode-refresh" \| "snode-refresh-wait" \| "shutting-down" \| "restarting" \| "rebalancing" |  |  |
| `phaseTriggered` _boolean_ | PhaseTriggered indicates the API call for the current NodePhase was already sent. |  |  |


#### NodeStatus







_Appears in:_
- [StorageNodeStatus](#storagenodestatus)

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


#### PVCTemplate



PVCTemplate describes the PVC the controller will create once the restore completes.



_Appears in:_
- [BackupRestoreSpec](#backuprestorespec)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `metadata` _[PVCTemplateMetadata](#pvctemplatemetadata)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  | Optional: \{\} <br /> |
| `spec` _[PersistentVolumeClaimSpec](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#persistentvolumeclaimspec-v1-core)_ | Spec follows core PersistentVolumeClaimSpec.<br />spec.resources.requests.storage must be >= the backup size. |  |  |


#### PVCTemplateMetadata



PVCTemplateMetadata describes the PVC metadata fields the controller honors.



_Appears in:_
- [PVCTemplate](#pvctemplate)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `name` _string_ |  |  | Optional: \{\} <br /> |
| `labels` _object (keys:string, values:string)_ |  |  | Optional: \{\} <br /> |
| `annotations` _object (keys:string, values:string)_ |  |  | Optional: \{\} <br /> |


#### PersistentVolumeClaimRef







_Appears in:_
- [StorageBackupSpec](#storagebackupspec)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `name` _string_ | Name is the PVC name. |  |  |
| `namespace` _string_ | Namespace overrides the backup resource namespace for the PVC lookup. |  |  |


#### Pool



Pool is the Schema for the pools API





| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha1` | | |
| `kind` _string_ | `Pool` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  | Optional: \{\} <br /> |
| `spec` _[PoolSpec](#poolspec)_ | spec defines the desired state of Pool |  | Required: \{\} <br /> |
| `status` _[PoolStatus](#poolstatus)_ | status defines the observed state of Pool |  | Optional: \{\} <br /> |


#### PoolQoSSpec



PoolQoSSpec defines pool QosSpec limits.



_Appears in:_
- [PoolSpec](#poolspec)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `iops` _integer_ | IOPS is the IOPS limit for the pool. |  |  |
| `throughput` _[PoolQoSThroughputSpec](#poolqosthroughputspec)_ | Throughput contains throughput limits for the pool. |  |  |


#### PoolQoSStatus



PoolQoSStatus defines observed pool QosSpec values.



_Appears in:_
- [PoolStatus](#poolstatus)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `host` _string_ | Host is the backend host handling pool QosSpec enforcement. |  |  |
| `iops` _integer_ | IOPS is the observed/configured IOPS value. |  |  |
| `throughput` _[PoolQoSThroughputStatus](#poolqosthroughputstatus)_ | Throughput contains observed/configured throughput values. |  |  |


#### PoolQoSThroughputSpec



PoolQoSThroughputSpec defines throughput QosSpec limits in MiB/s.



_Appears in:_
- [PoolQoSSpec](#poolqosspec)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `read` _integer_ | Read is the read throughput limit for the pool. |  |  |
| `readWrite` _integer_ | ReadWrite is the combined read/write throughput limit for the pool. |  |  |
| `write` _integer_ | Write is the write throughput limit for the pool. |  |  |


#### PoolQoSThroughputStatus



PoolQoSThroughputStatus defines observed throughput QosSpec values in MiB/s.



_Appears in:_
- [PoolQoSStatus](#poolqosstatus)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `read` _integer_ | Read is the observed/configured read throughput value. |  |  |
| `readWrite` _integer_ | ReadWrite is the observed/configured combined read/write throughput value. |  |  |
| `write` _integer_ | Write is the observed/configured write throughput value. |  |  |


#### PoolSpec



PoolSpec defines the desired state of Pool



_Appears in:_
- [Pool](#pool)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `clusterName` _string_ | ClusterName is the target storage cluster name. |  |  |
| `status` _string_ | Status is an optional desired-status hint for backend workflows.<br />FIXME: Unused for now |  |  |
| `capacityLimit` _string_ | CapacityLimit is the maximum aggregate capacity that can be allocated from this pool.<br />This maps to sbctl pool add --pool-max. Use sizes like 20M, 20G, or 0 for unlimited. |  |  |
| `logicalVolumeMaxSize` _string_ | LogicalVolumeMaxSize is the maximum size allowed for any single logical volume<br />created in this pool. This maps to sbctl pool add --lvol-max. Use sizes like<br />20M, 20G, or 0 for unlimited. |  |  |
| `dhchap` _boolean_ | DHCHAP enables DH-HMAC-CHAP key generation for the pool. Authentication is only<br />enforced when allowedNodes is non-empty | false |  |
| `allowedNodes` _string array_ | AllowedNodes is the list of Kubernetes worker node names allowed to access volumes<br />in this pool. The operator resolves each node name to a deterministic NQN derived<br />from the node's UID: nqn.2014-08.io.simplyblock:uuid:<node-uid>.<br />The CSI node uses the same formula so no manual NQN management is required. |  |  |
| `qos` _[PoolQoSSpec](#poolqosspec)_ | QosSpec defines QosSpec limits for the pool. |  |  |
| `action` _string_ | Action triggers an imperative pool operation.<br />FIXME: Unused for now |  |  |
| `storageClassParameters` _[StorageClassParameters](#storageclassparameters)_ | StorageClassParameters sets default StorageClass parameter values for volumes in this pool. | \{  \} |  |


#### PoolStatus



PoolStatus defines the observed state of Pool.



_Appears in:_
- [Pool](#pool)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `uuid` _string_ | UUID is the backend pool UUID. |  |  |
| `status` _string_ | Status is the backend lifecycle status. |  |  |
| `qos` _[PoolQoSStatus](#poolqosstatus)_ | QoS contains observed/configured QoS values. |  |  |
| `allowedNodes` _string array_ | AllowedNodes lists the Kubernetes node names currently registered on the backend. |  |  |


#### ReplicationError



ReplicationError stores timestamped error messages



_Appears in:_
- [VolumeReplicationStatus](#volumereplicationstatus)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `timestamp` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ |  |  |  |
| `message` _string_ |  |  |  |


#### SnapshotReplication



SnapshotReplication is the Schema for the snapshotreplications API





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

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `configured` _boolean_ |  |  |  |
| `observedFailbackGeneration` _integer_ | The metadata.generation value for which failback was last processed. |  |  |
| `volumes` _[VolumeReplicationStatus](#volumereplicationstatus) array_ | Per-volume replication status |  |  |
| `conditions` _[Condition](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#condition-v1-meta) array_ | Conditions provides human-readable status conditions for kubectl get output. |  |  |


#### StorageBackup



StorageBackup is the Schema for the storagebackups API.





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



_Appears in:_
- [PoolSpec](#poolspec)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `qosRwIops` _string_ | QosRwIops sets the read/write IOPS limit (0 = unlimited). | 0 |  |
| `qosRwMbytes` _string_ | QosRwMbytes sets the read/write throughput limit in MB/s (0 = unlimited). | 0 |  |
| `qosRMbytes` _string_ | QosRMbytes sets the read throughput limit in MB/s (0 = unlimited). | 0 |  |
| `qosWMbytes` _string_ | QosWMbytes sets the write throughput limit in MB/s (0 = unlimited). | 0 |  |
| `compression` _string_ | Compression enables compression for logical volumes. | False |  |
| `encryption` _boolean_ | Encryption enables encryption for logical volumes. | false |  |
| `replicate` _boolean_ | Replicate enables replication for logical volumes. | false |  |
| `numDataChunks` _string_ | NumDataChunks is the number of data chunks (distr_ndcs). | 1 |  |
| `numParityChunks` _string_ | NumParityChunks is the number of parity chunks (distr_npcs). | 1 |  |
| `lvolPriorityClass` _string_ | LvolPriorityClass sets the logical volume priority class. | 0 |  |
| `fabric` _string_ | Fabric is the transport fabric (e.g. tcp). | tcp |  |
| `maxNamespacePerSubsys` _string_ | MaxNamespacePerSubsys limits namespaces per NVMf subsystem. | 1 |  |
| `tune2fsReservedBlocks` _string_ | Tune2fsReservedBlocks sets the ext4 reserved-blocks percentage. | 0 |  |


#### StorageCluster



StorageCluster is the Schema for the storageclusters API





| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha1` | | |
| `kind` _string_ | `StorageCluster` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  | Optional: \{\} <br /> |
| `spec` _[StorageClusterSpec](#storageclusterspec)_ | spec defines the desired state of StorageCluster |  | Required: \{\} <br /> |
| `status` _[StorageClusterStatus](#storageclusterstatus)_ | status defines the observed state of StorageCluster |  | Optional: \{\} <br /> |


#### StorageClusterSpec



StorageClusterSpec defines the desired state of StorageCluster



_Appears in:_
- [StorageCluster](#storagecluster)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `enableNodeAffinity` _boolean_ | EnableNodeAffinity enables node-affinity placement for storage components. |  |  |
| `stripe` _[StripeSpec](#stripespec)_ | StripeSpec configures erasure-coding data/parity chunk counts. |  |  |
| `haType` _string_ | HAType defines the backend high-availability mode. |  |  |
| `action` _string_ | Action triggers a cluster-level action. |  | Enum: [activate expand shutdown start restart node-recycle] <br /> |
| `nodeRecycle` _[NodeRecycleSpec](#noderecyclespec)_ | NodeRecycle configures the node-recycle action. |  |  |
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


#### StorageClusterStatus



StorageClusterStatus defines the observed state of StorageCluster.



_Appears in:_
- [StorageCluster](#storagecluster)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `uuid` _string_ | UUID is the backend cluster UUID. |  |  |
| `clusterName` _string_ | ClusterName is the resolved backend cluster name. |  |  |
| `mgmtNodes` _integer_ | MgmtNodes is the number of management nodes.<br />FIXME: Unused for now (API update required?) |  |  |
| `storageNodes` _integer_ | StorageNodes is the number of storage nodes.<br />FIXME: Unused for now (API update required?) |  |  |
| `nqn` _string_ | NQN is the cluster NVM subsystem qualified name. |  |  |
| `status` _string_ | Status is the backend-reported lifecycle status. |  |  |
| `rebalancing` _boolean_ | Rebalancing indicates whether cluster rebalancing is currently active. |  |  |
| `erasureCodingScheme` _string_ | ErasureCodingScheme is the active erasure-coding layout, for example "2x1". |  |  |
| `secretName` _string_ | SecretName is the Kubernetes Secret containing cluster credentials. |  |  |
| `lastUpdated` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | LastUpdated is the last backend update timestamp.<br />FIXME: Unused for now (API update required?) |  |  |
| `created` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | Created is the backend creation timestamp.<br />FIXME: Unused for now (API update required?) |  |  |
| `configured` _boolean_ | Configured indicates whether initial cluster setup completed. |  |  |
| `actionStatus` _[ActionStatus](#actionstatus)_ | ActionStatus tracks the most recent action execution state. |  |  |
| `nodeRecycleStatus` _[NodeRecycleStatus](#noderecyclestatus)_ | NodeRecycleStatus tracks in-progress state for the node-recycle action. |  |  |


#### StorageNode



StorageNode is the Schema for the storagenodes API





| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `apiVersion` _string_ | `storage.simplyblock.io/v1alpha1` | | |
| `kind` _string_ | `StorageNode` | | |
| `metadata` _[ObjectMeta](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#objectmeta-v1-meta)_ | Refer to Kubernetes API documentation for fields of `metadata`. |  | Optional: \{\} <br /> |
| `spec` _[StorageNodeSpec](#storagenodespec)_ | spec defines the desired state of StorageNode |  | Required: \{\} <br /> |
| `status` _[StorageNodeStatus](#storagenodestatus)_ | status defines the observed state of StorageNode |  | Optional: \{\} <br /> |


#### StorageNodeSpec



StorageNodeSpec defines the desired state of StorageNode



_Appears in:_
- [StorageNode](#storagenode)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `clusterName` _string_ | ClusterName is the target storage cluster name. |  |  |
| `clusterImage` _string_ | ClusterImage is the container image used for storage-node workloads. |  |  |
| `action` _string_ | Action triggers an imperative node operation. |  | Enum: [shutdown restart suspend resume remove] <br /> |
| `nodeUUID` _string_ | NodeUUID is required when action is specified |  |  |
| `maxLogicalVolumeCount` _integer_ | MaxLogicalVolumeCount is the maximum number of logical volumes per node. |  |  |
| `maxSize` _string_ | MaxSize is the maximum allocatable size of the storage node. |  |  |
| `spdkImage` _string_ | SpdkImage is the SPDK image reference used by node services. |  |  |
| `spdkProxyImage` _string_ | SpdkProxyImage is the SPDK proxy image reference used by node services. |  |  |
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
| `workerNodes` _string array_ | WorkerNodes is the set of Kubernetes worker nodes to manage. |  |  |
| `workerNode` _string_ | WorkerNode is a single worker node used by action flows. |  |  |
| `reattachVolume` _boolean_ | ReattachVolume reattaches volumes during restart where supported by the backend. |  |  |
| `openShiftCluster` _boolean_ | OpenShiftCluster indicates OpenShift-specific behavior should be enabled. |  |  |
| `deviceNames` _string array_ | DeviceNames explicitly defines a comma separated list of nvme namespace names like nvme0n1,nvme1n1... |  |  |
| `ubuntuHost` _boolean_ | UbuntuHost indicates the node host OS is Ubuntu. |  |  |
| `skipKubeletConfiguration` _boolean_ | SkipKubeletConfiguration skips kubelet configuration changes. |  |  |
| `forceFormat4K` _boolean_ | ForceFormat4K forces 4K blocksize formatting of the NVMe device where supported. |  |  |
| `enableCpuTopology` _boolean_ | EnableCpuTopology enables topology-aware CPU handling. |  |  |
| `reservedSystemCPU` _string_ | ReservedSystemCPU defines CPUs reserved for system workloads. |  |  |
| `tolerations` _[Toleration](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#toleration-v1-core) array_ | Tolerations configures pod tolerations for storage-node pods. |  |  |
| `force` _boolean_ | Force enables forced action execution where supported. |  |  |


#### StorageNodeStatus



StorageNodeStatus defines the observed state of StorageNode.



_Appears in:_
- [StorageNode](#storagenode)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `nodes` _[NodeStatus](#nodestatus) array_ | Nodes is the observed state of each managed storage node. |  |  |
| `actionStatus` _[ActionStatus](#actionstatus)_ | ActionStatus tracks the latest action execution status. |  |  |
| `drainCoordination` _[NodeDrainState](#nodedrainstate) array_ | DrainCoordination tracks the upgrade-drain state per worker node. |  |  |


#### StripeSpec







_Appears in:_
- [StorageClusterSpec](#storageclusterspec)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `dataChunks` _integer_ | DataChunks defines the number of data chunks in the erasure-coding layout. |  |  |
| `parityChunks` _integer_ | ParityChunks defines the number of parity chunks in the erasure-coding layout. |  |  |


#### Task



Task is the Schema for the tasks API





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

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `clusterName` _string_ | ClusterName is the target storage cluster name. |  |  |
| `taskID` _string_ | TaskID filters results to a specific backend task when set. |  |  |
| `subtasks` _boolean_ | Subtasks includes related child subtasks when supported by the backend.<br />FIXME: Unused for now |  |  |


#### TaskStatus



TaskStatus defines the observed state of Task.



_Appears in:_
- [Task](#task)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `tasks` _[TaskEntry](#taskentry) array_ | Tasks is the currently reported task list for the query scope. |  |  |


#### VolumeReplicationStatus



VolumeReplicationStatus tracks the replication state of an individual volume



_Appears in:_
- [SnapshotReplicationStatus](#snapshotreplicationstatus)

| Field | Description | Default | Validation |
| --- | --- | --- | --- |
| `volumeID` _string_ | Volume ID |  |  |
| `phase` _string_ | Phase is the current replication phase for this volume. |  | Enum: [Pending Running TriggeringTargetReplication WaitingForTargetReplication ReplicatingToSource WaitingForTargetDeletion Completed Failed Paused] <br /> |
| `lastSnapshotID` _string_ | Last snapshot ID replicated for this volume |  |  |
| `lastReplicationTime` _[Time](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.36/#time-v1-meta)_ | Timestamp of the last successful replication for this volume |  |  |
| `replicatedCount` _integer_ | Number of snapshots successfully replicated |  |  |
| `errors` _[ReplicationError](#replicationerror) array_ | Optional: list of errors encountered for this volume |  |  |


