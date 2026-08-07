---
title: "Automatic Volume Placement"
description: "Reference for the PVC annotations and StorageCluster fields that control which storage node becomes a new volume's primary node."
weight: 40050
---

A new volume's primary storage node is resolved from up to three PVC annotations, evaluated in a
fixed order. If none apply, the storage cluster's built-in default placement is used.

## Resolution Order

| Order | Annotation                                       | Set by                |
|-------|---------------------------------------------------|------------------------|
| 1     | `simplyblock.io/selected-storage-node`             | User                   |
| 2     | `simplyblock.io/placement-hint`                    | Operator (automatic)   |
| 3     | `simplyblock.io/pod-affinity: "true"` (opt-in only) | User                   |
| —     | *(none of the above)*                              | Storage cluster default placement |

## Annotations

| Annotation                                | Type                        | Default | Description                                                                                                              |
|--------------------------------------------|-----------------------------|---------|----------------------------------------------------------------------------------------------------------------------------|
| `simplyblock.io/selected-storage-node`     | string (storage node UUID)  | —       | Pins the volume to a specific storage node. On a new PVC, sets the primary node directly. On a bound PVC, triggers a live migration to the new node. |
| `simplyblock.io/host-id`                  | string (storage node UUID)  | —       | Deprecated alias for `selected-storage-node`. Normalized into it automatically on admission.                             |
| `simplybk/host-id`                        | string (storage node UUID)  | —       | Deprecated legacy prefix for `host-id`. Normalized the same way.                                                          |
| `simplyblock.io/placement-hint`            | string (storage node UUID)  | —       | Written automatically by the operator when load-aware placement selects a node for a new volume. Not user-set, and does not pin the volume. |
| `simplyblock.io/pod-affinity`              | boolean                     | `false` | Opts a PVC into co-location with its consuming Pod's resolved node. Requires a `WaitForFirstConsumer` StorageClass.       |
| `simplyblock.io/disable-smart-placement`   | boolean                     | `false` | Disables load-aware placement for this PVC. Does not affect an explicit pin or `pod-affinity` co-location (those are already opt-in per PVC and need no separate opt-out). |

### `simplyblock.io/selected-storage-node`

```bash title="Pin a new PVC to a specific storage node"
kubectl annotate pvc my-pvc -n simplyblock \
  simplyblock.io/selected-storage-node=4e53efdd-86c9-424f-940c-e437eb6a2e95
```

The value must be a known storage node UUID, found with `{{ cliname }} storage-node list --cluster-id=<CLUSTER_ID>`.
Otherwise, the PVC is rejected by a validating webhook. On an already-bound PVC, a
[migration](../operations/volume-migration.md#migrating-by-pinning-a-pvc) to the new node is triggered by
this annotation instead.

### `simplyblock.io/pod-affinity`

```yaml title="Co-locate a new volume with its consuming Pod"
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: my-pvc
  annotations:
    simplyblock.io/pod-affinity: "true"
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: simplyblock-csi-sc
```

| Requirement                                   | Detail                                                                                    |
|------------------------------------------------|---------------------------------------------------------------------------------------------|
| StorageClass binding mode                      | `WaitForFirstConsumer` (see [Defining a StorageClass](storage-class.md))                    |
| Supported scheduling mechanisms                | `nodeSelector`, node affinity, pod affinity                                                 |
| Not supported                                  | `spec.nodeName` set directly on the Pod ([kubernetes/kubernetes#89953](https://github.com/kubernetes/kubernetes/issues/89953){:target="_blank" rel="noopener"}) |
| Multiple co-located storage nodes on one worker | One is selected at random                                                                    |
| Precedence                                     | Only applies when the volume is not already pinned or covered by a placement hint            |

### `simplyblock.io/disable-smart-placement`

```bash title="Exclude a single PVC from automatic placement"
kubectl annotate pvc my-pvc -n simplyblock \
  simplyblock.io/disable-smart-placement=true
```

Suppresses load-aware placement for this PVC, regardless of cluster-wide configuration. Placement then falls
through to whatever is next in the [resolution order](#resolution-order): an explicit pin, `pod-affinity`
co-location if the PVC also requests it, or the storage cluster's default placement.

## Load-Aware Placement

Load-aware placement for new volumes is controlled by the same `StorageCluster` field that also feeds
[auto-rebalancing's latency benchmark](../operations/volume-migration.md#auto-rebalancing):

| Field                                         | Type   | Default | Description                                                                                              |
|------------------------------------------------|--------|---------|------------------------------------------------------------------------------------------------------------|
| `volumeAutoPlacement.latencyBenchmarkEnabled`  | bool   | `false` | Enables load-aware placement for new volumes, independent of `volumeAutoPlacement.enabled` (continuous rebalancer only). |

```yaml title="Enabling load-aware placement for new volumes"
spec:
  volumeAutoPlacement:
    latencyBenchmarkEnabled: true
    prometheusURL: "http://prometheus.simplyblock.svc:9090"
```

A node is eligible when it is online, passes its health check, and is below its configured logical volume
limit.

## Clones and Snapshot Restores

None of the above applies to a PVC created from a `VolumeSnapshot` or another PVC (`dataSource`). A clone
or restore always uses its source volume's node.
