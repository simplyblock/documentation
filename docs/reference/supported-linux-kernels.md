---
title: "Supported Linux Kernels"
weight: 20300
---

Simplyblock is built upon NVMe over Fabrics. Hence, it requires a Linux kernel with NVMe and NVMe-oF support.

As a general rule, every Linux kernel 5.19 or later is expected to work, as long as the kernel modules for NVMe (nvme),
NVMe over Fabrics (nvme-of), and NVMe over TCP (nvme-tcp) are available. In most cases, the latter two kernel
modules need to be loaded manually or persisted. Please see
the [Bare Metal or Virtualized (Linux) installation section](../deployments/baremetal/index.md) on how to do this.

The following kernels are known to be compatible and tested. Additional kernel versions may work, but are untested.

| OS                       | Linux Kernel                            | Prerequisite      |
|--------------------------|-----------------------------------------|-------------------|
| Red Hat Enterprise Linux | 4.18.0-xxx Kernel on x86_64             | modprobe nvme-tcp |
| Amazon Linux 2           | Kernel 5.10 AMI 2.0.20230822.0          | modprobe nvme-tcp |
| Amazon Linux 2023        | 2023.1.20230825.0 x86_64 HVM kernel-6.1 | modprobe nvme-tcp |

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
