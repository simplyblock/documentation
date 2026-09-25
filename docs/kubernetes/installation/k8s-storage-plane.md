---
title: "Create a Storage Cluster"
description: "Create a simplyblock storage cluster: discover workers and devices, review and approve the ClusterDeploymentConfig, and provision a first volume."
weight: 30100
---

With the [Simplyblock Operator](k8s-control-plane.md) installed and the control plane `Available`, the next step is
to bring up a storage cluster. A storage cluster is described by a single `ClusterDeploymentConfig` (CDC) document.
The operator writes a draft of it by probing the workers, an administrator reviews and approves it, and the operator
then creates the `StorageCluster`, its `StorageNode` resources, a default storage pool, and a StorageClass.

The following overview shows the process:

```plain title="Storage Cluster Lifecycle"
OperatorOps (Discover)        ──► probes the workers, writes a draft
ClusterDeploymentConfig       ──► Draft
                                    │
                                    ▼  (review, then spec.approved: true)
ClusterDeploymentConfig       ──► Expanding ──► Expanded
  StorageCluster              ──► Creating ──► Online
  StoragePool <cluster>-default + StorageClass simplyblock-<namespace>-<cluster>
  StorageNode(s)              ──► Provisioning ──► Online
  StorageClusterOps <cluster>-activate
                                    │
                                    ▼  (create a PVC)
PersistentVolume              ──► Bound
```

!!! info
    Not all Kubernetes workers have to become part of the simplyblock storage cluster. It is possible and common to
    only use a subset of all Kubernetes worker nodes for storage.

    It is also possible to use a separate Kubernetes worker node pool dedicated to storage. In this case, it is
    important to remember to taint the nodes accordingly to prevent other workloads from being scheduled on them.

## Prerequisites

### OpenShift

If deploying onto an OpenShift cluster, there are additional environment-specific steps in the
[OpenShift](openshift.md) guide before continuing here.

### Talos

If deploying onto a Talos cluster, there are additional environment-specific steps in the [Talos](talos.md) guide
before continuing here.

### Networking

Multiple ports must be open on storage node hosts.

It is required to use one or more separate VLANs for simplyblock. Ports within the same VLAN do not require extra
firewall rules, but ports between the control plane and storage networks typically do.

{% include 'network-port-table.md' %}

## Discover Workers and Devices

A discovery run inspects the workers, starts one probe job per worker, and writes the result as a draft
`ClusterDeploymentConfig`. The draft is inert: nothing is deployed until it is approved.

### Automatic Initial Discovery

On a fresh installation, the operator raises the `OperatorOps` run `initial-discovery` by itself. It does so only if
no `OperatorOps`, no `ClusterDeploymentConfig`, and no `StorageCluster` exist yet, and at least one usable worker is
found. The run inspects every schedulable worker and writes the draft `discovered-initial-discovery`.

```bash title="Follow the initial discovery"
kubectl -n simplyblock get operatorops initial-discovery -w
kubectl -n simplyblock get clusterdeploymentconfig
```

The run moves through the steps `Inspecting`, `Probing`, and `Writing`, and ends in the phase `Succeeded`.
`status.configRef` names the draft it wrote.

### Manual Discovery

Additional discovery runs are requested with an `OperatorOps` resource and the action `Discover`. The run can be
narrowed to specific workers (`workers` by name or `nodeSelector` by label, not both) and to specific devices.

```yaml title="discover-rack-b.yaml"
apiVersion: storage.simplyblock.io/v1alpha2
kind: OperatorOps
metadata:
  name: discover-rack-b
  namespace: simplyblock
spec:
  action: Discover
  discover:
    configName: rack-b-draft
    nodeSelector:
      storage.simplyblock.io/storage: "true"
    deviceFilter:
      pcieDenyList:
        - "0000:00:1f.0"
      driveSizeRange: 1T-4T
      enablePartitionedDevices: true
```

```bash title="Run the discovery"
kubectl apply -f discover-rack-b.yaml
kubectl -n simplyblock get operatorops discover-rack-b -w
```

The most important fields of `spec.discover` are:

- **`configName`:** The name of the draft to write. If empty, the draft is named `discovered-<run name>`, so a second
  run never overwrites a draft that may already have been reviewed.
- **`workers` or `nodeSelector`:** The workers to inspect. Empty inspects every schedulable worker.
- **`enableControlPlaneNodes`:** Also considers nodes that run the Kubernetes API server and etcd. Off by default.
- **`deviceFilter`:** Narrows the devices that reach the draft. `pcieAllowList`, `pcieDenyList`, and `pcieModel`
  select NVMe devices. `enableLogicalBlockDevices` together with `blockAllowList` and `blockDenyList` selects Linux
  block devices instead. `driveSizeRange` (for example, `1T-4T`) and `enablePartitionedDevices` apply to both.
- **`clusterRef`:** Writes a growth draft for an existing storage cluster instead of a new one.

The filters are inputs to the run only. The draft contains the explicit device list they produced, so re-running a
filter against changed hardware cannot change what a reviewer already approved.

## Review the Draft

A draft produced by discovery looks similar to the following. It lists every worker and device the run found and a
proposed cluster template.

```yaml title="A discovered draft"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ClusterDeploymentConfig
metadata:
  name: discovered-initial-discovery
  namespace: simplyblock
spec:
  approved: false
  environment: K3s
  cluster:
    name: discovered-initial-discovery-cluster
    enableDriveFormat: true
    maxSubsystemCount: 30
    minHugePagesSize: 16G
    vcpuCount: 16
    stripe:
      dataChunks: 1
      parityChunks: 1
  nodeSets:
    - name: discovered
      groups:
        - name: group-1-nvme-4x3T
          mgmtInterface: eth0
          workers:
            - worker-01
            - worker-02
            - worker-03
          devices:
            nvme:
              - 0000:5e:00.0
              - 0000:5f:00.0
              - 0000:af:00.0
              - 0000:b0:00.0
```

`status.message` of the draft lists validation findings, for example, `DeviceNotFound`, `StripeBelowMinimumNodes`,
or `StripeBelowMinimumWorkers`. The draft is edited in place until the findings are resolved:

```bash title="Review and edit the draft"
kubectl -n simplyblock get cdc discovered-initial-discovery -o wide
kubectl -n simplyblock edit cdc discovered-initial-discovery
```

### Environment

`spec.environment` names the Kubernetes distribution: `Vanilla`, `OpenShift`, `Rancher`, `K3s`, or `Talos`. It sets
the storage node flags on `StorageCluster.spec.storageNodes`:

- **`OpenShift`:** Enables `openShiftCluster`, `enableCpuTopology`, and `enableKubeletConfiguration`.
- **`Talos`:** Disables `enableKubeletConfiguration`, because Talos has no writable kubelet configuration.
- **`Vanilla`, `Rancher`, `K3s`:** Enable `enableKubeletConfiguration`.

### Cluster Template

`spec.cluster` is the template of the storage cluster to create. It is ignored if `spec.clusterRef` names an existing
cluster.

- **`name`:** Name of the `StorageCluster` (at most 63 characters). Discovery proposes `<draft name>-cluster`.
- **`maxSubsystemCount`:** Required, from 10 to 75.
- **`vcpuCount`:** Required, at least 4. The number of vCPUs per storage node.
- **`minHugePagesSize`:** Minimum huge page memory per storage node, for example, `16G`.
- **`stripe`:** The [erasure coding scheme](../../deployment-preparation/erasure-coding-scheme.md) as `dataChunks` and
  `parityChunks`. Allowed combinations are 1+0, 1+1, 2+1, 4+1, 1+2, 2+2, and 4+2.
- **`fabricType`:** The NVMe-oF transport, for example, `tcp`.
- **`enableDriveFormat`:** Formats every listed device before a storage node takes it. This is destructive and must
  be reviewed before approving.
- **`enableJournalDevice`:** Dedicates the smallest NVMe device of each worker to the journal manager.
- **`socketsToUse`, `nodesPerSocket` (1 to 8), `nodeProvisioningBudget`:** How many storage nodes run on each worker
  and how many are provisioned in parallel. Empty `socketsToUse` means socket 0 only.
- **`enableChecksumValidation`, `enableAtomicity4K`:** Data integrity options. `enableAtomicity4K` requires checksum
  validation.
- **`enableFailureDomains`:** Places data across failure domains, see below.
- **`kms`:** An external KMS for volume encryption keys, see
  [Securing the Control Plane](security.md#external-key-management-kms).

Most of these settings are immutable on the created `StorageCluster`, so the review is the last opportunity to
change them.

### Node Groups and Devices

`spec.nodeSets` (1 to 64 sets) groups the workers. Each set contains `groups`, and each group lists:

- **`workers`:** The Kubernetes node names (1 to 200).
- **`mgmtInterface`, `dataInterfaces`:** The management and data network interfaces.
- **`devices`:** Either `nvme` (PCI addresses) or `block` (Linux block devices, for example, `/dev/sdb`). All groups of
  a document must use the same device class.
- **`failureDomain`:** The failure domain label of all workers in the group.
- **`spdkSystemMemory`, `journalManager`:** Optional per-group storage node settings.

Workers or devices that should not become part of the cluster, for example, a boot disk, are removed from the draft
before approving.

### Failure Domains

With `spec.cluster.enableFailureDomains: true`, every group must carry a `failureDomain` label, for example, a rack
name. The label is copied to each generated `StorageNode` and cannot be changed afterward.

```yaml title="Failure domains per group"
spec:
  cluster:
    name: production
    maxSubsystemCount: 50
    vcpuCount: 8
    stripe:
      dataChunks: 2
      parityChunks: 1
    enableFailureDomains: true
  nodeSets:
    - name: racks
      groups:
        - name: rack-a
          failureDomain: rack-a
          workers: [worker-1, worker-2]
          devices:
            nvme: ["0000:01:00.0", "0000:02:00.0"]
        - name: rack-b
          failureDomain: rack-b
          workers: [worker-3, worker-4]
          devices:
            nvme: ["0000:01:00.0", "0000:02:00.0"]
```

For details, see [Failure Domains](../operations/cluster/failure-domains.md).

### When Does the Cluster Become Active?

The erasure coding scheme determines the minimum number of storage nodes. The approval is refused if the document
provides fewer nodes, or if they sit on too few workers. An unstated scheme counts as 1+1.

| Scheme                | 1+0 | 1+1 | 2+1 | 4+1 | 1+2 | 2+2 | 4+2 |
|-----------------------|-----|-----|-----|-----|-----|-----|-----|
| Minimum storage nodes | 1   | 3   | 4   | 6   | 5   | 6   | 8   |

The operator activates the cluster as soon as all storage nodes of the document are `Online`.

## Approve the Deployment

Once the draft is correct, it is approved by setting `spec.approved: true`. The admission webhook validates the
approving edit against the live cluster, for example, that the devices exist. After approval, the document is
immutable and the approval cannot be withdrawn.

```bash title="Approve the draft"
kubectl -n simplyblock patch cdc discovered-initial-discovery \
    --type=merge -p '{"spec":{"approved":true}}'

kubectl -n simplyblock get cdc discovered-initial-discovery -w
```

The document moves from `Draft` to `Expanding` and finally to `Expanded` (or `Failed`). While expanding, it passes the
steps `Validating`, `CreatingCluster`, `AwaitingCluster`, `CreatingNodes`, and `Activating`.

!!! warning
    Simplyblock exclusively owns the resources it has been allocated. It must be ensured they are sized correctly
    alongside other workloads.

    Additionally, simplyblock manages huge page allocation automatically. Total RAM required depends on vCPU count, the
    number of active logical volumes, and utilized virtual storage per node.

    More information can be found in [Minimum Hardware Requirements](../../deployment-preparation/hardware-requirements.md#minimum-system-requirements).

### What Gets Created

The expansion creates the following resources:

- **`StorageCluster`:** Named after `spec.cluster.name`, in the namespace of the document. A namespace holds at most
  one storage cluster.
- **`StoragePool` `<cluster>-default`:** The default pool. It is created once and never recreated.
- **StorageClass `simplyblock-<namespace>-<cluster>`:** The class of the default pool, with the provisioner
  `csi.simplyblock.io`, `WaitForFirstConsumer` binding, the reclaim policy `Delete`, and volume expansion enabled. It
  is not marked as the Kubernetes default class.
- **`StorageNode` resources:** One per worker, socket, and node per socket. Each is provisioned by the storage node
  DaemonSet, and its devices appear as `StorageDevice` resources.
- **`StorageClusterOps` `<cluster>-activate`:** Raised once all storage nodes are `Online`.

With a cluster named `production` in the namespace `simplyblock`, the default pool is `production-default` and the
StorageClass is `simplyblock-simplyblock-production`.

The `ClusterDeploymentConfig` is no longer needed after it reaches `Expanded` and can be deleted.

## Verify the Cluster

```bash title="Check the storage cluster and its resources"
kubectl -n simplyblock get storagecluster,storagenode,storagedevice,storagepool
```

The same resources can be listed with their short names, `kubectl -n simplyblock get stc,sn,sd,sp`.

```plain title="Example output of kubectl -n simplyblock get stc"
NAME         PHASE    STEP   STATUS   EC    UUID                                   AGE
production   Online          active   2x1   bfa260ce-06a7-4bcb-a843-813d0be633af   12m
```

The `StorageCluster` phase is `Online` once the cluster is active. `Degraded` and `Unavailable` indicate problems,
and `status.message` explains them. The storage nodes report `Online` in their phase column.

The operator also writes the cluster credentials for the CSI driver into the Secret `simplyblock-csi-secret-v2` in the
operator's namespace. The Secret is maintained by the operator and does not need to be managed manually.

## Create a Storage Pool

Volumes can be provisioned from the default pool right away. Additional pools divide the cluster into tenancy units
with their own capacity and QoS limits. A `StoragePool` references its cluster with `clusterRef`.

```yaml title="storage-pool.yaml"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StoragePool
metadata:
  name: tenant-a
  namespace: simplyblock
spec:
  clusterRef: production
  limits:
    capacity: 10T
    maxVolumeSize: 2T
    iops: 200000
    throughput:
      readWrite: 4096
  volumeDefaults:
    iops: 20000
    throughput:
      readWrite: 512
    filesystem: xfs
```

```bash title="Create the pool"
kubectl apply -f storage-pool.yaml
kubectl -n simplyblock get storagepool tenant-a
```

`spec.limits` (capacity, maximum volume size, IOPS, and throughput in MB/s) can be changed later. `spec.volumeDefaults`
is immutable once set. `spec.allowedNodes` restricts the pool to specific Kubernetes nodes, see
[Host Authentication and Encryption](../operations/security/authentication-encryption.md).

### Author a StorageClass for the Pool

The operator creates a StorageClass only for the default pool. For every other pool, the StorageClass is written by
the administrator and linked to the pool with three labels: `storage.simplyblock.io/namespace`,
`storage.simplyblock.io/cluster`, and `storage.simplyblock.io/pool`. The parameters `cluster_id` (the cluster's
`status.uuid`) and `pool_name` direct the CSI driver to the pool.

```yaml title="storage-class-tenant-a.yaml"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: tenant-a-fast
  labels:
    storage.simplyblock.io/namespace: simplyblock
    storage.simplyblock.io/cluster: production
    storage.simplyblock.io/pool: tenant-a
provisioner: csi.simplyblock.io
parameters:
  cluster_id: "<StorageCluster status.uuid>"
  pool_name: tenant-a
  max_iops: "20000"
  csi.storage.k8s.io/fstype: xfs
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

The pool lists its assigned classes in `status.storageClassNames`. For the full parameter mapping, see
[Storage Class](../usage/storage-class.md).

## Provision the First Volume

Now, everything is in place to create the first volume. The operator has deployed the simplyblock CSI driver into the
Kubernetes cluster. Hence, creating a volume is as simple as creating a PersistentVolumeClaim with the correct
StorageClass set.

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
  storageClassName: simplyblock-simplyblock-production
```

```bash title="Create the PVC"
kubectl apply -f test-pvc.yaml
kubectl get pvc simplyblock-test-pvc
```

```plain title="Example output of PVC status"
NAME                    STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS                         AGE
simplyblock-test-pvc    Pending                                       simplyblock-simplyblock-production   5s
```

Since provisioning is asynchronous, the PVC status is initially `Pending`. The StorageClass uses
`WaitForFirstConsumer`, which means the volume is not provisioned until a pod actually needs it. The scheduler picks
the right node first, then the volume is created close to where it will be used.

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
NAME                    STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS                         AGE
simplyblock-test-pvc    Bound    pvc-3f2a1c9e-84b1-4d2e-9f3a-1234abcd5678   10Gi       RWO            simplyblock-simplyblock-production   30s
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

## Growing and Adding Clusters

- **More nodes for an existing cluster:** A `ClusterDeploymentConfig` with `spec.clusterRef` and no `spec.cluster`
  block adds nodes to an existing cluster. A discovery run with `discover.clusterRef` writes such a growth draft. See
  [Expanding a Storage Cluster](../operations/scaling/expanding-storage-cluster.md).
- **More storage clusters:** A namespace holds at most one `StorageCluster`, so every additional storage cluster
  needs a namespace of its own. It is recommended to point each storage cluster to a different set of workers.
