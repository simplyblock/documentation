---
title: "Cluster"
description: "Operate a simplyblock storage cluster outside Kubernetes: upgrade it, group its storage nodes into failure domains, and set where volume data is placed."
weight: 10100
---

A storage cluster is operated through the `{{ cliname }}` command line interface, which talks to the control plane.
The topology settings of a cluster, its failure domains and its node affinity, are cluster-level properties and are
read whenever the placement of data is decided.

| Topic                                          | Purpose                                                                          |
|------------------------------------------------|----------------------------------------------------------------------------------|
| [Upgrading a Cluster](cluster-upgrade.md)      | Upgrading the control plane and the storage plane of a running cluster.          |
| [Managing Failure Domains](failure-domains.md) | Grouping storage nodes into fault groups, so that chunks are spread across them. |
| [Configure Node Affinity](node-affinity.md)    | Keeping the data of a logical volume on the storage node that owns it.           |
