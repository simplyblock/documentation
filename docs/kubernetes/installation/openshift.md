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

To install the simplyblock components on OpenShift, follow the instructions to
[install the Simplyblock Operator](k8s-control-plane.md) and follow the instructions to [deploy the storage nodes and
CSI driver](k8s-storage-plane.md)
