---
title: "Ransomware Recovery with Simplyblock DR"
description: "Video walkthrough: protect applications on two active sites with simplyblock DR, then rebuild the hub and both sites after a ransomware attack."
source: "https://docs.simplyblock.io/latest/tutorials/ransomware-recovery/"
---

# Ransomware Recovery with Simplyblock DR

This video tutorial shows how simplyblock Disaster Recovery (DR) protects applications across two active sites and
a hub, and how all three are rebuilt after a ransomware attack that has compromised every cluster. It takes about
three minutes and is organized in five chapters.

<video controls preload="metadata" width="100%" poster="../../assets/videos/ransomware-recovery-three-sites.jpg">
  <source src="../../assets/videos/ransomware-recovery-three-sites.mp4" type="video/mp4">
</video>

!!! note
    Sample applications, values, resource names, and commands in the video are illustrative. Some steps of the
    recovery chapter show capabilities that are not available yet, see [Available Today](#available-today).

## Chapters

1. **Install sites:** Site A and Site B each run an OpenShift or Kubernetes cluster with local NVMe devices and
   host virtual machines and containers side by side. Each site gets the Simplyblock Operator, its own control
   plane, and the CSI driver.
2. **Install hub:** A separate hub cluster runs simplyblock DR, which brings up Open Cluster Management and Ramen.
   Both sites join the hub.
3. **Protect apps:** One protection plan covers both sites with DR paths in both directions. Asynchronous
   replication provides fast failover between the sites, and periodic backups to S3 with object lock provide a
   recovery point that an attacker cannot delete.
4. **Monitor:** The readiness of every application, the replication state, and the backups are watched from the
   hub.
5. **Recover:** After the attack, every cluster is treated as compromised:
    1. **Cleanup:** The network is isolated, servers and drives are wiped, credentials and keys are rotated, and clean
       base clusters are rebuilt from infrastructure automation. Nothing from the old clusters is reused.
    2. **Bootstrap:** simplyblock is installed on both sites and simplyblock DR on the new hub. The sites rejoin
       the hub with new credentials.
    3. **Restore the DR state:** The signed DR state bundle from before the attack is read from the archive bucket,
       its signature is verified, and the protection plan and applications are restored on the new hub.
    4. **Select a clean restore point:** Replicas are not trusted, since the attack may have replicated encrypted
       data. The newest backup generation from before the first encrypted write is selected.
    5. **Recover in tier order:** Each application is restored on its home site from that generation, first the data
       tier, then the application and web tiers, each gated by its readiness checks.
    6. **Protect again:** Protection resumes from a new baseline, and the next DR state bundle is written to the
       archive.

## Available Today

The recovery in the video follows the procedure of simplyblock DR, with a few steps that are shown ahead of their
release:

- **Restoring the DR state:** Available with the `dr-restore` command line tool. A declarative restore of the hub
  state is planned.
- **Selecting a clean restore point:** The video shows every backup generation with a verification result from an
  isolated test restore, and a roadmap for automatic detection of encrypted generations. Both are planned. Today, a
  backup generation is selected by its time, and test failovers in an isolated bubble can be used to check it.
- **Site profiles:** The site mapping shown on the hub in the video is planned.

## In the Documentation

- [Archive and State Bundle](../disaster-recovery/install/archive.md): The archive bucket with object lock and the
  signed state bundles.
- [Hub Recovery](../disaster-recovery/operations/hub-recovery.md): Restoring the DR state onto a new hub.
- [Backup and Restore](../disaster-recovery/operations/backup-restore.md): Restoring applications onto rebuilt sites
  after the loss of the hub and every site.
- [Workflows and Recipes](../disaster-recovery/configuration/workflows-and-recipes.md): Tiers and readiness checks
  that define the recovery order.
- [Test Failover](../disaster-recovery/testing/test-failover.md): Tests in an isolated bubble.
- [Disaster Recovery Requirements](../deployment-preparation/dr-requirements.md): The hub, the sites, and the S3
  buckets.
