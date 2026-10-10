---
title: "Deployment"
description: "Deploy a simplyblock edge cluster: prepare the hub, install the operator at the edge in the managed profile, discover devices, and approve the cluster."
weight: 10108
---

{{ experimental }}

The deployment of an edge cluster has four steps:

1. **Prepare the hub** once for all edge clusters.
2. **Install the operator** at the edge in the managed profile.
3. **Discover** the workers and devices of the edge and review the draft.
4. **Approve** the draft, which creates the storage cluster through the hub.

## Preparing the Hub

The hub runs the control plane with the standalone profile. An admin token lets edge operators authenticate:

```bash title="Create the admin token Secret on the hub"
kubectl create namespace simplyblock
kubectl -n simplyblock create secret generic sb-admin-token \
    --from-literal=token="$(openssl rand -hex 32)"
```

```bash title="Install the operator and control plane on the hub"
helm repo add simplyblock https://install.simplyblock.io/helm
helm repo update

helm install simplyblock-operator simplyblock/simplyblock-operator \
    --namespace simplyblock \
    --set deployment.profile=standalone \
    --set controlplane.local.adminTokenSecretRef=sb-admin-token
```

The Management API must be reachable from the edge sites. One way is a LoadBalancer Service with the selector of the
`simplyblock-webappapi` Service:

```bash title="Expose the Management API to the edge sites"
kubectl -n simplyblock expose service simplyblock-webappapi \
    --name simplyblock-webappapi-edge --type LoadBalancer
kubectl -n simplyblock get service simplyblock-webappapi-edge
```

An OpenShift Route or an Ingress works as well. The address and port of the exposed Service form the Management API
endpoint of the edge clusters.

## Installing the Operator at the Edge

On the Kubernetes cluster of the edge site, the operator is installed with the managed profile. The token Secret
holds the admin token of the hub. The CA Secret is only needed if the certificate of the Management API is not
signed by a CA in the system trust store.

```bash title="Create the Secrets at the edge"
kubectl create namespace simplyblock
kubectl -n simplyblock create secret generic cp-token \
    --from-literal=token='<ADMIN-TOKEN-OF-THE-HUB>'
kubectl -n simplyblock create secret generic cp-ca \
    --from-file=ca.crt=./control-plane-ca.crt
```

```bash title="Install the operator in the managed profile"
helm install simplyblock-operator simplyblock/simplyblock-operator \
    --namespace simplyblock \
    --set deployment.profile=managed \
    --set controlplane.managed.endpoint=https://<HUB-MANAGEMENT-API> \
    --set controlplane.managed.credentialsSecretRef=cp-token \
    --set controlplane.managed.caBundleSecretRef=cp-ca \
    --set controlplane.managed.storageNodeImage=<STORAGE-NODE-IMAGE>
```

`storageNodeImage` is the storage node image of the release. An edge cluster has no local control plane that names
it, so a storage cluster without its own image setting needs this default.

The `ControlPlane` resource reaches the phase `Available` once the hub answers:

```bash title="Check the connection to the hub"
kubectl -n simplyblock get controlplane simplyblock
kubectl -n simplyblock get simplyblockdriver simplyblock
```

The general description of the managed profile is in
[Connecting to an External Control Plane](../kubernetes/installation/install-csi.md).

## Discovering the Workers and Devices

A discovery run inspects the workers and writes a draft (`ClusterDeploymentConfig`). Small edge clusters often run
storage on nodes that are also Kubernetes control plane nodes, which the discovery skips by default.

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
    # Linux block devices instead of NVMe devices (experimental):
    # enableLogicalBlockDevices: true
    # forceJournalDevice: true
```

```bash title="Run the discovery"
kubectl apply -f discover-edge.yaml
kubectl -n simplyblock get operatorops discover-edge -w
kubectl -n simplyblock get clusterdeploymentconfig edge-draft -o yaml
```

With Linux block devices, `forceJournalDevice` lets the run dedicate one of several equal devices to the journal.
Without it, a run over workers with equal devices fails, because Linux block device clusters always need a dedicated
journal device.

## Reviewing the Draft

The draft is reviewed and completed before approval. For a one-node edge cluster, the erasure-coding scheme is 1+0,
because 1+1 needs at least three storage nodes:

```bash title="Set the cluster name, size, and erasure coding of the draft"
kubectl -n simplyblock patch clusterdeploymentconfig edge-draft --type merge -p '{
  "spec": {"cluster": {
    "name": "edge-site-a",
    "vcpuCount": 4,
    "minHugePagesSize": "8G",
    "stripe": {"dataChunks": 1, "parityChunks": 0}
  }}}'
```

The fields of the draft are described in
[Create a Storage Cluster](../kubernetes/installation/k8s-storage-plane.md#review-the-draft).

## Approving the Deployment

```bash title="Approve the draft"
kubectl -n simplyblock patch clusterdeploymentconfig edge-draft --type merge \
    -p '{"spec":{"approved":true}}'
```

The operator creates the storage cluster in the control plane of the hub, then the storage node and the storage pool.
The pool comes with a StorageClass for the workloads of the site.

## Two-Node Edge Clusters (Preview)

!!! warning "Preview"
    Two-node edge clusters cannot be deployed with this release. The activation of a storage cluster with the
    erasure-coding scheme 1+1 requires three storage nodes, and the arbitration protocol for two nodes is not
    released yet.

    The intended configuration adds a `twoNode` section to the `StorageCluster`:

    ```yaml title="Two-node settings of a StorageCluster (preview)"
    spec:
      twoNode:
        arbitration: true
        preferredNode: edge-worker-1
        holdMs: 2500
        leaseTtlMs: 1500
    ```

    `preferredNode` is the Kubernetes node that continues when neither node reaches the hub nor the other node.
    `holdMs` must stay below the host keep-alive timeout of 5 seconds, and the lease must be shorter than the hold.

## Verifying the Deployment

```bash title="Check the storage cluster, node, pool, and StorageClass"
kubectl -n simplyblock get storagecluster,storagenode,storagepool
kubectl get storageclass
```

The `StorageCluster` reaches the phase `Online`. A test volume confirms the data path:

```yaml title="test-pvc.yaml"
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: edge-test
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: <STORAGE-CLASS-OF-THE-POOL>
  resources:
    requests:
      storage: 1Gi
```

```bash title="Create and check the test volume"
kubectl apply -f test-pvc.yaml
kubectl get pvc edge-test
```
