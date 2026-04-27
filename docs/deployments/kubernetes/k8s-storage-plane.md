---
title: "Deploy Storage Nodes"
description: "Deploy simplyblock storage nodes, storage pools, and the CSI driver on Kubernetes using the simplyblock operator CRDs."
weight: 30100
---

With the [simplyblock operator installed](k8s-control-plane.md), you are ready to bring up a storage cluster.
This guide walks through the full journey: creating the cluster, adding storage nodes, creating a pool, and
provisioning your first volume — with exactly what to expect at each step along the way.

Here is the overall picture of what you will build:

```
StorageCluster  ──► unready
                       │
                       ▼  (add ≥ 3 storage nodes)
StorageNode(s)  ──► active
                       │
                       ▼  (create a pool)
Pool            ──► StorageClass created automatically
                       │
                       ▼  (create a PVC)
PVC             ──► Bound  ✓
```

!!! info
    Not all Kubernetes workers need to join the storage cluster. Simplyblock uses node labels to identify which
    workers host storage. It is common to dedicate a separate node pool for storage — if you do, remember to taint
    those nodes so other workloads are not scheduled on them.

## Prerequisites

### OpenShift

If you are deploying onto OpenShift, follow the environment-specific steps in the
[OpenShift Installation](openshift.md) guide before continuing here.

### Networking

Multiple ports must be open on storage node hosts. Ports within the same VLAN do not require extra firewall
rules, but ports between the control plane and storage networks typically do.

{% include 'storage-plane-network-port-table-k8s.md' %}

---

## Step 1 — Create the Storage Cluster

Start by creating a `StorageCluster` resource. This registers the cluster with the operator and prepares the
control plane — it does not yet require any storage capacity.

```yaml title="storage-cluster.yaml"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageCluster
metadata:
  name: simplyblock-cluster
  namespace: simplyblock
spec:
  clusterName: production
  mgmtIfname: eth0
  haType: ha
  stripe:
    dataChunks: 2
    parityChunks: 1
  fabric: tcp
```

```bash
kubectl apply -f storage-cluster.yaml
```

Check the status right after applying:

```bash
kubectl get storagecluster -n simplyblock
```

You will see something like this:

```
NAME                   STATUS    UUID                                   CONFIGURED   AGE
simplyblock-cluster    unready   81932010-8c06-4acd-b14a-51f5c3fca425   true         1m
```

**`unready` is expected** at this point — the cluster has been registered, but it has no storage nodes yet.
Move on to the next step.

!!! tip
    For additional cluster options — NVMe-oF transport security, backup configuration, capacity thresholds, and
    more — see [Cluster Deployment Options](../cluster-deployment-options.md).

---

## Step 2 — Add Storage Nodes

Now point storage nodes at the cluster. Create a `StorageNode` resource that lists the Kubernetes worker nodes
you want to dedicate to storage:

```yaml title="storage-nodes.yaml"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNode
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
    - worker-3
  maxSize: "500G"
  partitions: 1
  coreIsolation: true
```

```bash
kubectl apply -f storage-nodes.yaml
```

The operator bootstraps each listed worker, installing the SPDK service and registering it with the cluster.
You can watch the spdk pods being created:

```bash
kubectl get pods -n simplyblock
```

### When does the cluster become active?

Once at least three storage nodes have joined successfully, the operator automatically activates the cluster.
Check the cluster status again:

```bash
kubectl get storagecluster -n simplyblock
```

```
NAME                   STATUS   UUID                                   CONFIGURED   AGE
simplyblock-cluster    active   bfa260ce-06a7-4bcb-a843-813d0be633af   true         10m
```

When the status flips to `active`, the operator also creates the `simplyblock-csi-secret-v2` Secret in the
`simplyblock` namespace, containing the cluster credentials the CSI driver needs. You do not need to manage
this Secret manually — the operator keeps it up to date and removes the cluster entry when the cluster is
deleted.

For all available fields, see [Simplyblock Operator — Storage Node](../../reference/operator.md#storage-node).

!!! warning
    Simplyblock exclusively owns the resources it is allocated. Make sure they are sized correctly alongside
    other workloads. See [minimum hardware requirements](../deployment-preparation/hardware-requirements.md#minimum-system-requirements).

!!! info
    Simplyblock manages huge page allocation automatically. Total RAM required depends on vCPU count, the number
    of active logical volumes, and utilized virtual storage per node.

---

## Step 3 — Create a Storage Pool

A storage pool is a logical grouping of capacity within the cluster. Create one with a `Pool` resource:

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

```bash
kubectl apply -f storage-pool.yaml
```

Check that the pool is active:

```bash
kubectl get simplyblockpool -n simplyblock
```

Once the pool is active, the operator automatically creates a `StorageClass` named
`simplyblock-<clusterName>-<poolName>` — in this example, `simplyblock-production-production-pool`. It is
deleted when the pool is deleted. For full details and customization options, see
[Simplyblock Operator — Storage Pool](../../reference/operator.md#storage-pool).

```bash
kubectl get storageclass simplyblock-production-production-pool
```

---

## Step 4 — Provision Your First Volume

Everything is in place. Let's create a PersistentVolumeClaim and verify the full stack end-to-end.

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

```bash
kubectl apply -f test-pvc.yaml
kubectl get pvc simplyblock-test-pvc
```

```
NAME                    STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS                             AGE
simplyblock-test-pvc    Pending                                       simplyblock-production-production-pool   5s
```

**`Pending` is expected** — the StorageClass uses `WaitForFirstConsumer`, which means the volume is not
provisioned until a pod actually needs it. This is by design: the scheduler picks the right node first, then
the volume is created close to where it will be used.

### Mount it with a test pod

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

```bash
kubectl apply -f test-pod.yaml
```

Wait for the pod to reach `Running`, then check that the PVC is bound and the write succeeded:

```bash
kubectl get pvc simplyblock-test-pvc
```

```
NAME                    STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS                             AGE
simplyblock-test-pvc    Bound    pvc-3f2a1c9e-84b1-4d2e-9f3a-1234abcd5678   10Gi       RWO            simplyblock-production-production-pool   30s
```

```bash
kubectl exec simplyblock-test-pod -- cat /data/test.txt
```

```
volume provisioned successfully
```

Your cluster is fully operational. Clean up the test resources when you are done:

```bash
kubectl delete pod simplyblock-test-pod
kubectl delete pvc simplyblock-test-pvc
```

---

## Multi-Cluster Storage Node Support

A single Kubernetes cluster can host storage nodes connected to multiple simplyblock clusters. Create a
separate `StorageNode` resource for each simplyblock cluster, pointing different worker nodes at each:

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
