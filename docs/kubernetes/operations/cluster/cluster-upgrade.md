---
title: "Upgrading a Cluster"
description: "Upgrade the simplyblock operator, control plane, and CSI driver with Helm, then roll the new storage-node image across the storage plane one node at a time."
weight: 10130
---

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
NAME          PHASE       MESSAGE   AGE
simplyblock   Available             14d
```

| Phase         | Meaning                                                                                      |
|---------------|----------------------------------------------------------------------------------------------|
| `Installing`  | The control plane has not worked yet.                                                        |
| `Available`   | The readiness probe passes and the workload pods are settled.                                |
| `Degraded`    | It answers every request while a management API or FoundationDB pod is restarting behind it. |
| `Unavailable` | It worked and stopped, which is a different situation from one that never started.           |

`status.components` names which component is short when the phase is `Degraded`, and `status.message` carries the
reason. The storage plane is not touched until the phase is `Available`.

```bash title="Waiting for the control plane to become available"
kubectl wait --for=jsonpath='{.status.phase}'=Available \
    controlplane/simplyblock -n simplyblock --timeout=10m
```

## Upgrading the Storage Plane

Which image a storage node runs is decided by three fields. All of them accept only the trusted simplyblock
registries, and pinning by digest is recommended.

| Field                                    | Applies to                                            | Default                   |
|------------------------------------------|-------------------------------------------------------|---------------------------|
| `StorageCluster.spec.storageNodes.image` | The storage-node pod of every node in the cluster.    | `ControlPlane.spec.image` |
| `StorageNode.spec.config.spdkImage`      | The SPDK image, sent with the node-add request.       | The control plane default |
| `StorageNode.spec.config.spdkProxyImage` | The SPDK proxy image, sent with the node-add request. | The control plane default |

The storage-node pod image is cluster-uniform by construction: the pods come from one DaemonSet, and a DaemonSet's
pod template cannot differ per node. What can differ is what a `StorageNode` carries in `spec.config` — the two SPDK
images, the SPDK system memory, and the sizing block — which is per node precisely so that an image rollout can walk
the fleet one machine at a time.

A cluster that leaves `spec.storageNodes.image` empty inherits the image from the `ControlPlane` resource, which the
chart keeps up to date. On such a cluster the chart upgrade already changed the image, and the DaemonSet rolls its
pods as a consequence.

A cluster that pins `spec.storageNodes.image` does not follow the chart. Its image is raised explicitly.

```bash title="Pinning a new storage-node image on the cluster"
kubectl patch storagecluster simplyblock-cluster -n simplyblock --type=merge \
    -p '{"spec": {"storageNodes": {"image": "quay.io/simplyblock-io/simplyblock:26.4.0"}}}'
```

`spdkImage` and `spdkProxyImage` are read when a storage node is added, so a change to them governs nodes added from
that point on.

```bash title="Reading the images a cluster and a node are configured with"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{.spec.storageNodes.image}{"\n"}'
kubectl get storagenode simplyblock-node-mejue8 -n simplyblock \
    -o jsonpath='{.spec.config.spdkImage}{"\n"}{.spec.config.spdkProxyImage}{"\n"}'
```

### Rolling the Change Across the Nodes

A new image does not reach a running storage node on its own. The node has to be restarted, and the storage-node pod
has to be replaced so that it picks the image up rather than keeping the one it started with.

Both happen in a [Rolling Restart](rolling-restart.md) with the pod refresh enabled. One node at a time is shut down,
its pod is replaced, the node is restarted, and the cluster rebalances before the next node follows.

```bash title="Rolling the new image across the storage nodes"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageClusterOps
metadata:
  name: upgrade-rollout
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  action: RollingRestart
  rollingRestart:
    refreshSNodeAPI: true
EOF
```

```bash title="Following the rollout"
kubectl get storageclusterops upgrade-rollout -n simplyblock \
    -o jsonpath='{.status.phase}{"\t"}{.status.step.state}{"\t"}{.status.rollingRestart.nodeIndex}{"\n"}' -w
```

The rollout is complete when `status.phase` is `Succeeded`. The operation stays afterward as the record of what was
rolled and when, and nothing has to be cleared.

### Upgrading a Subset of Nodes First

A new SPDK image can be tried on a few nodes before the whole fleet follows, because `spec.config` is per node.

```bash title="Example of a phased rollout to two nodes"
kubectl patch storagenode simplyblock-node-mejue8 -n simplyblock --type=merge \
    -p '{"spec": {"config": {"spdkImage": "quay.io/simplyblock-io/spdk:26.4.0"}}}'
kubectl patch storagenode simplyblock-node-k2p4x1 -n simplyblock --type=merge \
    -p '{"spec": {"config": {"spdkImage": "quay.io/simplyblock-io/spdk:26.4.0"}}}'
```

The storage-node pod image cannot be staged this way: it comes from one DaemonSet and is the same on every node of
the cluster.

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
