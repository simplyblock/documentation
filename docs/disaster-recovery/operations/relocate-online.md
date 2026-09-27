---
title: "Relocate (Online)"
description: "Online relocation of running workloads between sites without restart, with cross-cluster VM live migration and simplyblock volume migration (coming soon)."
weight: 10450
---

An online relocation would move a running application from one site to another without stopping it. This is not
available in simplyblock DR today.

!!! info "Coming soon"
    Online relocation will migrate running workloads across clusters without a restart:

    - **Live VM migration:** Cross-cluster live migration of KubeVirt virtual machines, so that a VM keeps running
      while it moves to the other site.
    - **Live volume migration:** Migration of simplyblock volumes between storage clusters while they stay in use.

    This capability is not designed yet. Today, every move between sites is a
    [restart-based relocation](relocate-restart.md): the application is stopped on the source and restarted on the
    target after a final sync.

    Within a single storage cluster, simplyblock volumes can already be migrated online between storage nodes. See
    [Volume Migration](../../kubernetes/operations/volumes/volume-migration.md).
