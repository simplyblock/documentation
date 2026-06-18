---
title: "Simplyblock Architecture"
description: "Simplyblock Architecture: Simplyblock is a cloud-native, distributed block storage platform designed to deliver scalable, high-performance, and resilient."
weight: 20100
---

Simplyblock is a cloud-native, distributed block storage platform designed to deliver scalable, high-performance, and
resilient storage through a software-defined architecture. Centered around NVMe-over-Fabrics (NVMe-oF), simplyblock
separates compute and storage to enable scale-out elasticity, high availability, and low-latency operations in modern,
containerized environments.

The architecture is purpose-built to support Kubernetes-native and OpenShift-based deployments with seamless
integration.

Furthermore, simplyblock support virtual and physical machines (bare metal) for storage-side and client-side
deployments. 

## Control Plane

The control plane hosts the Simplyblock Management API and CLI endpoints with identical features. The CLI is equally
available on all management nodes. The API and CLI are secured using HTTPS / TLS.

The control plane operates through redundant management nodes that handle cluster health, metadata, and orchestration. A
quorum-based model ensures no single point of failure.

### Control Plane Responsibilities

The control plane provides the following functionality in two groups of distributed services:

- Operations Management and Automation
    - Lifecycle management of clusters
        - Deploy storage clusters
        - Manages nodes and devices
        - Resize and reconfigure clusters
    - Lifecycle management of logical volumes and pools
    - Raw IO Statistics, Capacity, Alerting and Log Feeds
- Observability Stack (optional)
    - Log Management (graylog, opensearch, mongoDB, thanos)
    - Performance Monitoring and Dashboarding (grafana, prometheus) with configurable alerting to email and slack

The observability stack is optional. It is typically used in PoC (proof of concept) or testing environments and for
customers, who need to get started quickly. For large scale, multi-cluster deployments it is 
rather recommended to integrate with pre-existing or targeted observability stacks.
      
The control plane is layered and its distributed control plane services run on both kubernetes and native Docker.
The latter can be used for non-Kubernetes (Proxmox, OpenStack) or disaggregated deployments.
All services are accessible via the Simplyblock CLI and Control Plane API.

On top of those services sits a CSI driver and a Kubernetes operator within the Kubernetes-native operations model. 
It is entirely managed by Custom Resource Definitions (CRDs), however, internally uses the same Control Plane APIs.

Communication between the Control Plane and the Storage Plane is performed via two separate access paths:

- A secure HTTPS RPC mechanism with JSON payloads.
- A secure HTTPS service endpoint for basic control, such as storage node availability monitoring, restart and shutdown.

### Control Plane State Storage

The control plane is implemented as a stack of containers running on one or more management nodes. For production
environments, simplyblock requires at least three management nodes for high availability. The management nodes run as
a set of replicated, stateful services.

For internal state storage, the control plane uses ([FoundationDB](https://www.foundationdb.org/){:target="_blank" rel="noopener"}) as
its key-value store. FoundationDB, by itself, operates in a replicated highly-available cluster across all management
nodes.

Within Kubernetes deployments, the control plane can now also be deployed alongside the storage nodes on the same k8s
workers. It will, however, run in separate pods.

## Storage Plane

The storage plane consists of distributed storage nodes that run on Linux-based systems and provide logical volumes (
LVs) as virtual NVMe devices. Using a fork of SPDK (Storage Performance Development Kit) and DPDK (Data Plane Development
Kit), simplyblock achieves high-speed, user-space storage operations with minimal latency.

To achieve that, simplyblock detaches NVMe devices from the Linux kernel, bypassing the typical kernel-based handling.
It then takes full control of the device directly, handling all communication with the hardware in user-space. That
removes transitions from user-space to kernel and back, improving latency and reducing processing time and context
switches.

### Scaling and Performance

Simplyblock supports linear scale-out by adding storage nodes without service disruption. Performance increases with
additional cores, network interfaces, and NVMe devices, with SPDK minimizing CPU overhead for maximum throughput.

Data written to a simplyblock logical volume is split into chunks and distributed across the storage plane cluster
nodes. This improves throughput by parallelizing the access to data through multiple storage nodes.

### Data Protection & Fault Tolerance

Simplyblock's storage engine implements distributed erasure coding, a RAID-like system, which uses parity information to protect
data and restore it in case of a failure. Due to the fully distributed nature of simplyblock's erasure coding
implementation, parity information is not only stored on disks other than the original data chunk, but also on other
nodes. This improves data protection and enables higher fault tolerance than typical implementations. While most
erasure coding implementations provide a Maximum Tolerable Failure (MFT) in terms of how many disks can fail,
simplyblock defines it as the number of nodes that can fail.

As a second layer, simplyblock leverages NVMe-oF multipathing to ensure continuous access to logical volumes by
automatically handling failover between primary and secondary nodes. Each volume is presented with multiple active
paths, allowing I/O operations to seamlessly reroute through secondary nodes if the primary node becomes unavailable due
to failure, maintenance, or network disruption. This multipath configuration is managed transparently by the NVMe-oF
subsystem, providing path redundancy, eliminating single points of failure, and maintaining high availability without
requiring manual intervention. The system continuously monitors path health, and when the primary path is restored, it
can be automatically reintegrated, ensuring optimal performance and reliability.

Last, simplyblock provides robust encryption for data-at-rest, ensuring that all data stored on logical volumes is
protected using industry-standard AES_XTS encryption with minimal performance overhead. This encryption is applied at
the volume level and is managed transparently within the simplyblock cluster, allowing compliance with strict regulatory
requirements such as GDPR, HIPAA, and PCI-DSS. Furthermore, simplyblock’s architecture is designed for strong
multitenant isolation, ensuring that encryption keys, metadata, and data are securely segregated between tenants. This
guarantees that unauthorized access between workloads and users is prevented, making simplyblock an ideal solution for
shared environments where security, compliance, and tenant separation are critical.

## Technologies in Simplyblock

Building strong and reliable distributed storage technology has to build on a strong foundation. That's why simplyblock
uses a variety of open-source key technologies as its basis.

| Component        | Technologies                                                                                                                                                                                                                                                                                             |
|------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Networking       | [NVMe-oF](https://nvmexpress.org/){:target="_blank" rel="noopener"}, [NVMe/TCP](../important-notes/terminology.md#nvmetcp-nvme-over-tcp), [NVMe/RoCE](../important-notes/terminology.md#nvmeroce-nvme-over-rdma-over-converged-ethernet), [DPDK](https://www.dpdk.org/){:target="_blank" rel="noopener"} |
| Storage          | [SPDK](https://spdk.io/){:target="_blank" rel="noopener"}, [FoundationDB](https://www.foundationdb.org/){:target="_blank" rel="noopener"}, [MongoDB](https://www.mongodb.com/){:target="_blank" rel="noopener"}                                                                                          |
| Observability    | [Prometheus](https://prometheus.io/){:target="_blank" rel="noopener"}, [Thanos](https://thanos.io/){:target="_blank" rel="noopener"}, [Grafana](https://grafana.com/){:target="_blank" rel="noopener"}                                                                                                   |
| Logging          | [Graylog](https://graylog.org/){:target="_blank" rel="noopener"}, [OpenSearch](https://opensearch.org/){:target="_blank" rel="noopener"}                                                                                                                                                                 |
| Kubernetes       | [SPDK CSI](https://github.com/spdk/spdk-csi){:target="_blank" rel="noopener"}, [Kubernetes CSI](https://kubernetes-csi.github.io/docs/){:target="_blank" rel="noopener"}                                                                                                                                 |
| Operating System | [Linux](https://www.kernel.org/){:target="_blank" rel="noopener"}                                                                                                                                                                                                                                        |
