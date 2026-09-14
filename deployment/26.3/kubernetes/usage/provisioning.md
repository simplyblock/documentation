---
title: "Provisioning"
description: "Provisioning a new PersistentVolume using simplyblock's Kubernetes CSI driver integration requires at least one StorageClass to be set up."
source: "https://docs.simplyblock.io/latest/kubernetes/usage/provisioning/"
---

# Provisioning

Provisioning a new PersistentVolume using simplyblock's Kubernetes CSI driver integration requires at least one
[StorageClass](storage-class.md) to be set up.

## Create a new Volume

To create a new persistent volume backed by simplyblock, requires a persistent volume claim with the correct storage
class.

```yaml title="Create a new PersistentVolumeClaim"
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-simplyblock-volume
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 256Mi
  storageClassName: simplyblock-csi-sc
```

!!! note
    Simplyblock allocates logical volumes on GiB boundaries. A requested size is rounded up to the next
    full GiB, so the claim above is backed by a logical volume of 1 GiB. The rounded size is what the
    persistent volume reports as its capacity.

Afterward, the PVC can be used as a normal PVC and added to a pod.

```yaml title="Using the PersistentVolumeClaim"
kind: Pod
apiVersion: v1
metadata:
  name: database
  labels:
    app: database
spec:
  containers:
  - name: alpine
    image: alpine:3
    imagePullPolicy: "IfNotPresent"
    command: ["sleep", "365d"]
    volumeMounts:
    - mountPath: "/mounted"
      name: my-volume
  volumes:
  - name: my-volume
    persistentVolumeClaim:
      claimName: my-simplyblock-volume
```

## Create a Volume from a Snapshot

To create a new persistent volume claim from an existing snapshot, see the section about
[Restoring a Snapshot](snapshotting.md#restore-a-volume-from-a-snapshot).

## Create a cloned Volume

To create a new persistent volume claim from an existing and live volume, see the section about [Cloning](cloning.md).

## Static Provisioning

!!! warning
    Simplyblock discourages the static provisioning of Kubernetes Persistent Volumes. Use it only with a clear
    understanding of the consequences. Dynamic provisioning through the Simplyblock CSI driver is highly recommended.

### NVMe over Fabrics Target

To create the static persistent volume, three values of the existing logical volume have to be known:

- The UUID of the storage cluster holding the logical volume
- The UUID of the storage pool the logical volume was created in
- The UUID of the logical volume itself

The three UUIDs are composed into `volumeHandle`, in the form `<clusterID>:<poolID>:<lvolID>`. A
`volumeHandle` in any other form is rejected, and the volume is never staged.

Everything required to attach the volume is resolved from the control plane at attach time: the
subsystem NQN, the model number, the namespace ID, the transport type, and the addresses of the NVMe
over Fabrics targets. None of it is carried in the persistent volume, and a value set there is
overwritten. The only volume attribute read is `cluster_id`, and if it is missing, the cluster UUID is
derived from the subsystem NQN.

```yaml title="Example of a statically provisioned persistent volume (pv-static.yaml)"
apiVersion: v1
kind: PersistentVolume
metadata:
  annotations:
    pv.kubernetes.io/provisioned-by: csi.simplyblock.io
  finalizers:
  - kubernetes.io/pv-protection
  name: pv-static
spec:
  accessModes:
  - ReadWriteOnce
  capacity:
    storage: 1Gi
  csi:
    driver: csi.simplyblock.io
    fsType: ext4
    volumeAttributes:
      # UUID of the storage cluster holding the logical volume
      cluster_id: 8ffac363-0c46-4714-a71b-f9c0b58a1269
    # <clusterID>:<poolID>:<lvolID> of the existing logical volume
    volumeHandle: 8ffac363-0c46-4714-a71b-f9c0b58a1269:df34f16c-1d5c-4e39-9a1e-2b0c7f8d9e10:aa481c21-26f8-4056-87fa-cd306f69a71e
  persistentVolumeReclaimPolicy: Retain
  storageClassName: simplyblock-csi-sc
  volumeMode: Filesystem
```

```bash title="Applying the statically provisioned persistent volume"
kubectl create -f pv-static.yaml
```

```plain title="Example output of applying the statically provisioned persistent volume"
persistentvolume/pv-static created
```

!!! warning
    Simplyblock's CSI driver does not support logical volume deletion for static persistent volumes. Hence,
    `persistentVolumeReclaimPolicy` in persistent volume specification must be set to `Retain` to avoid persistent
    volume delete attempt in csi-provisioner.

### Create static Persistent Volume Claim

```yaml title="Example of a statically provisioned persistent volume claim (pvc-static.yaml)"
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: pvc-static
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  # As a functional test, volumeName is same as PV name
  volumeName: pv-static
  storageClassName: simplyblock-csi-sc
```

```bash title="Creating the persistent volume claim"
kubectl create -f pvc-static.yaml
```

```plain title="Example output of the volume claim creation"
persistentvolumeclaim/pvc-static created
```
