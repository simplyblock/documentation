---
title: "Storage Nodes"
description: "Operate the storage nodes of a simplyblock cluster outside Kubernetes: restart a node, replace or relocate it, and find the node serving a failover path."
weight: 10200
---

A storage node is operated with the `{{ cliname }} storage-node` commands. Most of what a node needs is automatic: an
unavailable node is restarted by the control plane, and its logical volumes are served through their failover paths
while it is gone. What is left are the deliberate operations, and the lookups needed before one is started.

| Topic                                                                         | Purpose                                                                     |
|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| [Stopping and Manually Restarting a Storage Node](manual-restarting-nodes.md) | Restarting a node by hand when the automatic restart did not happen.        |
| [Replacing a Storage Node](replacing-storage-node.md)                         | Choosing between a relocation and a replacement when hardware is exchanged. |
| [Migrating a Storage Node](migrating-storage-node.md)                         | Moving a storage node onto a different host, keeping its identity.          |
| [Finding the Secondary Node](find-secondary-node.md)                          | Determining which node holds the failover path of a logical volume.         |
| [Linux Block Device Operations](lblk-device-operations.md)                    | Day-2 operations specific to a cluster in the `lblk` mode.                  |
