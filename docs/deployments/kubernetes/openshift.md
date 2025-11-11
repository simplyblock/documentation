---
title: "OpenShift"
weight: 40100
---

When installing simplyblock on OpenShift, the process is very similar to Kubernetes, with one key difference,
OpenShift requires explicitly granting the privileged Security Context Constraint (SCC) to service accounts to enable
storage and SPDK operations.

!!! info
    In OpenShift deployments, not all worker nodes must host storage components.
    Simplyblock uses node labels to identify nodes that participate in the storage cluster.
    You can isolate storage workloads on dedicated worker nodes or node pools.

## Prerequisites

Ensure your OpenShift cluster is operational and that you have administrator privileges.

Before deploying Simplyblock components, grant the required SCC permissions:

```bash title="Grant SCC permissions"
oc adm policy add-scc-to-group privileged system:serviceaccounts
```

This step is mandatory to allow SPDK and storage-related containers to run with the privileges required for NVMe device
access.
