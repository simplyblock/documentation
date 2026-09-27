---
title: "Storage Nodes"
description: "Operate the storage nodes of a simplyblock cluster on Kubernetes: request node operations, move a node to another worker, remove it, or replace it."
weight: 10200
---

A storage node is described by its `StorageNode` resource, one per worker and NUMA socket slot, and operated through
`StorageNodeOps` resources. Each `StorageNodeOps` names the target `StorageNode`, carries one action, and is driven to
completion by the Simplyblock Operator. Two operations are raised by the operator itself: a `HostMaintenance` when the
worker of a node is cordoned, and a `Remove` when a `StorageNode` that holds data is deleted.

A single device of a node is restarted with a `StorageDeviceOps` resource, as described in
[Storage Node Actions](storage-node-actions.md#restarting-a-storage-device).

## Topics

| Topic                                                           | Purpose                                                                                       |
|-----------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| [Storage Node Actions](storage-node-actions.md)                 | The `StorageNodeOps` kind: the target node, the actions, the locking, the tracking.           |
| [Shutting Down a Storage Node](shutting-down-a-storage-node.md) | Stopping one node while the rest of the cluster keeps serving I/O.                            |
| [Restarting a Storage Node](restarting-a-storage-node.md)       | Stopping and starting one node, optionally forced and reattaching its volumes.                |
| [Suspending a Storage Node](suspending-a-storage-node.md)       | Stopping new volumes from being placed on a node that keeps running.                          |
| [Resuming a Storage Node](resuming-a-storage-node.md)           | Returning a suspended node to normal service.                                                 |
| [Replacing a Storage Node](replacing-a-storage-node.md)         | Choosing between a migration and a removal when hardware is replaced.                         |
| [Migrating a Storage Node](migrating-a-storage-node.md)         | Moving a storage node onto a different worker, keeping its identity and devices.              |
| [Removing a Storage Node](removing-a-storage-node.md)           | Draining the volumes off a storage node and taking it out of the cluster.                     |
| [Coordinated Worker Node Drain](node-drain-coordination.md)     | The `HostMaintenance` operation that protects storage while a worker is cordoned and drained. |
