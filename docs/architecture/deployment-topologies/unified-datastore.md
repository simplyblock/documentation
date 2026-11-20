---
title: "Unified DataStore"
description: "Unified DataStore deployments run simplyblock storage nodes on LUNs of an FC, iSCSI, or NVMe-oF storage array, combined with HCI or disaggregated placement."
weight: 20256
---

{{experimental}}

In a Unified DataStore deployment, the storage nodes keep their data on LUNs of an external storage array instead of
local NVMe devices. The LUNs are created, presented, grown, and fenced by simplyblock itself through an array
plug-in, and each LUN is presented to standby nodes as well, so that a failed storage node's LUN is taken over within
seconds. The architecture is described in [Unified DataStore](../concepts/unified-datastore.md).

## How It Works

```plain title="Unified DataStore deployment"
          Kubernetes cluster
 ┌──────────────────────────────────────────────────────────┐
 │  Control plane + Simplyblock Operator ── HTTPS ──────────┼──► Array management API
 │                                                          │
 │  Worker A          Worker B          Worker C            │
 │  storage node      storage node      storage node        │
 │  local journal     local journal     local journal       │
 │   │ LUN A (serves)  │ LUN B (serves)  │ LUN C (serves)   │
 │   │ LUN C (standby) │ LUN A (standby) │ LUN B (standby)  │
 └───┼─────────────────┼─────────────────┼──────────────────┘
     └──── FC, iSCSI, or NVMe-oF (SAN) ──┴──► Storage array (RAID, thin pool)
```

Every worker that runs a storage node is connected to the array over the SAN. Each storage node owns one data LUN and
keeps its journal on a local disk of its worker. The LUN is also presented to the node's standby nodes: one with a
fault tolerance of `1`, two with a fault tolerance of `2`. The control plane reaches the array's management API over
HTTPS to create, map, grow, unmap, and delete LUNs.

Applications reach their volumes over NVMe-oF as in any other simplyblock deployment. The cluster runs `1+0`, so
every volume has data on every LUN, and a failed storage node pauses the I/O of all volumes for the seconds its LUN
takeover takes.

## Placement

The Unified DataStore is a choice of storage backend, not of placement. It combines with both placements:

- **Hyper-converged:** The storage nodes run on the application workers, which then need SAN connectivity. See
  [HCI (Hyper-Converged)](hci.md).
- **Disaggregated:** The storage nodes run on dedicated workers. Only these need SAN connectivity, and the
  application workers reach simplyblock over the storage network alone. See [Disaggregated](disaggregated.md).

Disaggregated placement is the common choice: the SAN ports, initiators, and zoning are limited to a few dedicated
workers, and the applications do not depend on the SAN configuration of their workers.

Both control-plane placements are supported (see [Control Plane and Operator](control-plane-and-operator.md)). The
control plane needs HTTPS access to the array's management API in either case.

## Networks

A Unified DataStore deployment uses three networks:

| Network                  | Between                                         | Carries                                                          |
|--------------------------|-------------------------------------------------|------------------------------------------------------------------|
| SAN (FC, iSCSI, NVMe-oF) | Storage workers and the array                   | The LUNs' data                                                   |
| Storage network          | Storage nodes, and storage nodes and clients    | NVMe-oF traffic between storage nodes, and volume I/O of clients |
| Management               | Control plane, the array, and the storage nodes | The array's management API, and the control of the storage nodes |

The SAN is kept separate from the storage network, so that array I/O and simplyblock I/O do not compete for the
same links.

## Benefits

- **Existing arrays:** Arrays already in the datacenter serve Kubernetes workloads with the full simplyblock feature
  set: Kubernetes-native volumes, snapshots and clones, QoS, encryption, replication, and disaster recovery.
- **No rebuild after a node failure:** The array keeps the data, so a failed storage node costs a LUN takeover of a
  few seconds instead of a rebuild.
- **No parity overhead:** The array's RAID protects the data, and simplyblock stores a single copy.
- **Automated provisioning:** LUNs are created, mapped, and grown by simplyblock, without manual work on the array
  for every node.

## Considerations

- **Shared failure domain:** All storage nodes depend on the array. An outage of the array stops the whole cluster.
- **SAN connectivity:** Every storage worker needs a working connection to the array, prepared before the
  deployment (see [Unified DataStore](../../deployment-preparation/unified-datastore.md)).
- **I/O pause on node failure:** The volumes pause their I/O while a failed node's LUN is taken over.
- **Minimum scale:** At least the fault tolerance plus one storage nodes, on as many workers: two for a fault
  tolerance of `1`, three for `2`.

## When to Choose the Unified DataStore

A Unified DataStore deployment is the preferred choice when:

- An existing storage array is to serve Kubernetes workloads.
- Data protection is to stay with the array, while snapshots, clones, replication, and disaster recovery move to
  simplyblock.
- Storage nodes are to survive node failures without rebuilding data.

The deployment itself is described in [Deploying a Unified DataStore](../../kubernetes/installation/unified-datastore.md).
