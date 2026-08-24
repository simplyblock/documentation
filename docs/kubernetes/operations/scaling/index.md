---
title: "Scaling"
description: "Scale a simplyblock cluster on Kubernetes by enrolling additional workers as storage nodes, and control how many of them are provisioned at a time."
weight: 10300
---

A storage cluster scales out by enrolling additional Kubernetes workers as storage nodes, which adds capacity and
performance at the same time. The cluster keeps serving I/O throughout, and the data is rebalanced onto the new devices
afterward.

| Topic                                                       | Purpose                                                                    |
|-------------------------------------------------------------|----------------------------------------------------------------------------|
| [Expanding a Storage Cluster](expanding-storage-cluster.md) | Adding storage nodes to a running cluster and following their integration. |
| [Parallel Storage Node Addition](parallel-node-addition.md) | Provisioning several workers concurrently instead of one after another.    |
