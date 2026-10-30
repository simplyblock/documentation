---
title: "Network"
description: "Network requirements of simplyblock: redundant storage networks, NVMe/TCP and NVMe/RoCE fabrics, management traffic, edge sites, and the ports to open."
weight: 29995
---

Simplyblock separates storage traffic, which carries the I/O of the volumes and the traffic between storage nodes,
from management traffic, which connects the control plane with the storage nodes. Both are planned before the
installation.

## Storage Traffic

In production, simplyblock works with one of two options:

- A **redundant network** for storage traffic, for example, through LACP, stacked switches, MLAG, active/active or
  active/passive NICs, STP, or MSTP.
- **Two separate VLANs** per node for storage traffic, connected through two separate NIC ports and switch paths, and
  used with NVMe multipathing (see
  [Failover Paths and Network Paths](../architecture/high-availability-fault-tolerance.md#failover-paths-and-network-paths)).
  A redundant network for management traffic is still recommended in this setup, but it is not required.

For production, software-defined switches, such as a Linux bridge or OVS, cannot be used. An interface on top of a
Linux bond over two ports of the NICs, or an SR-IOV interface, is used instead. At least 10 GBit/s of bandwidth per
storage node is required.

!!! warning
    Any gateway, firewall, or proxy above layer 2 on the storage network path should be avoided for performance
    reasons.

On Kubernetes, the network the SPDK pods serve on is declared per storage cluster. The options and how they meet these
requirements are described in [Storage Network](../kubernetes/installation/storage-network.md).

## Fabrics

Simplyblock implements NVMe over Fabrics, either NVMe/TCP or NVMe/RoCE (RoCEv2), over any Ethernet interconnect. The
transports can be mixed, for example, cluster-internal traffic over NVMe/RoCE and client traffic over NVMe/TCP. The
transport of a cluster is chosen at creation with `fabricType` (see
[Cluster Deployment Options](../kubernetes/installation/cluster-deployment-options.md)).

!!! info
    NICs with RDMA/RoCEv2 support, such as NVIDIA Mellanox ConnectX-6 or higher, can be used to deploy RoCEv2 fabrics
    over standard Ethernet infrastructure. Latency and tail latency over RoCEv2 are usually significantly lower than
    over TCP.

## Management Traffic

A separate physical NIC with two bonded ports and a highly available network is recommended for management traffic.
A 1 GBit/s network is sufficient, and a Linux bridge may be used. The Management API is reached through a Kubernetes
Service, so no external load balancer is needed.

## Ports

It is required to use one or more separate VLANs for simplyblock. Ports within the same VLAN do not require extra
firewall rules, but ports between the control plane and storage networks typically do.

{% include 'network-port-table.md' %}

## Edge Sites

The management traffic of an [edge cluster](../architecture/deployment-topologies/edge-clusters.md) crosses the WAN
to the hub. The following ports must be open between the hub and every edge worker that runs a storage node:

| Direction   | From          | To               | Port(s)                            | Protocol |
|-------------|---------------|------------------|------------------------------------|----------|
| Edge to hub | Edge workers  | Management API   | Port of the exposed Management API | TCP      |
| Hub to edge | Control plane | Storage node API | 5000                               | TCP      |
| Hub to edge | Control plane | Storage node RPC | 8080-9044                          | TCP      |

For two-node edge clusters, a failover decision of the hub must reach the nodes within the hold time of 2.5 seconds,
which works with a WAN round-trip time in the low hundreds of milliseconds.

A two-node edge cluster needs two independent paths: a link between the two storage nodes for journal and data
replication, and the management uplink to the hub. The two paths must not share a switch, a cable, or a network
interface. Otherwise, a single failure cuts both, and the hub cannot tell a failed node from a broken link. A direct
cable or a dedicated switch between the nodes is recommended.

!!! important "Hub Availability for Two-Node Edge Clusters"
    A two-node edge cluster fails over only while the control plane of the hub is reachable, because the hub
    arbitrates between the two nodes. If a node fails while the hub is down or unreachable, the other node fences
    itself and the volumes stay unavailable until the hub is back. The control plane has to run highly available, or
    in a third failure domain that must not share power, network, or location with the two edge nodes. See
    [Availability of the Hub](../architecture/deployment-topologies/edge-clusters.md#availability-of-the-hub).
