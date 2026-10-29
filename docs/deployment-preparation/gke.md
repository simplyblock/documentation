---
title: "GKE"
description: "Prepare a GKE cluster for simplyblock: recommended machine types with local NVMe SSDs, dedicated node pools, taints, node images, and control plane storage."
weight: 30060
---

Simplyblock runs in production on Google Kubernetes Engine (GKE) with dedicated node pools. As on EKS, a
production-like layout separates the control plane, the storage nodes, and the workloads that consume simplyblock
volumes into dedicated node pools, each tainted so that nothing else is scheduled onto it.

!!! info
    Hyper-converged deployments (co-location of workloads and storage) are supported on GKE, but complicate upgrades.

## Node Pools

The following node pools are recommended. Machine types are examples; the
[hardware requirements](hardware-requirements.md) and the [recommended machine types](#machine-types) apply.

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
write. A storage cluster can span zones with [failure domains](../architecture/concepts/failure-domains.md), using
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
    [Virtualization Support for pNFS](hardware-requirements.md#virtualization-support-for-pnfs)). On GKE, this means a
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
[NVMe over Fabrics multipathing](../important-notes/terminology.md#multipathing) (`CONFIG_NVME_MULTIPATH`). Client
node pools therefore use a node image that provides both, for example, Ubuntu (`--image-type UBUNTU_CONTAINERD`).
Whether a node supports native NVMe multipathing is checked on the host:

```bash title="Checking for native NVMe multipathing"
cat /sys/module/nvme_core/parameters/multipath
```

The answer must be `Y`. Storage nodes and control plane nodes are not affected, since the storage engine runs in user
space and the connections between storage nodes do not use the NVMe initiator of the host kernel.

## Storage for the Control Plane

FoundationDB and Prometheus of the control plane store their data on persistent volumes. GKE provides the Compute
Engine persistent disk CSI driver and the default StorageClass `standard-rwo`, which can be used for the control plane.
Host-local storage is not suitable, because an upgrade of a node pool replaces its nodes.

## TLS Prerequisite

TLS is enabled by default and requires cert-manager, unless TLS is explicitly turned off. cert-manager is installed into
the system node pool before the Simplyblock Operator. For details, see
[Install Simplyblock Operator](../kubernetes/installation/k8s-control-plane.md#prerequisites).

## Next Steps

The installation follows the same procedure as on [EKS](../kubernetes/installation/eks.md), with the node pools in
place of the node groups. The discovery detects GKE as the environment, and the storage nodes leave the kubelet
configuration of the workers unchanged.
