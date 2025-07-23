---
title: "Kubernetes"
weight: 20100
---

Before installing Simplyblock for Kubernetes, the [control plane](../install-simplyblock/install-cp.md) must be installed and ready-to-use.

The Simplyblock CSI driver can be [installed](install-csi.md) used with an existing dissaggregated cluster. 

However, it is also possible to install a Simplyblock storage cluster into an existing kubernetes cluster together with the CSI driver (supporting both [hyperconverged deployment](k8s-hyperconverged.md) and [disaggregated deployment on kubernetes](k8s-disaggregated.md)) - or to install a Simplyblock storage cluster into another kubernetes cluster, which is dedicated to the storage - [disaggregated deployment on kubernetes](k8s-disaggregated.md) - and then install and connect the CSI driver from other kubernetes clusters only consuming the storage.



