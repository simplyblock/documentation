---
title: "Install Simplyblock Operator"
description: "Install the simplyblock Kubernetes operator via Helm. The operator manages the full lifecycle of simplyblock clusters, storage nodes, pools, and the CSI driver."
weight: 30000
---

{{ experimental }}

The simplyblock operator is deployed via a single Helm chart. Once installed, it watches for simplyblock Custom
Resources and manages the full lifecycle of clusters, storage nodes, pools, and the CSI driver.

## Prerequisites

- A Kubernetes cluster (v1.24+)
- Helm 3 installed
- `kubectl` configured with cluster access

## OpenShift Prerequisites

If you are deploying onto an OpenShift cluster, ensure that the environment-specific instructions provided in the
[OpenShift Installation](openshift.md) guide are followed.

## Installing the Operator

```bash title="Install the simplyblock operator"
helm repo add simplyblock https://install.simplyblock.io/helm/csi
helm repo update

helm upgrade --install simplyblock -n simplyblock simplyblock/spdk-csi \
    --create-namespace \
    --set operator.enabled=true
```

!!! important "TLS Encryption"
    {{ experimental }}

    All internal control plane traffic can be encrypted with TLS. On OpenShift, the cluster's built-in certificate
    manager is used out of the box. Mutual TLS (mTLS), where components additionally authenticate each other with
    client certificates, is only works with Cert-Manager. That means that on OpenShift, the Cert-Manager must be
    installed to enable mTLS.

    See [Securing the Control Plane](security.md#transport-layer-security-mutual-tls-mtls) for configuration.

After installation, verify the operator is running:

```bash title="Verify the operator"
kubectl get pods -n simplyblock
```

## Next Steps

Once the cluster is created, proceed to [Deploy Storage Nodes](k8s-storage-plane.md) to add storage
capacity and enable volume provisioning.

For a complete reference of all CRD fields, see [Simplyblock Operator](../../reference/operator.md).
