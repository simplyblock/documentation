---
title: "Cluster"
description: "Operate a simplyblock storage cluster on Kubernetes: request cluster actions, restart it node by node, upgrade it, and set its data placement."
weight: 10100
---

A storage cluster is operated through its `StorageCluster` resource. A cluster-wide action is requested by setting
`spec.action`, and the Simplyblock Operator calls the control plane and reports the outcome in the status of the
resource. The topology settings of a cluster, its failure domains and its node affinity, are properties of the same
resource and are read when data placement is decided.

| Topic                                          | Purpose                                                                          |
|------------------------------------------------|----------------------------------------------------------------------------------|
| [Storage Cluster Actions](cluster-actions.md)  | Requesting a cluster-wide action through `spec.action` on the `StorageCluster`.  |
| [Rolling Restart](rolling-restart.md)          | Restarting every storage node of a cluster, one node at a time.                  |
| [Upgrading a Cluster](cluster-upgrade.md)      | Upgrading the Helm chart, and rolling the storage plane node by node afterward.  |
| [Managing Failure Domains](failure-domains.md) | Grouping storage nodes into fault groups, so that chunks are spread across them. |
| [Configuring Node Affinity](node-affinity.md)  | Keeping the data of a logical volume on the storage node that owns it.           |
