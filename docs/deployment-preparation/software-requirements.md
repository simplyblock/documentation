---
title: Software Requirements
description: "Software Requirements: Comprehensive Simplyblock Deployment Model Requirements."
weight: 29999
---

## Operating System Requirements (Control Plane, Storage Plane)

**Control plane nodes**, as well as storage nodes in a **plain Linux** deployment, require a Red Hat Linux-based
distribution in version 9.

In a hyper-converged deployment a broad range of operating systems are supported. The availability depends on the
used Kubernetes distribution.

The operating system must be on the latest patch-level.

A full overview of the supported operating systems can be found at the
[Supported Linux Distributions](../reference/supported-linux-distributions.md) reference.

# Operating System Requirements (Initiator)

An initiator (NVMe client) is the operating system to which simplyblock logical volumes are attached over the network
(NVMe/TCP or NVMe/RDMA).

A full overview of the supported operating systems for initiators can be found at:

- [Linux Distributions and Versions](../reference/supported-linux-distributions.md#hosts-initiators-accessing-storage-cluster-over-nvmf)
- [Linux Kernel Versions](../reference/supported-linux-kernels.md)

# Kubernetes Requirements

!!! important
    Simplyblock requires a Kubernetes cluster running on Linux host machines. Windows host machines are not supported.

For Kubernetes-based deployments, the following Kubernetes environments and distributions are supported:

| Distribution         | Versions                               |
|----------------------|----------------------------------------|
| Amazon EKS           | 1.30 and higher                        |
| Google GKE           | 1.30 and higher - non production only! |
| K3s                  | 1.33 and higher                        |
| Kubernetes (vanilla) | 1.33 and higher                        |
| RKE2                 | 1.33 and higher                        |
| Talos                | 1.6.7 and higher                       |
| OpenShift            | 4.19 and higher                        |

!!! info
    SUSE Rancher is a management plane, not a Kubernetes distribution. Simplyblock is installed into the downstream
    cluster it manages, which must run a supported RKE2 or K3s version. For details, see
    [SUSE Rancher and RKE2](../kubernetes/installation/rancher.md).

Additionally, there are verified and supported operating systems for the Kubernetes worker nodes. A full reference is
available at the [Supported Linux Distributions](../reference/supported-linux-distributions.md#kubernetes-hyper-converged-control-plane-and-storage-plane)
reference.

!!! note "Edge clusters"
    An [edge cluster](../architecture/deployment-topologies/edge-clusters.md) runs the Simplyblock Operator in the
    managed profile and connects to the control plane on a hub cluster:

    - **Hub:** The control plane runs with the standalone profile. Its Management API is reachable from every edge
      site, for example, through a LoadBalancer Service, an OpenShift Route, or an Ingress. Loopback and link-local
      endpoints are rejected. A Secret with a static admin token, referenced by
      `controlplane.local.adminTokenSecretRef`, lets edge operators authenticate, because the hub cannot verify a
      service account token of another cluster.
    - **Credentials at the edge:** The Management API endpoint, the admin token, the CA certificate of the Management
      API if it is not in the system trust store, and the storage node image of the release.
    - **Control plane nodes:** Small edge clusters often run storage on Kubernetes control plane nodes. The discovery
      must then be allowed to use them (`enableControlPlaneNodes`).
    - **Two-node OpenShift:** A two-node OpenShift cluster needs a tie-breaker for its own etcd, either OpenShift with
      an arbiter node or OpenShift with fencing through the BMCs of the servers. This is independent of the storage
      arbitration on the hub.
    - **Node remediation:** For two-node edge clusters, Node Health Check with Self Node Remediation or Fence Agents
      Remediation lets Kubernetes restart the workloads of a failed node. Without it, they wait for the default
      eviction timeout.

# Proxmox Requirements

The Proxmox integration supports any Proxmox installation of version 8.0 and higher.

# OpenStack Requirements

The OpenStack integration supports any OpenStack installation of version 25.1 (Epoxy) or higher. Support for older
versions may be available on request.
