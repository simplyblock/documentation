---
title: "Upgrading from 26.4.0-beta6"
description: "What upgrading a Kubernetes deployment from 26.4.0-beta6 needs beyond the standard upgrade sequence, and when each step runs."
weight: 20010
---

These notes apply to an upgrade of a Kubernetes deployment from `26.4.0-beta6` (including `26.4.0-beta6.1` and
`26.4.0-beta6.2`) to the next release. The upgrade itself follows [Upgrading a Cluster](../kubernetes/operations/cluster/cluster-upgrade.md).
This page lists what has to happen besides that sequence, and when. The `simplyblock-upgrade` tool of the target
release, and the chart's upgrade Jobs, run every step below at its point. By hand, each one is run as described.

No data or schema migration is needed: the stored resources, the control plane's records, and the storage-node
connections carry over unchanged.

## Summary

| What                                      | When                                    | Applies to                                |
|-------------------------------------------|-----------------------------------------|-------------------------------------------|
| Finish a pending device reweight          | Before the upgrade, on `26.4.0-beta6`   | Storage clusters of the lblk device class |
| Remove two pNFS values from values files  | Before the upgrade                      | Deployments that set them                 |
| Remove the old pNFS metadata-server state | After the operator runs the new release | Deployments with pNFS enabled             |
| Switch to v2 write protection             | After every storage node was restarted  | Every storage cluster upgraded from beta6 |

## Before the Upgrade

### Finish a Pending Device Reweight

`26.4.0-beta6` grew lblk devices unevenly and reweighted them afterward. The next release grows every device of a
cluster by the same factor and no longer finishes a reweight that is still pending, so the new weights would stay
recorded and never be pushed to every node. A pending reweight is finished on `26.4.0-beta6` before upgrading.

```bash title="Checking for a pending reweight, on 26.4.0-beta6"
sbctl cluster get <cluster-id> | grep reweight_pending
```

```bash title="Finishing a pending reweight, on 26.4.0-beta6"
sbctl cluster grow-devices <cluster-id>
```

`grow-devices` is repeated, without `--no-rebalance`, until `reweight_pending` reads `false`. The upgrade tool cannot read this from the control
plane, so its check is a warning that names every lblk cluster and asks for this to be confirmed.

### Remove the Old pNFS Values

The pNFS metadata server no longer keeps its state on a volume the chart sizes, so `driver.pnfs.mds.stateSize` and
`driver.pnfs.mds.stateStorageClassName` are gone from the chart. The next release still accepts both and ignores them,
so a values file carried over does not fail the upgrade, and the release after it refuses them. They are removed from
every values file now, and the upgrade tool reports them while they are still set.

## After the Operator Runs the New Release

### Remove the Old pNFS Metadata-Server State

With pNFS enabled, `26.4.0-beta6` ran one metadata server per storage cluster, with its state on a claim from a
derived StorageClass that an admission policy reserved. The next release runs an active metadata server with a
standby and manages their state itself. It updates the old StatefulSet's pods but cannot change its claim template, so
the old state is removed and the new operator recreates the metadata server.

This happens after the new operator runs, because the `26.4.0-beta6` operator recreates the StatefulSet the moment it
is deleted. The upgrade tool removes these objects. By hand, they are deleted in this order:

1. The metadata-server StatefulSet, whose name contains `-pnfs-mds-` and which still has a `state` volume claim
   template.
2. Its claims, whose StorageClass ends in `-pnfs-mds-state`.
3. That StorageClass.
4. The `ValidatingAdmissionPolicyBinding` and the `ValidatingAdmissionPolicy` named `<driver>-pnfs-mds-state`.

```bash title="Finding the old metadata-server state"
kubectl get statefulsets -n simplyblock | grep pnfs-mds
kubectl get pvc -n simplyblock -o custom-columns=NAME:.metadata.name,CLASS:.spec.storageClassName | grep pnfs-mds-state
kubectl get storageclass,validatingadmissionpolicy,validatingadmissionpolicybinding | grep pnfs-mds-state
```

!!! warning
    NFS clients reconnect to the new metadata server without reclaiming their open state. Applications holding
    locks on files of a ReadWriteMany volume see them released, so this step belongs in a window where that is
    acceptable.

## After the Storage Plane Is Rolled

### Switch to v2 Write Protection

A cluster created on `26.4.0-beta6` or earlier runs v1 distrib write protection, and an upgrade leaves it there. Every
cluster created by the next release starts on v2. The switch moves an upgraded cluster to v2. It runs once every
storage node is online on the new images, and it restarts nothing: the control plane switches every online node at
runtime and records v2 for the others.

```bash title="Checking which clusters still run v1 write protection"
kubectl get storageclusters -n simplyblock \
    -o custom-columns=NAME:.metadata.name,WRITE-PROTECTION:.status.writeProtection
```

```yaml title="Example of the write-protection switch (switch-write-protection.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageClusterOps
metadata:
  name: switch-write-protection
  namespace: simplyblock
spec:
  clusterRef: simplyblock-cluster
  action: SwitchWriteProtection
```

The operation holds until every node of the cluster is online, makes the switch, and succeeds once the cluster reports
`V2`. A cluster already on `V2` succeeds without a call. See
[Switching Write Protection](../kubernetes/operations/cluster/cluster-actions.md#switching-write-protection).

## Order of the Rollout

The storage plane is rolled before the write-protection switch, so every node runs the new release's SPDK image
before the switch reaches it. Every restart starts a node on its desired images, which follow the upgraded control
plane, so no node is restarted on the `26.4.0-beta6` SPDK image with the new control plane's memory sizing.
