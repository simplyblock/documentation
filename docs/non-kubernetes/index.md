---
title: Non-Kubernetes
description: "Non-Kubernetes: Simplyblock does not require Kubernetes. A full storage cluster can be deployed on plain Linux hosts using Docker."
weight: 10110
---

Simplyblock does not require Kubernetes. A full storage cluster can be deployed on plain Linux hosts, a mode also
referred to as Docker mode, where the control plane and the storage plane run as containers on separate hosts. Storage
nodes are typically bare-metal servers, while management nodes are typically virtual machines. Basic Docker knowledge is
helpful, but the entire cluster is managed through the `{{ cliname }}` command-line interface or the management API.

Once a cluster is running, its capacity can be consumed by any NVMe over Fabrics initiator. Simplyblock provides
integrations for Proxmox Virtual Environment and OpenStack, and volumes can be attached directly to plain Linux hosts
that run neither Kubernetes nor a virtualization platform.

Before deploying, review the node sizing, network, and erasure coding guidance in
[Deployment Preparation](../deployment-preparation/index.md). That guidance applies to all deployment models.

## What This Section Covers

- **[Install Simplyblock](installation/index.md):** Prepare the hosts and the network, then install the control plane
  (management nodes) and the storage plane (storage nodes) on plain Linux.
- **[Plain Linux Initiators](linux-initiators/index.md):** Perform the host-level configuration required to attach
  simplyblock volumes to Linux hosts that are not running Kubernetes, Proxmox, or OpenStack.
- **[OpenStack Integration](openstack/index.md):** Use simplyblock as a Cinder backend for OpenStack.
- **[Proxmox Integration](proxmox/index.md):** Provision volumes for KVM virtual machines and LXC containers through the
  simplyblock Proxmox storage plugin.
- **[Usage](usage/index.md):** Provision, expand, snapshot, clone, encrypt, and remove logical volumes with
  `{{ cliname }}`.
- **[Operations](operations/index.md):** Monitor cluster health, scale capacity, back up and restore volumes, upgrade
  the cluster, apply quality of service, and replace or migrate storage nodes.

## Related References

- [CLI / Command-line interface](../reference/cli/index.md): complete `{{ cliname }}` command reference.
- [API / Developer SDK](../reference/api/index.md): management API for automation and orchestration.
- [Control Plane](../reference/troubleshooting/control-plane.md): troubleshooting the management nodes.

!!! info
    To deploy simplyblock on Kubernetes with the simplyblock operator and consume storage through the CSI driver, see
    [Kubernetes](../kubernetes/index.md).
