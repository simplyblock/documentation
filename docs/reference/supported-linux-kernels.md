---
title: "Supported Linux Kernels"
description: "Supported Linux Kernels: Simplyblock is built upon NVMe over Fabrics. Hence, it requires a Linux kernel with NVMe and NVMe-oF support."
weight: 20300
---

Simplyblock is built upon NVMe over Fabrics. Hence, it requires a Linux kernel with NVMe and NVMe-oF support.

As a general rule, every Linux kernel 5.19 or later is expected to work, as long as the kernel modules for NVMe (`nvme`),
NVMe over Fabrics (`nvme-fabrics`), and NVMe over TCP (`nvme-tcp`) are available. In most cases, the latter two kernel
modules need to be loaded manually or persisted.

The following kernels are known to be compatible and tested. Additional kernel versions may work, but are untested.

| OS                       | Linux Kernel                            | Prerequisite      |
|--------------------------|-----------------------------------------|-------------------|
| Red Hat Enterprise Linux | 4.18.0-xxx Kernel on x86_64             | modprobe nvme-tcp |
| Amazon Linux 2           | Kernel 5.10 AMI 2.0.20230822.0          | modprobe nvme-tcp |
| Amazon Linux 2023        | 2023.1.20230825.0 x86_64 HVM kernel-6.1 | modprobe nvme-tcp |

## Package Providing the NVMe/TCP Module

Most distributions ship `nvme-tcp` in the package that is installed with the kernel. Ubuntu is the exception: on many
Ubuntu kernels, `nvme-tcp` is in `linux-modules-extra-<kernel release>`, which minimal and cloud images do not
install. Without it, `modprobe nvme-tcp` fails with `Module nvme-tcp not found`, and the simplyblock CSI node plugin
does not start on that node.

The package is the same on x86-64 and ARM64.

| Distribution                             | Kernel                            | Package with `nvme-tcp`                    | Extra package needed |
|------------------------------------------|-----------------------------------|--------------------------------------------|----------------------|
| Red Hat Enterprise Linux, Rocky, Alma 8  | 4.18                              | `kernel-core`                              | No                   |
| Red Hat Enterprise Linux, Rocky, Alma 9  | 5.14                              | `kernel-modules-core`                      | No                   |
| Red Hat Enterprise Linux, Rocky, Alma 10 | 6.12                              | `kernel-modules-core`                      | No                   |
| Amazon Linux 2                           | 5.10                              | `kernel`                                   | No                   |
| Amazon Linux 2023                        | 6.1, 6.12, 6.18                   | `kernel`, `kernel6.12`, `kernel6.18`       | No                   |
| Debian 12                                | 6.1 (`amd64` and `cloud-amd64`)   | `linux-image-<release>`                    | No                   |
| Debian 13                                | 6.12 (`amd64` and `cloud-amd64`)  | `linux-image-<release>`                    | No                   |
| SUSE Linux Enterprise 15 SP7             | 6.4                               | `kernel-default`                           | No<sup>1</sup>       |
| SUSE Linux Micro 6.1                     | 6.4                               | `kernel-default`                           | No                   |
| Ubuntu 22.04                             | 5.15 and 6.8 (all cloud flavors)  | `linux-modules-extra-<release>`            | **Yes**              |
| Ubuntu 22.04                             | 5.15 `lowlatency`                 | `linux-modules-<release>`                  | No                   |
| Ubuntu 24.04                             | 6.8 `generic`                     | `linux-modules-extra-<release>`            | **Yes**              |
| Ubuntu 24.04                             | 6.8 `lowlatency`                  | `linux-modules-<release>`                  | No                   |
| Ubuntu 24.04                             | 7.0 (HWE and all cloud flavors)   | `linux-modules-<release>`                  | No                   |
| Talos                                    | -                                 | Custom image (see [Talos](../kubernetes/installation/talos.md)) | No |

<span markdown style="font-size: small;"><sup>1</sup> The `kernel-default-base` package, which some minimal images
use instead of `kernel-default`, does not contain `nvme-tcp`. Install `kernel-default` on those nodes.</span>

The Ubuntu cloud flavors are `aws`, `azure`, `gcp`, and `oracle`. The Ubuntu `kvm` kernel flavor is built without
NVMe/TCP (`CONFIG_NVME_TCP` is not set) and cannot be used for simplyblock nodes.

On Ubuntu, install the package for the running kernel and load the module:

```bash
sudo apt-get install -y linux-modules-extra-$(uname -r)
sudo modprobe nvme-tcp
```

The package is versioned with the kernel, so the package for a new kernel must be installed after each kernel update.
For the `aws`, `azure`, and `gcp` flavors, the `linux-modules-extra-<flavor>` meta-package does this automatically:

```bash
sudo apt-get install -y linux-modules-extra-aws
```

## Kernel Requirements for pNFS Clients

Nodes that mount [pNFS volumes](../kubernetes/usage/pnfs.md) need the pNFS block layout driver, built with
`CONFIG_PNFS_BLOCK` and usually loaded as the `blocklayoutdriver` module. It also serves the SCSI layout used by
simplyblock. The driver must support NVMe devices, which it finds through `/dev/disk/by-id/nvme-eui.` links created by
the CSI node plugin.

This depends on the kernel build, not on its version number. A node without it still mounts pNFS volumes, but routes
all of their data through the metadata server. How to check a node is described in
[Verifying the Direct Data Path](../kubernetes/usage/pnfs.md#verifying-the-direct-data-path).

| OS                       | Linux Kernel | pNFS Client Support |
|--------------------------|--------------|---------------------|
| Red Hat Enterprise Linux | 5.14.0-687   | Yes (RHEL 9.8)      |

The metadata server has no requirements on the host kernel beyond KVM, since it runs its own kernel inside a virtual
machine.

!!! warning
    Amazon Linux 2 and Amazon Linux 2023 have a bug with
    [NVMe over Fabrics Multipathing](../important-notes/terminology.md#multipathing). That means that NVMe over Fabrics on any Amazon Linux operates in a degraded
    state with the risk of connection outages. As an alternative, multipathing must be configured using the Linux Device
    Manager (dm) via DM-MPIO. Use the following DM-MPIO configuration:

    ```plain
    cat /etc/multipath.conf
    defaults {
        polling_interval 1
        user_friendly_names yes
        find_multipaths yes
        enable_foreign nvme
        checker_timeout 3
        failback immediate
        max_polling_interval 3
        detect_checker yes
    }

    devices {
        device {
            vendor "NVMe"
            product ".*"
            path_grouping_policy group_by_prio
            path_selector "service-time 0"
            failback "immediate"
            no_path_retry "queue"
            hardware_handler "1 ana"
        }
    }

    blacklist {
    }
    ```
