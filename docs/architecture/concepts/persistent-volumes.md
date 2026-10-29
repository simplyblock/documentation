---
title: "Persistent Volumes"
description: "How Kubernetes persistent volumes map onto simplyblock logical volumes: provisioning, access modes, reclaim policies, and multipath NVMe-oF connections."
weight: 30200
---

Persistent Volumes (PVs) in Kubernetes provide storage whose lifecycle is independent of individual pods. Unlike
ephemeral storage, which ends with its pod, the data of a PV survives pod restarts and rescheduling, which lets
stateful applications run reliably in a Kubernetes cluster.

Kubernetes separates the request for storage from its provisioning. A **PersistentVolumeClaim (PVC)** is the
request an application makes, and a **PersistentVolume (PV)** is the storage that fulfills it. A **StorageClass**
describes how a PV is provisioned.

Key characteristics of persistent volumes include:

- **Decoupled storage management:** PVs exist independently of pods, so storage persists when pods are deleted or
  rescheduled.
- **Dynamic provisioning:** A claim against a StorageClass makes the CSI driver create a matching volume
  automatically.
- **Access modes:** Define how pods may use a volume, for example, `ReadWriteOnce` (one worker) or `ReadWriteMany`
  (many workers at once).
- **Reclaim policies:** Decide whether a volume is deleted or retained once its claim is removed.

## Persistent Volumes in Simplyblock

Each simplyblock PV is backed by a [logical volume](logical-volumes.md), which is created in the
[storage pool](storage-pooling.md) of the StorageClass. The logical volume is an NVMe namespace in an NVMe-oF
subsystem. The CSI node plugin connects it to the worker of the consuming pod over NVMe/TCP or NVMe/RoCE, with one
path to every storage node that serves the volume: the optimized path to the primary and standby paths to the
secondary and tertiary. The volume is handed to the pod as a raw block device or with a filesystem.

| Access mode     | Served by                                                            |
|-----------------|----------------------------------------------------------------------|
| `ReadWriteOnce` | Any simplyblock StorageClass, as a block device or with a filesystem |
| `ReadWriteMany` | StorageClasses with [pNFS](pnfs.md) only, as shared file storage     |

See [Provisioning](../../kubernetes/usage/provisioning.md) and [Storage Classes](../../kubernetes/usage/storage-class.md)
for the usage.
