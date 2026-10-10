---
title: "Deployment Preparation"
description: "Hardware, devices, network links and ports, Kubernetes prerequisites, and hub connectivity for simplyblock edge clusters."
weight: 10107
---

{{ experimental }}

## Hub

The hub is a Kubernetes cluster in the datacenter that runs the simplyblock control plane with the standalone
profile of the Simplyblock Operator. It is installed as described in
[Install Simplyblock Operator](../kubernetes/installation/k8s-control-plane.md), with two additions for edge
clusters:

- **Reachable Management API:** The Management API must be reachable from every edge site, for example, through a
  LoadBalancer Service, an OpenShift Route, or an Ingress. Edge clusters reject loopback and link-local endpoints.
- **Admin token for edges:** A Secret with a static admin token, referenced by
  `controlplane.local.adminTokenSecretRef`. An edge operator authenticates with this token, because a Kubernetes
  service account token of the edge cannot be verified by the hub.

The hub sizing follows the control plane requirements in
[Control Plane Cluster Architecture](../kubernetes/installation/management-cluster-architecture.md). One control
plane manages many edge clusters.

## Edge Hardware

Each storage node of an edge cluster needs:

- **CPU and memory:** Dedicated CPU cores and huge pages for the storage node, as for any simplyblock storage node.
  See [Hardware Requirements](../deployment-preparation/hardware-requirements.md).
- **Devices:** NVMe devices, or Linux block devices in the experimental
  [Linux block device mode](../architecture/concepts/linux-block-devices.md), for example, SATA or SAS SSDs or
  cloud volumes.
- **Journal:** With NVMe devices, a journal partition is carved out of every device, unless one device is smaller
  than the others and is dedicated to the journal. With Linux block devices, one device is always dedicated to the
  journal, so a worker needs at least two devices.

A one-node edge cluster runs storage and workloads on the same worker. On a worker that is also a Kubernetes control
plane node, as in many small edge clusters, the discovery must be allowed to use control plane nodes (see
[Deployment](deployment.md#discovering-the-workers-and-devices)).

## Network

### Ports

The edge operator connects to the Management API of the hub. The control plane on the hub connects to the storage
nodes at the edge. Both directions must be open between the hub and every edge worker that runs a storage node:

| Direction   | From           | To               | Port(s)                            | Protocol |
|-------------|----------------|------------------|------------------------------------|----------|
| Edge to hub | Edge workers   | Management API   | Port of the exposed Management API | TCP      |
| Hub to edge | Control plane  | Storage node API | 5000                               | TCP      |
| Hub to edge | Control plane  | Storage node RPC | 8080-9044                          | TCP      |
| Within edge | Clients, nodes | Storage nodes    | 4420-4499                          | TCP      |

The complete port list is in [Create a Storage Cluster](../kubernetes/installation/k8s-storage-plane.md#networking).

### Links for Two-Node Edge Clusters (Preview)

A two-node edge cluster needs two independent paths:

- **Link between the nodes:** Carries journal and data replication between the two storage nodes. A direct cable or
  a dedicated switch is recommended.
- **Management uplink:** Connects each node to the hub. It must use a different network interface and switch than the
  link between the nodes.

Latency to the hub matters for two-node edge clusters. A failover decision must reach the nodes within the hold
time of 2.5 seconds, which works with a WAN round-trip time in the low hundreds of milliseconds.

## Kubernetes and OpenShift

- **Kubernetes distribution:** A supported Kubernetes or OpenShift version, with the prerequisites of
  [Create a Storage Cluster](../kubernetes/installation/k8s-storage-plane.md#prerequisites) on every storage worker.
- **Two-node OpenShift:** A two-node OpenShift cluster needs a tie-breaker for its own etcd, either OpenShift with an
  arbiter node or OpenShift with fencing through the BMCs of the servers. This is independent of the storage
  arbitration on the hub.
- **Node remediation:** For two-node edge clusters, a node remediation mechanism, such as Node Health Check with Self
  Node Remediation or Fence Agents Remediation, lets Kubernetes restart workloads of a failed node. Without it,
  workloads on a failed node wait for the default eviction timeout.

## Credentials

Before the deployment, the following must be at hand:

- **Management API endpoint:** The URL of the Management API of the hub, as reachable from the edge.
- **Admin token:** The token stored in the hub Secret referenced by `controlplane.local.adminTokenSecretRef`.
- **CA certificate:** The CA that signed the certificate of the Management API, if it is not in the system trust
  store.
- **Storage node image:** The simplyblock storage node image of the release, because an edge cluster has no local
  control plane that names it.
