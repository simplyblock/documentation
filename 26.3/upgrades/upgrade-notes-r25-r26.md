---
title: "K8s Upgrade With Maintenance Window Upgrade (R25 to R26)"
description: "Maintenance-window procedure to upgrade a Kubernetes cluster from the R25 Helm charts to the R26 Simplyblock Operator, from node shutdown to workload restart."
source: "https://docs.simplyblock.io/latest/upgrades/upgrade-notes-r25-r26/"
---

# K8s Upgrade With Maintenance Window Upgrade (R25 to R26)

This is the maintenance-window procedure only (Steps 1–11). It assumes **Phase 1** (R25.x cluster deployed)
and **Phase 2** (pre-upgrade data, snapshots, clones, and captured baseline state) are complete, and is followed by
**Phase 4** (post-upgrade validation) in the parent guide.

**This is a maintenance window: client I/O is interrupted from Step 2 (storage nodes shut down) until Step 10.1 (cluster
active, health checks passing).** Read the whole document before starting.

## Maintenance Window Upgrade (R25 to R26)

!!! warning
    Storage nodes are shut down during this phase. Volumes are unavailable to workloads. Plan for downtime and notify teams.

### Step 1: Ensure FDB Resources Have `helm.sh/resource-policy: keep` in Chart

There are 9 resources that must survive `helm uninstall`: 8 FDB resources, plus the old Prometheus ConfigMap (needed in
Step 6.0.1 below):

| Kind                | Name                                                 |
|---------------------|------------------------------------------------------|
| Deployment          | simplyblock-fdb-controller-manager                   |
| ServiceAccount      | simplyblock-fdb-controller-manager                   |
| ClusterRole         | simplyblock-fdb-manager-role                         |
| ClusterRole         | simplyblock-fdb-manager-clusterrole                  |
| RoleBinding         | simplyblock-fdb-manager-rolebinding                  |
| ClusterRoleBinding  | simplyblock-fdb-manager-clusterrolebinding           |
| FoundationDBCluster | simplyblock-fdb-cluster                              |
| ConfigMap           | simplyblock-fdb-cluster-config                       |
| ConfigMap           | `<sbcli-release-name>`-simplyblock-prometheus-config |

!!! info "Why the ConfigMap?"
    The `simplyblock-fdb-cluster-config` ConfigMap contains the FDB cluster connection file. Admin pods mount it as
    volume `fdb-cluster-file`. If this ConfigMap is deleted during `helm uninstall sbcli`, admin pods will be stuck in
    `ContainerCreating` and all `sbcli`/`sbctl` commands will fail.

!!! info "Why the Prometheus ConfigMap?"
    The R25 `sbcli` chart's Prometheus ConfigMap (e.g., `sbcli-simplyblock-prometheus-config`) holds the cluster's
    monitoring `basic_auth` credentials. The R26 operator chart creates its own fresh ConfigMap
    (`simplyblock-prometheus-config`) with empty username/password. If the old ConfigMap is deleted on
    `helm uninstall`, there is nowhere left to read the old credentials from, and Step 6.0.1 (migrate them into the new
    ConfigMap) has nothing to migrate.

!!! danger "`kubectl annotate` on live resources is NOT effective for `helm uninstall`"
    Helm reads annotations from its stored release manifest (in `sh.helm.release.v1.*` secrets), not from the live
    object in etcd. Annotating a live resource with `kubectl annotate` only patches etcd. Helm's copy is unchanged and
    it will still delete the resource on uninstall.

    The correct approach is to add `helm.sh/resource-policy: keep` directly in the Helm chart templates so it is baked
    into the stored manifest. This requires a chart change and a `helm upgrade` before uninstall.

#### Option A: Chart Template Fix (Correct Way, Requires Chart Change)

Add to each FDB template in the chart:

```yaml title="Example of the keep annotation on an FDB chart template"
metadata:
  annotations:
    "helm.sh/resource-policy": keep
```

Then run `helm upgrade` to persist the annotation into Helm's release secret before
running `helm uninstall`.

#### Option B: Patch the Helm Release Secret Directly (Workaround Without Chart Change)

If the chart cannot be modified (e.g., when upgrading from an older R25 chart), the stored Helm release manifest can be
patched directly:

```bash title="Patching the stored Helm release manifest of the sbcli release"
# 1. Get the latest Helm release secret
SECRET_NAME=$(kubectl get secrets -n simplyblock -l owner=helm,name=sbcli \
    --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')

# 2. Decode, decompress, patch, recompress, re-encode the release data
kubectl get secret "$SECRET_NAME" -n simplyblock -o jsonpath='{.data.release}' \
    | base64 -d | base64 -d | gzip -d > /tmp/helm-release.json

# 3. Inject keep annotation into FDB resource manifests in the release
# (This is complex — use the chart fix if possible)
```

#### Option C: `kubectl annotate` Live Resources (Limited Effectiveness)

!!! warning
    This only works if Helm happens to check live objects, which standard Helm does NOT do. Listed here for reference,
    but **Option A is strongly recommended**.

```bash title="Annotating the live FDB resources with the keep policy"
kubectl annotate deployment simplyblock-fdb-controller-manager -n simplyblock \
    helm.sh/resource-policy=keep --overwrite
kubectl annotate serviceaccount simplyblock-fdb-controller-manager -n simplyblock \
    helm.sh/resource-policy=keep --overwrite
kubectl annotate clusterrole simplyblock-fdb-manager-role \
    helm.sh/resource-policy=keep --overwrite
kubectl annotate clusterrole simplyblock-fdb-manager-clusterrole \
    helm.sh/resource-policy=keep --overwrite
kubectl annotate rolebinding simplyblock-fdb-manager-rolebinding -n simplyblock \
    helm.sh/resource-policy=keep --overwrite
kubectl annotate clusterrolebinding simplyblock-fdb-manager-clusterrolebinding \
    helm.sh/resource-policy=keep --overwrite
kubectl annotate foundationdbcluster simplyblock-fdb-cluster -n simplyblock \
    helm.sh/resource-policy=keep --overwrite
kubectl annotate configmap simplyblock-fdb-cluster-config -n simplyblock \
    helm.sh/resource-policy=keep --overwrite
```

The result is verified against Helm's stored manifest, not just against the live object:

```bash title="Checking the resource policy on the live object"
# Check live object (may not reflect what Helm sees)
kubectl get deployment simplyblock-fdb-controller-manager -n simplyblock \
    -o jsonpath='{.metadata.annotations.helm\.sh/resource-policy}'
# Expected: keep
```

```bash title="Checking the resource policy in Helm's stored manifest"
# Check Helm's stored manifest (this is what actually matters)
helm get manifest sbcli -n simplyblock 2>/dev/null | grep -A5 "simplyblock-fdb-controller-manager" | grep resource-policy
# Expected: "helm.sh/resource-policy": keep
```

### Step 2: Shut Down All Storage Nodes

Force-shutdown each storage node. Using `--force` combines suspend and shutdown in one
command and avoids failures when some nodes are already in a non-online state:

```bash title="Force-shutting down every storage node"
for NODE_ID in $(sbctl sn list | grep -v "offline" | awk '{print $2}'); do
    sbctl sn shutdown "$NODE_ID" --force
done
```

Wait for all nodes to reach `offline`:

```bash title="Listing the storage nodes to confirm they are offline"
sbctl sn list
# Expected: All nodes show "offline" status
```

### Step 2.1: Disable Auto-Restart on All Nodes (Safety Net)

!!! note "Status"
    The R26 operator now skips creating `node_restart` tasks for nodes that were already offline before the operator
    started. This makes Step 2.1 optional in most cases. However, when an older R26 build is the upgrade target, or if
    the fix regresses, this step prevents the operator's tasks-runner from creating stale `node_restart` tasks that
    block the explicit `sn restart` in Step 10 (there is no `--force` flag for restart).

```bash title="Disabling the automatic restart on every storage node"
for NODE_ID in $(sbctl sn list --json | jq -r '.[].UUID'); do
    sbctl --dev sn set "$NODE_ID" auto_restart_disabled true
done
```

If stale restart tasks already exist (e.g., from a previous failed run), cancel
them before proceeding:

```bash title="Listing the tasks of the cluster"
# List tasks
sbctl cluster list-tasks "$CLUSTER_ID" --limit 0
```

```bash title="Canceling the running and new node_restart tasks"
# Cancel any running/new node_restart tasks
for TASK_ID in $(sbctl cluster list-tasks "$CLUSTER_ID" --json --limit 0 \
    | jq -r '.[] | select(.function=="node_restart" and (.status=="running" or .status=="new")) | .id'); do
    sbctl cluster cancel-task "$CLUSTER_ID" "$TASK_ID"
done
```

### Step 3: Uninstall the `spdk-csi` Helm Chart

```bash title="Uninstalling the spdk-csi Helm chart"
helm uninstall spdk-csi --namespace simplyblock --wait
```

### Step 3.1: Delete Orphaned Snapshot Controller

The `spdk-csi` chart deploys a `simplyblock-snapshot-controller` Deployment in
`kube-system` with `helm.sh/resource-policy: keep`. This means it survives the
`helm uninstall` above but retains stale ownership annotations pointing to the
old `spdk-csi` release. When the new `simplyblock-operator` chart tries to
install its own copy, Helm fails with:

```plain title="Example output of the resource conflict on the operator install"
rendered manifests contain a resource that already exists. Unable to continue
with install: existing resource conflict: namespace: kube-system, name:
simplyblock-snapshot-controller, existing_kind: apps/v1, Kind=Deployment,
new_kind: apps/v1, Kind=Deployment
```

The orphaned deployment is deleted after `spdk-csi` has been uninstalled:

```bash title="Deleting the orphaned snapshot controller"
kubectl delete deployment simplyblock-snapshot-controller -n kube-system --ignore-not-found
```

### Step 4: Uninstall the `sbcli` Helm Chart

```bash title="Uninstalling the sbcli Helm chart"
helm uninstall sbcli --namespace simplyblock --wait
```

FDB resources survive because the chart templates include `helm.sh/resource-policy: keep`
annotations (see Step 1). If the chart does NOT have these annotations, FDB will be
deleted by `helm uninstall` and the database will be destroyed.

!!! danger "Verify FDB is still running"
    This is critical. If any of the four checks below fails, the procedure is stopped and the cause is investigated.

```bash title="Checking that the FoundationDBCluster CR still exists"
# 1. FoundationDBCluster CR must still exist
kubectl get foundationdbcluster simplyblock-fdb-cluster -n simplyblock
# Expected: Shows the cluster resource
```

```bash title="Checking that the FDB controller-manager deployment still exists"
# 2. FDB controller-manager deployment must still exist
kubectl get deployment simplyblock-fdb-controller-manager -n simplyblock
# Expected: Shows the deployment
```

```bash title="Checking that the FDB pods are still running"
# 3. FDB pods must still be running
kubectl get pods -n simplyblock -l foundationdb.org/fdb-cluster-name=simplyblock-fdb-cluster
# Expected: Multiple FDB pods in Running state
```

```bash title="Checking that the FDB CRDs still exist"
# 4. FDB CRDs must still exist
kubectl get crd foundationdbclusters.apps.foundationdb.org
# Expected: Shows the CRD
```

!!! warning "If FDB resources are missing"
    The chart likely does not have `helm.sh/resource-policy: keep` in its templates. This must be fixed in the chart
    (see Step 1, Option A). Note that `kubectl annotate` on live objects does NOT protect against `helm uninstall`,
    because Helm reads from its stored release manifest, not from etcd.

### Step 4.1: Verify FDB Cluster-Config ConfigMap

Check that the `simplyblock-fdb-cluster-config` ConfigMap survived the Helm uninstall.
Admin pods mount this ConfigMap as volume `fdb-cluster-file`, and without it they will be
stuck in `ContainerCreating`.

```bash title="Checking that the FDB cluster-config ConfigMap survived"
kubectl get configmap simplyblock-fdb-cluster-config -n simplyblock
```

If the ConfigMap is missing, it is recreated from a running FDB pod:

```bash title="Recreating the FDB cluster-config ConfigMap from a running FDB pod"
# Extract the cluster file content from any FDB pod
FDB_POD=$(kubectl get pods -n simplyblock \
    -l foundationdb.org/fdb-cluster-name=simplyblock-fdb-cluster \
    -o jsonpath='{.items[0].metadata.name}')

CLUSTER_FILE=$(kubectl exec -n simplyblock "$FDB_POD" -- \
    cat /var/dynamic-conf/fdb.cluster 2>/dev/null)

# Recreate the ConfigMap
kubectl create configmap simplyblock-fdb-cluster-config \
    -n simplyblock \
    --from-literal=cluster-file="$CLUSTER_FILE"
```

```bash title="Verifying the content of the FDB cluster-config ConfigMap"
kubectl get configmap simplyblock-fdb-cluster-config -n simplyblock \
    -o jsonpath='{.data.cluster-file}'
# Expected: A non-empty FDB cluster connection string
```

### Step 5: Create the Upgrade Secret

The upgrade secret tells the operator to adopt the existing cluster instead of creating a new one.

```bash title="Creating the upgrade secret for the existing cluster"
kubectl create secret generic simplyblock-<CLUSTER_CR_NAME>-upgrade \
    --namespace simplyblock \
    --from-literal=uuid=<CLUSTER_UUID> \
    --from-literal=secret=<CLUSTER_SECRET>
```

```bash title="Example of the upgrade secret with the values filled in"
kubectl create secret generic simplyblock-simplyblock-cluster-upgrade \
    --namespace simplyblock \
    --from-literal=uuid=93cdb610-3a72-464c-b223-fe48327fc329 \
    --from-literal=secret=bdMyLkU5k4H0btBZU5H
```

!!! warning
    The secret name **must** match `simplyblock-<CR_NAME>-upgrade`, where `CR_NAME` is the `metadata.name` of the
    StorageCluster CR applied in Step 7.

### Step 6: Install the Operator Helm Chart (FDB Disabled)

!!! warning "Prerequisite: cert-manager (TLS-enabled installs only)"
    If the operator chart enables TLS (e.g., `simplyblock-webappapi-tls` Certificate resources), `cert-manager`
    must be installed before this step. Without it, Certificate CRDs will not exist and the
    Helm install will fail, or the TLS secret will never be created and admin pods will
    fail to start.

    ```bash title="Checking whether the cert-manager CRDs exist"
    # Check if cert-manager CRDs exist
    kubectl get crd certificates.cert-manager.io 2>/dev/null
    ```

    If they are missing, cert-manager is installed from the Jetstack Helm chart at a pinned version. The automated
    test uses this path, not the raw upstream manifest, to avoid drift from an unpinned "latest" release.

    ```bash title="Installing cert-manager from the Jetstack Helm chart"
    helm repo add jetstack https://charts.jetstack.io
    helm repo update
    helm upgrade --install cert-manager jetstack/cert-manager \
        --namespace cert-manager --create-namespace \
        --version v1.13.0 --set installCRDs=true
    kubectl wait --for=condition=Ready pods --all -n cert-manager --timeout=120s
    ```

    If cert-manager was left in a broken state by a previous failed attempt,
    `helm uninstall cert-manager -n cert-manager --no-hooks --timeout 60s` is run and the install is retried. A stale
    release can make the install above fail silently.

!!! danger "Apply CRDs explicitly before `helm upgrade --install` on a reused cluster"
    Helm v3 only installs CRDs from a chart's `crds/` directory on a fresh `helm install`.
    If a `simplyblock-operator` release already exists on this cluster (e.g., a previous failed
    upgrade attempt), `helm upgrade --install` performs an **upgrade**, and Helm **silently skips
    all CRD installation**. Any CRD added to the chart since the original install (e.g.,
    `StoragePool`) is never registered. The operator then has nothing to reconcile, no
    `StorageNodeSet` DaemonSet is created, and every node restart in Step 10 fails waiting for an
    agent that was never scheduled. Apply the CRDs directly first, regardless of install vs. upgrade:

    ```bash title="Applying the operator CRDs before the Helm install"
    kubectl apply --server-side --force-conflicts -f ./charts/simplyblock-operator/crds/
    ```

Install the new operator chart with FDB creation disabled (FDB is already running):

```bash title="Installing the Simplyblock Operator chart with FDB creation disabled"
helm upgrade --install simplyblock-operator ./charts/simplyblock-operator \
    --namespace simplyblock \
    --timeout 10m \
    --set operator.enabled=true \
    --set controlplane.foundationdb.enabled=false \
    --set image.simplyblock.repository=<TARGET_REPO> \
    --set image.simplyblock.tag=<TARGET_TAG> \
    --set image.operator.repository=simplyblock/simplyblock-operator \
    --set image.operator.tag=<OPERATOR_TAG> \
    --set controlplane.csiHostpathDriver.enabled=true \
    --set controlplane.storageclass.name=local-hostpath \
    --set csiConfig.simplybk.ip=http://simplyblock-webappapi.simplyblock:5000
```

Wait for operator pods:

```bash title="Waiting for the operator pods to become ready"
kubectl wait --for=condition=Ready pods --all -n simplyblock \
    --timeout=300s --field-selector=status.phase!=Succeeded
```

### Step 6.0.1: Migrate Prometheus Credentials to the New ConfigMap

!!! info "Why"
    The new operator chart's Prometheus ConfigMap is created fresh with an empty
    `basic_auth` username/password, while the old `sbcli` chart's ConfigMap (kept in Step 1)
    still has the real credentials. The new chart also switches Prometheus to HTTPS with mTLS,
    so the ConfigMaps cannot simply be swapped. The credentials must be copied across. Skipping
    this step leaves Prometheus running with empty auth post-upgrade.

```bash title="Migrating the Prometheus basic_auth credentials into the new ConfigMap"
OLD_CM=sbcli-simplyblock-prometheus-config   # <sbcli-release-name>-simplyblock-prometheus-config
NEW_CM=simplyblock-prometheus-config

# 1. Extract username/password from the old ConfigMap's basic_auth block
kubectl get configmap "$OLD_CM" -n simplyblock \
    -o jsonpath='{.data.prometheus\.yml}' > /tmp/old-prometheus.yml
# Parse `basic_auth: { username: ..., password: ... }` out of /tmp/old-prometheus.yml

# 2. Inject those values into the new ConfigMap's prometheus.yml (empty username/password
#    fields), then re-apply it
kubectl get configmap "$NEW_CM" -n simplyblock -o json > /tmp/new-cm.json
# Edit /tmp/new-cm.json: set data."prometheus.yml" username/password to the extracted values
kubectl replace -f /tmp/new-cm.json -n simplyblock

# 3. Restart Prometheus to pick up the new config
kubectl delete pod simplyblock-prometheus-0 -n simplyblock --ignore-not-found
```

**Expected**: The Prometheus pod restarts and scrapes successfully using the migrated
credentials. Check `kubectl logs simplyblock-prometheus-0 -n simplyblock` for auth errors.

### Step 6.1: Shut Down Nodes Again (Prevent Auto-Restart)

After the operator installs, it may try to auto-restart nodes. Shut them down again
to explicitly set `auto_restart_disabled=True`:

```bash title="Shutting the storage nodes down again after the operator install"
for NODE_ID in $(sbctl sn list | grep -E "online|in_creation|reaching" | awk '{print $2}'); do
    sbctl --dev sn shutdown "$NODE_ID"
done
```

### Step 7: Apply Custom Resources

Apply the StorageCluster, Pool, and StorageNodeSet CRs. The operator detects the upgrade
secret and adopts the existing cluster.

!!! warning "CR names must match existing backend names"
    - **Pool CR:** The `metadata.name` must match the existing pool name in the R25 cluster. If the pool was created
      as `testing1` via `sbcli-dev pool add testing1`, the Pool CR must use `name: testing1`. This allows the operator
      to adopt the existing pool.
    - **StorageCluster CR:** The `metadata.name` must be consistent with the upgrade secret name from Step 5
      (`simplyblock-<CR_NAME>-upgrade`).

!!! warning "CR schema drift between releases"
    The operator's CRD schema has changed shape across releases. Fields get moved or dropped with strict decoding, so
    a CR generated against an older schema is rejected outright.

    - **StorageCluster:** Does **not** accept `isSingleNode` or `strictNodeAntiAffinity`. It **does** accept
      `maxSubsystemCount` (moved here from `StorageNodeSet`).
    - **StorageNodeSet:** No longer accepts `maxSubsystemCount`.

    A field mismatch fails with `strict decoding error: unknown field "spec.xxx"`. The CR YAML is confirmed against
    the CRD actually installed on the target release before it is applied, rather than reusing a template from a
    previous version's documentation.

!!! warning "Verify CR application without merging stderr into stdout"
    If the automation checks "does this CR exist" via `kubectl get ... 2>&1` and a substring match on the CR name,
    it will get a **false positive**. A `NotFound` error message contains the CR name as a
    substring (`storageclusters.storage.simplyblock.io "simplyblock-cluster" not found`), so the
    check passes even though the CR was never created. Keep stdout and stderr separate and check
    stderr explicitly for `not found` / `could not find the requested resource`, and fail fast on
    `BadRequest` / `strict decoding error` rather than logging a warning and continuing. A CR
    that silently failed to apply here surfaces much later, as an inexplicable node-restart
    timeout in Step 10 with no obvious connection back to this step.

```yaml title="Example of the custom resources of the upgraded cluster (storagecluster.yaml)"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageCluster
metadata:
  name: simplyblock-cluster   # Must match upgrade secret: simplyblock-<name>-upgrade
  namespace: simplyblock
spec:
  fabricType: tcp
  enableNodeAffinity: true
  stripe:
    dataChunks: 1
    parityChunks: 0
  warningThreshold:
    capacity: 95
    provisionedCapacity: 97
  criticalThreshold:
    capacity: 96
    provisionedCapacity: 98
  maxSubsystemCount: 30          # a.k.a. max_lvol, moved here from StorageNodeSet
  vcpuCount: 16                  # SPDK vCPUs to allocate per node (see note below)
---
apiVersion: storage.simplyblock.io/v1alpha1
kind: StoragePool
metadata:
  name: <EXISTING_POOL_NAME>       # Must match the pool name from R25 (e.g., testing1)
  namespace: simplyblock
spec:
  clusterName: simplyblock-cluster
---
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeSet
metadata:
  name: simplyblock-node
  namespace: simplyblock
spec:
  clusterName: simplyblock-cluster
  clusterImage: "<TARGET_REPO>:<TARGET_TAG>"
  spdkImage: "<TARGET_SPDK_IMAGE>"
  spdkProxyImage: "<TARGET_REPO>:<TARGET_TAG>"
  mgmtIfname: ens18
  dataIfname:
    - enp1s0
  skipKubeletConfiguration: false   # true on Talos, the operator cannot edit kubelet config there
  enableCpuTopology: true           # false on Talos, for the same reason
  workerNodes:
    - <worker-node-1>
    - <worker-node-2>
    - <worker-node-3>
```

!!! note "`vcpuCount`, `skipKubeletConfiguration`, and `enableCpuTopology`"
    `vcpuCount` is computed as a percentage of each node's CPU count (e.g., 50% on OpenShift),
    not as a fixed value. Pick a number the operator's CRD will accept for the node sizing at hand rather
    than copying `16` verbatim. On Talos nodes the operator cannot modify kubelet configuration directly, so
    `skipKubeletConfiguration` and `enableCpuTopology` flip relative to a standard OpenShift or vanilla K8s install.
    Detect Talos before deciding the values.

```bash title="Applying the custom resources"
kubectl apply -f storagecluster.yaml -n simplyblock
```

Verify adoption (status should reflect existing UUIDs, not `in_creation`):

```bash title="Verifying the adoption of the existing cluster, nodes, and pool"
kubectl get storagecluster -n simplyblock -o yaml
kubectl get storagenode -n simplyblock -o yaml
kubectl get storagepool -n simplyblock -o yaml
```

### Step 8: Run R25 to R26 Data Migration Script

Run the migration script inside the admin pod to update storage node fields in the database
(`lvstore_ports`, `lvol_poller_mask`, `lvstore_stack_secondary`):

```bash title="Opening a shell in the admin pod"
ADMIN_POD=$(kubectl get pods -n simplyblock -l app=simplyblock-admin \
    -o jsonpath='{.items[0].metadata.name}')

kubectl exec -it -n simplyblock $ADMIN_POD -- bash
```

Inside the pod, run:

```python title="Migration script for the storage node, logical volume, and snapshot objects"
from simplyblock_core import utils
from simplyblock_core.db_controller import DBController
db_controller = DBController()

for snode in db_controller.get_storage_nodes():
    print(f"updating storage node object: {snode.get_id()}")
    for node in db_controller.get_storage_nodes():
        if snode.get_id() == node.secondary_node_id:
            snode.lvstore_stack_secondary = node.get_id()
            break
    snode.lvstore_ports = {
        snode.lvstore: {
            "lvol_subsys_port": snode.lvol_subsys_port,
            "hublvol_port": snode.hublvol.nvmf_port
        }
    }
    if snode.lvstore_stack_secondary:
        sec = db_controller.get_storage_node_by_id(snode.lvstore_stack_secondary)
        snode.lvstore_ports[sec.lvstore] = {
            "lvol_subsys_port": sec.lvol_subsys_port,
            "hublvol_port": sec.hublvol.nvmf_port,
        }
    if snode.poller_cpu_cores:
        snode.lvol_poller_mask = utils.generate_mask([snode.poller_cpu_cores[-1]])
        if len(snode.poller_cpu_cores) > 1:
            snode.poller_cpu_cores = snode.poller_cpu_cores[:-1]
            snode.pollers_mask = utils.generate_mask(snode.poller_cpu_cores)

    snode.write_to_db()

print("Creating mini lvol objects")
for lvol in db_controller.get_all_lvols():
    lvol.write_to_db()

print("Creating mini Snapshots objects")
for snap in db_controller.get_snapshots():
    snap.write_to_db()

print("done")
```

**Expected**: Output ends with `done`. After running, `sbctl sn list` shows `LVS Ports`
column values populated.

### Step 9: Patch Backend Objects with CR References

Register the K8s CR details on each backend object so the operator and backend stay in sync.

**Storage Cluster**:

```bash title="Registering the CR details on the storage cluster"
export CLUSTER_UUID=<CLUSTER_UUID>
export CLUSTER_CR_NAME=simplyblock-cluster

sbctl --dev cluster set $CLUSTER_UUID cr_plural storageclusters
sbctl --dev cluster set $CLUSTER_UUID cr_namespace simplyblock
sbctl --dev cluster set $CLUSTER_UUID cr_name $CLUSTER_CR_NAME
```

**Storage Nodes** (repeat for each):

```bash title="Registering the CR details on every storage node"
for NODE_ID in $(sbctl sn list | grep -E "offline|in_creation" | awk '{print $2}'); do
    sbctl --dev sn set "$NODE_ID" cr_plural storagenodesets
    sbctl --dev sn set "$NODE_ID" cr_namespace simplyblock
    sbctl --dev sn set "$NODE_ID" cr_name simplyblock-node
done
```

!!! note "Provisional"
    The test code carries a TODO that `cr_plural` may need to change from
    `storagenodesets` to `storagenodes` (with `cr_name` set to the individual `StorageNode` CR
    name, not the shared `StorageNodeSet` name) pending confirmation from the operator team.
    Treat the values above as current, not final. Check the operator's actual CR structure on
    the target release before relying on this in a scripted upgrade.

### Step 9.1: Cancel Stale Restart Tasks (If Needed)

!!! note "Status"
    With the R26 operator fix (see Step 2.1), stale tasks should not appear. This step is a safety net for older
    operator builds or regressions.

If any `node_restart` tasks were created by the operator's tasks-runner between
Step 6 (operator install) and Step 10, they will block `sn restart`. Check and
cancel them:

```bash title="Checking for and canceling stale node_restart tasks"
# Check for stale node_restart tasks
sbctl cluster list-tasks "$CLUSTER_ID" --limit 0

# Cancel any that are running or new
for TASK_ID in $(sbctl cluster list-tasks "$CLUSTER_ID" --json --limit 0 \
    | jq -r '.[] | select(.function=="node_restart" and (.status=="running" or .status=="new")) | .id'); do
    echo "Cancelling stale task: $TASK_ID"
    sbctl cluster cancel-task "$CLUSTER_ID" "$TASK_ID"
done
```

### Step 10: Restart Storage Nodes One at a Time

Restart each storage node with the new SPDK image and proxy image.

!!! warning "Maintenance upgrade"
    In a maintenance upgrade all nodes start offline. The cluster **cannot** become `active` until every node is back
    online. Do **not** wait for cluster `active` between individual node restarts. Wait only for each node to reach
    `online`, then proceed to the next. Check cluster `active` only after **all** nodes have been restarted.

```bash title="Restarting the storage nodes one at a time"
export SPDK_IMAGE=<TARGET_SPDK_IMAGE>
export SPDK_PROXY_IMAGE=<TARGET_DOCKER_IMAGE>

for NODE_ID in $(sbctl sn list --json | jq -r '.[].UUID'); do
    echo "Restarting node: $NODE_ID"
    sbctl -d --dev sn restart "$NODE_ID" \
        --spdk-image "$SPDK_IMAGE" \
        --spdk-proxy-image "$SPDK_PROXY_IMAGE"

    # Wait for this node to come online (up to 10 minutes)
    while ! sbctl sn list --json | jq -e ".[] | select(.UUID==\"$NODE_ID\" and .Status==\"online\")" > /dev/null 2>&1; do
        sleep 5
    done
    echo "  Node $NODE_ID is online"

    sleep 10  # brief pause before next node
done
```

!!! note "Admin-control pod recycling"
    During Step 10, the R26 operator may recycle the `simplyblock-admin-control` pods as nodes come back online
    (deployment rollout). If `kubectl exec` commands fail with `error: unable to upgrade connection: pod does not
    exist`, wait a few seconds and retry with the new pod name:

    ```bash title="Resolving the name of the recycled admin-control pod"
    ADMIN_POD=$(kubectl get pods -n simplyblock -l app=simplyblock-admin-control \
        -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    ```

!!! warning "Watch for a restart repeatedly using the wrong SPDK image"
    A run on 2026-08-26 saw a node cycle `offline -> in_restart -> offline` seven times over 43 minutes here.
    `sn restart` was called with `--spdk-image <TARGET>`, but the tasks-runner's `spdk_process_start` call used
    the node's old, stored R25 image instead. The R25 SPDK is incompatible with the already-running
    R26 control plane, so the process never came up and every attempt timed out after 300s. If a
    node does not come online in this step, check `tasks-runner-restart.log` for the `spdk_image`
    value actually sent to `spdk_process_start` and confirm it matches `--spdk-image`, not the
    node's pre-upgrade value. Do not assume repeated identical timeouts here are a transient
    infra issue.

### Step 10.1: Wait for Cluster Active and Health Checks

After all nodes are restarted, wait for the cluster to become `active` and for
all node health checks to settle to `True`. The `health_check` field may
remain `None` or `False` for 30-60 seconds after a node comes online while the
monitoring loop catches up.

```bash title="Waiting for the cluster to become active"
# Wait for cluster active
while [ "$(sbctl cluster list --json | jq -r '.[0].Status')" != "ACTIVE" ]; do
    echo "Waiting for cluster to become active..."
    sleep 10
done
echo "Cluster is active"
```

```bash title="Waiting for the health check of every node to report True"
# Wait for all nodes to report health_check=True (up to 2 minutes)
TIMEOUT=120
while [ $TIMEOUT -gt 0 ]; do
    UNHEALTHY=$(sbctl sn list --json | jq '[.[] | select(.Health != "True")] | length')
    if [ "$UNHEALTHY" -eq 0 ]; then
        echo "All nodes are healthy"
        break
    fi
    echo "  $UNHEALTHY node(s) still settling health_check, retrying in 10s..."
    sleep 10
    TIMEOUT=$((TIMEOUT - 10))
done

if [ $TIMEOUT -le 0 ]; then
    echo "WARNING: Some nodes still have health_check != True after 120s"
    sbctl sn list
fi
```

### Step 11: Restart Workload Pods

Once all storage nodes are online and the cluster is active, restart application
pods to re-establish NVMe connections:

```bash title="Restarting a single workload deployment"
kubectl rollout restart deployment/<workload> -n <namespace>
```

Or for all deployments in a namespace:

```bash title="Restarting all deployments of a namespace"
kubectl get deployments -n <namespace> -o name | \
    xargs -I{} kubectl rollout restart {} -n <namespace>
```
