---
title: "Multi-Tenancy"
weight: 30100
---

Simplyblock is designed to support secure and efficient multitenancy, enabling multiple independent tenants to share the
same physical infrastructure without compromising data isolation, performance guarantees, or security. This capability
is essential in cloud environments, managed services, and enterprise deployments where infrastructure is consolidated
across internal departments or external customers.

## Storage Isolation

Simplyblock provides multiple layers of isolation between multiple tenants depending on requirements and how tenants
are defined.

### Storage Pool Isolation

If tenants are expected to have multiple volumes, it might be required to define the overall available storage quota
a tenant can access and assign to volumes. Hence, simplyblock enables to create one storage pool with a maximum capacity
per tenant. All volumes for this tenant should be created in their respective storage pool and automatically count
towards the storage quota.

### Logical Volume Isolation

If a tenant is expected to have only one volume or strong isolation between volumes is required, each logical volume,
can be seen as fully isolated at the storage layer. Access to volumes is tightly controlled, and each LV is only exposed
to the workloads explicitly granted access.

## Quality of Service (QoS)

To prevent noisy neighbor effects and ensure fair resource allocation, simplyblock supports per-volume Quality of
Service (QoS) configurations. Administrators can define IOPS and bandwidth limits for each logical volume, providing
predictable performance and protecting tenants from resource contention.

Quality of service is available for
[Kubernetes-based installation quality of service](../../usage/simplyblock-csi/quality-of-service.md) and
[plain Linux installation quality of service](../../usage/baremetal/quality-of-service.md).

## Encryption and Data Security

All data is protected with encryption at rest, using strong AES-based cryptographic algorithms. Encryption is applied at
the volume level, ensuring that tenant data remains secure and inaccessible to other users—even at the physical storage
layer. Encryption keys are logically separated between tenants to support strong cryptographic isolation.

Encryption is available for [Kubernetes-based installation encryption](../../usage/simplyblock-csi/encrypting.md) and
[plain Linux installation encryption](../../usage/baremetal/encrypting.md).
