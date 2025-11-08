---
title: "Install Simplyblock on Kubernetes"
weight: 20100
---

Three simplyblock components can be installed into existing Kubernetes environments:

- [**Control Plane**](k8s-control-plane.md): In Kubernetes-based deployments, the simplyblock control plane can be installed into a Kubernetes
  cluster. This is always the first step. 
- [**Storage Plane**](k8s-storage-plane.md): In Kubernetes-based deployments, the simplyblock storage plane can be installed into Kubernetes
  clusters once the control plane is ready. It is possible to use separate workers or even separate clusters as storage nodes or to combine them with
  compute. The storage plane installs also installs necessary components of the CSI driver, no extra helm chart is needed.

  In general, all Kubernetes deployments follow the same procedure. However, here are some specifics worth to mention around [openshift](./openshift.md) and [talos](./talos.md).
  Also, if you want to use volume-based e2e encryption with customer-managed keys, please see [here](./volume-encryption.md). 
  
The Simplyblock [**CSI Driver**](./install-csi.md) can also be separately installed to connect to any external storage cluster
(this can be another hyperconverged or disaggregated cluster under Kubernetes or a Linux-based disaggregated deployment), see: [Install Simplyblock CSI](install-csi.md).
 
