---
title: "Install Simplyblock on Kubernetes"
weight: 20100
---

Three Simplyblock components can be installed into existing Kubernetes environments:
- CSI driver: It automates the lifecycle of Kubernetes PVCs, including snapshotting, deleting, resizing and cloning them.
  PVCs can be managed and connected to Simplyblock Clusters in Kubernetes as well as Docker-based Simplyblock Clusters.
- Control Plane: In Kubernetes-based deployments, the Simplyblock Control Plane can be installed into a
  Kubernetes cluster. 
- Storage Nodes: In Kubernetes-based deployments, the Simplyblock Control Plane can be installed into
  Kubernetes clusters. It is possible to use separate workers or even separate clusters as storage nodes or 
  to combine them with compute.



The Simplyblock CSI driver can be used with an existing disaggregated cluster, for further information on how to install
the CSI driver, see: [Install Simplyblock CSI](install-csi.md).

However, it is also possible to install a simplyblock storage cluster into an existing kubernetes cluster together with
the CSI driver (supporting both [Hyper-converged](k8s-storage plane.md) and [Disaggregated](k8s-control plane.md)
Kubernetes deployments).

Additionally, it can also be used with a simplyblock storage cluster installed into another Kubernetes cluster, which is
dedicated to the storage. In this case, the CSI driver connects from the client Kubernetes clusters to the storage
Kubernetes clusters and only consumes the storage.
