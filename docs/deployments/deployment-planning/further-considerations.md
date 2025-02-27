---
title: "Further Considerations"
weight: 30300
---

## System Compatibility

Simplyblock contains two major components, the control plane and the storage plane.

- For the control plane, simplyblock **requires** x86-64 (AMD64 / Intel 64) compatible CPUs.
- For the storage plane, simplyblock **supports** x86-64 (AMD64 / Intel 64) or ARM64 (AArch64) compatible CPUs.

!!! info
    A single storage plane cluster can be set up from both x86-64 and ARM64 CPUs. However, simplyblock recommends to
    build a storage plane from a single CPU architecture. When operating a hybrid storage cluster with Kubernetes
    a mixed CPU architecture should be limited to one CPU architecture for the disaggregated portion of the storage
    cluster and one architecture for the Kubernetes worker nodes.

In terms of operating system, simplyblock supports Red Hat-based Linux distribution and recommends a Linux kernel 5.9
or later.

## Storage Considerations

Simplyblock is an NVMe-first storage architecture and requires NVMe device with exclusive access. Simplyblock **does
not** support individual partitions, but requires full and exclusive access to the physical or virtual NVMe device.
