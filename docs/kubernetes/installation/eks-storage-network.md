---
title: "Storage Network on Amazon EKS"
description: "Attach a dedicated data ENI to simplyblock storage nodes on Amazon EKS with Cilium ENI mode and Multus, in the node subnet or a dedicated subnet."
weight: 40060
---

A simplyblock storage node serves NVMe over TCP from the SPDK pod. By default, the pod runs on the host network and
listens on an address of the worker's own interface. The _storage network_ feature replaces this with a dedicated
network interface that is moved into the SPDK pod, so that the storage traffic has an interface, an address, and a
security group of its own.

On Amazon EKS, the dedicated interface is a second elastic network interface (ENI) of the instance. This page describes
the cluster setup the feature requires on EKS, and the two ways to place the second ENI: in the same subnet as the
primary ENI of the node, or in a subnet of its own. Each layout has its own routing problems and its own solution. The
reasons are given with the steps, because the solutions follow from how Linux and the VPC route a packet.

!!! info "Scope and verification status"
    The setup in [Cluster Setup](#cluster-setup) and the layout in
    [Layout A: Same Subnet](#layout-a-same-subnet) were built and tested end to end on Amazon EKS 1.33 with Cilium
    1.19, Multus 4.3, and three `i3en.2xlarge` storage nodes. Volumes were created and verified with `fio` from a pod on
    the worker that serves the volume and from pods on other workers.

    [Layout B: Dedicated Subnet](#layout-b-dedicated-subnet) is derived from the same routing rules and has not been
    run end to end. The steps that are not verified are marked as such.

## How the Attachment Works

The storage network is declared on the storage cluster as a reference to a `NetworkAttachmentDefinition`. The definition
is owned by the administrator and names the CNI plugin and the interface that moves into the pod.

```yaml title="Excerpt of a ClusterDeploymentConfig with a data network"
spec:
  cluster:
    network:
      data:
        - name: fabric
          attachment:
            networkAttachmentRef:
              name: fabric-data
```

For every storage node, the operator then proceeds as follows:

1. The operator asks the CSI node plugin of the worker for the addresses of the interface the definition names (for
   example, `ens6`). The plugin runs on the host network, so it sees the interface before the SPDK pod takes it. The
   first IPv4 address becomes the address of the node on that network.
2. The operator hands the address to the control plane, which creates the SPDK pod. Multus moves the interface into the
   pod with the `host-device` plugin and assigns the address with the `static` IPAM plugin.
3. Once the control plane reports the node online, the operator asks the CSI node plugin of every worker to open a
   TCP connection to the SPDK listener at that address. The network is recorded as `Attached`, and the node is
   reported `Online`, only when every worker reaches it.

The operator does not write the definition, the routes, or the node's network configuration. It reads the address of
the interface and verifies the result. The rest of this page covers what the cluster, the nodes, and the definition
have to provide.

Because the address is the address the interface already holds in the VPC, no address has to be typed per node, and the
VPC, which only delivers the addresses assigned to an ENI, delivers the traffic.

!!! note "No management interface"
    A group that uses `spec.cluster.network` names no `mgmtInterface` and no `dataInterfaces`. Discovery proposes
    `mgmtInterface` from the host. It is removed from the draft before approval, and the schema refuses the
    combination.

## Cluster Setup

### Cilium in ENI Mode

The cluster runs Cilium as the primary CNI in _ENI mode_, with native routing and kube-proxy replacement.

| Setting                             | Value                                  | Reason                                                                                             |
|-------------------------------------|----------------------------------------|----------------------------------------------------------------------------------------------------|
| `eni.enabled`, `ipam.mode`          | `true`, `eni`                          | Pods get VPC addresses from ENIs the Cilium operator attaches to the node.                         |
| `routingMode`                       | `native`                               | Pod addresses are routed by the VPC. No encapsulation is needed.                                   |
| `ipv4NativeRoutingCIDR`             | The VPC CIDR                           | Traffic inside the VPC is not masqueraded.                                                         |
| `kubeProxyReplacement`              | `true`                                 | EKS is created without the AWS kube-proxy add-on (see below).                                      |
| `cni.exclusive`                     | `false`                                | Cilium leaves other CNI configurations in place. Multus chains secondary attachments through them. |
| `eni.nodeSpec.excludeInterfaceTags` | `sb-data-eni=true`                     | The data ENI is never used for pod addresses. This setting needs Cilium 1.19 or later.             |
| `eni.nodeSpec.subnetTags`           | A tag that selects the private subnets | Pod ENIs are created in the subnets meant for pods and not in a small data subnet.                 |

**Why ENI mode.** The control plane of EKS runs outside the VPC and calls the admission webhooks of the operator,
cert-manager, and other components on their pod addresses. With an overlay datapath (VXLAN or Geneve), pod addresses
exist only between the nodes, and the managed control plane cannot reach them. Webhook calls time out and installs
fail. In ENI mode, every pod has a VPC address that the control plane routes to directly.

**Why not chain Cilium on top of the AWS VPC CNI.** The VPC CNI would own the ENIs, including the data ENI, unless
every ENI is tagged `node.k8s.amazonaws.com/no_manage=true`. Cilium in ENI mode has an exclusion tag of its own, and
only one component manages ENIs. Both options keep pod addresses routable. The ENI mode of Cilium was chosen and tested.

**Why no VPC CNI and no kube-proxy add-on.** The cluster is created with `bootstrap_self_managed_addons = false`. Cilium
is installed before the nodes join, because a node created before a CNI exists never becomes ready and the managed node
group fails its health check. CoreDNS follows the node group.

### Multus and the CNI Plugins

Multus attaches the secondary interface to the SPDK pod. Two parts are installed:

- **Multus**, in thick-plugin mode, as the `kube-multus-ds` DaemonSet.
- **The reference CNI plugins** (`host-device`, `static`, and `sbr`), installed onto every node by a DaemonSet that
  downloads the plugin release into `/opt/cni/bin`. The EKS Amazon Linux 2023 image ships none of them, and Multus
  delegates to these binaries.

```yaml title="cni-plugins.yaml (DaemonSet that installs the plugins)"
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: cni-plugins
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: cni-plugins
  template:
    metadata:
      labels:
        app: cni-plugins
    spec:
      tolerations:
        - operator: Exists
      initContainers:
        - name: install
          image: alpine:3.22
          command:
            - sh
            - -c
            - |
              set -e
              wget -qO- https://github.com/containernetworking/plugins/releases/download/v1.9.1/cni-plugins-linux-amd64-v1.9.1.tgz \
                | tar -xz -C /host/opt/cni/bin ./host-device ./static ./sbr
          volumeMounts:
            - name: cni-bin
              mountPath: /host/opt/cni/bin
      containers:
        - name: pause
          image: registry.k8s.io/pause:3.10
      volumes:
        - name: cni-bin
          hostPath:
            path: /opt/cni/bin
```

The plugin version and the download location are examples. A production cluster pins a version and serves the archive
from an internal location.

**Why `host-device`.** The plugin moves the whole ENI into the pod. The SPDK process then has an interface of its own,
its queues and interrupts are not shared with the host or with other pods, and its address is the address AWS assigned to
the ENI. `macvlan` and `ipvlan` create a virtual interface on the host's ENI instead. The VPC delivers only addresses and
MAC addresses it assigned to an ENI, so these plugins need extra steps on AWS (secondary addresses registered on the
ENI, and, for `macvlan`, MAC addresses the VPC does not know). They are not verified on EKS.

### The Second ENI

Each storage node needs a second ENI at device index 1. The ENI is not declared in the launch template, because the Auto
Scaling group ignores a per-interface subnet in the template. Each node creates and attaches its own ENI in a boot
script, with the permissions of the node role.

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

`<DATA_ENI_SUBNET_ID>` is the subnet of the chosen layout, which is the subject of the next sections.

### Security Groups

The initiators of a volume are the worker hosts, which open NVMe/TCP connections to the SPDK address on the data ENI.
The data ENI therefore admits the node security group, and the members of the data security group admit each other (the
storage nodes talk to each other on the data network).

| Rule on the data security group | Source                  | Reason                                                  |
|---------------------------------|-------------------------|---------------------------------------------------------|
| Ingress, all traffic            | The data security group | Replication and mesh traffic between storage nodes.     |
| Ingress, all traffic            | The node security group | The host of every worker is an NVMe/TCP initiator.      |
| Egress, all traffic             | Anywhere                | Replies and outgoing connections between storage nodes. |

A security group admits traffic by the source address of the packet. In addition, the VPC applies a source and
destination check: a packet that leaves an ENI with an address that belongs to another ENI is dropped, and no security
group rule changes that. This check is the source of the routing problems described next.

### Node Image and Size

Storage nodes may run Amazon Linux 2023 (see [Amazon EKS](../../deployment-preparation/amazon-eks.md#node-images)). The
tested instance type is `i3en.2xlarge` with local NVMe instance storage and 8 vCPUs. The storage node needs at least
6 vCPUs.

### The StorageCluster

The chart enables the CSI link between the operator and the CSI node plugins by default. The address read and the
reachability check run over it, so the CSI node plugin has to run on every storage worker and be linked. A worker whose
plugin is not linked holds the node in `Pending` with the event `NetworkHostCheckUnavailable`.

## Why the Layout Matters

A Linux host or pod that has two interfaces in the same subnet has two routes for that subnet. The kernel chooses one for
each destination and, without further rules, sends the packet out of that interface with that interface's address as
source.

Most networks tolerate this: a switch passes the packet on anyway. A VPC does not. Every ENI may only send packets whose
source is one of its own addresses (the source and destination check), and the VPC drops everything else. A reply
that leaves the wrong interface disappears.

The storage layout therefore decides which problems exist:

- **Layout A, same subnet:** both ENIs of the node share one prefix. Two routing problems follow, one on the host and
  one in the SPDK pod. Both are solved with source-based routing, and the setup needs no route to the initiators.
- **Layout B, dedicated subnet:** the data ENI has a prefix of its own. The two problems of layout A do not occur. In
  return, the pod needs a route to the initiators.

| Property                     | Layout A: same subnet                                                                | Layout B: dedicated subnet                              |
|------------------------------|--------------------------------------------------------------------------------------|---------------------------------------------------------|
| Address planning             | None. The data ENI takes an address of the node subnet.                              | A data CIDR per availability zone.                      |
| Isolation of storage traffic | Security group only                                                                  | Own route table, network ACL, and security group        |
| Host workaround              | Pinned route to the node subnet through the primary ENI                              | None                                                    |
| Pod workaround               | `sbr` in the definition                                                              | `sbr`, plus a route to the initiators' subnet           |
| Route list per worker        | None                                                                                 | None, when the route covers the initiators' subnet      |
| Status                       | Tested end to end                                                                    | Derived, not run end to end                             |
| Choose when                  | Simple setups and tests, or when no address space is available for a separate subnet | Storage traffic has to be isolated at the network level |

## Layout A: Same Subnet

The primary ENI (`ens5`) and the data ENI (`ens6`) are in the same private subnet, here `10.10.0.0/20`.

```plain title="Layout A, one worker"
VPC 10.10.0.0/16, node subnet 10.10.0.0/20

 worker
 ├─ ens5  10.10.2.132/20   primary ENI, Cilium and the host      (node security group)
 ├─ (pod ENIs of Cilium)   pod addresses 10.10.x.x               (node security group)
 └─ ens6  10.10.15.99/20   data ENI, moved into the SPDK pod     (data security group)
                           pod: data0 = 10.10.15.99, eth0 = pod address
```

The layout needs no address plan and no route to the initiators: the initiators are the workers in the same subnet,
which reach the data address on-link through the VPC. Two workarounds keep the routing correct.

### Problem A1: Routing in the SPDK Pod

**Symptom.** The SPDK pod starts, but nothing reaches it. A ping from a pod on another worker to the SPDK pod's `eth0`
address fails, and the control plane's calls to the SPDK proxy end in connection timeouts. The node-add never completes.

**Cause.** After `host-device` has moved the ENI into the pod, the pod has two interfaces and one main routing table:

```plain title="Routing table inside the SPDK pod without a workaround"
eth0   10.10.14.194/32   Cilium, default route via cilium_host
data0  10.10.8.37/20     the data ENI

default via 10.10.1.110 dev eth0
10.10.0.0/20 dev data0                <- connected route of the data ENI
```

The connected route for `10.10.0.0/20` on `data0` is more specific than the default route on `eth0`. Every packet for an
address in the node subnet, which includes every other pod and every host, leaves through `data0`. A reply to a request
that arrived on `eth0` is therefore sent out of the data ENI with the pod address of `eth0` as source. That address does
not belong to the data ENI, and the VPC drops the packet. Security groups play no part and cannot fix this.

**Solution.** Source-based routing for the data interface. The `sbr` plugin follows `host-device` in the definition and
moves the interface's routes into a table of their own, which is selected only for packets whose source is the data
address.

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

The result inside the pod:

```plain title="Routing inside the SPDK pod with sbr"
rule 32765:  from 10.10.8.37 lookup 100
main:        default via 10.10.1.110 dev eth0
table 100:   10.10.0.0/20 dev data0
```

- A packet sourced from the data address uses table 100 and leaves through `data0`, on-link. This is the path of every
  reply to an NVMe/TCP initiator.
- Every other packet, including all pod-network traffic, uses the main table and leaves through `eth0`.

The definition names no routes and no per-worker addresses. The operator takes the plugin's first entry when it reads the
interface, so `device` is found in a chained definition.

**Check.**

```bash title="Inspecting the routing of the SPDK pod"
kubectl -n simplyblock debug <SPDK_POD> -it --image=nicolaka/netshoot --target=spdk-container -- sh -c 'ip route; ip rule'
```

The main table has only the `eth0` route, and a rule `from <data address> lookup <table>` exists.

### Problem A2: Routing on the Worker Host

**Symptom.** Before the first node is added, or after a storage node pod restarts, pods on the worker cannot resolve
cluster DNS, and the CSI node plugin cannot link to the operator (`dial tcp: lookup ... i/o timeout`). The storage
node stays in `Pending` with the event `NetworkHostCheckUnavailable`.

**Cause.** While the ENI is on the host, which is before the SPDK pod takes it and after it has been returned, the host
has both `ens5` and `ens6` in `10.10.0.0/20`. The generated network configuration gives each interface its own routes:

```plain title="Host routes with both ENIs in one subnet"
default via 10.10.0.1 dev ens5   metric 512
default via 10.10.0.1 dev ens6   metric 513
10.10.0.0/20 dev ens6 proto kernel  metric 513     <- the only route for the subnet
```

The host's route for the node subnet points to `ens6`, so a packet from the host to a pod or another worker leaves
through the data ENI with the data address as source. The destination ENI's security group does not admit the data
security group, and the packet is dropped.

The problem matters at two moments: while the operator reads the address of the interface through the CSI node plugin,
which needs the host network to work, and every time `host-device` returns the interface to the host (a pod restart
or removal). While the ENI is inside the pod, the host does not use it.

**Solution.** The host keeps a route for the node subnet through the primary interface with a lower metric than any
route of the data ENI. The route is node configuration and belongs in the user data of the node, next to the step that
creates the second ENI. A _drop-in_ for `systemd-networkd` makes the route persistent: `systemd-networkd` applies it
again at every boot, every lease renewal, and every reconfiguration of the interface.

```bash title="User data step that pins the node subnet to the primary ENI (Amazon Linux 2023 EKS image)"
mac=$(imds mac)
subnet_cidr=$(imds "network/interfaces/macs/$mac/subnet-ipv4-cidr-block")

mkdir -p /etc/systemd/network/70-eks-ens5.network.d
printf '[Route]\nDestination=%s\nScope=link\nMetric=100\n' "$subnet_cidr" \
  > /etc/systemd/network/70-eks-ens5.network.d/10-subnet-route.conf
```

The step uses the instance metadata, so no CIDR is typed. It runs once in the user data, before the node joins the
cluster, and is sufficient for the lifetime of the node: a drop-in is configuration, not a one-off `ip route` command.
It has to exist before the first node-add, because the first address read needs a working host network.

On a running node, the same commands create the drop-in, and a reload applies it without a reboot:

```bash title="Applying the drop-in on a running node"
networkctl reload
networkctl reconfigure ens5
```

!!! warning "Image-specific names"
    `ens5` and `70-eks-ens5.network` are the names the Amazon Linux 2023 EKS image generates for the primary ENI. Another
    image or operating system names the interface and its configuration differently. The step has to be adapted to the
    image, preferably by matching the primary interface by its MAC address and not by its name.

**Check.**

```bash title="Checking the host route"
ip route get <POD_ADDRESS_OF_ANOTHER_NODE>
```

The answer names `dev ens5`.

### Create the Cluster in Layout A

1. Create the VPC, the cluster without the AWS VPC CNI and kube-proxy add-ons, Cilium in ENI mode, and the storage
   node group with the user data above (second ENI and host route) in the same private subnet.
2. Install Multus and the CNI plugins DaemonSet, and create the definition with `host-device` and `sbr` in the
   namespace of the operator.
3. Install cert-manager and the Simplyblock Operator (see [Install Simplyblock Operator](k8s-control-plane.md)).
4. Edit the discovered draft: add the data network, remove `mgmtInterface`, and approve it.

```bash title="Adding the network to the draft"
kubectl -n simplyblock patch clusterdeploymentconfig discovered-initial-discovery --type=json -p='[
  {"op":"add","path":"/spec/cluster/network","value":{"data":[{"name":"fabric","attachment":{"networkAttachmentRef":{"name":"fabric-data"}}}]}},
  {"op":"remove","path":"/spec/nodeSets/0/groups/0/mgmtInterface"}]'
```

## Layout B: Dedicated Subnet

!!! warning "Not verified end to end"
    The reasoning follows from the same routing rules as layout A. The route in the definition and its interaction with
    `sbr` have not been run on a cluster. Verify them on a test cluster first.

The data ENI is created in a subnet that holds only data ENIs, for example, `10.10.100.0/24`. The subnet has its own route
table without a route out of the VPC, so storage traffic stays inside it. A subnet belongs to one availability zone, so
each zone that hosts storage nodes needs its own data subnet.

```plain title="Layout B, one worker"
VPC 10.10.0.0/16

 node subnet 10.10.0.0/20       data subnet 10.10.100.0/24
 worker
 ├─ ens5  10.10.2.132/20        primary ENI, the host and Cilium
 ├─ (pod ENIs of Cilium)        pod addresses
 └─ ens6  10.10.100.17/24       data ENI, moved into the SPDK pod
```

### What Is Easier Than in Layout A

- **The host has no conflict.** The subnets differ, so the host's route for `10.10.0.0/20` exists only on `ens5`. The
  default route of `ens5` has the lower metric. The host reaches the SPDK address through its primary ENI and the VPC.
  No host workaround is needed.
- **The pod has no overlapping route.** The connected route of `data0` covers only `10.10.100.0/24`. The pod's traffic to
  other pods stays on `eth0`.

### Problem B1: Replies to Initiators on Other Subnets

**Symptom.** A volume attach from a worker fails. The connection to the SPDK address times out, and the reachability
check reports `DataNetworkHostUnreachable`.

**Cause.** The initiators are hosts in the node subnet, which is not the data subnet. A request reaches the data ENI
through the VPC and the pod answers by its own routes. The pod's default route is `eth0`, so the reply leaves the pod
network with the data address as source. The VPC drops it, and a strict reverse-path filter drops the request before it
is answered.

**Solution.** A route for the initiators' subnet through the gateway of the data subnet, in the static IPAM block of
the definition. The VPC reserves the first host address of every subnet for its router, so the gateway of
`10.10.100.0/24` is `10.10.100.1`.

```yaml title="NetworkAttachmentDefinition for layout B (fabric-data), not verified"
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
            "routes": [ { "dst": "10.10.0.0/20", "gw": "10.10.100.1" } ]
          }
        },
        { "type": "sbr" }
      ]
    }
```

- `dst` is the subnet in which the worker hosts have their primary ENI, so one route covers every initiator and no
  list per worker is needed.
- `gw` is the first address of the data subnet.
- `sbr` is kept for a reason: it is expected to move the route into the source-based table, so the route applies only
  to packets sourced from the data address. This is the unverified part.

**Why `sbr` matters here.** In the node subnet, hosts and pods share one address range with Cilium in ENI mode. A route for
`10.10.0.0/20` in the pod's main table would also catch the pod's traffic to other pods and send it out of `data0` with
the pod address as source, which the VPC drops. If `sbr` does not move the route, two fallbacks exist:

- Put the pod addresses into subnets of their own (`eni.nodeSpec.subnetTags`, and `eni.nodeSpec.firstInterfaceIndex: 1`
  so that Cilium does not use the primary ENI for pods), so that the route covers only hosts.
- List one `/32` route per initiator. The list changes whenever a worker is replaced and does not scale.

### Create the Cluster in Layout B

1. Create the data subnet and its route table with only the local route, one per availability zone with storage nodes.
2. Create the data ENIs in that subnet (`<DATA_ENI_SUBNET_ID>` in the boot step) and allow the node security group
   in the data security group.
3. Create the definition with the route and `sbr`. No host workaround is needed.
4. Continue as in layout A.

## Choosing a Layout

A dedicated subnet is the conventional design for storage traffic on AWS: it separates routing, access control, and
address space, and the host needs no special configuration. It asks for more planning: a CIDR per availability zone, a
route for the initiators' subnet, and a decision about whether pods share the node subnet.

The same subnet needs no address planning and no route to the initiators. It asks for two workarounds that have to be
present in the node configuration and the definition, and it gives up network-level isolation. Both workarounds are
configuration that is applied once. Neither is something an administrator runs by hand during operation.

The bandwidth of an ENI does not depend on its subnet. The network bandwidth of an EC2 instance is a limit of the
instance as a whole, and a second ENI does not add to it on a single-network-card instance type such as `i3en`. A single
TCP flow is also limited by AWS, so the number of NVMe/TCP connections matters more than the choice of ENI.

## Verification

After the node group, Cilium, Multus, and the operator are installed and the draft is approved:

```bash title="Checking the storage nodes"
kubectl -n simplyblock get storagenode \
  -o custom-columns=NODE:.spec.workerNode,PHASE:.status.phase,PORT:.status.ports.nvmeof,NET:.status.network
```

Every node reaches `Online` with a network entry in phase `Attached` and `hostReachable: true`. The `assigned` address
is the address of the data ENI on the host. The control plane reports the same address on the pod's `data0`.

To verify the data path, create a volume and run a write and a verify from a pod on the worker that serves the volume,
and from pods on other workers:

```yaml title="Pod that writes and verifies a volume with fio"
apiVersion: v1
kind: Pod
metadata:
  name: fio-1
spec:
  nodeSelector:
    kubernetes.io/hostname: <WORKER_NAME>
  restartPolicy: Never
  containers:
    - name: fio
      image: alpine:3.22
      command:
        - sh
        - -c
        - >
          apk add --no-cache fio >/dev/null &&
          fio --name=w --filename=/data/f --size=1G --bs=4k --rw=randwrite --iodepth=16
          --ioengine=libaio --direct=1 --verify=crc32c --do_verify=1 --group_reporting
      volumeMounts:
        - name: d
          mountPath: /data
  volumes:
    - name: d
      persistentVolumeClaim:
        claimName: vol-1
```

!!! important "Pin test pods with a selector, not a node name"
    A pod that sets `spec.nodeName` bypasses the scheduler. A `WaitForFirstConsumer` StorageClass then never binds the
    claim, because the scheduler never selects a node. A `nodeSelector` on `kubernetes.io/hostname` pins the pod and keeps
    the scheduler involved.

## Troubleshooting

| Symptom                                                                                          | Cause                                                                                                 | Solution                                                                                             |
|--------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| `NetworkHostCheckUnavailable`, CSI node plugin log `lookup simplyblock-csi-link ... i/o timeout` | The host reaches the cluster network through the data ENI (layout A)                                  | Add the host route drop-in (problem A2).                                                             |
| Node-add stays in progress, task log shows `ConnectTimeoutError` to the SPDK proxy name          | The SPDK pod answers through the data ENI (layout A), or lacks the route to the initiators (layout B) | Chain `sbr` in the definition (problem A1), or add the route to the initiators' subnet (problem B1). |
| `NetworkInterfaceNoAddress`                                                                      | The interface the definition names has no usable IPv4 address on the host                             | Check the interface name in the definition and that the ENI is attached with an address.             |
| `NetworkAttachmentFailed`, "names no device or PCI address"                                      | The definition has no `device`, `master`, or `pciBusID`                                               | Add the interface to the first plugin of the definition.                                             |
| `DataNetworkHostUnreachable` naming a worker                                                     | No route or security group rule between that worker and the data ENI, or no return path               | Check the data security group (node security group admitted), and the routes of the layout.          |
| A claim stays `Pending` with `WaitForFirstConsumer`                                              | The pod sets `spec.nodeName`                                                                          | Pin with a `nodeSelector`.                                                                           |

## Not Verified

The following parts have not been verified on Amazon EKS:

- Layout B end to end, including the route in the definition and its behavior with `sbr`.
- `macvlan` and `ipvlan` attachments, which need secondary addresses or MAC addresses registered with the VPC.
- Storage nodes in several availability zones, which need a data subnet in each zone.
- Other node images than Amazon Linux 2023, for the host workaround of layout A.
- The throughput of the storage network. The verification above checks correctness, not performance.
