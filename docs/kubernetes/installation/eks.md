---
title: "EKS"
description: "Install simplyblock on EKS: node groups, taints, node images, the eksctl cluster configuration, Helm values, discovery, and verification, with complete files."
weight: 40050
---

Simplyblock runs on EKS with managed node groups. A production-like layout separates the system add-ons, the
control plane, the storage nodes, and the workloads that consume simplyblock volumes into dedicated node groups. Every
node group except the system node group is tainted, so that nothing else is scheduled onto it.

!!! info
    Hyper-converged deployments (co-location of workloads and storage) are supported on EKS, but complicate upgrades.

## Overview

An installation on EKS takes the following steps. Every file this page uses is shown in full.

1. [Create the cluster](#cluster-configuration) with `eksctl` from `cluster.yaml`, and add the client node group from
   `clients.yaml`.
2. [Install cert-manager](#cert-manager), unless the cluster has it already.
3. [Install the Simplyblock Operator](#installation) with Helm and `values-eks.yaml`. The operator installs what the
   control plane needs on EKS by itself, including the [storage for the control plane](#storage-for-the-control-plane),
   and runs the discovery on the storage node group.
4. [Review and approve the draft](#reviewing-and-approving-the-draft) the discovery wrote. The operator creates the
   storage cluster.
5. [Verify the placement](#verifying-the-placement).

### Tools

The commands on this page run on any machine with credentials for the AWS account: a workstation, a bastion host, or
a CI job. They need the following tools:

| Tool                                                                                                                      | Purpose                                      | Check                         |
|---------------------------------------------------------------------------------------------------------------------------|----------------------------------------------|-------------------------------|
| [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html){:target="_blank" rel="noopener"} | Credentials, account ID, and cluster details | `aws sts get-caller-identity` |
| [eksctl](https://eksctl.io/installation/){:target="_blank" rel="noopener"}                                                | Creates the cluster and the node groups      | `eksctl version`              |
| [kubectl](https://kubernetes.io/docs/tasks/tools/){:target="_blank" rel="noopener"}                                       | Works with the cluster                       | `kubectl version --client`    |
| [Helm](https://helm.sh/docs/intro/install/){:target="_blank" rel="noopener"}                                              | Installs cert-manager and the operator       | `helm version`                |

The AWS identity needs the rights to create EKS clusters, EC2 instances, CloudFormation stacks, and IAM roles.
`eksctl` writes the kubeconfig of the new cluster, so `kubectl` and `helm` work right after it.

!!! note "Windows"
    Every command on this page is written on a single line, so it runs unchanged in PowerShell and in bash. The tools
    have to be on the `PATH`. PowerShell does not run programs from the current directory without `.\`, so a tool
    that is only in the current directory is not found as `helm` or `kubectl`.

## Node Groups

The following node groups are recommended. Instance types are examples. The
[hardware requirements](../../deployment-preparation/hardware-requirements.md) and the
[recommended instance types](#instance-types) apply.

| Node Group    | Purpose                                                                                  | Example Instance Type              | Label                  | Taint                                              |
|---------------|------------------------------------------------------------------------------------------|------------------------------------|------------------------|----------------------------------------------------|
| System        | Cluster add-ons: CoreDNS, cert-manager, the EBS CSI controller, the Simplyblock Operator | `t3a.large`                        | `sb-role=system`       | None                                               |
| Control plane | The simplyblock control plane, including FoundationDB and Prometheus                     | `m6a.xlarge`, 100 GB gp3 boot disk | `sb-role=controlplane` | `simplyblock.io/role=controlplane:NoSchedule`      |
| Storage       | Simplyblock storage nodes                                                                | `m6id`, `i4i`, or `i3en` instances | `sb-role=storage-a`    | `storage.simplyblock.io/dedicated=true:NoSchedule` |
| Clients       | Workloads that mount simplyblock volumes                                                 | Any                                | `sb-role=client`       | `simplyblock.io/role=client:NoSchedule`            |

!!! warning "The system node group is required"
    The system node group carries no taint. Without it, every node is tainted, and CoreDNS, cert-manager, the EBS CSI
    controller, and the Simplyblock Operator itself have nowhere to run. They stay `Pending`, and the installation
    does not start.

The labels and taints are examples. Any label and taint work, as long as the same ones are used in `cluster.yaml`,
`clients.yaml`, and `values-eks.yaml`. A storage node group per storage cluster keeps the discovery runs of different
clusters apart.

Storage nodes require instances with local NVMe instance storage. EBS volumes work, but are not recommended for
storage nodes for performance reasons.

## Instance Types

Simplyblock has been tested on and recommends the following instance types. Other instance types can be used as long
as they fulfill the [hardware requirements](../../deployment-preparation/hardware-requirements.md). At least 8 vCPUs are required for a storage
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
    [Virtualization Support for pNFS](../../deployment-preparation/hardware-requirements.md#virtualization-support-for-pnfs)). On EC2, this means
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
    [NVMe over Fabrics multipathing](../../important-notes/terminology.md#multipathing) (`CONFIG_NVME_MULTIPATH`).
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

The NVMe/TCP initiator, the `nvme-tcp` kernel module, is not part of the Ubuntu EKS images. The Ubuntu AWS kernel
ships it in the package `linux-modules-extra-<KERNEL_VERSION>`, which the images do not install. Without it, the CSI
driver cannot load the module, and attaching a volume fails with
`Failed to open /dev/nvme-fabrics: No such file or directory`. The package is installed, and the module loaded, before
the node joins the cluster:

```bash title="Installing the NVMe/TCP initiator on an Ubuntu EKS node"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y linux-modules-extra-$(uname -r)
echo nvme-tcp > /etc/modules-load.d/nvme-tcp.conf
modprobe nvme-tcp
```

`/dev/nvme-fabrics` exists once the module is loaded, and the `nvme-tcp.conf` entry loads it again after a reboot.

A node group with a custom image needs an explicit bootstrap command in `eksctl`. The client node group in
[`clients.yaml`](#the-client-node-group) shows it in full. The control plane and storage node groups run the default
Amazon Linux 2023 image and need no bootstrap command.

## Cluster Configuration

The cluster is created in two steps. `cluster.yaml` creates the cluster with the system, control plane, and storage
node groups. The client node group runs a custom image, whose bootstrap command needs the API server endpoint and the
CA of the cluster, so `clients.yaml` adds it once the cluster exists.

The examples use the cluster name `simplyblock-eks` in the region `eu-central-1`. The names, the region, the
availability zones, and the instance types are replaced with the actual ones in both files.

### The Cluster

```yaml title="cluster.yaml"
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: simplyblock-eks
  region: eu-central-1
  version: "1.33"

# EKS places its own control plane in at least two availability zones, also when
# every node group runs in one of them.
availabilityZones: ["eu-central-1a", "eu-central-1b"]

iam:
  # Required for the IAM role of the EBS CSI driver add-on below, and for keyless
  # backup credentials (IRSA).
  withOIDC: true

addons:
  - name: vpc-cni
  - name: coredns
  - name: kube-proxy
  # Provisions the gp3 volumes of the control plane. The operator detects it and
  # creates the gp3 StorageClass for it.
  - name: aws-ebs-csi-driver
    wellKnownPolicies:
      ebsCSIController: true

managedNodeGroups:
  # Untainted: CoreDNS, cert-manager, the EBS CSI controller, and the operator.
  - name: system
    instanceType: t3a.large
    desiredCapacity: 2
    minSize: 2
    maxSize: 3
    availabilityZones: ["eu-central-1a"]
    labels: {sb-role: system}

  - name: controlplane
    instanceType: m6a.xlarge
    desiredCapacity: 3
    minSize: 3
    maxSize: 3
    availabilityZones: ["eu-central-1a"]
    volumeSize: 100
    volumeType: gp3
    labels: {sb-role: controlplane}
    taints: [{key: simplyblock.io/role, value: controlplane, effect: NoSchedule}]
    # Replace one node at a time during node group upgrades.
    updateConfig: {maxUnavailable: 1}

  - name: storage-a
    instanceType: m6id.2xlarge
    desiredCapacity: 3
    minSize: 3
    maxSize: 3
    availabilityZones: ["eu-central-1a"]
    volumeSize: 100
    volumeType: gp3
    labels: {sb-role: storage-a}
    taints: [{key: storage.simplyblock.io/dedicated, value: "true", effect: NoSchedule}]
    updateConfig: {maxUnavailable: 1}
```

`eksctl` checks the file without creating anything when it runs with `--dry-run`, and then creates the cluster. The
creation takes about 20 minutes.

```bash title="Creating the cluster"
eksctl create cluster -f cluster.yaml --dry-run
eksctl create cluster -f cluster.yaml
```

```bash title="Checking the nodes and their roles"
kubectl get nodes -L sb-role
```

Every node is `Ready`, and the `SB-ROLE` column shows two `system`, three `controlplane`, and three `storage-a` nodes.

The local NVMe devices of the storage nodes stay raw. The default Amazon Linux 2023 image neither formats nor mounts
instance storage, and nothing in `cluster.yaml` adds a step that would. The draft lists these devices later, and
discovery formats them before a storage node takes them.

`updateConfig.maxUnavailable: 1` makes an upgrade of a node group replace one node at a time (see
[Upgrading EKS](../operations/cluster/eks-upgrade.md)).

### The Client Node Group

The client node group runs the Ubuntu 24.04 EKS image (see [Node Images](#node-images)). Three values are read from
the AWS account and the new cluster: the image ID, the API server endpoint, and the CA of the cluster.

```bash title="Reading the image ID, the API server endpoint, and the cluster CA"
aws ec2 describe-images --region eu-central-1 --owners 099720109477 --filters "Name=name,Values=ubuntu-eks/k8s_1.33/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*" --query "sort_by(Images,&CreationDate)[-1].ImageId" --output text
aws eks describe-cluster --region eu-central-1 --name simplyblock-eks --query "cluster.endpoint" --output text
aws eks describe-cluster --region eu-central-1 --name simplyblock-eks --query "cluster.certificateAuthority.data" --output text
```

The Kubernetes version in the image name (`k8s_1.33`) is the version of the cluster. The three values replace
`<UBUNTU_EKS_AMI_ID>`, `<API_SERVER_ENDPOINT>`, and `<BASE64_CLUSTER_CA>` below. The cluster DNS IP is the tenth
address of the service CIDR: `10.100.0.10` for the default CIDR `10.100.0.0/16`.

```yaml title="clients.yaml"
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: simplyblock-eks
  region: eu-central-1

managedNodeGroups:
  - name: clients
    ami: <UBUNTU_EKS_AMI_ID>
    amiFamily: Ubuntu2404
    instanceType: c6a.2xlarge
    desiredCapacity: 3
    minSize: 3
    maxSize: 6
    availabilityZones: ["eu-central-1a"]
    labels: {sb-role: client}
    taints: [{key: simplyblock.io/role, value: client, effect: NoSchedule}]
    overrideBootstrapCommand: |
      #!/bin/bash
      export DEBIAN_FRONTEND=noninteractive
      apt-get update
      apt-get install -y linux-modules-extra-$(uname -r)
      echo nvme-tcp > /etc/modules-load.d/nvme-tcp.conf
      modprobe nvme-tcp
      /etc/eks/bootstrap.sh simplyblock-eks \
        --apiserver-endpoint '<API_SERVER_ENDPOINT>' \
        --b64-cluster-ca '<BASE64_CLUSTER_CA>' \
        --dns-cluster-ip 10.100.0.10 \
        --kubelet-extra-args '--node-labels=sb-role=client --register-with-taints=simplyblock.io/role=client:NoSchedule'
```

A node group with a custom image takes its labels and taints from the bootstrap command, which passes them to the
kubelet. The `labels` and `taints` fields only describe the node group to EKS.

```bash title="Adding the client node group"
eksctl create nodegroup -f clients.yaml
```

```bash title="Checking the client nodes"
kubectl get nodes -l sb-role=client
```

## Storage for the Control Plane

FoundationDB, the object store, and Prometheus of the control plane store their data on persistent volumes. On EKS,
they use gp3 volumes of the EBS CSI driver. The operator prepares them itself and only adds what is missing:

| What             | Used when it exists                                                                                   | Installed by the operator when it is missing                                       |
|------------------|-------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| EBS CSI driver   | Any `CSIDriver` named `ebs.csi.aws.com`: the EKS add-on from `cluster.yaml`, or an install of its own | The upstream driver, into `kube-system`                                            |
| gp3 StorageClass | Any StorageClass with the provisioner `ebs.csi.aws.com` and `type: gp3`, whatever its name            | `simplyblock-gp3`, made the default class only if the cluster has no default class |

The operator records the class it chose in the `ControlPlane` resource before the first volume is created, and keeps
it. It never moves the volumes of an existing control plane to another class.

```bash title="Checking the StorageClass of the control plane"
kubectl -n simplyblock get controlplane simplyblock -o jsonpath="{.status.storageClassName}"
```

A class of its own is set with `controlplane.storageclass.name` in the Helm values, and the operator then does not
choose one. If the operator installs the driver itself, the IAM role of the node the driver's controller runs on
needs the AWS managed policy `AmazonEBSCSIDriverPolicy`. In `cluster.yaml`, this is
`iam: {withAddonPolicies: {ebs: true}}` on the system node group. Alternatively, the role in
`controlplane.local.eksRoleARN` carries the policy.

!!! warning "Operator 26.4.0-beta4 and earlier"
    These operator versions neither detect EKS nor create the class. The EBS CSI driver add-on comes from
    `cluster.yaml`, the class is created by hand, and its name is set in the Helm values with
    `controlplane.storageclass.name: ebs-gp3`.

    ```yaml title="ebs-gp3.yaml"
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
      encrypted: "true"
    ```

    ```bash title="Creating the class"
    kubectl apply -f ebs-gp3.yaml
    ```

Host-local storage, such as a hostPath StorageClass, is not suitable for the control plane on EKS. An upgrade of a
managed node group replaces its nodes with new instances, and data on the replaced instance is lost. An EBS volume is
attached to the replacement node in the same availability zone.

## cert-manager

TLS of the control plane is on by default, and its certificates are issued by cert-manager. The Helm chart of the
operator refuses to install while the cluster serves no `cert-manager.io/v1`. An existing cert-manager is used as it
is, whatever namespace or version it was installed with, so the first command checks for one:

```bash title="Checking for cert-manager"
kubectl get crd certificates.cert-manager.io
```

If the CRD is found, cert-manager is installed, and this section is skipped. On `NotFound`, cert-manager is installed:

```bash title="Installing cert-manager"
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager -n cert-manager --create-namespace --set crds.enabled=true --wait
```

```bash title="Checking cert-manager"
kubectl -n cert-manager get pods -o wide
```

Three pods are `Running` on the system node group: `cert-manager`, `cert-manager-cainjector`, and
`cert-manager-webhook`. Without a system node group, they stay `Pending` (see [Node Groups](#node-groups)).

## Keyless S3 Backup Credentials (IRSA)

Backups can reach their S3 bucket with no access key stored in Kubernetes at all, through IAM Roles for Service
Accounts (IRSA): an IAM role is attached to the `simplyblock-storage-node-sa` and `simplyblock-sa` ServiceAccounts, and
EKS's pod-identity webhook injects the credentials every pod running as one of them needs. This replaces the
`credentialsSecretRef` Secret described in
[Backup Credentials Secret](../operations/data-protection/backup-recovery.md#backup-credentials-secret).

### Associating an OIDC Provider

IRSA requires an IAM OIDC provider associated with the cluster. A cluster created from
[`cluster.yaml`](#the-cluster) has one (`iam.withOIDC: true`). For another cluster, it is checked and associated:

```bash title="Checking for, and associating, an OIDC provider"
aws eks describe-cluster --name simplyblock-eks --query "cluster.identity.oidc.issuer" --output text
eksctl utils associate-iam-oidc-provider --cluster simplyblock-eks --approve
```

### Creating the IAM Role

The trust policy scopes the role to this namespace's two accounts specifically, through the OIDC provider's `sub`
claim. Replace `<ACCOUNT_ID>`, `<OIDC_PROVIDER>` (the issuer URL from the previous step, without the `https://`
prefix), and `<NAMESPACE>` (`simplyblock` in the examples throughout these docs). The account ID is the 12-digit ID
of the AWS account the cluster runs in:

```bash title="Reading the account ID"
aws sts get-caller-identity --query Account --output text
```

```json title="Trust policy for the backup role (trust-policy.json)"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/<OIDC_PROVIDER>"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "<OIDC_PROVIDER>:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "<OIDC_PROVIDER>:sub": [
            "system:serviceaccount:<NAMESPACE>:simplyblock-storage-node-sa",
            "system:serviceaccount:<NAMESPACE>:simplyblock-sa"
          ]
        }
      }
    }
  ]
}
```

The permissions policy grants only what the backup bucket needs.

```json title="Permissions policy for the backup role (backup-policy.json)"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::<BUCKET_NAME>"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::<BUCKET_NAME>/*"
    }
  ]
}
```

```bash title="Creating the role and attaching the policy"
aws iam create-role --role-name simplyblock-backup --assume-role-policy-document file://trust-policy.json
aws iam put-role-policy --role-name simplyblock-backup --policy-name simplyblock-backup-s3 --policy-document file://backup-policy.json
```

### Configuring the Operator

The role's ARN goes on the `ControlPlane` singleton, which annotates both ServiceAccounts with it. The Helm chart
exposes this as `controlplane.local.eksRoleARN`, which is set in [`values-eks.yaml`](#helm-values):

```yaml title="The role in values-eks.yaml"
controlplane:
  local:
    eksRoleARN: arn:aws:iam::<ACCOUNT_ID>:role/simplyblock-backup
```

```bash title="Applying the role to an installed operator"
helm upgrade simplyblock-operator simplyblock/simplyblock-operator -n simplyblock -f values-eks.yaml
```

A cluster deployed before the role was set picks it up on the next `helm upgrade`: the operator keeps the annotation
in sync with the value on every reconcile, so no manual annotation is needed. A pod already running when the
annotation changes keeps the credentials it started with, though, since EKS's pod-identity webhook injects them only
when a pod is admitted. Existing control plane and storage node pods are restarted, for example, with
`kubectl rollout restart`, to pick up the role. Then the `StorageCluster`'s backup store names `ProviderChain` instead
of a Secret:

```yaml title="Backup store authenticating through the EKS role"
spec:
  backup:
    endpoint: https://s3.<REGION>.amazonaws.com
    bucket: <BUCKET_NAME>
    region: <REGION>
    credentials:
      source: ProviderChain
```

No `credentialsSecretRef`, and no Secret, is needed anywhere in the namespace.

## Installation

The Simplyblock Operator is installed with Helm and one values file. The file places every simplyblock component on
its node group and lets it tolerate that group's taint. The operator itself and the CSI controller run on the
untainted system node group and need no placement. The general procedure is described in
[Install Simplyblock Operator](k8s-control-plane.md) and [Create a Storage Cluster](k8s-storage-plane.md).

A dedicated network interface for the storage traffic, a second ENI on each storage node, is described in
[Storage Network on Amazon EKS](storage-network/amazon-eks.md).

### Helm Values

```yaml title="values-eks.yaml"
controlplane:
  # Every control plane pod, FoundationDB and Prometheus included, runs on the
  # control plane node group. The add-ons the operator installs for the control
  # plane take the same tolerations.
  nodeSelector:
    create: true
    key: sb-role
    value: controlplane
  tolerations:
    create: true
    list:
      - key: simplyblock.io/role
        operator: Equal
        value: controlplane
        effect: NoSchedule
  local:
    # IAM role for keyless backups to S3 (see "Keyless S3 Backup Credentials").
    # Empty: no role. Backups then use a credentials Secret, or are not set up.
    eksRoleARN: ""

driver:
  # The CSI node plugin runs on every node that mounts volumes, the tainted
  # client nodes included.
  tolerations:
    - operator: Exists

# The initial discovery run, restricted to the storage node group. It writes
# the draft discovered-cluster-a.
discovery:
  enabled: true
  name: cluster-a
  nodeSelector:
    sb-role: storage-a
  tolerations:
    - key: storage.simplyblock.io/dedicated
      operator: Equal
      value: "true"
      effect: NoSchedule
```

With operator 26.4.0-beta4 and earlier, `controlplane.storageclass.name: ebs-gp3` is added under `controlplane` (see
[Storage for the Control Plane](#storage-for-the-control-plane)).

### Installing the Operator

```bash title="Installing the operator with the EKS values"
helm repo add simplyblock https://install.simplyblock.io/helm
helm repo update
helm install simplyblock-operator simplyblock/simplyblock-operator -n simplyblock --create-namespace -f values-eks.yaml
```

```bash title="Following the control plane"
kubectl -n simplyblock get controlplane simplyblock -w
```

The control plane moves through `Installing` and reaches `Available` after a few minutes. Before its first step, the
operator installs what the control plane needs and the cluster lacks (see
[Storage for the Control Plane](#storage-for-the-control-plane)). A control plane that stays in `Installing` names
the reason in its message:

```bash title="Reading why the control plane waits"
kubectl -n simplyblock get controlplane simplyblock -o jsonpath="{.status.message}"
kubectl -n simplyblock get events --field-selector involvedObject.kind=ControlPlane
```

## Referring to the Taint During the Storage Cluster Deployment

A storage cluster is created from a discovery run, which writes a draft `ClusterDeploymentConfig`. The probe pods of
the run are pinned to their nodes, which bypasses the scheduler but not the taints. A run that does not tolerate the
taint of the storage node group therefore finds no workers.

The taint is stated once, in the tolerations of the discovery run. The run carries them into the draft
(`spec.cluster.tolerations`), and from there they reach the storage node DaemonSet of the cluster.

### The First Storage Cluster

The initial discovery run is configured with `discovery.nodeSelector` and `discovery.tolerations` in
`values-eks.yaml`. After the control plane becomes `Available`, the operator starts the run and writes the draft
`discovered-cluster-a`.

```bash title="Following the initial discovery"
kubectl -n simplyblock get operatorops cluster-a -w
kubectl -n simplyblock get clusterdeploymentconfig
```

The run moves through `Inspecting`, `Probing`, and `Writing`, and ends in the phase `Succeeded`.

### Additional Storage Clusters

Every further storage cluster gets its own node group, added to `cluster.yaml` like `storage-a` with its own label,
and its own discovery run, an `OperatorOps` resource with the action `Discover`.

```yaml title="discover-cluster-b.yaml"
apiVersion: storage.simplyblock.io/v1alpha2
kind: OperatorOps
metadata:
  name: discover-cluster-b
  namespace: simplyblock
spec:
  action: Discover
  discover:
    configName: cluster-b
    nodeSelector:
      sb-role: storage-b
    tolerations:
      - key: storage.simplyblock.io/dedicated
        operator: Equal
        value: "true"
        effect: NoSchedule
```

```bash title="Running the discovery"
kubectl apply -f discover-cluster-b.yaml
kubectl -n simplyblock get operatorops discover-cluster-b -w
```

### Reviewing and Approving the Draft

The draft lists the workers of the storage node group, their NVMe instance storage, and the tolerations of the run.

```bash title="Reading the draft and the reasons for its values"
kubectl -n simplyblock get clusterdeploymentconfig discovered-cluster-a -o yaml
kubectl -n simplyblock get events --field-selector involvedObject.kind=OperatorOps,involvedObject.name=cluster-a
```

The following draft is an example for three `m6id.2xlarge` storage nodes. The device addresses, the worker names, and
the sizes differ on every cluster.

```yaml title="Example of a draft written for a tainted storage node group"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ClusterDeploymentConfig
metadata:
  labels:
    storage.simplyblock.io/component: nodeprobe
    storage.simplyblock.io/nodeprobe-run: cluster-a
  name: discovered-cluster-a
  namespace: simplyblock
spec:
  approved: false
  cluster:
    enableDriveFormat: true
    maxSubsystemCount: 30
    name: discovered-cluster-a-cluster
    network:
      podNetwork: true
    stripe:
      dataChunks: 1
      parityChunks: 1
    tolerations:
      - effect: NoSchedule
        key: storage.simplyblock.io/dedicated
        operator: Equal
        value: "true"
    vcpuCount: 5
  environment: EKS
  hostOS:
    distro: amzn
    family: RedHat
  nodeSets:
    - groups:
        - devices:
            nvme:
              - 0000:00:1f.0
          mgmtInterface: ens5
          name: group-1-nvme-1x474G
          workers:
            - ip-192-168-20-206.eu-central-1.compute.internal
            - ip-192-168-4-223.eu-central-1.compute.internal
            - ip-192-168-8-222.eu-central-1.compute.internal
      name: discovered
```

The values to check before the approval:

| Field                      | Check                                                                                                                                                                          |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `spec.cluster.tolerations` | The taint of the storage node group. Without it, the storage node pods are not scheduled.                                                                                      |
| `workers`                  | Exactly the nodes of the storage node group.                                                                                                                                   |
| `devices`                  | The NVMe instance storage. The boot disk of an EKS node is an EBS volume and does not appear.                                                                                  |
| `spec.cluster.vcpuCount`   | See [vCPU Count](k8s-storage-plane.md#vcpu-count). It cannot be changed after the approval.                                                                                    |
| `spec.cluster.network`     | `podNetwork` with one ENI per node. A second ENI for storage traffic is set up as in [Storage Network on Amazon EKS](storage-network/amazon-eks.md). Fixed after the approval. |

The events of the run explain each drafted value, one event per value.

A value is corrected in the draft before the approval, for example, the vCPU count. The change is written to a file,
which works the same in bash and in PowerShell:

```yaml title="draft-vcpu.yaml"
spec:
  cluster:
    vcpuCount: 6
```

```bash title="Correcting a value of the draft"
kubectl -n simplyblock patch clusterdeploymentconfig discovered-cluster-a --type=merge --patch-file draft-vcpu.yaml
```

After the review, the draft is approved, and the operator creates the storage cluster.

```yaml title="draft-approve.yaml"
spec:
  approved: true
```

```bash title="Approving the draft"
kubectl -n simplyblock patch clusterdeploymentconfig discovered-cluster-a --type=merge --patch-file draft-approve.yaml
```

```bash title="Following the storage cluster"
kubectl -n simplyblock get storagecluster -w
kubectl -n simplyblock get storagenodes -o wide
```

The review, the approval, and the verification of the cluster are described in detail in
[Create a Storage Cluster](k8s-storage-plane.md#review-the-draft).

## Verifying the Placement

```bash title="Checking where the simplyblock pods run"
kubectl get pods -A -o wide
kubectl get nodes -L sb-role
```

The pods are expected on these node groups:

| Pods                                                                            | Node group    |
|---------------------------------------------------------------------------------|---------------|
| Simplyblock Operator, CSI controller, cert-manager, EBS CSI controller, CoreDNS | System        |
| FoundationDB, management API, Prometheus, object store                          | Control plane |
| Storage node (SPDK) pods                                                        | Storage       |
| CSI node plugin                                                                 | Every node    |

A pod in `Pending` names the reason in its events, usually a taint it does not tolerate or a missing node group:

```bash title="Reading why a pod is pending"
kubectl -n simplyblock describe pod <POD_NAME>
```

On the client nodes, the volumes are attached with native NVMe multipathing. How to check it is described in
[Node Images](#node-images).
