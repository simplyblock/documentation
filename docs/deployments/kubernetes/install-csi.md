---
title: "Install Simplyblock CSI"
weight: 30200
---

Simplyblock provides a seamless integration with Kubernetes through its Kubernetes CSI driver. 

Before installing the Kubernetes CSI Driver, a control plane must be present, a (empty) storage cluster must have
been added to the control plane, and a storage pool must have been created.

This section explains how to install a CSI driver and connect it to a disaggregated storage cluster, which must already
exist prior to the CSI driver installation. The disaggregated cluster must be installed onto
[Plain Linux Hosts](../install-on-linux/install-sp.md) or into an [Existing Kubernetes Cluster](k8s-control-plane.md).
It must not be co-located on the same Kubernetes worker nodes as the CSI driver installation. 

For co-located (hyper-converged) deployment (which includes the CSI driver and storage node deployment), see
[Hyper-Converged Deployment](k8s-storage-plane.md).

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
information on the command, see [Retrieving a Cluster Secret](../../reference/cli/cluster.md#gets-a-clusters-secret).

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
helm repo add simplyblock-csi https://install.simplyblock.io/helm/csi
helm repo update
helm install -n simplyblock --create-namespace simplyblock simplyblock-csi/spdk-csi \
    --set csiConfig.simplybk.uuid=${CLUSTER_UUID} \
    --set csiConfig.simplybk.ip=${CNTR_ADDR} \
    --set csiSecret.simplybk.secret=${CLUSTER_SECRET} \
    --set logicalVolume.pool_name=${POOL_NAME}
```

```plain title="Example output of the CSI driver deployment"
demo@demo ~> export CLUSTER_UUID="4502977c-ae2d-4046-a8c5-ccc7fa78eb9a"
demo@demo ~> export CLUSTER_SECRET="oal4PVNbZ80uhLMah2Bs"
demo@demo ~> export CNTR_ADDR="http://192.168.10.1/"
demo@demo ~> export POOL_NAME="test"
demo@demo ~> helm repo add simplyblock-csi https://install.simplyblock.io/helm/csi
"simplyblock-csi" has been added to your repositories
demo@demo ~> helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "simplyblock-csi" chart repository
Update Complete. ⎈Happy Helming!⎈
demo@demo ~> helm install -n simplyblock --create-namespace simplyblock simplyblock-csi/spdk-csi \
  --set csiConfig.simplybk.uuid=${CLUSTER_UUID} \
  --set csiConfig.simplybk.ip=${CNTR_ADDR} \
  --set csiSecret.simplybk.secret=${CLUSTER_SECRET} \
  --set logicalVolume.pool_name=${POOL_NAME}
NAME: simplyblock-csi
LAST DEPLOYED: Wed Mar  5 15:06:02 2025
NAMESPACE: simplyblock
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
The Simplyblock SPDK Driver is getting deployed to your cluster.

To check CSI SPDK Driver pods status, please run:

  kubectl --namespace=simplyblock get pods --selector="release=simplyblock-csi" --watch
demo@demo ~> kubectl --namespace=simplyblock get pods --selector="release=simplyblock-csi" --watch
NAME                   READY   STATUS    RESTARTS   AGE
spdkcsi-controller-0   6/6     Running   0          30s
spdkcsi-node-tzclt     2/2     Running   0          30s
```

There are a lot of additional parameters for the Helm Chart deployment. Most parameters, however, aren't required in
real-world CSI driver deployments and should only be used on request of simplyblock.

The full list of parameters is available here: [Kubernetes Helm Chart Parameters](../../reference/kubernetes/index.md).

Please note that the `storagenode.create? parameter must be set to `false` (the default) to deploy only the CSI driver.

## Multi Cluster Support

The Simplyblock CSI driver now offers **multi-cluster support**, allowing to connect with multiple simplyblock clusters.
Previously, the CSI driver could only connect to a single cluster.

To enable interaction with multiple clusters, there are two key changes:

1.  Parameter **`cluster_id` in a storage class:** A new parameter, `cluster_id`, has been added to the storage class. 
    This parameter specifies which Simplyblock cluster a given request should be directed to.
2.  Secret **`simplyblock-csi-secret-v2`:** A new Kubernetes secret, `simplyblock-csi-secret-v2`, has been added to
    store credentials for all configured simplyblock clusters.

### Adding a Cluster

When the Simplyblock CSI driver is initially installed, only a single cluster can be referenced.

```
helm install simplyblock-csi ./ \
    --set csiConfig.simplybk.uuid=${CLUSTER_ID} \
    --set csiConfig.simplybk.ip=${CLUSTER_IP} \
    --set csiSecret.simplybk.secret=${CLUSTER_SECRET} \
```

The `CLUSTER_ID` (UUID), gateway endpoint (`CLUSTER_IP`), and secret (`CLUSTER_SECRET`) of the initial cluster must be
provided. This command automatically creates the `simplyblock-csi-secret-v2` secret.

The structure of the `simplyblock-csi-secret-v2` secret is as following:

```yaml
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

```json
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


```sh
# Save cluster secret to a file
kubectl get secret simplyblock-csi-secret-v2 -o jsonpath='{.data.secret\.json}' | base64 --decode > secret.yaml

# Edit the clusters and add the new cluster's cluster_id, cluster_endpoint, cluster_secret
# vi secret.json 

cat secret.json | base64 | tr -d '\n' > secret-encoded.json

# Replace data.secret.json with the content of secret-encoded.json
kubectl -n simplyblock edit secret simplyblock-csi-secret-v2
```

### Using Multi Cluster

With multi-cluster support enabled, a separate storage class per simplyblock cluster is required which defines the
individual cluster references. This provides clear segregation and management.

For example:

- `simplyblock-csi-sc-cluster1` (for `cluster_id: 4ec308a1-...`)
- `simplyblock-csi-sc-cluster2` (for `cluster_id: YOUR_NEW_CLUSTER_ID`)

### Topology-Aware Cluster Selection

For deployments spanning multiple availability zones, the CSI driver supports automatic cluster selection based on
Kubernetes node topology. Instead of specifying a fixed `cluster_id` per storage class, you can map zones or regions
to clusters:

- **`zone_cluster_map`:** Maps Kubernetes zones (`topology.kubernetes.io/zone`) to simplyblock cluster UUIDs.
- **`region_cluster_map`:** Maps Kubernetes regions (`topology.kubernetes.io/region`) to cluster UUIDs for coarser
  placement policies.

When combined with `volumeBindingMode: WaitForFirstConsumer`, the CSI driver delays volume creation until a pod is
scheduled, then selects the cluster that matches the pod's node topology. This enables a single StorageClass to work
transparently across multiple backend clusters.

## Kubernetes Operator Features

The Simplyblock CSI driver includes several operator-level features for managing storage infrastructure directly from
Kubernetes.

### Storage Node Management

Storage nodes can be deployed and managed as Kubernetes DaemonSets using the Helm chart. This enables fully
Kubernetes-native storage node lifecycle management:

- Set `storagenode.create=true` in the Helm values to deploy storage nodes as DaemonSets on labeled worker nodes.
- Nodes are labeled with `io.simplyblock.node-type=simplyblock-storage-plane` to target storage node scheduling.
- The **Storage Node Controller** (a Kubernetes Deployment) orchestrates node initialization, configuration, and
  health monitoring.
- Configuration options include huge page memory allocation, network interface selection, PCI device filtering, and
  CPU core isolation.

### NUMA Topology Support

For performance-sensitive deployments, the CSI driver includes an optional NUMA Resource Plugin:

- Deployed as a DaemonSet on storage nodes when `enableCpuTopology=true` is set.
- Exposes NUMA node capacity as a Kubernetes device resource for topology-aware scheduling.
- Ensures storage workloads are placed on the correct NUMA domain for optimal memory and PCIe locality.

### Guardian (Automatic Volume Recovery)

The Guardian is a daemon embedded in the CSI node component that automatically detects and recovers from broken NVMe
volume connections:

- Monitors NVMe-oF path health for all attached volumes.
- When both primary and secondary paths are lost, marks the volume as broken.
- After the cluster recovers (transitions to active or degraded state), automatically restarts affected pods to
  re-establish volume connections.
- Pods must opt in to automatic restart via the label `simplyblock.io/auto-restart-on-pathloss=true` on the pod or
  in the StorageClass.
- Includes configurable backoff periods to prevent restart storms during extended outages.

### Backup and Recovery CRDs

The CSI driver provides Custom Resource Definitions for managing backups from Kubernetes:

- **`Backup`:** Creates a backup of a PVC's snapshot to S3. Supports specifying the S3 target, retention, and
  snapshot selection.
- **`BackupSchedule`:** Defines recurring backup schedules for automated data protection.
- Restores can create new PVCs from backups or replace existing bound PVCs in place.
- Cross-cluster restore is supported by providing an imported backup metadata file.

### Replication CRDs

Replication between simplyblock clusters is managed through Kubernetes CRDs:

- **`Replication`:** Configures asynchronous replication between two clusters. Supports pool-level or PVC-level scope,
  configurable frequency (minimum 60 seconds), and status monitoring (running, stopped, delayed, failed).
- **`SyncReplication`:** Configures synchronous (real-time) replication for zero-RPO requirements.
- **Failover/Failback:** Both CRDs support `fail-over` and `fail-back` actions for controlled site switching. Failback
  uses iterative delta synchronization to minimize the final cutover window.

For operational details, see [Replication Operations](../../maintenance-operations/replication.md) and
[Backup and Recovery Operations](../../maintenance-operations/backup-recovery.md).
