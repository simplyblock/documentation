---
title: "Expanding"
description: "Expanding a Persistent Volume (PV) in Kubernetes allows for increasing the size of a volume without downtime, ensuring applications continue running with."
source: "https://docs.simplyblock.io/latest/kubernetes/usage/expanding/"
---

# Expanding

Expanding a Persistent Volume (PV) in Kubernetes allows for increasing the size of a volume without downtime, ensuring
applications continue running with sufficient storage. Simplyblock supports online expansion of Logical Volumes (LVs)
through its CSI driver, making it possible to resize volumes dynamically as storage requirements grow.

!!! info
    To enable volume expansion, Kubernetes 1.16 or later is required.

## Enable Volume Expansion

To enable volume expansion, the [StorageClass](storage-class.md) has to be configured accordingly. To enable volume
expansion, the property `allowVolumeExpansion` has to be set to true.

```yaml title="Allowing volume expansion in StorageClass"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: encrypted-volumes
provisioner: csi.simplyblock.io
parameters:
  encryption: "True"
  csi.storage.k8s.io/fstype: ext4
  ... other parameters
reclaimPolicy: Delete
volumeBindingMode: Immediate
allowVolumeExpansion: true # <- Enable volume expansion
```

## Expand a PersistentVolume

To expand an existing volume, update the field `spec.resources.requests.storage` in the existing resource descriptor.

```yaml title="Updating the volume size"
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-example-pvc
spec:
  resources:
    requests:
      storage: 500Gi # <- Was 100Gi before
```

Then apply the change.

```bash title="Apply resource update"
kubectl apply -f pvc.yaml
```

!!! note
    Simplyblock allocates logical volumes on GiB boundaries. A requested size is rounded up to the next full
    GiB, so an expansion that stays inside the current GiB does not change the size of the logical volume.

## Resize the Filesystem

For a volume mounted as a filesystem, the resize is performed by the CSI driver after the logical volume has
been expanded. The filesystem is grown in place, and no filesystem-specific command has to be run inside the
pod.

For a raw block volume, no filesystem resize is performed. The block device is expanded at the storage layer,
and the consuming application picks up the new size on its own.

## Shrinking a Volume

A volume cannot be shrunk. Kubernetes rejects a decrease of `spec.resources.requests.storage` on an existing
persistent volume claim. When a smaller volume is needed, a snapshot is created and restored onto a new
volume of the smaller size.
