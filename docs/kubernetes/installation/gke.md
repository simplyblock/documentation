---
title: "GKE"
description: "Prepare a GKE cluster for simplyblock: recommended machine types with local NVMe SSDs, dedicated node pools, taints, node images, and control plane storage."
weight: 40060
---

Simplyblock runs in production on Google Kubernetes Engine (GKE) with dedicated node pools. As on EKS, a
production-like layout separates the control plane, the storage nodes, and the workloads that consume simplyblock
volumes into dedicated node pools, each tainted so that nothing else is scheduled onto it.

!!! info
    Hyper-converged deployments (co-location of workloads and storage) are supported on GKE, but complicate upgrades.

## Node Pools

The following node pools are recommended. Machine types are examples; the
[hardware requirements](../../deployment-preparation/hardware-requirements.md) and the [recommended machine types](#machine-types) apply.

| Node Pool     | Purpose                                                                     | Example Machine Type                  | Example Taint                                      |
|---------------|-----------------------------------------------------------------------------|---------------------------------------|----------------------------------------------------|
| System        | Cluster add-ons: cert-manager, the Simplyblock Operator, the CSI controller | `e2-standard-2`                       | None                                               |
| Control plane | The simplyblock control plane, including FoundationDB and Prometheus        | `n2-standard-4`, 100 GB boot disk     | `simplyblock.io/role=controlplane:NoSchedule`      |
| Storage       | Simplyblock storage nodes                                                   | `n2-standard-16` with local NVMe SSDs | `storage.simplyblock.io/dedicated=true:NoSchedule` |
| Clients       | Workloads that mount simplyblock volumes                                    | Any                                   | `simplyblock.io/role=client:NoSchedule`            |

The taint keys and values are examples. Any taint works, as long as the same taint is referenced when the control
plane is installed and when the storage cluster is deployed. Each node pool also carries a label, for example,
`sb-role: storage-a`, which the Helm values and the discovery select nodes by. A storage node pool per storage
cluster keeps discovery runs of different clusters apart.

Storage nodes and client nodes are best placed in a single zone, since traffic between zones adds latency to every
write. A storage cluster can span zones with [failure domains](../../architecture/concepts/failure-domains.md), using
the zone as the failure domain label.

## Machine Types

In GCP, physical hosts are shared and sliced into virtual machines. This applies to CPU, RAM, and network bandwidth,
and also to the local NVMe SSDs, which provide a number of queue pairs that depends on their size. Several separately
attached local SSDs therefore give simplyblock the queue pairs it needs.

Three criteria drive the choice of a machine type for storage nodes:

- The minimum requirements of vCPUs and RAM
- The number and size of the local NVMe SSDs
- Network performance

The following machine types are commonly recommended for storage nodes:

| Machine Type     | vCPU(s) | RAM    | Additional Local SSD Storage | Network Performance |
|------------------|---------|--------|------------------------------|---------------------|
| _n2-standard-8_  | 8       | 32 GB  | 2x 2500 GB                   | 16 GBit/s           |
| _n2-standard-16_ | 16      | 64 GB  | 2x 2500 GB                   | 32 GBit/s           |
| _n2-standard-32_ | 32      | 128 GB | 4x 2500 GB                   | 32 GBit/s           |
| _n2-standard-48_ | 48      | 192 GB | 4x 2500 GB                   | 50 GBit/s           |
| _n2-standard-64_ | 64      | 256 GB | 6x 2500 GB                   | 75 GBit/s           |
| _n2-standard-80_ | 80      | 320 GB | 8x 2500 GB                   | 100 GBit/s          |

At least 8 vCPUs are required for a storage node.

!!! warning
    Local SSDs are added to a node pool when it is created and cannot be changed afterward. They have to be attached
    with the NVMe interface as raw block devices. SCSI-attached local SSDs do not work.

!!! note "pNFS volumes"
    The pNFS metadata server requires a worker node with a usable `/dev/kvm` (see
    [Virtualization Support for pNFS](../../deployment-preparation/hardware-requirements.md#virtualization-support-for-pnfs)). On GKE, this means a
    node pool with nested virtualization enabled, where the machine type supports it.

## Creating the Node Pools

The storage node pool is created with raw-block local NVMe SSDs, its label, and its taint:

```bash title="Creating the storage node pool"
gcloud container node-pools create storage-a \
    --cluster <CLUSTER_NAME> --zone <ZONE> \
    --machine-type n2-standard-16 --num-nodes 3 \
    --local-nvme-ssd-block count=2 \
    --node-labels sb-role=storage-a \
    --node-taints storage.simplyblock.io/dedicated=true:NoSchedule
```

The control plane and client node pools are created the same way, with their own labels and taints and without local
SSDs.

## Node Images

Nodes that mount simplyblock volumes require the `nvme-tcp` kernel module and native
[NVMe over Fabrics multipathing](../../important-notes/terminology.md#multipathing) (`CONFIG_NVME_MULTIPATH`). Client
node pools therefore use a node image that provides both, for example, Ubuntu (`--image-type UBUNTU_CONTAINERD`).
Whether a node supports native NVMe multipathing is checked on the host:

```bash title="Checking for native NVMe multipathing"
cat /sys/module/nvme_core/parameters/multipath
```

The answer must be `Y`. Storage nodes and control plane nodes are not affected, since the storage engine runs in user
space and the connections between storage nodes do not use the NVMe initiator of the host kernel.

An Ubuntu node image provides native multipathing but does not load the `nvme-tcp` module by default. Installing and
persisting it is the same as on any client node, described under
[NVMe/TCP Initiator on Client Nodes](install-csi.md#nvmetcp-initiator-on-client-nodes).

## Dedicated CPUs for Storage Nodes

By default, a storage node on GKE runs without the kubelet CPU topology configuration. The storage engine pins its
threads to CPUs, but the kubelet keeps those CPUs available to other pods, and enforces the CPU limit of the storage
node pod as a quota.

To give the storage engine CPUs of its own, the kubelet of the storage node pool is configured for static CPU
management, and the storage cluster is deployed with `enableCpuTopology`. The kubelet settings come from one of two
places:

- **Node system configuration:** The settings are part of the node pool and reach every node GKE creates for it.
- **Simplyblock:** The settings are written by simplyblock when a storage node is added. This requires the Ubuntu
  node image.

A node pool rebuilds the boot disk of a node whenever the node is recreated, for example, during an upgrade or a
repair. Settings written by simplyblock are lost with the disk, and the node system configuration is not. The node
system configuration is therefore recommended.

### Node System Configuration

The storage node pool is created with a node system configuration file.

```yaml title="Example of a node system configuration for storage nodes (storage-system-config.yaml)"
kubeletConfig:
  cpuManagerPolicy: static
  cpuCFSQuota: false
  topologyManager:
    policy: single-numa-node
    scope: pod
```

```bash title="Creating the storage node pool with dedicated CPUs"
gcloud container node-pools create storage-a \
    --cluster <CLUSTER_NAME> --zone <ZONE> \
    --machine-type n2-standard-16 --num-nodes 3 \
    --local-nvme-ssd-block count=2 \
    --image-type UBUNTU_CONTAINERD \
    --system-config-from-file storage-system-config.yaml \
    --node-labels sb-role=storage-a \
    --node-taints storage.simplyblock.io/dedicated=true:NoSchedule
```

With `cpuCFSQuota: false`, the polling threads of the storage engine are not throttled at the CPU limit of the pod.
The setting applies to every pod on the node, so it suits a node pool that is dedicated to storage nodes. The node
system configuration has no setting for reserved CPUs. One CPU is kept for the host by the kubelet reservation that
GKE sets.

The storage cluster is then deployed with the CPU topology enabled. The discovery writes a draft with
`environment: GKE`, which leaves the CPU topology off. Only a `Vanilla` draft states the two settings itself, so the
environment is changed before the draft is approved. `enableKubeletConfiguration: false` keeps the storage nodes from
changing the kubelet configuration that the node pool already provides.

```bash title="Enabling the CPU topology on a node pool with a node system configuration"
kubectl -n simplyblock patch clusterdeploymentconfig discovered-initial-discovery --type=merge -p '{
  "spec": {
    "environment": "Vanilla",
    "cluster": {"enableCpuTopology": true, "enableKubeletConfiguration": false}
  }
}'
```

### Kubelet Configuration by Simplyblock

On a node pool without a node system configuration, the kubelet configuration of the Ubuntu node image is written by
simplyblock when a storage node is added, and the kubelet is restarted once. Running pods are not stopped by that
restart.

```bash title="Enabling the CPU topology and the kubelet configuration by simplyblock"
kubectl -n simplyblock patch clusterdeploymentconfig discovered-initial-discovery --type=merge -p '{
  "spec": {
    "environment": "Vanilla",
    "cluster": {"enableCpuTopology": true, "enableKubeletConfiguration": true}
  }
}'
```

`reservedSystemCPU`, set per group of a node set, names the CPUs kept for the host and defaults to `0,1`. It names
both hardware threads of each reserved core. Otherwise, the storage engine receives the sibling thread and shares a
physical core with the host. The siblings of a CPU are read on the host:

```bash title="Reading the sibling threads of CPU 0"
cat /sys/devices/system/cpu/cpu0/topology/thread_siblings_list
```

### Priority Class Quota

With the CPU topology enabled, a NUMA resource plugin is run on every storage worker by the Simplyblock Operator. Its
pods carry the priority class `system-node-critical`. GKE admits pods of the system critical priority classes outside
of `kube-system` only in a namespace with a `ResourceQuota` that allows them. Without that quota, the plugin is not
started, and the storage node pods stay `Pending` with `Insufficient numa-align/numa-0`.

```yaml title="Example of a ResourceQuota for the critical pods of simplyblock (critical-pods-quota.yaml)"
apiVersion: v1
kind: ResourceQuota
metadata:
  name: simplyblock-critical-pods
  namespace: simplyblock
spec:
  hard:
    pods: "100"
  scopeSelector:
    matchExpressions:
      - operator: In
        scopeName: PriorityClass
        values: ["system-node-critical", "system-cluster-critical"]
```

The quota is created after the Simplyblock Operator is installed and before the draft is approved.

### Verification

After the storage cluster is active, the storage node pods belong to the `Guaranteed` class, which is what the kubelet
assigns exclusive CPUs to.

```bash title="Checking the class of the storage node pods"
kubectl -n simplyblock get pods -o custom-columns=NAME:.metadata.name,QOS:.status.qosClass | grep snode-spdk-pod
```

## Journal Device

The local NVMe SSDs of a GKE node have the same size, and by default a journal partition is carved out of each of
them. On GKE, the journal is placed on a device of its own instead. `enableJournalDevice` dedicates one local SSD of
each worker to the journal manager, so each storage node pool is created with one local SSD more than is needed for
data.

```bash title="Enabling the journal device in the draft"
kubectl -n simplyblock patch clusterdeploymentconfig discovered-initial-discovery --type=merge -p '{
  "spec": {"cluster": {"enableJournalDevice": true}}
}'
```

## Storage for the Control Plane

FoundationDB and Prometheus of the control plane store their data on persistent volumes. GKE provides the Compute
Engine persistent disk CSI driver and the default StorageClass `standard-rwo`, which can be used for the control plane.
Host-local storage is not suitable, because an upgrade of a node pool replaces its nodes.

## TLS Prerequisite

TLS is enabled by default and requires cert-manager, unless TLS is explicitly turned off. cert-manager is installed into
the system node pool before the Simplyblock Operator. For details, see
[Install Simplyblock Operator](k8s-control-plane.md#prerequisites).

## Next Steps

The installation follows the same procedure as on [EKS](eks.md), with the node pools in
place of the node groups. The discovery detects GKE as the environment, and the storage nodes leave the kubelet
configuration of the workers unchanged, unless the storage cluster is deployed as described under
[Dedicated CPUs for Storage Nodes](#dedicated-cpus-for-storage-nodes).
