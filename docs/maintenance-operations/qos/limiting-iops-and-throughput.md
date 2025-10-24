---
title: "QoS Limits"
weight: 10300
---

QoS Limits (IOPS, Read, Write, and Read-Write limits) can now be chosen on a logical volume and storage pool level.
It is not allowed to set Qos limits on the logical volume level if a limit exists on the storage pool level.

Therefore, in Kubernetes, if the [Storage Class](../../usage/simplyblock-csi/storage-class.md) references any storage
pool with a Qos limit attached, it is not allowed to add them to the storage class as well. 

The same applies to [Openstack](../../deployments/openstack/index.md) QoS settings on the volume type.

While Qos limits on a volume apply only to a specific volume, QoS limits on a storage pool apply to all logical volumes
attached to the pool. All logical volumes together (in the same storage pool) may not exceed the limit. There is,
however, no individual limit to any logical volume in that pool. 

!!! Warning  
    Volumes for which pool-level QoS is configured must be located on the same storage node in the cluster. Currently,
    it is not possible to spread them across storage nodes.

Qos limits set in the Storage Class always apply to the volume level. 

Using the CLI you can set and change QoS limits on the pool and volume: 

```bash
{{ cliname }} storage-pool add ...
{{ cliname }} storage-pool update...
```

```bash
{{ cliname }} volume add ...
{{ cliname }} volume set-qos ...
```
