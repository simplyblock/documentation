---
title: "Storage Network"
description: "Storage network options for simplyblock on Kubernetes: host network, pod network, and Multus with host-device, macvlan, ipvlan, VLAN, and SR-IOV."
weight: 30110
---

A simplyblock storage node serves its volumes over NVMe/TCP from its SPDK pod. Where that traffic flows is decided once
per storage cluster: on the host's own interfaces, on the pod network of the cluster's CNI, or on dedicated interfaces
that Multus attaches to the SPDK pod. This page describes every supported option, what each one requires from the
nodes and the network, how it is declared, and how its result is verified.

The storage network is part of the cluster declaration: `spec.cluster.network` in the `ClusterDeploymentConfig`, which
becomes `spec.storageNodes.network` in the `StorageCluster`. It is fixed when the cluster is created. Changing it later
means deleting the storage cluster and creating it again, so the choice is made during planning, together with the
[Network](../../deployment-preparation/network.md) requirements.

!!! info "Availability"
    The `spdkOnHostNetwork`, `podNetwork`, and `data` fields need a Simplyblock Operator and control plane release
    that includes them. A cluster that declares no network keeps the host-network behavior of earlier releases.

## Components and Their Networks

The storage network decides the network of the SPDK pod only. The other components of a storage node run on the same
network in every option, and the reason for each placement is part of the security model of the deployment.

| Component             | Network                                  | Reason                                                                                                                                                                                 |
|-----------------------|------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Control plane         | Pod network                              | It talks to the storage nodes through their agents and SPDK RPC, which the pod network reaches in every option.                                                                        |
| Storage node agent    | Pod network, with the host PID namespace | It reads the host's interfaces and opens host connections by entering the network namespace of the host's PID 1. That needs the host PID namespace, but no listener on a host port.    |
| CSI node plugin       | Host network                             | The NVMe/TCP initiator runs in the host's network namespace, and the kernel reconnects from it after every path loss. A pod-network connect would move to the host on the first reset. |
| Node preparation Jobs | Host network                             | They configure the host (huge pages, kernel modules, devices) and call the agent at its pod address.                                                                                   |
| SPDK pod              | Depends on the option                    | Described on this page.                                                                                                                                                                |

The initiator is always the host. Every option therefore has to give every worker that mounts volumes a path to every
storage address, including the storage node on the same worker. The operator checks that path before it reports a node
online.

## The Options at a Glance

| Option                                                                          | Declared as                | Multus | Storage traffic flows over                                  | Typical use                                            |
|---------------------------------------------------------------------------------|----------------------------|--------|-------------------------------------------------------------|--------------------------------------------------------|
| [1. Host network](#option-1-host-network)                                       | `spdkOnHostNetwork: true`  | No     | The host's own NICs, used directly by SPDK                  | Bare metal with dedicated storage NICs, RDMA           |
| [2. Pod network](#option-2-pod-network)                                         | `podNetwork: true`         | No     | The CNI's pod network, behind a Service per storage node    | One NIC, no host preparation, any cloud                |
| [3. Dedicated interface](#option-3-dedicated-interface-host-device)             | `podNetwork: true`, `data` | Yes    | A NIC, port, VF, or cloud interface moved into the SPDK pod | A spare port per SPDK pod, a second ENI on Amazon EKS  |
| [4. Shared dedicated interface](#option-4-macvlan-or-ipvlan-on-a-dedicated-nic) | `podNetwork: true`, `data` | Yes    | A `macvlan` or `ipvlan` interface on a storage NIC          | A storage NIC shared by the host and several SPDK pods |
| [5. VLAN on the CNI's NIC](#option-5-vlan-on-the-cnis-nic)                      | `podNetwork: true`, `data` | Yes    | A `macvlan` interface on a tagged VLAN of the CNI's NIC     | One NIC, storage isolated on a VLAN of its own         |
| [6. The CNI's NIC, untagged](#option-6-macvlan-on-the-cnis-nic)                 | `podNetwork: true`, `data` | Yes    | A `macvlan` interface on the CNI's NIC, in its own subnet   | One NIC, no VLAN available                             |
| [7. SR-IOV virtual functions](#option-7-sr-iov-virtual-functions)               | `podNetwork: true`, `data` | Yes    | A VF allocated to the SPDK pod by a device plugin           | SR-IOV NICs, the SR-IOV Network Operator on OpenShift  |

Options 3 to 7 attach the network through a `NetworkAttachmentDefinition`, here called a _definition_. They share the
requirements in [Requirements of Every Attached Network](#requirements-of-every-attached-network).

## Choosing an Option

The decision follows from three questions: whether SPDK may share the host's network namespace, how many NICs the
storage nodes have, and what the network accepts.

1. **RDMA is required:** option 1. Attached networks carry NVMe/TCP only.
2. **The storage nodes have dedicated storage NICs, and SPDK may run in the host's network namespace:** option 1. No
   CNI, Service, or virtual interface sits between SPDK and the NIC, so this path has the lowest overhead.
3. **The storage nodes have SR-IOV NICs, and SPDK has to stay out of the host's network namespace:** option 7. The VF
   gives SPDK a hardware interface, and the NIC's embedded switch carries the traffic to the host.
4. **The storage nodes have a spare storage NIC, and SPDK has to stay out of the host's network namespace:** option 4,
   or option 3 when the network routes between the storage subnet and the hosts.
5. **The storage nodes have one NIC, and storage has to stay off the CNI's datapath:** option 5 when the switches can
   trunk a VLAN to the nodes, option 6 otherwise.
6. **Nothing can be prepared on the hosts, or the bandwidth is capped by the infrastructure anyway:** option 2.
7. **The cluster runs on Amazon EKS with a second ENI:** option 3, as described in
   [Storage Network on Amazon EKS](eks-storage-network.md).

None of the options adds bandwidth. On a virtual machine whose network bandwidth is set by its instance type, that
limit applies to the instance as a whole, whichever option carries the traffic.

## Production Recommendations

The [Network](../../deployment-preparation/network.md#storage-traffic) page sets the requirements of a production
storage network: a redundant network or two VLANs with NVMe multipathing, at least 10 GBit/s per storage node, no
software-defined switch, and no gateway, firewall, or proxy above layer 2 on the storage path. Applied to the options,
they lead to these recommendations:

- **Option 1 on a bond or on two VLANs:** the reference production setup. The storage NICs are named per node, the
  redundancy is provided by the bond or by multipathing, and no software interface is added on the data path.
- **Option 7 where SPDK has to leave the host's network namespace:** a VF is switched in the NIC's hardware, so the
  separation costs no software datapath.
- **Options 4 to 6:** `macvlan` and `ipvlan` are kernel interfaces on a physical parent, not a bridge or a virtual
  switch. They need a host-side sibling interface on every node, which is node configuration and has to be managed as
  such (see [The Host-Side Sibling Interface](#the-host-side-sibling-interface)). Their throughput is to be measured
  against option 1 on the target hardware before production use.
- **Option 3 with a routed path:** the path from the hosts to the SPDK pods runs through a gateway, which the network
  requirements rule out on the storage path. On bare metal, option 3 is suitable where the hosts reach the storage
  subnet on-link through another interface. In a cloud network that routes every packet anyway, such as an Amazon VPC,
  the restriction does not apply in the same way.
- **Option 2:** all storage traffic passes the CNI's datapath and shares it with the pod traffic of the worker. It is
  suitable where the infrastructure caps the bandwidth below what the CNI carries, and for test and edge deployments.
- **MTU:** jumbo frames (MTU 9000) end to end on the storage network, on the parent interfaces, the siblings, the
  definitions, and the switches alike. A mismatch anywhere on the path shows up as stalled connections, not as errors.

## Configuration in Simplyblock

Exactly one of `podNetwork` and `spdkOnHostNetwork` is set. `data` adds dedicated networks to the pod network, so it
is only allowed together with `podNetwork: true`.

```yaml title="Example of the host network (option 1)"
spec:
  cluster:
    network:
      spdkOnHostNetwork: true
```

```yaml title="Example of the pod network (option 2)"
spec:
  cluster:
    network:
      podNetwork: true
```

```yaml title="Example of the pod network with a data network (options 3 to 7)"
spec:
  cluster:
    network:
      podNetwork: true
      data:
        - networkAttachmentRef:
            name: storage-data
            addressPool:
              subnet: 10.10.10.0/24
              first: 10.10.10.151
              last: 10.10.10.160
```

| Field                                     | Meaning                                                                                                                                                                        |
|-------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `spdkOnHostNetwork`                       | The SPDK pods run on the host network and serve on the NICs each node names in `mgmtInterface` and `dataInterfaces`.                                                           |
| `podNetwork`                              | The SPDK pods run on the pod network. Alone, the pod's `eth0` carries all traffic, behind a Service. With `data`, `eth0` carries the RPC and `data0` onward carry the volumes. |
| `data[].networkAttachmentRef.name`        | A definition in the namespace of the storage cluster. It is also the network's name in the status of the storage nodes.                                                        |
| `data[].networkAttachmentRef.addressPool` | The range each node's address on the network is taken from. Each node takes the first free address and keeps it for its lifetime, across restarts.                             |
| `addressPool` unset                       | The node takes the address that the interface named in the definition holds on the worker. This suits `host-device` only.                                                      |
| `addressPool.first`, `addressPool.last`   | Optional, and set together. Both lie inside `subnet`. Unset, the range is the whole subnet.                                                                                    |

The schema enforces these rules, so a declaration that breaks one of them is refused when it is applied:

- One of `podNetwork` and `spdkOnHostNetwork` is `true`, never both.
- `data` needs `podNetwork: true`, holds up to eight networks, and names each definition once.
- A cluster with `data` networks uses the `tcp` fabric. RDMA is served on the host network only.
- `dataInterfaces` are allowed only with `spdkOnHostNetwork: true`, on the cluster, on the groups of the
  `ClusterDeploymentConfig`, and on each `StorageNode`. A cluster that declares no network keeps the earlier
  host-network behavior and still accepts them.
- The network cannot be added, changed, or removed after the cluster is created.

**Interface names per node.** The NIC names belong to each node, because the workers of a fleet do not always agree on
them (`eth1` on some, `ens6f0` on others). Each group of the `ClusterDeploymentConfig` names its `mgmtInterface` and
`dataInterfaces`, and each `StorageNode` carries them in `spec.config`, where they are immutable. Workers whose NICs are
named differently go into separate groups of the same cluster.

**What discovery drafts.** Discovery drafts `spdkOnHostNetwork: true` when most workers have a data NIC besides the
management NIC, and `podNetwork: true` when none does. It adds a note to the draft for either choice, because the
network is fixed at creation. It never drafts a data network: options 3 to 7 are an edit of the draft before approval.
A group's own `networkAttachment` field, which discovery drafts when it finds definitions in the namespace, is not
deployed. The operator holds such a `ClusterDeploymentConfig` with the event `NetworkAttachmentNotDeployable` until the
network is declared in `spec.cluster.network` and the field is removed from the groups.

The draft's `network` is checked before the draft is approved:

```bash title="Showing the network of a draft before approval"
kubectl -n simplyblock get clusterdeploymentconfig <DRAFT> \
    -o jsonpath='{.spec.cluster.network}{"\n"}'
```

## Requirements of Every Attached Network

Options 3 to 7 share these requirements.

| Requirement                                                                            | Reason                                                                                                                                                                                                                                                            |
|----------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Multus, in thick-plugin mode                                                           | Multus attaches the definition's interface to the SPDK pod.                                                                                                                                                                                                       |
| The CNI plugins the definition uses, in the CNI binary directory of every storage node | Multus runs these binaries. `host-device`, `macvlan`, `ipvlan`, `static`, and `sbr` are part of the reference CNI plugins. `sriov` is a separate project.                                                                                                         |
| The definition in the namespace of the storage cluster                                 | Multus refuses a reference to another namespace.                                                                                                                                                                                                                  |
| `static` IPAM, and the `ips` capability declared                                       | The operator chooses each node's address and passes it to the pod. An IPAM plugin that allocates at attach time (DHCP, `host-local`, Whereabouts) returns an address nothing recorded, and it can change on a restart while every client still holds the old one. |
| No default route in the definition                                                     | The pod's default route stays on `eth0`, which carries the RPC and the reach to the cluster.                                                                                                                                                                      |
| Every worker that mounts volumes reaches every storage address                         | The initiator runs in the host's network namespace. The host needs an address in the storage subnet, or a route to it. The operator checks the path from every worker and holds a node that a worker cannot reach.                                                |
| The CSI node plugin on every worker, linked to the operator                            | The operator reads interface addresses and checks the reachability through the CSI node plugins.                                                                                                                                                                  |
| No two interfaces of a pod in one subnet                                               | Two routes for one subnet send replies out of the wrong interface. A definition that has to share a subnet chains the `sbr` plugin (see [Storage Network on Amazon EKS](eks-storage-network.md#problem-a1-routing-in-the-spdk-pod)).                              |

The CNI binary directory is `/opt/cni/bin` on most distributions. K3s and RKE2 use their own directory below
`/var/lib/rancher`, and Multus has to be installed with that directory and the directory its entries point to mounted.

**The reachability check.** Once the control plane reports a node online, the operator asks the CSI node plugin of
every worker to open a TCP connection to the node's SPDK listener on each data network. The network is recorded as
`Attached`, with `hostReachable: true`, and the node as `Online`, only when every worker reaches it. A node that fails
the check stays in `Provisioning`, its network is `Unavailable`, and the event `DataNetworkHostUnreachable` names the
address and the worker that cannot reach it.

## Option 1: Host Network

The SPDK pod runs in the host's network namespace and serves on the host's NICs. No CNI, Service, or virtual interface
lies between SPDK and the NIC. This is the only option that supports RDMA, and the behavior of a cluster that declares
no network.

| Requirement                                                              | Reason                                                                                               |
|--------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| A management NIC and one or more data NICs on every storage node         | SPDK binds the data NICs named for the node. The management NIC carries the control traffic.         |
| For RDMA: RDMA-capable NICs and the RDMA kernel modules                  | The NVMe/RDMA transport needs them on the storage nodes and on the clients.                          |
| Host ports free for the SPDK listeners and the RPC on every storage node | The listeners bind the host's addresses. See [Ports](../../deployment-preparation/network.md#ports). |

```yaml title="Example of the host network with interfaces named per group"
spec:
  cluster:
    network:
      spdkOnHostNetwork: true
  nodeSets:
    - name: rack-a
      groups:
        - name: nic-eth
          workers: [worker-1, worker-2]
          mgmtInterface: eth0
          dataInterfaces: [eth1]
        - name: nic-ens
          workers: [worker-3]
          mgmtInterface: ens5f0
          dataInterfaces: [ens6f0]
```

Each `StorageNode` takes the names of its group into `spec.config.mgmtInterface` and `spec.config.dataInterfaces`.

## Option 2: Pod Network

The SPDK pod runs on the CNI's pod network with one interface, `eth0`, which carries both the RPC and the volume
traffic. The pod's own address changes on every restart. The storage node agent therefore keeps a `ClusterIP` Service
in front of each SPDK pod, and the Service address is the address of the node for clients and for the other storage
nodes.

| Requirement                                                                            | Reason                                                                                                                                                         |
|----------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| A CNI that routes pod addresses between nodes                                          | Storage nodes and clients reach each other's SPDK pods.                                                                                                        |
| `ClusterIP` Services reachable from the host's network namespace                       | The initiator connects to the Service address from the host. kube-proxy and the kube-proxy replacement of Cilium both provide this.                            |
| No network policy that blocks the storage ports between hosts, SPDK pods, and Services | The listeners use the ports the control plane allocates from 4420 upward.                                                                                      |
| A pod MTU as large as the network allows                                               | The pod MTU bounds the NVMe/TCP payload per packet. With an overlay, the pod MTU is the underlay MTU minus the encapsulation, for example, 50 bytes for VXLAN. |

Multus is not needed, and nothing is prepared on the hosts: no NIC names, no extra plugin, and no host port. Several
storage clusters can therefore share a worker. On Cilium, native routing performs better than a tunnel, because it
avoids the encapsulation and the smaller MTU.

The status of each storage node reports the network `pod`, the interface `eth0`, and the Service address, with the
phase `Attached` once the pod runs behind its Service.

## Option 3: Dedicated Interface (host-device)

The `host-device` plugin moves a whole interface into the SPDK pod, and returns it to the host when the pod ends. The
interface can be a physical port, a NIC, a VF named in the definition, or a second cloud interface. SPDK then has an
interface whose queues and interrupts no other pod shares.

| Requirement                                                                                       | Reason                                                                                                                                                                        |
|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| One spare interface per SPDK pod on every storage node, with one name or PCI address on all nodes | The plugin moves the whole interface, and the definition names it once. Two SPDK pods on a worker need two interfaces and two definitions.                                    |
| A path from every host to the storage subnet over another interface                               | While the pod runs, the host has no interface on the storage network. The initiator on the same worker reaches its own SPDK pod only through another port, a VF, or a router. |
| Without an `addressPool`: an address on the interface that does not change                        | The node takes the address the interface holds on the host. A DHCP lease needs a reservation, because the host no longer renews it.                                           |

```yaml title="Example of a host-device definition (storage-data)"
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: storage-data
  namespace: simplyblock
spec:
  config: |
    {
      "cniVersion": "0.3.1",
      "name": "storage-data",
      "type": "host-device",
      "device": "ens4f1",
      "capabilities": { "ips": true },
      "ipam": { "type": "static" }
    }
```

`device` names the interface. When the interface names differ between nodes but the PCI slots agree,
`"pciBusID": "0000:3b:00.1"` names it instead. The network is declared with or without an `addressPool`.

**The return path.** Where the hosts reach the storage subnet only through a router, the pod needs a route back to the
hosts' subnet, because its default route is `eth0`. The route goes into the static IPAM block of the definition, and
the host gets a route to the storage subnet:

```json title="Example of a route back to the hosts' subnet in the definition's IPAM block"
"ipam": {
  "type": "static",
  "routes": [ { "dst": "192.168.10.0/24", "gw": "10.10.10.1" } ]
}
```

```bash title="Adding a route to the storage subnet on each worker"
ip route add 10.10.10.0/24 via 192.168.10.1 dev eth0
```

Without a path, the reachability check fails on every worker, and the nodes stay in `Provisioning`.

**Caveats.** An interface that returns to the host without its address, for example, after its storage node was
removed, holds the next node on that worker until the address is restored. With an `addressPool`, the interface needs no
address on the host. On Amazon EKS, the dedicated interface is a second ENI with routing rules of its own, described in
[Storage Network on Amazon EKS](eks-storage-network.md).

## Option 4: macvlan or ipvlan on a Dedicated NIC

The `macvlan` and `ipvlan` plugins create a virtual interface for the SPDK pod on a NIC that stays on the host. The
host and several SPDK pods share the NIC. `macvlan` gives each interface a MAC address of its own, and `bridge` mode
lets the interfaces of one parent reach each other. `ipvlan` shares the parent's MAC address, and `l2` mode places the
interfaces in the parent's subnet.

| Requirement                                                                  | Reason                                                                                                                                                                                               |
|------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| A storage NIC on every storage node, with one name on all nodes              | The definition names it as `master`.                                                                                                                                                                 |
| For `macvlan`: a network that accepts additional MAC addresses               | Switches with port security, and virtual switches that refuse unknown MAC addresses, drop the traffic. Cloud networks drop it always. `ipvlan` avoids this, because it shares the NIC's MAC address. |
| A host-side sibling interface on every node, with the host's storage address | A host cannot reach the `macvlan` or `ipvlan` interfaces of its own NIC (see [The Host-Side Sibling Interface](#the-host-side-sibling-interface)).                                                   |
| An `addressPool`                                                             | The parent stays on the host. Without a pool, the SPDK pod would take the parent's address, and the pod and the host would hold the same address.                                                    |

```yaml title="Example of a macvlan definition (storage-data)"
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: storage-data
  namespace: simplyblock
spec:
  config: '{"cniVersion":"0.3.1","name":"storage-data","type":"macvlan","master":"eth1","mode":"bridge","mtu":9000,"capabilities":{"ips":true},"ipam":{"type":"static"}}'
```

For `ipvlan`, the type is `ipvlan` and the mode `l2`. The network is declared with an `addressPool` in the storage subnet, outside the range of the hosts' own storage
addresses, as in [Configuration in Simplyblock](#configuration-in-simplyblock).

With the host's address moved from the parent to the sibling, the parent carries no address. Discovery then finds no
data NIC on the workers and drafts `podNetwork: true` without a data network. The draft's `network` is therefore set as
above before the draft is approved.

**Caveats.** All `ipvlan` interfaces share the MAC address of the parent. A duplicate-address check that relies on one
reply per MAC address cannot tell them apart.

## Option 5: VLAN on the CNI's NIC

The storage traffic uses a tagged VLAN on the NIC the CNI uses. The SPDK pod gets a `macvlan` interface on the host's
VLAN interface. Storage has a broadcast domain and a subnet of its own over one cable, and the switches can prioritize
it by VLAN.

| Requirement                                                                                    | Reason                                                                                                                                                                                           |
|------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| The switches trunk the VLAN to every node, the clients' nodes included                         | The storage traffic is tagged.                                                                                                                                                                   |
| A VLAN interface on the CNI's NIC of every node, without an address                            | The definition names it as `master`. The plugin creates the pod's interface on it, but not the VLAN interface itself.                                                                            |
| A host-side sibling interface on the VLAN interface, with the host's storage address           | A host cannot reach the `macvlan` interfaces of its own VLAN interface.                                                                                                                          |
| For Cilium: the VLAN in `bpf.vlanBypass`, and the Cilium agent restarted after a VLAN is added | Cilium's programs on the NIC drop tagged frames of VLANs they do not know. An agent that started before the VLAN interface existed drops its frames until it restarts, even with the bypass set. |

The VLAN interface is created by the network configuration of the distribution: netplan, NetworkManager, or
`systemd-networkd`. On Talos Linux, a machine configuration patch creates it without a reboot:

```yaml title="Example of a Talos machine configuration patch for VLAN 100"
machine:
  network:
    interfaces:
      - interface: ens18
        vlans:
          - vlanId: 100
```

```bash title="Allowing VLAN 100 through Cilium"
helm upgrade cilium cilium/cilium \
    --namespace kube-system \
    --reuse-values \
    --set "bpf.vlanBypass={100}"
kubectl -n kube-system rollout restart ds/cilium
```

```yaml title="Example of a macvlan definition on VLAN 100 (storage-vlan100)"
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: storage-vlan100
  namespace: simplyblock
spec:
  config: '{"cniVersion":"0.3.1","name":"storage-vlan100","type":"macvlan","master":"ens18.100","mode":"bridge","mtu":1500,"capabilities":{"ips":true},"ipam":{"type":"static"}}'
```

The network is declared with an `addressPool` in the VLAN's subnet, for example, `10.10.100.0/24`.

**Caveats.** The MTU of the VLAN is bounded by the NIC's MTU. Cloud networks do not carry customer VLAN tags, so the
option is limited to networks under the operator's control.

## Option 6: macvlan on the CNI's NIC

The SPDK pod gets a `macvlan` interface directly on the NIC the CNI uses, untagged, in a subnet of its own. No switch
configuration is needed. In return, storage shares the broadcast domain of the node network and is separated from it
only by its subnet.

| Requirement                                                                                                     | Reason                                                                                                                                   |
|-----------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------|
| A subnet for storage that no other system on the segment uses, or a range of the node subnet reserved from DHCP | The SPDK pods take their addresses from it on the shared segment.                                                                        |
| A network that accepts additional MAC addresses                                                                 | Each SPDK pod's interface has a MAC address of its own on the node's switch port.                                                        |
| A host-side sibling interface on the CNI's NIC, with the host's storage address                                 | The hosts need an address in the storage subnet, and a host cannot reach the `macvlan` interfaces of its own NIC through the NIC itself. |

Cilium needs no setting, because untagged frames for the `macvlan` interfaces pass Cilium's programs on the NIC.

```yaml title="Example of a macvlan definition on the CNI's NIC (storage-mvnic)"
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: storage-mvnic
  namespace: simplyblock
spec:
  config: '{"cniVersion":"0.3.1","name":"storage-mvnic","type":"macvlan","master":"ens18","mode":"bridge","mtu":1500,"capabilities":{"ips":true},"ipam":{"type":"static"}}'
```

The network is declared with an `addressPool` in the storage subnet, for example, `10.10.200.0/24`.

## Option 7: SR-IOV Virtual Functions

The SR-IOV Network Device Plugin advertises the VFs of the nodes as an extended resource. A definition annotated with
that resource takes the VF the plugin allocates to the SPDK pod, and the SPDK pod requests one of it. The host keeps the
physical function or another VF for its own storage address. The NIC's embedded switch carries the traffic between the
host and the SPDK pod, on the same node as well, so no host-side sibling is needed.

| Requirement                                                                          | Reason                                                                 |
|--------------------------------------------------------------------------------------|------------------------------------------------------------------------|
| VFs created on the physical function of every storage node (`sriov_numvfs`)          | The device plugin advertises existing VFs. It creates none.            |
| The SR-IOV Network Device Plugin, with a pool that selects the storage VFs           | The plugin allocates a VF to each SPDK pod and tells Multus which one. |
| For the `sriov` type: the `sriov` CNI plugin in the CNI binary directory             | Neither Multus nor the reference CNI plugins include it.               |
| An address of the host in the storage subnet, on the physical function or another VF | The initiator on every node reaches the storage addresses.             |
| VFs in kernel mode, not bound to `vfio-pci`                                          | The SPDK pod uses the VF as a kernel interface for NVMe/TCP.           |

On OpenShift, the SR-IOV Network Operator provides the VFs, the device plugin, and the `sriov` plugin, and generates the
definition from a `SriovNetwork` resource. The `SriovNetwork` sets `ipam` to `'{"type": "static"}'` and `capabilities`
to `'{"ips": true}'`, so that the generated definition meets the requirements above.

The definition carries the resource in the `k8s.v1.cni.cncf.io/resourceName` annotation and names no device:

```yaml title="Example of an sriov definition (storage-sriov)"
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: storage-sriov
  namespace: simplyblock
  annotations:
    k8s.v1.cni.cncf.io/resourceName: simplyblock.io/storage_vf
spec:
  config: |
    {
      "cniVersion": "0.3.1",
      "name": "storage-sriov",
      "type": "sriov",
      "vlan": 100,
      "spoofchk": "on",
      "trust": "off",
      "capabilities": { "ips": true },
      "ipam": { "type": "static" }
    }
```

`vlan`, `spoofchk`, and `trust` are optional. The `sriov` plugin sets them on the VF through the physical function.

Where the `sriov` plugin is not available, or the nodes see only VFs, a `host-device` definition with
`"capabilities":{"deviceID":true,"ips":true}` and the same annotation attaches the allocated VF.

The network is declared with an `addressPool`. The VF is unknown until the device plugin allocates it, so no address
can be read from it beforehand, and the operator holds a node with an event that says so when the pool is missing. The
operator reads the annotation and passes the resource to the control plane, which requests one of it for the SPDK
container. Nothing else is configured for the resource.

## The Host-Side Sibling Interface

Options 4, 5, and 6 give the SPDK pod a `macvlan` or `ipvlan` interface on a parent interface of the host. The Linux
kernel does not deliver traffic between a parent interface and its own `macvlan` or `ipvlan` interfaces. A host whose
storage address sits on the parent therefore reaches the SPDK pods of other nodes, but not the one on its own node.
Without a sibling, the reachability check fails from each node to its own SPDK pod, and the node stays in
`Provisioning` with the event `DataNetworkHostUnreachable`. A client on the storage node would otherwise lose the local
path of its volumes and, with it, a failover path.

The solution is a second interface of the same type on the same parent, the _sibling_, which carries the host's storage
address. Two interfaces of one parent reach each other. The parent itself keeps no address in the storage subnet. The
sibling is node configuration: it is created on every node, the clients' nodes included, and it has to survive a
reboot.

In the examples, the parent is `eth1`, the sibling is `shim0`, and `IP` is the node's own storage address, which
differs per node.

=== "NetworkManager (macvlan)"
    NetworkManager keeps the sibling across reboots.

    ```bash title="Creating a persistent macvlan sibling with NetworkManager"
    IP=10.10.10.62
    nmcli con add type macvlan con-name shim0 ifname shim0 \
        macvlan.parent eth1 \
        macvlan.mode bridge \
        macvlan.tap no \
        802-3-ethernet.mtu 9000 \
        ipv4.method manual \
        ipv4.addresses $IP/24 \
        ipv6.method disabled \
        connection.autoconnect yes
    nmcli con mod eth1 \
        ipv4.method disabled \
        ipv4.addresses "" \
        802-3-ethernet.mtu 9000
    nmcli con up eth1
    nmcli con up shim0
    ```

    ```bash title="Removing the macvlan sibling and restoring the address on eth1"
    nmcli con delete shim0
    nmcli con mod eth1 ipv4.method manual ipv4.addresses $IP/24
    nmcli con up eth1
    ```

=== "iproute2 (macvlan or ipvlan)"
    The `ip` commands take effect at once but do not survive a reboot. A reboot, or `nmcli con up eth1`, puts the
    address back on `eth1`, where it clashes with the sibling. A persistent setup runs them from a systemd unit or a
    network script at boot.

    ```bash title="Creating a sibling with iproute2"
    IP=10.10.10.62
    # macvlan: type macvlan mode bridge; ipvlan: type ipvlan mode l2
    ip link add shim0 link eth1 type ipvlan mode l2
    ip link set shim0 mtu 9000 up
    ip addr flush dev eth1
    ip addr add $IP/24 dev shim0
    ```

    ```bash title="Removing the sibling and restoring the address on eth1"
    ip link del shim0
    ip addr flush dev eth1
    nmcli con up eth1
    ```

```bash title="Checking the parent and the sibling on a node"
ip -br addr show eth1
ip -br addr show shim0
```

The parent shows no IPv4 address, and the sibling shows the node's storage address.

## Verification

The operator reports the network of each storage node:

```bash title="Showing the network status of the storage nodes"
kubectl -n simplyblock get storagenode \
    -o custom-columns=NODE:.spec.workerNode,PHASE:.status.phase,NET:.status.network[*].network,STATE:.status.network[*].phase,ADDR:.status.network[*].address,REACH:.status.network[*].hostReachable
```

Every node reaches `Online`. Each data network is `Attached`, with `hostReachable` set to `true` and the address taken
from the pool, or adopted from the interface. On the pod network, the network is `pod` and the address is the
Service address.

The paths of a volume on a client node show whether the local storage node is reachable. On the host, or in a
privileged pod on the client's node:

```bash title="Listing the paths of the volumes on a node"
nvme list-subsys
```

Each volume has one `live` path per storage node that serves it, and the path to the storage node on the same worker
is present and `live`.

## Troubleshooting

| Symptom                                                                                                      | Cause                                                                                                                | Solution                                                                                         |
|--------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| `DataNetworkHostUnreachable` from each worker to the storage node on the same worker                         | `macvlan` or `ipvlan` with the host's storage address on the parent interface                                        | Add the host-side sibling and remove the address from the parent.                                |
| `DataNetworkHostUnreachable` from every worker, with `host-device`                                           | The hosts have no interface on the storage network and no route to it                                                | Give the hosts an on-link path through another interface, or a route and a return route.         |
| `DataNetworkHostUnreachable` naming one worker                                                               | That worker has no address in the storage subnet or no route to it, or a firewall blocks the storage ports           | Give the worker an address or a route, and allow the ports from 4420 upward.                     |
| `NetworkAttachmentNotDeployable` on the `ClusterDeploymentConfig`                                            | A group carries the `networkAttachment` field that discovery drafted                                                 | Declare the network in `spec.cluster.network`, and remove the field from the groups.             |
| The `ClusterDeploymentConfig` or `StorageCluster` is refused with `dataInterfaces are allowed only with ...` | A group or the cluster names `dataInterfaces` with `podNetwork`                                                      | Remove `dataInterfaces`, or use `spdkOnHostNetwork: true`.                                       |
| Tagged frames do not arrive on a node, and Cilium's monitor reports `VLAN traffic disallowed by VLAN filter` | The VLAN is not in `bpf.vlanBypass`, or the Cilium agent started before the VLAN interface existed                   | Add the VLAN to `bpf.vlanBypass` and restart the Cilium agent on the node.                       |
| The SPDK pod stays `Pending` with `Insufficient simplyblock.io/storage_vf`                                   | The device plugin advertises no free VF on the node                                                                  | Check the node's allocatable resources, the VFs, and the plugin's pool selectors.                |
| `NetworkAttachmentFailed`, the definition "names no device or PCI address"                                   | A device-plugin definition without an `addressPool`, or a `host-device` definition without `device` or `pciBusID`    | Declare an `addressPool`, or name the interface in the definition.                               |
| `NetworkInterfaceNoAddress`                                                                                  | No `addressPool`, and the interface named in the definition has no usable IPv4 address on the host                   | Assign an address to the interface, or declare an `addressPool`.                                 |
| The SPDK pod does not start, and Multus reports `Link not found`                                             | The `master` or `device` named in the definition does not exist on the node                                          | Create the interface, for example, the VLAN interface, on every storage node.                    |
| Every pod on a storage worker fails to start after Multus is installed on K3s or RKE2                        | Multus cannot run the plugins, because the CNI binary directory or the directory its entries point to is not mounted | Install Multus with the distribution's CNI directories mounted into its pod.                     |
| No traffic reaches a `macvlan` interface                                                                     | The switch or virtual switch drops unknown MAC addresses                                                             | Allow additional MAC addresses on the ports, or use `ipvlan`, option 5 with a VLAN, or option 7. |
