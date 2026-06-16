---
title: "Disaggregated"
description: "Disaggregated storage represents a modern approach to distributed storage architectures, where compute and storage resources are decoupled."
weight: 30400
---

Simplyblock supports disaggregated storage deployments, in which dedicated storage nodes serve separately from compute, in addition to 
Hyper-converged and hybrid deployment topologies.

It is important to note that while we support plain Linux (docker-based) disaggregated deployments, they can also fully run in the 
Kubernetes-native Operations Model, either within the same cluster with the compute workloads or in separate ones.

The main difference to the Hyper-converged model is the separation of storage and compute in terms of resources. 

The biggest benefit of the disaggregated model is the decoupling of lifecycle of storage operations from 
compute lifecycle managment (worker node upgrades, node maintainance, node reboots) as well as independent scaling 
(for example, a small compute cluster with io-intensive workloads may still require a lot of storage capacity and IOPS).

The biggest disadvantages are loss of data locality and also possible mis-alignments in scaling (required minimum scale of
storage cluster, scaling of storage cluster with compute). 

Key characteristics of our disaggregated storage solutions include:

- **Independent Scalability:** Compute and storage can be scaled separately, optimizing resource utilization and
  reducing unnecessary hardware expansion. IO demand and compute sizing are treated independently.
  **Independent Cluster Lifecycle**: Storage and compute can be maintained, upgraded and replaced independently of each other.
- **Controlled Storage Performance:** It is easier to control latency, throughput and IOPS output in a disaggregated model. 
- **Hardware Independence:** This feature is shared with Hyper-converged storage, hardware component and node replacements
  can be performed entirely independently from the software, choosing different vendors in accordance with procurement strategies,
  and supporting gradual and rolling replacements.
