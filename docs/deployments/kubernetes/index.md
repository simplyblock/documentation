---
title: "Kubernetes"
weight: 20100
---

Before installing Simplyblock for Kubernetes, the [Control Plane](../install-simplyblock/install-cp.md) must be
installed and ready-to-use.

The Simplyblock CSI driver can be used with an existing disaggregated cluster, for further information on how to install
the CSI driver, see: [Install Simplyblock CSI](install-csi.md).

However, it is also possible to install a simplyblock storage cluster into an existing kubernetes cluster together with
the CSI driver (supporting both [Hyper-converged](k8s-hyperconverged.md) and [Disaggregated](k8s-disaggregated.md)
Kubernetes deployments).

Additionally, it can also be used with a simplyblock storage cluster installed into another Kubernetes cluster, which is
dedicated to the storage. In this case, the CSI driver connects from the client Kubernetes clusters to the storage
Kubernetes clusters and only consumes the storage.
