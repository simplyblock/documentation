---
title: "Software Requirements"
description: "Supported Kubernetes distributions and versions, host operating systems and kernels, NVMe multipathing on client nodes, and the requirements of pNFS."
weight: 29999
---

Simplyblock runs on Kubernetes clusters with Linux worker nodes. This page lists the supported distributions, the
requirements of the nodes that consume volumes, and the additional requirements of pNFS.

## Kubernetes Distributions

| Distribution         | Versions         |
|----------------------|------------------|
| EKS                  | 1.30 and higher  |
| GKE                  | 1.30 and higher  |
| K3s                  | 1.33 and higher  |
| Kubernetes (vanilla) | 1.33 and higher  |
| RKE2                 | 1.33 and higher  |
| Talos                | 1.6.7 and higher |
| OpenShift            | 4.19 and higher  |

!!! info
    SUSE Rancher is a management plane, not a Kubernetes distribution. Simplyblock is installed into the downstream
    cluster it manages, which must run a supported RKE2 or K3s version. For details, see
    [SUSE Rancher and RKE2](../kubernetes/installation/rancher.md).

Windows worker nodes are not supported. The operating system of every node must be on the latest patch level. The
verified operating systems for Kubernetes workers are listed in the
[Supported Linux Distributions](../reference/supported-linux-distributions.md#kubernetes-hyper-converged-control-plane-and-storage-plane)
reference.

## Client Nodes

A client node (initiator) is a worker to which simplyblock volumes are attached over NVMe/TCP or NVMe/RoCE. Client
nodes require:

- The `nvme-tcp` kernel module, or `nvme-rdma` for NVMe/RoCE.
- Native NVMe multipathing (`CONFIG_NVME_MULTIPATH`), so that a volume with several paths appears as one device and
  fails over between them. Some cloud node images lack it, for example, the default Amazon Linux 2023 image on EKS (see
  [EKS](../kubernetes/installation/eks.md#node-images) and [GKE](../kubernetes/installation/gke.md#node-images)).

The supported distributions and kernels for client nodes are listed in
[Linux Distributions and Versions](../reference/supported-linux-distributions.md#hosts-initiators-accessing-storage-cluster-over-nvmf)
and [Linux Kernel Versions](../reference/supported-linux-kernels.md).

## pNFS

These requirements apply only when [pNFS volumes](../kubernetes/usage/pnfs.md) (`ReadWriteMany`,
[distributed file storage](../architecture/concepts/distributed-file-storage.md)) are used.
The metadata server's proxy runs on the host network. See
[Host Network and Privileged Workloads](../kubernetes/installation/security.md#host-network-and-privileged-workloads).

**Metadata server node:**

- At least one worker node with a usable `/dev/kvm` (see
  [Virtualization Support for pNFS](hardware-requirements.md#virtualization-support-for-pnfs)). At least two such nodes
  are recommended, so that the metadata server can be rescheduled.
- The operator's namespace must admit privileged pods (for example, the `privileged` Pod Security Standard), because
  the metadata server pod uses the host devices `/dev/kvm` and `/dev/net/tun`.

**Client nodes** (every worker node that runs a pod using a pNFS volume):

- A kernel with the pNFS block layout driver (`CONFIG_PNFS_BLOCK`, usually the `blocklayoutdriver` module), which also
  serves the SCSI layout simplyblock uses, with its support for NVMe devices. The kernel must carry
  `nvme_get_unique_id`, so that the device a layout names can be identified. This is a property of the kernel build,
  not of its version number: Red Hat Enterprise Linux 9.8 (kernel 5.14.0-687) is validated, while Red Hat Enterprise
  Linux 9.5 (kernel 5.14.0-503) lacks it. Debian and Ubuntu are not validated yet. See
  [Kernel Requirements for pNFS Clients](../reference/supported-linux-kernels.md#kernel-requirements-for-pnfs-clients).
- No NFS packages (`nfs-utils`, `nfs-common`) are needed on the host. The NFS client tools ship with the CSI node
  plugin.
- A node that does not meet the kernel requirement still mounts pNFS volumes, but routes all of their data through the
  metadata server.

**Network:**

- NFSv4.1 or NFSv4.2 over TCP port 2049 from every client node to the metadata server pod. Clients mount a Kubernetes
  Service ClusterIP per export, so the CNI must route a kernel NFS mount to a ClusterIP. No portmapper (port 111) and no
  `rpc.statd` are used.
- NVMe/TCP from every client node and from the metadata server pod to the storage nodes, as for block volumes.

**Configuration:**

- pNFS is enabled on the `SimplyblockDriver` resource through `spec.pnfs.mds`. Without it, pNFS volumes stay
  `Pending`. The metadata server's memory limit must be at least `512Mi` (default `2Gi`).
- A StorageClass with `csi.storage.k8s.io/fstype: pnfs`, and a simplyblock StorageClass for the metadata server's
  state disk (`1Gi` by default, created per storage cluster when none is given).

## Edge Clusters

An [edge cluster](../architecture/deployment-topologies/edge-clusters.md) runs the Simplyblock Operator in the managed
profile and connects to the control plane on a hub cluster:

- **Hub:** The control plane runs with the standalone profile. Its Management API is reachable from every edge site,
  for example, through a LoadBalancer Service, an OpenShift Route, or an Ingress. Loopback and link-local endpoints are
  rejected. A Secret with a static admin token, referenced by `controlplane.local.adminTokenSecretRef`, lets edge
  operators authenticate, because the hub cannot verify a service account token of another cluster.
- **Credentials at the edge:** The Management API endpoint, the admin token, the CA certificate of the Management API
  if it is not in the system trust store, and the storage node image of the release.
- **Control plane nodes:** Small edge clusters often run storage on Kubernetes control plane nodes. The discovery must
  then be allowed to use them (`enableControlPlaneNodes`).
- **Two-node OpenShift:** A two-node OpenShift cluster needs a tie-breaker for its own etcd, either OpenShift with an
  arbiter node or OpenShift with fencing through the BMCs of the servers. This is independent of the storage
  arbitration on the hub.
- **Node remediation:** For two-node edge clusters, Node Health Check with Self Node Remediation or Fence Agents
  Remediation lets Kubernetes restart the workloads of a failed node. Without it, they wait for the default eviction
  timeout.

## Other Integrations

- **Proxmox:** Proxmox VE 8.0 and higher.
- **OpenStack:** OpenStack 25.1 (Epoxy) and higher. Support for older versions may be available on request.
