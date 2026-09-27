---
title: "Cluster"
description: "Operate a simplyblock storage cluster on Kubernetes: request cluster operations, restart it node by node, upgrade it, and set its data placement."
weight: 10100
---

A storage cluster is described by its `StorageCluster` resource and operated through `StorageClusterOps` resources.
Each `StorageClusterOps` names the cluster, carries one action, and is driven to completion by the
Simplyblock Operator, which reports the progress in the status of the operation. The topology settings of a cluster,
its failure domains and its node affinity, are properties of the `StorageCluster` itself and are read when data
placement is decided.

The operation pattern that every Ops kind shares is described in [Operations](../index.md#the-operation-pattern).

## Topics

| Topic                                                         | Purpose                                                                          |
|---------------------------------------------------------------|----------------------------------------------------------------------------------|
| [Storage Cluster Actions](cluster-actions.md)                 | The `StorageClusterOps` kind: its actions, parameters, steps, and tracking.      |
| [Activating a Storage Cluster](activating-a-cluster.md)       | Making a cluster serve I/O, and the gates an activation waits on.                |
| [Shutting Down a Storage Cluster](shutting-down-a-cluster.md) | Suspending the whole cluster and taking all of its volumes offline.              |
| [Starting a Storage Cluster](starting-a-cluster.md)           | Bringing a suspended cluster back into service.                                  |
| [Restarting a Storage Cluster](restarting-a-cluster.md)       | Sequencing a shutdown and a start in one operation.                              |
| [Rolling Restart](rolling-restart.md)                         | Restarting every storage node of a cluster, one node at a time.                  |
| [Upgrading a Cluster](cluster-upgrade.md)                     | Upgrading the operator, the control plane, and the storage plane.                |
| [Managing Failure Domains](failure-domains.md)                | Grouping storage nodes into fault groups, so that chunks are spread across them. |
| [Configuring Node Affinity](node-affinity.md)                 | Keeping the data of a logical volume on the storage node that owns it.           |
