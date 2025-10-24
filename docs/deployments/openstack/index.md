---
title: OpenStack Integration
weight: 20350
---

!!! info
    This driver is still not part of the official OpenStack support matrix. 

    We are working on getting it there.
        
### Features Supported

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
- QoS
- Active/active HA support

### Deployment

Depending on the fabric, it is necessary to load the Linux kernel modules on compute nodes and controller:

```bash title="Load NVMe/TCP on Ubuntu  or Debian"
sudo apt-get install -y linux-modules-extra-$(uname -r)
sudo modprobe nvme_tcp
```
```bash title="Load NVMe/TCP on RHEL, Rocky or Alma"
sudo modprobe nvme_tcp
```
In case you need the RoCE/RDMA fabric or both fabrics, (also) run:

```bash title="Load NVMe/RoCE on Ubuntu  or Debian"
sudo apt-get install -y linux-modules-extra-$(uname -r)
sudo modprobe nvme_rdma
```
```bash title="Load NVMe/RoCE on RHEL, Rocky or Alma"
sudo modprobe nvme_rdma
```

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

```bash title="Rerun Kolla-Ansible Deploy Command for Cinder"
kolla-ansible deploy -i <inventory_file> --tags cinder
```
