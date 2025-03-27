---
title: "Deployments"
weight: 10300
---

Simplyblock is a highly flexible storage solution. It can be installed in a variety of different deployment models
inside and outside of Kubernetes.

!!! info
    Bare Metal Linux installation can be installed on dedicated machines, virtual machines, on-premises or on private
    and public clouds. For AWS EC2-based installation, there is a specific installation guide which is recommended to
    follow if an AWS EC2 installation is planned.

<div class="grid cards" markdown>

-   :material-kubernetes:{ .lg .middle } __Kubernetes__

    ---

    [:octicons-arrow-right-24: Systems Recommendations](deployment-planning/recommendations.md)<br/>
    [:octicons-arrow-right-24: Node Sizing](deployment-planning/node-sizing.md)<br/>
    [:octicons-arrow-right-24: Erasure Coding Configuration](deployment-planning/erasure-coding-scheme.md)<br/>
    [:octicons-arrow-right-24: Prerequisites](kubernetes/prerequisites.md)<br/>
    [:octicons-arrow-right-24: Hyper-Converged Setup](kubernetes/install-simplyblock/hyper-converged.md)<br/>
    [:octicons-arrow-right-24: Disaggregated Setup](kubernetes/install-simplyblock/disaggregated.md)<br/>
    [:octicons-arrow-right-24: Hybrid Setup](kubernetes/install-simplyblock/hybrid.md)

-   :material-linux:{ .lg .middle } __Bare Metal Linux__

    ---

    [:octicons-arrow-right-24: Node Sizing](deployment-planning/node-sizing.md)<br/>
    [:octicons-arrow-right-24: Erasure Coding Configuration](deployment-planning/erasure-coding-scheme.md)<br/>
    [:octicons-arrow-right-24: Prerequisites](baremetal/prerequisites.md)<br/>
    [:octicons-arrow-right-24: Install Storage Cluster](baremetal/install-simplyblock.md)<br/>
    [:octicons-arrow-right-24: Install Kubernetes CSI Driver](baremetal/install-simplyblock-csi.md)<br/>

-   :material-aws:{ .lg .middle } __AWS EC2__

    ---

    [:octicons-arrow-right-24: Node Sizing](deployment-planning/node-sizing.md)<br/>
    [:octicons-arrow-right-24: Erasure Coding Configuration](deployment-planning/erasure-coding-scheme.md)<br/>
    [:octicons-arrow-right-24: Prerequisites](aws-ec2/prerequisites.md)<br/>
    [:octicons-arrow-right-24: Install Storage Cluster](aws-ec2/install-simplyblock.md)<br/>
    [:octicons-arrow-right-24: Install Kubernetes CSI Driver](aws-ec2/install-simplyblock-csi.md)<br/>

-   :material-hvac-off:{ .lg .middle } __Air Gapped__

    ---

    [:octicons-arrow-right-24: General Information](air-gap/index.md)
</div>
