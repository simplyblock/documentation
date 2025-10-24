---
title: "Deployments"
weight: 10300
---

Simplyblock is a highly flexible storage solution. 

Different initiator (host) drivers (Kubernetes CSI, Proxmox, OpenStack) are available. The storage cluster 
deployment can be installed into Kubernetes (disaggregated or [hyper-converged](../architecture/concepts/hyper-converged.md)) 
or via Docker (also called "Plain Linux" deployment). The Docker-based deployment is fully 
deployed and managed via the Simplyblock CLI or API, minimal Docker knowledge is required. 

## Control Plane Installation

Each storage cluster requires a control plane to run. Multiple storage clusters may be connected to a single control 
plane. The deployment of the control plane must happen before a storage cluster deployment. 
The control plane can be installed into a Kubernetes Cluster or on Plain Linux VMs (using Docker internally).
For details, see the [Control Plane Deployment on VM](install-on-linux/install-cp.md) or [Install Control Plane on Kubernetes](kubernetes/k8s-storage-plane.md)

## Storage Node Installation

For details on how to install the storage cluster into Plain Linux, see [Install Simplyblock Storage Nodes on Linux](install-on-linux/install-sp.md).

For installation of Storage Nodes into Kubernetes, see here: [Install Storage Nodes on Kubernetes](kubernetes/k8s-control-plane.md)

## Installation of Drivers

Simplyblock logical volumes are NVMe over TCP or RDMA (ROCEv2) volumes. 
They are attached to the Linux kernel via the provided `nvme-tcp` or `nvme-rdma`
modules and managed via the `nvme-cli` tool. For more information, see
  [Linux NVMe-oF Attach](baremetal/index.md).
On top of the NVMe-oF devices, which show up as linux block devices such as `/dev/nvme1n1`,  
life cycle automation is performed by the orchestrator-specific Simplyblock drivers: 

- On Kubernetes: [Simplyblock CSI Driver](kubernetes/install-csi.md) 
- On Proxmox: [Proxmox Integration](proxmox/index.md) 
- On OpenStack: [Cinder Driver](openstack/index.md)

Generally, before creating volumes it is important to understand the difference btw. an
[NVMe-oF Subsystem and a Namespace](../NVMf Namespaces and Subsystems.md). 

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


