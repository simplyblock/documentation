---
title: "Install Simplyblock on Kubernetes"
description: "Install Simplyblock on Kubernetes using the simplyblock operator, which manages the full lifecycle of clusters, storage nodes, pools, and the CSI driver via CRDs."
weight: 20050
---

Simplyblock provides a Kubernetes operator that manages the full lifecycle of simplyblock storage infrastructure. The
operator is installed via a single Helm chart and uses Custom Resource Definitions (CRDs) to declaratively manage
clusters, storage nodes, storage pools, and the CSI driver.

For Kubernetes environments, a **hyper-converged setup is a first-class simplyblock deployment model** and the
recommended approach. In this model, simplyblock storage services run on selected Kubernetes worker nodes, sharing
resources with other workloads in the same Kubernetes cluster.

For OpenShift environments, *hyper-converged* deployments are the recommended approach.

## Hyper-Converged Deployment Overview (Recommended)

A typical Kubernetes deployment follows these steps:

1. **[Install the Operator](k8s-control-plane.md)**: Deploy the simplyblock operator via the Helm chart. The operator
   watches for simplyblock CRDs and reconciles the desired state.
2. **[Deploy Storage Nodes and CSI](k8s-storage-plane.md)**: Apply CRDs to create the storage cluster, add storage
   nodes, create storage pools, and deploy the CSI driver.

For a detailed breakdown of every pod and service created by the Helm chart, see
[Management Cluster Architecture](management-cluster-architecture.md).

For connecting to an **external** simplyblock cluster (e.g., a disaggregated Linux-based cluster), the CSI driver
can be installed separately: [Install Simplyblock CSI](install-csi.md).

## Operator CRDs

The operator manages the following resources:

| CRD              | Description                                       |
|------------------|---------------------------------------------------|
| `StorageCluster` | Creates and manages a simplyblock storage cluster |
| `StorageNode`    | Deploys and manages storage nodes                 |
| `Pool`           | Creates and manages storage pools                 |
| `Lvol`           | Views logical volume status                       |
| `Device`         | Manages NVMe devices on storage nodes             |
| `Task`           | Monitors cluster tasks                            |

For detailed CRD documentation, see [Simplyblock Operator](../../reference/operator.md).

## Platform-Specific Notes

- [OpenShift](openshift.md) — additional configuration for OpenShift clusters.
- [Talos](talos.md) — specifics for Talos-based OS images.
- [Volume Encryption](volume-encryption.md) — end-to-end encryption with customer-managed keys.
