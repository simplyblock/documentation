---
title: Software Requirements
description: "Software Requirements: Comprehensive Simplyblock Deployment Model Requirements."
weight: 29999
---

## Operating System Requirements (Control Plane, Storage Plane)

**Control plane nodes**, as well as storage nodes in a **plain Linux** deployment, require a Red Hat Linux-based
distribution with minimum version 9.

In a hyper-converged deployment a broad range of operating systems are supported. The availability depends on the
used Kubernetes distribution.

The operating system must be on the latest patch-level.

A full overview of the supported operating systems can be found at the
[Supported Linux Distributions](../../reference/supported-linux-distributions.md) reference.

# Operating System Requirements (Initiator)

An initiator (NVMe client) is the operating system to which simplyblock logical volumes are attached over the network
(NVMe/TCP or NVMe/RDMA).

A full overview of the supported operating systems for initiators can be found at:

- [Linux Distributions and Versions](../../reference/supported-linux-distributions.md#hosts-initiators-accessing-storage-cluster-over-nvmf)
- [Linux Kernel Versions](../../reference/supported-linux-kernels.md)

# Kubernetes Requirements

!!! important
    Simplyblock requires a Kubernetes cluster running on Linux host machines. Windows host machines are not supported.

For Kubernetes-based deployments, the following Kubernetes environments and distributions are supported:

| Distribution         | Versions         |
|----------------------|------------------|
| Amazon EKS           | 1.28 and higher  |
| Google GKE           | 1.28 and higher  |
| K3s                  | 1.29 and higher  |
| Kubernetes (vanilla) | 1.28 and higher  |
| Talos                | 1.6.7 and higher |
| OpenShift            | 4.19 and higher  |

Additionally, there are verified and supported operating systems for the Kubernetes worker nodes. A full reference is
available at the [Supported Linux Distributions](../../reference/supported-linux-distributions.md#kubernetes-hyper-converged-control-plane-and-storage-plane)
reference.

# Proxmox Requirements

The Proxmox integration supports any Proxmox installation of version 8.0 and higher.

# OpenStack Requirements

The OpenStack integration supports any OpenStack installation of version 25.1 (Epoxy) or higher. Support for older
versions may be available on request.
