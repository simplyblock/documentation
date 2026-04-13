---
title: "Deployment Preparation"
description: "Deployment Preparation: Proper deployment planning is essential for ensuring the performance, scalability, and resilience of a simplyblock storage cluster."
weight: 20000
---

Proper deployment planning is essential for ensuring the performance, scalability, and resilience of a simplyblock
storage cluster.

!!! tip
    For OpenShift environments, simplyblock’s **recommended** deployment model is
    **hyper-converged**.

## Deployment Models

Two deployment options are supported:

- **Plain Linux**: In this mode, which is also called Docker mode, all nodes are deployed to separate hosts. Storage
  nodes are usually bare-metal, and control plane nodes are usually VMs.Basic Docker knowledge is helpful, but all
  management can be performed within the system via its CLI or API. 

- **Kubernetes**: In Kubernetes, both **disaggregated** deployments with dedicated workers or clusters for storage
  nodes, or **hyper-converged deployments** (co-located with compute workloads) are supported. A wide range of
  Kubernetes distros and operating systems are supported. For OpenShift clusters, the hyper-converged deployment model
  is recommended. Kubernetes Knowledge is required.

## General Information on Requirements

Before installation, key factors such as node sizing, storage capacity, and fault tolerance mechanisms should be
carefully evaluated to match workload requirements. This section provides guidance on sizing management nodes and
storage nodes, helping administrators allocate adequate CPU, memory, and disk resources for optimal cluster performance.

Additionally, it explores selectable erasure coding schemes, detailing how different configurations impact storage
efficiency, redundancy, and recovery performance. Other critical considerations, such as network infrastructure,
high-availability strategies, and workload-specific optimizations, are also covered to assist in designing a simplyblock
deployment that meets both operational and business needs.

This guidance applies to all deployment models, with special sizing notes for hyper-converged Kubernetes/OpenShift
deployments where compute and storage share cluster nodes.
