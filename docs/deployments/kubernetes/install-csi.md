---
title: "Install Simplyblock CSI"
description: "Install Simplyblock CSI: Simplyblock provides a seamless integration with Kubernetes through its Kubernetes CSI driver."
weight: 30200
---

Simplyblock provides a seamless integration with Kubernetes through its Kubernetes CSI driver.

!!! note
    For Kubernetes-native deployments where both the storage cluster and CSI driver are managed on Kubernetes, use the
    [simplyblock operator](k8s-control-plane.md) instead. The operator installs and manages the CSI driver
    automatically via CRDs.

This section explains how to install the CSI driver **standalone** to connect to an **external** simplyblock storage
cluster. The external cluster must be installed onto
[Plain Linux Hosts](../install-on-linux/install-sp.md) or into an
[Existing Kubernetes Cluster](k8s-control-plane.md) and must not be co-located on the same Kubernetes worker nodes
as the CSI driver installation.

Before installing the Kubernetes CSI Driver, the external cluster must be present and a storage pool must have been
created.

## CSI Driver System Requirements

The CSI driver consists of two parts: 

- A controller part, which communicates to the control plane via the control plane API
- A node part, which is deployed to and must be present on all nodes with pods attaching simplyblock storage (Daemonset)

The worker node of the node part must satisfy the following requirements:

- [Linux Distributions and Versions](../../reference/supported-linux-distributions.md)
- [Linux Kernel Versions](../../reference/supported-linux-kernels.md)

## Installation Options

To install the Simplyblock CSI Driver, a Helm chart is provided. While it can be installed manually, the Helm chart is
strongly recommended. If a manual installation is preferred, see the
[CSI Driver Repository](https://github.com/simplyblock-io/simplyblock-csi/blob/master/docs/install-simplyblock-csi-driver.md){:target="_blank" rel="noopener"}.

## Retrieving Credentials

Credentials are available via `{{ cliname }} cluster get-secret` from any of the control plane nodes. For further
information on the command, see [the CLI reference](../../reference/cli/index.md).

First, the unique cluster id must be retrieved. Note down the cluster UUID of the cluster to access.

```bash title="Retrieving the Cluster UUID"
sudo {{ cliname }} cluster list
```

An example of the output is below.

```plain title="Example output of a cluster listing"
[demo@demo ~]# {{ cliname }} cluster list
+--------------------------------------+-----------------------------------------------------------------+---------+-------+------------+---------------+-----+--------+
| UUID                                 | NQN                                                             | ha_type | tls   | mgmt nodes | storage nodes | Mod | Status |
+--------------------------------------+-----------------------------------------------------------------+---------+-------+------------+---------------+-----+--------+
| 4502977c-ae2d-4046-a8c5-ccc7fa78eb9a | nqn.2023-02.io.simplyblock:4502977c-ae2d-4046-a8c5-ccc7fa78eb9a | ha      | False | 1          | 4             | 1x1 | active |
+--------------------------------------+-----------------------------------------------------------------+---------+-------+------------+---------------+-----+--------+
```

In addition, the cluster secret must be retrieved. Note down the cluster secret.

```bash title="Retrieve the Cluster Secret"
{{ cliname }} cluster get-secret <CLUSTER_UUID>
```

Retrieving the cluster secret will look somewhat like that.

```plain title="Example output of retrieving a cluster secret"
[demo@demo ~]# {{ cliname }} cluster get-secret 4502977c-ae2d-4046-a8c5-ccc7fa78eb9a
oal4PVNbZ80uhLMah2Bs
```

## Creating a Storage Pool

Additionally, a storage pool is required. If a pool already exists, it can be reused. Otherwise, creating a storage
pool can be created as follows:

```bash title="Create a Storage Pool"
{{ cliname }} pool add <POOL_NAME> <CLUSTER_UUID>
```

To enable NVMe-oF security for all volumes in the pool, provide a JSON configuration file with the `--sec-options` flag.
This configures which security keys (DH-HMAC-CHAP, TLS/PSK) are auto-generated for each allowed host. The cluster
must have been created with `--host-sec` for authentication to work.

```bash title="Create a Storage Pool with NVMe-oF Security"
{{ cliname }} pool add <POOL_NAME> <CLUSTER_UUID> --sec-options=sec-options.json
```

```json title="Example: sec-options.json"
{
  "dhchap_key": true,
  "dhchap_ctrlr_key": true,
  "psk": true
}
```

For more information, see [NVMe-oF Security](../../architecture/concepts/nvmf-security.md).

The last line of a successful storage pool creation returns the new pool id.

```plain title="Example output of creating a storage pool"
[demo@demo ~]# {{ cliname }} pool add test 4502977c-ae2d-4046-a8c5-ccc7fa78eb9a
2025-03-05 06:36:06,093: INFO: Adding pool
2025-03-05 06:36:06,098: INFO: {"cluster_id": "4502977c-ae2d-4046-a8c5-ccc7fa78eb9a", "event": "OBJ_CREATED", "object_name": "Pool", "message": "Pool created test", "caused_by": "cli"}
2025-03-05 06:36:06,100: INFO: Done
ad35b7bb-7703-4d38-884f-d8e56ffdafc6 # <- Pool Id
```

The last item necessary before deploying the CSI driver is the control plane address. It is recommended to front the
simplyblock API with an AWS load balancer, HAproxy, or similar service. Hence, your control plane address is the
"public" endpoint of this load balancer.

## Deploying the Helm Chart

Anyhow, deploying the Simplyblock CSI Driver using the provided Helm Chart comes down to providing the four necessary
values, adding the helm chart repository, and installing the driver.

```bash title="Install Simplyblock's CSI Driver"
CLUSTER_UUID="<UUID>"
CLUSTER_SECRET="<SECRET>"
CNTR_ADDR="<CONTROL-PLANE-ADDR>"
POOL_NAME="<POOL-NAME>"
helm repo add simplyblock https://install.simplyblock.io/helm
helm repo update
helm install -n simplyblock --create-namespace simplyblock simplyblock/spdk-csi \
    --set csiConfig.simplybk.uuid=${CLUSTER_UUID} \
    --set csiConfig.simplybk.ip=${CNTR_ADDR} \
    --set csiSecret.simplybk.secret=${CLUSTER_SECRET} \
    --set logicalVolume.pool_name=${POOL_NAME}
```

```plain title="Example output of the CSI driver deployment"
[demo@demo ~]# export CLUSTER_UUID="4502977c-ae2d-4046-a8c5-ccc7fa78eb9a"
[demo@demo ~]# export CLUSTER_SECRET="oal4PVNbZ80uhLMah2Bs"
[demo@demo ~]# export CNTR_ADDR="http://192.168.10.1/"
[demo@demo ~]# export POOL_NAME="test"
[demo@demo ~]# helm repo add simplyblock https://install.simplyblock.io/helm
"simplyblock" has been added to your repositories
[demo@demo ~]# helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "simplyblock" chart repository
Update Complete. ⎈Happy Helming!⎈
[demo@demo ~]# helm install -n simplyblock --create-namespace simplyblock simplyblock/spdk-csi \
  --set csiConfig.simplybk.uuid=${CLUSTER_UUID} \
  --set csiConfig.simplybk.ip=${CNTR_ADDR} \
  --set csiSecret.simplybk.secret=${CLUSTER_SECRET} \
  --set logicalVolume.pool_name=${POOL_NAME}
NAME: simplyblock
LAST DEPLOYED: Wed Mar  5 15:06:02 2025
NAMESPACE: simplyblock
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
The Simplyblock SPDK Driver is getting deployed to your cluster.

To check CSI SPDK Driver pods status, please run:

  kubectl --namespace=simplyblock get pods --selector="release=simplyblock" --watch
[demo@demo ~]# kubectl --namespace=simplyblock get pods --selector="release=simplyblock" --watch
NAME                   READY   STATUS    RESTARTS   AGE
spdkcsi-controller-0   6/6     Running   0          30s
spdkcsi-node-tzclt     2/2     Running   0          30s
```

There are a lot of additional parameters for the Helm Chart deployment. Most parameters, however, aren't required in
real-world CSI driver deployments and should only be used on request of simplyblock.

The full list of parameters is available here: [Kubernetes Helm Chart Parameters](../../reference/kubernetes/index.md).

Please note that the `storagenode.create` parameter must be set to `false` (the default) to deploy only the CSI driver.

## Multi Cluster Support

The Simplyblock CSI driver now offers **multi-cluster support** and **zone-aware configurations**, allowing to connect with multiple simplyblock clusters based on ClusterID 
or based on their topology zone.
Previously, the CSI driver could only connect to a single cluster.

To enable interaction with multiple clusters, there are two key changes:

1.  Parameter **`cluster_id` in a storage class:** A new parameter, `cluster_id`, has been added to the storage class. 
    This parameter specifies which simplyblock cluster a given request should be directed to.
2.  Secret **`simplyblock-csi-secret-v2`:** A new Kubernetes secret, `simplyblock-csi-secret-v2`, has been added to
    store credentials for all configured simplyblock clusters.

### Adding a Cluster

When the Simplyblock CSI driver is initially installed, only a single cluster can be referenced.

```bash title="Install the Simplyblock CSI driver via Helm"
helm install simplyblock-csi ./ \
    --set csiConfig.simplybk.uuid=${CLUSTER_ID} \
    --set csiConfig.simplybk.ip=${CLUSTER_IP} \
    --set csiSecret.simplybk.secret=${CLUSTER_SECRET} \
```

The `CLUSTER_ID` (UUID), gateway endpoint (`CLUSTER_IP`), and secret (`CLUSTER_SECRET`) of the initial cluster must be
provided. This command automatically creates the `simplyblock-csi-secret-v2` secret.

The structure of the `simplyblock-csi-secret-v2` secret is as following:

```yaml title="simplyblock-csi-secret-v2 Structure"
apiVersion: v1
data:
  secret.json: <base64 encoded secret>
kind: Secret
metadata:
  name: simplyblock-csi-secret-v2
type: Opaque
```

The decoded secret must be valid JSON content and contain an array of JSON items, one per cluster. Each items consists
of three properties, `cluster_id`, `cluster_endpoint`, and `cluster_secret`.

```json title="Example secret.json Payload"
{
   "clusters": [
     {
       "cluster_id": "4ec308a1-61cf-4ec6-bff9-aa837f7bc0ea",
       "cluster_endpoint": "http://127.0.0.1",
       "cluster_secret": "super_secret"
     }
   ]
}
```

To add a new cluster, the current secret must be retrieved from Kubernetes, edited (adding the new cluster information),
and uploaded to the Kubernetes cluster.  


```bash title="Update and Reapply Cluster Secret"
# Save cluster secret to a file
kubectl get secret simplyblock-csi-secret-v2 \
    -o jsonpath='{.data.secret\.json}' |\
    base64 --decode > secret.json

# Edit the clusters and add the new cluster's cluster_id,
# cluster_endpoint, cluster_secret vi secret.json 

cat secret.json | base64 | tr -d '\n' > secret-encoded.json

# Replace data.secret.json with the content of secret-encoded.json
kubectl -n simplyblock edit secret simplyblock-csi-secret-v2
```

### Using Multi Cluster

#### Option 1: Cluster ID–Based Method (One StorageClass per Cluster)

In this approach, each simplyblock cluster has its own dedicated StorageClass that specifies which cluster to use for provisioning.
This is ideal for setups where workloads are manually directed to specific clusters.

```yaml title="Example of Cluster ID-Based Selection"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: simplyblock-csi-sc-cluster1
provisioner: csi.simplyblock.io
parameters:
  cluster_id: "cluster-uuid-1"
  ... other parameters
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

You can define another StorageClass for a different cluster:

```yaml title="Example of selecting another cluster"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: simplyblock-csi-sc-cluster2
provisioner: csi.simplyblock.io
parameters:
  cluster_id: "cluster-uuid-2"
  ... other parameters
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

Each StorageClass references a unique cluster_id.
The CSI driver uses that ID to determine which simplyblock cluster to connect to.

#### Option 2: Zone-Aware Method (Automatic Multi-Cluster Selection)

This approach allows a single StorageClass to automatically select the appropriate simplyblock cluster based on the Kubernetes zone where the workload runs.
It is recommended for multi-zone Kubernetes deployments that span multiple simplyblock clusters.

`storageclass.zoneClusterMap`

Sets the mapping between Kubernetes zones and simplyblock cluster IDs.
Each zone is associated with one cluster.

`storageclass.allowedTopologyZones`

Sets the list of zones where the StorageClass is permitted to provision volumes.
This ensures that scheduling aligns with the clusters defined in `zoneClusterMap`.

```yaml title="Example of zoneClusterMap usage"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: simplyblock-csi-sc
provisioner: csi.simplyblock.io
parameters:
  zone_cluster_map: |
    {"us-east-1a":"cluster-uuid-1","us-east-1b":"cluster-uuid-2"}
  ... other parameters
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
allowedTopologies:
- matchLabelExpressions:
  - key: topology.kubernetes.io/zone
    values:
      - us-east-1a
      - us-east-1b
```

This method allows Kubernetes to automatically pick the right cluster based on the pod’s scheduling zone.

#### Option 3: Region-Aware Method (Automatic Multi-Cluster Selection)

This approach allows a single StorageClass to automatically select the appropriate simplyblock cluster based on the Kubernetes region where the workload runs.
It’s recommended when:

- your cluster spans multiple regions, and

- each region maps to a different simplyblock backend, or

- you want region-scoped placement rather than zone-scoped placement

`storageclass.regionClusterMap`

Sets the mapping between Kubernetes regions and simplyblock cluster IDs.
Each region is associated with one cluster.

`storageclass.allowedTopologyRegions`

Sets the list of regions where the StorageClass is permitted to provision volumes.
This ensures scheduling aligns with the clusters defined in `regionClusterMap`.

```yaml title="Example of regionClusterMap usage"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: simplyblock-csi-sc
provisioner: csi.simplyblock.io
parameters:
  region_cluster_map: |
    {"us-east-1":"cluster-uuid-a","us-west-2":"cluster-uuid-b"}
  ... other parameters
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
allowedTopologies:
- matchLabelExpressions:
  - key: topology.kubernetes.io/region
    values:
      - us-east-1
      - us-west-2
```

This method allows Kubernetes to automatically pick the right cluster based on the pod’s scheduling region.

!!! tip
    The keys inside `region_cluster_map` must match the region labels present on your Kubernetes nodes
    (typically `topology.kubernetes.io/region`). You can include as many regions as needed, each pointing to
    the cluster ID defined in `simplyblock-csi-secret-v2`.
