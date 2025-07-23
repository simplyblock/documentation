---
title: "Deployments"
weight: 10300
---

Simplyblock is a highly flexible storage solution. It can be installed in a variety of different deployment models inside and outside of Kubernetes.

## control plane installation

Each storage cluster requires a control plane to run. Multiple storage clusters may be connected with a single control plane. The deployment of the control plane always comes before storage cluster deployments. See [Control Plane Deployment](install-simplyblock/install-cp.md).

For a production deployment of the control plane, the use of three virtual machines running on hosts in failure domains, which are different from each other and from the storage nodes (i.e. independent hosts or racks).

## storage node installation

Storage nodes can be installed directly under Linux Rocky, Alma or RHEL version 9. A k8s worker must not be present in this case and a minimum os image is sufficient: [Install Simplyblock Storage Nodes](install-simplyblock/install-sn.md). This setup is not suitable for kubernetes [hyper-converged](../architecture/concepts/hyper-converged.md) deployments.

It is also possible to __alternatively__ install Simplyblock storage nodes into existing k8s clusters, allowing for both hyper-converged, disaggregated and hybrid deployment models (see below Kubernetes). This alternative can be chosen, if storage is mainly provisioned via CSI driver (k8s workloads).

## Initiator-Side Installation

nvme-tcp volumes are attached over the network from k8s worker nodes via the csi driver, proxmox hypervisors via the proxmox driver and any other linux host using nvme-cli. 

## System requirements and Sizing

Please read the following to prepare for the deployment: 

[System Requirements](deployment-planning/recommendations.md)
[Node Sizing](deployment-planning/node-sizing.md)
[Erasure Coding Configuration](deployment-planning/erasure-coding-scheme.md)
[Air Gapped Installation](air-gap/index.md)

and if deploying to either aws or gcp:
[Cloud Instance Types](deployment-planning/further-considerations.md)

<div class="grid cards" markdown>

-   :material-kubernetes:{ .lg .middle } __Kubernetes__

    ---

    Kubernetes deployments include AWS' EKS and GCP's GKE.

    [:octicons-arrow-right-24: Install CSI Driver](kubernetes/install-csi.md)<br/>    
    [:octicons-arrow-right-24: Hyper-Converged Setup](kubernetes/k8s-hyperconverged.md)<br/>
    [:octicons-arrow-right-24: k8s disaggregated Setup](kubernetes/k8s-disaggregated.md)<br/>

-   :material-linux:{ .lg .middle } __Plain Linux__

    ---

    You may attach Simplyblock Storage manually to the Linux Operating System via the kernel nvmf-tcp
    module. 

    [:octicons-arrow-right-24: Attach storage to Linux](baremetal/index.md/)<br/>

-   :material-ProxMox:{ .lg .middle } __ProxMox__

    ---
    
    [:octicons-arrow-right-24: Install ProxMox Driver](proxmox/index.md)<br/>
    <br/>
</div>
