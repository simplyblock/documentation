---
title: "Scaling"
description: "Scale a simplyblock cluster outside Kubernetes by adding capacity to a storage pool, so that its logical volumes can grow beyond the current limit."
source: "https://docs.simplyblock.io/latest/non-kubernetes/operations/scaling/"
---

# Scaling

A cluster scales out by adding storage nodes, and it scales its provisioning limit by growing a storage pool. Both are
online operations, and the data is rebalanced onto the new capacity afterward. Adding the storage nodes themselves is
part of the deployment, described under
[Deploy a Storage Plane](../../installation/install-sp.md).

| Topic                                                 | Purpose                                                    |
|-------------------------------------------------------|------------------------------------------------------------|
| [Expanding a Storage Pool](expanding-storage-pool.md) | Raising the capacity limit of a storage pool of a cluster. |
