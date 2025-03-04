---
title: "Expanding"
weight: 40300
---

Expanding a Persistent Volume (PV) in Kubernetes allows to increase the size of a volume without downtime, ensuring
applications continue running with sufficient storage. Simplyblock supports online expansion of Logical Volumes (LVs)
through its CSI driver, making it possible to resize volumes dynamically as storage requirements grow.

!!! info
    To enable volume expansion Kubernetes 1.16 or later is required.

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

## Resize the Filesystem (If Required)

Certain filesystems, such as ext4, may require growing the filesystem after the underlying volume has been expanded.
This can usually be handled automatically by the CSI driver or may require running filesystem-specific commands within
the pod.

## Shrinking a Volume

Theoretically it is possible to shrink a volume. It can, however, create issues with certain filesystems. When a volume
needs to be shrunk, it is recommended to create a snapshot and restore it onto a new volume.
