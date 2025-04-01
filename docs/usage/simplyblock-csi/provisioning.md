---
title: "Provisioning"
weight: 40000
---

Provisioning a new PersistentVolume using simplyblock's Kubernetes CSI driver integration, requires at least one
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
  storageClassName: simplyblock-storage-class     
```

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
    Simplyblock discourages the static provisioning of Kubernetes Persistent Volumes. Only do it if you know what you
    do. We highly recommend to use the dynamic provisioning through the Simplyblock CSI driver.

### NVMe over Fabrics Target

To create the static persistent volume, the following values need to be known:
- `model`
- `nqn`
- `lvol`
- `targetAddr`
- `targetPort`
- `targetType`
- Name of the logical volume

```yaml title="Staticly provisioned persistent volume: pv-static.yaml"
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
    storage: 256Mi
  csi:
    driver: csi.simplyblock.io
    fsType: ext4
    volumeAttributes:
      # MODEL_NUMBER, set by the `nvmf_create_subsystem` method
      model: aa481c21-26f8-4056-87fa-cd306f69a71e
      # Subsystem NQN (ASCII), set by the `nvmf_create_subsystem` method
      nqn: nqn.2020-04.io.spdk.csi:uuid:aa481c21-26f8-4056-87fa-cd306f69a71e
      # The listen address to an NVMe-oF subsystemset, set by the `nvmf_subsystem_add_listener` method
      targetAddr: 127.0.0.1
      targetPort: "4420"
      # transport type, TCP or RDMA
      targetType: TCP
    # volumeHandle should be same as lvol store name(uuid)
    volumeHandle: aa481c21-26f8-4056-87fa-cd306f69a71e
  persistentVolumeReclaimPolicy: Retain
  storageClassName: spdkcsi-sc
  volumeMode: Filesystem
```

```plain title="Example output of applying the statically persistent volume"
demo@demo ~> kubectl create -f pv-static.yaml
persistentvolume/pv-static created
```

!!! warning
    Simplyblock's CSI driver does not supports logical volume deletion for static persistent volumes. Hence,
    `persistentVolumeReclaimPolicy` in persistent volume specification must be set to `Retain` to avoid persistent
    volume delete attempt in csi-provisioner.


### iSCSI Target

To create the static persistent volume, the following values need to be known:

- `lvol`
- `targetAddr`
- `targetPort`
- Name of the logical volume

```yaml title="Staticly provisioned persistent volume: pv-static.yaml"
apiVersion: v1
kind: PersistentVolume
metadata:
  annotations:
    pv.kubernetes.io/provisioned-by: csi.simplyblock.io
  name: pv-static
spec:
  accessModes:
  - ReadWriteOnce
  capacity:
    storage: 256Mi
  csi:
    driver: csi.simplyblock.io
    fsType: ext4
    volumeAttributes:
      # number Initiator group tag, the default value is `iqn.2016-06.io.spdk:`+ `volumeHandle`
      iqn: iqn.2016-06.io.spdk:c0cd9559-cd6e-43b6-98af-45196e41655f
      # iSCSI transport address, set by the `iscsi_create_portal_group` method
      targetAddr: 127.0.0.1
      targetPort: "3260"
      targetType: iscsi
    # volumeHandle should be same as lvol store name(uuid)
    volumeHandle: c0cd9559-cd6e-43b6-98af-45196e41655f
  persistentVolumeReclaimPolicy: Retain
  storageClassName: spdkcsi-sc
  volumeMode: Filesystem
```

```plain title="Example output of applying the statically persistent volume"
demo@demo ~> kubectl create -f pv-static.yaml
persistentvolume/pv-static created
```

!!! warning
    Simplyblock's CSI driver does not supports logical volume deletion for static persistent volumes. Hence,
    `persistentVolumeReclaimPolicy` in persistent volume specification must be set to `Retain` to avoid persistent
    volume delete attempt in csi-provisioner.

### Create static Persistent Volume Claim

```yaml title="Staticly provisioned persistent volume claim: pvc-static.yaml"
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: pvc-static
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 256Mi
  # As a functional test, volumeName is same as PV name
  volumeName: pv-static
  storageClassName: spdkcsi-sc
```

```bash
demo@demo ~> kubectl create -f pvc-static.yaml
persistentvolumeclaim/pvc-static created
```

