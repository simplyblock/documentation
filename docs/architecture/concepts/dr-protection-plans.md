---
title: "DR Protection Plans"
description: "A protection plan declares the DR sites, the storage classes to protect, the replication methods, and the S3 stores. DR paths declare the allowed directions."
weight: 30900
---

A protection plan is the central configuration object of simplyblock Disaster Recovery (DR). It describes which
sites take part in disaster recovery, which simplyblock storage is protected, how data is replicated between the
sites, and where metadata and backups are kept in S3. A protection plan is a cluster-scoped `ProtectionPlan` resource
on the DR hub. The directions in which applications may move between the sites of a plan are declared separately as
DR paths. From both, the DR hub derives all lower-level Ramen and csi-addons objects, so these are never written by
hand.

## Sites

A site is a Kubernetes cluster that is registered with the DR hub through Open Cluster Management (OCM). A plan lists
between two and sixteen sites. Every site has a name that is used throughout the DR configuration and names the
managed cluster it runs on. Optionally, a site records the zone and region of its nodes, which correspond to the
`topology.kubernetes.io/zone` and `topology.kubernetes.io/region` node labels, and the namespace of its Velero
installation.

## Storage Profile

The storage profile selects the simplyblock storage that the plan protects. It consists of a label selector for
storage classes and, optionally, a separate selector for volume snapshot classes (by default, the storage class
selector is used for both). Only a single label, for example, `simplyblock.io/replicated: "true"`, has to be set on
the classes. The DR hub adds all further labels that Ramen needs.

The storage profile also decides whether the volumes of an application are replicated as one consistency group.
Consistency groups are enabled by default, so all volumes of an application are captured at the same point in time.

## Replication Methods

A plan declares between one and eight replication methods, each with a name. A protected application uses exactly
one method of its plan.

| Method type   | Also known as | Behavior                                                                                              |
|---------------|---------------|-------------------------------------------------------------------------------------------------------|
| `sync`        | Metro DR      | Volumes are written synchronously to both sites. Both sites share one storage identity.               |
| `async`       | Regional DR   | Volumes are replicated at a fixed scheduling interval, for example, every 5 minutes.                  |
| `snapshot-s3` | Backup        | Application objects and volume records are backed up to S3 on a cron schedule with a retention count. |

A plan cannot mix `sync` and `async` methods, since a storage class carries exactly one storage identity. A
`snapshot-s3` method can be declared alongside either of them. The replication types and their parameters are
described in [Replication Types](../../disaster-recovery/configuration/replication-types.md).

## S3 Profiles

Ramen stores the Kubernetes metadata of protected volumes, and Velero stores the captured Kubernetes objects, in an S3
bucket per site. A plan either names an existing Ramen S3 profile or declares one S3 store per site with bucket,
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

## What Is Derived

From a plan and its paths, the DR hub derives and maintains:

- **DR clusters:** One Ramen DRCluster per site.
- **DR policies:** One Ramen DRPolicy per pair of sites connected by a path and per replication method (not for
  `snapshot-s3`).
- **Class labels:** Storage identity and replication labels on the selected storage classes and volume snapshot
  classes on every site.
- **Replication classes:** For `async` methods, the VolumeReplicationClass and VolumeGroupReplicationClass on each
  site. For `sync` methods, both sites receive the same storage identity instead.
- **S3 profiles:** The Ramen S3 profiles for the declared per-site stores.

A plan reports `Ready` once all derived objects are in place, the site agents report their inventory, and Ramen has
paired the storage classes of both sides.

## Further Reading

- [Protection Plans](../../disaster-recovery/configuration/protection-plans.md)
- [DR Applications](dr-applications.md)
- [Failover](failover.md)
- [Relocation](relocation.md)
