---
title: "Upgrading a Cluster"
description: "Upgrade a simplyblock deployment on Kubernetes to the next release, with the chart's upgrade Jobs or step by step from the CRDs to the storage plane."
weight: 10130
---

A simplyblock deployment on Kubernetes upgrades in a fixed order. The CRDs of the new release are applied first, then
the Simplyblock Operator is upgraded with Helm, then the control plane with a `ControlPlaneOps` operation, and last the
storage plane, one storage node at a time with a rolling restart. Some releases need a few extra steps on top of that
order. Those are listed on the [upgrade notes](../../../upgrades/index.md) of the release, and each one has to be read
for every release an upgrade crosses.

A control plane that is newer than its storage planes is the only combination supported during the transition. The
control plane is therefore upgraded before the storage plane, and a control plane that manages several storage
clusters is upgraded before any of them.

The whole sequence runs either from the chart, as two Jobs that `helm upgrade` creates, or step by step. Both run the
same steps, and the chart's Jobs are the same commands as the step-by-step procedure below.

## Before Starting

An upgrade starts from a healthy deployment, because a cluster that is already absorbing a failure should not also
absorb an upgrade.

- Every `StorageCluster` is `Online`, and every `StorageNode` is `Online`.
- No `StorageClusterOps`, `StorageNodeOps`, or `ControlPlaneOps` is `Pending` or `Running`.
- The [upgrade notes](../../../upgrades/index.md) of every release between the running one and the target are read,
  and anything they ask to be done on the running release is done.

```bash title="Checking that the deployment is healthy"
kubectl get storageclusters,storagenodes -n simplyblock
kubectl get storageclusterops,storagenodeops,controlplaneops -n simplyblock
```

The chart is taken from the simplyblock Helm repository.

```bash title="Adding the simplyblock Helm repository"
helm repo add simplyblock https://install.simplyblock.io/helm
helm repo update
```

## Upgrading with the Chart's Upgrade Jobs

With `upgrade.enabled` set, `helm upgrade` runs the whole upgrade:

1. A pre-upgrade hook Job, `simplyblock-upgrade-prepare`, runs the checks of the target release and applies its CRDs
   before Helm changes anything. If a check fails, `helm upgrade` fails, nothing has changed, and the Job's log says
   which check refused the upgrade and how to fix it.
2. Helm upgrades the operator, the CSI driver, and the storage-node agents.
3. A Job named for the target release, `simplyblock-upgrade-<version>`, upgrades the control plane, then rolls each
   storage cluster onto the new images, one cluster after the other, and runs the steps the upgrade notes describe.
   `helm upgrade` returns before it finishes, because a rolling restart of a large cluster takes hours.

```bash title="Upgrading with the chart's upgrade Jobs"
helm upgrade simplyblock-operator simplyblock/simplyblock-operator \
    -n simplyblock --version <version> --reuse-values --set upgrade.enabled=true
```

```bash title="Following the rollout"
kubectl logs -n simplyblock -f job/simplyblock-upgrade-<version-with-dashes>
kubectl get controlplaneops,storageclusterops -n simplyblock -w
```

`--reuse-values` keeps the values the release was installed with. Without it, every value that was set at install time
falls back to the chart default, which silently reverts settings such as the TLS configuration.

The rollout keeps no state of its own. Every step creates an operation named for the target release, such as
`upgrade-<version>` for the control plane and `upgrade-<version>-<cluster>-restart` for a cluster's rolling restart, and
a step whose operation already succeeded is skipped. A pod of the Job that dies is replaced and continues where the
last one stopped. When an operation fails, the rollout stops with its message. Once the cause is fixed, the failed
operation is deleted, and the Job is deleted so that the next `helm upgrade` to the same version creates it again.

With `upgrade.enabled` set, `helm upgrade` no longer moves the control-plane image itself: the chart renders the image
the `ControlPlane` already runs, and only the rollout's `ControlPlaneOps` changes it.

| Value                     | Default | Description                                                                                                                                                                                                    |
|---------------------------|---------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `upgrade.enabled`         | `false` | Runs the upgrade from the chart.                                                                                                                                                                               |
| `upgrade.rollout.enabled` | `true`  | `false` runs only the pre-upgrade hook, for a deployment that upgrades the control plane and the storage plane in its own maintenance window, with the steps below.                                            |
| `upgrade.skip`            | `[]`    | Identities of checks or steps to skip, for a finding that was looked at and accepted. Every skipped rule is reported.                                                                                          |
| `upgrade.spdkImage`       | `""`    | The SPDK image the new control plane uses by default. When set, the rollout waits for every cluster to report exactly it before rolling. When empty, it waits a settle period after the control-plane upgrade. |

## Upgrading Step by Step

The step-by-step procedure is the same sequence, run by hand. It is the procedure for an OLM-installed operator, for a
GitOps controller that renders the chart without hooks, and for anyone who wants to watch each step. The
`simplyblock-upgrade` tool of the target release runs Steps 1 and 2, and Steps 4 to 7 as a single command. Every
step also has a plain `kubectl` or `helm` form.

### Step 1: Run the Checks

```bash title="Listing what the upgrade will do"
simplyblock-upgrade release plan -n simplyblock
```

```bash title="Running the checks, changing nothing"
simplyblock-upgrade release preflight -n simplyblock
```

The tool reads the running release from the operator's Helm release and takes its own release as the target. Without a
Helm release, `--from <version>` names the running one. A finding of severity `ERROR` refuses the upgrade, and a
`WARNING` names something to check by hand.

### Step 2: Apply the CRDs

`helm upgrade` does not update the CRDs of a chart, so they are applied first. `release prepare` runs the checks again
and applies the CRDs the tool carries, which are the target release's.

```bash title="Applying the CRDs with the upgrade tool"
simplyblock-upgrade release prepare -n simplyblock
```

Without the tool, the CRDs of the target chart are applied with a server-side apply. `--force-conflicts` is needed
because Helm owns the fields it wrote at install.

```bash title="Applying the CRDs of the target chart without the tool"
helm show crds simplyblock/simplyblock-operator --version <version> \
    | kubectl apply --server-side --force-conflicts -f -
```

!!! danger
    A CRD is never deleted to be recreated. Deleting a CRD deletes every resource of its kind in the whole
    Kubernetes cluster, including every `StorageCluster` and `StorageNode`.

### Step 3: Upgrade the Operator

```bash title="Upgrading the Helm release"
helm upgrade simplyblock-operator simplyblock/simplyblock-operator \
    -n simplyblock --version <version> --reuse-values --no-hooks
```

`--no-hooks` keeps Helm from running the pre-upgrade hook, which only repeats Step 2. With `--reuse-values`, the
control-plane image value stays at the running release, so this step does not move the control plane: Step 4 does.

!!! warning
    Without `upgrade.enabled`, the chart writes `spec.source.local.image` of `ControlPlane/simplyblock` from the values
    `image.simplyblock.repository` and `image.simplyblock.tag`. A chart upgrade that changes this image moves the
    control plane directly, without the drain and the verification of an `Upgrade` operation, and a chart upgrade that
    states an older image moves it back. The tag is raised in the values only after Step 4, to the version the control
    plane runs by then.

### Step 4: Upgrade the Control Plane

The control plane is upgraded with a `ControlPlaneOps` that names the `ControlPlane` singleton and the new image. It
is available only for a control plane that the operator installed (`spec.source.local`). A managed control plane is
upgraded from the hub that runs it.

```yaml title="Example of a control plane upgrade (upgrade-control-plane.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ControlPlaneOps
metadata:
  name: upgrade-control-plane
  namespace: simplyblock
spec:
  controlPlaneRef: simplyblock
  action: Upgrade
  upgrade:
    image: quay.io/simplyblock-io/simplyblock:<version>
```

```bash title="Requesting the control plane upgrade"
kubectl apply -f upgrade-control-plane.yaml
kubectl get controlplaneops upgrade-control-plane -n simplyblock -w
```

| Step        | Description                                                                                                      |
|-------------|------------------------------------------------------------------------------------------------------------------|
| `Preflight` | Checks that the control plane is `Available` and does not already run the requested image.                       |
| `Draining`  | Waits until no cluster, node, or pool operation is running in the namespace, with an `OperationsInFlight` event. |
| `Applying`  | Writes the new image into `spec.source.local.image`, which rolls the control-plane workloads.                    |
| `Awaiting`  | Waits for the rollout to become ready.                                                                           |
| `Verifying` | Compares the version the control plane reports with the requested image.                                         |

Once the operation succeeds, the image value of the Helm release is raised to match, so a later `helm upgrade` does not
move the control plane back.

```bash title="Raising the control-plane image in the Helm values"
helm upgrade simplyblock-operator simplyblock/simplyblock-operator \
    -n simplyblock --version <version> --reuse-values --no-hooks \
    --set image.simplyblock.tag=<version>
```

### Step 5: Roll the Storage Plane

Every storage node has desired SPDK images, and the `Images` column of `kubectl get storagenodes` shows whether the
node runs them. A node's desired SPDK image is the first that is set of:

1. `StorageNode.spec.config.spdkImage`, an override for that node.
2. `StorageCluster.spec.storageNodes.spdkImage`, for every node of the cluster.
3. The default SPDK image of the control plane, which `StorageCluster.status.defaultSpdkImage` shows.

The SPDK proxy image resolves the same way from the `spdkProxyImage` fields. A cluster that sets neither follows its
control plane, so the control-plane upgrade of Step 4 already changed the desired images of its nodes. Every restart
the operator asks for starts the node on its desired images.

```bash title="Listing which nodes do not run their desired images yet"
kubectl get storagenodes -n simplyblock \
    -o custom-columns=NAME:.metadata.name,CURRENT:.status.imagesCurrent,RUNS:.status.spdkImage,WANTS:.status.desiredSpdkImage
```

A [Rolling Restart](rolling-restart.md) with `selection: OutOfDate` restarts every node that is not on its desired
images, one at a time, and leaves the others alone. `refreshSNodeAPI` also replaces each node's storage-node pod, so
it runs the new storage-node image when the node comes back.

```yaml title="Example of rolling the new images across the storage nodes (roll-storage-plane.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageClusterOps
metadata:
  name: roll-simplyblock-cluster
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  action: RollingRestart
  rollingRestart:
    refreshSNodeAPI: true
    selection: OutOfDate
```

```bash title="Rolling the storage plane"
kubectl apply -f roll-storage-plane.yaml
kubectl get storageclusterops roll-simplyblock-cluster -n simplyblock -w
```

The rollout of a cluster is complete when the operation reaches the phase `Succeeded`. A walk that stopped can be
started again with a new operation, and it restarts only the nodes it had not reached. A deployment with several
storage clusters rolls them one after the other.

With the upgrade tool, Steps 4 to 7 are a single command, which is what the rollout Job runs.

```bash title="Running the control plane and storage plane steps with the upgrade tool"
simplyblock-upgrade release rollout -n simplyblock \
    --simplyblock-image quay.io/simplyblock-io/simplyblock:<version>
```

### Step 6: Run the Release-Specific Steps

The [upgrade notes](../../../upgrades/index.md) of each release crossed list what has to happen besides this sequence,
and at which point. The upgrade tool runs them at that point. By hand, they are run as each note describes.

### Step 7: Verify the Result

Every storage cluster is `Online` and no longer rebalancing, and every storage node is `Online` on its desired images.

```bash title="Checking the storage nodes after an upgrade"
kubectl get storagenodes -n simplyblock
```

```bash title="Checking that the cluster settled"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
    -o jsonpath='{.status.phase}{" "}{.status.status}{" rebalancing="}{.status.rebalancing}{"\n"}'
```

The CSI driver follows the operator, and its version is reported in `SimplyblockDriver.status.version`.

## Upgrading a Subset of Nodes First

A new SPDK image can be tried on a few nodes before the whole fleet follows. `spec.config.spdkImage` and
`spec.config.spdkProxyImage` of a `StorageNode` override the images for that node only, and the next
[restart](../storage-nodes/restarting-a-storage-node.md) of the node starts it on them.

```bash title="Setting a new SPDK image on one storage node"
kubectl patch storagenode simplyblock-cluster-worker-1-0 -n simplyblock --type=merge \
    -p '{"spec": {"config": {"spdkImage": "quay.io/simplyblock-io/ultra:<version>"}}}'
```

Once the sample has proven itself, the rest of the fleet follows, and the per-node overrides are removed again.

## Rolling Back

A storage-plane image is rolled back the way it was rolled forward: the image field is set to the previous reference,
and the nodes are restarted with a rolling restart of `selection: OutOfDate`. The control plane is rolled back with
another `ControlPlaneOps` of the action `Upgrade` that names the previous image, and the Helm release with
`helm rollback`.

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
    not complete yet, and the procedure will be documented here once it is released. The release upgrade above refuses
    a deployment that still stores `v1alpha1`.
