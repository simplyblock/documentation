---
title: "Security"
description: "Secure a simplyblock deployment on Kubernetes: authenticate the NVMe-oF transport per storage pool, encrypt volumes, and isolate tenants from each other."
weight: 10700
---

Security covers three layers of the storage stack. The NVMe-oF transport between an initiator and a storage node is
restricted to allowed hosts and authenticated per `StoragePool`, a volume is encrypted at rest with keys that can be
held outside the cluster, and the tenants of a cluster are isolated from each other through separate storage pools,
namespaces, and Kubernetes RBAC.

| Topic                                                              | Purpose                                                             |
|--------------------------------------------------------------------|---------------------------------------------------------------------|
| [Host Authentication and Encryption](authentication-encryption.md) | Restricting and authenticating the NVMe-oF transport of a pool.     |
| [Multi-Tenancy](multi-tenancy.md)                                  | Isolating tenants from each other with pools, namespaces, and RBAC. |
| [Volume Encryption](../../usage/volume-encryption.md)              | Encrypting the data of a volume at rest.                            |
