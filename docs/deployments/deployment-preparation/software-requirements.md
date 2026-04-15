---
title: Software Requirements
description: "Software Requirements: Comprehensive Simplyblock Deployment Model Requirements."
weight: 29999
---

## Operating System Requirements (Control Plane, Storage Plane)

**Control plane nodes**, as well as storage nodes in a **plain linux** deployment, require one of the following
operating systems:

| Operating System               | Versions |
|--------------------------------|----------|
| Alma Linux                     | 9        |
| Rocky Linux                    | 9        |
| Redhat Enterprise Linux (RHEL) | 9        |

In a hyper-converged deployment a broad range of operating systems are supported. The availability also depends on the
utilized Kubernetes distribution.

| Operating System               | Versions     |
|--------------------------------|--------------|
| Alma Linux                     | 9, 10        |
| Rocky Linux                    | 9, 10        |
| Redhat Enterprise Linux (RHEL) | 9, 10        |
| Ubuntu                         | 22.04, 24.04 |   
| Debian                         | 12, 13       |
| Talos                          | from 1.6.7   |

The operating system must be on the latest patch-level.


# Operating System Requirements (Initiator)

An initiator is the operating system to which simplyblock logical volumes are attached over the network (NVMe/TCP).

For further information on the requirements of the initiator-side (client-only), see:

- [Linux Distributions and Versions](../../reference/supported-linux-distributions.md)
- [Linux Kernel Versions](../../reference/supported-linux-kernels.md)

# Kubernetes Requirements

For Kubernetes-based deployments, the following Kubernetes environments and distributions are supported:

| Distribution         | Versions         |
|----------------------|------------------|
| Amazon EKS           | 1.28 and higher  |
| Google GKE           | 1.28 and higher  |
| K3s                  | 1.29 and higher  |
| Kubernetes (vanilla) | 1.28 and higher  |
| Talos                | 1.6.7 and higher |
| OpenShift            | 4.19 and higher  |

!!! important
    Simplyblock requires a Kubernetes cluster running on Linux host machines. Windows host machines are not supported.

# Proxmox Requirements

The Proxmox integration supports any Proxmox installation of version 8.0 and higher.

# OpenStack Requirements

The OpenStack integration supports any OpenStack installation of version 25.1 (Epoxy) or higher. Support for older
versions may be available on request.
