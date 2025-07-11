---
title: "Prerequisites"
weight: 30000
---

When installing simplyblock control planes and storage planes, a number of prerequisites are important to understand.

Simplyblock uses Docker Swarm for the control plane cluster. In case of a bare metal or virtualized installation, it
will also use Docker Swarm for the storage plane. Hence, Docker has to be installed.

Furthermore, simplyblock requires installing the `{{ cliname }}` command line tool. This tool is written in
Python. Therefore, Python (3.5 or later) has to be installed. Likewise, pip, the Python package manager, has to be
installed with version 20 or later.

To install `{{ cliname }}` run:

```bash
sudo pip install {{ cliname }} --upgrade
```

## Node Sizing

Simplyblock has certain requirements in terms of CPU, RAM, and storage. See the specific
[Node Sizing](../deployment-planning/node-sizing.md) documentation to learn more.

### Node Instance Type

Simplyblock recommends pre-tested and verified instance types. Those instance types are:

- i3en.6xlarge
- i4i.8xlarge

## Network Configuration

Simplyblock requires a number of network ports to be available from different networks. The configuration of the
required network ports are provided in the [installation documentation](install-simplyblock.md).

Additionally, IPv6 must be disabled on all nodes running simplyblock.

```bash
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
sudo sysctl -w net.ipv6.conf.default.disable_ipv6=1
```

### AWS Networks
Specifically for AWS, simplyblock strongly advises using individual networks for the control plane and storage plane.

For access to the Cluster Management API, simplyblock recommends using an AWS load balancer as a front instead of
making the API available directly.

!!! warning
    Amazon Linux 2 and Amazon Linux 2023 **do not** support
    [NVMe over Fabrics Multipathing](../../important-notes/terminology.md#multipathing) right now!

### Careful with "Up To GBit/s Instances" 

AWS heavily discounts instances with "up to GBit/s" network bandwidth. These instances use a credit-based system to
calculate the currently available network bandwidth. These instances initially offer good throughput until the credits
are used up, which happens very quickly.

In addition to the limitation on the maximum available bandwidth, AWS heavily limits the number of packets per second.

!!! recommendation
    Simplyblock strongly recommends using EC2 instances with dedicated bandwidth. Generally recommended Amazon EC2
    instances are _i3en.6xlarge_ and _i4i.8xlarge_.

### Network Ports for Control Plane

{% include 'control-plane-network-port-table.md' %}

### Network Ports for Storage Plane

{% include 'storage-plane-network-port-table.md' %}

## Storage Configuration

Simplyblock has certain requirements in terms of storage. While the most important facts are provided in the
installation section, here are things to consider.

### Root Volume

The volume mounted as the root directory has to provide at least **35GiB** of free capacity. More free space is
recommended, especially for control plane nodes, which collect logs and the cluster state.

### NVMe Devices

{% include 'nvme-format.md' %}