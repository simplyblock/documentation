---
title: Software Requirements
description: "Software Requirements: Comprehensive Simplyblock Deployment Model Requirements."
weight: 29999
---

!!! info
    In cloud environments including GCP and AWS, instance types are pre-configured. In general,  
    there are no restrictions on instance types as long as these system requirements are met. However, it is highly
    recommended to stay with the [Recommended Cloud Instance Types](cloud-instance-recommendations.md) for production.

    For [hyper-converged](../../architecture/concepts/hyper-converged.md) deployments, it is important that node sizing
    applies to the dedicated resources consumed by simplyblock. Hyper-converged instances must provide enough of
    resources to satisfy both, simplyblock and other compute demand, including the Kubernetes worker itself and the 
    operating system.

## Deployment Models

Two deployment options are supported:

- **Plain Linux**: In this mode, which is also called Docker mode, all nodes are deployed to separate hosts. Storage
  nodes are usually bare-metal and control plane nodes are usually VMs.

  Basic Docker knowledge is helpful, but all management can be performed within the system via its CLI or API. 

- **Kubernetes**: In Kubernetes, both **disaggregated** deployments with dedicated workers or clusters for storage
  nodes, or **hyper-converged deployments** (co-located with compute workloads) are supported. A wide range of
  Kubernetes distros and operating systems are supported. For OpenShift clusters, the hyper-converged deployment model
  is recommended.

  Kubernetes Knowledge is required.

The minimum system requirements below concern simplyblock only and must be dedicated to simplyblock.

## Operating System Requirements (Control Plane, Storage Plane)

__Control plane nodes__, as well as storage nodes in a __plain linux__ deployment, require one of the following
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
