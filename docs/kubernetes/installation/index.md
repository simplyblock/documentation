---
title: "Install Simplyblock"
description: "Install Simplyblock on Kubernetes using the simplyblock operator, which manages the full lifecycle of clusters, storage nodes, pools, and the CSI driver via CRDs."
weight: 20000
---

Simplyblock provides a Kubernetes operator that manages the full lifecycle of simplyblock storage infrastructure. The
operator is installed via a single Helm chart and uses Custom Resource Definitions (CRDs) to declaratively manage
clusters, storage nodes, storage pools, and the CSI driver.

For Kubernetes environments, a **simplyblock deployment** can be either hyper-converged or disaggregated.
In the hyper-converged model, simplyblock storage services run on selected Kubernetes worker nodes, sharing
resources with other workloads in the same Kubernetes cluster. In a disaggregated deployment, storage services run on
dedicated worker nodes either within the same or a different cluster.

## Deployment Overview (Recommended)

A typical Kubernetes deployment follows these steps:

1. **[Install the Operator](k8s-control-plane.md):** Deploy the simplyblock operator via the Helm chart with
   `deployment.profile=standalone`. The chart installs the operator, its CRDs, and the CSI driver, and the operator
   brings up the control plane.
2. **[Create a Storage Cluster](k8s-storage-plane.md):** The operator inspects the cluster's workers and writes a
   `ClusterDeploymentConfig` describing what it found. Review that draft, approve it, and the operator expands it
   into a storage cluster and its storage nodes. Then create a storage pool and provision the first volume.

For a detailed breakdown of every pod and service created by the Helm chart, see
[Management Cluster Architecture](management-cluster-architecture.md).

For connecting to an **external** simplyblock cluster (e.g., a disaggregated Linux-based cluster), the CSI driver
can be installed separately: [Install Simplyblock CSI](install-csi.md).

## Operator CRDs

The operator manages the following resources:

| CRD                       | Description                                                                        |
|---------------------------|------------------------------------------------------------------------------------|
| `ClusterDeploymentConfig` | A discovered deployment an administrator approves, expanded into the objects below |
| `OperatorOps`             | The discovery run that produces such a document                                    |
| `ControlPlane`            | The control plane this deployment uses, installed here or owned elsewhere          |
| `SimplyblockDriver`       | The CSI driver deployment                                                          |
| `StorageCluster`          | Creates and manages a simplyblock storage cluster                                  |
| `StorageNode`             | Represents a single backend storage node instance (auto-created)                   |
| `StorageNodeOps`          | One-shot operational action targeting a single storage node                        |
| `StoragePool`             | Creates and manages storage pools                                                  |

For detailed CRD documentation, see [Simplyblock Operator](../../reference/operator/index.md).

## Platform-Specific Notes

- [OpenShift](openshift.md): Additional configuration for OpenShift clusters.
- [SUSE Rancher and RKE2](rancher.md): Permissions and kubelet configuration for RKE2 and K3s clusters.
- [Talos](talos.md): Specifics for Talos-based OS images.
- [Volume Encryption](../usage/volume-encryption.md): End-to-end encryption with customer-managed keys.
