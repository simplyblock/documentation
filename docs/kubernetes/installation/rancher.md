---
title: "SUSE Rancher and RKE2"
description: "Installing simplyblock into RKE2 or K3s clusters managed by SUSE Rancher, including the permissions required on CIS-hardened clusters."
weight: 40150
---

[SUSE Rancher](https://www.rancher.com/){:target="_blank" rel="noopener"} (Rancher Manager, Rancher Prime) is a
management plane for Kubernetes clusters and not a Kubernetes distribution of its own. Simplyblock is installed into a
downstream cluster managed by Rancher, never into the Rancher management cluster.

A Rancher-based deployment is made up of three layers, and the simplyblock requirements differ per layer:

| Layer                   | Examples                                                                                                                | Simplyblock requirements                    |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|
| Management plane        | Rancher Manager, Rancher Prime                                                                                          | None                                        |
| Kubernetes distribution | [RKE2](https://docs.rke2.io/){:target="_blank" rel="noopener"}, [K3s](https://k3s.io/){:target="_blank" rel="noopener"} | Privileged permissions on hardened clusters |
| Worker node OS          | SUSE Linux Enterprise, SUSE Linux Micro, RHEL, Ubuntu                                                                   | Supported Linux distribution                |

!!! info
    Not all worker nodes of a downstream cluster have to host storage components.
    The `ClusterDeploymentConfig` lists the workers that participate in the storage cluster.
    Storage workloads can be isolated on dedicated worker nodes or node pools.

## Prerequisites

The downstream cluster has to be operational, and cluster administrator privileges are required. `kubectl` is
configured against the downstream cluster with the kubeconfig provided by the Rancher UI, not with the kubeconfig of
the management cluster.

The cluster and its worker nodes have to meet the general simplyblock requirements:

- [Software Requirements](../../deployment-preparation/software-requirements.md)
- [Hardware Requirements](../../deployment-preparation/hardware-requirements.md)
- [Supported Linux Distributions](../../reference/supported-linux-distributions.md#kubernetes-hyper-converged-control-plane-and-storage-plane)

## Required Permissions

The Simplyblock CSI driver connects NVMe over Fabrics devices, formats them, and mounts them. Therefore, it runs as a
privileged container.

By default, RKE2 ships a Pod Security Admission configuration that enforces the `privileged` standard cluster-wide, and
nothing else has to be granted. On a cluster provisioned with the CIS hardening profile, the `restricted` standard is
enforced instead, and only the RKE2 system namespaces are exempted from it. The simplyblock namespace therefore has to
be labeled with the exemptions itself.

```yaml title="Example of the simplyblock namespace with privileged exemptions (simplyblock-namespace.yaml)"
apiVersion: v1
kind: Namespace
metadata:
  name: simplyblock
  labels:
    pod-security.kubernetes.io/enforce: privileged
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/audit: privileged
    pod-security.kubernetes.io/audit-version: latest
    pod-security.kubernetes.io/warn: privileged
    pod-security.kubernetes.io/warn-version: latest
```

```bash title="Creating the simplyblock namespace with the privileged exemptions"
kubectl apply -f simplyblock-namespace.yaml
```

The namespace is created before the operator is installed. Otherwise, the Helm chart creates an unlabeled namespace of
its own, and the exemptions never take effect.

## CPU Topology and Kubelet Configuration

The kubelet CPU topology of the storage nodes is configured by simplyblock itself. The cluster definition of RKE2 or
K3s stays untouched. The settings are part of the storage cluster, not of the Helm chart:

- **`spec.environment` of the `ClusterDeploymentConfig`:** `Rancher` for RKE2 clusters and `K3s` for K3s clusters.
  Both let the storage nodes apply the kubelet configuration they need (`enableKubeletConfiguration: true`).
- **`StorageCluster.spec.storageNodes`:** Holds the resulting storage node settings. `enableCpuTopology` and
  `reservedSystemCPU` are not derived from the environment and are set on the `StorageCluster` directly.

| Field on `spec.storageNodes` | Purpose                                                                                                         |
|------------------------------|-----------------------------------------------------------------------------------------------------------------|
| `enableCpuTopology`          | Enables topology-aware CPU assignment on storage nodes                                                          |
| `enableKubeletConfiguration` | Lets the storage nodes apply the kubelet CPU topology configuration. Set to `false` if it is already configured |
| `reservedSystemCPU`          | Reserves CPU cores for the host and system workloads                                                            |

```yaml title="ClusterDeploymentConfig for an RKE2 cluster (excerpt)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ClusterDeploymentConfig
metadata:
  name: simplyblock-deployment
  namespace: simplyblock
spec:
  approved: false
  environment: Rancher
  cluster:
    name: simplyblock-cluster
    maxSubsystemCount: 50
    vcpuCount: 8
  nodeSets:
    - name: storage
      groups:
        - name: default
          workers: [worker-1, worker-2, worker-3]
          devices:
            nvme: ["0000:01:00.0", "0000:02:00.0"]
```

The Helm values `storagenode.enableCpuTopology`, `storagenode.isolateCores`, `storagenode.skipKubeletConfiguration`,
and `storagenode.reservedSystemCpu` of earlier releases no longer exist. For the full list of `storageNodes` fields,
see [Simplyblock Operator](../../reference/operator/index.md).

## SUSE Linux Micro Nodes

[SUSE Linux Micro](https://www.suse.com/products/micro/){:target="_blank" rel="noopener"} (SL Micro, formerly SLE Micro)
is supported as a worker node operating system and needs no image customization. Huge pages are allocated by
simplyblock automatically, and `/etc` is writable, so configuration drop-ins are applied directly.

Additional packages cannot be installed in place, because the root filesystem is read-only. Such a change is applied
with `transactional-update` and takes effect after a reboot.

## Installation of Simplyblock

To install the simplyblock components on a Rancher-managed cluster, follow the instructions to
[install the Simplyblock Operator](k8s-control-plane.md) and to [create a storage cluster](k8s-storage-plane.md).
