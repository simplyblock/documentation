---
title: Simplyblock Cluster
description: "A simplyblock deployment consists of a control plane and one or more storage clusters, whose storage nodes take primary, secondary, and tertiary roles."
weight: 30000
---

A simplyblock deployment consists of two planes: the control plane, which manages the storage, and the storage
plane, which serves it. Both run as pods in Kubernetes and are deployed and managed by the Simplyblock Operator.

## Control Plane

The control plane orchestrates, monitors, and controls the storage clusters. It holds their state, exposes the
management API, runs health checks, collects statistics, and executes long-running tasks, such as node restarts,
migrations, and backups. A single control plane can manage several storage clusters.

The control plane is separate from the storage plane and not in the I/O path: volumes keep serving I/O while it is
unavailable. It consists of the management API, task runners, and a FoundationDB database, and it optionally
includes an observability stack (Prometheus, Grafana, and Graylog) for a quick start. Larger deployments usually
feed metrics and logs into their existing observability stack instead.

On Kubernetes, the Simplyblock Operator manages the control plane and the storage clusters through custom
resources, which makes all storage operations Kubernetes-native. See
[Simplyblock Architecture](../simplyblock-architecture.md#control-plane) for the components.

## Storage Plane

The storage plane stores the data and serves all I/O. It consists of one or more storage clusters, each formed by a
group of storage nodes. Within a cluster, the storage plane handles data placement, erasure coding, failover, and
rebalancing. It runs on dedicated storage workers, on the same workers as the applications (hyper-converged), or in
a mix of both (see [Deployment Topologies](../deployment-topologies/index.md)).

## Storage Node

A storage node is a pod that takes over the storage devices of its Kubernetes worker and contributes them to the
storage cluster. By default, one storage node runs per worker. Workers with several CPU sockets can run one storage
node per socket, each using only the resources of its socket.

Every storage node owns a logical volume store, in which the logical volumes it serves as primary are created. The
data of those volumes is spread across the devices of all storage nodes of the cluster.

## Primary, Secondary, and Tertiary Roles

Every logical volume store is served by more than one storage node, so that its volumes survive a node failure:

- **Primary:** The node that owns the logical volume store and serves the I/O of its volumes.
- **Secondary:** A second node that keeps a ready copy of the logical volume store and takes over when the primary
  fails.
- **Tertiary:** With two parity chunks, a third node that keeps another copy, so that the volumes survive two node
  failures.

These are roles, not node types. Every storage node is the primary of its own logical volume store and, at the same
time, the secondary or tertiary of the stores of other nodes. Only a dedicated secondary node, which is optional,
holds no store of its own. The roles are assigned when the cluster is activated
and always placed on different hosts and, with [failure domains](failure-domains.md), in different domains wherever
possible. See [High Availability and Fault Tolerance](../high-availability-fault-tolerance.md#node-failures).

## Client-Side Storage Drivers

Client-side drivers connect workloads to their volumes and automate the volume lifecycle: creating, attaching,
resizing, snapshotting, cloning, and deleting. On Kubernetes, this is the simplyblock CSI driver, complemented by the
Simplyblock Operator for operations beyond the standard CSI model. Drivers for Proxmox and OpenStack
are available as well.
