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
OperatorOps            ──► the operator inspects every eligible worker
      │                      (raised automatically on a fresh install)
      ▼ writes
ClusterDeploymentConfig ──► Draft: what the fleet has, as a reviewable document
      │                      │
      │                      ▼  (review, edit, then spec.approved: true)
      ▼ expands into       Expanding ──► Expanded
StorageCluster         ──► active (once enough storage nodes are online)
StorageNode(s)
      │
      ▼  (create a pool)
StoragePool            ──► a StorageClass is assigned to it
      │
      ▼  (create a PVC)
PersistentVolume       ──► Bound
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

## Review the Discovered Deployment

A cluster is not authored field by field. The operator inspects the workers and writes a
`ClusterDeploymentConfig`: one reviewable document holding the environment it targets, the cluster to create, and
the node sets with their workers, interfaces, and devices.

On a fresh install the operator raises that discovery run by itself, as an `OperatorOps` named
`initial-discovery`, so there is a draft to look at rather than an empty namespace. It is declined the moment
anything already exists — any `OperatorOps`, any `ClusterDeploymentConfig`, any `StorageCluster`, or a cluster with
no worker worth inspecting — because probing puts a Job on every worker.

```bash title="Find the discovered deployment config"
kubectl get clusterdeploymentconfig -n simplyblock
```

```plain title="Example output"
NAME                            PHASE   APPROVED   CLUSTER   AGE
discovered-initial-discovery    Draft   false                2m
```

A document produced by a run named `<name>` is called `discovered-<name>`. The phase is `Draft` and
`spec.approved` is `false`: it is validated but otherwise inert, which is what makes reviewing a wrong document
safe.

```bash title="Read the draft"
kubectl get clusterdeploymentconfig discovered-initial-discovery -n simplyblock -o yaml
```

```yaml title="A discovered deployment config, abridged"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ClusterDeploymentConfig
metadata:
  name: discovered-initial-discovery
  namespace: simplyblock
spec:
  approved: false
  environment: Vanilla
  cluster:
    name: simplyblock-cluster
    maxSubsystemCount: 75
    vcpuCount: 16
    fabricType: tcp
    stripe:
      dataChunks: 2
      parityChunks: 1
  nodeSets:
    - name: default
      groups:
        - name: default
          workers:
            - worker-1.example.com
            - worker-2.example.com
            - worker-3.example.com
          mgmtInterface: eth0
          dataInterfaces:
            - eth1
          devices:
            nvme:
              - "0000:01:00.0"
              - "0000:02:00.0"
```

The draft is everything the fleet has, because a guess at which disks somebody meant is a guess they then have to
find and undo. Narrowing it is the review.

## Edit the Draft

While `spec.approved` is `false`, the document is an ordinary editable resource. This is where workers that should
not hold storage are removed, disks are narrowed, failure domains are assigned, and the cluster's own settings are
set.

```bash title="Edit the draft"
kubectl edit clusterdeploymentconfig discovered-initial-discovery -n simplyblock
```

The operator validates a `Draft` on every reconcile and expands it on none. What validation found is written to
`status.message`, so the problems appear while the document is still editable rather than after it has been
approved:

```bash title="Read what validation found"
kubectl get clusterdeploymentconfig discovered-initial-discovery -n simplyblock \
    -o jsonpath='{.status.message}'
```

`DeviceNotFound` names a device the document claims and the worker does not have. `StripeBelowMinimumNodes` means
the erasure coding scheme needs more storage nodes than the document produces — `ndcs+npcs` to place a stripe
across, plus one spare per tolerated failure, so 3 for 1+1, 4 for 2+1, 6 for 4+1, 5 for 1+2, 6 for 2+2, and 8 for
4+2. `StripeBelowMinimumWorkers` is the same count falling short of *machines* rather than nodes, which several
nodes per worker cannot fix: every node of a worker fails with the worker.

A document discovery wrote cannot be wrong about its devices, because the list came from the inspection. A
hand-written one can, and this is the only check a device gets before the deployment runs.

`spec.cluster` is the cluster template: sizing, stripe, fabric, ports, and the cluster-wide toggles. Sizing is
uniform across a cluster and is stated once here rather than per node.

`spec.nodeSets[]` is the organizational grouping, usually a rack: the workers that are added or grown together.
Each set holds `groups[]`, and a group carries the workers plus what they share — `mgmtInterface`,
`dataInterfaces`, `devices`, `failureDomain`, `spdkSystemMemory`, `reservedSystemCPU`, and `journalManager`. Mixed
hardware is described by putting the workers that differ in their own group.

```yaml title="Two racks, one failure domain each"
spec:
  cluster:
    name: simplyblock-cluster
    enableFailureDomains: true
  nodeSets:
    - name: rack-a
      groups:
        - name: rack-a-nodes
          failureDomain: rack-a
          workers:
            - worker-a-1.example.com
            - worker-a-2.example.com
    - name: rack-b
      groups:
        - name: rack-b-nodes
          failureDomain: rack-b
          workers:
            - worker-b-1.example.com
            - worker-b-2.example.com
```

!!! note
    Every group has to name the same device class: either all `nvme` or all `block`, never a mix. A group's
    `devices` block names one or the other, not both.

### Copying, Splitting, and Hand-Authoring

A `ClusterDeploymentConfig` is an ordinary Kubernetes resource, and the discovered draft is a starting point rather
than the only thing that may be approved. A reviewer can copy it under another name, split one draft into several
documents that are approved separately, or write one from scratch and never run discovery at all.

Splitting is the usual reason. A draft covering three racks can become three documents, each holding one rack's
node set, so each rack is reviewed and brought up on its own schedule. The first document creates the cluster and
the other two name it in `spec.clusterRef`, as [Growing a Cluster](#growing-a-cluster) describes.

Each document describes exactly one cluster. The expansion never produces or extends more than the one
`spec.cluster` or `spec.clusterRef` names, so two clusters in one namespace are two documents.

A copy is a plain `kubectl get -o yaml`, edited and applied under a new name. Clear `metadata.resourceVersion`,
`metadata.uid`, and `status` from it first, as with any copied resource.

!!! tip "External KMS"
    If volumes in this cluster should offload their encryption keys to an external KMS, set
    `spec.cluster.kms.vault.endpoint` on the draft now. The setting can also be added to the `StorageCluster`
    later, but configuring it upfront means encrypted volumes use the external KMS from day one. See
    [Securing the Control Plane: External KMS](security.md#external-key-management-kms).

!!! note
    There are additional configuration properties for a storage cluster, such as NVMe-oF transport security, backup
    configuration, and capacity thresholds. They are described at
    [Cluster Deployment Options](../../deployment-preparation/cluster-deployment-options.md) and belong under
    `spec.cluster`.

## Approve the Deployment

Approval is a field, and it is the gate the expansion waits on.

```bash title="Approve the deployment"
kubectl patch clusterdeploymentconfig discovered-initial-discovery -n simplyblock \
    --type=merge -p '{"spec": {"approved": true}}'
```

!!! warning "Approval is one-way"
    An approved document is immutable, and approval cannot be withdrawn. Everything that should be changed has to
    be changed before this point. A deployment that was approved wrongly is corrected by deleting the objects it
    produced, not by editing the document.

The operator expands the document as soon as it is approved, through these steps, tracked in `status.step.state`:

| Step              | Description                                                    |
|-------------------|----------------------------------------------------------------|
| `Validating`      | The document is checked against what the cluster actually has. |
| `CreatingCluster` | The `StorageCluster` is created from `spec.cluster`.           |
| `AwaitingCluster` | The operator waits for the cluster to register.                |
| `CreatingNodes`   | One `StorageNode` is created per worker and NUMA socket.       |
| `Activating`      | The cluster is activated once enough storage nodes are online. |

```bash title="Watch the expansion"
kubectl get clusterdeploymentconfig discovered-initial-discovery -n simplyblock -w
```

The phase moves `Draft` → `Expanding` → `Expanded`. `status.clusterRef` names the `StorageCluster` that was
created and `status.nodeRefs` the `StorageNode` objects.

```bash title="Check what the expansion produced"
kubectl get storagecluster,storagenodes -n simplyblock
```

The document is ephemeral. Everything the expansion produces is self-describing, so the config can be edited or
deleted once it has been expanded: it is a deployment instruction, not a source of truth.

## Running Discovery Again

Discovery raises itself only on an install that has nothing. Every later run is created by hand:

```yaml title="discover.yaml"
apiVersion: storage.simplyblock.io/v1alpha2
kind: OperatorOps
metadata:
  name: rediscover
  namespace: simplyblock
spec:
  action: Discover
```

**A run reports only what is unclaimed, which is what makes re-running it useful.** A worker that already carries a
`StorageNode`, and a device that node already names in its `spec.config`, are not candidates. So a run against a
deployed fleet finds exactly the machines and disks nobody has taken yet, and re-running discovery after every
expansion is how a fleet is grown without anybody writing a worker list by hand.

A second run always writes a second document and never edits the first, because the first may already have been
reviewed and corrected, and overwriting a reviewer's corrections with a fresh guess is the worst thing it could do.
Its output is a `Draft` like any other.

`spec.discover` narrows the run:

| Field                     | Effect                                                                             |
|---------------------------|------------------------------------------------------------------------------------|
| `configName`              | The name of the document to write. Absent generates `discovered-<opsName>`.        |
| `clusterRef`              | Names an existing `StorageCluster` the draft grows rather than creating a new one. |
| `workers`                 | Inspects the named machines only.                                                  |
| `nodeSelector`            | Restricts which workers are inspected at all.                                      |
| `tolerations`             | What the probe pods tolerate, and what the draft then states on the cluster.       |
| `deviceFilter`            | Narrows which devices reach the draft.                                             |
| `enableControlPlaneNodes` | Lets the run consider machines that run the API server. Off by default.            |

A probe pod is pinned to its worker with `spec.nodeName`, which bypasses the scheduler but not the taints, so a run
against a dedicated storage plane that tolerates nothing inspects nothing. The same tolerations reach the draft's
`spec.cluster.tolerations`, because the taints a run was allowed to probe through are the taints the cluster it
proposes has to live with.

`spec.discover.deviceFilter` selects one class of backend storage and narrows it. `pcieAllowList`, `pcieDenyList`,
and `pcieModel` narrow the NVMe class; `enableLogicalBlockDevices` scans logical block devices instead, narrowed by
`blockAllowList` and `blockDenyList`. `driveSizeRange` and `enablePartitionedDevices` apply to whichever class is
being scanned. A cluster is built out of one class, so no draft holds both, and a filter naming the class the run
is not scanning is refused rather than ignored.

On a fleet that is uniform about which slot holds the boot device, one deny list keeps that device out of every
group of every draft — the difference between correcting one document and correcting each of twenty groups.

The run progresses through `Inspecting`, `Probing`, and `Writing`, and `status.configRef` names the document it
wrote.

## Growing a Cluster

Adding capacity is a second document, not an edit of the first. `spec.clusterRef` on the document is what says so:

```yaml title="A growth document"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ClusterDeploymentConfig
metadata:
  name: rack-c
  namespace: simplyblock
spec:
  approved: false
  clusterRef: simplyblock-cluster
  nodeSets:
    - name: rack-c
      groups:
        - name: rack-c-nodes
          failureDomain: rack-c
          workers:
            - worker-c-1.example.com
            - worker-c-2.example.com
```

A document that names `spec.clusterRef` carries no `spec.cluster`: the cluster already exists and its settings are
not restated. Naming it is also what marks every node the document creates as an expansion, so the control plane
rebalances onto them rather than treating them as part of an initial layout. There is no separate flag to set.

The two fields decide between them what the expansion does:

| `spec.cluster.name` resolves to | `spec.clusterRef` | Expansion does                             |
|---------------------------------|-------------------|--------------------------------------------|
| No existing `StorageCluster`    | absent            | Creates the cluster and all its nodes      |
| An existing `StorageCluster`    | absent            | Refuses: `ClusterExists`, phase `Failed`   |
| An existing `StorageCluster`    | set to it         | Adds only the nodes that do not exist yet  |
| No existing `StorageCluster`    | set               | Refuses: `ClusterNotFound`, phase `Failed` |

Setting `spec.discover.clusterRef` on the discovery run produces such a document directly: the run reports the
unclaimed workers and writes them as a growth document against that cluster, ready to review.

!!! warning "A config never removes anything"
    A node set left out of a later document does not drain a node, and a device removed from a group does not
    shrink one. Removal is destructive and belongs to `StorageNodeOps` with `action: Remove`, where it is
    deliberate, audited, and drains first. A document that could remove nodes by omission would make a typo a
    data-loss event.

The full expansion procedure, including its preconditions and what the cluster does while it integrates the new
nodes, is at [Expanding a Storage Cluster](../operations/scaling/expanding-storage-cluster.md).

## When does the Cluster become Active?

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

For a full list of configuration options see
[Simplyblock Operator: Fleet Configuration on the StorageCluster](../../reference/operator/index.md#fleet-configuration-on-the-storagecluster).

!!! warning
    Simplyblock exclusively owns the resources it has been allocated. It must be ensured they are sized correctly
    alongside other workloads.

    Additionally, simplyblock manages huge page allocation automatically. Total RAM required depends on vCPU count, the
    number of active logical volumes, and utilized virtual storage per node.

    More information can be found in [Minimum Hardware Requirements](../../deployment-preparation/hardware-requirements.md#minimum-system-requirements).

## Create a Storage Pool

A storage pool is a grouping of logical volumes and capacity limits within the cluster. An initial `StoragePool` resource must
be created to define a storage pool before being able to provision volumes.

```yaml title="storage-pool.yaml"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StoragePool
metadata:
  name: production-pool
  namespace: simplyblock
spec:
  clusterRef: production
  limits:
    capacity: "10T"
```

```bash title="Create the pool"
kubectl apply -f storage-pool.yaml
```

The status of the storage pool can be checked with:

```bash title="Check the pool status"
kubectl get storagepools -n simplyblock
```

A pool created this way has no StorageClass yet. A class is assigned to it by carrying the pool's three
assignment labels, and a pool may have as many as the volumes drawing on it need. The one class the operator
writes by itself belongs to the default pool a `StorageCluster` is created with.

`cluster_id` and `pool_name` are set from the storage pool and cannot be overridden. The remaining StorageClass
parameters come from `spec.volumeDefaults`. See
[Storage Class: StorageClass Created by a Storage Pool](../usage/storage-class.md#storageclass-created-by-a-storage-pool)
for the assignment labels and the full parameter mapping.

A StorageClass's parameters cannot be changed after creation, so `spec.volumeDefaults` is immutable
once the storage pool is created. A new storage pool is required to provision volumes with different defaults.

`spec.limits` is mutable. Raising a pool's capacity, or changing its QoS ceilings, is an ordinary operation the
control plane supports and it touches no `StorageClass`. The operator sends the whole block whenever the pool's
`metadata.generation` moves past `status.observedGeneration`, so an edit reaches the backend on the next reconcile.

```bash title="Raise the capacity limit of an existing pool"
kubectl patch storagepool production-pool -n simplyblock \
    --type=merge -p '{"spec": {"limits": {"capacity": "20T"}}}'
```

What the control plane reports the ceilings actually are is published separately, in `status.limits`, which is not
necessarily what `spec.limits` asked for.

```bash title="Read the ceilings the control plane applied"
kubectl get storagepool production-pool -n simplyblock -o jsonpath='{.status.limits}'
```

`allowedNodes` is reconciled as well, see
[Host Authentication and Encryption](../operations/security/authentication-encryption.md#managing-allowed-nodes).
`spec.clusterRef` is immutable, like `spec.volumeDefaults`.

### Deleting a Pool

A pool carries the finalizer `storage.simplyblock.io/storagepool-finalizer` and refuses to finish deleting while
anything Kubernetes knows about still refers to it.

| Deleting a pool with                      | Result                                                                 |
|-------------------------------------------|------------------------------------------------------------------------|
| An authored `StorageClass` assigned to it | Held. `StorageClassStillAssigned`, requeued, nothing deleted           |
| Only the operator's own default class     | The class is deleted, then the backend pool, then the finalizer clears |
| A `PersistentVolume` in it                | Held. `VolumesStillBound`, requeued, nothing deleted                   |
| Neither                                   | The backend pool is deleted and the finalizer clears                   |

An authored class holds the deletion because the operator neither wrote it nor knows why it exists, and deleting
somebody's provisioning contract to let a pool go is not a trade it makes. Deleting the class releases the pool.
The operator's own default class does not hold, because removing it is cleanup rather than a decision.

A `StorageCluster` owns its pools, so deleting one cascades — and is held behind any pool that is itself held, with
an event naming the pool and what is still in it.

Full details and customization options are available at
[Simplyblock Operator: Storage Pool](../../reference/operator/reference.md#storagepool).

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

A single Kubernetes cluster can host storage nodes belonging to several simplyblock clusters. Each one is its own
deployment config, approved separately.

Run discovery again without `spec.discover.clusterRef`, so the draft describes a new cluster rather than growing
the existing one, and narrow it to the workers that should belong to it:

```yaml title="Discover a second storage cluster"
apiVersion: storage.simplyblock.io/v1alpha2
kind: OperatorOps
metadata:
  name: discover-cluster-b
  namespace: simplyblock
spec:
  action: Discover
  discover:
    configName: cluster-b
    workers:
      - worker-b-1.example.com
      - worker-b-2.example.com
```

Set `spec.cluster.name` on the resulting draft to the name the second `StorageCluster` should have, then approve it
as above. Multiple storage clusters can share Kubernetes worker nodes, but it is recommended to point each storage
cluster to a different set of workers.
