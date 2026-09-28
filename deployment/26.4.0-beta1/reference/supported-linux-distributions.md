---
title: "Supported Linux Distributions"
description: "Supported Linux Distributions: Simplyblock requires a Linux Kernel 5.19 or later with NVMe over Fabrics and NVMe over TCP enabled."
source: "https://docs.simplyblock.io/latest/reference/supported-linux-distributions/"
---

# Supported Linux Distributions

Simplyblock requires a Linux Kernel 5.19 or later with NVMe over Fabrics and NVMe over TCP enabled. However,
`sbctl`, the simplyblock commandline interface, requires some additional tools and expects certain
conventions for configuration files and locations. For **plain Linux deployments**, which are managed through
`sbctl`, simplyblock therefore officially only supports Red Hat-based Linux distributions as of now.

**Kubernetes deployments** do not use `sbctl` on the nodes. The distributions supported for the Kubernetes
worker nodes are listed below.

While others may work, manual intervention may be required, and simplyblock cannot support those.

## Control Plane (Plain Linux)

The following Linux distributions are considered tested and supported to run a control plane:

| Distribution             | Version     | Architecture | Support Level   |
|--------------------------|-------------|--------------|-----------------|
| Red Hat Enterprise Linux | 9 and later | x64          | Fully supported |
| Rocky Linux              | 9 and later | x64          | Fully supported |
| AlmaLinux                | 9 and later | x64          | Fully supported |

## Storage Plane (Plain Linux)

The following Linux distributions are considered tested and supported to run a disaggregated storage plane:

| Distribution             | Version     | Architecture            | Support Level   |
|--------------------------|-------------|-------------------------|-----------------|
| Red Hat Enterprise Linux | 9 and later | x86-64, ARM64 (AArch64) | Fully supported |
| Rocky Linux              | 9 and later | x86-64, ARM64 (AArch64) | Fully supported |
| AlmaLinux                | 9 and later | x86-64, ARM64 (AArch64) | Fully supported |

## Kubernetes Hyper-Converged: Control Plane and Storage Plane

The following Linux distributions are considered tested and supported to run a hyper-converged control and storage
plane:

| Distribution             | Version         | Architecture            | Support Level               |
|--------------------------|-----------------|-------------------------|-----------------------------|
| Red Hat Enterprise Linux | 9 and later     | x86-64, ARM64 (AArch64) | Fully supported             |
| Rocky Linux              | 9 and later     | x86-64, ARM64 (AArch64) | Fully supported             |
| Alma Linux               | 9 and later     | x86-64, ARM64 (AArch64) | Fully supported             |
| Ubuntu                   | 22.04 and later | x86-64, ARM64 (AArch64) | Fully supported             |
| Debian                   | 12 or later     | x86-64, ARM64 (AArch64) | Fully supported             |
| Amazon Linux 2 (AL2)     | -               | x86-64, ARM64 (AArch64) | Fully supported             |
| Amazon Linux 2023        | -               | x86-64, ARM64 (AArch64) | Fully supported             |
| SUSE Linux Enterprise    | 15 SP7 or later | x86-64, ARM64 (AArch64) | Fully supported             |
| SUSE Linux Micro         | 6.1 or later    | x86-64, ARM64 (AArch64) | Fully supported             |
| Talos                    | 1.6.7 or later  | x86-64, ARM64 (AArch64) | Fully supported<sup>1</sup> |

<span markdown style="font-size: small;"><sup>1</sup> Talos is an immutable distribution shipping a minimal kernel
module set. It requires a custom node image and additional preparation to load the required kernel modules and reserve
huge pages. See [Talos](../kubernetes/installation/talos.md) for details.</span>

## Hosts (Initiators accessing Storage Cluster over NVMf)

The following Linux distributions are considered tested and supported as NVMe-oF storage clients:

| Distribution             | Version       | Architecture            | Support Level                   |
|--------------------------|---------------|-------------------------|---------------------------------|
| Red Hat Enterprise Linux | 8.1 and later | x86-64, ARM64 (AArch64) | Fully supported                 |
| CentOS                   | 8 and later   | x86-64, ARM64 (AArch64) | Fully supported                 |
| Rocky Linux              | 9 and later   | x86-64, ARM64 (AArch64) | Fully supported                 |
| AlmaLinux                | 9 and later   | x86-64, ARM64 (AArch64) | Fully supported                 |
| Ubuntu                   | 18.04         | x86-64, ARM64 (AArch64) | Fully supported                 |
| Ubuntu                   | 20.04         | x86-64, ARM64 (AArch64) | Fully supported                 |
| Ubuntu                   | 22.04         | x86-64, ARM64 (AArch64) | Fully supported                 |
| Debian                   | 12 or later   | x86-64, ARM64 (AArch64) | Fully supported                 |
| Amazon Linux 2 (AL2)     | -             | x86-64, ARM64 (AArch64) | Partially supported<sup>2</sup> |
| Amazon Linux 2023        | -             | x86-64, ARM64 (AArch64) | Partially supported<sup>2</sup> |

<span markdown style="font-size: small;"><sup>2</sup> Amazon Linux 2 and Amazon Linux 2023 have a bug with
[NVMe over Fabrics Multipathing](../important-notes/terminology.md#multipathing). That means that NVMe over Fabrics
on any Amazon Linux operates in a degraded state with the risk of connection outages. Alternatively,
multipathing must be configured using the Linux Device Manager (dm) via DM-MPIO.</span>
