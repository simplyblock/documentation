---
title: "Persistent Volumes"
weight: 30200
---

Persistent Volumes (PVs) in Kubernetes provide a mechanism for managing storage resources independently of individual
Pods. Unlike ephemeral storage, which is tied to the lifecycle of a Pod, PVs ensure data persistence across Pod restarts
and rescheduling, enabling stateful applications to function reliably in a Kubernetes cluster.

In Kubernetes, storage resources are abstracted through the Persistent Volume framework, which decouples storage
provisioning from application deployment. A **Persistent Volume (PV)** represents a piece of storage that has been
provisioned in the cluster, while a **Persistent Volume Claim (PVC)** is a request for storage made by an application.

Key characteristics of Persistent Volumes include:

- **Decoupled Storage Management:** PVs exist independently of Pods, allowing storage to persist even when Pods are deleted or rescheduled.
- **Dynamic and Static Provisioning:** Storage can be provisioned manually by administrators (static provisioning) or automatically by storage classes (dynamic provisioning).
- **Access Modes:** PVs support multiple access modes, such as ReadWriteOnce (RWO), ReadOnlyMany (ROX), and ReadWriteMany (RWX), defining how storage can be accessed by Pods.
- **Reclaim Policies:** When a PV is no longer needed, it can be retained, recycled, or deleted based on its configured reclaim policy.
- **Storage Classes:** Kubernetes allows administrators to define different types of storage using StorageClasses, enabling automated provisioning of PVs based on workload requirements.
