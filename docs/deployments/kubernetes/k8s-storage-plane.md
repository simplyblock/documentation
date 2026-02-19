---
title: "Install Simplyblock Storage Plane on Kubernetes"
weight: 30100
---

When installed on Kubernetes, simplyblock installations consist of three parts, the control plane, the storage nodes 
and the CSI driver.

!!! info
    In a Kubernetes deployment, not all Kubernetes workers have to become part of the storage cluster.
    Simplyblock uses node labels to identify Kubernetes workers that are deemed as storage hosting instances.

    It is common to add dedicated Kubernetes worker nodes for storage to the same
    Kubernetes cluster. They can be separated into a different node pool, and using a different type of host. In this case,
    it is important to remember to taint the Kubernetes worker accordingly to prevent other services from being
    scheduled on this worker.

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

!!! info
    It is possible to configure QoS limits on a storage pool level. This limit will collectively cap all volumes
    assigned to this pool without being limited individually. In fact, if pool-level QoS is active, it is not 
    allowed to set volume-level QoS in the storage class!

Example:

```bash title="Create a Storage Pool with QoS Limits"
{{ cliname }} pool add <POOL_NAME> <CLUSTER_UUID> --max-iops 10000 --max-rw-mb 500 --max-w-mb 100
```

## Labeling Nodes

Before the Helm Chart can be installed, it is required to label all Kubernetes worker nodes deemed as storage nodes.

It is also possible to label additional nodes at a later stage to add them to the storage cluster. However, expanding
a storage cluster always requires at least two new nodes to be added as part of the same expansion operation.

```bash title="Label the Kubernetes worker node"
kubectl label nodes <NODE_NAME> io.simplyblock.node-type=simplyblock-storage-plane
```

## Networking Configuration

Multiple ports are required to be opened on storage node hosts.

Ports using the same source and target networks (VLANs) will not require any additional firewall settings.

Opening ports may be required between the control plane and storage networks as those typically reside on different
VLANs.

{% include 'storage-plane-network-port-table-k8s.md' %}

## Installing CSI Driver and Storage Nodes via Helm

In the simplest deployment, compared to a pure [Simplyblock CSI Driver](install-csi.md) installation, the deployment of
a storage node via the Helm Chart requires only one additional parameter  `--set storagenode.create=true`:

```bash title="Install the helm chart"
CLUSTER_UUID="<UUID>"
CLUSTER_SECRET="<SECRET>"
CNTR_ADDR="<CONTROL-PLANE-ADDR>"
POOL_NAME="<POOL-NAME>"
helm repo add simplyblock-csi https://install.simplyblock.io/helm/csi
helm repo add simplyblock-controller https://install.simplyblock.io/helm/controller
helm repo update

# Install Simplyblock CSI Driver and Storage Node API
helm install -n simplyblock \
    --create-namespace simplyblock \
    simplyblock-csi/spdk-csi \
    --set csiConfig.simplybk.uuid=<CLUSTER_UUID> \
    --set csiConfig.simplybk.ip=<CNTR_ADDR> \
    --set csiSecret.simplybk.secret=<CLUSTER_SECRET> \
    --set logicalVolume.pool_name=<POOL_NAME> \
    --set storagenode.create=true
```

```plain title="Example output of the Simplyblock Kubernetes deployment"
demo@demo ~> export CLUSTER_UUID="4502977c-ae2d-4046-a8c5-ccc7fa78eb9a"
demo@demo ~> export CLUSTER_SECRET="oal4PVNbZ80uhLMah2Bs"
demo@demo ~> export CNTR_ADDR="http://192.168.10.1/"
demo@demo ~> export POOL_NAME="test"
demo@demo ~> helm repo add simplyblock-csi https://install.simplyblock.io/helm/csi
"simplyblock-csi" has been added to your repositories
demo@demo ~> helm repo add simplyblock-controller https://install.simplyblock.io/helm/controller
"simplyblock-controller" has been added to your repositories
demo@demo ~> helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "simplyblock-csi" chart repository
...Successfully got an update from the "simplyblock-controller" chart repository
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

There are a number of other Helm Chart parameters that are important for storage node deployment in hyper-converged
mode. The most important ones are:

| Parameter                     | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                | Default   | 
|-------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------|
| `storagenode.ifname`          | Sets the interface name of the management interface (traffic between storage nodes and control plane, see storage mgmt VLAN). Highly available ports and networks are required in production. While this value can be changed at a later point in time, it requires a storage node restart.                                                                                                                                                                | eth0      | 
| `storagenode.maxSize`         | Sets the maximum utilized storage capacity of this storage node. A conservative setting is the expected cluster capacity. This setting has significant impact on RAM demand with 0.02% of `maxSixe` is required in additional RAM.                                                                                                                                                                                                                         | 150g      | 
| `storagenode.isolateCores`    | Enabled core isolation of cores used by simplyblock from other processes and system, including IRQs, can significantly increase performance. Core isolation requires a Kubernetes worker node restart after the deployment is completed. Changes are performed via a privileged container on the OS-level (grub).                                                                                                                                          | false     | 
| `storagenode.dataNics`        | Sets the interface name of the storage network(s). This includes traffic inside the storage cluster and between csi-nodes and storage nodes. Highly available ports and networks are required for production.                                                                                                                                                                                                                                              |           |
| `storagenode.pciAllowed`      | Sets the list of allowed NVMe PCIe addresses.                                                                                                                                                                                                                                                                                                                                                                                                              | `<empty>` | 
| `storagenode.pciBlocked`      | Sets the list of blocked NVMe PCIe addresses.                                                                                                                                                                                                                                                                                                                                                                                                              | `<empty>` | 
| `storagenode.socketsToUse`    | Sets the list of NUMA sockets to use. If a worker node has more than 1 NUMA socket, it is possible to deploy more than one simplyblock storage node per host, depending on the distribution of NVMe devices and NICs across NUMA sockets and the resource demand of other workloads.                                                                                                                                                                       | 1         |
| `storagenode.nodesPerSocket`  | Sets the number of storage nodes to be deployed per NUMA socket. It is possible to deploy one or two storage nodes per socket. This improves performance if one each NUMA socket has more than 32 cores.| 1         |  
| `storagenode.coresPercentage` | Sets the percentage of total cores (vCPUs) available to simplyblock storage node services. It must be ensured that the configured percentage yields at least 8 vCPUs per storage node. For example, if a host has 128 vCPUs on two NUMA sockets (64 each) and `--storagenode.socketsToUse=2` and `--storagenode.nodesPerSocket=1`, at least 13% (as `13% * 64 > 8`) must be set. Simplyblock does not use more than 32 vCPUs per storage node efficiently. | `<empty>` | 
| `storagenode.deviceNames` | Comma separated list of nvme namespace names to be used by the storage node (for example `nvme0n1`, `nvme1n1`). Do **not** include the `/dev/` prefix. | `<empty>` |
| `storagenode.format4k`    | If set to `true`, the specified devices will be formatted with a 4K sector size. Recommended for modern NVMe drives when supported. | `false` |
| `storagenode.multiCluster.enable`                      | Enable multi-cluster storage node support. When enabled, a single Kubernetes cluster can host storage nodes connected to multiple Simplyblock clusters. | `false`   |
| `storagenode.multiCluster.clusters[].cluster_id`       | UUID of the Simplyblock cluster this storage node should connect to.                                          | `<empty>` |
| `storagenode.multiCluster.clusters[].secret`           | Secret used to authenticate against the specified Simplyblock cluster.                                       | `<empty>` |
| `storagenode.multiCluster.clusters[].workers`          | List of Kubernetes worker node names assigned to this Simplyblock cluster. Storage nodes will only be scheduled on these workers. | `<empty>` |


### Multi-Cluster Storage Node Support 

```yaml title="Multi-Cluster definition"
storagenode:
  multiCluster:
    enable: true
    clusters:
      - cluster_id: cluster-uuid-1
        secret: cluster-secret-id-1
        workers:
          - worker-a-1
          - worker-a-2
      - cluster_id: cluster-uuid-2
        secret: cluster-secret-id-2
        workers:
          - worker-b-1
          - worker-b-2
```

!!! warning
    The resources consumed by simplyblock are exclusively used and have to be aligned with resources required by other
    workloads. For further information, see [Minimum System Requirements](../deployment-preparation/system-requirements.md#minimum-system-requirements).

!!! info
    The RAM requirement itself is split in between huge page memory and system memory. However, this is transparent to
    users.

    Simplyblock takes care of allocating, reserving, and freeing huge pages as part of its overall RAM management.

    The total amount of RAM required depends on the number of vCPUs used, the number of active logical volumes
    (Persistent Volume Claims or PVCs) and the utilized virtual storage on this node. This doesn't mean the physical
    storage provided on the storage host, but the storage connected to via this storage node.
