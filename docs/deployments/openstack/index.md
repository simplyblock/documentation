---
title: OpenStack Integration
description: "OpenStack Integration: This driver is still not part of the official OpenStack support matrix."
weight: 20350
---

!!! info
    This driver is still not part of the official OpenStack support matrix. 

    We are working on getting it there.

## Scope and Support Status

This guide describes how to integrate simplyblock as a Cinder backend in OpenStack environments managed via
Kolla-Ansible style configuration.

Because this integration is not yet in the official support matrix, validate all changes in a staging environment
before production rollout.

## Features Supported

The following list of features is supported:

- Thin provisioning 
- Creating a volume
- Resizing (extend) a volume
- Deleting a volume
- Snapshotting a volume
- Reverting to snapshot
- Cloning a volume (copy-on-write)
- Extending an attached volume
- Multi-attaching a volume
- Volume migration (driver-supported)
- QoS (Quality of Service)
- Active/active HA support

## Architecture Overview

At a high level:

- OpenStack Cinder uses the simplyblock backend driver.
- Cinder backend configuration points to a simplyblock API endpoint and target cluster/pool.
- Compute/controller hosts must have the required NVMe transport kernel modules loaded (`nvme_tcp` and optionally
  `nvme_rdma`).

## Prerequisites

Before deployment:

- OpenStack control plane is healthy and Cinder is operational.
- A reachable simplyblock endpoint is available.
- Valid simplyblock backend values are prepared:
  - `simplyblock_endpoint`
  - `simplyblock_cluster_uuid`
  - `simplyblock_cluster_secret`
  - `simplyblock_pool_name`
- Network and firewall rules allow control and data-path communication.

## Prepare Hosts

Depending on the fabric, it is necessary to load the Linux kernel modules on compute nodes and controller:

=== "Red Hat / Alma / Rocky"
    ```bash title="Load NVMe/TCP on RHEL, Rocky or Alma"
    sudo modprobe nvme_tcp
    ```

=== "Debian / Ubuntu"
    ```bash title="Load NVMe/TCP on Ubuntu  or Debian"
    sudo apt-get install -y linux-modules-extra-$(uname -r)
    sudo modprobe nvme_tcp
    ```

In case you need the RoCE/RDMA fabric or both fabrics, (also) run:

=== "Red Hat / Alma / Rocky"
    ```bash title="Load NVMe/RoCE on RHEL, Rocky or Alma"
    sudo modprobe nvme_rdma
    ```

=== "Debian / Ubuntu"
```bash title="Load NVMe/RoCE on Ubuntu  or Debian"
sudo apt-get install -y linux-modules-extra-$(uname -r)
sudo modprobe nvme_rdma
    ```

## Configure OpenStack (Kolla-Ansible)

```bash title="Update globals.yaml"
enable_cinder: "yes"
...
#This is a fork of the cinder-volume driver container including Simplyblock:
cinder_volume_image: "docker.io/simplyblock/cinder-volume"
#If Simplyblock is the only Cinder Storage Backend:
skip_cinder_backend_check: "yes"
```

```bash title="Update Cinder Override for Simplyblock Backend Located in /etc/kolla/config/cinder.conf"
[DEFAULT]
debug = True
# Add Simplyblock to enabled_backends list
enabled_backends = simplyblock

[simplyblock]
volume_driver = cinder.volume.drivers.simplyblock.driver.SimplyblockDriver
volume_backend_name = simplyblock
simplyblock_endpoint = <simplyblock_endpoint>
simplyblock_cluster_uuid = <simplyblock_cluster_uuid>
simplyblock_cluster_secret = <simplyblock_cluster_secret>
simplyblock_pool_name = <simplyblock_pool_name>
```

## Deploy and Reload Cinder

```bash title="Rerun Kolla-Ansible Deploy Command for Cinder"
kolla-ansible deploy -i <inventory_file> --tags cinder
```

## Validation

After deployment:

1. Confirm Cinder services are healthy.
2. Create a test volume on the simplyblock backend.
3. Attach the volume to a test instance and verify device visibility in the guest OS.
4. Perform a basic read/write smoke test.
5. Detach and delete the test volume.

## Troubleshooting

Common issues to check first:

- Required kernel modules are not loaded on relevant hosts.
- Cinder backend configuration values are incorrect or incomplete.
- Endpoint, cluster UUID, secret, or pool name mismatch.
- Cinder service restart/deploy did not apply updated config.
- Network path issues between OpenStack services and simplyblock control/data paths.

## Operational Notes

- For RDMA/RoCE deployments, ensure NIC and fabric prerequisites are satisfied consistently across all relevant hosts.
- Re-validate this integration after OpenStack, Kolla, or simplyblock version upgrades.
