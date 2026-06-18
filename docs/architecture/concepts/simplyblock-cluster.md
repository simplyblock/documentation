---
title: Simplyblock Cluster
description: "Simplyblock Cluster: The simplyblock storage platform consists of three different types of cluster nodes and belongs to the control plane or storage plane."
weight: 30000
---

The simplyblock storage platform consists of three different types of cluster nodes and belongs to the control plane
or storage plane. 

A node, in simplyblock terminology, is either a set of pods in Kubernetes or a stack of Docker containers deployed under 
plain Linux.

## Control Plane

The control plane orchestrates, monitors, and controls the overall storage infrastructure. It provides centralized
administration, policy enforcement, and automation for managing storage nodes, logical volumes (LVs), and cluster-wide
configurations. The control plane operates independently of the storage plane, ensuring that control and metadata
operations do not interfere with data processing. It facilitates provisioning, fault management, and system scaling
while offering APIs and CLI tools for seamless integration with external management systems. A single control plane
can manage multiple clusters.

The control plane is distributed and can be deployed either on plain Linux (using Docker containers) or 
into an existing Kubernetes cluster. Within Kubernetes, an operator is part of the control plane and uses its own API
services.

Using the operator, storage cluster operations are fully based on Custom Resource Definitions (CRDs) and become entirely
Kubernetes-native.

The control plane also contains an optional observability stack to get started quickly. For large deployments, users 
usually integrate feeds of telemetry and logs with their own, often preexisting, observability stack. 

## Storage Plane

The storage plane is the layer responsible for managing and distributing data across storage nodes within a cluster. It
handles data placement, replication, fault tolerance, and access control, ensuring that logical volumes (LVs) provide
high-performance, low-latency storage to applications. The storage plane operates independently of the control plane,
allowing seamless scalability and dynamic resource allocation without disrupting system operations. By leveraging
NVMe-oF (TCP and RoCEv2) and software-defined storage principles, simplyblock’s storage plane ensures efficient data distribution,
high availability, and resilience, making it ideal for cloud-native and high-performance computing environments.

It either deploys onto plain Linux (Docker containers) or as pods into existing Kubernetes clusters, where it can be run
on dedicated storage node workers or in a mix with compute (hyper-converged). 

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
availability for logical volumes using NVMe-oF multipathing. In a highly available cluster, simplyblock automatically
provisions secondary nodes alongside primary nodes and assigns one secondary node per primary.

## Client-side Storage Drivers

This includes the Kubernetes CSI driver, the Proxmox driver, and the OpenStack driver (experimental). Those drivers automate
volume lifecycle operations such as creating, attaching, resizing, deleting, snapshotting, and cloning volumes. In Kubernetes,
the Simplyblock Operator provides additional volume lifecycle management beyond the constraints of the standard CSI Model.


