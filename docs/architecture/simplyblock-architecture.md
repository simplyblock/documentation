---
title: "Simplyblock Architecture"
weight: 20100
---

Simplyblock is a cloud-native, distributed block storage platform designed to deliver scalable, high-performance, and
resilient storage through a software-defined architecture. Centered around NVMe-over-Fabrics (NVMe-oF), simplyblock
separates compute and storage to enable scale-out elasticity, high availability, and low-latency operations in modern,
containerized environments. The architecture is purpose-built to support Kubernetes-native deployments with seamless
integration but supports virtual and even physical machines as clients as well.

## Control Plane

The control plane hosts the Simplyblock Management API and CLI endpoints with identical features. The CLI is equally
available on all management nodes. The API and CLI are secured using HTTPS / TLS.

The control plane operates through redundant management nodes that handle cluster health, metadata, and orchestration. A
quorum-based model ensures no single point of failure.

### Control Plane Responsibilities

The control plane provides the following functionality:

- Lifecycle management of clusters:
    - Deploy storage clusters
    - Manages nodes and devices
    - Resize and re-configure clusters
- Lifecycle management of logical volumes and pools
    - For Kubernetes, the Simplyblock CSI driver integrates with the persistent volume lifecycle management
- Cluster operations
    - I/O Statistics
    - Capacity Statistics
    - Alerts
    - Logging
    - others

The control plane also provides real-time collection and aggregation of io stats (performance, capacity,
utilization), proactive cluster monitoring and health checks, monitoring dashboards, alerting, a log file repository
with a management interface, data migration and automated node and device restart services.

For monitoring dashboards and alerting, the simplyblock control plane provides Grafana and Prometheus. Both systems are
configured to provide a set of standard alerts which can be delivered via Slack or email. Additionally, customers
are free to define their own custom alerts.

For log management, simplyblock uses Graylog. For a comprehensive insight, Graylog is configured to collect container
logs from control plane and storage plane services, the RPC communication between the control plane and storage cluster
and the data services logs ([SPDK](https://spdk.io/){:target="_blank"} or Storage Performance Development Kit).

### Control Plane State Storage

The control plane is implemented as a stack of containers running on one or more management nodes. For production
environments, simplyblock requires at least 3 management nodes for high availability. The management nodes run as
a set of replicated, stateful services.

For internal state storage, the control plane uses ([FoundationDB](https://www.foundationdb.org/){:target="_blank"}) as
its key-value store. FoundationDB, by itself, operates in a replicated high-available cluster across all management
nodes.

## Storage Plane

The storage plane consists of distributed storage nodes that run on Linux-based systems and provide logical volumes (
LVs) as virtual NVMe devices. Using SPDK and DPDK (Data Plane Development Kit), simplyblock achieves high-speed,
user-space storage operations with minimal latency.

To achieve that, simplyblock detaches NVMe devices from the Linux kernel, bypassing the typical kernel-based handling.
It then takes full control of the device directly, handling all communication with the hardware in user-space. That
removes transitions from user-space to kernel and back, improving latency and reducing processing time and context
switches.

### Scaling and Performance

Simplyblock supports linear scale-out by adding storage nodes without service disruption. Performance increases with
additional cores, network interfaces, and NVMe devices, with SPDK minimizing CPU overhead for maximum throughput.

Data written to a simplyblock logical volume is split into chunks and distributed across the storage plane cluster
nodes. This improves throughput by parallelizing the access to data through multiple storage nodes.

### Data Protection

Simplyblock's storage engine implements erasure coding, a RAID-like system, which uses parity information to protect
data and restore it in case of a failure. Due to the fully distributed nature of simplyblock's erasure coding
implementation, parity information is not only stored on other disks than the original data chunk, but even other nodes.
This improves the data protection and enables higher fault tolerance over typical implementations. While most erasure
coding implementation provide a Maximum Tolerable Failure (MFT) in terms of how many disks can fail, simplyblock defines
it as the number of nodes that can fail.

<Multipathing>

<Encryption>

## Technologies in Simplyblock

Building strong and reliable distributed storage technology has to build on a strong foundation. That's why simplyblock
uses a variety of open source key technologies as its basis.

| Component        | Technologies                                                                                                                                                                                                                                                               |
|------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Networking       | [NVMe-oF](https://nvmexpress.org/){:target="_blank"}, [NVMe/TCP](../important-notes/terminology.md#nvmetcp-nvme-over-tcp), [NVMe/RoCE](../important-notes/terminology.md#nvmeroce-nvme-over-rdma-over-converged-ethernet), [DPDK](https://www.dpdk.org/){:target="_blank"} |
| Storage          | [SPDK](https://spdk.io/){:target="_blank"}, [FoundationDB](https://www.foundationdb.org/){:target="_blank"}, [MongoDB](https://www.mongodb.com/){:target="_blank"}                                                                                                         |
| Observability    | [Prometheus](https://prometheus.io/){:target="_blank"}, [Thanos](https://thanos.io/){:target="_blank"}, [Grafana](https://grafana.com/){:target="_blank"}                                                                                                                  |
| Logging          | [Graylog](https://graylog.org/){:target="_blank"}, [OpenSearch](https://opensearch.org/){:target="_blank"}                                                                                                                                                                 |
| Kubernetes       | [SPDK CSI](https://github.com/spdk/spdk-csi){:target="_blank"}, [Kubernetes CSI](https://kubernetes-csi.github.io/docs/){:target="_blank"}                                                                                                                                 |
| Operating System | [Linux](https://www.kernel.org/){:target="_blank"}                                                                                                                                                                                                                         |
