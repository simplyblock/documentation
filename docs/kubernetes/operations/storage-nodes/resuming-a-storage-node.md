---
title: "Resuming a Storage Node"
description: "Return a suspended simplyblock storage node to normal service with the resume action of a StorageNodeOps resource, so new volumes are placed on it again."
weight: 10218
---

A resume returns a suspended storage node to normal service, so that new volumes are placed on it again. The operation
succeeds once the node reports the status `online`.

```bash title="Resuming a suspended storage node"
kubectl apply -n simplyblock -f - <<EOF
apiVersion: storage.simplyblock.io/v1alpha1
kind: StorageNodeOps
metadata:
  name: resume-worker-1
  namespace: simplyblock
spec:
  storageNodeRef: simplyblock-node-mejue8
  action: resume
EOF
```

Only a `suspended` node can be resumed, and a request against a node in any other state is refused. The control plane
takes no force flag for a resume, so `spec.force` has no effect on it. How an operation is tracked and cleaned up is
described in [Storage Node Actions](storage-node-actions.md).
