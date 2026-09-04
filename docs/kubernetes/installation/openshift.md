---
title: "OpenShift"
description: "When installing simplyblock on OpenShift, the process is very similar to Kubernetes, with one key difference, OpenShift requires explicitly granting the."
weight: 40100
---

When installing simplyblock on OpenShift, the process is very similar to Kubernetes, with one key difference,
OpenShift requires explicitly granting the privileged Security Context Constraint (SCC) to service accounts to enable
storage and SPDK operations.

!!! info
    In OpenShift deployments, not all worker nodes must host storage components.
    Simplyblock uses node labels to identify nodes that participate in the storage cluster.
    Storage workloads can be isolated on dedicated worker nodes or node pools.

## Prerequisites

Ensure the OpenShift cluster is operational and that administrator privileges are available.

Before deploying simplyblock components, grant the required SCC permissions:

```bash title="Grant SCC permissions"
oc create namespace simplyblock

oc adm policy add-scc-to-group privileged system:serviceaccounts:simplyblock
oc adm policy add-scc-to-group anyuid system:serviceaccounts:simplyblock

oc label namespace simplyblock \
  pod-security.kubernetes.io/enforce=privileged \
  pod-security.kubernetes.io/audit=privileged \
  pod-security.kubernetes.io/warn=privileged
```

This step is mandatory to allow SPDK and storage-related containers to run with the privileges required for NVMe device
access.

## Installation of Simplyblock

The Simplyblock Operator is installed with the Helm chart or through the OpenShift OperatorHub, since
simplyblock-operator is published in Red Hat's certified-operators catalog. Storage nodes, storage pools, and the CSI
driver are deployed the same way regardless of which install method is used.

=== "Helm"
    To install the simplyblock components on OpenShift, follow the instructions to
    [install the Simplyblock Operator](k8s-control-plane.md) and follow the instructions to [deploy the storage
    nodes and CSI driver](k8s-storage-plane.md).

=== "OperatorHub"
    {{ experimental }}

    The operator is installed from OperatorHub in the OpenShift web console. Only the `AllNamespaces` install mode
    is supported, so the operator is installed into the `openshift-operators` namespace and reconciles resources
    across the whole cluster. The container images referenced by the bundle are pulled from
    `quay.io/simplyblock-io`, so no Red Hat entitlement or pull secret is required.

    The same subscription is created directly with the following manifest:

    ```yaml title="Example of a Subscription for the Simplyblock Operator (simplyblock-subscription.yaml)"
    apiVersion: operators.coreos.com/v1alpha1
    kind: Subscription
    metadata:
      name: simplyblock-operator
      namespace: openshift-operators
    spec:
      channel: alpha
      name: simplyblock-operator
      source: certified-operators
      sourceNamespace: openshift-marketplace
    ```

    ```bash title="Creating the subscription"
    oc apply -f simplyblock-subscription.yaml
    ```

    The SCC permissions described above are still required, and storage nodes, storage pools, and the CSI driver
    are still deployed by following [Deploy Storage Nodes and CSI](k8s-storage-plane.md).
