---
title: "Node Sizing"
weight: 30000
---

When planning the deployment of a simplyblock cluster, it is essential to plan the sizing of the nodes. The sizing
requirements are elaborated below, whether deployed on a private or public cloud, or inside and outside of Kubernetes.

!!! info
    In cloud environments including GCP and AWS, instance types are pre-configured. In general,  
    there are no restrictions on instance types as long as these system requirements and
    [Node Sizing Requirements](node-sizing.md) are met. However, it is highly recommended to
    stay with the [Recommended Cloud Instance Types](cloud-instance-recommendations.md).

    For [hyper-converged](../../architecture/concepts/hyper-
    converged.md) deployments, it is important that node sizing applies to the dedicated 
    resources consumed by simplyblock. Hyper-converged instances must provide enough of resources 
    to satisfy both, simplyblock and other compute demand, including the Kubernetes worker itself and the 
    operating system.

## Sizing Assumptions

The following sizing information is meant for production environments.

!!! warning
    If the sizing document discusses virtual CPUs (vCPUs), it means 0.5 physical CPUs. This corresponds to a typical
    hyper-threaded CPU core x86-64. This also relates to how AWS EC2 cores are measured for x86-64, while in AWS
    Graviton (ARM) a single vCPU corresponds to an entire core. It is recommended to switch off hyper-threading of the
    CPU if 32 or more vCPUs are available per storage node.

## Management Nodes (Control Plane)

There are now two types of deployments for the management cluster:
- standalone (on separate VMs): this deployment is recommended if you are not managing
  kubernetes yourself.
- Into kubernetes cluster. This can be either a dedicated storage cluster or a mixed
  (hyper-converged with compute) cluster.  

An appropriately sized management node cluster is required to ensure optimal performance and scalability. The management
plane oversees critical functions such as cluster topology management, health monitoring, statistics collection,
and automated maintenance tasks.

The following hardware sizing specifications are recommended for a standalone deployment:

| Hardware        |                                                                                                                             |
|-----------------|-----------------------------------------------------------------------------------------------------------------------------|
| CPU             | Minimum 4 vCPUs, plus:<ul><li>1 vCPU per 5 storage nodes</li><li>1 vCPU 500 logical volumes</li></ul>                       |
| RAM             | Minimum 16 GiB, plus:<ul><li>1 GiB RAM per 5 storage nodes</li><li>1 GiB per 500 logical volumes</li></ul>                  |
| Disk            | Minimum 50 GiB, plus:<ul><li>500 MiB per 100 cluster objects (storage nodes, devices, logical volumes, snapshots)</li></ul> |
| Node type       | Bare metal or virtual machine with a supported Linux distribution                                                           |
| Number of nodes | For a production environment, a minimum of 3 management nodes is required.                                                  |

In case of a kubernetes-based deployment, the key-value store is always replicated (clustered)
across a minimum of three nodes. The observability stack is optionally replicated (min. 3
replicas) and the WebAPI runs as a daemon set. The stateless sb-services-pod runs as a single
replica.

| Service                       | vCPU | RAM (GB) | Disk (GB) |                                                                                                                      |
|-------------------------------|------|----------|-----------|
| Key-Value Store               |  1   |    4     |  5        |
| Observability Stack           |  4   |    8     |  25       | 
| Web-API (daemonset)           |  1   |    2     |  0.5      |
| sb-services                   |  1   |    2     |  0.5      |

This configuration is for up to 10 storage nodes and 5.000 lvols and one week of full statistics and log retention. 

The other services (CLI, health monitoring and reconciliation, statistics and event collectors, task runners) are 
stateless and have moderate resource consumption. 
                                                                                                                     
## Storage Nodes (Storage Plane)

!!! warning
    A storage node is not equal to a physical or virtual storage host. For optimal performance, at least two storage
    nodes are deployed on two socket systems (one per NuMA socket). Depending on the storage host system, even four
    storage nodes may be recommended (2 per socket).

A suitably sized storage node cluster is required to ensure optimal performance and scalability. Storage nodes are
responsible for handling all I/O operations and data services for logical volumes and snapshots.

The following hardware sizing specifications are recommended:

| Hardware |                                          |
|----------|------------------------------------------|
| CPU      | Minimum 8 vCPU                           |
| RAM      | Minimum 16 GiB                           |
| Disk     | Minimum 10 GiB free space on boot volume |

### Memory Requirements

In addition to the above RAM requirements, the storage node requires additional memory based on the managed storage
capacity.

While a certain amount of RAM is pre-reserved
for [SPDK](../../important-notes/terminology.md#spdk-storage-performance-development-kit),
another part is dynamically pre-allocated. Users should ensure that the full amount of required RAM is available
(reserved) from the system as long as simplyblock is running.

The exact amount of memory is calculated when adding or restarting a node based on two parameters:

- The maximum amount of storage available in the cluster
- The maximum amount of logical volumes that can be created on the node

| Unit                               | Memory Requirement |
|------------------------------------|--------------------|
| Fixed amount                       | 3 GiB              |
| Per logical volume                 | 15 MiB             |
| % of max. cluster storage capacity | 300 MiB / TiB      |

!!! info
    Example: A node has 10 NVMe devices with 8TB each. The cluster has 3 nodes and a total capacity of 240 TB.
    Logical volumes are equally distributed across nodes, and it is planned to use up to 1,000 logical volumes on
    each node. Hence, the following formula:
    ```plain
    3 + (0.5 * 80) + (0.015 * 1000) = 58 GB
    ```

If not enough memory is available, the node will refuse to start. In this case, `/proc/meminfo` may be checked for
total, reserved, and available system and huge page memory on a corresponding node.

!!! info
    Part of the memory will be allocated as huge-page memory. In case of a high degree of memory fragmentation, a system
    may not be able to allocate enough of the huge-page memory even if there is enough system memory available. If the
    node fails to start up, a system reboot may ensure enough free memory.

    The following command can be executed to temporarily allocate huge pages while the system is already running. It
    will allocate 8 GiB in huge pages. The number of huge pages must be adjusted depending on the requirements.

    ```bash title="Allocate temporary huge pages"
    sudo sysctl vm.nr_hugepages=4096
    ```

    Since the allocation is temporary, it will disappear after a system reboot. It must be ensured that either the
    setting is reapplied after each system reboot or persisted to be automatically applied on system boot up.

### Storage Planning

Simplyblock storage nodes require one or more NVMe devices to provide storage capacity to the distributed storage pool
of a storage cluster.

Furthermore, simplyblock storage nodes require one additional NVMe device with less capacity as a journaling device.
The journaling device becomes part of the distributed record journal, keeping track of all changes before being
persisted into their final position. This helps with write-performance and transactional behavior by using a
write-ahead log structure and replaying the journal in case of an issue.

!!! warning
    Simplyblock does not work with device partitions, partitioned devices, or claimed (mounted) devices. It must be
    ensured that all NVMe devices to be used by simplyblock are exclusive, unmounted, and not busy in any other way.

    Any partition must be removed from the NVMe devices prior to installing simplyblock. Furthermore, NVMe devices must
    be low-level formatted with a 4KB block size (lbaf: 12). More information can be found in
    [NVMe Low-Level Format](../../reference/nvme-low-level-format.md).

