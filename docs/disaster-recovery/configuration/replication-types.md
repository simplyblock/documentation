---
title: "Replication Types"
description: "Synchronous, asynchronous, and snapshot-s3 protection in simplyblock Disaster Recovery: use cases, prerequisites, recovery points, and constraints."
weight: 10210
---

A protection plan declares one or more replication methods. Each method has a type that decides how the data of a
protected application reaches the other site: synchronous replication for metro distances, asynchronous replication
for regional distances, or periodic backups to S3 for the loss of all sites. The type determines the achievable
recovery point, the failover behavior, and the storage prerequisites.

Methods are declared in `spec.methods[]` of a [protection plan](protection-plans.md), and each protected application
uses exactly one of them.

## Comparison

| Property         | `sync` (Metro-DR)                                                     | `async` (Regional-DR)                                                              | `snapshot-s3` (backup and restore)                                    |
|------------------|-----------------------------------------------------------------------|------------------------------------------------------------------------------------|-----------------------------------------------------------------------|
| Use case         | Two datacenters at metro distance                                     | Geographically separated sites                                                     | Loss of the hub and all sites, ransomware                             |
| Mechanism        | csi-addons VolumeReplication and VolumeGroupReplication, NetworkFence | csi-addons VolumeReplication and VolumeGroupReplication with a scheduling interval | Velero backups of objects and volume records to S3 on a cron schedule |
| Storage identity | Same storage ID on both sites                                         | Different storage ID per site                                                      | Not applicable                                                        |
| Recovery point   | Zero data loss while in sync                                          | Bounded by the scheduling interval                                                 | Bounded by the backup schedule                                        |
| Failover         | Requires fencing of the source (feature gate)                         | Available without fencing                                                          | Restore onto the rebuilt source site only                             |
| Failback         | Relocate along the reverse path                                       | Relocate along the reverse path                                                    | None                                                                  |
| Ramen DRPolicy   | Yes, without interval                                                 | Yes, with interval                                                                 | No                                                                    |

## Synchronous Replication

Synchronous replication (type `sync`) is Ramen's Metro-DR. Every write is acknowledged only after it has reached both
sites, so a failover while the replication is in sync loses no data.

- **Topology:** Two site clusters that share the same storage identity. The storage is stretched across both sites,
  and `dr-hub` labels the selected StorageClasses on both sites with the same storage ID (`sb-sync-<hash>`).
- **Distance:** Synchronous replication adds the round trip between the sites to every write. It is intended for
  sites at metro distance with low latency between them.
- **Fencing:** Before a failover, the source site must be fenced from the storage with a csi-addons NetworkFence, so
  that it cannot write to the volumes after the target has taken over.
- **Recovery point:** Only whether the replication is in sync is tracked. There is no RPO number for a sync method.

```yaml title="Synchronous method in a protection plan"
methods:
  - name: sync
    type: sync
```

!!! info "Coming soon"
    The NetworkFence pre-flight check for failovers under synchronous replication is behind the `metroFencing`
    feature gate in `DRConfig.spec.featureGates` until the csi-addons fencing support of the simplyblock CSI driver is
    available. Unplanned failovers of synchronously replicated applications have not been validated yet.

## Asynchronous Replication

Asynchronous replication (type `async`) is Ramen's Regional-DR. The storage replicates volume snapshots to the other
site at a fixed interval, set by `schedulingInterval` (for example, `5m`, `1h`, or `1d`).

- **Topology:** Two independent site clusters, each with its own simplyblock storage cluster. `dr-hub` gives the
  StorageClasses of every site a different storage ID (`sb-<hash>`) and creates a VolumeReplicationClass and a
  VolumeGroupReplicationClass per method on each site.
- **Distance:** No latency limit applies, because writes are acknowledged locally.
- **Recovery point:** A failover loses at most the writes since the last completed replication, which is normally at
  most one interval. The achieved RPO of a failover is recorded in its report.
- **Readiness:** If the last group sync of an application is older than 1.5 times the scheduling interval, the
  `ramen-healthy` readiness check fails, and the application is `NotReady` for actions until the replication catches
  up or an administrator overrides the verdict.

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

## Backup and Restore to S3

The type `snapshot-s3` takes periodic backups of every application of the plan into the S3 store of its site, on a
cron schedule. It protects against the loss of the hub and all sites at once, for example, by a ransomware attack, when
only the object storage remains.

- **Schedule:** `snapshotS3.schedule` is a five-field cron expression. `snapshotS3.retention` is the number of
  complete backup sets that are kept.
- **Content:** Each backup set consists of two Velero backups, one with the Kubernetes objects and one with the volume
  records. The backups are stored below `simplyblock-dr/backups` in the site's S3 store, or in the store named by
  `snapshotS3.s3ProfileName`.
- **Restore:** After all clusters are rebuilt and the hub state is restored, an administrator creates a RestoreAction
  per application. The application is restored onto its source site, as a whole, and protected again. There is no
  failback, and no restore to a different site. See [Backup and Restore](../operations/backup-restore.md).
- **Recovery point:** Bounded by the backup schedule. The RestoreAction reports an upper bound of the data loss.

```yaml title="Backup method every five minutes, keeping three sets"
methods:
  - name: backup-5m
    type: snapshot-s3
    snapshotS3:
      schedule: "*/5 * * * *"
      retention: 3
```

!!! info "Coming soon"
    The integration of `snapshot-s3` with the simplyblock volume backup backend is not yet available. The method
    schedules and restores the Velero object backups, but the volume data is not yet shipped by simplyblock storage.

## Combining Methods

The following rules apply when a plan declares several methods:

- **No sync and async mix:** A plan cannot contain both `sync` and `async` methods. A StorageClass carries exactly one
  storage ID, which is shared by both sites for sync and differs per site for async.
- **One mode per cluster pair:** Two plans cannot use sync and async for the same pair of clusters. Ramen does not
  support both modes between the same two clusters.
- **Backups alongside:** A `snapshot-s3` method can be added to a plan with either sync or async methods. It
  applies to every application of the plan.
- **Changing the mode:** Switching an application from async to sync is a storage migration outside of disaster
  recovery. The application must be protected again under a new plan.

## Prerequisites per Type

| Prerequisite                                             | `sync`           | `async` | `snapshot-s3` |
|----------------------------------------------------------|------------------|---------|---------------|
| simplyblock CSI with csi-addons VolumeReplication        | Yes              | Yes     | No            |
| VolumeGroupReplication (with consistency groups enabled) | Yes              | Yes     | No            |
| csi-addons NetworkFence                                  | Yes              | No      | No            |
| Shared storage identity across both sites                | Yes              | No      | No            |
| Network path for storage replication between sites       | Yes, low latency | Yes     | No            |
| S3 store per site                                        | Yes              | Yes     | Yes           |

The hardware, network, and S3 requirements are described in
[Disaster Recovery Requirements](../../deployment-preparation/dr-requirements.md).
