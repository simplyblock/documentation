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
StorageCluster    ──► unready
                        │
                        ▼  (enroll ≥ 3 workers in a StorageNodeSet)
StorageNodeSet    ──► operator creates StorageNode CRs and provisions each worker
StorageNode(s)    ──► active (once ≥ 3 nodes are online)
                        │
                        ▼  (create a pool)
Pool              ──► StorageClass created automatically
                        │
                        ▼  (create a PVC)
PersistentVolume  ──► Bound
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

{% include 'network-port-table.md' %}

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
    [Cluster Deployment Options](../../deployment-preparation/cluster-deployment-options.md).

!!! tip "External KMS"
    If volumes in this cluster should offload their encryption keys to an external KMS, set
    `spec.hashicorpVaultSettings.base_url` on the `StorageCluster` now. The setting can also be added later, but
    configuring it upfront means encrypted volumes use the external KMS from day one. See
    [Securing the Control Plane: External KMS](security.md#external-key-management-kms).

## Add Storage Nodes

To enroll Kubernetes workers as simplyblock storage nodes, create a `StorageNodeSet` resource. It declares which
workers to use and how to configure them. The operator creates one `StorageNode` CR per worker (and per NUMA socket
if multiple sockets are configured), then provisions each one sequentially.

```yaml title="storage-nodeset.yaml"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeSet
metadata:
  name: simplyblock-node
  namespace: simplyblock
spec:
  clusterName: simplyblock-cluster
  maxLogicalVolumeCount: 20
  partitions: 0
  corePercentage: 50
  workerNodes:
    - worker-1.example.com
    - worker-2.example.com
    - worker-3.example.com
```

```bash title="Enroll storage nodes"
kubectl apply -f storage-nodeset.yaml
```

As part of the provisioning process, the operator bootstraps each listed worker, installs the SPDK service, and
registers it with the previously created storage cluster. Workers are added one at a time by default
(`maxParallelNodeAdds: 1`) to protect FoundationDB from simultaneous reboots.

The process takes a little while as SPDK pods are created. Track progress with:

```bash title="Check the bring-up process"
kubectl get storagenodeset simplyblock-node -n simplyblock
kubectl get storagenodes -n simplyblock
```

### When does the Cluster become Active?

By default, simplyblock clusters use the [Erasure Coding](../../deployment-preparation/erasure-coding-scheme.md) schema
of `1+1` which requires at least three storage nodes to join the cluster.

The operator automatically activates the cluster when at least three storage nodes are online. For other erasure
coding schemes, the required number differs (see the erasure coding documentation for details).

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

For a full list of configuration options see [Simplyblock Operator: StorageNodeSet](../../reference/operator/reference.md#storagenodeset).

!!! warning
    Simplyblock exclusively owns the resources it has been allocated. It must be ensured they are sized correctly
    alongside other workloads.

    Additionally, simplyblock manages huge page allocation automatically. Total RAM required depends on vCPU count, the
    number of active logical volumes, and utilized virtual storage per node.

    More information can be found in [Minimum Hardware Requirements](../../deployment-preparation/hardware-requirements.md#minimum-system-requirements).

## Create a Storage Pool

A storage pool is a grouping of logical volumes and capacity limits within the cluster. An initial `Pool` resource must
be created to define a storage pool before being able to provision volumes.

```yaml title="storage-pool.yaml"
apiVersion: storage.simplyblock.io/v1alpha1
kind: Pool
metadata:
  name: production-pool
  namespace: simplyblock
spec:
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
`simplyblock-<namespace>-<clusterName>-<poolName>`. In this example, the StorageClass is called
`simplyblock-simplyblock-cluster-production-pool`.

The StorageClass is automatically removed when the storage pool is deleted. For full details and customization options
are available at [Simplyblock Operator: Storage Pool](../../reference/operator/reference.md#pool).

```bash title="Check the StorageClass"
kubectl get storageclass simplyblock-simplyblock-production-my-pool
```

## Provision the First Volume

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
  storageClassName: simplyblock-simplyblock-production-my-pool
```

```bash title="Create the PVC"
kubectl apply -f test-pvc.yaml
kubectl get pvc simplyblock-test-pvc
```

```plain title="Example output of PVC status"
NAME                    STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS                             AGE
simplyblock-test-pvc    Pending                                       simplyblock-simplyblock-production-my-pool   5s
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
simplyblock-test-pvc    Bound    pvc-3f2a1c9e-84b1-4d2e-9f3a-1234abcd5678   10Gi       RWO            simplyblock-simplyblock-production-my-pool   30s
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

Create a separate `StorageNodeSet` for each simplyblock cluster. Multiple storage clusters can share Kubernetes
worker nodes, but it is recommended to point each storage cluster to a different set of workers.

```yaml title="Multi-cluster storage nodes"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeSet
metadata:
  name: cluster-a-nodes
  namespace: simplyblock
spec:
  clusterName: cluster-a
  workerNodes:
    - worker-a-1.example.com
    - worker-a-2.example.com
---
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeSet
metadata:
  name: cluster-b-nodes
  namespace: simplyblock
spec:
  clusterName: cluster-b
  workerNodes:
    - worker-b-1.example.com
    - worker-b-2.example.com
```
