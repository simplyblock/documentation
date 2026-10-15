---
title: "Edge Clusters"
description: "Small simplyblock storage clusters with one or two nodes at edge sites, managed by a central control plane on a hub cluster."
weight: 20254
---

An edge cluster is a small simplyblock storage cluster at an edge site, such as a branch office, a factory, or a
store. It consists of one or two storage nodes on the Kubernetes cluster of the site. The edge cluster does not run a
control plane of its own. It is managed by a central simplyblock control plane on a hub cluster in the datacenter,
which can manage many edge clusters.

![Edge clusters managed by a central simplyblock control plane](../../assets/images/architecture/edge-clusters.svg)

## Components

| Component                         | Runs on      | Role                                                                                                                       |
|-----------------------------------|--------------|----------------------------------------------------------------------------------------------------------------------------|
| Control plane                     | Hub cluster  | Holds the state of every edge storage cluster in FoundationDB, exposes the Management API, and orchestrates storage nodes. |
| Simplyblock Operator (standalone) | Hub cluster  | Installs and operates the control plane on the hub.                                                                        |
| Simplyblock Operator (managed)    | Edge cluster | Discovers workers and devices, creates the storage cluster through the hub, and maintains the CSI configuration.           |
| CSI driver                        | Edge cluster | Provisions and attaches volumes for the workloads of the site.                                                             |
| Storage nodes                     | Edge workers | Serve the volumes over NVMe-oF from local NVMe devices or Linux block devices.                                             |

The hub follows the centralized model described in [Control Plane and Operator](control-plane-and-operator.md). It
can be the same cluster that runs the simplyblock Disaster Recovery hub.

## Control and Data Flow

- **Edge to hub:** The operator at the edge reaches the Management API of the hub over HTTPS. It registers the storage
  cluster, creates its storage nodes and pools, and reads their state. It authenticates with a bearer token.
- **Hub to edge:** The control plane reaches every storage node of every edge on the storage node API and the storage
  node RPC ports. It configures and monitors the storage nodes and runs restarts and recovery.
- **Data path:** Volume I/O stays at the edge. Workloads reach the storage nodes of their own site over NVMe-oF.
  Volume data never crosses the WAN.

Storage at the edge keeps serving I/O while the WAN link to the hub is down. Management operations, such as creating
a volume, and automatic recovery actions of the control plane wait until the link is back.

## High Availability

### One-Node Edge Clusters

A one-node edge cluster has a single storage node and is declared as such (cluster mode `Single`). It is not highly
available: if the node fails, its volumes are unavailable until the node is back. Applications that must survive the
loss of the node need a two-node edge cluster or application-level replication.

Within the node, the cluster still protects against device failures. Erasure coding places every chunk of a stripe
on a different device of the node, so any supported scheme can be used as long as the node has one device per chunk:

| Scheme | Minimum devices | Device failures the data survives |
|--------|-----------------|-----------------------------------|
| 1+0    | 1               | 0                                 |
| 1+1    | 2               | 1                                 |
| 2+1    | 3               | 1                                 |
| 4+1    | 5               | 1                                 |
| 1+2    | 3               | 2                                 |
| 2+2    | 4               | 2                                 |
| 4+2    | 6               | 2                                 |

The journal has its own protection, which depends on where it is placed:

- **Journal partitions (NVMe devices, the default):** The journal is mirrored across the devices of the node: two
  devices form a mirror (RAID 1), more devices form a mirror of two striped groups (RAID 0+1). The journal survives
  the failure of any one device. Two devices failing at the same time are only survived if both are in the same
  group, so a one-node cluster with 1+2, 2+2, or 4+2 is guaranteed to survive one device failure at a time, not
  two at once.
- **Dedicated journal device (`enableJournalDevice`, always used with Linux block devices):** The journal is on one
  device and is not mirrored. A failure of that device stops the node, whatever the erasure-coding scheme.

After a device failure, the data of the failed device is rebuilt onto the remaining devices of the node. This data
migration runs in relaxed placement, which places chunks without the anti-affinity a larger cluster enforces, so it
needs no second node. The remaining devices need enough free capacity to hold the rebuilt data.

### Two-Node Edge Clusters

!!! note
    Two-node edge clusters require two-node arbitration support in the control plane, the Simplyblock Operator, and
    the storage nodes.

A two-node edge cluster (cluster mode `Dual`) uses the erasure-coding scheme 1+1 on exactly two storage nodes and
keeps a copy of the journal and the data on each node. Every volume has a primary on one node and a secondary on the
other, and a workload connects to both over two NVMe-oF paths. When a node fails, the other node takes over
leadership, the active path switches, and I/O continues after a short pause.

A device failure on either node is survived as well: the other node holds a copy of the data and of the journal.
Data migration after a device failure or after adding a device runs in relaxed placement, so it needs no third node.

With only two nodes, a broken link between the nodes looks the same to each node as a failed peer. To prevent both
nodes from writing on their own (split brain), the control plane on the hub acts as the third vote:

- **Hold:** A node that loses the connection to the journal of its peer holds its write I/O for a short time
  (2.5 seconds by default, below the host keep-alive timeout) and reports the event to the hub.
- **Decision:** When one node is lost, the hub grants the surviving node solo operation. When both nodes are
  reachable but cannot reach each other (a broken link between them), the hub fences both nodes, because it cannot
  decide which copy is current. A fenced node returns the held I/O as a path error, so the hosts retry on the other
  path.
- **Leases:** Each node holds a lease from the hub. A lease only matters while a node holds I/O. A slow or broken
  link to the hub never fences a healthy pair.
- **No grant, no solo operation:** A node that has no grant from the hub when the hold time ends fences itself. If
  neither node reaches the hub nor the other node, both nodes fence themselves, and I/O resumes once the hub is
  reachable again.
- **Workload restart:** The operator taints the Kubernetes node of a fenced storage node with
  `storage.simplyblock.io/fenced`, so that Kubernetes and KubeVirt restart the affected workloads on the other node.

#### Availability of the Hub

The arbitration runs in the control plane on the hub, so a failover of a two-node edge cluster needs a reachable
hub. A surviving node never continues on its own, because it cannot tell a failed peer from a broken link. This
trades availability for consistency: without the hub as the third vote, a broken link could leave both nodes writing.

| Situation                                    | Behavior                                                                                                            |
|----------------------------------------------|---------------------------------------------------------------------------------------------------------------------|
| A node fails, hub reachable                  | The surviving node is granted solo operation. I/O pauses for about 0.5 to 2 seconds.                                |
| A node fails, hub not reachable              | The surviving node fences itself when the hold time ends. Volumes are unavailable until the hub is reachable again. |
| The hub is not reachable, both nodes healthy | No effect. An expired lease never fences a healthy node.                                                            |
| The link between the nodes breaks            | Both nodes are fenced. After the link is restored, the hub unfences both and restores leadership.                   |
| A host loses its path to one node            | The host switches to the other path (NVMe multipathing). No hub involvement.                                        |
| Two-node cluster without arbitration         | The surviving node continues on its own, without protection against split brain.                                    |

A node failure during an outage of the hub therefore means downtime. The control plane of the hub has to run highly
available, or in a third failure domain that must not share power, network, or location with the two edge nodes.

## Network Paths

| Path                   | Between                        | Purpose                                                   | Required for           |
|------------------------|--------------------------------|-----------------------------------------------------------|------------------------|
| Management uplink      | Edge workers and the hub       | Management API, storage node API, storage node RPC        | All edge clusters      |
| Storage network        | Edge workers and their clients | NVMe-oF volume traffic                                    | All edge clusters      |
| Link between the nodes | The two storage nodes          | Journal and data replication, second path besides the hub | Two-node edge clusters |

For a two-node edge cluster, the link between the nodes and the management uplink must not share a switch, a cable,
or a network interface. Otherwise, a single failure cuts both paths at the same time, and the hub cannot tell a
failed node from a broken link.

The edge-specific requirements are noted in [Hardware Requirements](../../deployment-preparation/hardware-requirements.md)
and [Software Requirements](../../deployment-preparation/software-requirements.md), the deployment is described in
[Deploying Edge Clusters](../../kubernetes/installation/edge-clusters.md), and the operation in
[Operating Edge Clusters](../../kubernetes/operations/cluster/edge-clusters.md).
