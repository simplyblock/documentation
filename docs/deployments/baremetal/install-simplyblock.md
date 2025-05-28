---
title: "Install Simplyblock Storage Cluster"
weight: 30100
---

<!-- include: install intro -->
{% include 'bare-metal-intro.md' %}

!!! danger
    Simplyblock requires a fully redundant network interconnect, implemented via a solution such as LACP or Static
    LAG. Failing to provide that may cause data corruption or data loss in case of network issues. For more information
    see the [Network Considerations](../../deployments/deployment-planning/network-considerations.md)
    section.

<!-- include: install control plane documentation -->
{% include 'install-control-plane.md' %}

<!-- include: install storage plane (bare metal) documentation -->
{% include 'install-storage-plane-bare-metal.md' %}

Now that the cluster is ready, it is time to install the [Kubernetes CSI Driver](install-simplyblock-csi.md) or learn
how to use the simplyblock storage cluster to
[manually provision logical volumes](../../usage/baremetal/provisioning.md).
