---
title: "Operations"
description: "Operate simplyblock edge clusters: monitoring, failure behavior of one-node and two-node clusters, maintenance, upgrades, and troubleshooting."
weight: 10109
---

{{ experimental }}

## Monitoring and Alerts

The control plane on the hub monitors every edge cluster. Alerts, events, and capacity of an edge cluster are read
on the hub, as for any storage cluster managed by that control plane. See
[Monitoring](../kubernetes/operations/monitoring/index.md).

The observability stack of the operator chart (`controlplane.observability`) runs on the hub only. An edge cluster
with the managed profile does not collect logs or metrics into a stack of its own.

The state at the edge is visible in the custom resources of the edge cluster:

```bash title="Check an edge cluster"
kubectl -n simplyblock get controlplane,storagecluster,storagenode,storagepool
```

## Failure Behavior

### One-Node Edge Clusters

| Event                    | Effect                                                                                |
|--------------------------|---------------------------------------------------------------------------------------|
| WAN link to the hub down | Volume I/O continues. Management operations and automatic recovery wait for the link. |
| Storage node restart     | Volumes are unavailable until the node is back.                                       |
| Device failure           | With erasure coding 1+0, the data on the device is lost. Volumes on that device fail. |
| Worker failure           | Volumes are unavailable until the worker and its devices are back.                    |

A one-node edge cluster keeps no second copy of the data. Data protection for it relies on backups, snapshots
replicated to another cluster, or application-level replication.

### Two-Node Edge Clusters (Preview)

!!! warning "Preview"
    Two-node edge clusters are not released yet. The table describes the intended behavior of the arbitration
    protocol.

| Event                                      | Effect                                                                                                           |
|--------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| WAN link to the hub down                   | Both nodes keep serving I/O. The hub cannot decide anything until the link is back.                              |
| One node fails                             | The surviving node holds I/O briefly, the hub grants it solo operation, and I/O continues on the remaining path. |
| Link between the nodes down, both nodes up | Both nodes hold I/O. The hub keeps the current leader of each volume group and fences the other node.            |
| Link between the nodes and WAN link down   | The preferred node continues after the hold time. The other node fences itself.                                  |
| One node fails while the WAN link is down  | If the survivor is the preferred node, it continues. Otherwise, it stops until the hub is reachable again.       |

Without a hub, a failed node and a broken link look the same, so a non-preferred node never continues on its own.

## Planned Maintenance

A storage node is shut down and restarted with the operations described in
[Storage Node Actions](../kubernetes/operations/storage-nodes/storage-node-actions.md). On a one-node edge cluster,
this makes the volumes unavailable for the duration of the maintenance, so workloads are stopped first. On a
two-node edge cluster (preview), the other node continues and takes over the volumes of the node under maintenance.

## Healing and Failback (Preview)

After a partition or a node failure in a two-node edge cluster, the hub waits until both nodes see each other again
for a stable period (30 seconds by default). The returning node catches up with the journal and the data it missed,
then rejoins as secondary. The `storage.simplyblock.io/fenced` taint is removed once the cluster is back to normal.
Moving leadership back to the returning node is an optional, planned step.

## Upgrades

- **Hub:** The control plane and its operator are upgraded on the hub, as described in
  [Upgrade](../kubernetes/operations/cluster/cluster-upgrade.md).
- **Edge:** The operator chart at every edge site is upgraded with `helm upgrade`. The storage node image follows
  `controlplane.managed.storageNodeImage` or the image of the `StorageCluster`.

The hub is upgraded first, so that the edge operators talk to a control plane of the same or a newer release.

## Expansion

A one-node edge cluster uses the erasure-coding scheme 1+0, which cannot be changed after the cluster is created. A
second storage node does not make an existing one-node edge cluster highly available. A highly available edge site
is created as a two-node edge cluster from the start (preview).

## Troubleshooting

| Symptom                                       | Check                                                                                                       |
|-----------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| `ControlPlane` is not `Available` at the edge | The endpoint, the token Secret, and the CA Secret. The event `EndpointUnreachable` names the failing check. |
| Storage nodes stay offline in the hub         | The ports 5000 and 8080-9044 from the hub to the edge workers.                                              |
| Discovery reports no devices                  | `enableControlPlaneNodes`, the device mode (`enableLogicalBlockDevices`), and the device filters.           |
| Discovery of Linux block devices fails        | `forceJournalDevice` for workers whose devices are all of equal size.                                       |
| Activation waits on a two-node cluster        | The erasure-coding scheme. 1+1 needs three storage nodes with this release.                                 |

For a two-node edge cluster (preview), the state of the arbitration is read from the Management API of the hub:

```bash title="Read the arbitration state of a two-node edge cluster (preview)"
curl -s -H "Authorization: Bearer <ADMIN-TOKEN>" \
    https://<HUB-MANAGEMENT-API>/api/v2/clusters/<CLUSTER-ID>/arbitration
```

Logs of the control plane are on the hub. Logs of the operator and the storage nodes are in the `simplyblock`
namespace of the edge cluster.
