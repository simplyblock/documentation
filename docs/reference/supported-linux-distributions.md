---
title: "Supported Linux Distributions"
weight: 20200
---

Simplyblock requires a Linux Kernel 5.19 or later with NVMe over Fabrics and NVMe over TCP enabled. However, `sbcli`,
the simplyblock commandline interface, requires some additional tools and expects certain conventions for configuration
files and locations. Therefore, simplyblock officially only supports Red Hat-based Linux distribution as of now.

While others may work, manual intervention may be required and simplyblock cannot support those as of now.

The following Linux distributions are considered tested and supported:

| Distribution             | Version | Support Level       |
|--------------------------|---------|---------------------|
| Red Hat Enterprise Linux | 9       | Fully supported     |
| Rocky Linux              | 9       | Fully supported     |
| AlmaLinux                | 9       | Fully supported     |
| Amazon Linux 2           | -       | Partially supported |
| Amazon Linux 2023        | -       | Fully supported     |

