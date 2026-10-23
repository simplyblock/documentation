---
title: "Upgrading Amazon EKS"
description: "Upgrade the Kubernetes version of an Amazon EKS cluster that runs simplyblock: the EKS control plane, the control plane node group, and new storage capacity."
weight: 10135
---

An Amazon EKS cluster that runs simplyblock is upgraded to a new Kubernetes version in steps. The EKS control plane
moves first, then the node group of the simplyblock control plane, one node at a time. Storage node groups are not
rolled in place: new storage capacity is added as a new node group on the new version, and volumes move onto it with an
online migration.

This page covers the Kubernetes version of the EKS cluster. Upgrading simplyblock itself is described in
[Upgrading a Cluster](cluster-upgrade.md).

## Prerequisites

- The control plane persistence is backed by Amazon EBS (see
  [Storage for the Control Plane](../../../deployment-preparation/amazon-eks.md#storage-for-the-control-plane)). An
  upgrade of a managed node group replaces its nodes with new instances, and host-local data does not survive it.
- The control plane node group has `updateConfig.maxUnavailable: 1`, so that only one control plane node is replaced at
  a time.
- The control plane is `Available` and every storage cluster is `active` before the upgrade starts.

```bash title="Checking the state before the upgrade"
kubectl -n simplyblock get controlplane
kubectl -n simplyblock get storageclusters
```

## Upgrade Order

1. Upgrade the EKS control plane to the next Kubernetes version.
2. Upgrade the node group of the simplyblock control plane to the same version.
3. Leave the storage and client node groups on the previous version, or replace them as described below.

Kubernetes allows nodes to run up to three minor versions behind the EKS control plane, so storage and client nodes keep
running while the control plane is upgraded.

### Upgrading the EKS Control Plane

```bash title="Upgrading the EKS control plane"
eksctl upgrade cluster --name <CLUSTER_NAME> --version <NEW_VERSION> --approve
```

While the EKS control plane is upgraded, the Kubernetes API can be briefly unavailable. Simplyblock I/O and the
simplyblock Management API do not depend on the Kubernetes API, and they continue.

### Upgrading the Control Plane Node Group

```bash title="Upgrading the control plane node group"
eksctl upgrade nodegroup --cluster <CLUSTER_NAME> --name <CONTROL_PLANE_NODE_GROUP> \
    --kubernetes-version <NEW_VERSION>
```

EKS replaces the nodes of the group one by one. For each node, it starts a new instance, drains the old node, and
terminates it. The control plane pods of the drained node start on the new node, and the EBS volumes of FoundationDB
and Prometheus attach to it. FoundationDB keeps serving from its remaining processes while one node is replaced.

The following is watched while the node group is replaced:

```bash title="Watching the control plane during the node group upgrade"
kubectl get nodes -l sb-role=controlplane -L sb-role
kubectl -n simplyblock get pods -o wide | grep -E "fdb-cluster|webappapi|tasks"
kubectl -n simplyblock get controlplane
```

The upgrade is complete when every control plane node runs the new version, every FoundationDB process pod is
`Running`, and the control plane is `Available`.

!!! note
    The Management API runs with two replicas. While a replica is evicted from a drained node, requests that the
    Service still routes to it can fail for a few seconds.

## Storage and Client Node Groups

Storage nodes hold data, and a storage node that is replaced by a new instance loses its local NVMe instance storage.
Storage node groups are therefore not upgraded with `eksctl upgrade nodegroup`.

New storage capacity on the new Kubernetes version is added as a new node group:

1. Create a new storage node group. It runs the version of the upgraded EKS control plane.
2. Run a discovery against the new node group and approve the draft, as described in
   [Additional Storage Clusters](../../installation/eks.md#additional-storage-clusters).
3. Move the volumes from the old storage cluster to the new one with an online migration, using
   [asynchronous replication](../data-protection/asynchronous-replication.md) in the `migration` mode.
4. Remove the old storage cluster and its node group once all volumes have moved.

Client node groups are replaced like any other workload node group. A replacement client node group uses a node image
with native NVMe multipathing (see [Node Images](../../../deployment-preparation/amazon-eks.md#node-images)).
