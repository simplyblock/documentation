---
title: "Operating Edge Clusters"
description: "Operation specific to simplyblock edge clusters: monitoring from the hub, failure behavior, maintenance, healing, upgrades, and troubleshooting."
weight: 10160
---

Edge clusters are operated with the same resources and actions as any storage cluster. This page covers what differs
for edge clusters. The architecture is described in
[Edge Clusters](../../../architecture/deployment-topologies/edge-clusters.md).

## Monitoring

The control plane on the hub monitors every edge cluster. Alerts, events, and capacity are read on the hub, see
[Monitoring](../monitoring/index.md). The observability stack (`controlplane.observability`) runs on the hub only.
At the edge, the state is visible in the custom resources:

```bash title="Check an edge cluster"
kubectl -n simplyblock get controlplane,storagecluster,storagenode,storagepool
```

## Failure Behavior

### One-Node Edge Clusters

| Event                    | Effect                                                                                  |
|--------------------------|-----------------------------------------------------------------------------------------|
| WAN link to the hub down | Volume I/O continues. Management operations and automatic recovery wait for the link.   |
| Storage node restart     | Volumes are unavailable until the node is back.                                         |
| One device fails         | With any scheme except 1+0, I/O continues and the data is rebuilt on the other devices. |
| One device fails, 1+0    | The data on the device is lost.                                                         |
| Two devices fail         | With 1+2, 2+2, or 4+2, the data survives. The journal survives as described below.      |
| Journal device fails     | With a dedicated journal device, the node stops, whatever the scheme.                   |

The journal limits what the node survives. With journal partitions (NVMe devices, the default), the journal is
mirrored across the devices: RAID 1 for two devices, RAID 0+1 for more. It survives any one device failure. Two
devices failing at the same time are survived only if both are in the same striped group of the journal. With a
dedicated journal device, which Linux block devices always use, the journal is not mirrored.

After a device failure, the data of the failed device is rebuilt onto the remaining devices of the node in relaxed
placement, so no second node is needed. The remaining devices need enough free capacity for the rebuilt data.

The node itself is not redundant. Protection against the loss of the node relies on backups, replicated snapshots,
or application-level replication.

### Two-Node Edge Clusters

!!! note
    The behavior below requires two-node arbitration support in the control plane, the Simplyblock Operator, and the
    storage nodes.

| Event                                      | Effect                                                                                                                                                                        |
|--------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| WAN link to the hub down                   | Both nodes keep serving I/O. The hub cannot decide anything until the link is back.                                                                                           |
| One node fails                             | The surviving node holds I/O briefly, the hub grants it solo operation, and I/O continues. With host fencing, the workloads of the failed node restart on the surviving node. |
| Link between the nodes down, both nodes up | Both nodes hold I/O. The hub fences both nodes, or with host fencing keeps one node and restarts the workloads of the other one on it.                                        |
| Storage node process fails, node healthy   | The other node continues. The workloads keep running through the path to the other node and are not restarted.                                                                |
| Link between the nodes and WAN link down   | Both nodes fence themselves after the hold time. I/O resumes once the hub is reachable.                                                                                       |
| One node fails while the WAN link is down  | The surviving node fences itself after the hold time and stops until the hub is reachable.                                                                                    |
| Device failure on one node                 | The other node holds a copy of the data and the journal. The data is rebuilt without a third node.                                                                            |

Without the hub, a failed node and a broken link look the same, so no node continues on its own without a grant.

### Host Fencing

With host fencing on (`spec.arbitration.hostFencing`), a fence of the hub is followed by Kubernetes, as described in
[Edge Clusters](../../../architecture/deployment-topologies/edge-clusters.md#coordination-with-kubernetes). The state
of a fence is visible on the cluster, on the node, and on the remediation:

```bash title="Follow a host fence"
kubectl -n simplyblock get storagecluster edge-site-b -o jsonpath='{.status.arbitration.hostFences}'
kubectl get node <NODE> -o jsonpath='{.status.conditions[?(@.type=="StorageFenced")]}'
kubectl -n simplyblock get storagefenceremediation
```

| Host fence state | Meaning                                                                                                 |
|------------------|---------------------------------------------------------------------------------------------------------|
| `revoking`       | The hub is revoking the host of the node on the other node. The node is not marked `StorageFenced` yet. |
| `revoked`        | The host is cut off. The node is marked `StorageFenced`, and NodeHealthCheck remediates it.             |
| `releasable`     | The storage has healed. The host gets its access back once the node is `Ready` and clean.               |
| `restoring`      | The host gets its access back.                                                                          |
| `unavailable`    | No NVMe host NQN is known for the node. Nothing is revoked, and Kubernetes is not told to act.          |

| Remediation phase | Meaning                                                                            |
|-------------------|------------------------------------------------------------------------------------|
| `Pending`         | The fence is not confirmed by the hub yet, or host fencing is off for the cluster. |
| `Blocked`         | A volume of another CSI driver is attached to the node. `status.message` names it. |
| `Tainted`         | The node carries `node.kubernetes.io/out-of-service`.                              |

## Maintenance

Storage nodes are shut down and restarted as described in
[Storage Node Actions](../storage-nodes/storage-node-actions.md). On a one-node edge cluster, the volumes are
unavailable during the maintenance, so the workloads are stopped first. On a two-node edge cluster, the other node
continues and takes over the volumes.

## Healing

After a partition or a node failure in a two-node edge cluster, the hub waits until both nodes see each other again
for a stable period (30 seconds by default). The returning node catches up with the journal and the data it missed,
then rejoins as secondary. The `storage.simplyblock.io/fenced` taint is removed once the cluster is back to normal.
Moving leadership back to the returning node is an optional, planned step.

With host fencing, the returning node gets its host access back in a fixed order: the storage has healed, the node is
`Ready`, and no pod from before the fence is left on it (the out-of-service taint has removed them). Then the
`StorageFenced` condition turns `False`, NodeHealthCheck deletes the remediation, and the out-of-service taint is
removed, so the node takes workloads again. The operator removes only an out-of-service taint that its remediation
set. A taint set by an administrator stays until the administrator removes it.

## Upgrades

The control plane and its operator are upgraded on the hub as described in [Cluster Upgrade](cluster-upgrade.md).
The operator chart at every edge site is upgraded with `helm upgrade`. The hub is upgraded first, so that edge
operators talk to a control plane of the same or a newer release.

## Expansion

The erasure-coding scheme of a cluster cannot be changed after the cluster is created, and a cluster cannot be
changed to or from the cluster mode `Single`. A one-node edge cluster does not become highly available by adding a
second storage node. A highly available edge site is created as a two-node edge cluster from the start.

Devices can be added to the storage nodes of an edge cluster. The data is rebalanced onto the new devices in relaxed
placement, so a one-node or two-node cluster needs no additional node for it.

## Troubleshooting

| Symptom                                        | Check                                                                                                              |
|------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| `ControlPlane` is not `Available` at the edge  | The endpoint, the token Secret, and the CA Secret. The event `EndpointUnreachable` names the failing check.        |
| Storage nodes stay offline in the hub          | The ports 5000 and 8080-9044 from the hub to the edge workers.                                                     |
| Discovery reports no devices                   | `enableControlPlaneNodes`, the device mode (`enableLogicalBlockDevices`), and the device filters.                  |
| Activation of a 1+1 cluster on two nodes waits | `clusterMode: Dual` in the deployment document or the `StorageCluster`.                                            |
| Activation of a one-node cluster waits         | `clusterMode: Single`, exactly one storage node, and one data device per chunk of the stripe.                      |
| Host fence stays `unavailable`                 | The CSI node plugin runs on the node, and `status.remediation.reportedHostNQNs` of the StorageNode lists two NQNs. |
| Host fence stays `releasable`                  | The node is `Ready`, and no pod from before the fence is left on it. The operator log names the reason.            |
| Remediation stays `Blocked`                    | A volume of another CSI driver is attached. Detach it, or set `allowForeignVolumes` on the remediation itself.     |
| A fenced node is not remediated                | The NodeHealthCheck has `maxUnhealthy: 1` and its selector matches the node.                                       |
| `Tainted`, but the workloads did not move      | The pods and `VolumeAttachments` of the node. `Tainted` only confirms the taint, not the eviction.                 |

For a two-node edge cluster, the arbitration state is read from the Management API of the hub:

```bash title="Read the arbitration state of a two-node edge cluster"
curl -s -H "Authorization: Bearer <ADMIN-TOKEN>" \
    https://<HUB-MANAGEMENT-API>/api/v2/clusters/<CLUSTER-ID>/arbitration
```

Logs of the control plane are on the hub. Logs of the operator and the storage nodes are in the `simplyblock`
namespace of the edge cluster.
