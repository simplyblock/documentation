---
title: "Supported Linux Kernels"
weight: 20300
---

Simplyblock is built upon NVMe over Fabrics. Hence, it requires a Linux kernel with NVMe and NVMe-oF support.

As a general rule, every Linux kernel 5.19 or later is expected to work, as long as the kernel modules for NVMe (nvme),
NVMe over Fabrics (nvme-of), and NVMe over TCP (nvme-tcp) are available. In most cases, the latter two kernel
modules need to be loaded manually or persisted. Please see
the [Bare Metal (Linux) installation section](../deployments/baremetal/index.md) on how to do this.

The following kernels are known to be compatible and tested. Additional kernel versions may work but are untested.

| OS                       | Linux Kernel                            | Prerequisite      |
|--------------------------|-----------------------------------------|-------------------|
| Red Hat Enterprise Linux | 4.18.0-xxx Kernel on x86_64             | modprobe nvme-tcp |
| Amazon Linux 2           | Kernel 5.10 AMI 2.0.20230822.0          | modprobe nvme-tcp |
| Amazon Linux 2023        | 2023.1.20230825.0 x86_64 HVM kernel-6.1 | modprobe nvme-tcp |

!!! warning
    Amazon Linux 2 and Amazon Linux 2024 have a bug with NVMe multipathing. That means that NVMe over Fabrics on any
    Amazon Linux operates in a degraded state. It is **NOT** recommended to use Amazon Linux images to run simplyblock.
