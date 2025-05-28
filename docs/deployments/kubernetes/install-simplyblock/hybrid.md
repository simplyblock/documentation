---
title: "Hybrid Setup"
weight: 50200
---

## Network Preparation

Simplyblock recommends two individual network interfaces, one for the control plane and one for the storage plane.
Hence, in the following installation description, we assume two separate subnets. To install simplyblock in your
environment, you may have to adopt these commands to match your configuration.

| Network interface | Network definition | Abbreviation | Subnet          |
|-------------------|--------------------|--------------|-----------------|
| eth0              | Control Plane      | control      | 192.168.10.0/24 |
| eth1              | Storage Plane      | storage      | 10.10.10.0/24   |

## Storage Plane Installation

### Firewall Configuration (SP)

<!-- include: install control plane documentation -->
{% include 'install-control-plane.md' %}

{% include 'install-storage-plane-bare-metal.md' %}

### Hyper-Converged Storage Node Installation

{% include 'kubernetes-install-storage-node-helm.md' %}
