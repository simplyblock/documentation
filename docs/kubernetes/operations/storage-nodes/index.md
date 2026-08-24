---
title: "Storage Nodes"
description: "Operate the storage nodes of a simplyblock cluster on Kubernetes: request node actions, move a node to another worker, remove it, or replace it."
weight: 10200
---

An operation against a single storage node is requested with a `StorageNodeOps` resource, which names the target
`StorageNode`, carries the action, and is driven to completion by the Simplyblock Operator. Taking a worker out for
maintenance needs no resource at all, since a cordon or a drain is picked up by the operator on its own.

| Topic                                                       | Purpose                                                                           |
|-------------------------------------------------------------|-----------------------------------------------------------------------------------|
| [Storage Node Actions](storage-node-actions.md)             | Requesting an action against one storage node with a `StorageNodeOps` resource.   |
| [Replacing a Storage Node](replacing-a-storage-node.md)     | Choosing between a migration and a removal when hardware is replaced.             |
| [Migrating a Storage Node](migrating-a-storage-node.md)     | Moving a storage node onto a different worker, keeping its identity and devices.  |
| [Removing a Storage Node](removing-a-storage-node.md)       | Draining the volumes off a storage node and taking it out of the cluster.         |
| [Coordinated Worker Node Drain](node-drain-coordination.md) | Protecting storage availability while a Kubernetes worker is cordoned or drained. |
