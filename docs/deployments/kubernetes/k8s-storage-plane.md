---
title: "Create a Storage Cluster"
description: "Deploy simplyblock storage nodes, storage pools, and the CSI driver on Kubernetes using the simplyblock operator CRDs."
weight: 30100
---

With the [Simplyblock Operator](k8s-control-plane.md) being installed, it's time to bring up a storage cluster.

This includes creating the cluster resource, adding storage nodes, creating a storage pool, and provisioning the first
simplyblock logical volume.

Before going on, here is a high-level overview of the following deployment process:

```plain title="Storage Cluster Lifecycle"
StorageCluster   ──► unready
                       │
                       ▼  (add ≥ 3 storage nodes)
StorageNode(s)   ──► active
                       │
                       ▼  (create a pool)
Pool             ──► StorageClass created automatically
                       │
                       ▼  (create a PVC)
PersitentVolume  ──► Bound
```

!!! info
    Not all Kubernetes workers have to become part of the simplyblock storage cluster. It is possible and common to
    only use a subset of all Kubernetes worker nodes for storage.
    
    It is also possible to use a separate Kubernetes worker node pool dedicated to storage. In this case, it is
    important to remember to taint the nodes accordingly to prevent other workloads from being scheduled on them.

## Prerequisites

### OpenShift

If deploying onto an OpenShift cluster, there are additional environment-specific steps in the
[OpenShift Installation](openshift.md) guide before continuing here.

### Talos

If deploying onto a Talos cluster, there are additional environment-specific steps in the
[Talos Installation](talos.md) guide before continuing here.

### Networking

Multiple ports must be open on storage node hosts.

It is required to use one or more separate VLANs for simplyblock. Ports within the same VLAN do not require extra
firewall rules, but ports between the control plane and storage networks typically do.

{% include 'storage-plane-network-port-table-k8s.md' %}

---

## Create the Storage Cluster

The first step is to create a `StorageCluster` resource. This registers the cluster with the operator and prepares the
control plane. This step does not yet acquire storage devices.

```yaml title="storage-cluster.yaml"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageCluster
metadata:
  name: simplyblock-cluster
  namespace: simplyblock
spec:
  clusterName: production
  mgmtIfname: eth0
  fabricType: tcp
  haType: ha
  stripe:
    dataChunks: 2
    parityChunks: 1
```

```bash title="Create the cluster"
kubectl apply -f storage-cluster.yaml
```

Next, the cluster status can be checked:

```bash title="Check the cluster status"
kubectl get storagecluster -n simplyblock
```

The output should look similar to this:

```plain title="Example output of cluster status"
NAME                   STATUS    UUID                                   CONFIGURED   AGE
simplyblock-cluster    unready   81932010-8c06-4acd-b14a-51f5c3fca425   true         1m
```

The cluster is set up, but not yet ready to use. Hence, **`unready` is expected** at this point. While the cluster has
been registered, it has no storage nodes yet. Those are added in the next step.

!!! note
    There are additional configuration properties when creating a storage cluster. The documentation, such
    as NVMe-oF transport security, backup configuration, capacity thresholds, and more, are available at
    [Cluster Deployment Options](../cluster-deployment-options.md).

## Add Storage Nodes

Now, Kubernetes worker nodes will be transformed into simplyblock storage nodes. To initiate the process, a
`StorageNode` resource must be created. The resource lists all Kubernetes worker nodes that are supposed to become
part of the storage cluster.

```yaml title="storage-nodes.yaml"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNode
metadata:
  name: storage-nodes
  namespace: simplyblock
spec:
  clusterName: production
  clusterImage: "quay.io/simplyblock-io/simplyblock:26.2.1-PRE"
  maxLogicalVolumeCount: 100
  partitions: 1
  coreIsolation: false
  enableCpuTopology: true
  workerNodes:
    - worker-1
    - worker-2
    - worker-3
```

```bash title="Add storage nodes"
kubectl apply -f storage-nodes.yaml
```

As part of the provisioning process, the operator bootstraps each listed worker, installs the SPDK service, and
registers it with the previously created storage cluster.

The process takes a little while the spdk pods are being created. It can be checked with:

```bash title="Check the bring up process"
kubectl get pods -n simplyblock -w
```

### When does the Cluster become Active?

By default, simplyblock clusters use the [Erasure Coding](../deployment-preparation/erasure-coding-scheme.md) schema
of `1+1` which requires at least three storage nodes to join the cluster.

That means the operator will automatically activate the cluster when at least three storage nodes have joined. For
other erasure coding schemes, the number of required storage nodes will be different. See the erasure coding scheme
documentation for more details.

The cluster status can be checked with:

```bash title="Check the cluster status"
kubectl get storagecluster -n simplyblock
```

```plain title="Example output of cluster status"
NAME                   STATUS   UUID                                   CONFIGURED   AGE
simplyblock-cluster    active   bfa260ce-06a7-4bcb-a843-813d0be633af   true         10m
```

When the status becomes `active`, the operator automatically creates a `simplyblock-csi-secret-v2` secret in the
`simplyblock` namespace, containing the cluster credentials for the CSI driver.

There is no necessity to manage this secret manually. The operator keeps it up to date and removes the cluster entry
when the cluster is deleted.

There are additional configuration properties. A full list is available at [Simplyblock Operator: Storage Node](../../reference/operator.md#storage-node).

!!! warning
    Simplyblock exclusively owns the resources it has been allocated. It must be ensured they are sized correctly
    alongside other workloads.

    Additionally, simplyblock manages huge page allocation automatically. Total RAM required depends on vCPU count, the
    number of active logical volumes, and utilized virtual storage per node.

    More information can be found in [Minimum Hardware Requirements](../deployment-preparation/hardware-requirements.md#minimum-system-requirements).

## Create a Storage Pool

A storage pool is a grouping of logical volumes and capacity limits within the cluster. An initial `Pool` resource must
be created to define a storage pool before being able to provision volumes. 

```yaml title="storage-pool.yaml"
apiVersion: storage.simplyblock.io/v1alpha1
kind: Pool
metadata:
  name: my-pool
  namespace: simplyblock
spec:
  name: production-pool
  clusterName: production
  capacityLimit: "10T"
```

```bash title="Create the pool"
kubectl apply -f storage-pool.yaml
```

The status of the storage pool can be checked with:

```bash title="Check the pool status"
kubectl get simplyblockpool -n simplyblock
```

Once the pool is active, the operator automatically creates a StorageClass named
`simplyblock-<clusterName>-<poolName>`. In this example, the StorageClass is called
`simplyblock-production-production-pool`.

The StorageClass is automatically removed when the storage pool is deleted. For full details and customization options
are available at [Simplyblock Operator: Storage Pool](../../reference/operator.md#storage-pool).

```bash title="Check the StorageClass"
kubectl get storageclass simplyblock-production-production-pool
```

## Provision Your First Volume

Now, everything is in place to create the first volume. The operator has automatically deployed the Simplyblock CSI
Driver into the Kubernetes cluster. Hence, creating a volume is as simple as creating PersistentVolumeClaim with the
correct StorageClass set.

### Create the PVC

```yaml title="test-pvc.yaml"
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: simplyblock-test-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: simplyblock-production-production-pool
```

```bash title="Create the PVC"
kubectl apply -f test-pvc.yaml
kubectl get pvc simplyblock-test-pvc
```

```plain title="Example output of PVC status"
NAME                    STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS                             AGE
simplyblock-test-pvc    Pending                                       simplyblock-production-production-pool   5s
```

Since provisioning is asynchronous, the PVC status will initially be `Pending`. The StorageClass uses
`WaitForFirstConsumer` by default, which means the volume is not provisioned until a pod actually needs it. The
scheduler picks the right node first, then the volume is created close to where it will be used.

### Mount the Volume into a Test Pod

To mount the volume, it can be used like any other Kubernetes persistent volume claim by referencing it in the pod's
volumes specification.

```yaml title="test-pod.yaml"
apiVersion: v1
kind: Pod
metadata:
  name: simplyblock-test-pod
spec:
  containers:
    - name: test
      image: busybox
      command: ["/bin/sh", "-c", "echo 'volume provisioned successfully' > /data/test.txt && sleep 3600"]
      volumeMounts:
        - mountPath: /data
          name: storage
  volumes:
    - name: storage
      persistentVolumeClaim:
        claimName: simplyblock-test-pvc
```

```bash title="Create the pod"
kubectl apply -f test-pod.yaml
```

When the pod reaches `Running` status, the PVC changes to bound.

```bash title="Check the PVC status"
kubectl get pvc simplyblock-test-pvc
```

```plain title="Example output of PVC status"
NAME                    STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS                             AGE
simplyblock-test-pvc    Bound    pvc-3f2a1c9e-84b1-4d2e-9f3a-1234abcd5678   10Gi       RWO            simplyblock-production-production-pool   30s
```

It is now possible to access the data written to the volume when the pod started up.

```bash title="Check the volume contents"
kubectl exec simplyblock-test-pod -- cat /data/test.txt
```

```plain title="Example output of volume contents"
volume provisioned successfully
```

The cluster is now fully operational and the test resources should be cleaned up with:

```bash title="Cleanup the test resources"
kubectl delete pod simplyblock-test-pod
kubectl delete pvc simplyblock-test-pvc
```

## Multi-Cluster Storage Node Support

A single Kubernetes cluster can host storage nodes connected to multiple simplyblock clusters.

To create an additional storage cluster, a separate `StorageNode` resource must be created for each simplyblock cluster.

Multiple storage clusters can share Kubernetes worker nodes, but it is recommended to point each storage cluster to a
different set of worker nodes.

```yaml title="Multi-cluster storage nodes"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNode
metadata:
  name: cluster-a-nodes
  namespace: simplyblock
spec:
  clusterName: cluster-a
  workerNodes:
    - worker-a-1
    - worker-a-2
---
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNode
metadata:
  name: cluster-b-nodes
  namespace: simplyblock
spec:
  clusterName: cluster-b
  workerNodes:
    - worker-b-1
    - worker-b-2
```
