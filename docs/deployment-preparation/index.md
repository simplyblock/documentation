---
title: "Deployment Preparation"
description: "Plan a simplyblock deployment before installing it: the architecture, fault tolerance, sizing, hardware and storage devices, network, and software."
weight: 10090
---

This section covers the decisions to make and the infrastructure to prepare before simplyblock is installed. The pages
follow the order in which a deployment is usually planned. The installation itself, including the preparation of
specific platforms such as EKS, GKE, OpenShift, Rancher, or Talos, is described in
[Install](../kubernetes/installation/index.md).

## Plan

| Step | Page                                                           | Decides                                                                                       |
|------|----------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| 1    | [Deployment Architectures](deployment-architectures.md)        | How many Kubernetes and storage clusters, where the control plane runs, and disaster recovery |
| 2    | [Fault Tolerance and Erasure Coding](erasure-coding-scheme.md) | The erasure coding scheme, the minimum number of nodes, and failure domains                   |
| 3    | [Sizing](sizing.md)                                            | vCPUs, memory, and NUMA placement of the storage nodes, and the size of the control plane     |

## Requirements

| Page                                                     | Covers                                                                                     |
|----------------------------------------------------------|--------------------------------------------------------------------------------------------|
| [Hardware and Storage Devices](hardware-requirements.md) | Minimum hardware, CPU architectures, virtualization, NVMe devices, and Linux block devices |
| [Storage Arrays](storage-arrays.md)                      | Running on FC, iSCSI, or NVMe-oF array LUNs                                                |
| [Network](network.md)                                    | Storage and management networks, fabrics, ports, and edge sites                            |
| [Software Requirements](software-requirements.md)        | Kubernetes distributions, client node kernels, NVMe multipathing, and pNFS                 |

The deployment topologies behind these decisions (hyper-converged, disaggregated, local or hub control plane) are
explained in [Deployment Topologies](../architecture/deployment-topologies/index.md), and the prerequisites of
disaster recovery in [Disaster Recovery Requirements](../disaster-recovery/install/requirements.md).
