---
title: "Edge Clusters"
description: "Small simplyblock storage clusters at edge sites, with one or two nodes, managed by a central control plane in the datacenter."
weight: 10105
---

{{ experimental }}

An edge cluster is a small simplyblock storage cluster at an edge site, such as a branch office, a factory, or a
store. It consists of one or two storage nodes on the Kubernetes cluster of the site. The edge cluster does not run a
control plane of its own. It is managed by a central simplyblock control plane in the datacenter (the hub), which
can manage many edge clusters.

Each edge site runs only the Simplyblock Operator in the managed profile, the CSI driver, and the storage nodes. The
footprint of a control plane and its FoundationDB cluster stays in the datacenter.

The section covers:

- **[Architecture](architecture.md):** Components, data and control flow, and the high-availability model of one-node
  and two-node edge clusters.
- **[Deployment Preparation](deployment-preparation.md):** Hardware, devices, network links and ports, Kubernetes
  prerequisites, and the connection to the hub.
- **[Deployment](deployment.md):** Preparing the hub, installing the operator at the edge, discovering devices,
  creating the storage cluster, and verifying it.
- **[Operations](operations.md):** Monitoring, failure behavior, maintenance, upgrades, and troubleshooting.

!!! warning "Two-node edge clusters are a preview"
    One-node edge clusters can be deployed with this release. Two-node edge clusters with automatic failover between
    the nodes depend on an arbitration protocol that is not released yet. The pages describe the intended behavior
    and mark it as a preview.
