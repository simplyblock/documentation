---
title: "Kubernetes Storage"
description: "Kubernetes Storage: Simplyblock runs natively on Kubernetes, where it is deployed and managed by the Simplyblock Operator through Custom Resource Definitions."
weight: 10100
---

Simplyblock runs natively on Kubernetes, where it is deployed and managed by the Simplyblock Operator through Custom
Resource Definitions (CRDs) of the API group `storage.simplyblock.io/v1alpha2`. Workloads consume storage through the
simplyblock CSI driver using standard Kubernetes objects such as `StorageClass`, `PersistentVolumeClaim`, and
`VolumeSnapshot`. Provisioning, snapshotting, cloning, and resizing therefore become part of the regular application
lifecycle instead of a separate administrative task.

The installation is driven by custom resources. A single Helm chart installs the operator together with a
`ControlPlane` and a `SimplyblockDriver` resource, and the operator installs the control plane and the CSI driver
from them. The operator then discovers the workers and their devices and writes a draft `ClusterDeploymentConfig`.
Once an administrator reviews and approves that draft, the operator creates the storage cluster, its storage nodes,
a default storage pool, and a matching StorageClass.

Entities such as `StorageCluster`, `StorageNode`, and `StoragePool` describe the desired state. Imperative operations,
for example, a restart, a rolling restart, a node migration, or a restore, are requested with dedicated `*Ops`
resources (`StorageClusterOps`, `StorageNodeOps`, `ControlPlaneOps`, and others) that report their progress in their
own status.

Both **hyper-converged** and **disaggregated** topologies are supported. In a hyper-converged deployment, simplyblock
storage services share Kubernetes worker nodes with application workloads. In a disaggregated deployment, they run on
dedicated workers, either within the same cluster or in a separate one. A wide range of Kubernetes distributions is
supported, including OpenShift, SUSE Rancher (RKE2 and K3s), and Talos.

Before deploying, review the node sizing, network, and erasure coding guidance in
[Deployment Preparation](../deployment-preparation/index.md). That guidance applies to all deployment models, with
additional sizing notes for hyper-converged clusters where compute and storage share nodes.

!!! info "Coming soon"
    A centralized hub deployment is in development. In this model, the Simplyblock Operator and the control plane run
    on a hub cluster that manages the storage of many member Kubernetes clusters through Open Cluster Management (OCM).
    See [Control Plane and Operator](../architecture/deployment-topologies/control-plane-and-operator.md).

## What This Section Covers

- **[Install](installation/index.md):** Install the operator with its Helm chart, let it install the control plane
  and the CSI driver, create a storage cluster from a discovered and approved deployment configuration, and apply
  distribution-specific configuration.
- **[Usage](usage/index.md):** Configure storage classes and quality of service, and provision, expand, snapshot, clone,
  encrypt, and remove logical volumes using Kubernetes resources.
- **[Operations](operations/index.md):** Monitor cluster health, scale capacity, protect volumes with backups, replicate
  asynchronously, coordinate node drains, and run cluster operations through the operator.

## Related References

- [Simplyblock Operator](../reference/operator/index.md): CRD fields and operational actions.
- [Simplyblock Helm Chart Reference](../reference/kubernetes/index.md): configurable Helm chart values.
- [Kubernetes CSI](../reference/troubleshooting/simplyblock-csi.md): troubleshooting the CSI driver.
