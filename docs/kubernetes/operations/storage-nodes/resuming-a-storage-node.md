---
title: "Resuming a Storage Node"
description: "Return a suspended simplyblock storage node to normal service with a Resume operation of a StorageNodeOps resource, so new volumes are placed on it again."
weight: 10218
---

A resume returns a suspended storage node to normal service, so that new volumes are placed on it again. The operation
succeeds once the node reports the status `online`.

```yaml title="Example of a node resumption (resume-node.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageNodeOps
metadata:
  name: resume-worker-1
  namespace: simplyblock
spec:
  nodeRef: simplyblock-cluster-worker-1-0
  action: Resume
```

```bash title="Resuming a suspended storage node"
kubectl apply -f resume-node.yaml
```

The operation runs the steps `Requesting` and `Awaiting`. A resume of a node that is already `online` succeeds at once
without a call to the control plane. The control plane resumes only a `suspended` node, and it takes no force flag for
a resume.

A node that was left suspended by a failed removal, reported with a `NodeResumeFailed` event, is brought back the same
way. How an operation is tracked and cleaned up is described in [Storage Node Actions](storage-node-actions.md).
