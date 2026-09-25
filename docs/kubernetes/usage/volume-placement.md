---
title: "Automatic Volume Placement"
description: "Reference for the PVC annotations and StorageCluster fields that control which storage node becomes a new volume's primary node, and how a pin change migrates a volume."
weight: 40050
---

{{ experimental }}

The primary storage node of a new volume is decided when the volume is provisioned. Several mechanisms can decide it,
each driven by a PVC annotation and evaluated in a fixed order. The first mechanism that applies wins, and the
remaining ones are not evaluated. If none applies, the storage cluster's built-in default placement is used.

## Resolution Order

| Order | Mechanism                                           | Annotation                                     | Set by               | Applies when                                                                      |
|-------|-----------------------------------------------------|------------------------------------------------|----------------------|-----------------------------------------------------------------------------------|
| 1     | [Pinning](#pinning-a-volume-to-a-storage-node)      | `storage.simplyblock.io/selected-storage-node` | User                 | The annotation names a storage node.                                              |
| 2     | [Load-aware placement](#load-aware-placement)       | `storage.simplyblock.io/placement-hint`        | Operator (automatic) | Load-aware placement is enabled for the cluster and an eligible node exists.      |
| 3     | Legacy host ID                                      | `storage.simplyblock.io/host-id`               | User (legacy)        | A claim from an earlier release carries the annotation.                           |
| 4     | [Pod co-location](#co-locating-a-volume-with-a-pod) | `simplyblock.io/pod-affinity`                  | User                 | The annotation is set to `"true"` and the StorageClass is `WaitForFirstConsumer`. |
| none  | Default placement                                   | *(none of the above)*                          | none                 | No annotation applies.                                                            |

The annotations moved to the `storage.simplyblock.io/` prefix. The older spellings `simplyblock.io/selected-storage-node`,
`simplyblock.io/placement-hint`, `simplyblock.io/host-id`, and `simplybk/host-id` are still read, and the newer spelling
wins when a claim carries both. `simplyblock.io/pod-affinity` keeps its prefix.

A [clone or a snapshot restore](#clones-and-snapshot-restores) is placed outside this order.

## Pinning a Volume to a Storage Node

On a new PVC, `storage.simplyblock.io/selected-storage-node` sets the primary node directly. On an already-bound PVC,
changing the annotation raises a `PersistentVolumeOps` migration of the volume to the new node instead (see
[Migrating by Pinning a PVC](../operations/volumes/volume-migration.md#migrating-by-pinning-a-pvc)).

```bash title="Pinning a new PVC to a specific storage node"
kubectl annotate pvc my-pvc -n my-app \
  storage.simplyblock.io/selected-storage-node=4e53efdd-86c9-424f-940c-e437eb6a2e95
```

The value must be a known storage node UUID. Any other value is rejected by a validating webhook. The UUID of a
storage node is held in `status.uuid` of its `StorageNode` resource (short name `sn`), shown in the `UUID` column of the
wide listing.

```bash title="Listing the storage nodes of a cluster with their UUIDs"
kubectl get storagenodes -n simplyblock -o wide
```

```plain title="Example output of the storage node listing"
NAME                CLUSTER      WORKER     SOCKET   SLOT   PHASE    STEP   STATUS   HEALTH   UUID                                   FD    AGE
production-7f3a9c   production   worker-1   0        0      Online          online   true     82198a36-fcbb-43e3-949c-0260bf40f0ac         43h
production-9c21de   production   worker-2   0        1      Online          online   true     707dd443-5d0e-470f-bdde-92f1238c4b01         43h
production-a4410b   production   worker-3   0        2      Online          online   true     114899a6-d708-499e-8051-bc9ca9713cf8         43h
```

A pinned volume is never moved by auto-rebalancing, and it blocks the removal of its storage node until it is re-pinned
or unpinned (see [Pinned Volumes](../operations/volumes/volume-migration.md#pinned-volumes)).

## Load-Aware Placement

When load-aware placement selects a node for a new volume, that node is recorded on the PVC in the
`storage.simplyblock.io/placement-hint` annotation. The hint is written by the operator's admission webhook rather than
set by a user, it is removed by the CSI driver once the volume has been created, and it does not pin the volume. A
node is eligible when it is online, passes its health check, and is below its configured logical volume limit. A claim
that already carries `storage.simplyblock.io/selected-storage-node` gets no hint.

Load-aware placement is controlled by the same `StorageCluster` field that also feeds
[auto-rebalancing's latency benchmark](../operations/volumes/volume-migration.md#auto-rebalancing):

| Field                                        | Type | Default | Description                                                                                                            |
|----------------------------------------------|------|---------|------------------------------------------------------------------------------------------------------------------------|
| `volumeAutoPlacement.enableLatencyBenchmark` | bool | `false` | Enables load-aware placement for new volumes, independent of `enableVolumeAutoPlacement` (continuous rebalancer only). |

```yaml title="Enabling load-aware placement for new volumes"
spec:
  volumeAutoPlacement:
    enableLatencyBenchmark: true
```

## Co-locating a Volume with a Pod

`simplyblock.io/pod-affinity` places a new volume on a storage node that is co-located with the volume's consuming
Pod. It is a boolean, defaults to `false`, and is opt-in per PVC.

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
  storageClassName: simplyblock-simplyblock-production
```

A `WaitForFirstConsumer` StorageClass is required (see [Storage Class](storage-class.md)). The Pod's node is resolved
from `nodeSelector`, node affinity, or pod affinity. Setting `spec.nodeName` directly on the Pod is not supported
([kubernetes/kubernetes#89953](https://github.com/kubernetes/kubernetes/issues/89953){:target="_blank" rel="noopener"}).
When the Pod's node hosts more than one storage node, one of them is selected at random.

## Clones and Snapshot Restores

None of the above applies to a PVC created from a `VolumeSnapshot` or another PVC (`dataSource`). A clone or restore
always uses its source volume's node.
