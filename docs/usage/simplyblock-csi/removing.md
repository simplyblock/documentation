---
title: "Removing"
weight: 40400
---

A simplyblock-managed logical volume which is connected to a Kubernetes PersistentVolumeClaim is target to Kubernetes'
automatic lifecycle management. Therefore, if the PVC is removed, the logical volume is removed as well.

If the storage class is defined with a reclaim policy that keeps the volume around after it's claim has been deleted,
it has to be removed specifically.

## Removing a Persistent Volume

When a Persistent Volume (PV) in Kubernetes has its reclaim policy set to Retain, deleting the associated Persistent
Volume Claim (PVC) does not automatically delete the PV or its underlying storage. Instead, the PV enters a Released
state, signaling that the PVC has been deleted, but the storage remains intact and requires manual cleanup. This reclaim
policy is commonly used when manual review of data or explicit deprovisioning is required.

### Steps to remove a retained persistent volume

If the PersistentVolumeClaim still exists, it has to be deleted first:

```bash title="Removing a PersistentVolumeClaim"
kubectl delete pvc <pvc-name>
```

When the PVC is deleted, the PersistentVolume state must be checked. It should be _released_:

```bash title="Check PersistentVolume status"
kubectl get pv
```

Now the PV can be deleted:

```bash title="Delete a PersistentVolume"
kubectl get pv <pv-name>
```
