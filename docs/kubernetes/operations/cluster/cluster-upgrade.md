---
title: "Upgrading a Cluster"
description: "Upgrade the Simplyblock Operator and its CRDs with Helm, move the control plane with a ControlPlaneOps Upgrade, and roll the storage plane node by node."
weight: 10130
---

A simplyblock deployment on Kubernetes upgrades in three parts. The Simplyblock Operator and its CRDs come from the
Helm chart. The control plane is installed by the operator from the `ControlPlane` resource, and it is moved to a new
version with a `ControlPlaneOps` operation. The storage plane runs from the storage-node image of each
`StorageCluster`, and it is rolled node by node with a rolling restart.

A control plane that is newer than its storage planes is the only combination that is supported during the
transition. The control plane is therefore upgraded before the storage plane, and a control plane that manages several
storage clusters is upgraded before any of them.

## Upgrade Order

1. Apply the CRDs of the new chart version.
2. Upgrade the Helm release, which moves the operator.
3. Upgrade the control plane with a `ControlPlaneOps` of the action `Upgrade`, and wait for it to succeed.
4. Roll the new storage-node image across each storage cluster.

## Upgrading the Operator and the CRDs

`helm upgrade` does not update the CRDs of a chart. They are applied from the `crds/` directory of the new chart
version first, with a server-side apply.

```bash title="Applying the CRDs of the new chart version"
helm repo update
helm pull simplyblock/simplyblock-operator --untar --untardir /tmp/simplyblock-chart
kubectl apply --server-side -f /tmp/simplyblock-chart/simplyblock-operator/crds/
```

```bash title="Upgrading the Helm release"
helm upgrade simplyblock-operator simplyblock/simplyblock-operator \
    -n simplyblock --reuse-values
```

`--reuse-values` keeps the values the release was installed with. Without it, every value that was set at install time
falls back to the chart default, which silently reverts settings such as the TLS configuration.

!!! warning
    The chart renders `ControlPlane/simplyblock` and writes `spec.source.local.image` from the values
    `image.simplyblock.repository` and `image.simplyblock.tag`. A chart upgrade that changes this image moves the
    control plane directly, without the drain and the verification of an `Upgrade` operation, and a chart upgrade that
    states an older image moves it back. The image value of the release is therefore kept in line with the version the
    control plane is upgraded to.

## Upgrading the Control Plane

The control plane is upgraded with a `ControlPlaneOps` that names the `ControlPlane` singleton and the new image. It is
available only for a control plane that the operator installed (`spec.source.local`), and the admission webhook refuses
it for a managed control plane.

```yaml title="Example of a control plane upgrade (upgrade-control-plane.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ControlPlaneOps
metadata:
  name: upgrade-control-plane-26-3-0
  namespace: simplyblock
spec:
  controlPlaneRef: simplyblock
  action: Upgrade
  upgrade:
    image: quay.io/simplyblock-io/simplyblock:26.3.0
```

```bash title="Requesting the control plane upgrade"
kubectl apply -f upgrade-control-plane.yaml
kubectl get controlplaneops upgrade-control-plane-26-3-0 -n simplyblock -w
```

| Step        | Description                                                                                                      |
|-------------|------------------------------------------------------------------------------------------------------------------|
| `Preflight` | Checks that the control plane is `Available` and does not already run the requested image.                       |
| `Draining`  | Waits until no cluster, node, or pool operation is running in the namespace, with an `OperationsInFlight` event. |
| `Applying`  | Writes the new image into `spec.source.local.image`, which rolls the control-plane workloads.                    |
| `Awaiting`  | Waits for the rollout to become ready.                                                                           |
| `Verifying` | Compares the version the control plane reports with the requested image.                                         |

A control plane that does not report a version passes `Verifying` as unverified, and the message says so.

```bash title="Waiting for the control plane to become available"
kubectl -n simplyblock wait controlplane simplyblock \
    --for=jsonpath='{.status.phase}'=Available --timeout=600s
```

```bash title="Reading the version the control plane reports"
kubectl get controlplane simplyblock -n simplyblock \
    -o jsonpath='{.status.phase}{" "}{.status.version}{"\n"}'
```

The storage plane is not touched until the control plane is `Available`. The CSI driver follows the operator, and its
version is reported in `SimplyblockDriver.status.version`.

## Upgrading the Storage Plane

Which image a storage node runs is decided by the fields below. All image fields accept only the trusted simplyblock
registries, and pinning by digest is recommended.

| Field                                    | Applies to                                            | Default                                |
|------------------------------------------|-------------------------------------------------------|----------------------------------------|
| `StorageCluster.spec.storageNodes.image` | The storage-node pods of the cluster's DaemonSet.     | `ControlPlane.spec.source.local.image` |
| `StorageNode.spec.config.spdkImage`      | The SPDK image the control plane starts for one node. | The control-plane default              |
| `StorageNode.spec.config.spdkProxyImage` | The SPDK proxy image for one node.                    | The control-plane default              |

A cluster that leaves `spec.storageNodes.image` empty follows the image of the `ControlPlane`, so the control plane
upgrade already changed its storage-node image. A cluster that pins the field does not follow the control plane, and
its image is raised explicitly.

```bash title="Setting a new storage-node image on a cluster"
kubectl patch storagecluster simplyblock-cluster -n simplyblock --type=merge \
    -p '{"spec": {"storageNodes": {"image": "quay.io/simplyblock-io/simplyblock:26.3.0"}}}'
```

### Rolling the Change Across the Nodes

A new image does not reach a running backend storage node on its own. The node has to be restarted, and its
storage-node pod has to be replaced so that it runs the current image. Both happen in a
[Rolling Restart](rolling-restart.md) with `refreshSNodeAPI` enabled: one node at a time is shut down, its pod is
replaced, the node is restarted, and the cluster rebalances before the next node follows.

```yaml title="Example of rolling the new image across the storage nodes"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageClusterOps
metadata:
  name: roll-simplyblock-cluster-26-3-0
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  action: RollingRestart
  rollingRestart:
    refreshSNodeAPI: true
```

The rollout is complete when the operation reaches the phase `Succeeded`.

### Upgrading a Subset of Nodes First

A new SPDK image can be tried on a few nodes before the whole fleet follows. `spec.config.spdkImage` and
`spec.config.spdkProxyImage` of a `StorageNode` override the images for that node only, and a
[restart](../storage-nodes/restarting-a-storage-node.md) of the node picks the change up.

```bash title="Setting a new SPDK image on one storage node"
kubectl patch storagenode simplyblock-cluster-worker-1-0 -n simplyblock --type=merge \
    -p '{"spec": {"config": {"spdkImage": "quay.io/simplyblock-io/spdk:26.3.0"}}}'
```

Once the sample has proven itself, the rest of the fleet follows, and the per-node overrides are removed again.

## Verifying the Result

The storage nodes are online and healthy after a rollout, and the cluster is no longer rebalancing.

```bash title="Checking the storage nodes after an upgrade"
kubectl get storagenodes -n simplyblock
```

```bash title="Checking that the cluster settled"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status.phase}{" "}{.status.status}{" rebalancing="}{.status.rebalancing}{"\n"}'
```

## Rolling Back

A storage-plane image is rolled back the way it was rolled forward: the field is set to the previous reference, and
the nodes are restarted again. The control plane is rolled back with another `ControlPlaneOps` of the action `Upgrade`
that names the previous image, and the Helm release with `helm rollback`.

```bash title="Rolling the Helm release back to the previous revision"
helm rollback simplyblock-operator -n simplyblock
```

!!! warning
    A rollback of the control plane below the version of a storage plane leaves the deployment in the one combination
    that is not supported. The storage planes are rolled back first, and the control plane after them.

## Upgrading from the v1alpha1 API

!!! info "Coming soon"
    Deployments installed with an operator that stored its resources at `storage.simplyblock.io/v1alpha1` move to
    `v1alpha2` with the separate `simplyblock-upgrade` tool. It runs a read-only preflight, installs the conversion
    webhook and the new CRDs, hands the release over, and migrates the settings of the retired kinds into their
    `v1alpha2` successors, for example, the storage-node workload into `StorageCluster.spec.storageNodes`. The tool is
    not complete yet, and the procedure will be documented here once it is released.
