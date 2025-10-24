---
title: "Supported Linux Distributions"
weight: 20200
---

Simplyblock requires a Linux Kernel 5.19 or later with NVMe over Fabrics and NVMe over TCP enabled. However,
`{{ cliname }}`, the simplyblock commandline interface, requires some additional tools and expects certain
conventions for configuration files and locations. Therefore, simplyblock officially only supports Red Hat-based Linux
distributions as of now.

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

| Distribution             | Version     | Architecture | Support Level   |
|--------------------------|-------------|--------------|-----------------|
| Red Hat Enterprise Linux | 9 and later | x64, arm64   | Fully supported |
| Rocky Linux              | 9 and later | x64, arm64   | Fully supported |
| AlmaLinux                | 9 and later | x64, arm64   | Fully supported |

## Kubernetes: Control Plane and Storage Plane

The following Linux distributions are considered tested and supported to run a hyper-converged storage plane:

| Distribution             | Version         | Architecture | Support Level   |
|--------------------------|-----------------|--------------|-----------------|
| Red Hat Enterprise Linux | 9 and later     | x64, arm64   | Fully supported |
| Rocky Linux              | 9 and later     | x64, arm64   | Fully supported |
| Alma Linux               | 9 and later     | x64, arm64   | Fully supported |
| Ubuntu                   | 22.04 and later | x64, arm64   | Fully supported |
| Debian                   | 12 or later     | x64, arm64   | Fully supported |
| Amazon Linux 2 (AL2)     | -               | x64, arm64   | Fully supported |
| Amazon Linux 2023        | -               | x64, arm64   | Fully supported |
| Talos                    | 1.6.7 or later  | x64, arm64   | Fully supported |

## Hosts (Initiators accessing Storage Cluster over NVMf)

The following Linux distributions are considered tested and supported as NVMe-oF storage clients:

| Distribution             | Version       | Architecture | Support Level                   |
|--------------------------|---------------|--------------|---------------------------------|
| Red Hat Enterprise Linux | 8.1 and later | x64, arm64   | Fully supported                 |
| CentOS                   | 8 and later   | x64, arm64   | Fully supported                 |
| Rocky Linux              | 9 and later   | x64, arm64   | Fully supported                 |
| AlmaLinux                | 9 and later   | x64, arm64   | Fully supported                 |
| Ubuntu                   | 18.04         | x64, arm64   | Fully supported                 |
| Ubuntu                   | 20.04         | x64, arm64   | Fully supported                 |
| Ubuntu                   | 22.04         | x64, arm64   | Fully supported                 |
| Debian                   | 12 or later   | x64, arm64   | Fully supported                 |
| Amazon Linux 2 (AL2)     | -             | x64, arm64   | Partially supported<sup>1</sup> |
| Amazon Linux 2023        | -             | x64, arm64   | Partially supported<sup>1</sup> |

<span markdown style="font-size: small;"><sup>1</sup> Amazon Linux 2 and Amazon Linux 2023 have a bug with
[NVMe over Fabrics Multipathing](../important-notes/terminology.md#multipathing). That means that NVMe over Fabrics
on any Amazon Linux operates in a degraded state with the risk of connection outages. Alternatively,
multipathing must be configured using the Linux Device Manager (dm) via DM-MPIO.</span> 
