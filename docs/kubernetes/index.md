---
title: Kubernetes
description: "Kubernetes: Simplyblock runs natively on Kubernetes, where it is deployed and managed by the simplyblock operator through Custom Resource Definitions."
weight: 10100
---

Simplyblock runs natively on Kubernetes, where it is deployed and managed by the simplyblock operator through Custom
Resource Definitions (CRDs). Workloads consume storage through the simplyblock CSI driver using standard Kubernetes
objects such as `StorageClass`, `PersistentVolumeClaim`, and `VolumeSnapshot`. Provisioning, snapshotting, cloning, and
resizing therefore become part of the regular application lifecycle instead of a separate administrative task.

Both **hyper-converged** and **disaggregated** topologies are supported. In a hyper-converged deployment, simplyblock
storage services share Kubernetes worker nodes with application workloads. In a disaggregated deployment, they run on
dedicated workers, either within the same cluster or in a separate one. A wide range of Kubernetes distributions is
supported, including OpenShift, SUSE Rancher (RKE2 and K3s), and Talos.

Before deploying, review the node sizing, network, and erasure coding guidance in
[Deployment Preparation](../deployment-preparation/index.md). That guidance applies to all deployment models, with
additional sizing notes for hyper-converged clusters where compute and storage share nodes.

## What This Section Covers

- **[Install Simplyblock](installation/index.md)**: Install the operator with its Helm chart, deploy the control plane
  and storage plane through CRDs, install the CSI driver, and apply distribution-specific configuration.
- **[Usage](usage/index.md)**: Configure storage classes and quality of service, and provision, expand, snapshot, clone,
  encrypt, and remove logical volumes using Kubernetes resources.
- **[Operations](operations/index.md)**: Monitor cluster health, scale capacity, back up and restore volumes, replicate
  asynchronously, coordinate node drains, and run cluster operations through the operator.

## Related References

- [Simplyblock Operator](../reference/operator/index.md): CRD fields and operational actions.
- [Simplyblock Helm Chart Reference](../reference/kubernetes/index.md): configurable Helm chart values.
- [Kubernetes CSI](../reference/troubleshooting/simplyblock-csi.md): troubleshooting the CSI driver.

!!! info
    To attach simplyblock storage to hosts outside of Kubernetes, or to run the storage cluster itself on plain Linux,
    Proxmox, or OpenStack, see [Non-Kubernetes](../non-kubernetes/index.md).
