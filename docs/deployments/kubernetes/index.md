---
title: "Install Simplyblock on Kubernetes"
weight: 20100
---

Three simplyblock components can be installed into existing Kubernetes environments:

- **CSI Driver**: It automates the lifecycle of Kubernetes PVCs, including snapshotting, deleting, resizing and cloning
  them. PVCs can be managed and connected to simplyblock clusters in Kubernetes as well as Docker-based Simplyblock
  Clusters.
- **Control Plane**: In Kubernetes-based deployments, the simplyblock control plane can be installed into a Kubernetes
  cluster.
- **Storage Plane**: In Kubernetes-based deployments, the simplyblock storage plane can be installed into Kubernetes
  clusters. It is possible to use separate workers or even separate clusters as storage nodes or to combine them with
  compute.

The Simplyblock CSI Driver can be separately installed to connect to any disaggregated storage cluster
(external to the Kubernetes cluster, under docker or kubernetes), see: [Install Simplyblock CSI](install-csi.md).
 
