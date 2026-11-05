---
title: "Amazon EKS"
description: "Attach a dedicated data ENI to simplyblock storage nodes on Amazon EKS with Cilium ENI mode and Multus, in the node subnet or a dedicated subnet."
weight: 40060
---

On Amazon EKS, the storage traffic can run on a second elastic network interface (ENI) of each storage node, which
Multus moves into the SPDK pod. The storage traffic then has an interface, an address, and a security group of its own.
This is option 3 of [Storage Network](index.md), which also compares it with the other options.

The data ENI sits either in the node subnet (layout A) or in a subnet of its own (layout B). The layout decides which
routing workarounds are needed, so it is chosen first (see [Choosing a Layout](#choosing-a-layout)).

## Choosing a Layout

| Layout                                            | Data ENI subnet                                            | Workaround in the SPDK pod                                                  | Workaround on the host                                                                            | Trade-off                                                               |
|---------------------------------------------------|------------------------------------------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------|
| [A: Node subnet](#layout-a-node-subnet)           | The node subnet, shared with the primary ENI               | [`sbr`](#fix-in-the-spdk-pod-source-based-routing)                          | [Pin the node subnet to the primary ENI](#fix-on-the-host-pin-the-node-subnet-to-the-primary-eni) | No address planning, no network-level isolation                         |
| [B: Dedicated subnet](#layout-b-dedicated-subnet) | A subnet holding only data ENIs, one per availability zone | [`sbr`, with a route to the initiators' subnet](#layout-b-dedicated-subnet) | None                                                                                              | A CIDR per availability zone, storage traffic isolated at network level |

Everything except the routing is the same in both layouts. The [Routing](#routing) section describes each layout.

## Overview

1. [Install Cilium in ENI mode](#cilium-in-eni-mode), without the AWS VPC CNI and kube-proxy add-ons.
2. Install Multus and the `host-device`, `static`, and `sbr` CNI plugins, as listed in
   [Requirements of Every Attached Network](index.md#requirements-of-every-attached-network). The EKS Amazon
   Linux 2023 image ships none of the plugins.
3. [Create the data ENI](#the-data-eni) on every storage node at boot.
4. [Set up the security groups](#security-groups) of the data ENI.
5. [Fix the routing](#routing) in the SPDK pod and on the host.
6. [Deploy the storage cluster](#deploying-the-storage-cluster) with the data network.

## Cilium in ENI Mode

The cluster runs Cilium as the primary CNI in _ENI mode_, with native routing and kube-proxy replacement. The cluster is
created with `bootstrap_self_managed_addons = false`, and Cilium is installed before the nodes join.

| Setting                             | Value                                  | Reason                                                                                             |
|-------------------------------------|----------------------------------------|----------------------------------------------------------------------------------------------------|
| `eni.enabled`, `ipam.mode`          | `true`, `eni`                          | Pods get VPC addresses from ENIs the Cilium operator attaches to the node.                         |
| `routingMode`                       | `native`                               | Pod addresses are routed by the VPC. No encapsulation is needed.                                   |
| `ipv4NativeRoutingCIDR`             | The VPC CIDR                           | Traffic inside the VPC is not masqueraded.                                                         |
| `kubeProxyReplacement`              | `true`                                 | EKS is created without the AWS kube-proxy add-on.                                                  |
| `cni.exclusive`                     | `false`                                | Cilium leaves other CNI configurations in place. Multus chains secondary attachments through them. |
| `eni.nodeSpec.excludeInterfaceTags` | `sb-data-eni=true`                     | The data ENI is never used for pod addresses. This setting needs Cilium 1.19 or later.             |
| `eni.nodeSpec.subnetTags`           | A tag that selects the private subnets | Pod ENIs are created in the subnets meant for pods and not in a small data subnet.                 |

??? info "Why ENI mode, and why no VPC CNI and no kube-proxy add-on"
    The control plane of EKS runs outside the VPC and calls the admission webhooks of the operator, cert-manager, and
    other components on their pod addresses. With an overlay datapath (VXLAN or Geneve), pod addresses exist only
    between the nodes, and the managed control plane cannot reach them. Webhook calls time out and installs fail. In ENI
    mode, every pod has a VPC address that the control plane routes to directly.

    Cilium is installed before the nodes join, because a node created before a CNI exists never becomes ready and the
    managed node group fails its health check. CoreDNS follows the node group.

## The Data ENI

Each storage node needs a second ENI at device index 1. Each node creates and attaches its own ENI in a boot script,
because the Auto Scaling group ignores a per-interface subnet in the launch template.

| Requirement                                         | Reason                                                                                            |
|-----------------------------------------------------|---------------------------------------------------------------------------------------------------|
| Created and attached at boot, before the node joins | The interface has to exist before the operator reads its address.                                 |
| Tag `sb-data-eni=true`                              | Cilium's exclusion tag. Without it, the Cilium operator takes the ENI for pod addresses.          |
| `DeleteOnTermination=true`                          | A replaced node does not leak its ENI.                                                            |
| Its own security group                              | The data ENI is protected separately from the pod ENIs of the node.                               |
| Idempotent boot step                                | The same script runs on every boot and attaches nothing when an ENI is already at device index 1. |

The node role needs `ec2:DescribeInstances`, `ec2:DescribeNetworkInterfaces`, `ec2:CreateNetworkInterface`,
`ec2:AttachNetworkInterface`, `ec2:ModifyNetworkInterfaceAttribute`, and `ec2:CreateTags` for this step. The Cilium
operator needs its own set of ENI permissions in ENI mode.

```bash title="Boot step that creates and attaches the data ENI (user data of the storage node group)"
#!/bin/bash
set -euo pipefail

token=$(curl -s -X PUT http://169.254.169.254/latest/api/token -H 'X-aws-ec2-metadata-token-ttl-seconds: 300')
imds() { curl -s -H "X-aws-ec2-metadata-token: $token" "http://169.254.169.254/latest/meta-data/$1"; }
instance_id=$(imds instance-id)
export AWS_DEFAULT_REGION=<REGION>

attached=$(aws ec2 describe-instances --instance-ids "$instance_id" \
  --query 'Reservations[0].Instances[0].NetworkInterfaces[?Attachment.DeviceIndex==`1`].NetworkInterfaceId' --output text)
if [ -n "$attached" ]; then
  exit 0
fi

eni_id=$(aws ec2 create-network-interface \
  --subnet-id <DATA_ENI_SUBNET_ID> \
  --groups <DATA_SECURITY_GROUP_ID> \
  --tag-specifications "ResourceType=network-interface,Tags=[{Key=sb-data-eni,Value=true}]" \
  --query 'NetworkInterface.NetworkInterfaceId' --output text)

attachment_id=$(aws ec2 attach-network-interface \
  --network-interface-id "$eni_id" --instance-id "$instance_id" --device-index 1 \
  --query 'AttachmentId' --output text)

aws ec2 modify-network-interface-attribute --network-interface-id "$eni_id" \
  --attachment "AttachmentId=$attachment_id,DeleteOnTermination=true"
```

`<DATA_ENI_SUBNET_ID>` is the node subnet in layout A, or the data subnet in layout B.

??? info "Why `host-device` and not `macvlan` or `ipvlan`"
    The plugin moves the whole ENI into the pod. The SPDK process then has an interface of its own, its queues and
    interrupts are not shared with the host or with other pods, and its address is the address AWS assigned to the ENI.
    `macvlan` and `ipvlan` create a virtual interface on the host's ENI instead. The VPC delivers only addresses and MAC
    addresses it assigned to an ENI, so these plugins need extra steps on AWS (secondary addresses registered on the
    ENI, and, for `macvlan`, MAC addresses the VPC does not know). They are not verified on EKS.

Storage nodes may run Amazon Linux 2023 (see [Amazon EKS](../eks.md#node-images)). An example instance type is
`i3en.2xlarge`, with local NVMe instance storage and 8 vCPUs. The storage node needs at least 6 vCPUs.

## Security Groups

The initiators of a volume are the worker hosts, which open NVMe/TCP connections to the SPDK address on the data ENI.
The storage nodes also talk to each other on the data network.

| Rule on the data security group | Source                  | Reason                                                  |
|---------------------------------|-------------------------|---------------------------------------------------------|
| Ingress, all traffic            | The data security group | Replication and mesh traffic between storage nodes.     |
| Ingress, all traffic            | The node security group | The host of every worker is an NVMe/TCP initiator.      |
| Egress, all traffic             | Anywhere                | Replies and outgoing connections between storage nodes. |

## Routing

The routing workarounds depend on the layout.

### Layout A: Node Subnet

In layout A, the host and the SPDK pod each have two interfaces in the node subnet. Two fixes keep every packet on the
interface that owns its source address: one in the definition and one in the user data of the node.

??? info "Why two interfaces in one subnet break on AWS"
    A Linux host or pod that has two interfaces in the same subnet has two routes for that subnet. The kernel chooses one
    for each destination and, without further rules, sends the packet out of that interface with that interface's
    address as source.

    Most networks tolerate this: a switch passes the packet on anyway. A VPC does not. Every ENI may only send packets
    whose source is one of its own addresses (the source and destination check), and the VPC drops everything else. A
    reply that leaves the wrong interface disappears. Security groups play no part and cannot fix this.

```plain title="Layout A, one worker"
VPC 10.10.0.0/16, node subnet 10.10.0.0/20

 worker
 ├─ ens5  10.10.2.132/20   primary ENI, Cilium and the host      (node security group)
 ├─ (pod ENIs of Cilium)   pod addresses 10.10.x.x               (node security group)
 └─ ens6  10.10.15.99/20   data ENI, moved into the SPDK pod     (data security group)
                           pod: data0 = 10.10.15.99, eth0 = pod address
```

#### Fix in the SPDK Pod: Source-Based Routing

The `sbr` plugin follows `host-device` in the definition. It moves the data interface's routes into a table of their
own, which is selected only for packets whose source is the data address. The workaround is described in general in
[Source-Based Routing](index.md#source-based-routing).

```yaml title="NetworkAttachmentDefinition for layout A (fabric-data)"
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: fabric-data
  namespace: simplyblock
spec:
  config: |
    {
      "cniVersion": "0.3.1",
      "name": "fabric-data",
      "plugins": [
        {
          "type": "host-device",
          "device": "ens6",
          "capabilities": { "ips": true },
          "ipam": { "type": "static" }
        },
        { "type": "sbr" }
      ]
    }
```

The definition names no routes and no per-worker addresses. The operator takes the plugin's first entry when it reads
the interface, so `device` is found in a chained definition.

??? info "Without `sbr`: the SPDK pod is unreachable"
    **Symptom.** The SPDK pod starts, but nothing reaches it. A ping from a pod on another worker to the SPDK pod's
    `eth0` address fails, and the control plane's calls to the SPDK proxy end in connection timeouts. The node-add never
    completes.

    **Cause.** The connected route for `10.10.0.0/20` on `data0` is more specific than the default route on `eth0`.
    Every packet for an address in the node subnet leaves through `data0`, including replies to requests that arrived on
    `eth0`, with the pod address of `eth0` as source. The VPC drops them.

    ```plain title="Routing table inside the SPDK pod without sbr"
    default via 10.10.1.110 dev eth0
    10.10.0.0/20 dev data0                <- connected route of the data ENI
    ```

    With `sbr`, a packet sourced from the data address uses table 100 and leaves through `data0`. Every other packet
    uses the main table and leaves through `eth0`.

    ```plain title="Routing inside the SPDK pod with sbr"
    rule 32765:  from 10.10.8.37 lookup 100
    main:        default via 10.10.1.110 dev eth0
    table 100:   10.10.0.0/20 dev data0
    ```

#### Fix on the Host: Pin the Node Subnet to the Primary ENI

The host keeps a route for the node subnet through the primary interface, with a lower metric than any route of the
data ENI. A drop-in for `systemd-networkd` in the user data, next to the step that creates the data ENI, makes the route
persistent across boots, lease renewals, and reconfigurations of the interface.

```bash title="User data step that pins the node subnet to the primary ENI (Amazon Linux 2023 EKS image)"
mac=$(imds mac)
subnet_cidr=$(imds "network/interfaces/macs/$mac/subnet-ipv4-cidr-block")

mkdir -p /etc/systemd/network/70-eks-ens5.network.d
printf '[Route]\nDestination=%s\nScope=link\nMetric=100\n' "$subnet_cidr" \
  > /etc/systemd/network/70-eks-ens5.network.d/10-subnet-route.conf
```

The step has to run before the node joins the cluster, because the first address read needs a working host network.

!!! warning "Image-specific names"
    `ens5` and `70-eks-ens5.network` are the names the Amazon Linux 2023 EKS image generates for the primary ENI.
    Another image or operating system names the interface and its configuration differently. The step has to be adapted
    to the image, preferably by matching the primary interface by its MAC address and not by its name.

??? info "Without the host route: DNS and the CSI link fail on the worker"
    **Symptom.** Before the first node is added, or after a storage node pod restarts, pods on the worker cannot
    resolve cluster DNS, and the CSI node plugin cannot link to the operator (`dial tcp: lookup ... i/o timeout`). The
    storage node stays in `Pending` with the event `NetworkHostCheckUnavailable`.

    **Cause.** While the ENI is on the host (before the SPDK pod takes it, and after it is returned), the host's only
    route for the node subnet points to `ens6`. Packets from the host leave through the data ENI with the data address
    as source, and the destination's security group does not admit the data security group.

    ```plain title="Host routes with both ENIs in one subnet"
    default via 10.10.0.1 dev ens5   metric 512
    default via 10.10.0.1 dev ens6   metric 513
    10.10.0.0/20 dev ens6 proto kernel  metric 513     <- the only route for the subnet
    ```

### Layout B: Dedicated Subnet

In layout B, the data ENI sits in a subnet that holds only data ENIs, one per availability zone, with a route table,
network ACL, and security group of its own. The host has no second interface in the node subnet, so the host fix of
layout A is not needed.

The SPDK pod's data interface is the only one in the data subnet, but the initiators sit in the node subnet. Without a
route, the SPDK pod answers them through `eth0`. The definition therefore carries a route to the node subnet through
the gateway of the data subnet, which is the first address of that subnet in a VPC. The `sbr` plugin then places the
route in the data interface's own table.

```yaml title="NetworkAttachmentDefinition for layout B (fabric-data)"
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: fabric-data
  namespace: simplyblock
spec:
  config: |
    {
      "cniVersion": "0.3.1",
      "name": "fabric-data",
      "plugins": [
        {
          "type": "host-device",
          "device": "ens6",
          "capabilities": { "ips": true },
          "ipam": {
            "type": "static",
            "routes": [ { "dst": "10.10.0.0/20", "gw": "10.10.16.1" } ]
          }
        },
        { "type": "sbr" }
      ]
    }
```

In the example, the node subnet is `10.10.0.0/20` and the data subnet `10.10.16.0/24`. Each availability zone has a
data subnet and a gateway of its own, so a definition per zone, or a route per node subnet, is needed where the zones
differ.

Neither layout adds bandwidth: the network bandwidth of an EC2 instance is a limit of the instance as a whole, and a
single TCP flow is limited by AWS as well, so the number of NVMe/TCP connections matters more than the choice of ENI.

## Deploying the Storage Cluster

1. Install cert-manager and the Simplyblock Operator (see [Install Simplyblock Operator](../k8s-control-plane.md)). The
   chart enables the CSI link between the operator and the CSI node plugins by default. The address read and the
   reachability check run over it, so the CSI node plugin has to run on every storage worker.
2. Create the definition `fabric-data` in the namespace of the operator.
3. Edit the discovered draft: replace its `network` with the data network, and remove `dataInterfaces` from every
   group. Discovery finds the data ENI on the workers and drafts `spdkOnHostNetwork: true` with `dataInterfaces`, which
   the schema allows only on the host network.
4. Check the network of the draft, and approve the draft.

```bash title="Editing the draft"
kubectl -n simplyblock edit clusterdeploymentconfig discovered-initial-discovery
```

```yaml title="Example of the edited draft (excerpt)"
spec:
  cluster:
    network:
      podNetwork: true
      data:
        - networkAttachmentRef:
            name: fabric-data
  nodeSets:
    - name: discovered
      groups:
        - name: group-1
          mgmtInterface: ens5
```

```bash title="Checking the network of the draft before approval"
kubectl -n simplyblock get clusterdeploymentconfig discovered-initial-discovery \
    -o jsonpath='{.spec.cluster.network}{"\n"}'
```

The network declares no `addressPool`, so each node adopts the address the VPC assigned to its data ENI. The operator
reads that address through the CSI node plugin before the SPDK pod takes the interface, and reports the node `Online`
only when every worker reaches it.

## Verification

```bash title="Checking the storage nodes"
kubectl -n simplyblock get storagenode \
    -o custom-columns=NODE:.spec.workerNode,PHASE:.status.phase,NET:.status.network
```

Every node reaches `Online` with a network entry in phase `Attached` and `hostReachable: true`. The `assigned` address
is the address of the data ENI on the host. A volume is then written and verified from a pod on the worker that serves
it and from pods on other workers, each pinned with a `nodeSelector` on `kubernetes.io/hostname`, because a pod that
sets `spec.nodeName` bypasses the scheduler and never binds a `WaitForFirstConsumer` claim.

## Troubleshooting

| Symptom                                                                                          | Cause                                                                                                 | Solution                                                                                                                                              |
|--------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| `NetworkHostCheckUnavailable`, CSI node plugin log `lookup simplyblock-csi-link ... i/o timeout` | The host reaches the cluster network through the data ENI (layout A)                                  | Add the [host route](#fix-on-the-host-pin-the-node-subnet-to-the-primary-eni).                                                                        |
| Node-add stays in progress, task log shows `ConnectTimeoutError` to the SPDK proxy name          | The SPDK pod answers through the data ENI (layout A), or lacks the route to the initiators (layout B) | Chain [`sbr`](#fix-in-the-spdk-pod-source-based-routing) in the definition, or add the [route to the initiators' subnet](#layout-b-dedicated-subnet). |
| `NetworkInterfaceNoAddress`                                                                      | The interface the definition names has no usable IPv4 address on the host                             | Check the interface name in the definition and that the ENI is attached with an address.                                                              |
| `NetworkAttachmentFailed`, "names no device or PCI address"                                      | The definition has no `device`, `master`, or `pciBusID`                                               | Add the interface to the first plugin of the definition.                                                                                              |
| `DataNetworkHostUnreachable` naming a worker                                                     | No route or security group rule between that worker and the data ENI, or no return path               | Check the data security group (node security group admitted), and the routes of the layout.                                                           |
| A claim stays `Pending` with `WaitForFirstConsumer`                                              | The pod sets `spec.nodeName`                                                                          | Pin with a `nodeSelector`.                                                                                                                            |
