---
title: "Deployments"
description: "Deployments: Simplyblock is a highly flexible storage solution Different initiator (host) drivers (Kubernetes CSI, Proxmox, OpenStack) are available."
weight: 10300
---

Simplyblock is a highly flexible storage solution. 

Different initiator (host) drivers (Kubernetes CSI, Proxmox, OpenStack) are available and the control plane (management
cluster) and storage cluster can be installed in multiple, flexible deployment strategies: 

Simplyblock supports two deployment models:

- **Kubernetes Hyper-Converged:** The control plane and storage plane can be installed into Kubernetes in a fully
  [hyper-converged](../architecture/concepts/hyper-converged.md) fashion. That means that the control plane and storage
  cluster share the same underlying Kubernetes cluster with other workloads. The control plane and storage cluster
  are fully managed via the Simplyblock API.
- **Kubernetes Disaggregated:** The control plane and storage plane can be installed into Kubernetes in a
  [disaggregated](../architecture/concepts/disaggregated.md) fashion. That means that the control plane and storage
  cluster are deployed into a separate Kubernetes cluster from other workloads. The control plane and storage
  cluster are fully managed via the Simplyblock API.
- **Plain Linux:** The control plane and storage cluster can be installed into a Linux-running local virtual machine 
  (such as Proxmox, KVM, or other virtualization solutions), a bare metal server, or a cloud VM (such as AWS EC2 or 
  Google Compute Engine). The control plane and storage plane use a Docker-based deployment and are fully managed via
  the Simplyblock CLI or API.
- **Hybrid Setups:** A combination of a Kubernetes hyper-converged and a Kubernetes-, or Linux-based disaggregated setup. 

For most Kubernetes environments, the recommended and first-class deployment model is **hyper-converged**, where
simplyblock storage services run on selected Kubernetes worker nodes alongside application workloads.

If strict resource separation is required, simplyblock one of the **disaggregated** modes, Kubernetes or plain Linux
deployments, is recommended.

## Control Plane Installation

Each storage cluster requires a control plane to run. Multiple storage clusters may be connected to a single control 
plane. The deployment of the control plane must happen before a storage cluster deployment. 
The control plane can be installed into a Kubernetes cluster or on plain Linux VMs.

For details, see the [Install Control Plane on Kubernetes](kubernetes/k8s-control-plane.md) (recommended) or
[Control Plane Deployment on VM](install-on-linux/install-cp.md).

## Storage Node Installation

For details on how to install the storage cluster into Kubernetes, see here: [Install Storage Nodes on Kubernetes](kubernetes/k8s-control-plane.md)

For details on how to install the storage cluster into Plain Linux, see [Install Simplyblock Storage Nodes on Linux](install-on-linux/install-sp.md).

## OpenShift Installation

OpenShift requires an additional step before successfully installing simplyblock. For details on how to install
simplyblock into an OpenShift cluster, see [Install Simplyblock on OpenShift](kubernetes/openshift.md).

## Installation of Drivers

Simplyblock logical volumes are NVMe over TCP or RDMA (ROCEv2) volumes. 
They are attached to the Linux kernel via the provided `nvme-tcp` or `nvme-rdma`
modules and managed via the `nvme-cli` tool. For more information, see
  [Linux NVMe-oF Attach](baremetal/index.md).
On top of the NVMe-oF devices, which show up as linux block devices such as `/dev/nvme1n1`,  
life cycle automation is performed by the orchestrator-specific simplyblock drivers: 

- On Kubernetes: [Simplyblock CSI Driver](kubernetes/install-csi.md) 
- On Proxmox: [Proxmox Integration](proxmox/index.md) 
- On OpenStack: [Cinder Driver](openstack/index.md)

Generally, before creating volumes it is important to understand the difference btw. an
[NVMe-oF Subsystem and a Namespace](nvme-namespaces-and-subsystems.md). 

## System Requirements and Sizing

Simplyblock is designed for high-performance storage operations. Therefore, it has specific system requirements that
must be met. The following sections describe the system and node sizing requirements. 

- [System Requirements](deployment-preparation/system-requirements.md)
- [Erasure Coding Configuration](deployment-preparation/erasure-coding-scheme.md)
- [Air Gapped Installation](air-gap/index.md)

For deployments on hyper-scalers, like Amazon AWS and Google GCP, there are instance type recommendations. While other
instance types may work, it is highly recommended to use the instance type recommendations.

- [Amazon EC2](deployment-preparation/cloud-instance-recommendations.md#aws-amazon-ec2-recommendations)
- [Google Compute Engine](deployment-preparation/cloud-instance-recommendations.md#google-compute-engine-recommendations)

