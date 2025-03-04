---
title: "Cloning"
weight: 40200
---

Kubernetes PersistentVolumes, backed by simplyblock, can be instantly cloned. A clone refers back to the same data, as
simplyblock is a full [copy-on-write](../../important-notes/terminology.md#cow-copy-on-write) storage engine. That
enables instant database forks which act independently after cloning.

## Create a Volume Clone

To clone an existing PersistentVolume, it has to be named as the clone basis (_dataSource_) in the PersistentVolumeClaim
Kubernetes resource.

```yaml title="PersistentVolumeClaim to clone an existing volume"
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-persistent-volume-clone
spec:
  storageClassName: simplyblock-storage-class
  dataSource:
    name: original-persistent-volume-name # <- Name of the original volume
    kind: PersistentVolumeClaim
    apiGroup: ""
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 256Mi
```

Afterward, the PVC can be used as a normal PVC and added to a pod.

```yaml title="Using the cloned PersistentVolumeClaim"
kind: Pod
apiVersion: v1
metadata:
  name: cloned-database
  labels:
    app: cloned-database
spec:
  containers:
  - name: alpine
    image: alpine:3
    imagePullPolicy: "IfNotPresent"
    command: ["sleep", "365d"]
    volumeMounts:
    - mountPath: "/mounted"
      name: my-cloned-volume
  volumes:
  - name: my-cloned-volume
    persistentVolumeClaim:
      claimName: my-persistent-volume-clone
```
