---
title: "Storage Network Multipathing"
description: "Configure NVMe-oF multipathing over two independent storage networks as an alternative to a bonded, highly available network."
weight: 36000
---

Simplyblock supports two ways to make the storage network redundant:

- A **redundant network** below a single interface, built with link aggregation (LACP), stacked switches, MLAG, or
  active/passive bonding. Simplyblock sees one data interface; the redundancy is handled entirely in the network
  layer.
- **NVMe-oF multipathing** over two (or more) independent storage networks. Each storage node is attached with
  multiple data interfaces in separate VLANs or subnets, routed over separate NIC ports and switches. Simplyblock
  exposes every NVMe-oF subsystem on all data interfaces, and the NVMe hosts and cluster-internal connections use
  native NVMe multipathing across them.

Multipathing places the redundancy in the NVMe layer instead of in the network layer (L2). It requires no switch
support for link aggregation, keeps the two paths physically independent end-to-end, and also spreads the I/O load
across both networks.

## Network Requirements

Each data interface of a host must be in its **own VLAN or subnet**, connected through separate NIC ports and
switch paths.

!!! warning
    Placing two data interfaces into the same subnet does not provide independent paths. Linux routes all outbound
    traffic of a subnet through one interface (the one with the lowest metric), so both "paths" collapse onto a
    single NIC. Use separate subnets per data interface, or set up policy routing.

A typical layout separates management and storage traffic completely:

| Network interface | Purpose                    | Subnet (example) |
|-------------------|----------------------------|------------------|
| eth0              | Management / control plane | 192.168.10.0/24  |
| eth1              | Storage path A             | 10.10.10.0/24    |
| eth2              | Storage path B             | 10.10.20.0/24    |

The management network should still be highly available (a simple bond is sufficient), but it does not carry
storage traffic.

## Configuring Storage Nodes

The data interfaces of a storage node are declared when the node is attached to the cluster, using the
`--data-nics` parameter of `storage-node add-node`. Multiple interfaces are given as a comma-separated list:

```bash title="Attach a storage node with two data interfaces"
{{ cliname }} storage-node add-node <CLUSTER_ID> <SN_CTR_ADDR> <MGT_IF> \
  --data-nics eth1,eth2 <FURTHER_OPTIONS>
```

!!! note
    The interface list is comma-separated without spaces (`eth1,eth2`). If `--data-nics` is omitted, the
    management interface carries the storage traffic and no multipathing is available.

There is no separate switch to enable multipathing: as soon as a node has more than one usable data interface,
all of its NVMe-oF subsystems — logical volumes as well as cluster-internal device and journal subsystems — listen
on every data interface, and all connections to the node are established once per interface.

Multipathing applies per node, but a consistent configuration across all nodes is strongly recommended: use the
same number of data interfaces, in the same set of VLANs, on every storage node.

## Client Connections

With multipathing, `{{ cliname }} volume connect` returns one `nvme connect` command per combination of node and
data interface. A volume with one failover path (erasure coding with one parity chunk) on nodes with two data
interfaces yields **four** connection strings; with two failover paths (two parity chunks), **six**:

```bash title="Retrieve all connection strings for a volume"
{{ cliname }} volume connect <VOLUME_ID>
```

Run **all** returned `nvme connect` commands on the host. The commands connect the same NVMe subsystem (the same
NQN) over the different paths; the Linux kernel's native NVMe multipathing merges them into a single block device
and steers I/O based on the ANA (Asymmetric Namespace Access) state that simplyblock manages per path. No
`dm-multipath` configuration is required or supported.

If a path fails — a NIC, a switch, or an entire network — the kernel transparently continues on the remaining
paths. When a primary node fails over to a secondary node, simplyblock switches the ANA states, and the host
follows without a reconnect.

## Verifying the Configuration

After attaching the nodes, verify that all paths exist:

1. `{{ cliname }} storage-node list --json` — every node reports all of its data interfaces (`data_nics`).
2. `{{ cliname }} storage-node port-list <NODE_ID>` — lists the data interfaces of a node.
3. `{{ cliname }} volume connect <VOLUME_ID>` — returns one connection string per node and interface (for
   example, four entries for a volume with one failover path on dual-interface nodes).
4. `{{ cliname }} storage-node check <NODE_ID>` — verifies all NVMe-oF connections to and from the node,
   including all paths of the cluster-internal connections.

Per-interface I/O statistics are available with `{{ cliname }} storage-node port-io-stats <PORT_ID>`.

## Kubernetes Deployments

In Kubernetes-based deployments, the data interfaces are declared in the `StorageNodeSet` resource: the
`dataIfname` field takes a list of interface names, equivalent to `--data-nics`. Volume connections made by the
CSI driver automatically use all paths; no storage-class parameter is required. See the
[Operator Reference](../../reference/operator/index.md) for details.

## Interaction with Failure Domains and Migration

- Multipathing and [failure domains](../../architecture/concepts/failure-domains.md) are independent features
  that combine naturally: failure domains protect against the loss of a rack or site, multipathing against the
  loss of a network path.
- During a [volume migration](../operations/volume-migration.md), the target subsystem is exposed on all data
  interfaces of the target node. The client must connect all returned target paths before continuing the
  migration, so that the cutover is seamless on every path.
