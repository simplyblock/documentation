---
title: "Replacing a Storage Node"
weight: 20050
---

A simplyblock storage cluster is designed to be always up. Hence, operations such as extending a cluster or
replacing a storage node are online operations and don't require a system downtime. However, there are a few
things to keep in mind when replacing a storage node.

!!! danger
    If a storage node should be migrated, [Migrating a Storage Node](migrating-storage-node.md) must be followed.
    Removing a storage node from a simplyblock cluster without migrating it will make the logical volumes owned by this
    storage node inaccessible!

## Starting the new Storage Node

It is always recommended to start the new storage node before removing the old one, even if the remaining
cluster has enough storage available to absorb the additional (temporary) storage requirement.

Every operation that changes the cluster topology comes with a set of migration tasks, moving data across
the cluster to ensure equal usage distribution.

If a storage node failed and cannot be recovered, adding a new storage node is perfectly fine, though.

To start a new storage node, follow the storage node installation according to your chosen setup:

- [storage nodes in kubernetes](../deployments/kubernetes/index.md)
- [storage nodes on Bare Metal or Virtualized Linux](../deployments/install-simplyblock/install-sp.md)

## Remove the old Storage Node

!!! danger
    All volumes on this storage node, which haven't been migrated before the removal, will become inaccessible!

To remove the old storage node, use the `{{ cliname }}` command line tool. 

```bash title="Remove a storage node"
{{ cliname }} storage-node remove <NODE_ID>
```

Wait until the operation has successfully finished. Afterward, the storage node is removed from the cluster.

This can be checked again with the `{{ cliname }}` command line tool.

```bash title="List storage nodes"
{{ cliname }} storage-node list --cluster-id=<CLUSTER_ID>
```
