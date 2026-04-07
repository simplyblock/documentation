---
title: "Install Simplyblock Operator"
description: "Install the simplyblock Kubernetes operator via Helm. The operator manages the full lifecycle of simplyblock clusters, storage nodes, pools, and the CSI driver."
weight: 30000
---

The simplyblock operator is deployed via a single Helm chart. Once installed, it watches for simplyblock Custom
Resources and manages the full lifecycle of clusters, storage nodes, pools, and the CSI driver.

## Prerequisites

- A Kubernetes cluster (v1.24+)
- Helm 3 installed
- `kubectl` configured with cluster access

## Installing the Operator

```bash title="Install the simplyblock operator"
helm repo add simplyblock https://install.simplyblock.io/helm
helm repo update

helm install simplyblock -n simplyblock --create-namespace simplyblock/spdk-csi
```

After installation, verify the operator is running:

```bash title="Verify the operator"
kubectl get pods -n simplyblock
```

## Creating a Storage Cluster

Once the operator is running, create a storage cluster by applying a `SimplyBlockStorageCluster` CRD:

```yaml title="Example: storage-cluster.yaml"
apiVersion: simplyblock.simplyblock.io/v1alpha1
kind: SimplyBlockStorageCluster
metadata:
  name: my-cluster
  namespace: simplyblock
spec:
  clusterName: production
  mgmtIfc: eth0
  haType: ha
  stripeWdata: 2
  stripeWparity: 1
  fabric: tcp
```

```bash title="Apply the cluster resource"
kubectl apply -f storage-cluster.yaml
```

Check the cluster status:

```bash title="Check cluster status"
kubectl get simplyblockstoragecluster -n simplyblock
```

### Cluster Options

For NVMe-oF transport security, backup configuration, and other cluster options, see
[Cluster Deployment Options](../cluster-deployment-options.md).

## Next Steps

Once the cluster is created, proceed to [Deploy Storage Nodes and CSI](k8s-storage-plane.md) to add storage
capacity and enable volume provisioning.

For a complete reference of all CRD fields, see [Simplyblock Operator](operator.md).
