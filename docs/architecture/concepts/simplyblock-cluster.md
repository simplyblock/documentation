---
title: Simplyblock Cluster
weight: 30000
---

The simplyblock storage platform consists of three different types of cluster nodes and belongs to the control plane
or storage plane.

## Control Plane

The control plane orchestrates, monitors, and controls the overall storage infrastructure. It provides centralized
administration, policy enforcement, and automation for managing storage nodes, logical volumes (LVs), and cluster-wide
configurations. The control plane operates independently of the storage plane, ensuring that control and metadata
operations do not interfere with data processing. It facilitates provisioning, fault management, and system scaling
while offering APIs and CLI tools for seamless integration with external management systems. A single control plane
can manage multiple clusters.

## Storage Plane

The storage plane is the layer responsible for managing and distributing data across storage nodes within a cluster. It
handles data placement, replication, fault tolerance, and access control, ensuring that logical volumes (LVs) provide
high-performance, low-latency storage to applications. The storage plane operates independently of the control plane,
allowing seamless scalability and dynamic resource allocation without disrupting system operations. By leveraging
NVMe-over-TCP and software-defined storage principles, simplyblock’s storage plane ensures efficient data distribution,
high availability, and resilience, making it ideal for cloud-native and high-performance computing environments.

## Management Node

A management node is a node of the control plane cluster. The management node runs the necessary management services
including the Cluster API, services such as Grafana, Prometheus, and Graylog, as well as the FoundationDB database
cluster.

## Storage Node

A storage node is a node of the storage plane cluster. The storage node provides storage capacity to the distributed
storage pool of a specific storage cluster. The storage node runs the necessary data management services including
the Storage Node Management API, the SPDK service, and handles logical volume primary connections of NVMe-oF
multipathing.

## Secondary Node

A secondary node is a node of the storage plane cluster. The secondary node provides automatic fail over and high
availability for logical volumes using NVMe-oF multipathing. Simplyblock requires additional secondary nodes for
a fully high available cluster to minimize performance impact in case of a storage node failure.
