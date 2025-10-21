---
title: "What is Simplyblock?"
weight: 20000
---

Simplyblock is a high-performance, distributed storage orchestration layer designed for cloud-native environments. It
provides NVMe over TCP (NVMe/TCP) block storage to hosts and offers block storage to containers through its Container
Storage Interface (CSI) and ProxMox drivers.

## What makes Simplyblock Special?

- **Environment Agnostic:** Simplyblock operates seamlessly across major cloud providers, regional, and specialized
  providers, bare-metal and virtual provisioners, and private clouds, including both virtualized and bare-metal
- Kubernetes environments.

- **NVMe/f-optimized:** Simplyblock is built from the scratch around NVMe. 
  All internal and external storage access is entirely based on NVMe and NVMf (tcp and/or rdma).
  This includes storage node local back-storage, host-to-cluster and node-to-node traffic.
  Together with the user-space data plane, distributed data placement and 
  advanced QoS and other characterists, this makes Simplyblock the storage platform with most advanced performance guarantees in
  hyperconverged solutions available today. 

- **User-space data plane:** Simplyblock data plane is built entirely in user-space
  with an interrupt-free, lockless, zero-copy architecture with thread-to-core pinning. 
  The hot data path entirely avoids linux kernel involvement, data copies, 
  dynamic thread scheduling and inter-thread synchronization. 
  Its deployment is fully numa-node-aware. 

- **Advanced QoS:** Simplyblock provides not only IOPS or throughput based caps, but also true
  QoS service classes, effectively isolating IO traffic. 

- **Distributed data placement:** Simplyblock advanced data placement, which is based on small, fixed-size data chunks,
  ensures a perfectly balanced utilization of storage, compute and network bandwidth,
  avoiding any performance bottlenecks local to specific nodes. This gives an almost linear
  performance scalability to the cluster.

- **Containerized Architecture:** The solution comprises:
    - *Storage Nodes:* Container stacks delivering distributed data services via NVMe over Fabrics (NVMe over TCP),
      forming storage clusters.
    - *Management Nodes:* Container stacks offering control and management services, collectively known as the control
      plane.

- **Platform Support:** Simplyblock supports deployment on virtual machines, bare-metal instances, and Kubernetes
  containers, compatible with x86 and ARM architectures.

- **Deployment Flexibility:** Simplyblock offers the greatest deployment flexibility in the industry. It can be deployed
  hyper-converged, disaggregated, and in a hybrid fashion, combining the best of both worlds.

## Customer Benefits Across Industries

Simplyblock offers tailored advantages to various sectors:

- **Financial Services:** Enhances data management by boosting performance, strengthening security, and optimizing cloud
  storage costs.

- **Media and Gaming:** Improves storage performance, reduces costs, and streamlines data management, facilitating
  efficient handling of large media files and gaming data.

- **Technology and SaaS Companies:** Provides cost savings and performance enhancements, simplifying storage management
  and improving application performance without significant infrastructure changes.

- **Telecommunications:** Offers ultra-low-latency access to data, enhances security, and simplifies complex storage
  infrastructures, aiding in the efficient management of customer records and network telemetry.

- **Blockchain and Cryptocurrency:** Delivers cost efficiency, enhanced performance, scalability, and robust data
  security, addressing the unique storage demands of blockchain networks.
 
