---
title: "Storage Pooling"
description: "Simplyblock aggregates the devices of all storage nodes into one storage cluster and divides it into storage pools, which carry limits and volume defaults."
weight: 30000
---

Storage pooling aggregates many storage devices into a single, unified storage resource. Instead of assigning
devices to specific applications, which leaves capacity stranded, simplyblock combines the devices of all storage
nodes of a cluster and allocates capacity to volumes on demand.

Simplyblock pools storage on two levels:

- **The storage cluster** combines the devices of all its storage nodes, NVMe devices or
  [Linux block devices](linux-block-devices.md), into one distributed capacity. Adding devices or nodes expands it
  without interrupting operations.
- **Storage pools** divide a cluster logically, for example, per tenant, team, or workload type. Every volume belongs
  to one pool. A pool reserves no devices, so all pools share the capacity and performance of the whole cluster.

A storage pool carries the settings for its volumes:

- **Limits:** A capacity limit for the pool, and IOPS and throughput caps for the pool as a whole and per volume.
- **Volume defaults:** Encryption, the [service class](../storage-performance-and-qos.md#service-classes), the number
  of namespaces per NVMe-oF subsystem, client-side compression and deduplication, and the transport (TCP or RDMA).
- **Security:** NVMe-oF host authentication (DH-HMAC-CHAP) and transport encryption (TLS), applied to every volume
  of the pool (see [NVMe over Fabrics Security](nvmf-security.md)).

On Kubernetes, a pool is a `StoragePool` resource and comes with its own StorageClass (see
[Storage Classes](../../kubernetes/usage/storage-class.md)).

!!! important
    Because the front storage is virtualized separately from the back storage, a pool is not bound to particular
    nodes or devices. Volumes of any size up to the per-volume limit can be carved from it, and its capacity and
    performance grow with the cluster.

    This conflicts with data locality, so data locality is turned off by default and data is distributed for a fully
    balanced load. When enabled, data locality is applied on a best-effort basis (see
    [Data Locality](../storage-performance-and-qos.md#data-locality)).
