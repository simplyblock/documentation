---
title: "Configuring Volumes via Storage Classes"
weight: 30200
---

Based on the simplyblock storage cluster type and configuration, multiple settings can be applied in
the kubernetes storage class via settings under the <parameters> section:

```bash title="Storage Class Parameters"
parameters:
   stripe: <n=1,2,4>,<k=0,1,2>
   qos-service-class: <1-6>
   max-iops: <max-iops>
   max-write-mb: <max MB/s>
   maw-read-mb: <max MB/s>
   max-rw-mb: <max MB/s>
   namespace-volume: <yes,no>
   max-namespace-per-volume: <2-32>
   fabric: rdma
   cluster: <cluster-tag>
   pool: <poolname>
```

Stripe-size is an optional erasure coding schema. Each cluster has a default schema, but each volume
can optionally use an alternative schema. However, the schema must "fit" into the cluster: 
n+k must be equal to (or better smaller) than the number of nodes in the cluster.

See [Erasure Coding Configuration](../deployment-preparation/erasure-coding-scheme.md) for details.

See here how to configure [Service Classes] and [Qos Limits](../../maintenance-operations/QoS/Limiting%20IOPS%20and%20Throughput.md). 

##Namespace Volumes

For a definition of namespace volumes, see [here](../../architecture/concepts/logical-volumes.md).  

Find the advantages and disadvantages of NVMf namespaces versus NVMf subystems [here]().

If ```namespace-volumes``` is set to ```yes```, you also need to define the amount 
of namspaces per subsystem, e.g. ```max-namespace-per-volume: <n>```. This means that for every new
subsystem <n> namespaces will be created. 





















