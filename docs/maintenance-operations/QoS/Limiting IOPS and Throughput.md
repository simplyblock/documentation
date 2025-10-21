---
title: "QoS  Limits"
weight: 10300
---

QoS Limits (IOPS, R,W and RW limits) can now be chosen on both volume and pool level.
It is not allowed to set Qos Limits on the volume level, if they are already set on the pool level.
Therefore, in kubernetes, if the [storage class]() references any pool, 
which has Qos limits attached, it is not allowed
to add them to the storage class as well. 
The same applies to [Openstack]() QoS Settings on the Volume Type.

While Qos limits on a volume apply only to this volume, qos limits on a pool apply to all volumes attached to the 
pool together. All volumes together in the pool may not exceed the limit, but there is no limit to any 
individual volume in that pool. 

!!! Warning  
    Volumes for which pool-level qos is defined must be located
    on the same storage node in the cluster. Currently it is not possible to spread them across storage nodes.

Qos Limits set in the Storage Class always apply to the volume level. 

Using the CLI you can set and change QoS limits on the pool and volume: 


```
sbcli pool add ...
sbcli pool update...
```

```
sbcli lvol add ...
sbcli lvol set-qos ...
```

