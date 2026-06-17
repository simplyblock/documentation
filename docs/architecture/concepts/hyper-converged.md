---
title: "Hyper-Converged"
description: "Hyper-converged storage is a key component of hyper-converged infrastructure (HCI), where compute, storage, and networking resources are tightly integrated into."
weight: 30300
---

Simplyblock supports Hyper-converged, dissaggregated and hybrid deployment topologies. In Hyper-converged setups,
simplyblock values data locality 

Hyper-converged storage is a key component of hyper-converged infrastructure (HCI), where compute, storage, and
networking resources are tightly integrated into a unified system. This approach simplifies management, enhances
scalability, and optimizes resource utilization in distributed data storage environments.

Simplyblock values data-locality in hyper-converged deployments and even implements dynamic data locality "following"
the workloads. 
However, data locality in simplyblock is always best-effort, never limiting the scalability of individual volumes or 
entire storage pools and clusters as well as a balanced resource utilization. 

Traditional storage architectures often separate compute and storage into distinct hardware layers, requiring complex
management and specialized hardware. Hyper-converged storage consolidates these resources within the same nodes, forming
a software-defined storage (SDS) layer that dynamically distributes and manages data across the cluster.

Key characteristics and benefits of hyper-converged storage include:

- **Massive Simplification of Hardware Management and Operations**: A single type and configuration of a rack server and networking
  setup can scale to hundreds, thousands or hundreds of thousands of units. There is no need for specialized storage hardware and fabric 
  to be fitted into the operations model. This model provides much better economies of scale from hardware procurement to infrastructure
  operations. 
- **Cluster Scalability:** Clusters can scale from very small to very large without having to adjust storage separately. 
  New nodes can be added seamlessly, increasing both compute and storage capacity without complex
  reconfiguration. Storage capacity and performance grows and shrinks seamlessly with the size of the cluster.
  This provides a great deal of flexibility for customers with strong and unknown dynamics as well as those with a variety of different sizing
  requirements from small edge clusters to large data center clusters.  
-  **De-coupling from Hardware Lifecycle** Individual hardware components or units can be replaced choosing from different vendors 
without service interruption or degradation. Gradual replacement of hardware is supported.
-  **Data Locality**: Best-effort data locality can significantly reduce the burden on the shared network and improve the latency of and 
  throughput of IO. 

