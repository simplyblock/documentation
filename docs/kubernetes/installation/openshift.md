---
title: "OpenShift"
description: "Install simplyblock on OpenShift: grant the privileged SCC, choose the TLS provider, and set the OpenShift environment of the deployment config."
weight: 40100
---

When installing simplyblock on OpenShift, the process is very similar to Kubernetes, with a few key differences.
OpenShift requires explicitly granting the privileged Security Context Constraint (SCC) to service accounts to enable
storage and SPDK operations, it provides its own certificate service for TLS, and the storage nodes apply their host
configuration through OpenShift MachineConfig objects.

!!! info
    In OpenShift deployments, not all worker nodes must host storage components.
    The `ClusterDeploymentConfig` lists the workers that participate in the storage cluster.
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

## TLS on OpenShift

TLS is enabled by default. On OpenShift, two certificate providers are available:

- **OpenShift service CA (`tls.provider=openshift`):** Uses the certificates OpenShift issues for services. It
  provides one-way TLS only, so `tls.mutual_enabled` must be set to `false`.
- **Cert-manager (`tls.provider=cert-manager`):** Required for mutual TLS and for an external KMS.
  [cert-manager](https://cert-manager.io/){:target="_blank" rel="noopener"} must be installed first.

```bash title="Install the operator with the OpenShift service CA"
helm install simplyblock-operator simplyblock/simplyblock-operator \
    --namespace simplyblock \
    --set tls.provider=openshift \
    --set tls.mutual_enabled=false
```

For details, see [Securing the Control Plane](security.md).

## OpenShift Environment

The `ClusterDeploymentConfig` that describes the storage cluster must name the environment `OpenShift`. Discovery
detects the distribution and writes it into the draft, but it should be checked during the review:

```yaml title="ClusterDeploymentConfig for OpenShift (excerpt)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ClusterDeploymentConfig
metadata:
  name: simplyblock-deployment
  namespace: simplyblock
spec:
  approved: false
  environment: OpenShift
  cluster:
    name: simplyblock-cluster
    maxSubsystemCount: 50
    vcpuCount: 8
    minHugePagesSize: "100G"
    stripe:
      dataChunks: 1
      parityChunks: 1
    fabricType: tcp
  nodeSets:
    - name: rack-a
      groups:
        - name: default
          workers: [worker-node-1, worker-node-2, worker-node-3]
          mgmtInterface: br-ex
          dataInterfaces: [br-ex]
          devices:
            nvme: ["0000:01:00.0", "0000:02:00.0"]
```

With `environment: OpenShift`, the expansion sets `openShiftCluster`, `enableCpuTopology`, and
`enableKubeletConfiguration` on `StorageCluster.spec.storageNodes`. The MachineConfig objects the storage nodes
generate are labeled into the MachineConfigPool named in `spec.storageNodes.openShiftMachineConfigPool`, which
defaults to `worker`.

## Installation of Simplyblock

To install the simplyblock components on OpenShift, follow the instructions to
[install the Simplyblock Operator](k8s-control-plane.md) and to [create a storage cluster](k8s-storage-plane.md).
