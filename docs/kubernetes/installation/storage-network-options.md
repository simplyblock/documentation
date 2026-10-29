---
title: "Storage Network Options"
description: "Storage network options for simplyblock on Kubernetes: host network, pod network, and Multus with host-device, macvlan, VLAN, and SR-IOV."
weight: 30150
---

A simplyblock storage node serves NVMe over TCP from its SPDK pod. Where that traffic flows is a choice of the
deployment: on an interface of the host, on the pod network of the cluster's CNI, or on an interface that Multus
attaches to the SPDK pod. This page describes every option simplyblock supports. For each option, it lists what the
cluster and its network have to provide, what is configured in simplyblock, and the caveats
found while testing.

[Storage Network on Amazon EKS](eks-storage-network.md) covers the cloud-specific setup on EKS in depth. This page links
to it where the options meet.

!!! info "Availability"
    The pod network attachment (option 2) and definitions whose device a device plugin allocates (option 7) need an
    operator and control plane release that includes them. The other options are available in every release with the
    storage network feature.

## The Options at a Glance

| Option                                                                                 | Multus | Definition type                           | Storage traffic flows over                                  | Typical use                                                    |
|----------------------------------------------------------------------------------------|--------|-------------------------------------------|-------------------------------------------------------------|----------------------------------------------------------------|
| [1. Host network](#option-1-host-network)                                              | No     | None                                      | An interface of the host, used by the SPDK pod on the host  | Existing deployments, RDMA                                     |
| [2. Pod network](#option-2-pod-network)                                                | No     | None                                      | The CNI's pod network, behind a Service per storage node    | One NIC, no Multus, any cloud                                  |
| [3. Dedicated interface](#option-3-dedicated-interface-host-device)                    | Yes    | `host-device`                             | A NIC, port, or VF that moves into the SPDK pod             | Bare metal with a spare port, a VF by name, a second ENI (EKS) |
| [4. Shared dedicated interface](#option-4-macvlan-or-ipvlan-on-a-dedicated-interface)  | Yes    | `macvlan` or `ipvlan`                     | A virtual interface on a dedicated NIC that stays on host   | A storage NIC shared by several pods or by the host            |
| [5. VLAN on the CNI's NIC](#option-5-vlan-on-the-cnis-interface)                       | Yes    | `macvlan` on a VLAN interface             | A tagged VLAN on the same NIC the CNI uses                  | One NIC, storage isolated on its own VLAN                      |
| [6. The CNI's NIC, untagged](#option-6-macvlan-on-the-cnis-interface)                  | Yes    | `macvlan` on the CNI's interface          | The same NIC and segment as the CNI, in a subnet of its own | One NIC, no VLAN available                                     |
| [7. SR-IOV virtual functions](#option-7-sr-iov-virtual-functions-from-a-device-plugin) | Yes    | `sriov`, or `host-device` with `deviceID` | A VF that a device plugin allocates to the SPDK pod         | SR-IOV NICs, the SR-IOV Network Operator on OpenShift          |

Options 3 to 7 attach the network through a `NetworkAttachmentDefinition` (a _definition_) and share the requirements
in [Requirements of Every Attached Network](#requirements-of-every-attached-network).

### Measured Performance

The table gives the throughput of each option on one test cluster, to show the relative cost of the paths. It is not a
sizing guide: the numbers depend on the NIC, the CPU, the MTU, and the CNI's datapath.

| Option                          | 4K random read, queue depth 32, client on the storage node | Same, client on another node |
|---------------------------------|------------------------------------------------------------|------------------------------|
| 1. Host network (VF)            | 46.8k IOPS                                                 | 46.2k IOPS                   |
| 2. Pod network (Cilium, native) | 32.8k IOPS                                                 | 32.5k IOPS                   |
| 4. `macvlan` on a dedicated VF  | 51.6k IOPS                                                 | 51.2k IOPS                   |
| 5. VLAN on the CNI's NIC        | 47.4k IOPS                                                 | 41.3k IOPS                   |
| 6. `macvlan` on the CNI's NIC   | 45.4k IOPS                                                 | 39.5k IOPS                   |
| 7. VF from a device plugin      | 46.8k IOPS                                                 | 44.9k IOPS                   |

Test cluster: four Talos Linux workers as virtual machines, two Mellanox ConnectX-3 virtual functions per worker (MTU
9000), a virtio interface for the CNI (MTU 1500), Cilium 1.20 in native routing mode, erasure coding 2+1, one 2 GiB
volume. Every option in the table also passed a restart of the storage node under verified writes and a live volume
migration under verified writes without an I/O error.

## Choosing an Option

1. **The deployment needs RDMA:** option 1. Attached networks carry NVMe over TCP only.
2. **Multus cannot be installed, or the cluster runs in a cloud whose network only delivers addresses it assigned (EKS,
   GKE):** option 2, or option 3 with a second cloud interface (see
   [Storage Network on Amazon EKS](eks-storage-network.md)).
3. **The nodes have a spare port or NIC for storage:** option 3, or option 4 when the host or several SPDK pods must
   share it.
4. **The nodes have SR-IOV NICs:** option 7, or option 3 with a VF named in the definition.
5. **The nodes have one NIC, and storage traffic must stay off the CNI's datapath:** option 5 when the switches can trunk
   a VLAN to the nodes, option 6 otherwise.
6. **The nodes have one NIC, and no further network configuration is wanted:** option 2.

## Configuration in Simplyblock

The storage network is part of the cluster declaration: `spec.cluster.network` in a `ClusterDeploymentConfig`, and
`spec.storageNodes.network` in a `StorageCluster`.

```yaml title="The network section of a ClusterDeploymentConfig"
spec:
  cluster:
    network:
      management:                 # optional; the network the control plane reaches the SPDK RPC on
        name: mgmt
        attachment:
          networkAttachmentRef:
            name: storage-mgmt
      data:                       # one to eight networks the storage nodes serve volumes on
        - name: fabric
          attachment:
            networkAttachmentRef:
              name: storage-data
          addressPool:            # optional for host-device; declare it for every other definition type
            subnet: 10.10.10.0/24
            first: 10.10.10.220
            last: 10.10.10.239
```

| Field                       | Meaning                                                                                                                                       |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| `data[].name`               | The network's name within the cluster. The nodes' status reports the network under it.                                                        |
| `attachment`                | Exactly one of `networkAttachmentRef` (options 3 to 7), `hostInterface` (option 1), or `podNetwork` (option 2).                               |
| `networkAttachmentRef.name` | A definition in the namespace of the storage cluster.                                                                                         |
| `addressPool`               | The range the operator takes each node's address from. Every node of the namespace gets the first free address and keeps it for its lifetime. |
| `addressPool` unset         | Only for `host-device`: the node takes the address the interface holds on the host.                                                           |
| `management` unset          | The SPDK RPC is served on the pod network. This is the usual setting.                                                                         |

The schema enforces these rules:

- All networks of a cluster use the same kind of attachment.
- `hostInterface` has no `addressPool`, because the interface carries the host's own address.
- `podNetwork` is the only network of the cluster: one data network, no management network, no `addressPool`.
- With `spec.cluster.network` set, no group names a `mgmtInterface` or `dataInterfaces`. Discovery proposes them, so
  they are removed from the draft before it is approved.
- A group's own `networkAttachment` field, which discovery drafts when it finds definitions in the namespace, is not
  deployed. The operator holds the `ClusterDeploymentConfig` with the event `NetworkAttachmentNotDeployable`. The
  network is declared in `spec.cluster.network` instead, and the field is removed from the groups.
- The network is fixed when the cluster is created.

## Requirements of Every Attached Network

Options 3 to 7 have the following requirements in common.

| Requirement                                                                 | Reason                                                                                                                                                                                                                                                                          |
|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Multus, in thick-plugin mode                                                | Multus attaches the definition's interface to the SPDK pod.                                                                                                                                                                                                                     |
| The CNI plugins the definition uses in `/opt/cni/bin` on every storage node | Multus runs these binaries. `host-device`, `macvlan`, `ipvlan`, `static`, and `sbr` are part of the reference CNI plugins. `sriov` is a separate project.                                                                                                                       |
| The definition in the namespace of the storage cluster                      | Multus refuses a reference to another namespace.                                                                                                                                                                                                                                |
| `static` IPAM, and the `ips` capability declared                            | The operator chooses each node's address and passes it to the pod. An IPAM plugin that allocates at attach time (DHCP, `host-local`, Whereabouts) returns an address that nothing recorded, and the address can change on a restart while every client still holds the old one. |
| No `default-route` in the definition                                        | Multus would replace the pod's default route and break its reach to the cluster.                                                                                                                                                                                                |
| Every worker that mounts volumes reaches every storage address              | The NVMe over TCP initiator runs in the host's network namespace. The host needs an address in the storage subnet or a route to it. The operator checks this from every worker and holds a node that a worker cannot reach.                                                     |
| The CSI node plugin on every worker, linked to the operator                 | The operator reads interface addresses and checks the reachability through the CSI node plugins.                                                                                                                                                                                |
| Two interfaces of a pod do not share a subnet                               | Two routes for one subnet cause replies to leave the wrong interface. A definition that must share a subnet chains the `sbr` plugin (see [Storage Network on Amazon EKS](eks-storage-network.md#problem-a1-routing-in-the-spdk-pod)).                                           |

The control plane runs on the pod network in every option. When a network is declared, the node agent and the SPDK
pod leave the host network as well. The CSI node plugin, the volume migration jobs, and the node-preparation jobs stay
on the host network, because the NVMe over TCP initiator reconnects from the host's network namespace.

## Option 1: Host Network

The SPDK pod runs on the host network and serves on an interface of the host. This is the behavior of a cluster that
declares no network, and the only option that supports RDMA.

**Requirements from the customer.** Every storage node has an interface for the management traffic and one or more for
the data traffic, with the same names on every node. RDMA needs RDMA-capable NICs and the RDMA kernel modules on the
nodes.

**Configuration in simplyblock.** The interfaces are named on the node group, either as `mgmtInterface` and
`dataInterfaces`, or as `hostInterface` attachments in `spec.cluster.network`.

```yaml title="Host interfaces on a node group"
spec:
  nodeSets:
    - name: all
      groups:
        - name: group-1
          mgmtInterface: eth0
          dataInterfaces: [eth1]
```

## Option 2: Pod Network

The SPDK pod runs on the CNI's pod network, with no further interface. The node agent keeps a `ClusterIP` Service in
front of each SPDK pod: the Service address is the node's address for clients and the other storage nodes, and it
survives restarts of the pod, while the pod's own address changes with each restart.

**Requirements from the customer.**

| Requirement                                                                            | Reason                                                                                                                                                                 |
|----------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| A CNI that routes pod addresses between nodes                                          | Storage nodes and clients reach each other's SPDK pods.                                                                                                                |
| `ClusterIP` Services reachable from the host network namespace                         | The NVMe over TCP initiator connects to the Service address from the host. kube-proxy and Cilium's kube-proxy replacement both provide this.                           |
| No network policy that blocks the storage ports between hosts, SPDK pods, and Services | The listeners use the ports the control plane allocates from 4420 upward.                                                                                              |
| A pod MTU as large as the network allows                                               | The MTU of the pod network bounds the NVMe over TCP payload per packet. With an overlay, the pod MTU is the underlay MTU minus the encapsulation (50 bytes for VXLAN). |

Multus is not needed. On Cilium, native routing performs better than a tunnel: in an early test on the same cluster,
native routing gave about a fifth more 4K random-read IOPS across nodes than VXLAN.

**Configuration in simplyblock.**

```yaml title="Pod network"
spec:
  cluster:
    network:
      data:
        - name: cni
          attachment:
            podNetwork: {}
```

The operator reports each node's network as `cni`, interface `eth0`, with the Service address, and the phase
`Attached` once the pod runs behind the Service.

**Caveats.** All storage traffic passes the CNI's datapath, which costs throughput and latency compared with a NIC of its
own (see [Measured Performance](#measured-performance)). The storage traffic cannot be separated from the pod traffic by
the network.

## Option 3: Dedicated Interface (host-device)

The `host-device` plugin moves a whole interface into the SPDK pod: a physical port, a NIC, a VF named in the definition,
or a second cloud interface. The SPDK process then has an interface of its own.

**Requirements from the customer.**

| Requirement                                                                                         | Reason                                                                                                                                      |
|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| One spare interface per SPDK pod on every storage node, with one name (or PCI address) on all nodes | The plugin moves the whole interface. A node with two SPDK pods needs two interfaces and two definitions.                                   |
| Another interface of the host in the storage subnet, or a route to it                               | The interface leaves the host while the pod runs. The initiator on the same node reaches the pod through another port, a VF, or the switch. |
| Without an `addressPool`: an address on the interface that does not change                          | The node takes the address the interface holds on the host. A DHCP lease needs a reservation, because the host no longer renews it.         |

**Configuration in simplyblock.**

```yaml title="NetworkAttachmentDefinition storage-data (host-device)"
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

`device` names the interface. When the interface names differ between nodes but the PCI slots agree, `"pciBusID":
"0000:3b:00.1"` names it instead. The network is declared with `networkAttachmentRef: {name: storage-data}`, with or
without an `addressPool`.

**Caveats.** With an `addressPool`, the interface needs no address on the host. Without one, an interface that returns
to the host without its address (for example, after its storage node was removed) holds the next node on that worker
until the address is restored. On Amazon EKS, the dedicated interface is a second ENI with routing rules of its own,
described in [Storage Network on Amazon EKS](eks-storage-network.md).

## Option 4: macvlan or ipvlan on a Dedicated Interface

The `macvlan` and `ipvlan` plugins create a virtual interface for the SPDK pod on a NIC that stays on the host. Several
SPDK pods and the host share the NIC.

**Requirements from the customer.**

| Requirement                                                                  | Reason                                                                                                                                                                                                                            |
|------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| A NIC for storage on every storage node, with one name on all nodes          | The definition names it as `master`.                                                                                                                                                                                              |
| A network that accepts additional MAC addresses (`macvlan`)                  | Each `macvlan` interface has a MAC address of its own. Switches with port security and virtual switches that refuse unknown MAC addresses drop its traffic. Cloud networks drop it always. `ipvlan` shares the NIC's MAC address. |
| A host-side sibling interface on every node, with the host's storage address | A host cannot reach the `macvlan` or `ipvlan` interfaces of its own NIC (see [The Host-Side Sibling Interface](#the-host-side-sibling-interface)).                                                                                |

**Configuration in simplyblock.**

```yaml title="NetworkAttachmentDefinition storage-data (macvlan)"
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: storage-data
  namespace: simplyblock
spec:
  config: '{"cniVersion":"0.3.1","name":"storage-data","type":"macvlan","master":"enp2s0","mode":"bridge","mtu":9000,"capabilities":{"ips":true},"ipam":{"type":"static"}}'
```

For `ipvlan`, the type is `ipvlan` and the mode `l2`. The network is declared with an `addressPool`:

```yaml title="Data network with an address pool"
data:
  - name: storage-data
    attachment:
      networkAttachmentRef: {name: storage-data}
    addressPool: {subnet: 10.10.10.0/24, first: 10.10.10.220, last: 10.10.10.239}
```

!!! warning "Always declare an address pool"
    Without a pool, the node would take the address of the `master` interface, which stays on the host. The SPDK pod and
    the host would then hold the same address.

## Option 5: VLAN on the CNI's Interface

The storage traffic uses a tagged VLAN on the same NIC the CNI uses. The SPDK pod gets a `macvlan` interface on the VLAN
interface of the host. Storage has a broadcast domain and a subnet of its own, over one cable.

**Requirements from the customer.**

| Requirement                                                                                    | Reason                                                                                                                                                                                           |
|------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| The switches trunk the VLAN to every node, the clients' nodes included                         | The storage traffic is tagged.                                                                                                                                                                   |
| A VLAN interface on the CNI's NIC on every node, without an address                            | The definition names it as `master`. The plugin creates the pod's interface on it and does not create the VLAN interface.                                                                        |
| A host-side sibling interface on the VLAN interface, with the host's storage address           | A host cannot reach the `macvlan` interfaces of its own VLAN interface. With the address on the VLAN interface itself, clients on the same node lose the path to the local storage node.         |
| For Cilium: the VLAN in `bpf.vlanBypass`, and the Cilium agent restarted after a VLAN is added | Cilium's programs on the NIC drop tagged frames of VLANs they do not know. An agent that started before the VLAN interface existed drops its frames until it restarts, even with the bypass set. |

**VLAN interface on Talos Linux.** A machine configuration patch creates the VLAN interface on each node, without a
reboot:

```yaml title="Talos machine configuration patch"
machine:
  network:
    interfaces:
      - interface: ens18
        vlans:
          - vlanId: 100
```

Other distributions create the VLAN interface in their network configuration (netplan, NetworkManager, or
`systemd-networkd`).

**Cilium.**

```bash title="VLAN bypass in Cilium"
helm upgrade cilium cilium/cilium -n kube-system --reuse-values --set "bpf.vlanBypass={100}"
kubectl -n kube-system rollout restart ds/cilium
```

**Configuration in simplyblock.**

```yaml title="NetworkAttachmentDefinition storage-vlan100"
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: storage-vlan100
  namespace: simplyblock
spec:
  config: '{"cniVersion":"0.3.1","name":"storage-vlan100","type":"macvlan","master":"ens18.100","mode":"bridge","mtu":1500,"capabilities":{"ips":true},"ipam":{"type":"static"}}'
```

The network is declared with an `addressPool` in the VLAN's subnet, for example, `10.10.100.0/24`.

**Caveats.** The MTU of the VLAN is bounded by the NIC's MTU. The option does not work in clouds, whose networks do not
carry customer VLAN tags.

## Option 6: macvlan on the CNI's Interface

The SPDK pod gets a `macvlan` interface directly on the NIC the CNI uses, untagged, in a subnet of its own. The option
needs no switch configuration. In return, storage shares the broadcast domain of the node network and is separated from
it only by its subnet.

**Requirements from the customer.**

| Requirement                                                                                                     | Reason                                                                                                                                   |
|-----------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------|
| A subnet for storage that no other system on the segment uses, or a range of the node subnet reserved from DHCP | The SPDK pods take their addresses from it on the shared segment.                                                                        |
| A network that accepts additional MAC addresses                                                                 | Each SPDK pod's interface has a MAC address of its own on the node's switch port.                                                        |
| A host-side sibling interface on the CNI's NIC, with the host's storage address                                 | The hosts need an address in the storage subnet, and a host cannot reach the `macvlan` interfaces of its own NIC through the NIC itself. |

Cilium needs no setting: untagged frames for the `macvlan` interfaces pass Cilium's programs on the NIC.

**Configuration in simplyblock.**

```yaml title="NetworkAttachmentDefinition storage-mvnic"
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: storage-mvnic
  namespace: simplyblock
spec:
  config: '{"cniVersion":"0.3.1","name":"storage-mvnic","type":"macvlan","master":"ens18","mode":"bridge","mtu":1500,"capabilities":{"ips":true},"ipam":{"type":"static"}}'
```

The network is declared with an `addressPool` in the storage subnet, for example, `10.10.200.0/24`.

**Choosing between options 5 and 6.** Both use the same NIC, the same plugin, and the same host-side sibling, and both
perform alike. Option 5 isolates the storage traffic at layer 2 and lets the switches prioritize it by VLAN. Option 6
needs no switch configuration, but every system on the node segment can reach the storage subnet by adding an address.

## Option 7: SR-IOV Virtual Functions from a Device Plugin

The SR-IOV Network Device Plugin advertises the VFs of the nodes as an extended resource. A definition annotated with
that resource takes the VF the plugin allocates to the SPDK pod, and the SPDK pod requests one of it. The host keeps the
physical function or another VF for its own storage address, and the NIC's embedded switch carries the traffic between
the host and the SPDK pod, on the same node as well. No host-side sibling interface is needed.

**Requirements from the customer.**

| Requirement                                                                          | Reason                                                                 |
|--------------------------------------------------------------------------------------|------------------------------------------------------------------------|
| VFs created on the physical function of every storage node (`sriov_numvfs`)          | The device plugin advertises existing VFs. It creates none.            |
| The SR-IOV Network Device Plugin, with a pool that selects the storage VFs           | The plugin allocates a VF to each SPDK pod and tells Multus which one. |
| For the `sriov` type: the `sriov` CNI plugin in `/opt/cni/bin`                       | Neither Multus nor the reference CNI plugins include it.               |
| An address of the host in the storage subnet, on the physical function or another VF | The initiator on every node reaches the storage addresses.             |
| VFs in kernel mode (a network interface), not bound to `vfio-pci`                    | The SPDK pod uses the VF as a kernel interface for NVMe over TCP.      |

On OpenShift, the SR-IOV Network Operator provides the VFs, the device plugin, and the `sriov` plugin, and generates the
definition from a `SriovNetwork` resource.

```json title="Device plugin pool that selects the VFs of a physical function"
{
  "resourceList": [
    {
      "resourceName": "storage_vf",
      "resourcePrefix": "simplyblock.io",
      "selectors": { "pfNames": ["ens4f0"] }
    }
  ]
}
```

**Configuration in simplyblock.** The definition carries the resource in the `k8s.v1.cni.cncf.io/resourceName`
annotation and names no device. With the `sriov` plugin:

```yaml title="NetworkAttachmentDefinition storage-sriov (sriov)"
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

Where the `sriov` plugin is not available, or the nodes only see VFs (for example, virtual machines with VFs passed
through), `host-device` with the `deviceID` capability attaches the allocated VF:

```yaml title="NetworkAttachmentDefinition storage-vfdp (host-device with a device plugin)"
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: storage-vfdp
  namespace: simplyblock
  annotations:
    k8s.v1.cni.cncf.io/resourceName: simplyblock.io/storage_vf
spec:
  config: '{"cniVersion":"0.3.1","name":"storage-vfdp","type":"host-device","capabilities":{"deviceID":true,"ips":true},"ipam":{"type":"static"}}'
```

The network is declared with an `addressPool`: the VF is unknown until the device plugin allocates it, so no address can
be read from it beforehand. The operator holds the node with an event that says so when the pool is missing.

The operator reads the annotation and passes the resource to the control plane, which requests one of it for the SPDK
container. Nothing else is configured for the resource.

## The Host-Side Sibling Interface

Options 4, 5, and 6 give the SPDK pod a `macvlan` (or `ipvlan`) interface on a parent interface of the host. The Linux
kernel does not deliver traffic between a parent interface and its own `macvlan` interfaces. A host whose storage
address sits on the parent can therefore reach the SPDK pods of other nodes but not the one on its own node.

The consequences without a sibling:

- The operator's reachability check fails from each node to its own SPDK pod. The node stays in `Provisioning`, its
  network in `Unavailable` with `hostReachable` set to `false`, and the event `DataNetworkHostUnreachable` names the
  worker that cannot reach the SPDK listener.
- On an operator that does not check, a client on the storage node silently uses the remote paths only: in the test
  cluster, 35.1k instead of 47.4k IOPS, and the volume loses its local path for failover.

The solution is a second `macvlan` interface on the same parent for the host, which carries the host's storage address.
Two `macvlan` interfaces of one parent reach each other. The parent itself keeps no address in the storage subnet.

The sibling is node configuration and is created on every node, the clients' nodes included. Where the distribution's
network configuration supports `macvlan` interfaces, it belongs there. Otherwise, a DaemonSet creates and keeps it:

```yaml title="DaemonSet that keeps a host-side macvlan sibling (example for option 6)"
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: sb-host-macvlan
  namespace: kube-system
spec:
  selector:
    matchLabels: {app: sb-host-macvlan}
  template:
    metadata:
      labels: {app: sb-host-macvlan}
    spec:
      hostNetwork: true
      tolerations: [{operator: Exists}]
      containers:
        - name: link
          image: nicolaka/netshoot:v0.13
          env:
            - name: HOST_IP
              valueFrom: {fieldRef: {fieldPath: status.hostIP}}
          command: ["/bin/sh", "-c"]
          args:
            - |
              IP=10.10.200.${HOST_IP##*.}       # host's storage address, here derived from its node address
              trap "ip link del sbhost0 2>/dev/null; exit 0" TERM
              while true; do
                ip link show sbhost0 >/dev/null 2>&1 || ip link add sbhost0 link ens18 type macvlan mode bridge
                ip link set sbhost0 up
                ip -4 addr show dev sbhost0 | grep -q "$IP/24" || ip addr add $IP/24 dev sbhost0
                sleep 10 & wait $!
              done
          securityContext: {privileged: true}
```

For option 5, the parent is the VLAN interface (`ens18.100`) and the address is in the VLAN's subnet. The image, the
interface names, and the address scheme are examples.

## Verification

The operator reports the network of each storage node:

```bash title="Network status of the storage nodes"
kubectl -n simplyblock get storagenode \
  -o custom-columns=NODE:.spec.workerNode,PHASE:.status.phase,NET:.status.network[*].phase,ADDR:.status.network[*].address,REACH:.status.network[*].hostReachable
```

Every node reaches `Online`, with each network `Attached` and `hostReachable` set to `true`.

The paths of a volume on a client node show whether the local storage node is reachable. In a privileged pod on the
client's node, or on the host:

```bash title="Paths of the volumes on a node"
nvme list-subsys
```

Each volume has one `live` path per storage node that serves it. A path to the storage node on the same worker is
present and `live`.

For option 7, the SPDK pod requests the device plugin's resource and carries the allocated VF:

```bash title="Resource request and allocated device of an SPDK pod"
kubectl -n simplyblock get pod <SPDK_POD> -o jsonpath='{.spec.containers[0].resources.limits}'
kubectl -n simplyblock get pod <SPDK_POD> -o jsonpath='{.metadata.annotations.k8s\.v1\.cni\.cncf\.io/network-status}'
```

The limits include the resource, and the network status shows the data interface with a `device-info` entry naming the
VF's PCI address.

## Troubleshooting

| Symptom                                                                                                      | Cause                                                                                                             | Solution                                                                                         |
|--------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| `DataNetworkHostUnreachable` from each worker to the storage node on the same worker                         | `macvlan` or `ipvlan` with the host's storage address on the parent interface                                     | Add the host-side sibling and remove the address from the parent.                                |
| `DataNetworkHostUnreachable` naming one worker                                                               | That worker has no address in the storage subnet or no route to it, or a firewall blocks the storage ports        | Give the worker an address or a route, and allow the ports from 4420 upward.                     |
| Tagged frames do not arrive on a node, and Cilium's monitor reports `VLAN traffic disallowed by VLAN filter` | The VLAN is not in `bpf.vlanBypass`, or the Cilium agent started before the VLAN interface existed                | Add the VLAN to `bpf.vlanBypass` and restart the Cilium agent on the node.                       |
| The SPDK pod stays `Pending` with `Insufficient simplyblock.io/storage_vf`                                   | The device plugin advertises no free VF on the node                                                               | Check the node's allocatable resources, the VFs, and the plugin's pool selectors.                |
| `NetworkAttachmentFailed`, the definition "names no device or PCI address"                                   | A device-plugin definition without an `addressPool`, or a `host-device` definition without `device` or `pciBusID` | Declare an `addressPool`, or name the interface in the definition.                               |
| `NetworkInterfaceNoAddress`                                                                                  | No `addressPool`, and the interface named in the definition has no usable IPv4 address on the host                | Assign an address to the interface, or declare an `addressPool`.                                 |
| The SPDK pod does not start, and Multus reports `Link not found`                                             | The `master` or `device` named in the definition does not exist on the node                                       | Create the interface (for example, the VLAN interface) on every storage node.                    |
| No traffic reaches a `macvlan` interface                                                                     | The switch or virtual switch drops unknown MAC addresses                                                          | Allow additional MAC addresses on the ports, or use `ipvlan`, option 5 with a VLAN, or option 7. |

## Verification Status

Options 1, 2, and 4 to 7 were deployed and tested end to end on the test cluster described in
[Measured Performance](#measured-performance): deployment, I/O with verification, a restart of a storage node under I/O,
and a live volume migration under I/O. Option 3 was deployed and tested with I/O and a restart of a storage node on the
same cluster, and on Amazon EKS as described in [Storage Network on Amazon EKS](eks-storage-network.md). The following
parts are not verified:

- A live volume migration on option 3. Option 7 with `host-device` moves the VF with the same plugin and passed it.
- The `sriov` plugin of option 7 with a physical function. The test cluster only had VFs passed through to virtual
  machines and used `host-device` with `deviceID`, which takes the device from the same allocation and the same pod
  request.
- `ipvlan` on the CNI's NIC (option 6 with `ipvlan`).
- Option 2 on Amazon EKS, and the live volume migration of option 2 on GKE Dataplane V2.
- MTU above 1500 on the pod network, and on a VLAN of the CNI's NIC.
- Cilium network policies, the host firewall, and transparent encryption on the storage path.
