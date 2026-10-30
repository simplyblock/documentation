---
title: "Storage Network Configuration"
description: "Choose how the SPDK pods of a storage cluster reach the network: host network, pod network, or a NetworkAttachmentDefinition with host-device, ipvlan, or macvlan, including the host setup each needs."
weight: 30110
---

Every storage node runs an SPDK pod that serves the volumes over NVMe/TCP. How that pod reaches the network is chosen
once, when the storage cluster is created, and each choice has different host requirements and different
consequences. This page describes the options and the host setup each one needs.

The choice is part of the `ClusterDeploymentConfig` (CDC) in `spec.cluster.network`, which becomes
`spec.storageNodes.network` of the `StorageCluster`. It cannot be added, changed, or removed afterwards. To change it,
delete the storage cluster and create it again.

!!! info
    The storage node agent, which the control plane uses to manage a node, runs on the pod network in every
    configuration. Only the SPDK pod differs between them.

## Overview

| Configuration                      | Field in `spec.cluster.network`            | SPDK pod network                    | Data interface of the SPDK pod       | Host setup                                              |
|------------------------------------|--------------------------------------------|-------------------------------------|--------------------------------------|---------------------------------------------------------|
| [Host network](#host-network)      | `spdkOnHostNetwork: true`                  | The host's own                      | The host's NICs, named per node      | None, besides naming the NICs                           |
| [Pod network](#pod-network)        | `podNetwork: true`                         | The cluster CNI                     | `eth0`, behind a Service             | None                                                    |
| [Network attachment](#network-attachment-definitions) | `podNetwork: true` and `data`   | The cluster CNI, plus attached NICs | `data0`, from a NetworkAttachmentDefinition | Multus, a CNI plugin, and for some plugins a host interface |

Exactly one of `podNetwork` and `spdkOnHostNetwork` is set, and `data` is only allowed together with `podNetwork`.
Discovery drafts the host network when most workers have a data NIC besides the management NIC, and the pod network
when none does. It never drafts a network attachment, so that case is an edit of the draft before approval.

!!! warning
    The [Network](../../deployment-preparation/network.md) page lists the requirements for the storage network of a
    production deployment. That includes avoiding software-defined switches and any gateway above layer 2 on the
    storage path. Check these options against it, especially the routed path of `host-device` and the software
    interfaces of `macvlan` and `ipvlan`.

## Host Network

```yaml title="Host network"
spec:
  cluster:
    network:
      spdkOnHostNetwork: true
  nodeSets:
    - name: discovered
      groups:
        - name: group-1
          workers: [worker-1, worker-2, worker-3]
          mgmtInterface: eth0
          dataInterfaces: [eth1]
```

The SPDK pod shares the network namespace of the host and uses the host's NICs directly. There is no CNI, Service, or
overlay between SPDK and the NIC, so this has the lowest overhead and is the choice for dedicated high-performance
NICs. It is also what existing clusters that state no network use.

The NICs are named per group. `mgmtInterface` is the management NIC, and `dataInterfaces` are the NICs that carry
volume traffic. `dataInterfaces` is only allowed in this configuration. Workers whose NICs are named differently, for
example `eth1` on some and `ens6f0` on others, go into separate groups of the same cluster.

Host networking does not add bandwidth. On virtual machines whose network bandwidth is set by the instance type, for
example on Amazon EC2, that limit applies in every configuration.

## Pod Network

```yaml title="Pod network"
spec:
  cluster:
    network:
      podNetwork: true
```

The SPDK pod runs on the cluster's CNI network with its one interface, `eth0`. It carries both the management
traffic and the volume traffic. A Service in front of the pod provides the address that peers and clients use,
because the pod's own address changes on every restart.

Use it when:

- nothing can or should be prepared on the hosts: no NIC names, no dedicated NIC, no extra CNI plugin
- the storage nodes have a single NIC, or host networking is not allowed in the environment
- the performance is limited by the infrastructure anyway, as on instance types with a capped network bandwidth
- several clusters share a worker, because no host ports are bound

The volume traffic then takes the CNI path and shares it with all other pod traffic of the worker.

## Network Attachment Definitions

A NetworkAttachmentDefinition (NAD) is the Kubernetes-native way to give a pod an additional interface. Multus
attaches it, and a CNI plugin decides what the interface is. The SPDK pod keeps its pod-network `eth0` for management
traffic and gets the attached interface as `data0` for volume traffic. The address of `data0` stays the same across
restarts, so no Service is kept.

```yaml title="Pod network with an attached data network"
spec:
  cluster:
    network:
      podNetwork: true
      data:
        - networkAttachmentRef:
            name: fabric-data
            addressPool:
              subnet: 10.10.10.0/24
              first: 10.10.10.151
              last: 10.10.10.160
  nodeSets:
    - name: discovered
      groups:
        - name: group-1
          workers: [worker-1, worker-2, worker-3]
```

Requirements and rules:

- Multus 4 or later, the CNI plugin the NAD names, and the `static` IPAM plugin are installed on every storage worker.
- The NAD is in the namespace of the storage cluster, and its configuration uses static IPAM and
  `"capabilities":{"ips":true}`. The operator chooses the address, not the NAD.
- The cluster refers to the NAD by name only. The plugin is not part of the cluster definition, so the choice between
  `host-device`, `ipvlan`, and `macvlan` is made in the NAD.
- `addressPool` is optional. `first` and `last` are set together and both lie inside `subnet`. Without a pool, a node
  takes the address that the NIC named in the NAD holds on its worker. Every worker's NIC therefore has the same name,
  as the NAD names it once.
- Up to 8 networks, each naming a different NAD. Network attachments carry NVMe/TCP only, not RDMA.
- `dataInterfaces` is not allowed in this configuration.

After a node is added, the operator checks from every worker that the SPDK listener at the node's data address can be
reached. A node that fails the check stays in `Provisioning`, its network is `Unavailable`, and the event
`DataNetworkHostUnreachable` names the address and the worker that could not reach it. The three plugins differ mainly
in how the host can reach a pod on its own worker.

```bash title="Check the result"
kubectl -n simplyblock get storagenode \
  -o custom-columns=NAME:.metadata.name,PHASE:.status.phase,NETWORK:.status.network
```

A healthy node reports `phase: Attached`, `hostReachable: true`, the assigned address, and the interface `data0`.

### host-device

```yaml title="NetworkAttachmentDefinition"
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: fabric-data
  namespace: simplyblock
spec:
  config: '{"cniVersion":"0.3.1","type":"host-device","device":"eth1","capabilities":{"ips":true},"ipam":{"type":"static"}}'
```

The plugin moves the whole NIC into the SPDK pod and moves it back when the pod ends. While the pod runs, the host has
no interface on the data network, so it has no direct path to the pod. One pod can hold a NIC at a time, so a worker
needs one NIC and one NAD per SPDK pod.

A routed path therefore has to be arranged. The initiators, which are the CSI node plugins in the host's network
namespace, reach the pod over another NIC, through a router that has a leg on the data network. The pod needs a route
back, because its default route is `eth0`. Both are the administrator's, and both are examples, not tested here:

```bash title="On each worker: a route to the data subnet through a router, over the management NIC"
ip route add 10.10.10.0/24 via 192.168.10.1 dev eth0
```

```yaml title="In the NAD: a route from the pod to the initiators' subnet"
spec:
  config: '{"cniVersion":"0.3.1","type":"host-device","device":"eth1","capabilities":{"ips":true},"ipam":{"type":"static","routes":[{"dst":"192.168.10.0/24","gw":"10.10.10.1"}]}}'
```

Without such a path, the reachability check fails on every worker. In a test with three workers, each with a single
data NIC and no router, every node stayed in `Provisioning` with its network `Unavailable`:

```plain title="Event on a node without a path"
Cannot reach the SPDK listener at 10.10.10.67:4421 on network "fabric-data" from worker vm17 (dial tcp 10.10.10.67:4421: i/o timeout), so volumes cannot be attached from it.
```

The path also runs through a gateway, which the [Network](../../deployment-preparation/network.md) page advises
against on the storage path. On Rocky Linux 9 with NetworkManager, the NIC's address returned to the host by itself
after the pod ended. Do not rely on that on other systems.

### ipvlan

ipvlan creates an interface on the physical NIC that shares the NIC's MAC address, and `l2` mode puts it on the same
subnet as the NIC.

```yaml title="NetworkAttachmentDefinition"
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: fabric-data
  namespace: simplyblock
spec:
  config: '{"cniVersion":"0.3.1","type":"ipvlan","master":"eth1","mode":"l2","mtu":9000,"ipam":{"type":"static"},"capabilities":{"ips":true}}'
```

A parent interface cannot talk to its own children. While the worker's address sits on `eth1`, the host cannot reach an
SPDK pod on its own worker, and a pod on that worker cannot attach a volume from it. The workaround is a second ipvlan
interface on `eth1`, a sibling, which holds the worker's address instead. Create it on each worker, as root, with the
worker's own data address:

```bash title="Create an ipvlan sibling that holds the worker's address"
IP=10.10.10.62        # the worker's own data address: .63 on the next worker, and so on
ip link add shim0 link eth1 type ipvlan mode l2
ip link set shim0 up
ip addr flush dev eth1
ip addr add $IP/24 dev shim0
ip -br addr show eth1; ip -br addr show shim0    # eth1 has no address, shim0 has $IP/24
```

`eth1` now has no address, so the NAD needs an `addressPool`, as in the example above. The operator takes each node's
address from the pool, and the workers' own addresses stay on their siblings. Check the draft's `network` before
approving it, because discovery drafts the network from the interfaces it finds.

This setup is not persistent. A reboot, or `nmcli con up eth1`, puts the address back on `eth1`, and it then clashes
with the sibling. Make it persistent with a systemd unit or a network script. Neither NetworkManager nor
kubernetes-nmstate supports ipvlan interfaces. The persistent variant is not tested here. To undo the sibling:

```bash title="Remove the ipvlan sibling and restore eth1"
ip link del shim0
ip addr flush dev eth1
nmcli con up eth1
```

All children share the MAC address of `eth1`. A check for an address that is already in use, which relies on one
reply per MAC address, therefore cannot tell the pods apart. This was not tested.

### macvlan

macvlan creates an interface on the physical NIC with its own MAC address, and `bridge` mode lets the children on one
NIC reach each other.

```yaml title="NetworkAttachmentDefinition"
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: fabric-data
  namespace: simplyblock
spec:
  config: '{"cniVersion":"0.3.1","type":"macvlan","master":"eth1","mode":"bridge","mtu":9000,"ipam":{"type":"static"},"capabilities":{"ips":true}}'
```

The same restriction as for ipvlan applies: a parent cannot reach its own children. The workaround is a macvlan
sibling of `eth1` that holds the worker's address. With NetworkManager, which makes it persistent, run this on each
worker as root, with the worker's own data address:

```bash title="Create a macvlan sibling that holds the worker's address"
IP=10.10.10.62        # the worker's own data address: .63 on the next worker, and so on
nmcli con add type macvlan con-name shim0 ifname shim0 \
  macvlan.parent eth1 macvlan.mode bridge macvlan.tap no 802-3-ethernet.mtu 9000 \
  ipv4.method manual ipv4.addresses $IP/24 ipv6.method disabled connection.autoconnect yes
nmcli con mod eth1 ipv4.method disabled ipv4.addresses "" 802-3-ethernet.mtu 9000
nmcli con up eth1 && nmcli con up shim0
ip -br addr show eth1; ip -br addr show shim0    # eth1 has no address, shim0 has $IP/24
```

```bash title="Remove the macvlan sibling and restore eth1"
nmcli con delete shim0
nmcli con mod eth1 ipv4.method manual ipv4.addresses $IP/24
nmcli con up eth1
```

Without NetworkManager, or for a setup that does not survive a reboot, the same interface is created with `ip`:

```bash title="Create the macvlan sibling without NetworkManager"
ip link add shim0 link eth1 type macvlan mode bridge
ip link set shim0 mtu 9000 up
ip addr flush dev eth1
ip addr add $IP/24 dev shim0
```

kubernetes-nmstate can apply the same configuration declaratively: one `NodeNetworkConfigurationPolicy` per worker
that sets `eth1` to no address and creates `shim0` of type `mac-vlan` on `eth1` in bridge mode. It needs NetworkManager
on the hosts. Delete a policy only after applying one that undoes it, because deleting a policy does not undo what it
applied.

As with ipvlan, `eth1` holds no address, so the NAD needs an `addressPool`. With `eth1` bare, discovery found no data
NIC in the test and drafted the pod network, so check the draft's `network` and set it as in the example before
approving it.

## Tested Setups

These configurations were exercised on a three-worker k3s cluster with Flannel, Multus 4.2.3, the CNI reference plugins
1.6.2, and Rocky Linux 9 hosts with an MTU of 9000 on the data NIC.

| Configuration              | Result                                                                                                                  |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------|
| Host network               | All nodes online, volumes written and verified over the data NICs, node shutdown and restart worked.                    |
| Pod network                | All nodes online behind Services, volumes written and verified, node shutdown and restart worked.                       |
| NAD with `macvlan` and sibling | All nodes `Attached` and reachable at the pool addresses, volumes written from every worker including the worker of the SPDK pod, restart kept the node's address. |
| NAD with `ipvlan` and sibling  | The same result as `macvlan`. The pods share the MAC address of `eth1`.                                            |
| NAD with `host-device`     | The SPDK pods start with `data0`, and the nodes stay in `Provisioning` without a routed path.                           |

Not tested: `host-device` with a routed path, the persistent variant of the ipvlan sibling, the duplicate-address check
under ipvlan, `macvlan` and `ipvlan` without the sibling, and SR-IOV.

## Choosing

| Situation                                                                      | Configuration                                |
|--------------------------------------------------------------------------------|----------------------------------------------|
| Dedicated NICs on bare metal, and the best performance is the goal             | Host network                                 |
| Cloud instances or a single NIC, or nothing can be prepared on the hosts       | Pod network                                  |
| A dedicated data NIC, without giving SPDK the host's network namespace         | Network attachment with `macvlan` or `ipvlan` |
| A NIC that belongs to one SPDK pod, and a fabric that routes between the subnets | Network attachment with `host-device`        |
