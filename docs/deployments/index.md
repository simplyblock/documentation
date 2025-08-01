---
title: "Deployments"
weight: 10300
---

Simplyblock is a highly flexible storage solution. It can be installed in a variety of different deployment models 
inside and outside of Kubernetes.

## Control Plane Installation

Each storage cluster requires a control plane to run. Multiple storage clusters may be connected to a single control 
plane. The deployment of the control plane must happen before a storage cluster deployment. For details, see the
[Control Plane Deployment](install-simplyblock/install-cp.md).

For a production deployment, the control plane requires three management nodes. For fault tolerance, these instances
must be operated in separate failure domains from each other and the storage nodes (e.g., independent hosts or racks).

## Storage Node Installation

Storage nodes can be installed directly under any Linux Rocky, Alma or RHEL version 9 (or later). A Kubernetes cluster
is no requirement. A minimal OS image is sufficient. For details on how to install the storage cluster, see
[Install Simplyblock Storage Nodes](install-simplyblock/install-sp.md).

The above setup is not suitable for Kubernetes [hyper-converged](../architecture/concepts/hyper-converged.md) deployments.

Alternatively, it is possible to install simplyblock storage nodes into an existing Kubernetes cluster. This allows for
both, hyper-converged, and disaggregated setups. It is also possible to run a hybrid deployment, with some nodes running
hyper-converged and others running disaggregated. For more information, see the Kubernetes section below.

This alternative can be chosen if storage is mainly provisioned via CSI driver (Kubernetes workloads).

## Initiator-Side Installation

Simplyblock logical volumes are NVMe over TCP volumes. They are attached to the Linux kernel via the provided `nvme-tcp`
module.

The initiator-side installation (or client-side) depends on the client environment.

- On Kubernetes, the[Simplyblock CSI Driver](kubernetes/install-csi.md) takes care of attaching, reconnecting, and
  disconnecting the logical volumes.
- On Proxmox, the [Proxmox Integration](proxmox/index.md) handles the same situations.
- On plain Linux hosts, a logical volume is connected via the `nvme-cli` tool. For more information, see
  [Bare-Metal Attach](baremetal/index.md).

## System Requirements and Sizing

Simplyblock is designed for high-performance storage operations. Therefore, it has specific system requirements that
must be met. The following sections describe the system and node sizing requirements. 

- [System Requirements](deployment-preparation/system-requirements.md)
- [Node Sizing](deployment-preparation/node-sizing.md)
- [Erasure Coding Configuration](deployment-preparation/erasure-coding-scheme.md)
- [Air Gapped Installation](air-gap/index.md)

For deployments on hyper-scalers, like Amazon AWS and Google GCP, there are instance type recommendations. While other
instance types may work, it is highly recommended to use the instance type recommendations.

- [Amazon EC2](deployment-preparation/cloud-instance-recommendations.md#aws-amazon-ec2-recommendations)
- [Google Compute Engine](deployment-preparation/cloud-instance-recommendations.md#google-compute-engine-recommendations)

## Related Articles

<div class="grid cards" markdown>

-   :material-kubernetes:{ .lg .middle } __Kubernetes__

    ---

    Kubernetes deployments, including Amazon EKS and Google Kubernetes Engine (GKE).

    [:octicons-arrow-right-24: Install CSI Driver](kubernetes/install-csi.md)<br/>
    [:octicons-arrow-right-24: Hyper-Converged Setup](kubernetes/k8s-hyperconverged.md)<br/>
    [:octicons-arrow-right-24: Kubernetes Disaggregated Setup](kubernetes/k8s-disaggregated.md)

-   :material-linux:{ .lg .middle } __Plain Linux__

    ---

    Plain Linux deployments, including the control plane, the storage plane, and
    bare-metal attaching.

    [:octicons-arrow-right-24: Install Control Plane](install-simplyblock/install-cp.md)<br/>
    [:octicons-arrow-right-24: Install Storage Plane](install-simplyblock/install-sp.md)<br/>
    [:octicons-arrow-right-24: Attach storage to Linux](baremetal/index.md)

-   :material-cloud-circle:{ .lg .middle } __Proxmox__

    ---

    The Proxmox integration is provided as a Debian (.deb) package.

    [:octicons-arrow-right-24: Install Proxmox Integration](proxmox/index.md)

</div>
