---
title: "Kubernetes CSI"
weight: 30300
---

Simplyblock integrates seamlessly with Kubernetes through its Container Storage Interface (CSI) driver, enabling dynamic
provisioning and management of high-performance Logical Volumes (LVs) directly from Kubernetes workloads. This
documentation section provides detailed guidance on how to handle the full lifecycle of simplyblock-backed volumes in
Kubernetes, including provisioning, removal, expansion, snapshotting, cloning, and applying performance controls.

By leveraging the Simplyblock CSI driver, administrators and developers can automate storage operations with standard
Kubernetes objects, ensuring efficient and reliable storage for stateful workloads running on simplyblock clusters.
