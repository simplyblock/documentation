---
title: "Install Simplyblock Storage Cluster"
weight: 30100
---

<!-- include: install intro -->
--8<-- "bare-metal-intro.md"

!!! warning
    Simplyblock strongly recommends to set up individual networks for the storage plane and control plane traffic.  

## Amazon Elastic Kubernetes Service (EKS)

!!! info
    If simplyblock is to be installed into Amazon EKS, the [Kubernetes documentation](../kubernetes/index.md) section
    has the necessary step-by-step guide.

<!-- include: install control plane documentation -->
--8<-- "install-control-plane.md"

<!-- include: install storage plane (bare metal) documentation -->
--8<-- "install-storage-plane-bare-metal.md"
