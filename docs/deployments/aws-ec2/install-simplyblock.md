---
title: "Install Simplyblock Storage Cluster"
weight: 30100
---

<!-- include: install intro -->
{% include 'bare-metal-intro.md' %}

!!! warning
    Simplyblock strongly recommends setting up individual networks for the storage plane and control plane traffic.  

!!! recommendation
    Simplyblock recommends using AlmaLinux, Rocky, or Red Hat Enterprise Linux on Amazon EC2 machines. Amazon Linux
    does not support native NVMe-oF Multipathing. While it is possible to use DM-MPIO (device manager multipathing)
    usage is not as straight forward as possible.

## Amazon Elastic Kubernetes Service (EKS)

!!! info
    If simplyblock is to be installed into Amazon EKS, the [Kubernetes documentation](../kubernetes/index.md) section
    has the necessary step-by-step guide.

<!-- include: install control plane documentation -->
{% include 'install-control-plane.md' %}

<!-- include: install storage plane (bare metal) documentation -->
{% include 'install-storage-plane-bare-metal.md' %}

Now that the cluster is ready, it is time to install the [Kubernetes CSI Driver](install-simplyblock-csi.md) or learn
how to use the simplyblock storage cluster to
[manually provision logical volumes](../../usage/baremetal/provisioning.md).
