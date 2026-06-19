---
title: NUMA Considerations
description: "NUMA Considerations: Modern multi-socket servers use a memory architecture called NUMA (Non-Uniform Memory Access){:target=\"_blank\" rel=\"noopener\"}."
weight: 30300
---

Modern multi-socket servers use a memory architecture called
[NUMA (Non-Uniform Memory Access)](https://en.wikipedia.org/wiki/Non-uniform_memory_access){:target="_blank" rel="noopener"}.
In a NUMA system, each CPU socket has its own local memory and I/O paths. Accessing local resources is faster than
reaching across sockets to remote memory or devices. Simplyblock is fully NUMA-aware.

On a host with more than one socket, by default one storage node is deployed per NUMA node.

In rare cases, it can make sense to deploy more than one storage node per NUMA node (disaggregated deployment only):

- A single socket has attached more than 10 NVMe.
- A single socket provides more than 48 cores (96 vCPUs).

Users can change this behavior. Either by setting the appropriate Helm Chart parameters (in case of Kubernetes-based
storage node deployment) or by manually modifying the initially created configuration file on the storage node
(after running `{{ cliname }} storage-node configure`).

It is critical for performance that all NVMe devices of a storage node are directly connected to the NUMA socket to
which the storage node is deployed.

If a socket has no NVMe devices connected, it will not qualify to run a simplyblock storage node.

It is also important that the NIC(s) used by simplyblock for storage traffic are connected to the same NUMA socket.
However, simplyblock does not auto-assign a NIC and users have manually to take care of that.

!!! Important
    In a hyper-converged deployment, it can be preferable to attach all NVMe devices to one socket and only deploy a
    node on this socket. This saves overall CPU and RAM required for Simplyblock.

## Checking NUMA Configuration

Before configuring simplyblock, the system configuration should be checked for multiple NUMA nodes. This can be done
using the `lscpu` tool.

```bash title="How to check the NUMA configuration"
lscpu | grep -i numa
```

```plain title="Example output of the NUMA configuration"
[root@demo ~]# lscpu | grep -i numa
NUMA node(s):                         2
NUMA node0 CPU(s):                    0-31
NUMA node1 CPU(s):                    32-63
```

In the example above, the system has two NUMA nodes.

!!! recommendation
    If the system consists of multiple NUMA nodes, it is recommended to configure simplyblock with multiple storage
    nodes per storage host. The number of storage nodes should match the number of NUMA nodes.

## Ensuring NUMA-Aware Devices 

For optimal performance, there should be a similar number of NVMe devices per NUMA node. Additionally, it is recommended
to provide one Ethernet NIC per NUMA node. 

To check the NUMA assignment of PCI-e devices, the `lspci` tool and a small script can be used.

```bash title="Install pciutils which includes lspci"
yum install pciutils
```

```bash title="Small script to list all PCI-e devices and their NUMA nodes"
#!/bin/bash

for i in  /sys/class/*/*/device; do
    pci=$(basename "$(readlink $i)")
    if [ -e $i/numa_node ]; then
        echo "NUMA Node: `cat $i/numa_node` ($i): `lspci -s $pci`" ;
    fi
done | sort
```
