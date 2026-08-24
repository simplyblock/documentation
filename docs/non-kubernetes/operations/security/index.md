---
title: "Security"
description: "Secure a simplyblock deployment outside Kubernetes: authenticate and encrypt the NVMe-oF transport, encrypt volumes, and isolate tenants from each other."
weight: 10700
---

Security covers three layers of the storage stack. The NVMe-oF transport between an initiator and a storage node is
authenticated and encrypted, a logical volume is encrypted at rest, and the tenants of a cluster are isolated from each
other through separate storage pools and credentials.

| Topic                                                              | Purpose                                                           |
|--------------------------------------------------------------------|-------------------------------------------------------------------|
| [Host Authentication and Encryption](authentication-encryption.md) | Authenticating and encrypting the NVMe-oF transport of a cluster. |
| [Multi-Tenancy](multi-tenancy.md)                                  | Isolating tenants from each other within one storage cluster.     |
| [Volume Encryption](../../usage/encrypting.md)                     | Encrypting the data of a single logical volume at rest.           |
