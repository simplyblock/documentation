---
title: "Edge Cluster Requirements"
description: "Requirements specific to simplyblock edge clusters: hub connectivity, devices, network links and ports, two-node OpenShift options, and credentials."
weight: 29985
---

Edge clusters share the general requirements of simplyblock storage nodes, described in
[Hardware Requirements](hardware-requirements.md) and [Software Requirements](software-requirements.md). This page
lists only what is specific to edge clusters. The architecture is described in
[Edge Clusters](../architecture/deployment-topologies/edge-clusters.md).

## Hub

The hub runs the simplyblock control plane with the standalone profile of the Simplyblock Operator, sized as
described in [Control Plane Cluster Architecture](../kubernetes/installation/management-cluster-architecture.md). One
control plane manages many edge clusters. For edge clusters, the hub additionally needs:

- **Reachable Management API:** The Management API must be reachable from every edge site, for example, through a
  LoadBalancer Service, an OpenShift Route, or an Ingress. Edge clusters reject loopback and link-local endpoints.
- **Admin token:** A Secret with a static admin token, referenced by `controlplane.local.adminTokenSecretRef`. An edge
  operator authenticates with this token, because the hub cannot verify a service account token of another cluster.

## Devices

- **NVMe devices:** A journal partition is carved out of every device, unless one device is smaller than the others
  and is dedicated to the journal.
- **Linux block devices:** SATA or SAS SSDs or cloud volumes in the
  [Linux block device mode](../architecture/concepts/linux-block-devices.md). One device is always dedicated to the
  journal, so a worker needs at least two devices.

Many small edge clusters run storage on Kubernetes control plane nodes. The discovery must then be allowed to use
them (`enableControlPlaneNodes`).

## Network

### Ports Between Hub and Edge

| Direction   | From          | To               | Port(s)                            | Protocol |
|-------------|---------------|------------------|------------------------------------|----------|
| Edge to hub | Edge workers  | Management API   | Port of the exposed Management API | TCP      |
| Hub to edge | Control plane | Storage node API | 5000                               | TCP      |
| Hub to edge | Control plane | Storage node RPC | 8080-9044                          | TCP      |

The ports within the edge site are the same as for any storage cluster, see
[Create a Storage Cluster](../kubernetes/installation/k8s-storage-plane.md#networking).

### Independent Links for Two-Node Edge Clusters

A two-node edge cluster needs two independent paths:

- **Link between the nodes:** Carries journal and data replication between the two storage nodes. A direct cable or
  a dedicated switch is recommended.
- **Management uplink:** Connects each node to the hub. It must use a different network interface and switch than the
  link between the nodes.

A failover decision must reach the nodes within the hold time of 2.5 seconds. This works with a WAN round-trip time
to the hub in the low hundreds of milliseconds.

## Two-Node OpenShift

A two-node OpenShift cluster needs a tie-breaker for its own etcd: OpenShift with an arbiter node, or OpenShift with
fencing through the BMCs of the servers. This is independent of the storage arbitration on the hub.

For two-node edge clusters, a node remediation mechanism, such as Node Health Check with Self Node Remediation or
Fence Agents Remediation, lets Kubernetes restart the workloads of a failed node. Without it, these workloads wait
for the default eviction timeout.

## Credentials

The deployment of an edge cluster needs:

- **Management API endpoint:** The URL of the Management API of the hub, as reachable from the edge.
- **Admin token:** The token stored in the hub Secret referenced by `controlplane.local.adminTokenSecretRef`.
- **CA certificate:** The CA that signed the certificate of the Management API, if it is not in the system trust
  store.
- **Storage node image:** The storage node image of the release, because an edge cluster has no local control plane
  that names it.
