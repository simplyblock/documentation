---
title: "Expanding a Storage Cluster"
description: "Expanding a Storage Cluster: Simplyblock is designed as an always-on storage solution."
weight: 29001
---

Simplyblock is designed as an always-on storage solution. Hence, storage cluster expansion is an online operation
without a need for maintenance downtime.

However, every operation that changes the cluster topology comes with a set of migration tasks, moving data across
the cluster to ensure equal usage distribution. While these migration tasks are low priority and their overhead is
designed to be minimal, it is still recommended to expand the cluster at times when the storage cluster isn't under
full utilization.

!!! info
    Add storage nodes in **pairs** (i.e., 2, 4, 6, … nodes at a time).  
    Expansions with an odd number of nodes are **not supported**.

To add a new storage node, follow the installation steps for the chosen deployment method up to the point where nodes are added to the cluster, then continue here:

- [Storage nodes in Kubernetes](../../installation/index.md)
- [Storage nodes on Linux](../../../non-kubernetes/installation/install-sp.md)

After adding the **first** new storage node, the cluster transitions to **IN_EXPANSION** and starts background rebalancing.
Add the remaining node(s) required for the expansion (storage nodes must be added in **pairs**).
Once all newly added nodes are healthy/ready, finalize the expansion:

```bash title="Finalize cluster expansion"
{{ cliname }} cluster complete-expand <CLUSTER_ID>
```

After the expansion is complete, the cluster returns to **ACTIVE** and resumes normal operation mode.

## Adding Worker Nodes with the Kubernetes Operator

There are two ways to add nodes when using the Kubernetes operator: via the `StorageNodeSet` (recommended for
adding multiple nodes) or by creating individual `StorageNode` CRs manually (useful for per-node
overrides or want fine-grained control).

---

### Option A: Add Nodes via a New StorageNodeSet (recommended)

Create a separate `StorageNodeSet` for the expansion workers. Setting `spec.expand: true` tells the operator to
register each node as an expansion add rather than a fresh cluster node. This keeps the expansion cleanly
separated from the original set and avoids mutating an existing resource.

**Adding two new nodes:**

```yaml title="expansion-nodeset.yaml — add 2 nodes"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeSet
metadata:
  name: simplyblock-node-expansion
  namespace: simplyblock
spec:
  clusterName: simplyblock-cluster
  expand: true
  maxLogicalVolumeCount: 20
  partitions: 0
  corePercentage: 50
  workerNodes:
    - new-node-4.example.com
    - new-node-5.example.com
```

**Adding four new nodes:**

```yaml title="expansion-nodeset.yaml — add 4 nodes"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeSet
metadata:
  name: simplyblock-node-expansion
  namespace: simplyblock
spec:
  clusterName: simplyblock-cluster
  expand: true
  maxLogicalVolumeCount: 20
  partitions: 0
  corePercentage: 50
  workerNodes:
    - new-node-4.example.com
    - new-node-5.example.com
    - new-node-6.example.com
    - new-node-7.example.com
```

```bash title="Apply the expansion StorageNodeSet"
kubectl apply -f expansion-nodeset.yaml
```

The operator creates `StorageNode` CRs for each new worker, deploys the storage-node DaemonSet, and registers
them with the backend one at a time.

Monitor until all new nodes are online:

```bash title="Watch the expansion StorageNodeSet"
kubectl get storagenodeset simplyblock-node-expansion -n simplyblock -w
```

```bash title="Check individual StorageNode status"
kubectl get storagenodes -n simplyblock
```

---

### Option B: Add a Single Node via StorageNode CR

For cases that need per-node overrides (custom `maxLogicalVolumeCount`, `spdkSystemMemory`, etc.) or a
single node added manually, create a `StorageNode` CR directly. Set `overrides.expand: true` so the backend
treats it as an expansion add rather than a fresh cluster node.

`spec.storageNodeSetRef` must point to the existing `StorageNodeSet` and `spec.workerNode` must match the
Kubernetes node hostname. The CR name is arbitrary.

```yaml title="Add a single expansion node manually"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNode
metadata:
  name: simplyblock-new-node-4-expansion
  namespace: simplyblock
spec:
  storageNodeSetRef: simplyblock-node
  workerNode: new-node-4.example.com
  socketIndex: 0
  overrides:
    expand: true
    maxLogicalVolumeCount: 20
```

```bash title="Apply the StorageNode CR"
kubectl apply -f expansion-node.yaml
```

The operator picks up the new CR and provisions the node. Watch the status:

```bash title="Watch the new node's provisioning status"
kubectl get storagenode simplyblock-new-node-4-expansion \
  -n simplyblock -w
```

!!! note
    The `StorageNode` CR is normally auto-created by the operator when a worker is added to the `StorageNodeSet`.
    Create it manually only for per-node overrides that are not covered by `StorageNodeSet.spec.nodeConfigs`.

---

### Finalizing the Expansion

Once all newly added nodes are online (regardless of which method was used), finalize the expansion:

The backend transitions to **IN_EXPANSION** once the first new node is registered. All new nodes must be online
before finalizing.

```bash title="Finalize expansion via the operator"
kubectl patch storagecluster simplyblock-cluster -n simplyblock \
  --type=merge -p '{"spec": {"action": "expand"}}'
```

Monitor until the cluster returns to `active`:

```bash title="Watch expansion status"
kubectl get storagecluster simplyblock-cluster -n simplyblock \
  -o jsonpath='{.status.status}{"\n"}' -w
```

```plain title="Example output for finalizing cluster expansion"
[demo@demo ~]# {{ cliname }} cluster complete-expand e2cda3fe-e9f2-42ce-bb2d-eecd10f58ccf
2026-02-19 11:28:49,995: 139892426475328: INFO: Connecting to remote_jm_af8d10c1-6613-47a9-8ed0-ebdf1f873738
2026-02-19 11:28:50,133: 139892426475328: INFO: Connecting to remote_jm_e17ffb0c-89aa-496d-98ec-700e58cb831f
2026-02-19 11:28:50,786: 139892426475328: INFO: Connecting to remote_jm_86ccd3d3-378b-4ba1-ba26-a299e168a8cb
2026-02-19 11:28:50,933: 139892426475328: INFO: Connecting to remote_jm_e17ffb0c-89aa-496d-98ec-700e58cb831f
2026-02-19 11:28:51,357: 139892426475328: INFO: Creating hublvol on 86ccd3d3-378b-4ba1-ba26-a299e168a8cb
2026-02-19 11:28:52,467: 139892426475328: INFO: Connecting node af8d10c1-6613-47a9-8ed0-ebdf1f873738 to hublvol on 86ccd3d3-378b-4ba1-ba26-a299e168a8cb
2026-02-19 11:28:52,681: 139892426475328: INFO: Connecting to remote_jm_86ccd3d3-378b-4ba1-ba26-a299e168a8cb
2026-02-19 11:28:52,687: 139892426475328: INFO: Connecting to remote_jm_6bc978d0-84ba-4815-8b25-697cc4de5d5d
2026-02-19 11:28:52,841: 139892426475328: INFO: Connecting to remote_jm_e17ffb0c-89aa-496d-98ec-700e58cb831f
2026-02-19 11:28:53,319: 139892426475328: INFO: Connecting to remote_jm_af8d10c1-6613-47a9-8ed0-ebdf1f873738
2026-02-19 11:28:53,326: 139892426475328: INFO: Connecting to remote_jm_e17ffb0c-89aa-496d-98ec-700e58cb831f
2026-02-19 11:28:53,344: 139892426475328: INFO: Connecting to remote_jm_6bc978d0-84ba-4815-8b25-697cc4de5d5d
2026-02-19 11:28:53,873: 139892426475328: INFO: Creating hublvol on af8d10c1-6613-47a9-8ed0-ebdf1f873738
2026-02-19 11:28:54,953: 139892426475328: INFO: Connecting node 86ccd3d3-378b-4ba1-ba26-a299e168a8cb to hublvol on af8d10c1-6613-47a9-8ed0-ebdf1f873738
2026-02-19 11:28:55,098: 139892426475328: INFO: {"cluster_id": "e2cda3fe-e9f2-42ce-bb2d-eecd10f58ccf", "event": "STATUS_CHANGE", "object_name": "Cluster", "message": "Cluster status changed from in_expansion to active", "caused_by": "cli"}
2026-02-19 11:28:55,100: 139892426475328: INFO: Cluster expanded successfully
True
```
