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

1. **[Install the Operator](k8s-control-plane.md):** Deploy the simplyblock operator via the Helm chart. The operator
   watches for simplyblock CRDs and reconciles the desired state.
2. **[Deploy Storage Nodes and CSI](k8s-storage-plane.md):** Apply CRDs to create the storage cluster, add storage
   nodes, create storage pools, and deploy the CSI driver.

For a detailed breakdown of every pod and service created by the Helm chart, see
[Management Cluster Architecture](management-cluster-architecture.md).

For connecting to an **external** simplyblock cluster (e.g., a disaggregated Linux-based cluster), the CSI driver
can be installed separately: [Install Simplyblock CSI](install-csi.md).

## Operator CRDs

The operator manages the following resources:

| CRD              | Description                                                      |
|------------------|------------------------------------------------------------------|
| `StorageCluster` | Creates and manages a simplyblock storage cluster                |
| `StorageNodeSet` | Fleet-level declarative configuration for a set of storage nodes |
| `StorageNode`    | Represents a single backend storage node instance (auto-created) |
| `StorageNodeOps` | One-shot operational action targeting a single storage node      |
| `Pool`           | Creates and manages storage pools                                |
| `Device`         | Manages NVMe devices on storage nodes                            |
| `Task`           | Monitors cluster tasks                                           |

For detailed CRD documentation, see [Simplyblock Operator](../../reference/operator/index.md).

## Platform-Specific Notes

- [OpenShift](openshift.md): Additional configuration for OpenShift clusters.
- [SUSE Rancher and RKE2](rancher.md): Permissions and kubelet configuration for RKE2 and K3s clusters.
- [Talos](talos.md): Specifics for Talos-based OS images.
- [Volume Encryption](../usage/volume-encryption.md): End-to-end encryption with customer-managed keys.
