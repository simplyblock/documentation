---
title: "Terminology"
weight: 20400
params:
sidebar:
forceLinkTitle: "Terminology"
cascade:
type: "docs"
---

## Storage Related Terms

### Storage Pool

A storage pool is a logical aggregation of multiple physical storage devices that provides a flexible and scalable
foundation for managing storage resources. By pooling storage from different drives or nodes, a storage pool enables
efficient capacity management, redundancy, and performance optimization through techniques such as thin provisioning,
replication, and erasure coding. Storage pools are commonly used in software-defined storage (SDS), hyper-converged
infrastructure (HCI), and enterprise storage systems to simplify storage provisioning and dynamically allocate space
based on workload demands. This abstraction layer improves fault tolerance, scalability, and resource utilization in
modern storage architectures.

### Storage Device

A storage device is a hardware component or system that stores and retrieves digital data in computing environments.
Storage devices can be classified into different types based on technology and access speed, including hard disk
drives (HDDs), solid-state drives (SSDs), NVMe drives, and optical or tape storage. They can be locally attached to a
single machine or shared across multiple systems in networked storage architectures such as Storage Area Networks (SANs)
and Network-Attached Storage (NAS). Modern distributed and cloud environments leverage software-defined storage (SDS) to
manage multiple storage devices efficiently, ensuring scalability, redundancy, and optimized data access for various
applications.

### NVMe (Non-Volatile Memory Express)

NVMe (Non-Volatile Memory Express) is a high-performance storage protocol explicitly designed for flash-based storage
devices like SSDs, leveraging the PCIe (Peripheral Component Interconnect Express) interface for ultra-low latency and
high throughput. Unlike traditional protocols such as SATA or SAS, NVMe takes advantage of parallelism and multiple
queues, significantly improving data transfer speeds and reducing CPU overhead. It is widely used in enterprise storage,
cloud computing, and high-performance computing (HPC) environments, where speed and efficiency are critical. NVMe is
also the foundation for NVMe-over-Fabrics (NVMe-oF), which extends its benefits across networked storage systems,
enhancing scalability and flexibility in distributed environments.

### NVMe-oF (NVMe over Fabrics)

NVMe-oF (NVMe over Fabrics) is an extension of the NVMe (Non-Volatile Memory Express) protocol that enables
high-performance, low-latency access to remote NVMe storage devices over network fabrics such as TCP, RDMA (RoCE,
iWARP), and Fibre Channel (FC). Unlike traditional networked storage protocols, NVMe-oF maintains the efficiency and
parallelism of direct-attached NVMe storage while allowing disaggregation of compute and storage resources. This
architecture improves scalability, resource utilization, and flexibility in cloud, enterprise, and high-performance
computing (HPC) environments. NVMe-oF is a key technology in modern software-defined and disaggregated storage
infrastructures, providing fast and efficient remote storage access.

### NVMe/TCP (NVMe over TCP)

NVMe/TCP (NVMe over TCP) is a transport protocol that extends NVMe-over-Fabrics (NVMe-oF) using standard TCP/IP networks
to enable high-performance, low-latency access to remote NVMe storage. By leveraging existing Ethernet infrastructure,
NVMe/TCP eliminates the need for specialized networking hardware such as RDMA (RoCE or iWARP) or Fibre Channel (FC),
making it a cost-effective and easily deployable solution for cloud, enterprise, and data center storage environments.
It maintains the efficiency of NVMe, providing scalable, high-throughput, and low-latency remote storage access while
ensuring broad compatibility with modern network architectures.

### NVMe/RoCE (NVMe over RDMA over Converged Ethernet)

NVMe/RoCE (NVMe over RoCE) is a high-performance storage transport protocol that extends NVMe-over-Fabrics (NVMe-oF)
using RDMA over Converged Ethernet (RoCE) to enable ultra-low-latency and high-throughput access to remote NVMe storage
devices. By leveraging Remote Direct Memory Access (RDMA), NVMe/RoCE bypasses the CPU for data transfers, reducing
latency and improving efficiency compared to traditional TCP-based storage protocols. This makes it ideal for
high-performance computing (HPC), enterprise storage, and latency-sensitive applications such as financial trading and
AI workloads. NVMe/RoCE requires lossless Ethernet networking and specialized NICs to fully utilize its performance
advantages.

### Multipathing

Multipathing is a storage networking technique that enables multiple physical paths between a compute system and a
storage device to improve redundancy, load balancing, and fault tolerance. Multipathing enhances performance and
reliability by using multiple connections, ensuring continuous access to storage even if one path fails. It is commonly
implemented in Fibre Channel (FC), iSCSI, and NVMe-oF (including NVMe/TCP and NVMe/RoCE) environments, where high
availability and optimized data transfer are critical.

### Storage Node

A storage node in a distributed storage cluster is a physical or virtual machine that contributes storage resources to
the cluster, providing a portion of the overall storage capacity and participating in data distribution, redundancy, and
retrieval processes. Each storage node typically runs specialized storage software to manage data placement,
replication, and access, ensuring high availability and fault tolerance. In modern distributed storage architectures,
storage nodes communicate with one another to maintain data consistency, balance workloads, and optimize performance,
often using techniques such as erasure coding or replication to safeguard against node failures.

### Management Node

A management node is a containerized component that orchestrates, monitors, and controls the distributed storage
cluster. It forms part of the control plane, managing cluster-wide configurations, provisioning logical volumes,
handling metadata operations, and ensuring overall system health. Management nodes facilitate communication between
storage nodes and client applications, enforcing policies such as access control, data placement, and fault tolerance.
They also provide an interface for administrators to interact with the storage system via the Simplyblock CLI or API,
enabling seamless deployment, scaling, and maintenance of the storage infrastructure.

### Storage Cluster

A storage cluster is a group of interconnected storage nodes that work together to provide a scalable, fault-tolerant,
and high-performance storage system. Unlike traditional single-node storage solutions, storage clusters distribute data
across multiple nodes, ensuring redundancy, load balancing, and resilience against hardware failures. To optimize data
availability and efficiency, these clusters can be configured using different architectures, such as replication,
erasure coding, or software-defined storage (SDS). Storage clusters are commonly used in cloud storage, high-performance
computing (HPC), and enterprise data centers, enabling seamless scalability and improved data accessibility across
distributed environments.

### Erasure Coding

Erasure coding is a data protection technique used in distributed storage systems to provide fault tolerance and
redundancy while minimizing storage overhead. It works by breaking data into k data fragments and generating m parity
fragments using mathematical algorithms. These k + m fragments are then distributed across multiple storage nodes,
allowing the system to reconstruct lost or corrupted data from any k available fragments. Compared to traditional
replication, erasure coding offers greater storage efficiency while maintaining high availability, making it ideal for
cloud storage, object storage, and high-performance computing (HPC) environments where durability and cost-effectiveness
are critical.

### Replication

Replication in storage is the process of creating and maintaining identical copies of data across multiple storage
devices or nodes to ensure fault tolerance, high availability, and disaster recovery. Replication can occur
synchronously, where data is copied in real-time to ensure consistency, or asynchronously, where updates are delayed to
optimize performance. It is commonly used in distributed storage systems, cloud storage, and database management to
protect against hardware failures and data loss. By maintaining redundant copies, replication enhances data resilience,
load balancing, and accessibility, making it a fundamental technique for enterprise and cloud-scale storage solutions.

### RAID (Redundant Array of Independent Disks)

RAID (Redundant Array of Independent Disks) is a data storage technology that combines multiple physical drives into a
single logical unit to improve performance, fault tolerance, or both. RAID configurations vary based on their purpose:
RAID 0 (striping) enhances speed but offers no redundancy, RAID 1 (mirroring) duplicates data for high availability and
RAID 5, 6, and 10 use combinations of striping and parity to balance performance and fault tolerance. RAID is widely
used in enterprise storage, servers, and high-performance computing to protect against drive failures and optimize data
access. It can be implemented in hardware controllers or software-defined storage solutions, depending on system
requirements.

### Quality of Service

Quality of Service (QoS) refers to the ability to define and enforce performance guarantees for storage workloads by
controlling key metrics such as IOPS (Input/Output Operations Per Second), throughput, and latency. QoS ensures that
different applications receive appropriate levels of performance, preventing resource contention in multi-tenant
environments. By setting limits and priorities for Logical Volumes (LVs), Simplyblock allows administrators to allocate
storage resources efficiently, ensuring critical workloads maintain consistent performance even under high demand.
This capability is essential for optimizing storage operations, improving reliability, and meeting service-level
agreements (SLAs) in distributed cloud-native environments.

### SPDK (Storage Performance Development Kit)

Storage Performance Development Kit (SPDK) is an open-source set of libraries and tools designed to optimize
high-performance, low-latency storage applications by bypassing traditional kernel-based I/O processing. SPDK leverages
user-space and polled-mode drivers to eliminate context switching and interrupts, significantly reducing CPU overhead
and
improving throughput. It is particularly suited for NVMe storage, NVMe-over-Fabrics (NVMe-oF), and iSCSI target
acceleration, making it a key technology in software-defined storage solutions. By providing a highly efficient
framework for storage processing, SPDK enables modern storage architectures to achieve high IOPS, reduced latency, and
better resource utilization in cloud and enterprise environments.

### Volume Snapshot

A volume snapshot is a point-in-time copy of a storage volume, file system, or virtual machine that captures its state
without duplicating the entire data set. Snapshots enable rapid data recovery, backup, and versioning by preserving only
the changes made since the last snapshot, often using copy-on-write (COW) or redirect-on-write (ROW) techniques to
minimize storage overhead. They are commonly used in enterprise storage, cloud environments, and virtualized systems to
ensure data consistency, quick rollback capabilities, and protection against accidental deletions or system failures.
Unlike full backups, snapshots are lightweight and allow near-instantaneous recovery of data.

### Volume Clone

A volume clone is an exact, fully independent copy of a storage volume, virtual machine, or dataset that can be used for
testing, development, backup, or deployment purposes. Unlike snapshots, which capture a point-in-time state and depend
on the original data, a clone is a complete duplication that can operate separately without relying on the source.
Cloning is commonly used in enterprise storage, cloud environments, and containerized applications to create quick,
reproducible environments for workloads without affecting the original data. Storage systems often use thin cloning to
optimize space by sharing unchanged data blocks between the original and the clone, reducing storage overhead. COW is
widely implemented in storage virtualization and containerized environments, enabling fast, space-efficient backups,
cloning, and data protection while maintaining high system performance.

### CoW (Copy-on-Write)

Copy-on-Write (COW) is an efficient data management technique used in snapshots, cloning, and memory management to
optimize storage usage and performance. Instead of immediately duplicating data, COW defers copying until a modification
is made, ensuring that only changed data blocks are written to a new location. This approach minimizes storage overhead,
speeds up snapshot creation, and reduces unnecessary data duplication.

![type:video](https://www.youtube.com/embed/wMy1r8RVTz8?si=mOl3nfBqkEtVGZH9)

## Kubernetes Related Terms

### Kubernetes

[Kubernetes (K8s)](https://kubernetes.io/){:target="_blank" rel="noopener"} is an open-source container orchestration
platform that automates the deployment, scaling, and management of containerized applications across clusters of
machines. Initially developed by Google and now maintained by
the [Cloud Native Computing Foundation (CNCF)](https://www.cncf.io/){:target="_blank" rel="noopener"},
Kubernetes provides a robust framework for load balancing, self-healing, storage orchestration, and automated rollouts
and rollbacks. It manages application workloads using Pods, Deployments, Services, and Persistent Volumes (PVs),
ensuring scalability and resilience. By abstracting underlying infrastructure, Kubernetes enables organizations to
efficiently run containerized applications across on-premises, cloud, and hybrid environments, making it a cornerstone
of modern cloud-native computing.

### Kubernetes CSI (Container Storage Interface)

The [Kubernetes Container Storage Interface (CSI)](https://kubernetes-csi.github.io/docs/drivers.html){:target="_blank"
rel="noopener"}
is a standardized API enabling external storage providers to integrate their storage solutions with Kubernetes. CSI
allows Kubernetes to dynamically provision, attach, mount, and manage Persistent Volumes (PVs) across different storage
backends without requiring changes to the Kubernetes core. Using a CSI driver, storage vendors can offer block and file
storage to Kubernetes workloads, supporting advanced features like snapshotting, cloning, and volume expansion. CSI
enhances Kubernetes’ flexibility by enabling seamless integration with cloud, on-premises, and software-defined storage
solutions, making it the de facto method for managing storage in containerized environments.

### Pod

A Pod in Kubernetes is the smallest and most basic deployable unit, representing a single instance of a running process
in a cluster. A Pod can contain one or multiple containerized applications that share networking, storage, and runtime
configurations, enabling efficient communication and resource sharing. Kubernetes schedules and manages Pods, ensuring
they are deployed on suitable worker nodes based on resource availability and constraints. Since Pods are ephemeral,
they are often managed by higher-level controllers like Deployments, StatefulSets, or DaemonSets to maintain
availability and scalability. Pods facilitate scalable, resilient, and cloud-native application deployments across
diverse infrastructure environments.

### Persistent Volume

A Persistent Volume (PV) is a cluster-wide Kubernetes storage resource that provides durable and independent storage for
Pods, allowing data to persist beyond the lifecycle of individual containers. Unlike ephemeral storage, which is tied to
a Pod’s runtime, a PV is provisioned either statically by an administrator or dynamically using StorageClasses.
Applications request storage by creating Persistent Volume Claims (PVCs), which Kubernetes binds to an available PV
based on capacity and access requirements. Persistent Volumes support different access modes, such as ReadWriteOnce (
RWO), ReadOnlyMany (ROX), and ReadWriteMany (RWX), and are backed by various storage solutions, including local disks,
network-attached storage (NAS), and cloud-based storage services.

### Persistent Volume Claim

A Persistent Volume Claim (PVC) is a request for Kubernetes storage made by a Pod, allowing it to dynamically or
statically access a Persistent Volume (PV). PVCs specify storage requirements such as size, access mode (ReadWriteOnce,
ReadOnlyMany, or ReadWriteMany), and storage class. Kubernetes automatically binds a PVC to a suitable PV based on these
criteria, abstracting the underlying storage details from applications. This separation enables dynamic storage
provisioning, ensuring that Pods can seamlessly consume persistent storage resources without needing direct knowledge of
the storage infrastructure. When a PVC is deleted, its associated PV handling depends on its reclaim policy (Retain,
Recycle, or Delete), determining whether the storage is preserved, cleared, or removed.

### Storage Class

A StorageClass is a Kubernetes abstraction that defines different types of storage available within a cluster, enabling
dynamic provisioning of Persistent Volumes (PVs). It allows administrators to specify storage requirements such as
performance characteristics, replication policies, and backend storage providers (e.g., cloud block storage, network
file systems, or distributed storage systems). Each StorageClass includes a provisioner, which determines how volumes
are created and parameters that define specific configurations for the underlying storage system. By referencing a
StorageClass in a Persistent Volume Claim (PVC), users can automatically provision storage that meets their
application's needs without manually pre-allocating PVs, streamlining storage management in cloud-native environments.

## Network Related Terms

### TCP (Transmission Control Protocol)

Transmission Control Protocol (TCP) is a core communication protocol in the Internet Protocol (IP) suite that ensures
reliable, ordered, and error-checked data delivery between devices over a network. TCP operates at the transport
layer and establishes a connection-oriented communication channel using a three-way handshake process to synchronize
data exchange. It segments large data streams into smaller packets, ensures their correct sequencing, and retransmits
lost packets to maintain data integrity. TCP is widely used in applications requiring stable and accurate data
transmission, such as web browsing, email, and file transfers, making it a fundamental protocol for modern networked
systems.

### UDP (User Datagram Protocol)

User Datagram Protocol (UDP) is a lightweight, connectionless communication protocol in the Internet Protocol (IP) suite
that enables fast, low-latency data transmission without guaranteeing delivery, order, or error correction. Unlike
Transmission Control Protocol (TCP), UDP does not establish a connection before sending data, making it more efficient
for applications prioritizing speed over reliability. It is commonly used in real-time communications, streaming
services, online gaming, and DNS lookups, where occasional data loss is acceptable in exchange for reduced latency and
overhead.

### IP (Internet Protocol), IPv4, IPv6

Internet Protocol (IP) is the fundamental networking protocol that enables devices to communicate over the Internet and
private networks by assigning unique IP addresses to each device. Operating at the network layer of the Internet
Protocol suite, IP is responsible for routing and delivering data packets from a source to a destination based on their
addresses. It functions in a connectionless manner, meaning each packet is sent independently and may take different
paths to reach its destination. IP exists in two primary versions: IPv4, which uses 32-bit addresses, and IPv6, which
uses 128-bit addresses for expanded address space. IP works alongside transport layer protocols like TCP and UDP to
ensure effective data transmission across networks.

### Netmask

A netmask is a numerical value used in IP networking to define a subnet's range of IP addresses. It works by
masking a portion of an IP address to distinguish the network part from the host part. A netmask consists of a series of
binary ones (1s) followed by zeros (0s), where the ones represent the network portion and the zeros indicate the host
portion. Common netmasks include 255.255.255.0 (/24) for standard subnets and 255.255.0.0 (/16) for larger networks.
Netmasks are essential in subnetting, routing, and IP address allocation, ensuring efficient traffic management and
communication within networks.

### CIDR (Classless Inter-Domain Routing)

Classless Inter-Domain Routing (CIDR) is a method for allocating and managing IP addresses more efficiently than the
traditional class-based system. CIDR uses variable-length subnet masking (VLSM) to define IP address ranges with
flexible subnet sizes, reducing wasted addresses and improving routing efficiency. CIDR notation represents an IP
address followed by a slash (/) and a number indicating the number of significant bits in the subnet mask (e.g.,
`192.168.1.0/24` means the first 24 bits define the network, leaving 8 bits for host addresses). Widely used in modern
networking and the internet, CIDR helps optimize IP address distribution and enhances routing aggregation, reducing the
size of global routing tables.

### Hyper-Converged

Hyper-converged refers to an IT infrastructure model that integrates compute, storage, and networking into a single,
software-defined system. Unlike traditional architectures that rely on separate hardware components for each function,
hyper-converged infrastructure (HCI) leverages virtualization and centralized management to streamline operations,
improve scalability, and reduce complexity. This approach enhances performance, fault tolerance, and resource efficiency
by distributing workloads across multiple nodes, allowing seamless scaling by simply adding more nodes. HCI is widely
used in cloud environments, virtual desktop infrastructure (VDI), and enterprise data centers for its ease of
deployment, automation capabilities, and cost-effectiveness.

### Disaggregated

Disaggregated refers to an IT architecture approach where compute, storage, and networking resources are separated into
independent components rather than being tightly integrated within the same physical system. In disaggregated storage,
for example, storage resources are managed independently of compute nodes, allowing for flexible scaling, improved
resource utilization, and reduced hardware dependencies. This contrasts with traditional or hyper-converged
architectures, where these resources are combined. Disaggregated architectures are widely used in cloud computing,
high-performance computing (HPC), and modern data centers to enhance scalability, cost-efficiency, and operational
flexibility while optimizing performance for dynamic workloads.
