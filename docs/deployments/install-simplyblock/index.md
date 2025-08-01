---
title: "Install Simplyblock"
weight: 20050
---

Installing simplyblock for production requires a few components to be installed, as well as a couple of configurations
to secure the network, ensure the performance, and data protection in the case of hardware or software failures.

Simplyblock provides two test scripts to automatically check your system's configuration. While those may not catch all
edge cases, they can help to streamline the configuration check. This script can be run multiple times during the
preparation phase to find missing configurations during the process.

```bash title="Automatically check your configurations"
# Configuration check for the control plane (management nodes)
curl -s -L https://install.simplyblock.io/scripts/prerequisites-cp.sh | bash

# Configuration check for the storage plane (storage nodes)
curl -s -L https://install.simplyblock.io/scripts/prerequisites-sn.sh | bash
```

## Before We Start

A simplyblock production cluster consists of three different types of nodes:

1. _Management nodes_ are part of the control plane which managed the cluster(s). A production cluster requires at least
   **three nodes**.
2. _Storage nodes_ are part of a specific storage cluster and provide capacity to the distributed storage pool. A
   production cluster requires at least **three nodes**.
3. _Secondary nodes_ are part of a specific storage cluster and enable automatic fail over for NVMe-oF connections. In a
   high-availability cluster, every primary storage node automatically provides a secondary storage node.

A single control plane can manage one or more clusters. If started afresh, a control plane must be set up before
creating a storage cluster. If there is a preexisting control plane, an additional storage cluster can be added
to it directly.

More information on the control plane, storage plane, and the different node types is available under
[Simplyblock Cluster](../../architecture/concepts/simplyblock-cluster.md) in the architecture section.

## Network Preparation

For network requirements,
see [System Requirements](../deployment-preparation/system-requirements.md#network-requirements).

Simplyblock recommends two individual network interfaces, one for the control plane and one for the storage plane.
Hence, in the following installation description, we assume two separate subnets. To install simplyblock in your
environment, you may have to adopt these commands to match your configuration.

| Network interface | Network definition | Abbreviation | Subnet          |
|-------------------|--------------------|--------------|-----------------|
| eth0              | Control Plane      | control      | 192.168.10.0/24 |
| eth1              | Storage Plane      | storage      | 10.10.10.0/24   |
