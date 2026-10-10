---
title: "Architecture"
description: "Components, control and data flow, and the high-availability model of one-node and two-node simplyblock edge clusters managed from a hub."
weight: 10106
---

{{ experimental }}

## Overview

An edge deployment splits the management of storage from the storage itself. The simplyblock control plane runs once,
on a hub cluster in the datacenter. Every edge site runs a small Kubernetes cluster with the storage nodes of one
storage cluster, the Simplyblock Operator in the managed profile, and the CSI driver.

![Edge clusters managed by a central simplyblock control plane](../assets/images/architecture/edge-clusters.svg)

## Components

| Component                         | Runs on      | Role                                                                                                                       |
|-----------------------------------|--------------|----------------------------------------------------------------------------------------------------------------------------|
| Control plane                     | Hub cluster  | Holds the state of every edge storage cluster in FoundationDB, exposes the Management API, and orchestrates storage nodes. |
| Simplyblock Operator (standalone) | Hub cluster  | Installs and operates the control plane on the hub.                                                                        |
| Simplyblock Operator (managed)    | Edge cluster | Discovers workers and devices, creates the storage cluster through the hub, and maintains the CSI configuration.           |
| CSI driver                        | Edge cluster | Provisions and attaches volumes for the workloads of the site.                                                             |
| Storage nodes                     | Edge workers | Serve the volumes over NVMe-oF from local NVMe devices or Linux block devices.                                             |

The hub can be the same cluster that runs the simplyblock Disaster Recovery hub. See
[Control Plane and Operator](../architecture/deployment-topologies/control-plane-and-operator.md) for the local and
the centralized placement of the control plane.

## Control and Data Flow

- **Edge to hub:** The operator at the edge reaches the Management API of the hub over HTTPS. It registers the storage
  cluster, creates its storage nodes and pools, and reads their state. It authenticates with a bearer token from a
  Secret.
- **Hub to edge:** The control plane reaches every storage node of every edge on the storage node API and the storage
  node RPC ports. It configures the storage nodes, monitors them, and runs restarts and recovery.
- **Data path:** Volume I/O stays at the edge. Workloads reach the storage nodes of their own site over NVMe-oF.
  Volume data never crosses the WAN.

Storage at the edge keeps serving I/O while the WAN link to the hub is down. Management operations, such as creating a
volume, and automatic recovery actions of the control plane wait until the link is back.

## High Availability

### One-Node Edge Clusters

A one-node edge cluster has a single storage node and is not highly available. Its storage cluster uses the
erasure-coding scheme 1+0, and its journal is kept on the node itself. If the node fails, the volumes are
unavailable until the node is back. Applications that need to survive the loss of the node require a second node
(see below) or application-level replication.

### Two-Node Edge Clusters (Preview)

!!! warning "Preview"
    Two-node edge clusters are not released yet. The control plane, the operator, and the storage nodes need the
    arbitration protocol described here, which is under development. The behavior below may change before release.

A two-node edge cluster keeps a copy of the journal and the data on each node. Every volume has a primary on one node
and a secondary on the other, and a workload connects to both over two NVMe-oF paths. When a node fails, the other
node takes over leadership, the active path switches, and I/O continues after a short pause.

With only two nodes, a broken link between the nodes looks the same to each node as a failed peer. To prevent both
nodes from writing on their own (split brain), the control plane on the hub acts as the third vote:

- **Hold:** A node that loses the connection to the journal of its peer holds its write I/O for a short time
  (2.5 seconds by default, below the host keep-alive timeout) and reports the event to the hub.
- **Decision:** The hub decides which node continues. It grants that node solo operation and fences the other one.
  A fenced node returns the held I/O as a path error, so the hosts retry on the other path.
- **Leases:** Each node holds a lease from the hub. A lease only matters while a node holds I/O. A slow or broken
  link to the hub never fences a healthy pair.
- **Preferred node:** If neither node reaches the hub nor the other node, the preferred node continues after the hold
  time and the other node fences itself.
- **Workload restart:** The operator taints the Kubernetes node of a fenced storage node with
  `storage.simplyblock.io/fenced`, so that KubeVirt and Kubernetes restart the affected workloads on the other node.

Two-node edge clusters require two independent network paths, see
[Deployment Preparation](deployment-preparation.md#network).

## Network Requirements

| Path                   | Between                        | Purpose                                                   | Required for           |
|------------------------|--------------------------------|-----------------------------------------------------------|------------------------|
| Management uplink      | Edge workers and the hub       | Management API, storage node API, storage node RPC        | All edge clusters      |
| Storage network        | Edge workers and their clients | NVMe-oF volume traffic                                    | All edge clusters      |
| Link between the nodes | The two storage nodes          | Journal and data replication, hub-independent second path | Two-node edge clusters |

For a two-node edge cluster, the link between the nodes and the management uplink must not share a switch, a cable,
or a network interface. Otherwise, a single failure cuts both paths at the same time, and the hub cannot tell a failed
node from a broken link.
