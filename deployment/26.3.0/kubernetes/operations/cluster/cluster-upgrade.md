---
title: "Upgrading a Cluster"
description: "Upgrade the simplyblock operator, control plane, and CSI driver with Helm, then roll the new storage-node image across the storage plane one node at a time."
source: "https://docs.simplyblock.io/latest/kubernetes/operations/cluster/cluster-upgrade/"
---

# Upgrading a Cluster

A simplyblock deployment on Kubernetes upgrades in two parts. The control plane, the operator, and the CSI driver come
from the Helm chart and move together with a chart upgrade. The storage plane runs from container images referenced by
the operator resources, and it is rolled node by node afterward.

The two parts can be upgraded independently, but a control plane that is newer than its storage planes is the only
combination that is supported during the transition. The control plane is therefore upgraded first, and a control
plane that manages several storage clusters is upgraded before any of them.

## Upgrade Order

1. Upgrade the Helm release, which covers the operator, the control plane, and the CSI driver.
2. Wait for the control plane to report itself ready again.
3. Roll the storage-node image across each storage cluster.

## Upgrading the Control Plane

The control plane, the operator, and the CSI driver are all rendered by the same chart, so one upgrade moves them.

```bash title="Upgrading the Helm release"
helm repo update
helm upgrade --install simplyblock -n simplyblock simplyblock/simplyblock-operator \
    --reuse-values
```

`--reuse-values` keeps the values the release was installed with. Without it, every value that was set at install time
falls back to the chart default, which silently reverts settings such as the TLS configuration.

!!! warning
    A chart upgrade re-renders every object the chart owns, which discards manual edits to them. A patch that has to
    survive an upgrade is reapplied afterward, for example, the credentials mount described in
    [FoundationDB Backup and Restore](../data-protection/foundationdb-backup.md).

### Confirming the Control Plane Is Ready

The `ControlPlane` resource is a singleton named `simplyblock`, created by the chart. Its phase is driven by the
readiness endpoint of the management API, which the operator polls every 30 seconds.

```bash title="Checking the control plane phase"
kubectl get controlplane simplyblock -n simplyblock
```

```plain title="Example output of the control plane status"
NAME          PHASE   MESSAGE   AGE
simplyblock   Ready             14d
```

A phase of `Initializing` means the health check is still failing, and the `MESSAGE` column carries the reason. The
storage plane is not touched until the phase is `Ready`.

```bash title="Waiting for the control plane to become ready"
kubectl wait --for=jsonpath='{.status.phase}'=Ready \
    controlplane/simplyblock -n simplyblock --timeout=10m
```

## Upgrading the Storage Plane

Which image a storage node runs is decided by three fields. All of them accept only the trusted simplyblock
registries, and pinning by digest is recommended.

| Field                 | Applies to                                            | Default                   |
|-----------------------|-------------------------------------------------------|---------------------------|
| `spec.clusterImage`   | The storage-node pod of the `StorageNodeSet`.         | `ControlPlane.spec.image` |
| `spec.spdkImage`      | The SPDK image, sent with the node-add request.       | The control plane default |
| `spec.spdkProxyImage` | The SPDK proxy image, sent with the node-add request. | The control plane default |

A `StorageNodeSet` that leaves `spec.clusterImage` empty inherits the image from the `ControlPlane` resource, which the
chart keeps up to date. On such a set the chart upgrade already changed the image, and the DaemonSet rolls its pods as
a consequence.

A `StorageNodeSet` that pins `spec.clusterImage` does not follow the chart. Its image is raised explicitly.

```bash title="Pinning a new storage-node image on a StorageNodeSet"
kubectl patch storagenodeset simplyblock-node -n simplyblock --type=merge \
    -p '{"spec": {"clusterImage": "quay.io/simplyblock-io/simplyblock:26.3.0"}}'
```

`spec.spdkImage` and `spec.spdkProxyImage` are read when a storage node is added, so a change to them governs nodes
added from that point on.

```bash title="Reading the images a StorageNodeSet is configured with"
kubectl get storagenodeset simplyblock-node -n simplyblock \
    -o jsonpath='{.spec.clusterImage}{"\n"}{.spec.spdkImage}{"\n"}{.spec.spdkProxyImage}{"\n"}'
```

### Rolling the Change Across the Nodes

A new image does not reach a running storage node on its own. The node has to be restarted, and the storage-node pod
has to be replaced so that it picks the image up rather than keeping the one it started with.

Both happen in a [Rolling Restart](rolling-restart.md) with the pod refresh enabled. One node at a time is shut down,
its pod is replaced, the node is restarted, and the cluster rebalances before the next node follows.

```bash title="Rolling the new image across the storage nodes"
kubectl patch storagecluster simplyblock-cluster -n simplyblock --type=merge \
    -p '{"spec": {"action": "node-recycle", "nodeRecycle": {"refreshSNodeAPI": true}}}'
```

```bash title="Following the rollout"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status.nodeRecycleStatus}' | jq .
```

The rollout is complete when `status.actionStatus.state` is `success`. The action field is then cleared, so that the
cluster returns to normal status reconciliation, as described in
[Storage Cluster Actions](cluster-actions.md#re-running-and-clearing-an-action).

```bash title="Clearing the action after the rollout"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
    --type=merge -p '{"spec": {"action": ""}}'
```

### Upgrading a Subset of Nodes First

A new image can be tried on a few nodes before the whole fleet follows. The per-node configuration of a
`StorageNodeSet` overrides the fleet image for the workers named in it.

```yaml title="Example of a phased rollout to two workers"
spec:
  nodeConfigs:
    worker-1.example.com:
      spdkImage: quay.io/simplyblock-io/spdk:26.3.0
    worker-2.example.com:
      spdkImage: quay.io/simplyblock-io/spdk:26.3.0
```

The overrides are propagated to the `StorageNode` resources of those workers on the next reconcile. Once the sample
has proven itself, the fleet field is raised and the overrides are removed again.

## Verifying the Result

The storage nodes are online and healthy after a rollout, and the cluster is no longer rebalancing.

```bash title="Checking the storage nodes after an upgrade"
kubectl get storagenodes -n simplyblock
```

```bash title="Checking that the cluster settled"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status.status}{" rebalancing="}{.status.rebalancing}{"\n"}'
```

```bash title="Checking the running storage-node pods"
kubectl get pods -n simplyblock -l app=storage-node \
    -o custom-columns=NAME:.metadata.name,NODE:.spec.nodeName,IMAGE:.spec.containers[0].image
```

## Rolling Back

A storage-plane image is rolled back the way it was rolled forward: the field is set to the previous reference and the
nodes are recycled again. A Helm release is rolled back with `helm rollback`, which restores the previous chart
version together with the values it was rendered from.

```bash title="Rolling the Helm release back to the previous revision"
helm rollback simplyblock -n simplyblock
```

!!! important
    A rollback of the control plane below the version of a storage plane leaves the deployment in the one combination
    that is not supported. The storage planes are rolled back first, and the control plane after them.
