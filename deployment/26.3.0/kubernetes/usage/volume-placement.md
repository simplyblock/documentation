---
title: "Automatic Volume Placement"
description: "Reference for the PVC annotations and StorageCluster fields that control which storage node becomes a new volume's primary node."
source: "https://docs.simplyblock.io/latest/kubernetes/usage/volume-placement/"
---

# Automatic Volume Placement

**Experimental**{.chip-experimental}

The primary storage node of a new volume is decided when the volume is provisioned. Three mechanisms can
decide it, each driven by a PVC annotation and evaluated in a fixed order. The first mechanism that applies
wins, and the remaining ones are not evaluated. If none applies, the storage cluster's built-in default
placement is used.

## Resolution Order

| Order | Mechanism                                           | Annotation                             | Set by               | Applies when                                                                      |
|-------|-----------------------------------------------------|----------------------------------------|----------------------|-----------------------------------------------------------------------------------|
| 1     | [Pinning](#pinning-a-volume-to-a-storage-node)      | `simplyblock.io/selected-storage-node` | User                 | The annotation names a storage node.                                              |
| 2     | [Load-aware placement](#load-aware-placement)       | `simplyblock.io/placement-hint`        | Operator (automatic) | Load-aware placement is enabled for the cluster and not disabled for the PVC.     |
| 3     | [Pod co-location](#co-locating-a-volume-with-a-pod) | `simplyblock.io/pod-affinity`          | User                 | The annotation is set to `"true"` and the StorageClass is `WaitForFirstConsumer`. |
| —     | Default placement                                   | *(none of the above)*                  | —                    | No annotation applies.                                                            |

A [clone or a snapshot restore](#clones-and-snapshot-restores) is placed outside this order.

## Pinning a Volume to a Storage Node

On a new PVC, `simplyblock.io/selected-storage-node` sets the primary node directly. On an already-bound PVC,
a [migration](../operations/volumes/volume-migration.md#migrating-by-pinning-a-pvc) to the new node is triggered by
this annotation instead.

```bash title="Pinning a new PVC to a specific storage node"
kubectl annotate pvc my-pvc -n simplyblock \
  simplyblock.io/selected-storage-node=4e53efdd-86c9-424f-940c-e437eb6a2e95
```

The value must be a known storage node UUID. Any other value is rejected by a validating webhook. The UUID
of a storage node is held in the `UUID` column of its `StorageNode` resource (short name `sn`).

```bash title="Listing the storage nodes of a cluster with their UUIDs"
kubectl get storagenodes -n simplyblock
```

```plain title="Example output of the storage node listing"
NAME                      WORKER                          SOCKET   NODEIDX   UUID                                   STATUS   HEALTH   AGE
simplyblock-node-mejue8   vm04.simplyblock3.localdomain   0        0         82198a36-fcbb-43e3-949c-0260bf40f0ac   online   true     43h
simplyblock-node-o6x20i   vm03.simplyblock3.localdomain   0        0         707dd443-5d0e-470f-bdde-92f1238c4b01   online   true     43h
simplyblock-node-v92jx7   vm02.simplyblock3.localdomain   0        0         114899a6-d708-499e-8051-bc9ca9713cf8   online   true     43h
```

## Load-Aware Placement

When load-aware placement selects a node for a new volume, that node is recorded on the PVC in the
`simplyblock.io/placement-hint` annotation. The hint is written by the operator rather than set by a user,
and it does not pin the volume. A node is eligible when it is online, passes its health check, and is below
its configured logical volume limit.

Load-aware placement is controlled by the same `StorageCluster` field that also feeds
[auto-rebalancing's latency benchmark](../operations/volumes/volume-migration.md#auto-rebalancing):

| Field                                         | Type | Default | Description                                                                                                                       |
|-----------------------------------------------|------|---------|-----------------------------------------------------------------------------------------------------------------------------------|
| `volumeAutoPlacement.latencyBenchmarkEnabled` | bool | `false` | Enables load-aware placement for new volumes, independent of `volumeAutoPlacement.migrationEnabled` (continuous rebalancer only). |

```yaml title="Enabling load-aware placement for new volumes"
spec:
  volumeAutoPlacement:
    latencyBenchmarkEnabled: true
```

## Co-locating a Volume with a Pod

`simplyblock.io/pod-affinity` places a new volume on a storage node that is co-located with the volume's
consuming Pod. It is a boolean, defaults to `false`, and is opt-in per PVC.

```yaml title="Example of a PVC co-located with its consuming Pod"
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

A `WaitForFirstConsumer` StorageClass is required (see [Defining a StorageClass](storage-class.md)). The
Pod's node is resolved from `nodeSelector`, node affinity, or pod affinity. Setting `spec.nodeName` directly
on the Pod is not supported
([kubernetes/kubernetes#89953](https://github.com/kubernetes/kubernetes/issues/89953){:target="_blank" rel="noopener"}).
When the Pod's node hosts more than one storage node, one of them is selected at random.

## Clones and Snapshot Restores

None of the above applies to a PVC created from a `VolumeSnapshot` or another PVC (`dataSource`). A clone
or restore always uses its source volume's node.
