---
title: "QoS  Limits"
weight: 10300
---

QoS Limits (IOPS, R,W and RW limits) can be chosen on both volume and pool level.

It is not allowed to set them on both. A volume assigned to a pool with active QoS setting 
can not contain own QoS settings or vice versa. It is possible to combine both approaches in
one cluster though. 

QoS settings on a pool limit the total consumption of all volumes in the pool, but they do not
determine how resources are split within a pool. Some volumes require and receive more IOPS, while 
others require and receive less. If the aggregate IO demand is beyond the limits set for a pool,
all volumes will be relatively throttled.

In Kubernetes, storage class-level QoS Settings are not allowed if the storage class is connected
to a pool with QoS settings.

Therefore, in kubernetes, if the [storage class](../../deployments/kubernetes/csi-features.md) references any pool, 
which has Qos limits attached, it is not allowed to add them to the storage class as well. 
The same applies to [Openstack](../../deployments/OpenStack/index.md) QoS Settings on the Volume Type.

!!! Warning  
    Volumes for which pool-level QoS is active must be located on the same storage node 
    in the cluster. Currently, it is not possible to spread them across storage nodes.

To set QoS limits when adding or changing a volume:
```Setting and updating QoS on volumes
sbctl volume add lvol01 100G pool01 --max-rw-iops 5000 --max-rw-mbytes 50 --max-r-mbytes 35 --max-w-mbytes 15
sbctl volume qos-set --max-rw-iops 10000 --max-rw-mbytes 100 --max-r-mbytes 70 --max-w-mbytes 30
```
And the same on pools:
```Setting and updating QoS on pools
sbctl pool add pool01 <CLUSTER-UUID> --max-rw-iops 5000 --max-rw-mbytes 50 --max-r-mbytes 35 --max-w-mbytes 15
sbctl pool set <POOL-UUID> --max-rw-iops 5000 --max-rw-mbytes 50 --max-r-mbytes 35 --max-w-mbytes 15
```

