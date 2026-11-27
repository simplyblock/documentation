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
[Install Simplyblock Operator](k8s-control-plane.md), with TLS off and with admin tokens for the edge operators.

The control plane of the hub calls the storage nodes of every edge directly. With TLS on, it calls them over HTTPS and
verifies their certificates against the CA of the hub, which did not sign the certificates of an edge cluster. A hub
with `tls.enabled=false` calls them over plain HTTP at the address of the worker, which is the only way it reaches
remote storage nodes. The `tls` block cannot be changed once the control plane exists, so TLS is turned off at the
first installation. Without TLS, the admin tokens and the management traffic of the storage nodes cross the network
unencrypted. The hub and the edge sites are therefore connected through a VPN or a private link, and the Management API
is exposed on that link only.

The Secret holds the admin tokens under the key `token`, as a comma-separated list. One token per edge site allows a
single site to be revoked. Every token is a full admin credential of the hub, and it can read the cluster secret of
every edge cluster.

Whether the control plane sets up monitoring is decided when the first edge cluster registers. Every later cluster
takes that decision over, so the observability stack is enabled at the installation if it is wanted. Enabling it after
the first edge cluster has registered leaves monitoring off for every edge cluster.

```bash title="Creating the admin tokens of two edge sites and installing the hub"
kubectl create namespace simplyblock
kubectl -n simplyblock create secret generic sb-admin-token \
    --from-literal=token="$(openssl rand -hex 32),$(openssl rand -hex 32)"

helm install simplyblock-operator simplyblock/simplyblock-operator \
    --namespace simplyblock \
    --set deployment.profile=standalone \
    --set tls.enabled=false \
    --set tls.mutual_enabled=false \
    --set controlplane.local.adminTokenSecretRef=sb-admin-token \
    --set controlplane.observability.enabled=true
```

The tokens are read when the Management API starts, and the Secret is not watched. A changed list takes effect after a
restart of `simplyblock-webappapi`:

```yaml title="Example of a restart of the Management API (restart-webappapi.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ControlPlaneOps
metadata:
  name: restart-webappapi
  namespace: simplyblock
spec:
  controlPlaneRef: simplyblock
  action: Restart
  restart:
    components:
      - simplyblock-webappapi
```

The Management API must be reachable from the edge sites over the private link, for example, through a LoadBalancer
Service with the selector of the `simplyblock-webappapi` Service. The Service gets an address on the private network,
or it is limited to that network with `spec.loadBalancerSourceRanges`:

```bash title="Expose the Management API to the edge sites"
kubectl -n simplyblock expose service simplyblock-webappapi \
    --name simplyblock-webappapi-edge --type LoadBalancer
```

## Installing the Operator at the Edge

At the edge site, the operator is installed in the managed profile as described in
[Connecting to an External Control Plane](install-csi.md). The endpoint is the `http://` address of the Management API
on the private link. An `https://` endpoint makes the operator serve the storage nodes of the edge over TLS, which the
hub cannot call. TLS is off at the edge as well: with `tls.enabled` on, the CSI driver rewrites the endpoint to
`https://` and trusts only the CA of the edge cluster. The token Secret holds one of the admin tokens of the hub. An
edge cluster also needs the default storage node image, because it has no local control plane that names it:

```bash title="Install the operator in the managed profile"
helm install simplyblock-operator simplyblock/simplyblock-operator \
    --namespace simplyblock \
    --set deployment.profile=managed \
    --set tls.enabled=false \
    --set tls.mutual_enabled=false \
    --set controlplane.managed.endpoint=http://<HUB-MANAGEMENT-API> \
    --set controlplane.managed.credentialsSecretRef=cp-token \
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

A one-node edge cluster sets `clusterMode` to `Single` in the deployment document. The cluster mode lets any
supported erasure-coding scheme run on the one storage node, with every chunk of a stripe on a different device. It
is copied to `spec.clusterMode` of the `StorageCluster` when the cluster is created. A cluster cannot be changed to
or from `Single` afterward.

For a one-worker fleet, the discovery proposes the cluster mode `Single` and the scheme that the data devices of the
worker carry: 2+1 with three or more devices, 1+1 with two, and 1+0 with one. A device dedicated to the journal does
not count as a data device. Other schemes are chosen by setting the stripe, as long as the worker hands over one data
device per chunk:

```bash title="One-node edge cluster with six data devices"
kubectl -n simplyblock patch clusterdeploymentconfig edge-draft --type merge -p '{
  "spec": {"cluster": {
    "name": "edge-site-a",
    "clusterMode": "Single",
    "stripe": {"dataChunks": 4, "parityChunks": 2}
  }}}'
```

The validation of the document refuses a `Single` document with more than one storage node, or with a group that
names fewer data devices than the scheme has chunks.

How many device failures the node survives depends on the scheme and on the journal placement, as described in
[Edge Clusters](../../architecture/deployment-topologies/edge-clusters.md#one-node-edge-clusters).

## Draft for a Two-Node Edge Cluster

!!! note
    Two-node edge clusters require two-node arbitration support in the control plane, the Simplyblock Operator, and
    the storage nodes.

A two-node edge cluster sets `clusterMode` to `Dual` in the deployment document. The cluster mode lets the
erasure-coding scheme 1+1 run on exactly two storage nodes, which otherwise needs three. It is copied to
`spec.clusterMode` of the `StorageCluster` when the cluster is created, together with `enableArbitration` and
`arbitration`. For a fleet of exactly two workers, the discovery proposes the cluster mode `Dual` with 1+1. Other
schemes still need their usual number of storage nodes:

```bash title="Two-node edge cluster"
kubectl -n simplyblock patch clusterdeploymentconfig edge-draft --type merge -p '{
  "spec": {"cluster": {
    "name": "edge-site-b",
    "stripe": {"dataChunks": 1, "parityChunks": 1},
    "clusterMode": "Dual",
    "enableArbitration": true,
    "arbitration": {
      "hostFencing": true
    }
  }}}'
```

| Field                     | Default    | Description                                                                                                  |
|---------------------------|------------|--------------------------------------------------------------------------------------------------------------|
| `clusterMode`             | `Standard` | `Single` for one storage node, `Dual` for two, `Standard` for three or more.                                 |
| `enableArbitration`       | Off        | Enables the arbitration of the hub between the two nodes.                                                    |
| `arbitration.hostFencing` | Off        | Lets Kubernetes restart the workloads of a fenced node on the other node. See [Host Fencing](#host-fencing). |

`enableArbitration` and `arbitration` are refused unless `clusterMode` is `Dual`.

The fields `arbitration.holdMs` and `arbitration.leaseTtlMs` are accepted, but they are not passed to the control
plane. Every two-node cluster runs with a hold time of 2500 ms, the time a node holds write I/O after losing its peer,
and with leases from the hub that stay valid for 1500 ms.

## Host Fencing

With host fencing, Kubernetes follows the fencing decision of the hub: when the hub fences a node, the workloads of
that node restart on the other node within seconds. The mechanism is described in
[Edge Clusters](../../architecture/deployment-topologies/edge-clusters.md#coordination-with-kubernetes).

### Prerequisites

- The NodeHealthCheck operator of the medik8s project. On OpenShift, it is the Node Health Check Operator from
  OperatorHub. It is the component that turns the `StorageFenced` condition into a remediation.
- All stateful workloads on the two nodes use simplyblock volumes. The out-of-service taint force-detaches every
  volume of a node, and only simplyblock volumes are fenced. A node with a volume of another CSI driver attached is
  not remediated unless the remediation template allows it.
- The CSI driver runs on both nodes. Its node plugin publishes the NVMe host NQN of the node as the annotation
  `storage.simplyblock.io/nvme-host-nqn`, which the hub needs to fence the host.

### Enabling Host Fencing

Host fencing is set in the deployment document as shown above, or on an existing cluster:

```bash title="Turn on host fencing for a two-node edge cluster"
kubectl -n simplyblock patch storagecluster edge-site-b --type merge \
    -p '{"spec": {"arbitration": {"hostFencing": true}}}'
```

The operator passes the setting to the hub and reports the NVMe host NQNs of both Kubernetes nodes. Each storage node
lists two of them, the kernel default (`nqn.2014-08.org.nvmexpress:uuid:...`) and the simplyblock form
(`nqn.2014-08.io.simplyblock:uuid:...`):

```bash title="Check the reported host NQNs"
kubectl -n simplyblock get storagenode \
    -o jsonpath='{range .items[*]}{.spec.workerNode}{"\t"}{.status.remediation.reportedHostNQNs}{"\n"}{end}'
```

### Configuring NodeHealthCheck

The remediation template names the simplyblock remediation, and the NodeHealthCheck triggers it on the
`StorageFenced` condition:

```yaml title="storage-fence-remediation.yaml"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageFenceRemediationTemplate
metadata:
  name: storage-fence
  namespace: simplyblock
spec:
  template:
    spec:
      # Refuse the out-of-service taint while a volume of another CSI driver is
      # attached to the node.
      allowForeignVolumes: false
---
apiVersion: remediation.medik8s.io/v1alpha1
kind: NodeHealthCheck
metadata:
  name: simplyblock-storage-fenced
spec:
  # The operator labels the Kubernetes nodes of a storage cluster with the
  # cluster's name, whether they are workers or control-plane nodes.
  selector:
    matchLabels:
      io.simplyblock.storagenodeset: edge-site-b
  # Required: with the default minHealthy of 51%, one of two nodes is never
  # remediated.
  maxUnhealthy: 1
  unhealthyConditions:
    - type: StorageFenced
      status: "True"
      duration: 2s
  remediationTemplate:
    apiVersion: storage.simplyblock.io/v1alpha2
    kind: StorageFenceRemediationTemplate
    namespace: simplyblock
    name: storage-fence
```

| Setting                          | Value                 | Why                                                                                        |
|----------------------------------|-----------------------|--------------------------------------------------------------------------------------------|
| `maxUnhealthy`                   | `1`                   | With two nodes, the default `minHealthy` of 51% blocks the remediation of either node.     |
| `unhealthyConditions[].duration` | `2s`                  | The condition is set only after the hub has fenced the host, so no grace period is needed. |
| `selector`                       | The two storage nodes | `io.simplyblock.storagenodeset` matches control-plane nodes as well, and no arbiter node.  |
| `allowForeignVolumes`            | `false`               | Keeps a node with volumes of another CSI driver from being force-detached unfenced.        |

The template is copied into each `StorageFenceRemediation` when it is created, so a change to the template only applies
to later remediations. The NodeHealthCheck operator creates and deletes `StorageFenceRemediation` resources with its own
service account. The Simplyblock Operator grants it access through a ClusterRole with the label
`rbac.ext-remediation/aggregate-to-ext-remediation: "true"`, which the chart installs.

### Host Connection Settings

Nothing has to be configured on the hosts. The control plane sets the NVMe keep-alive, fast I/O failure, and controller
loss timeouts for two-node edge clusters with arbitration, and the CSI driver applies them when it connects a volume.

## Approving and Verifying

The draft is approved and the cluster verified as described in
[Create a Storage Cluster](k8s-storage-plane.md#approve-the-deployment). The operator creates the storage cluster in
the control plane of the hub, then the storage nodes and the storage pool with its StorageClass.

The name of the storage cluster has to be unique on the hub, for example, the name of the site. The control plane
refuses a second cluster with the same name, and the operator of the second edge then adopts the existing cluster of
that name. Two edge sites then drive one cluster.
