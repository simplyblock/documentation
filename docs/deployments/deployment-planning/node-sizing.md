---
title: "Node Sizing"
weight: 30000
---

When planning the deployment of a simplyblock cluster, it is essential to plan the sizing of the nodes. The sizing
requirements are elaborated below, whether deployed on a private or public cloud or inside or outside of Kubernetes.

## Sizing Assumptions

The following sizing information is meant for production environments.

!!! warning
    Simplyblock always recommends using physical cores over virtual and hyper-threading cores. If the sizing document
    discusses virtual CPUs (vCPU), it means 0.5 physical CPUs. This corresponds to a typical hyper-threaded CPU core
    x86-64. This also relates to how AWS EC2 cores are measured.

## Management Nodes

An appropriately sized management node cluster is required to ensure optimal performance and scalability. The management
plane oversees critical functions such as cluster topology management, health monitoring, statistics collection,
and automated maintenance tasks.

The following hardware sizing specifications are recommended:

| Hardware        |                                                                                                                             |
|-----------------|-----------------------------------------------------------------------------------------------------------------------------|
| CPU             | Minimum 4 vCPUs (AMD64), plus<ul><li>1 vCPU per 5 storage nodes</li><li>1 vCPU 500 logical volumes</li></ul>           |
| RAM             | Minimum 8 GiB, plus:<ul><li>1 GiB RAM per 5 storage nodes</li><li>1 GiB per 500 logical volumes</li></ul>                   |
| Disk            | Minimum 35 GiB, plus:<ul><li>500 MiB per 100 cluster objects (storage nodes, devices, logical volumes, snapshots)</li></ul> |
| Node type       | Bare metal or virtual machine with a supported Linux distribution                                                           |
| Number of nodes | For a production environment, a minimum of 3 management nodes is required.                                                  |

## Storage Nodes

A suitably sized storage node cluster is required to ensure optimal performance and scalability. Storage nodes are
responsible for handling all I/O operations and data services for logical volumes and snapshots.

The following hardware sizing specifications are recommended:

| Hardware |                                                                                                                                                                                                                                                                                          |
|----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| CPU      | Minimum 8 vCPUs (AMD64/ARM64).<br/>3 cores are dedicated to service threads.<br/>Additionally, available cores are allocated to worker threads. Each additional core contributes about 200.000 IOPS to the node's performance profile (disregarding other limiting factors such as network bandwidth). |
| RAM      | Minimum 4 GiB (for operating system)                                                                                                                                                                                                                                                     |
| Disk     | Minimum 5 GiB boot volume                                                                                                                                                                                                                                                                |

### Memory Requirements

In addition to the above RAM requirements, the storage node requires additional memory based on the managed storage
capacity.

Simplyblock works with two types of memory: [huge pages memory](https://wiki.debian.org/Hugepages), which has to be
pre-allocated prior to starting the storage node services and is then exclusively assigned to simplyblock, as well as
system memory, which is required on demand.

#### Huge Pages

The exact amount of huge page memory is calculated when adding or restarting a node based on two parameters: the maximum
amount of storage available in the cluster and the maximum amount of logical volumes which can be created on the node:

| Unit                           | Memory Requirement |
|--------------------------------|--------------------|
| Per logical volume             | 6 MiB              |
| Per TB of max. cluster storage | 256 MiB            |

!!! recommendation
    For bare metal, virtualized, or disaggregated deployments, simplyblock recommends allocating around 75% of the
    available memory as huge pages, minimizing memory overhead.<br/><br/>
    For hyper-converged deployments, please use the [huge pages calculator](../../reference/huge-pages-calculator.md). 

If not enough huge pages memory is available, the node will refuse to start. In this case, you may check
`/proc/meminfo` for total, reserved, and available huge page memory on a corresponding node.

Execute the following command to allocate temporary huge pages while the system is already running. It will allocate
8 GiB in huge pages. Please adjust the number of huge pages depending on your requirements.

```bash title="Allocate temporary huge pages"
sudo sysctl vm.nr_hugepages=4096
```

Since the allocation is temporary, it will disappear after a system reboot.

!!! recommendation
    Simplyblock recommends to pre-allocate huge pages via the bootloader commandline. This prevents fragmentation of
    the huge pages memory and ensures a continuous memory area to be allocated.
    ```plain title="GRUB configuration change"
    GRUB_CMDLINE_LINUX="${GRUB_CMDLINE_LINUX} default_hugepagesz=2MB hugepagesz=2MB hugepages=4096"
    ```
    Afterward, you need to persist the change to take effect.
    ```bash title="Persist GRUB configuration"
    sudo grub2-mkconfig -o /boot/efi/EFI/redhat/grub.cfg
    ```

#### Conventional Memory

Additionally to huge pages, simplyblock requires dynamically allocatable conventional system memory. The required
amount depends on the utilized storage.

| Unit                                   | Memory Requirement |
|----------------------------------------|--------------------|
| Per TiB of used local SSD storage      | 256 MiB            |
| Per TiB of used logical volume storage | 256 MiB            |

!!! info
    Used local SSD storage is the physically utilized capacity of the local NVMe devices on the storage node at a point
    in time. Used logical volume storage is the physically utilized capacity of all logical volumes on a specific
    storage node at a point in time.

### Storage Planning

Simplyblock storage nodes require one or more NVMe devices to provide storage capacity to the distributed storage pool
of a storage cluster.

!!! recommendation
    Simplyblock requires at least three similar sized NVMe devices per storage node.

Furthermore, simplyblock storage nodes require one additional NVMe device with less capacity as a journaling device.
The journaling device becomes part of the distributed record journal, keeping track of all changes before being
persisted into their final position. This helps with write performance and transactional behavior by using a
write-ahead log structure and replaying the journal in case of a issue.

!!! info
    Secondary nodes don't need NVMe storage disks.

## Caching Nodes (K8s only)

In Kubernetes, simplyblock can be configured to deploy caching nodes. These nodes provide a ultra-low latency
write-through cache to a disaggregated cluster, improving access latency substantially.

| Hardware |                                                      |
|----------|------------------------------------------------------|
| CPU      | Minimum 2 vCPU, better 2 physical cores.             |
| RAM      | Minimum 2 GiB, plus 25% of the configured huge pages |

In addition to the base conventional memory configuration, a caching node requires huge pages memory. Calculating the
required huge pages memory can be achieved using the following formula:

```plain title="Huge page calculation (caching node)"
huge_pages_size=2GiB + 0.0025 * nvme_size_gib
```

With the above formula, a locally-attached NVMe device of 1.9TiB would require 6.75GiB huge pages memory
(`2 + 0.0025 * 1900`).
