---
title: NUMA Considerations
weight: 30300
---

Modern multi-socket servers use a memory architecture called
[NUMA (Non-Uniform Memory Access)](https://en.wikipedia.org/wiki/Non-uniform_memory_access){:target="_blank" rel="noopener"}.
In a NUMA system, each CPU socket has its own local memory and I/O paths. Accessing local resources is faster than
reaching across sockets to remote memory or devices.

Simplyblock is NUMA-aware. On a host with more than one socket, it will per default deploy one or two storage nodes per socket. 
Two nodes per socket are deployed if: more than 32 vcpu (cores) are dedicated to Simplyblock per socket and/or if more than
10 NVME are connected to the socket.   

Users can change this behaviour either by setting the appropriate helm chart parameters (in case of kubernetes-based storage node deployment)
or by manually modifying the configuration file created by the first step of the deployment on the storage node (after running _sbctl sn configure_).

It is critical for performance that all NVME devices of a storage node are directly connected to the socket to which the storage node is deployed.
If a socket has no NVME devices connected, it is not qualified to run a Simplyblock Storage Node.

It is also important that the NIC(s) used by Simplyblock for storage traffic are connected to the same socket. However, Simplyblock does not auto-assign a NIC 
and users have to take care of that.

## Checking NUMA Configuration

Before configuring simplyblock, the system configuration should be checked for multiple NUMA nodes. This can be done
using the `lscpu` tool.

```bash title="How to check the NUMA configuration"
lscpu | grep -i numa
```

```plain title="Example output of the NUMA configuration"
root@demo:~# lscpu | grep -i numa
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
