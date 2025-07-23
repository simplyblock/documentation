---
title: "baremetal-attach"
weight: 20200
---

Simplyblock storage can be  attached over the network to linux hosts not running kubernetes or proxmox. 

While no Simplyblock components are installed on those hosts, os-level configuration steps, which are otherwise taken care of by csi or proxmox, have to be performed manually on each host to which simplyblock storage is to be attached.

### Install nvme client package

```bash title="Install nvme client package"
sudo yum install nvme-cli
```

### Load the kernel module

{% include 'prepare-nvme-tcp.md' %}

### Create a pool (via cli on one of the mgmt nodes)

Before lvols can be created and connected, a storage pool is required. If a pool already exists, it can be reused. Otherwise, creating a storage
pool can be created as following:

```bash title="Create a Storage Pool"
{{ cliname }} pool add <POOL_NAME> <CLUSTER_UUID>
```

The last line of a successful storage pool creation returns the new pool id.

```plain title="Example output of creating a storage pool"
[demo@demo ~]# {{ cliname }} pool add test 4502977c-ae2d-4046-a8c5-ccc7fa78eb9a
2025-03-05 06:36:06,093: INFO: Adding pool
2025-03-05 06:36:06,098: INFO: {"cluster_id": "4502977c-ae2d-4046-a8c5-ccc7fa78eb9a", "event": "OBJ_CREATED", "object_name": "Pool", "message": "Pool created test", "caused_by": "cli"}
2025-03-05 06:36:06,100: INFO: Done
ad35b7bb-7703-4d38-884f-d8e56ffdafc6 # <- Pool Id
```

### create and connect an lvol (via cli on one of the mgmt nodes)
```plain title="Example lvol create"
{{ cliname }} lvol add lvol01 1000G test  
```
In this example, an lvol with name lvol01 and 1TB of thinly provisioned capacity is created in the pool of name _test_. The uuid of the lvol is returned. Now run:
```plain title="Example lvol create"
{{ cliname }} lvol connect <LVOL-UUID>
```
Copy-Paste the output of this command to the host to which you want to attach the volume and run it.






