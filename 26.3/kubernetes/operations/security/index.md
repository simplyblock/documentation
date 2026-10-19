---
title: "Security"
description: "Secure a simplyblock deployment on Kubernetes: authenticate and encrypt the NVMe-oF transport, encrypt volumes, and isolate tenants from each other."
source: "https://docs.simplyblock.io/latest/kubernetes/operations/security/"
---

# Security

Security covers three layers of the storage stack. The NVMe-oF transport between an initiator and a storage node is
authenticated and encrypted, a volume is encrypted at rest with keys that can be held outside the cluster, and the
tenants of a cluster are isolated from each other through separate storage pools and credentials.

| Topic                                                              | Purpose                                                           |
|--------------------------------------------------------------------|-------------------------------------------------------------------|
| [Host Authentication and Encryption](authentication-encryption.md) | Authenticating and encrypting the NVMe-oF transport of a cluster. |
| [Multi-Tenancy](multi-tenancy.md)                                  | Isolating tenants from each other within one storage cluster.     |
| [Volume Encryption](../../usage/volume-encryption.md)              | Encrypting the data of a single volume at rest.                   |
