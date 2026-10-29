---
title: "EKS"
description: "Prepare an EKS cluster for simplyblock: recommended instance types, dedicated node groups, taints, node images with NVMe multipathing, and EBS storage."
weight: 30050
---

Simplyblock runs on EKS with managed node groups. A production-like layout separates the control plane, the
storage nodes, and the workloads that consume simplyblock volumes into dedicated node groups, each tainted so that
nothing else is scheduled onto it.

!!!! info
     Hyper-converged deployments (co-location of workloads and storage) are supported on EKS, but complicate upgrades.

## Node Groups

The following node groups are recommended. Instance types are examples; the
[hardware requirements](hardware-requirements.md) and the [recommended instance types](#instance-types) apply.

| Node Group    | Purpose                                                                              | Example Instance Type              | Example Taint                                      |
|---------------|--------------------------------------------------------------------------------------|------------------------------------|----------------------------------------------------|
| System        | Cluster add-ons: CoreDNS, cert-manager, the Simplyblock Operator, the CSI controller | `t3a.large`                        | None                                               |
| Control plane | The simplyblock control plane, including FoundationDB and Prometheus                 | `m6a.xlarge`, 100 GB gp3 boot disk | `simplyblock.io/role=controlplane:NoSchedule`      |
| Storage       | Simplyblock storage nodes                                                            | `m6id`, `i4i`, or `i3en` instances | `storage.simplyblock.io/dedicated=true:NoSchedule` |
| Clients       | Workloads that mount simplyblock volumes                                             | Any                                | `simplyblock.io/role=client:NoSchedule`            |

The taint keys and values are examples. Any taint works, as long as the same taint is referenced when the control
plane is installed and when the storage cluster is deployed (see [EKS](../kubernetes/installation/eks.md)).

Each node group also carries a label, for example, `sb-role: controlplane`, `sb-role: storage-a`, or `sb-role: client`.
The label is what the Helm values and the discovery select nodes by. A storage node group per storage cluster keeps
discovery runs of different clusters apart.

Storage nodes require instances with local NVMe instance storage. EBS volumes work, but are not recommended for
storage nodes for performance reasons.

## Instance Types

Simplyblock has been tested on and recommends the following instance types. Other instance types can be used as long
as they fulfill the [hardware requirements](hardware-requirements.md). At least 8 vCPUs are required for a storage
node.

Three criteria drive the choice of an instance type for storage nodes:

- The minimum requirements of vCPUs and RAM
- Locally attached NVMe devices
- Network performance (dedicated, not "up to")

For storage nodes ***in disaggregated clusters***, the following instance types are commonly recommended:

| Instance Type   | vCPU(s) | RAM    | Locally Attached Storage | Network Performance |
|-----------------|---------|--------|--------------------------|---------------------|
| _i4g.8xlarge_   | 32      | 256 GB | 2x 3750 GB               | 18.5 GBit/s         |
| _i4g.16xlarge_  | 64      | 512 GB | 4x 3750 GB               | 37.5 GBit/s         |
| _i3en.6xlarge_  | 24      | 192 GB | 2x 7500 GB               | 25 GBit/s           |
| _i3en.12xlarge_ | 48      | 384 GB | 4x 7500 GB               | 50 GBit/s           |
| _i3en.24xlarge_ | 96      | 768 GB | 8x 7500 GB               | 100 GBit/s          |
| _m5d.4xlarge_   | 16      | 64 GB  | 2x 300 GB                | 10 GBit/s           |
| _i4i.8xlarge_   | 32      | 256 GB | 2x 3750 GB               | 18.75 GBit/s        |
| _i4i.12xlarge_  | 48      | 384 GB | 3x 3750 GB               | 28.12 GBit/s        |

For hyper-converged workers, any instance type with a local NVMe SSD can be chosen.

!!! note "pNFS volumes"
    The pNFS metadata server requires a worker node with a usable `/dev/kvm` (see
    [Virtualization Support for pNFS](hardware-requirements.md#virtualization-support-for-pnfs)). On EC2, this means
    nested virtualization on a virtualized instance type, where the instance type supports it, or a bare-metal
    instance type, which exposes `/dev/kvm` once the KVM kernel modules are loaded.

### Availability Zones and Placement

Storage nodes and client nodes are best placed in a single availability zone. Traffic between availability zones adds
latency to every write and is billed. Within the zone, storage nodes are placed into a placement group of type
_Spread_, so that no two storage nodes share the same hardware.

!!! important
    A storage cluster can span availability zones in two ways:

    - Use failure domains and the zone name to label nodes with the failure domain. This works across two or four sites.
      With 4 sites, two can be down concurrently. The protection overhead is x2 in both cases.
    - Use synchronous replication on top of per-zone distributed erasure coding. This works across two sites
      and survives a site outage and a local node outage concurrently. The protection overhead is x2.5.
    - In both cases, still use a placement group of type _Spread_ for the nodes in the storage node pool per AZ.

## Node Images

!!! warning "Amazon Linux 2023 is not suitable for client nodes"
    Nodes that mount simplyblock volumes require a Linux kernel with native
    [NVMe over Fabrics multipathing](../important-notes/terminology.md#multipathing) (`CONFIG_NVME_MULTIPATH`).
    The kernel of the default Amazon Linux 2023 EKS node image is built without it. Every path of a volume then appears
    as a separate block device, and the client cannot switch paths. A storage node outage, a failover, and the cutover
    of an online migration interrupt the I/O of the volume.

    Client nodes therefore run an image with native NVMe multipathing, for example, the Ubuntu 24.04 EKS images
    published by Canonical (`ubuntu-eks/k8s_<VERSION>/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*`).

Storage nodes and control plane nodes may run Amazon Linux 2023. The storage engine runs in user space, and the
connections between storage nodes do not use the NVMe initiator of the host kernel.

Whether a node supports native NVMe multipathing is checked on the host:

```bash title="Checking for native NVMe multipathing"
cat /sys/module/nvme_core/parameters/multipath
```

The answer must be `Y`. Once a volume is attached, `nvme list-subsys` shows a single subsystem with one `live` path per
storage node that serves the volume, and the volume appears as one block device.

```plain title="Example output with native NVMe multipathing"
nvme-subsys1 - NQN=nqn.2023-02.io.simplyblock:<CLUSTER_UUID>:lvol:<VOLUME_UUID>
               iopolicy=numa
\
 +- nvme2 tcp traddr=192.168.4.223,trsvcid=4426 live
 +- nvme1 tcp traddr=192.168.20.206,trsvcid=4426 live
```

A node group with a custom image needs an explicit bootstrap command in `eksctl`. The Ubuntu EKS images provide
`/etc/eks/bootstrap.sh`. Labels and taints are passed to the kubelet, and the API server endpoint and the cluster CA
are stated explicitly, because the node role is usually not allowed to read them from the EKS API.

```yaml title="Example of a client node group with Ubuntu 24.04 (eksctl)"
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig
metadata:
  name: <CLUSTER_NAME>
  region: <REGION>
managedNodeGroups:
  - name: clients
    ami: <UBUNTU_EKS_AMI_ID>
    amiFamily: Ubuntu2404
    instanceType: c6a.2xlarge
    desiredCapacity: 3
    availabilityZones: ["<AVAILABILITY_ZONE>"]
    labels: {sb-role: client}
    taints: [{key: simplyblock.io/role, value: client, effect: NoSchedule}]
    overrideBootstrapCommand: |
      #!/bin/bash
      /etc/eks/bootstrap.sh <CLUSTER_NAME> \
        --apiserver-endpoint '<API_SERVER_ENDPOINT>' \
        --b64-cluster-ca '<BASE64_CLUSTER_CA>' \
        --dns-cluster-ip <CLUSTER_DNS_IP> \
        --kubelet-extra-args '--node-labels=sb-role=client --register-with-taints=simplyblock.io/role=client:NoSchedule'
```

The API server endpoint and the CA are read with
`aws eks describe-cluster --name <CLUSTER_NAME> --query 'cluster.[endpoint,certificateAuthority.data]'`. The cluster DNS IP
is the tenth address of the service CIDR, `10.100.0.10` for the default CIDR `10.100.0.0/16`.

The control plane and storage node groups are declared the same way, with their own labels and taints, and without a
custom image.

```yaml title="Example of control plane and storage node groups (eksctl)"
managedNodeGroups:
  - name: controlplane
    instanceType: m6a.xlarge
    desiredCapacity: 3
    availabilityZones: ["<AVAILABILITY_ZONE>"]
    volumeSize: 100
    volumeType: gp3
    labels: {sb-role: controlplane}
    taints: [{key: simplyblock.io/role, value: controlplane, effect: NoSchedule}]
    updateConfig: {maxUnavailable: 1}
  - name: storage-a
    instanceType: m6id.2xlarge
    desiredCapacity: 3
    availabilityZones: ["<AVAILABILITY_ZONE>"]
    labels: {sb-role: storage-a}
    taints: [{key: storage.simplyblock.io/dedicated, value: "true", effect: NoSchedule}]
```

`updateConfig.maxUnavailable: 1` makes an upgrade of the control plane node group replace one node at a time (see
[Upgrading EKS](../kubernetes/operations/cluster/eks-upgrade.md)).

## Storage for the Control Plane

FoundationDB and Prometheus of the control plane store their data on persistent volumes. An EKS cluster has no default
StorageClass, so the EBS CSI driver add-on and a gp3 StorageClass are created first. The node role (or an IAM
role for the add-on's service account) needs the AWS managed policy `AmazonEBSCSIDriverPolicy`.

```bash title="Installing the EBS CSI driver add-on"
aws eks create-addon --cluster-name <CLUSTER_NAME> --addon-name aws-ebs-csi-driver
```

```yaml title="gp3 StorageClass for the control plane (ebs-gp3.yaml)"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-gp3
provisioner: ebs.csi.aws.com
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Delete
allowVolumeExpansion: true
parameters:
  type: gp3
```

Host-local storage, such as a hostPath StorageClass, is not suitable for the control plane on EKS. An upgrade of a
managed node group replaces its nodes with new instances, and data on the replaced instance is lost. An EBS volume is
attached to the replacement node in the same availability zone.

## TLS Prerequisite

TLS is enabled by default and requires cert-manager, unless TLS is explicitly turned off. cert-manager is installed into
the system node group before the Simplyblock Operator. For details, see
[Install Simplyblock Operator](../kubernetes/installation/k8s-control-plane.md#prerequisites).

```bash title="Installing cert-manager"
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
    -n cert-manager --create-namespace --set crds.enabled=true
```

## Next Steps

With the node groups, the StorageClass, and cert-manager in place, the installation continues with
[EKS](../kubernetes/installation/eks.md).
