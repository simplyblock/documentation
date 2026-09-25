---
title: "Scaling"
description: "Scale a simplyblock cluster on Kubernetes by adding workers with a growth ClusterDeploymentConfig, and control how many are provisioned at a time."
weight: 10400
---

A storage cluster scales out by adding Kubernetes workers as storage nodes, which adds capacity and performance at the
same time. New workers are described in a growth `ClusterDeploymentConfig` that names the existing cluster, either
written by hand or drafted by a discovery run. The cluster keeps serving I/O throughout, and the data is rebalanced onto
the new devices afterward.

## Topics

| Topic                                                       | Purpose                                                                    |
|-------------------------------------------------------------|----------------------------------------------------------------------------|
| [Expanding a Storage Cluster](expanding-storage-cluster.md) | Adding storage nodes to a running cluster and following their integration. |
| [Parallel Storage Node Addition](parallel-node-addition.md) | Provisioning several workers concurrently instead of one after another.    |
