---
title: "AWS EC2 (Amazon Linux)"
weight: 20300
---

An installation on Amazon EC2 is mostly comparable with a bare metal or virtualized installation. There are however a
few small differences. Hence, we decided to give it a separate documentation section.

An installation on Amazon EKS is comparable with a standard Kubernetes installation. The differences between an Amazon
EKS installation and a basic Kubernetes

!!! warning
    Amazon Linux 2 and Amazon Linux 2023 **do not** support
    [NVMe over Fabrics Multipathing](../../important-notes/terminology.md#multipathing)!

<div class="grid cards" markdown>

-   :material-pencil-circle:{ .lg .middle } __Prerequisites__

    ---

    [:octicons-arrow-right-24: Node Sizing](../deployment-planning/node-sizing.md)<br/>
    [:octicons-arrow-right-24: Prerequisites](prerequisites.md)

-   :material-aws:{ .lg .middle } __Simplyblock Installation__

    ---

    [:octicons-arrow-right-24: Install Simplyblock](install-simplyblock.md)

-   :material-kubernetes:{ .lg .middle } __Kubernetes CSI Driver Installation__

    ---

    [:octicons-arrow-right-24: Install Kubernetes CSI Driver](install-simplyblock-csi.md)

-   :material-cached:{ .lg .middle } __Caching Node Installation__

    ---

    [:octicons-arrow-right-24: Install Caching Nodes](install-caching-nodes.md)
</div>
