---
title: "Relocate (Online)"
description: "Online relocation of running workloads between sites without restart: cross-cluster VM live migration (coming soon) and online volume migration."
source: "https://docs.simplyblock.io/latest/disaster-recovery/operations/relocate-online/"
---

# Relocate (Online)

An online relocation moves a running application from one site to another without stopping it.

Simplyblock volumes already move between storage clusters of one control plane while they stay in use, with an
[online cluster migration](../../kubernetes/operations/data-protection/online-cluster-migration.md). The cutover of each
volume holds I/O for a brief freeze, and the workload keeps running.

!!! info "Coming soon"
    **Live VM migration:** Cross-cluster live migration of KubeVirt virtual machines, so that a VM keeps running while
    it moves to the other site, is not available yet. Until then, a recovery action of simplyblock DR moves an
    application between sites with a [restart-based relocation](relocate-restart.md): the application is stopped on
    the source and restarted on the target after a final sync.

    Within a single storage cluster, simplyblock volumes can already be migrated online between storage nodes. See
    [Volume Migration](../../kubernetes/operations/volumes/volume-migration.md).
