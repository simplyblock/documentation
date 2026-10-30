---
title: "Sizing"
description: "Size simplyblock storage nodes and the control plane: vCPUs, memory, NUMA placement, hyper-converged shares, and the observability stack."
weight: 29980
---

This page sizes the two planes of simplyblock. A storage node is sized by its vCPUs, memory, devices, and network
bandwidth. The control plane is sized by the number of storage nodes and objects it manages. The minimum values are
listed in [Hardware and Storage Devices](hardware-requirements.md#minimum-system-requirements).

## Storage Node CPU

IOPS performance depends on the vCPUs of a storage node. The maximum performance is reached with 48 physical cores
per socket, of which 40 are dedicated (isolated) to the simplyblock data plane and the rest remain under the control
of Linux.

The vCPUs of a storage node are set as an absolute number per storage node, which applies to every node of the cluster:
`vcpuCount` in the deployment document (see [Cluster Deployment Options](../kubernetes/installation/cluster-deployment-options.md#sizing-options)).
A worker with fewer than the configured count plus one vCPU for the system is refused as a storage node.

If 32 or more physical cores are available per storage node, it is recommended to turn off hyperthreading in the
BIOS or UEFI setup.

### Hyper-Converged Sizing Guidance

As hyper-converged deployments share vCPUs with the applications, it is recommended to dedicate 15%-20%, but not less
than 8 vCPUs per socket, to simplyblock. For example, on a system with 32 cores (64 vCPUs) per socket, 8 vCPUs amount to
12.5% of the vCPU capacity. For very I/O-intensive applications, this amount should be increased.

Hyper-converged workers must provide enough resources for both simplyblock and the other workloads, including the
Kubernetes worker itself and the operating system.

### Core Isolation

!!! warning
    On storage nodes, the required vCPUs can be isolated from the operating system. No kernel-space process,
    user-space process, or interrupt handler is then scheduled on those vCPUs, which significantly improves tail
    latency and performance consistency. In Kubernetes, the CPU Manager and the Topology Manager are used by default,
    but the core isolation itself is opt-in and requires additional configuration on both the cluster and the host.

## NUMA Placement

Modern multi-socket servers use a memory architecture called
[NUMA (Non-Uniform Memory Access)](https://en.wikipedia.org/wiki/Non-uniform_memory_access){:target="_blank" rel="noopener"}.
Each CPU socket has its own local memory and I/O paths, and accessing local resources is faster than reaching across
sockets. Simplyblock is fully NUMA-aware: a storage node uses only the CPU cores, memory, NVMe devices, and network
interfaces of its own socket.

The sockets used on each worker and the number of storage nodes per socket are set with `socketsToUse` and
`nodesPerSocket` in the deployment document. By default, socket 0 is used with one storage node. More than one storage
node per socket can make sense in a disaggregated deployment when a socket has more than 10 NVMe devices attached or
provides more than 48 cores (96 vCPUs).

- **Devices:** All devices of a storage node must be directly attached to the socket the node runs on. A socket without
  attached devices cannot run a storage node. Spread the devices evenly across the sockets that run storage nodes.
- **Network interfaces:** The interfaces used for storage traffic should be attached to the same socket. Simplyblock
  does not assign them automatically.

!!! tip
    In a hyper-converged deployment, it can be preferable to attach all NVMe devices to one socket and to run a
    storage node only on that socket. This saves CPU and memory.

The NUMA layout of a host is checked with `lscpu`:

```bash title="Checking the NUMA configuration"
lscpu | grep -i numa
```

```plain title="Example output of the NUMA configuration"
NUMA node(s):                         2
NUMA node0 CPU(s):                    0-31
NUMA node1 CPU(s):                    32-63
```

The socket of every PCIe device, such as the NVMe devices and network interfaces, is listed with a short script:

```bash title="Listing the PCIe devices and their NUMA nodes"
#!/bin/bash

for i in /sys/class/*/*/device; do
    pci=$(basename "$(readlink $i)")
    if [ -e $i/numa_node ]; then
        echo "NUMA Node: $(cat $i/numa_node) ($i): $(lspci -s $pci)"
    fi
done | sort
```

## Storage Node Memory

The memory of a storage node depends on the maximum number of NVMe-oF subsystems per node (`maxSubsystemCount`).
For each 10 GBit/s of dedicated network bandwidth, at least 3 subsystems are recommended, and for each vCPU above 8, one
additional subsystem. Use the lower of both values. The hard limits are listed in [Limits](../reference/limits.md).

| Unit                                     | Memory Requirement |
|------------------------------------------|--------------------|
| Fixed amount                             | 3 GiB              |
| Per subsystem (cluster average per node) | 35 MiB             |
| Per TiB of storage capacity on the host  | 0.5 GiB            |

!!! note "Edge clusters"
    The memory formula applies to edge clusters as well, with a minimum of 3 GB of RAM per storage node.

## Control Plane

The minimum requirements of the simplyblock control plane are 4 vCPUs, 8 GiB of RAM, and about 25 GiB of disk space
per replica, on each of three nodes. Three nodes are the minimum for a highly available setup. The replicas are placed
on workers or on Kubernetes control plane nodes. In addition, an S3 bucket of at least 50 GB is highly recommended
for the backups of the control plane database.

!!! important
    Three replicas across three nodes are mandatory for FoundationDB, the key-value store of the control plane. The
    observability stack can optionally be replicated, and the remaining control plane services run without
    replication.

A control plane of that size manages up to three storage nodes and 18,000 objects, of which up to half can be logical
volumes. Per managed storage node above three, 1 vCPU, 2 GB of RAM, 5 GB of disk space, and 5 GB of backup space are
added.

### Observability Stack

Additionally, a non-production observability stack can be deployed. It is distributed across Kubernetes control plane
nodes or workers, and Thanos is the only replicated service. In total, at least 8 vCPUs, 20 GB of RAM, and 125 GB of
disk space are required. The disk space requirement grows significantly with a retention period above three days and
with more than three nodes.
