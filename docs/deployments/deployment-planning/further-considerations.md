---
title: "Further Considerations"
weight: 30400
---

## System Compatibility

Simplyblock contains two major components, the control plane and the storage plane.

- For the control plane, simplyblock **requires** x86-64 (AMD64 / Intel 64) compatible CPUs.
- For the storage plane, simplyblock **supports** x86-64 (AMD64 / Intel 64) or ARM64 (AArch64) compatible CPUs.

!!! info
    A single storage plane cluster can be set up from both x86-64 and ARM64 CPUs. However, simplyblock recommends to
    build a storage plane from a single CPU architecture. This is especially important to consider when running
    hyper-converged or in a hybrid setup.

In terms of operating system, simplyblock requires a Red Hat-based Linux distribution version 9 (including Rocky Linux and Alma Linux) 
for the control plane nodes and disaggregated storage nodes (docker-swarm) and recommends a Linux kernel 5.9 or later. 

For storage nodes running in Kubernetes, any Linux distribution (RHEL-based, Debian-based, Talos) can be used. For more
information, see the supported [Linux Distributions Matrix](../../reference/supported-linux-distributions.md).

For any client host, the `nvme-tcp` module must be loaded and support [NVMe Multipathing](https://docs.kernel.org/admin-guide/nvme-multipath.html){:target="_blank" rel="noopener"}.

## Storage Considerations

Simplyblock is an NVMe-first storage architecture and requires NVMe device with exclusive access. Simplyblock **does
not** support individual partitions, but requires full and exclusive access to the physical or virtual NVMe device.
