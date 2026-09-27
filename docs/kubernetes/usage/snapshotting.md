---
title: "Snapshotting"
description: "Snapshot simplyblock PersistentVolumes with VolumeSnapshots, take crash-consistent group snapshots, and restore a whole group with VolumeGroupSnapshotOps."
weight: 40100
---

Kubernetes PersistentVolumes backed by simplyblock can be instantly snapshotted. Snapshots are almost free due to
simplyblock's [copy-on-write](../../important-notes/terminology.md#cow-copy-on-write) nature.

In simplyblock, a snapshot is comparable to the table of contents in a book, meaning that the snapshot refers to the same
data as the original volume. If the volume diverges from the snapshot, the mutated data segment is duplicated, changed,
and stored as a new data block. Now, the volume refers to the new block, while the snapshot refers to the old one.

A deeper explanation can be found here:

<div data-service="YouTube" data-id="wMy1r8RVTz8" data-autoscale></div>

## Snapshotting a PersistentVolume

To snapshot a persistent volume, a new Kubernetes `VolumeSnapshot` resource is created. When applying the resource,
the snapshot is taken immediately. The VolumeSnapshotClass is created by the Simplyblock Operator together with the CSI
driver, as `simplyblock-csi-snapshotclass` for the default `SimplyblockDriver` named `simplyblock`.

```yaml title="Creating a Snapshot resource"
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: my-volume-snapshot
spec:
  volumeSnapshotClassName: simplyblock-csi-snapshotclass
  source:
    persistentVolumeClaimName: my-persistent-volume-claim # <- refers to the PVC to snapshot
```

## Restore a Volume from a Snapshot

After a snapshot was created, it can be used as a source (_dataSource_) of a new persistent volume. In this case, the
new persistent volume claim refers to the snapshot, which is automatically restored into the new persistent volume.

```yaml title="Restoring a snapshot"
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-restored-snapshot-volume
spec:
  storageClassName: simplyblock-simplyblock-production
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

## Snapshotting a Group of Volumes

Several volumes that have to be snapshotted at the same point in time, for example, the data and the log volume of a
database, form a consistency group. A claim joins a group through the label `storage.simplyblock.io/consistency-group`,
which is read once, when the volume is provisioned. The control plane places the members of a group together.

```yaml title="Example of a claim that joins the consistency group db-group"
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: db-data
  namespace: prod
  labels:
    storage.simplyblock.io/consistency-group: db-group
spec:
  storageClassName: simplyblock-simplyblock-production
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
```

A crash-consistent snapshot of the whole group is taken with a Kubernetes `VolumeGroupSnapshot`, whose selector
matches exactly the members of the group. A VolumeGroupSnapshotClass for the simplyblock driver is created once:

```yaml title="Example of a VolumeGroupSnapshotClass and a VolumeGroupSnapshot"
apiVersion: groupsnapshot.storage.k8s.io/v1beta1
kind: VolumeGroupSnapshotClass
metadata:
  name: simplyblock-groupsnapshotclass
driver: csi.simplyblock.io
deletionPolicy: Delete
---
apiVersion: groupsnapshot.storage.k8s.io/v1beta1
kind: VolumeGroupSnapshot
metadata:
  name: db-group-gen4
  namespace: prod
spec:
  volumeGroupSnapshotClassName: simplyblock-groupsnapshotclass
  source:
    selector:
      matchLabels:
        storage.simplyblock.io/consistency-group: db-group
```

A validating webhook of the operator rejects a `VolumeGroupSnapshot` whose selector matches claims of more than one
group, an unlabeled claim, or no claim at all. One `VolumeSnapshot` is created per member, and each of them can be
restored on its own as described above.

## Restoring a Volume Group Snapshot

All members of a `VolumeGroupSnapshot` are restored in one step by a `VolumeGroupSnapshotOps` operation with
`action: Restore`. It creates one claim per member snapshot, named `<namePrefix>-<source claim name>`, and waits until
every claim is bound.

```yaml title="Example of a group restore (restore-db-group.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: VolumeGroupSnapshotOps
metadata:
  name: restore-db-gen4
  namespace: prod
spec:
  volumeGroupSnapshotRef: db-group-gen4
  action: Restore
  restore:
    namePrefix: restored
    consistencyGroup: db-group-restored
```

```bash title="Starting the group restore"
kubectl apply -f restore-db-group.yaml
```

| Field                          | Description                                                                                                               |
|--------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| `volumeGroupSnapshotRef`       | Name of the `VolumeGroupSnapshot` in the same namespace. Required.                                                        |
| `action`                       | `Restore`, the only action. Required.                                                                                     |
| `restore.namePrefix`           | Prefix of the restored claim names. Defaults to the name of the operation.                                                |
| `restore.storageClassName`     | StorageClass of every restored claim. When empty, each claim uses the class of its source claim, which then has to exist. |
| `restore.consistencyGroup`     | Labels the restored claims with `storage.simplyblock.io/consistency-group`, so the clones form a new group.               |
| `restore.enablePartialRestore` | Restores the members an incomplete group snapshot still has, instead of failing. Defaults to `false`.                     |

The whole spec is immutable, and the operation cannot be aborted. `status.phase` moves from `Pending` through
`Running` to `Succeeded` or `Failed`, and while it runs, `status.step.state` is `Validating`, `CreatingClaims`, or
`WaitingForBind`. `status.membersExpected`, `status.membersBound`, and `status.members` report the progress per member.

```bash title="Watching the group restore"
kubectl get volumegroupsnapshotops -n prod -w
```
