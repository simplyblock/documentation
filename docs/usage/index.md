---
title: "Usage"
weight: 10400
---

Simplyblock provides powerful tools for managing Logical Volumes (LVs) through its command-line interface
({{ variables.cliname }}) and Kubernetes CSI driver, enabling seamless storage operations in cloud-native and
enterprise environments. Whether working in a standalone environment or integrating with Kubernetes, these tools allow
users to provision, unprovision, expand, snapshot, and clone logical volumes efficiently.

The `{{ variables.cliname }}` utility offers direct control over storage management via the command line, making it
ideal for administrators who need fine-grained operational control. Meanwhile, the Kubernetes CSI driver enables
automated volume provisioning and lifecycle management within containerized workloads. This section provides detailed
guidance on using both methods to perform essential storage operations, ensuring scalable and resilient data management
within simplyblock’s distributed storage architecture.
