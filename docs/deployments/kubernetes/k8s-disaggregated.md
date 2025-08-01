---
title: "Disaggregated Setup (Kubernetes)"
weight: 50000
---

Technically, the disaggregated setup in Kubernetes is very similar to the [Hyper-Converged](k8s-hyperconverged.md) one.
However, it is substantially different from the default disaggregated setup
on [Plain Linux](../install-simplyblock/install-sp.md).

There are generally two variants of this option:

- Locate storage nodes (sn-s) in the same cluster as the compute workloads, but on distinct, dedicated worker nodes,
  preferably a separate node pool
- Create and maintain a separate Kubernetes storage plane cluster. Storage from this cluster can be attached to other
  Kubernetes clusters using the CSI driver. It is also possible to attach storage to Proxmox clusters or baremetal / 
  plain Linux initiators.

The use of Kubernetes for hosting disaggregated storaging clusters makes sense for users who want all workloads,
including stateful ones, to be entirely managed from within Kubernetes.

To install simplyblock in a disaggregated fashion, follow the [Hyper-Converged Deployment](k8s-hyperconverged.md)
instructions but do not set the `storagenode.coresPercentage` parameter.

As the storage node is dedicated to simplyblock storage, cores will automatically be split accordingly between the
operating system and simplyblock containers.
