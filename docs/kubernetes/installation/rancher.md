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
    Simplyblock uses node labels to identify nodes that participate in the storage cluster.
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

## CPU Topology and Core Isolation

The kubelet CPU topology and the core isolation of the storage nodes are configured by simplyblock through the Helm
values of the operator. The cluster definition of RKE2 or K3s stays untouched:

| Helm value                             | Purpose                                                        |
|----------------------------------------|----------------------------------------------------------------|
| `storagenode.enableCpuTopology`        | Enables the CPU topology configuration on storage nodes        |
| `storagenode.isolateCores`             | Enables the automatic core isolation                           |
| `storagenode.skipKubeletConfiguration` | Skips the kubelet CPU topology configuration if already set up |
| `storagenode.reservedSystemCpu`        | Reserves CPU cores for the host and system workloads           |

The full list of values is documented in the [Kubernetes Reference](../../reference/kubernetes/index.md).

## SUSE Linux Micro Nodes

[SUSE Linux Micro](https://www.suse.com/products/micro/){:target="_blank" rel="noopener"} (SL Micro, formerly SLE Micro)
is supported as a worker node operating system and needs no image customization. Huge pages are allocated by
simplyblock automatically, and `/etc` is writable, so configuration drop-ins are applied directly.

Additional packages cannot be installed in place, because the root filesystem is read-only. Such a change is applied
with `transactional-update` and takes effect after a reboot.

## Installation of Simplyblock

To install the simplyblock components on a Rancher-managed cluster, follow the instructions to
[install the Simplyblock Operator](k8s-control-plane.md) and follow the instructions to [deploy the storage nodes and
CSI driver](k8s-storage-plane.md).
