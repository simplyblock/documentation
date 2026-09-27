---
title: "Deployment Preparation"
description: "Deployment Preparation: Proper deployment planning is essential for ensuring the performance, scalability, and resilience of a simplyblock storage cluster."
weight: 10090
---

Proper deployment planning is essential for ensuring the performance, scalability, and resilience of a simplyblock
storage cluster.

## Deployment Model

Simplyblock is deployed on Kubernetes and OpenShift and is managed through the Simplyblock Operator and its custom
resources. Both **disaggregated** deployments, with dedicated workers or clusters for storage nodes, and
**hyper-converged** deployments, co-located with compute workloads, are supported, as well as a hybrid of both. A
wide range of Kubernetes distributions and operating systems is supported. If the same cluster is used to serve and
consume the storage, there is no essential difference between the models from a deployment perspective: the choice
becomes a question of node selection only. The topologies are described in
[Deployment Topologies](../architecture/deployment-topologies/index.md).

## Deployment Architectures and Disaster Recovery

Before sizing individual nodes, the overall architecture has to be chosen: how many Kubernetes clusters and storage
clusters are involved, where the control plane runs, and whether a hub cluster coordinates disaster recovery between
sites.

- **[Deployment Architectures](deployment-architectures.md):** Supported architectures with and without disaster
  recovery, from a single cluster to a hub with several site clusters, and a decision table.
- **[Disaster Recovery Requirements](dr-requirements.md):** Hub cluster sizing, Kubernetes versions, site cluster
  prerequisites, S3, networking, and site labeling for simplyblock Disaster Recovery.

## General Information on Requirements

Before installation, key factors such as node sizing, storage capacity, and fault tolerance mechanisms should be
carefully evaluated to match workload requirements. This section provides guidance on sizing management nodes and
storage nodes, helping administrators allocate adequate CPU, memory, and disk resources for optimal cluster performance.

Additionally, it explores selectable erasure coding schemes, detailing how different configurations impact storage
efficiency, redundancy, and recovery performance. Other critical considerations, such as network infrastructure,
high-availability strategies, and workload-specific optimizations, are also covered to assist in designing a simplyblock
deployment that meets both operational and business needs.

This guidance applies to all deployment topologies, with special sizing notes for hyper-converged Kubernetes and
OpenShift deployments, where compute and storage share cluster nodes.
