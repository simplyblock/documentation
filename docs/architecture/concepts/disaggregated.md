---
title: "Disaggregated"
description: "Disaggregated storage represents a modern approach to distributed storage architectures, where compute and storage resources are decoupled."
weight: 30400
---

Simplyblock supports disaggregated storage deployments, in which dedicated storage nodes operate separately from compute, in addition to
hyper-converged and hybrid deployment topologies.

It is important to note that, while we support plain Linux (Docker-based) disaggregated deployments, they can also run fully in the
Kubernetes-native operations model, either within the same cluster as the compute workloads or in separate clusters.

The main difference from the hyper-converged model is the separation of storage and compute resources.

The biggest benefit of the disaggregated model is the decoupling the lifecycle of storage operations from
compute lifecycle management (worker node upgrades, node maintenance, and node reboots), as well as independent scaling.
For example, a small compute cluster with I/O-intensive workloads may still require a lot of storage capacity and IOPS.

The biggest disadvantages are the loss of data locality and possible misalignments in scaling (required minimum scale of the
storage cluster and scaling of the storage cluster with compute).

Key characteristics of our disaggregated storage solutions include:

- **Independent Scalability:** Compute and storage can be scaled separately, optimizing resource utilization and
  reducing unnecessary hardware expansion. IO demand and compute sizing are treated independently.
- **Independent Cluster Lifecycle:** Storage and compute can be maintained, upgraded, and replaced independently of each other.
- **Controlled Storage Performance:** It is easier to control latency, throughput, and IOPS output in a disaggregated model. 
- **Hardware Independence:** This feature is shared with hyper-converged storage. Hardware component and node replacements
  can be performed entirely independently of the software, choosing different vendors in accordance with procurement strategies,
  and supporting gradual and rolling replacements.
