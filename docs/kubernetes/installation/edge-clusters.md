---
title: "Deploying Edge Clusters"
description: "Deploy a simplyblock edge cluster with one or two nodes: prepare the hub, install the operator in the managed profile, and approve the draft."
weight: 30250
---

An edge cluster is deployed with the same resources as any storage cluster. This page covers only the steps that
differ for edge clusters. The edge-specific requirements are noted in
[Hardware Requirements](../../deployment-preparation/hardware-requirements.md) and
[Software Requirements](../../deployment-preparation/software-requirements.md).

## Preparing the Hub

The hub runs the control plane with the standalone profile, installed as described in
[Install Simplyblock Operator](k8s-control-plane.md), with an admin token for the edge operators:

```bash title="Create the admin token and install the hub"
kubectl create namespace simplyblock
kubectl -n simplyblock create secret generic sb-admin-token \
    --from-literal=token="$(openssl rand -hex 32)"

helm install simplyblock-operator simplyblock/simplyblock-operator \
    --namespace simplyblock \
    --set deployment.profile=standalone \
    --set controlplane.local.adminTokenSecretRef=sb-admin-token
```

The Management API must be reachable from the edge sites, for example, through a LoadBalancer Service with the
selector of the `simplyblock-webappapi` Service:

```bash title="Expose the Management API to the edge sites"
kubectl -n simplyblock expose service simplyblock-webappapi \
    --name simplyblock-webappapi-edge --type LoadBalancer
```

## Installing the Operator at the Edge

At the edge site, the operator is installed in the managed profile as described in
[Connecting to an External Control Plane](install-csi.md). The token Secret holds the admin token of the hub. An edge
cluster also needs the default storage node image, because it has no local control plane that names it:

```bash title="Install the operator in the managed profile"
helm install simplyblock-operator simplyblock/simplyblock-operator \
    --namespace simplyblock \
    --set deployment.profile=managed \
    --set controlplane.managed.endpoint=https://<HUB-MANAGEMENT-API> \
    --set controlplane.managed.credentialsSecretRef=cp-token \
    --set controlplane.managed.caBundleSecretRef=cp-ca \
    --set controlplane.managed.storageNodeImage=<STORAGE-NODE-IMAGE>
```

## Discovery

The discovery follows [Create a Storage Cluster](k8s-storage-plane.md#manual-discovery). Small edge clusters often run
storage on Kubernetes control plane nodes, which the discovery skips by default:

```yaml title="discover-edge.yaml"
apiVersion: storage.simplyblock.io/v1alpha2
kind: OperatorOps
metadata:
  name: discover-edge
  namespace: simplyblock
spec:
  action: Discover
  discover:
    configName: edge-draft
    enableControlPlaneNodes: true
    # Linux block devices instead of NVMe devices:
    # enableLogicalBlockDevices: true
    # forceJournalDevice: true
```

With Linux block devices, `forceJournalDevice` lets the run dedicate one of several equal devices to the journal. The discovery proposes whole disks only. Partitions of a disk shared with the operating system are selected
explicitly, as described in [Linux Block Devices](../../architecture/concepts/linux-block-devices.md#partitions).

## Draft for a One-Node Edge Cluster

A one-node edge cluster uses the erasure-coding scheme 1+0:

```bash title="One-node edge cluster"
kubectl -n simplyblock patch clusterdeploymentconfig edge-draft --type merge -p '{
  "spec": {"cluster": {
    "name": "edge-site-a",
    "stripe": {"dataChunks": 1, "parityChunks": 0}
  }}}'
```

## Draft for a Two-Node Edge Cluster

!!! note
    Two-node edge clusters require two-node arbitration support in the control plane, the Simplyblock Operator, and
    the storage nodes.

A two-node edge cluster declares `twoNode` in the deployment document. The declaration lets the erasure-coding scheme
1+1 run on exactly two storage nodes, which otherwise needs three. It is copied to `spec.twoNode` of the
`StorageCluster` when the cluster is created:

```bash title="Two-node edge cluster"
kubectl -n simplyblock patch clusterdeploymentconfig edge-draft --type merge -p '{
  "spec": {"cluster": {
    "name": "edge-site-b",
    "stripe": {"dataChunks": 1, "parityChunks": 1},
    "twoNode": {
      "arbitration": true,
      "preferredNode": "edge-worker-1",
      "holdMs": 2500,
      "leaseTtlMs": 1500
    }
  }}}'
```

| Field           | Default | Description                                                                          |
|-----------------|---------|--------------------------------------------------------------------------------------|
| `arbitration`   | Off     | Enables the arbitration of the hub between the two nodes.                            |
| `preferredNode` | —       | Kubernetes node that continues when neither node reaches the hub nor the other node. |
| `holdMs`        | `2500`  | How long a node holds write I/O after losing its peer. Must stay below 5 seconds.    |
| `leaseTtlMs`    | `1500`  | Validity of the lease the hub grants each node. Must be shorter than the hold time.  |

## Approving and Verifying

The draft is approved and the cluster verified as described in
[Create a Storage Cluster](k8s-storage-plane.md#approve-the-deployment). The operator creates the storage cluster in
the control plane of the hub, then the storage nodes and the storage pool with its StorageClass.
