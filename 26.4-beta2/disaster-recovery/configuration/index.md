---
title: "Configuration"
description: "The configuration model of simplyblock Disaster Recovery: DR configuration, protection plans, DR paths, protected applications, tiers, hooks, and Recipes."
source: "https://docs.simplyblock.io/latest/disaster-recovery/configuration/"
---

# Configuration

Simplyblock Disaster Recovery is configured entirely through Kubernetes custom resources on the hub cluster, in the
API groups `dr.simplyblock.io/v1alpha1` and `sitemap.simplyblock.io/v1alpha1`, by `kubectl` or through the
[Control Center](../control-center.md). The resources describe which sites exist, how data moves between them, in
which directions applications may move, and how each application is started on the target site.

## Configuration Model

The configuration is layered. Each layer references the one above it:

1. **DRConfig:** The cluster-scoped singleton `default` holds hub-wide settings: the S3 archive and state bundle, the
   retention of finished runs, the agent settings (including the image allow list for hook Jobs), and feature gates.
   It is created by the hub chart (see [Installing the Hub](../install/hub.md)).
2. **ProtectionPlan:** A cluster-scoped plan declares a set of sites, the protected StorageClasses, the replication
   methods (sync, async, or snapshot-s3), and the S3 stores of the sites. See [Protection Plans](protection-plans.md)
   and [Replication Types](replication-types.md).
3. **DRPath:** A cluster-scoped path declares one direction between two sites of a plan and the actions allowed
   along it (Failover, Relocate, Test). Directions are declared, never inferred. See [DR Paths](paths.md).
4. **ProtectedApplication:** A namespaced resource binds one application to a plan, with a source site, one target
   site, and a method. It also declares health probes and dependencies. See
   [Protected Applications](applications.md).
5. **Tiers, hooks, and Recipes:** Within a protected application, tiers define the boot order on the target site, and
   external hooks run steps outside the cluster, such as DNS changes. A hand-written Recipe can replace the tiers when
   more control is needed. See [Workflows and Recipes](workflows-and-recipes.md).

6. **Site profiles and mappings:** In the API group `sitemap.simplyblock.io/v1alpha1`, a SiteProfile per managed
   cluster describes the site and binds logical roles to its networks, and a DHCPServer names a DHCP server dr-hub
   renders reservations into. The site mapper translates the network attachments and guest addresses of virtual
   machines between the sites of a path. See [Site Profiles and Mappings](site-profiles.md).

Operational resources, such as RecoveryAction, RecoveryPlan, TestBubble, TestSchedule, and RestoreAction, build on
this configuration and are described in [Operations](../operations/index.md) and [Testing](../testing/index.md).

## Resource Overview

| Kind                   | Scope                     | Short name | Written by    |
|------------------------|---------------------------|------------|---------------|
| `DRConfig`             | Cluster (named `default`) | None       | `dr-admin`    |
| `ProtectionPlan`       | Cluster                   | `pplan`    | `dr-admin`    |
| `DRPath`               | Cluster                   | None       | `dr-admin`    |
| `ProtectedApplication` | Namespaced                | `papp`     | `dr-operator` |
| `SiteProfile`          | Cluster (one per cluster) | None       | `dr-admin`    |
| `DHCPServer`           | Cluster                   | None       | `dr-admin`    |

The relationships between the resources are:

```plain title="Relationships between the DR resources"
DRConfig "default"
ProtectionPlan "fra" ── sites: fra-a, fra-b ── methods: async-5m
 ├── DRPath "fra-a-to-fra-b"  (Failover, Relocate, Test)
 ├── DRPath "fra-b-to-fra-a"  (Relocate)
 └── ProtectedApplication "orders"  (source fra-a, target fra-b, method async-5m)
      ├── tiers
      └── health.probes, externalHooks
```

The concepts behind the resources are explained in [Protection Plans and Paths](../../architecture/concepts/dr-protection-plans.md)
and [Protected Applications](../../architecture/concepts/dr-applications.md).

## Pages in This Section

- [Replication Types](replication-types.md)
- [Protection Plans](protection-plans.md)
- [DR Paths](paths.md)
- [Protected Applications](applications.md)
- [Workflows and Recipes](workflows-and-recipes.md)
- [Site Profiles and Mappings](site-profiles.md)
- [Access Control](access-control.md)
