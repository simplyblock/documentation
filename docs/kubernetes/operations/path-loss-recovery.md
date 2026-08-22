---
title: "Recovering from Path Loss"
description: "How the simplyblock CSI node plugin restores NVMe-oF paths after a storage node outage, and how to opt a workload into an automatic pod restart."
weight: 10820
---

An NVMe-oF path breaks when the storage node serving a volume goes away, during a node restart, a worker reboot, or a
cluster outage. The paths are re-established by the CSI node plugin, which needs no intervention. What sometimes does
need attention is the workload: a process holding a file descriptor across a long path loss can be left with I/O errors
that only a restart clears.

Plain Linux clients reconnect their volumes by hand, as described in
[Reconnecting Logical Volume](../../non-kubernetes/operations/reconnect-nvme-device.md). On Kubernetes none of that
applies. The node plugin repairs the fabric itself, and the only decision left is whether affected pods should be
restarted automatically.

## Automatic Path Repair

Each volume is attached over NVMe-oF with a primary path and one or more failover paths, so the loss of a single
storage node is absorbed by the remaining paths. The node plugin watches for the case where a subsystem is connected
but exports no usable namespace, which is what a stale controller looks like, and repairs it by reattaching the
subsystem.

This happens during volume staging and at runtime, and it requires no configuration.

## Automatic Pod Restart

A path that comes back does not necessarily heal the workload. A filesystem that saw I/O errors can stay in a state
that only a remount clears, and a database that lost its data directory mid-write usually has to start over.

The node plugin therefore ships a guardian that can restart the affected pods once the storage is healthy again. It is
off by default and opted into per workload.

```yaml title="Example of a StorageClass whose volumes opt into the automatic restart"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: simplyblock-autorestart
  annotations:
    simplyblock.io/auto-restart-on-pathloss: "true"
provisioner: csi.simplyblock.io
```

The same key is honored on a Pod, on a PersistentVolumeClaim, and on a StorageClass, as either a label or an
annotation. The first of them that carries the value `true` opts the pod in, which allows a single workload to opt in
without changing the StorageClass every volume shares.

```bash title="Opting a single workload in through its claim"
kubectl label pvc my-pvc -n simplyblock \
    simplyblock.io/auto-restart-on-pathloss=true
```

### When a Pod Is Restarted

A restart is deliberately slow to trigger, because a pod that is restarted while its storage is still gone comes back
no healthier. Several conditions have to hold at once.

- The volume has been unusable for at least 30 seconds.
- The cluster the volume belongs to reports itself active again. A volume whose cluster is still down is left alone,
  however long it has been broken.
- The pod has an owning controller, so that something recreates it. A bare pod is never deleted, since deleting it
  would remove the workload rather than restart it.
- The pod is outside the restart backoff, which is ten minutes per pod.

The guardian evaluates this every five minutes, and a grace period of 90 seconds after the first broken volume gives
the cluster time to report its own state before any decision is made. A restart is carried out by deleting the pod and
letting its controller recreate it.

### Volumes Sharing an NVMe Subsystem

A volume provisioned with `max_namespace_per_subsys` above `1` shares its NVMe-oF subsystem with other volumes, so
tearing its paths down would disconnect volumes belonging to other pods. Such pods are restarted as a group, all at
once, and only when every pod in the group passes the checks above. A single pod that fails them suppresses the whole
group, and an event on that pod names it as the blocker.

| Event reason                | Emitted on       | Meaning                                                                   |
|-----------------------------|------------------|---------------------------------------------------------------------------|
| `AutoRestartSuppressed`     | The affected pod | The volume shares a subsystem and a coordinated restart was not possible. |
| `CoordinatedRestartBlocked` | The blocking pod | This pod prevented the restart of its subsystem group.                    |

```bash title="Checking for suppressed restarts"
kubectl get events -A --field-selector reason=AutoRestartSuppressed
kubectl get events -A --field-selector reason=CoordinatedRestartBlocked
```

The message of a `CoordinatedRestartBlocked` event names what the blocking pod is missing, which is usually the opt-in
on its own controller.

### Disabling the Restart for One Workload

A pod that must never be restarted automatically carries the opt-out key, which wins over any opt-in inherited from
its claim or its StorageClass.

```yaml title="Example of a pod excluded from the automatic restart"
metadata:
  labels:
    simplyblock.io/guardian-disable: "true"
```

## Checking the Paths of a Volume

The paths of a volume are inspected on the worker that consumes it. The subsystem carries the volume UUID in its NQN.

```bash title="Listing the NVMe subsystems on a worker"
kubectl debug node/worker-1.example.com -it --image=busybox -- \
    nvme list-subsys
```

A subsystem that is connected but exports no namespace is the state the node plugin repairs. A subsystem that is
missing entirely means the volume is not staged on this worker.

Further diagnosis of the CSI driver is covered in
[Kubernetes CSI Troubleshooting](../../reference/troubleshooting/simplyblock-csi.md).

## Related Operations

A path loss that follows from a planned operation is expected, and the operation itself reports its progress. See
[Storage Node Actions](storage-node-actions.md) for a single node, [Rolling Restart](rolling-restart.md) for a whole
cluster, and [Coordinated Worker Node Drain](node-drain-coordination.md) for a worker going down for maintenance.
