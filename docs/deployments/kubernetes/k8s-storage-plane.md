---
title: "Deploy Storage Nodes and CSI"
description: "Deploy simplyblock storage nodes, storage pools, and the CSI driver on Kubernetes using the simplyblock operator CRDs."
weight: 30100
---

After [installing the simplyblock operator](k8s-control-plane.md) and creating a storage cluster, the next step is
to deploy storage nodes, create a storage pool, and enable volume provisioning via the CSI driver.

!!! info
    In a Kubernetes deployment, not all Kubernetes workers have to become part of the storage cluster.
    Simplyblock uses node labels to identify Kubernetes workers that are deemed as storage hosting instances.

    It is common to add dedicated Kubernetes worker nodes for storage to the same
    Kubernetes cluster. They can be separated into a different node pool, and using a different type of host. In this case,
    it is important to remember to taint the Kubernetes worker accordingly to prevent other services from being
    scheduled on this worker.

## OpenShift Prerequisites

If you are deploying onto an OpenShift cluster, ensure that the environment-specific instructions provided in the
[OpenShift Installation](openshift.md) guide are followed.

## Labeling Nodes

Before deploying storage nodes, label all Kubernetes worker nodes designated as storage nodes:

```bash title="Label the Kubernetes worker node"
kubectl label nodes <NODE_NAME> io.simplyblock.node-type=simplyblock-storage-plane
```

## Networking Configuration

Multiple ports are required to be opened on storage node hosts.

Ports using the same source and target networks (VLANs) will not require any additional firewall settings.

Opening ports may be required between the control plane and storage networks as those typically reside on different
VLANs.

{% include 'storage-plane-network-port-table-k8s.md' %}

## Deploying Storage Nodes

Apply a `SimplyBlockStorageNode` CRD to deploy storage nodes:

```yaml title="Example: storage-nodes.yaml"
apiVersion: simplyblock.simplyblock.io/v1alpha1
kind: SimplyBlockStorageNode
metadata:
  name: storage-nodes
  namespace: simplyblock
spec:
  clusterName: production
  clusterImage: "public.ecr.aws/simply-block/simplyblock:26.1.2"
  maxLogicalVolumeCount: 100
  workerNodes:
    - worker-1
    - worker-2
  maxSize: "500G"
  partitions: 1
  coreIsolation: true
```

```bash title="Apply the storage node resource"
kubectl apply -f storage-nodes.yaml
```

### Storage Node Parameters

| Parameter               | Description                                                            | Default |
|-------------------------|------------------------------------------------------------------------|---------|
| `clusterName`           | Name of the cluster this node belongs to. **Required**.                |         |
| `clusterImage`          | Storage-node image. **Required when `action` is not specified**.       |         |
| `maxLogicalVolumeCount` | Maximum number of logical volumes on this node. **Required when `action` is not specified**. | 10      |
| `maxSize`               | Maximum utilized storage capacity (e.g., `500G`). Impacts RAM demand.  | 150g    |
| `partitions`            | Number of partitions per device.                                       | 1       |
| `coreIsolation`         | Enable CPU core isolation. Requires a node restart after deployment.   | false   |
| `corePercentage`        | Percentage of total cores allocated to simplyblock.                    |         |
| `pcieAllowList`         | List of allowed NVMe PCIe addresses.                                   |         |
| `pcieDenyList`          | List of blocked NVMe PCIe addresses.                                   |         |
| `dataIfname`            | Data network interface names for storage traffic.                      |         |
| `socketsToUse`          | Number of NUMA sockets to use.                                         |         |
| `nodesPerSocket`        | Number of storage nodes per NUMA socket.                               |         |
| `workerNodes`           | Worker node names for deployment. **Required and must be non-empty when `action` is not specified**. |         |

For a complete list of fields, see [Simplyblock Operator](../../reference/operator.md).

## Creating a Storage Pool

Apply a `SimplyBlockPool` CRD to create a storage pool:

```yaml title="Example: storage-pool.yaml"
apiVersion: simplyblock.simplyblock.io/v1alpha1
kind: SimplyBlockPool
metadata:
  name: my-pool
  namespace: simplyblock
spec:
  name: production-pool
  clusterName: production
  capacityLimit: "10T"
```

```bash title="Apply the storage pool resource"
kubectl apply -f storage-pool.yaml
```

## Verification

Check the status of all simplyblock resources:

```bash title="Verify deployment status"
kubectl get simplyblockstoragecluster -n simplyblock
kubectl get simplyblockstoragenode -n simplyblock
kubectl get simplyblockpool -n simplyblock
kubectl get pods -n simplyblock
```

## Multi-Cluster Storage Node Support

A single Kubernetes cluster can host storage nodes connected to multiple simplyblock clusters. To configure this,
specify the `workerNodes` field in the `SimplyBlockStorageNode` CRD:

```yaml title="Multi-cluster storage nodes"
apiVersion: simplyblock.simplyblock.io/v1alpha1
kind: SimplyBlockStorageNode
metadata:
  name: cluster-a-nodes
  namespace: simplyblock
spec:
  clusterName: cluster-a
  workerNodes:
    - worker-a-1
    - worker-a-2
---
apiVersion: simplyblock.simplyblock.io/v1alpha1
kind: SimplyBlockStorageNode
metadata:
  name: cluster-b-nodes
  namespace: simplyblock
spec:
  clusterName: cluster-b
  workerNodes:
    - worker-b-1
    - worker-b-2
```

!!! warning
    The resources consumed by simplyblock are exclusively used and have to be aligned with resources required by other
    workloads. For further information, see [Minimum System Requirements](../deployment-preparation/system-requirements.md#minimum-system-requirements).

!!! info
    The RAM requirement is split between huge page memory and system memory. Simplyblock manages huge page
    allocation automatically.

    The total amount of RAM required depends on the number of vCPUs used, the number of active logical volumes
    (Persistent Volume Claims or PVCs) and the utilized virtual storage on this node.
