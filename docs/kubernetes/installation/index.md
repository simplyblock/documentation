---
title: "Install"
description: "Install simplyblock on Kubernetes: Helm installs the operator, then custom resources drive the control plane, CSI driver, and storage cluster."
weight: 20000
---

Simplyblock on Kubernetes is installed and managed by the Simplyblock Operator. The operator is installed with a
single Helm chart, and every further step is driven by custom resources of the API group
`storage.simplyblock.io/v1alpha2`: the control plane, the CSI driver, the storage cluster, its storage nodes, and its
storage pools.

For Kubernetes environments, a simplyblock deployment can be either hyper-converged or disaggregated. In the
hyper-converged model, simplyblock storage services run on selected Kubernetes worker nodes, sharing resources with
other workloads in the same Kubernetes cluster. In a disaggregated deployment, storage services run on dedicated
worker nodes either within the same or a different cluster.

## Installation Flow

A typical installation follows these steps:

1. **[Install the operator](k8s-control-plane.md):** `helm install` deploys the operator, all CRDs, and two custom
   resources, `ControlPlane/simplyblock` and `SimplyblockDriver/simplyblock`.
2. **Control plane becomes `Available`:** The operator installs FoundationDB, the object store, and the management
   API from the `ControlPlane` resource. Nothing else is reconciled until the control plane reports the phase
   `Available`.
3. **CSI driver becomes `Ready`:** The operator deploys the CSI node and controller plugins from the
   `SimplyblockDriver` resource.
4. **[Discovery](k8s-storage-plane.md#discover-workers-and-devices):** On a fresh installation, the operator raises the
   `OperatorOps` run `initial-discovery`, which probes the workers and writes a draft `ClusterDeploymentConfig`.
   Additional discovery runs can be requested manually.
5. **[Review and approve](k8s-storage-plane.md#review-the-draft):** The administrator reviews the draft, adjusts
   workers, devices, erasure coding, and failure domains, and sets `spec.approved: true`.
6. **[Expansion](k8s-storage-plane.md#approve-the-deployment):** The operator creates the `StorageCluster`, one
   `StorageNode` per worker and socket, the default `StoragePool` `<cluster>-default`, and the StorageClass
   `simplyblock-<namespace>-<cluster>`.
7. **Activation:** Once all storage nodes are online, the operator activates the cluster, and volumes can be
   provisioned.

For a breakdown of the components the operator installs for the control plane, see
[Control Plane Cluster Architecture](management-cluster-architecture.md). To consume storage from a control plane that
runs elsewhere, see [Connecting to an External Control Plane](install-csi.md).

## Custom Resources

The operator manages the following resources. All of them use the API version `storage.simplyblock.io/v1alpha2`.

| Kind                      | Short name | Category | Description                                                                                                  |
|---------------------------|------------|----------|--------------------------------------------------------------------------------------------------------------|
| `ControlPlane`            | `cp`       | Entity   | The control plane, either installed locally by the operator or managed elsewhere. Created by the Helm chart. |
| `SimplyblockDriver`       | `sbd`      | Entity   | The CSI driver deployment. Created by the Helm chart.                                                        |
| `ClusterDeploymentConfig` | `cdc`      | Entity   | A complete deployment in one document. Once approved, it is expanded into a storage cluster and its nodes.   |
| `StorageCluster`          | `stc`      | Entity   | One simplyblock storage cluster, at most one per namespace. Owns its nodes and pools.                        |
| `StorageNode`             | `sn`       | Entity   | One storage node on a worker and socket. Normally generated from a `ClusterDeploymentConfig`.                |
| `StoragePool`             | `sp`       | Entity   | A tenancy unit with capacity and QoS limits. StorageClasses attach to it by label.                           |
| `StorageBackupPolicy`     | `sbp`      | Entity   | Backup schedule and retention for the claims its selector matches.                                           |
| `StorageDevice`           | `sd`       | Observed | Mirrors one device of a storage node. Never written by users.                                                |
| `StorageBackup`           | `sb`       | Observed | One backup found in the backup store. Never written by users.                                                |
| `OperatorOps`             | `oops`     | Ops      | Discovers workers and devices and writes a draft `ClusterDeploymentConfig`.                                  |
| `ControlPlaneOps`         | `cpops`    | Ops      | Restarts, upgrades, or backs up a local control plane.                                                       |
| `StorageClusterOps`       | `scops`    | Ops      | Activates, expands, shuts down, starts, restarts, or rolling-restarts a cluster, or cancels a task.          |
| `StorageNodeOps`          | `snops`    | Ops      | Shuts down, restarts, suspends, resumes, removes, or migrates a storage node.                                |
| `StorageDeviceOps`        | `sdops`    | Ops      | Restarts a storage device.                                                                                   |
| `PersistentVolumeOps`     | `pvops`    | Ops      | Moves a persistent volume to another storage node. Cluster-scoped.                                           |
| `StorageBackupOps`        | `sbops`    | Ops      | Restores a backup into a new PersistentVolumeClaim.                                                          |
| `VolumeGroupSnapshotOps`  | `vgsops`   | Ops      | Restores every member of a VolumeGroupSnapshot.                                                              |

Every `*Ops` resource shares one shape: an immutable `spec.action`, a mutable `spec.abort`, and a `status.phase` of
`Pending`, `Running`, `Succeeded`, `Failed`, or `Aborted`. Only one operation runs at a time per entity. Further
operations wait in `Pending`.

In addition, the operator serves the read-only metrics API `metrics.simplyblock.io/v1alpha2` through an aggregated API
server. It provides `StorageClusterMetrics` (`scm`), `StorageNodeMetrics` (`snm`), `StoragePoolMetrics` (`spm`),
`StorageDeviceMetrics` (`sdm`), and `LogicalVolumeMetrics` (`lvm`), which report capacity figures for the respective
objects.

For detailed CRD documentation, see [Simplyblock Operator](../../reference/operator/index.md).

## Pages in This Section

- [Control Plane Cluster Architecture](management-cluster-architecture.md): The components of a local control plane.
- [Securing the Control Plane](security.md): TLS, mutual TLS, and an external KMS.
- [Install Simplyblock Operator](k8s-control-plane.md): The Helm installation and its key values.
- [Create a Storage Cluster](k8s-storage-plane.md): Discovery, review, approval, and the first volume.
- [Connecting to an External Control Plane](install-csi.md): The managed profile for clusters without a local control
  plane.
- [OpenShift](openshift.md): Security context constraints and TLS on OpenShift.
- [SUSE Rancher and RKE2](rancher.md): Permissions and CPU topology on RKE2 and K3s clusters.
- [Talos](talos.md): Kernel modules, huge pages, and permissions on Talos.
