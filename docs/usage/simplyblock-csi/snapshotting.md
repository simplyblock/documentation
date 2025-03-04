---
title: "Snapshotting"
weight: 40100
---

Kubernetes PersistentVolumes backed by simplyblock can be instantly snapshotted. Snapshots are almost free due to
simplyblock's [copy-on-write](../../important-notes/terminology.md#cow-copy-on-write) nature.

In simplyblock, a snapshot is comparable to the table of contents in a book, meaning, the snapshot refers to the same
data as the original volume. If the volume diverges from the snapshot, the mutated data segment is duplicated, changed,
and stored as a new data block. Now the volume refers to the new block, while the snapshot to the old one.

A deeper explanation can be found here:

![type:video](https://www.youtube.com/embed/wMy1r8RVTz8?si=kNpI8FJuiifS6Pwt)

<div class="video-wrapper" data-service="youtube" data-id="wMy1r8RVTz8"></div>

## Snapshotting a PersistentVolume

To snapshot a persistent volume, a new Kubernetes Snapshot resource is created. When applying the resource, the
snapshot is taken immediately.

```yaml title="Creating a Snapshot resource"
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: my-volume-snapshot
spec:
  volumeSnapshotClassName: csi-spdk-snapclass
  source:
    persistentVolumeClaimName: my-persistent-volume-claim # <- refers to the PVC to snapshot
```

## Restore a Volume from a Snapshot

After a snapshot was created, it can be used as a source (_dataSource_) of a new persistent volume. In this case, the
new persistent volume claim refers to the snapshot which is automatically restored into the new persistent volume.

```yaml title="Restoring a snapshot"
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-restored-snapshot-volume
spec:
  storageClassName: simplyblock-storage-class
  dataSource:
    name: my-volume-snapshot
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 256Mi
```

Afterward, the PVC can be used as a normal PVC and added to a pod.

```yaml title="Using the restored PersistentVolumeClaim"
kind: Pod
apiVersion: v1
metadata:
  name: restored-database
  labels:
    app: restored-database
spec:
  containers:
  - name: alpine
    image: alpine:3
    imagePullPolicy: "IfNotPresent"
    command: ["sleep", "365d"]
    volumeMounts:
    - mountPath: "/mounted"
      name: my-restored-volume
  volumes:
  - name: my-restored-volume
    persistentVolumeClaim:
      claimName: my-restored-snapshot-volume
```
