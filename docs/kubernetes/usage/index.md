---
title: "Usage"
description: "Use simplyblock volumes on Kubernetes through the simplyblock CSI driver: StorageClasses, provisioning, QoS, encryption, placement, snapshots, clones, and expansion."
weight: 30000
---

Simplyblock integrates with Kubernetes through its Container Storage Interface (CSI) driver, enabling dynamic
provisioning and management of high-performance logical volumes directly from Kubernetes workloads. The driver is
deployed by the Simplyblock Operator as the `SimplyblockDriver` resource, under the driver name `csi.simplyblock.io`.

Every volume is provisioned from a `StoragePool` of a `StorageCluster`. The operator creates a StorageClass named
`simplyblock-<namespace>-<cluster>` for the default pool of each cluster, and further StorageClasses are authored for
additional pools. This section covers the full lifecycle of simplyblock-backed volumes in Kubernetes.

- [Storage Class](storage-class.md)
- [Provisioning](provisioning.md)
- [Volume Encryption](volume-encryption.md)
- [Automatic Volume Placement](volume-placement.md)
- [Snapshotting](snapshotting.md)
- [Cloning](cloning.md)
- [Expanding](expanding.md)
- [Removing](removing.md)
- [Defining Quality of Service](quality-of-service.md)
