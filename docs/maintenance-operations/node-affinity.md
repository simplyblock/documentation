---
title: "Node Affinity"
weight: 20060
---

Simplyblock features node affinity, sometimes also referred to as data locality. This feature ensures that storage
volumes are physically co-located on storage or Kubernetes worker nodes running the corresponding workloads. This
minimizes network latency and maximizes I/O performance by keeping data close to the application. Ideal for
latency-sensitive workloads, node affinity enables smarter, faster, and more efficient storage access in hyper-converged
and hybrid environments.

!!! info
    Node affinity is only available with hyper-converged or hybrid setups.

Node affinity does not sacrifice fault tolerance as parity data will still be distributed to other storage cluster nodes
enabling transparent fail over in case of a failure, or spill over in the situation where the locally available storage
runs out of available capacity.

## Enabling Node Affinity

To use node affinity, the storage cluster needs to be created with node affinity activated. When node affinity is
enabled for a logical volume, it will influence how the data distribution algorithm will handle read and write requests.

To enable node affinity at creation time of the cluster, the `--enable-node-affinity` parameter needs to be added:

```bash title="Enabling node affinity when the cluster is created"
sbcli cluster create \
    --ifname=<IF_NAME> \
    --ha-type=ha \
    --enable-node-affinity # <- this is important
```

To see all available parameters for cluster creation, see
[Cluster Create](../reference/cli/cluster.md#creates-a-new-cluster).

When the cluster was created with node affinity enabled, logical volumes can be created with node affinity which will
always try to locate data co-located with the requested storage node. 

## Create a Node Affine Logical Volume

When creating a logical volume, it is possible to provide a host id (storage node uuid) to request the storage cluster
to co-locate the volume with this storage node. This configuration will have no influence on storage clusters without
node affinity enabled.

To create a co-located logical volume, the parameter `--host-id` needs to be added to the creation command:

```bash title="Create a node affine logical volume"
sbcli volume add <NAME> <SIZE> <POOL> \
    --host-id=<HOST_ID> \
    ... # other parameters
```

To see all available parameters for a logical volume creation, see
[Logical Volume Creation](../reference/cli/volume.md#adds-a-new-logical-volume).

The storage node uuid (or host id) can be found using the `sbcli storage-node list` command.

```bash title="List all storage nodes in a storage cluster"
sbcli storage-node list --cluster-id=<CLUSTER_ID>
```
