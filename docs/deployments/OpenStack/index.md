---
title: OpenStack Integration
weight: 20350
---

!!! info
    This driver is still not part of the official OpenStack support matrix. 
    We are working on getting it there.
        
### Features Supported

The following list of features is supported:
- create a volume
- thin provisioning 
- resize (extend) a volume
- delete a volume
- snapshot a volume
- revert to snapshot
- clone a volume (copy-on-write)
- extend an attached volume
- multi-attach a volume
- volume migration (driver-supported)
- QoS
- active/active HA support

### Deployment

Depending on the fabric, it is necessary to load the kernel modules on compute nodes and controller:

```bash title="Load nvmf/tcp on Ubuntu  or Debian"
sudo apt-get install -y linux-modules-extra-$(uname -r)
sudo modprobe nvme_tcp
```
```bash title="Load nvmf/tcp on RHEL, Rocky or Alma"
sudo modprobe nvme_tcp
```
In case you need the rdma fabric or both fabrics, (also) run:

```bash title="Load nvmf/rdma on Ubuntu  or Debian"
sudo apt-get install -y linux-modules-extra-$(uname -r)
sudo modprobe nvme_rdma
```
```bash title="Load nvmf/tcp on RHEL, Rocky or Alma"
sudo modprobe nvme_rdma
```

```bash title="Update globals.yaml"
enable_cinder: "yes"
...
#This is a fork of the cinder-volume driver container including Simplylblock:
cinder_volume_image: "docker.io/simplyblock/cinder-volume"
#If Simplyblock is the only Cinder Storage Backend:
skip_cinder_backend_check: "yes"
```

```bash title="Update cinder override for simplyblock backend located in /etc/kolla/config/cinder.conf"
[DEFAULT]
debug = True
# add simlyblock to enabled_backends list
enabled_backends = simplyblock

[simplyblock]
volume_driver = cinder.volume.drivers.simplyblock.driver.SimplyblockDriver
volume_backend_name = simplyblock
simplyblock_endpoint = <simplyblock_endpoint>
simplyblock_cluster_uuid = <simplyblock_cluster_uuid>
simplyblock_cluster_secret = <simplyblock_cluster_secret>
simplyblock_pool_name = <simplyblock_pool_name>
```

```Rerun kolla-ansible deploy command for cinder
kolla-ansible deploy -i <inventory_file> --tags cinder
```

