---
title: "Replication Types"
description: "The five replication method types of simplyblock Disaster Recovery: sync, async, s3-backup, and their combinations, with use cases, recovery points, prerequisites, and constraints."
weight: 10210
---

A protection plan declares one or more replication methods. Each method has a type that decides how the data of a
protected application reaches the other site: synchronous replication between the zones of a stretch cluster,
asynchronous replication between two clusters, backups to S3, or a combination of replication and backups. The type
determines the achievable recovery point, the failover behavior, and the storage prerequisites.

Methods are declared in `spec.methods[]` of a [protection plan](protection-plans.md), and each protected application
uses exactly one of them. Every protection an application has is carried by that one method.

## Method Types

| Type              | Replication                                          | Backups to S3 | Data loss on unplanned failover |
|-------------------|------------------------------------------------------|---------------|---------------------------------|
| `sync`            | Synchronous, between the zones of a cluster          | No            | None                            |
| `sync-s3-backup`  | Synchronous, between the zones of a cluster          | Yes           | None                            |
| `async`           | Asynchronous, between two clusters                   | No            | Up to the scheduling interval   |
| `async-s3-backup` | Asynchronous, between two clusters                   | Yes           | Up to the scheduling interval   |
| `s3-backup`       | Through S3: the peer promotes from the newest backup | Yes           | Up to the backup interval       |

A combined type is one method with one replication class, not two methods. Each type has its own settings:

- **`schedulingInterval`:** For `async` and `async-s3-backup`, the replication interval, for example, `5m`, `1h`, or
  `1d`.
- **`s3Backup.interval`, `s3Backup.retention`:** For the three backup types, the backup interval in the same notation
  and the number of backups kept per volume. For `s3-backup`, the backup interval is also the scheduling interval.
- **`replicationParameters`:** Up to 16 parameters passed verbatim to the CSI driver, for every type.

The backup types need the plan's own site stores (`spec.s3Profiles`), because the storage writes the backups into them.

## Synchronous Replication

Synchronous replication (`sync`, `sync-s3-backup`) is a stretch cluster: one Kubernetes cluster that spans two zones,
with one simplyblock storage cluster underneath that writes every block to both zones. Every write is acknowledged
only after it has reached both zones, so a failover between the zones loses no data.

- **Sites:** The sites of a sync plan are the zones of one cluster. Every site names the same cluster and its own
  zone (`spec.sites[].zone`), matched against the node label `topology.kubernetes.io/zone`. The plan refuses sites
  on different clusters.
- **Protection:** A sync application is protected by dr-simplyblock end to end, without Ramen. dr-hub delivers a
  zone binding to the cluster, and dr-agent keeps every volume primary in the current zone and every Deployment,
  StatefulSet, and VirtualMachine pinned to it. The application must be `discovered`.
- **Moves:** A Relocate or Failover stops the workloads, demotes and promotes the volumes to the other zone, and
  starts the workloads pinned there. On a Failover, the nodes of a lost zone are tainted out of service, so their
  pods and volume attachments are released. The achieved RPO is zero.
- **Distance:** Synchronous replication adds the round trip between the zones to every write. It is intended for
  zones at metro distance with low latency between them.
- **Readiness:** The check `zone-protected` replaces `ramen-healthy`, and `storage-replicating` reads the volumes of
  the zone binding.

```yaml title="Synchronous method in a stretch cluster plan"
sites:
  - name: zone-a
    cluster: stretch
    zone: eu-central-1a
  - name: zone-b
    cluster: stretch
    zone: eu-central-1b
methods:
  - name: sync
    type: sync
```

!!! info "Coming soon"
    - **Stretched storage cluster type:** The stretched simplyblock storage cluster that a sync plan protects is not
      released yet. See [Stretched Storage Cluster](../../deployment-preparation/dr-requirements.md#stretched-storage-cluster).
    - **Managed applications:** GitOps-delivered applications on a sync plan are refused, because their GitOps owner
      would undo the pinning and scaling.
    - **Restore of a `sync-s3-backup` application onto a rebuilt stretch cluster.**

## Asynchronous Replication

Asynchronous replication (`async`, `async-s3-backup`) is regional DR between two independent site clusters, each with
its own simplyblock storage cluster, under one simplyblock control plane. The storage replicates volume snapshots to
the other cluster at the scheduling interval.

- **Topology:** Two clusters that are managed by one simplyblock control plane. A replication target is named by the
  UUID of its storage cluster, so both storage clusters must belong to the same control plane.
- **Distance:** No latency limit applies, because writes are acknowledged locally.
- **Recovery point:** A failover loses at most the writes since the last completed replication, which is normally at
  most one interval. The achieved RPO of a failover is recorded in its report.
- **Readiness:** If the last group sync of an application is older than 1.5 times the scheduling interval, the
  `ramen-healthy` readiness check fails, and the application is `NotReady` for actions until the replication catches
  up or an administrator overrides the verdict.
- **Backend pairing:** dr-hub creates everything the simplyblock CSI driver needs on the clusters of a plan: a
  `ReplicationPair` and a `ReplicationPolicy` toward the peer storage cluster (through the Simplyblock Operator), one
  VolumeReplicationClass per direction of a DR path, and the replication Secret the csi-addons sidecar requires.
  Nothing has to be authored by hand.

```yaml title="Asynchronous method with a five-minute interval"
methods:
  - name: async-5m
    type: async
    schedulingInterval: 5m
```

A plan can declare several asynchronous methods with different intervals, for example, `async-5m` for critical
applications and `async-1h` for the rest. Each application then chooses one with `spec.method`.

!!! note
    The reported RPO lags behind the real one by up to one interval, because the last sync time is only updated once
    a replication cycle completes.

### How a Volume Moves

Under an asynchronous method, the volume of a protected PVC is replicated as a chain of snapshots: at every interval,
a snapshot is taken on the source and transferred into a landing copy on the target. A planned move demotes the
volume on the source, which fences its paths and ships a final snapshot, and promotes the landing copy on the target
as a new volume. An unplanned move promotes the newest replicated snapshot on the target. The PersistentVolume keeps
its original volume handle through every move, and the CSI driver resolves the chain behind the handle to the volume
that currently serves the data. Each move appends a member to that chain, and a fail-back re-aims the replication at
the previous member, so only the delta since the move is transferred back.

The chain is never compacted, so a volume that moved ten times sits ten members out from its handle. The CSI driver
follows the chain to its end however long it is and stops only on a loop. It acts on the member the operation
belongs to:

- **Demote and disable:** The newest member on the driver's own site, so that a demote on the old primary's site
  never fences the live primary on the other site. A member the storage has already removed counts as done.
- **Promote, resync, and replication status:** The active end of the chain, wherever it lives.
- **Attach:** The volume that currently serves the data, on whichever storage cluster holds it.

Because a moved volume's handle names the storage cluster it was created on, the CSI driver of every site must
reach every storage cluster of the plan. Each site's driver configuration (the secret
`simplyblock-csi-secret-v2` in the operator's namespace) lists both clusters, and the site's own cluster is marked
`local: true`.

!!! info "Coming soon"
    - **Automatic cross-registration:** The Simplyblock Operator registers every storage cluster of its control
      plane in the driver configuration itself and marks its own cluster as local.

## Backups to S3

The backup types (`s3-backup`, `sync-s3-backup`, `async-s3-backup`) make the storage back up every primary volume
into the S3 store of its site at the backup interval and keep `retention` backups per volume. They protect against
the loss of the hub and every site at once, for example, by a ransomware attack, when only the object storage remains.

- **Who backs up:** The storage cluster, as its own copy-on-write backups, keyed by the volume handle of the
  PersistentVolume. dr-hub schedules nothing and takes nothing. Ramen keeps the volume handle through every failover
  and relocation, so the key stays stable.
- **Store:** The site's own DR metadata store from `spec.s3Profiles`. A plan with a shared `spec.s3Profile` cannot
  use a backup type.
- **Restore:** A volume handle the storage does not know is restored from the newest backup of that handle in any
  store of the plan. For `s3-backup`, this is how a failover to the peer gets its data. It is also how a site rebuilt
  from scratch gets its data back. See [Backup and Restore](../operations/backup-restore.md).
- **Recovery point:** Bounded by the backup interval.

```yaml title="Asynchronous replication with backups every hour, keeping 24"
methods:
  - name: async-5m-backup
    type: async-s3-backup
    schedulingInterval: 5m
    s3Backup:
      interval: 1h
      retention: 24
```

```yaml title="Protection through S3 only"
methods:
  - name: vault-15m
    type: s3-backup
    s3Backup:
      interval: 15m
      retention: 96
```

!!! info "Coming soon"
    The backups of the backup types are implemented by the simplyblock CSI driver on the `integrate_csi_addons`
    branch of the Simplyblock Operator. On a released driver, the method is accepted, but no backup is written. Plans
    written for the earlier API (`snapshot-s3`) are refused by the CRD and must be rewritten.

## Combining Methods

The following rules apply when a plan declares several methods:

- **No sync and async mix:** A plan cannot contain synchronous and asynchronous types at once. A sync plan holds
  exactly one method.
- **One pair and one method per application:** An application is protected toward one target with one method. The
  method decides everything the storage does for it.
- **Changing the method:** Switching an application between methods or from async to sync is a new protection. The
  application must be protected again under a new ProtectedApplication, or, between sync and async, a new plan.

## Consistency Groups

With `storageProfile.consistencyGroups: Enabled`, the volumes of an application on its group StorageClasses are
replicated together with one consistency point (VolumeGroupReplication). Membership is a prerequisite the
application's owner meets before the PVCs are provisioned, and DR does not set or repair it:

- **Label:** The PVCs, or a StatefulSet's `volumeClaimTemplates`, carry the label
  `storage.simplyblock.io/consistency-group` before they are created.
- **One group per application and namespace:** Ramen creates one VolumeGroupReplication per namespace and group.
- **Readiness:** The blocking check `consistency-group-labels` fails when a PVC on a group StorageClass has no label,
  the PVCs of a namespace span two groups, or a group also holds PVCs of another namespace.

Consistency groups are disabled by default. A synchronous stretch volume is consistent across all volumes of an
application by construction and needs no group.

## Prerequisites per Type

| Prerequisite                                                 | `sync`, `sync-s3-backup` | `async`, `async-s3-backup` | `s3-backup` |
|--------------------------------------------------------------|--------------------------|----------------------------|-------------|
| Simplyblock CSI driver with csi-addons VolumeReplication     | Yes                      | Yes                        | Yes         |
| One simplyblock control plane managing both storage clusters | No                       | Yes                        | Yes         |
| Stretched simplyblock storage cluster across both zones      | Yes                      | No                         | No          |
| Network path for storage replication between the sites       | Yes, low latency         | Yes                        | No          |
| DR metadata bucket                                           | Yes                      | Yes                        | Yes         |
| Per-site S3 stores in the plan (`spec.s3Profiles`)           | For `sync-s3-backup`     | For `async-s3-backup`      | Yes         |

The hardware, network, and S3 requirements are described in
[Disaster Recovery Requirements](../../deployment-preparation/dr-requirements.md).
