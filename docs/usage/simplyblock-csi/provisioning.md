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
