---
title: "Disaggregated Setup (Kubernetes)"
weight: 50000
---

Technically, the disaggregated setup in Kubernetes is very similar to the [hyperconverged](k8s-hyperconverged.md) one. 
However, it is substantially different from the default disaggregated setup on [plain Linux](../install-simplyblock/install-sn.md).

There are generally two variants of this options:
* locate storage nodes (sn-s) in the same cluster as the compute workloads, but on distinct, dedicated worker nodes (hybrid setup)
* create and maintain a separate k8s storage cluster; storage from this cluster can be attached to other clusters using the CSI driver. It is also possible to attache storage to ProxMox clusters or baremetal-Linux.

The use of Kubernetes for hosting disaggregated storaging clusters makes sense for users, who want all workloads, including stateful ones, to be entirely managed from within Kubernetes. 

Follow the [hyperconverged setup](k8s-hyperconverged.md) guideline, but do not set the _storagenode.coresPercentage_ parameter. As the node is dedicated to Simplyblock storage, cores will be split automatically accordingly between the operating system and Simplyblock containers.
