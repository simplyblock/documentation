---
title: "Node Sizing"
weight: 30000
---

When planning the deployment of a simplyblock cluster, it is essential to plan the sizing of the nodes. The sizing
requirements are elaborated below, whether deployed on a private or public cloud or inside or outside of Kubernetes.

## Sizing Assumptions

The following sizing information is meant for production environments.

!!! warning
    If the sizing document discusses virtual CPUs (vCPU), it means 0.5 physical CPUs. This corresponds to a typical hyper-threaded CPU core
    x86-64. This also relates to how AWS EC2 cores are measured.

## Management Nodes

An appropriately sized management node cluster is required to ensure optimal performance and scalability. The management
plane oversees critical functions such as cluster topology management, health monitoring, statistics collection,
and automated maintenance tasks.

The following hardware sizing specifications are recommended:

| Hardware        |                                                                                                                             |
|-----------------|-----------------------------------------------------------------------------------------------------------------------------|
| CPU             | Minimum 4 vCPUs, plus<ul><li>1 vCPU per 5 storage nodes</li><li>1 vCPU 500 logical volumes</li></ul>                        |
| RAM             | Minimum 8 GiB, plus:<ul><li>1 GiB RAM per 5 storage nodes</li><li>1 GiB per 500 logical volumes</li></ul>                   |
| Disk            | Minimum 35 GiB, plus:<ul><li>500 MiB per 100 cluster objects (storage nodes, devices, logical volumes, snapshots)</li></ul> |
| Node type       | Bare metal or virtual machine with a supported Linux distribution                                                           |
| Number of nodes | For a production environment, a minimum of 3 management nodes is required.                                                  |

## Storage Nodes

!!! warning
    A storage node is not equal to a physical or virtual host. For optimal performance, at least two storage nodes are deployed on a two
    socket system (one per NuMA socket), for optimal performance even four storage nodes are recommended (2 per socket). 

A suitably sized storage node cluster is required to ensure optimal performance and scalability. Storage nodes are
responsible for handling all I/O operations and data services for logical volumes and snapshots.

The following hardware sizing specifications are recommended:

| Hardware |                                                                                                           |
|----------|-----------------------------------------------------------------------------------------------------------|
| CPU      | Minimum 5 vCPU                                                                                            |
| RAM      | Minimum 4 GiB                                                                                             |
| Disk     | Minimum 10 GiB free space on boot volume                                                                  |

### Memory Requirements

In addition to the above RAM requirements, the storage node requires additional memory based on the managed storage
capacity.

While a certain amount of ram is pre-reserved for spdk, another part is dynamically pre-allocated. Users should ensure that
the the full amount of required RAM is available (reserved) on the system as long as simplyblock is running.

The exact amount of memory is calculated when adding or restarting a node based on two parameters: the maximum
amount of storage available in the cluster and the maximum amount of logical volumes which can be created on the node:

| Unit                                  | Memory Requirement |
|---------------------------------------|--------------------|
| Fixed amount                          | 2 GiB              |
| Per logical volume                    | 25 MiB             |
| % of max. utilized capacity on node   | 0.05               |
| % of local node nvme capacity         | 0.025              |

Example: Your node has 10 nvme with 8TB each, your cluster has 3 nodes with 240TB in total capacity,
logial volumes are equally distributed across nodes and you plan to use up to 1.000 logical volumes on the node.
This gives you (2 + 0.025*1.000 + 0.05 * 240.000/3 + 0.025 * 80.000) = 64.5GB.

If not enough memory is available, the node will refuse to start. In this case, you may check
`/proc/meminfo` for total, reserved, and available system and huge page memory on a corresponding node. 

!!! info
    Part of the memory will be allocated as huge-page memory. In case of a high degree of memory fragmentation, a system
    may not be able to allocate enough of huge-page memory even if there is enough of system memory available. Reboot 
    your system if you run into an error at node start time.  
    Execute the following command to allocate temporary huge pages while the system is already running. It will allocate
    8 GiB in huge pages. Please adjust the number of huge pages depending on your requirements.

    ```bash title="Allocate temporary huge pages"
    sudo sysctl vm.nr_hugepages=4096
    ```
    Since the allocation is temporary, it will disappear after a system reboot.

### Storage Planning

Simplyblock storage nodes require one or more NVMe devices to provide storage capacity to the distributed storage pool
of a storage cluster.

Furthermore, simplyblock storage nodes require one additional NVMe device with less capacity as a journaling device.
The journaling device becomes part of the distributed record journal, keeping track of all changes before being
persisted into their final position. This helps with write performance and transactional behavior by using a
write-ahead log structure and replaying the journal in case of a issue.

!!! warning
   Simplyblock does not work with device partitions or claimed (mounted) devices. Make sure all of your nvme devices
   are unmounted and not busy. Remove any partitions from devices prior to installing simplyblock. Low-level format
   nvme devices with 4KB block size (lbaf: 12). 

!!! info
    Secondary nodes don't need NVMe storage disks.

## Caching Nodes (K8s only)

In Kubernetes, simplyblock can be configured to deploy caching nodes. These nodes provide a ultra-low latency
write-through cache to a disaggregated cluster, improving access latency substantially.

| Hardware |                                                      |
|----------|------------------------------------------------------|
| CPU      | Minimum 6 vCPU                                       |
| RAM      | Minimum 4 GiB                                        |


