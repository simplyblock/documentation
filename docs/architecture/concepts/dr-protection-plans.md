---
title: "DR Protection Plans"
description: "A protection plan declares the DR sites, the storage classes to protect, the replication methods, and the S3 stores. DR paths declare the allowed directions."
weight: 30900
---

A protection plan is the central configuration object of simplyblock Disaster Recovery (DR). It describes which
sites take part in disaster recovery, which simplyblock storage is protected, how data is replicated between the
sites, and where metadata and backups are kept in S3. A protection plan is a cluster-scoped `ProtectionPlan` resource
on the DR hub. The directions in which applications may move between the sites of a plan are declared separately as
DR paths.

## Sites

A site is a Kubernetes cluster that is registered with the DR hub through Open Cluster Management (OCM). A plan lists
between two and sixteen sites. Every site has a name that is used throughout the DR configuration and names the
managed cluster it runs on. The whole cluster is assigned to the site at once, so no node has to be labeled for DR.
Optionally, a site records a zone and a region, and the namespace of its Velero installation. Within one plan, a
site is exactly one cluster and a cluster is exactly one site. The same cluster can be a site in several plans.

## Storage Profile

The storage profile selects the simplyblock storage that the plan protects. It consists of a label selector for
storage classes and, optionally, a separate selector for volume snapshot classes (by default, the storage class
selector is used for both). Only a single label, for example, `simplyblock.io/replicated: "true"`, has to be set on
the classes.

The storage profile also decides whether the volumes of an application are replicated as one consistency group.
Consistency groups are enabled by default, so all volumes of an application are captured at the same point in time.

## Replication Methods

A plan declares between one and eight replication methods, each with a name. A protected application uses exactly
one method of its plan.

| Method type   | Also known as | Behavior                                                                                              |
|---------------|---------------|-------------------------------------------------------------------------------------------------------|
| `sync`        | Metro DR      | Volumes are written synchronously to both sites.                                                      |
| `async`       | Regional DR   | Volumes are replicated at a fixed scheduling interval, for example, every 5 minutes.                  |
| `snapshot-s3` | Backup        | Application objects and volume records are backed up to S3 on a cron schedule with a retention count. |

A plan cannot mix `sync` and `async` methods. A `snapshot-s3` method can be declared alongside either of them. The replication types and their parameters are
described in [Replication Types](../../disaster-recovery/configuration/replication-types.md).

### Storage-Level and Application-Level Protection

The replication methods protect whole applications. Simplyblock DR replicates the Kubernetes objects of an
application together with its volumes, restarts the application on the target site in a defined order, checks its
health, and fails it back.

Underneath, asynchronous replication between simplyblock clusters is snapshot-based. At every interval, a
copy-on-write snapshot of each volume is taken on the source cluster and transferred to the target cluster, where the
snapshots form an incremental chain. The data gap after an unplanned failover therefore equals the replication
interval plus any time the replication was behind schedule.

The same storage-level replication can also be used on its own, without simplyblock DR, per volume between two
storage clusters of one control plane. Volumes of one cluster can replicate to different target clusters and on
different schedules. Typical uses are disaster recovery with an RPO of minutes for volumes whose applications are
recovered by other means, the distribution of data to other sites, and the migration of volumes to another cluster.
See [Asynchronous Replication](../../kubernetes/operations/data-protection/asynchronous-replication.md).

## S3 Profiles

The Kubernetes metadata of protected volumes and the captured Kubernetes objects are stored in an S3 bucket per
site. A plan either names an existing Ramen S3 profile or declares one S3 store per site with bucket,
endpoint, region, credentials Secret, and optional CA certificates. Every S3-compatible object store can be used.
The per-site stores must cover exactly the sites of the plan.

## DR Paths

A DR path declares one direction, from a source site to a target site, together with the actions that are allowed
along it: `Failover`, `Relocate`, and `Test`. Directions are declared, never inferred. An action that a path does not
list is refused and cannot be overridden. A return direction is a separate path. For example, a plan can allow
failover and testing from `fra-a` to `fra-b`, but only a planned relocation back from `fra-b` to `fra-a`.

A path that allows tests carries the test settings, such as an isolated network attachment for the test bubble.
Failback is always a relocation along the reverse path. See
[DR Paths](../../disaster-recovery/configuration/paths.md).

## Plan Readiness

A plan reports `Ready` once its configuration is in place on all sites, the site agents report their inventory, and
the storage classes of both sides are paired.

## Further Reading

- [Protection Plans](../../disaster-recovery/configuration/protection-plans.md)
- [DR Applications](dr-applications.md)
- [Failover](failover.md)
- [Relocation](relocation.md)
