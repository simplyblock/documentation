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

## OpenShift Prerequisites

When deploying onto an OpenShift cluster, ensure that the environment-specific instructions provided in the
[OpenShift Installation](openshift.md) guide are followed.

## Choosing a Deployment Profile

`deployment.profile` decides where the control plane is. It is one of two values:

| Profile      | What it does                                                                                                            |
|--------------|-------------------------------------------------------------------------------------------------------------------------|
| `standalone` | This cluster hosts its own control plane. The operator installs FoundationDB, the object store, and the management API. |
| `managed`    | A control plane elsewhere manages this cluster's storage. Nothing is installed here for it.                             |

`standalone` is the default and is what a self-contained Kubernetes deployment uses. The `managed` profile
additionally needs `controlplane.managed.endpoint`, which is where that control plane answers; see
[Management Cluster Architecture](management-cluster-architecture.md).

## Installing the Operator

```bash title="Install the simplyblock operator"
helm repo add simplyblock https://install.simplyblock.io/helm
helm repo update

helm upgrade --install simplyblock -n simplyblock simplyblock/simplyblock-operator \
    --create-namespace \
    --set deployment.profile=standalone
```

The chart installs the operator and its CRDs, the CSI driver, and, for the `standalone` profile, a `ControlPlane`
resource. The operator installs FoundationDB, the object store, and the management API from that resource, in that
order. The database has to reach quorum before the management API starts, so the first install takes a few minutes.

## Waiting for the Control Plane

```bash title="Wait for the control plane to become available"
kubectl wait controlplane simplyblock -n simplyblock \
    --for=jsonpath='{.status.phase}'=Available --timeout=600s
```

`status.phase` is `Available` once the control plane answers. `Degraded` means it answers while something behind it
is short, and `status.components` names which.

```bash title="Watch the control plane settle"
kubectl get controlplane simplyblock -n simplyblock -w
```

!!! important "TLS Encryption"
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

Once the control plane is `Available`, proceed to [Create a Storage Cluster](k8s-storage-plane.md). On a fresh
install the operator has already inspected the cluster's workers and written a deployment config describing what it
found, which is what that page reviews and approves.

For a complete reference of all CRD fields, see [Simplyblock Operator](../../reference/operator/index.md).
