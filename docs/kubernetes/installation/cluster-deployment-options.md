---
title: "Cluster Deployment Options"
description: "The options of a simplyblock storage cluster deployed by the operator: what is set in the deployment document, what is fixed at creation, and what can change."
weight: 30120
---

A storage cluster is deployed by the Simplyblock Operator from a `ClusterDeploymentConfig`, the deployment
document described in [Create a Storage Cluster](k8s-storage-plane.md). Its `spec.cluster` section holds the options
of the new cluster, which the operator copies into the `StorageCluster` it creates. Most of them describe the on-disk
or on-wire layout and cannot be changed afterward, so they are planned before the document is approved.

## Options Fixed at Creation

The following options are set in `spec.cluster` of the deployment document and cannot be changed on the running
cluster.

| Option                                     | Description                                                                                                                                                                            |
|--------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `stripe.dataChunks`, `stripe.parityChunks` | The [erasure coding scheme](../../deployment-preparation/erasure-coding-scheme.md), for example, `4+1` or `2+2`. It applies to all volumes of the cluster.                             |
| `clusterMode`                              | `Standard` (default), `Single` for a one-node cluster, or `Dual` for a two-node cluster (see [Deploying Edge Clusters](edge-clusters.md)).                                             |
| `fabricType`                               | The NVMe-oF transport the cluster serves volumes over, for example, `tcp` or `rdma`.                                                                                                   |
| `enableFailureDomains`                     | Spreads data, journal copies, and failover paths across [failure domains](../../architecture/concepts/failure-domains.md). Every group of the document then names its `failureDomain`. |
| `enableJournalDevice`                      | Dedicates the smallest device of each worker to the journal, instead of a journal partition on every device. Required for Linux block devices.                                         |
| `enableChecksumValidation`                 | Inline CRC validation of every I/O, which detects silent data corruption.                                                                                                              |
| `enableAtomicity4K`                        | Enforces 4K write atomicity on devices with a smaller logical block size, so that checksum validation can run on them. Requires `enableChecksumValidation`.                            |
| `socketsToUse`, `nodesPerSocket`           | The NUMA sockets used on each worker and the number of storage nodes per socket (see [NUMA Considerations](../../deployment-preparation/numa-considerations.md)).                      |
| `enableNodeAffinity`                       | Serves a volume's I/O from the devices of its own node where possible (see [Configuring Node Affinity](../operations/cluster/node-affinity.md)).                                       |
| `kms`                                      | An external key management system for the volume encryption keys (see [External Key Management](../../architecture/concepts/external-key-management.md)).                              |

## Sizing Options

| Option                   | Description                                                                                                                                                                                                        |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `vcpuCount`              | Required. The vCPUs each storage node dedicates to the data plane, at least 4.                                                                                                                                     |
| `minHugePagesSize`       | The minimum huge page memory of each storage node, for example, `16G`. The effective allocation is the larger of this value and the computed minimum.                                                              |
| `maxSubsystemCount`      | Required. The maximum number of NVMe-oF subsystems per storage node, which sizes the huge page memory. It can be raised later and reaches each node at its next restart (see [Limits](../../reference/limits.md)). |
| `nodeProvisioningBudget` | How many workers are added to the cluster in parallel.                                                                                                                                                             |
| `enableDriveFormat`      | Formats every listed device before use. **Destructive.**                                                                                                                                                           |

## Options That Can Change Later

The following options are set in the deployment document or later on the `StorageCluster`:

| Option                                  | Where                         | Description                                                                                                                                                                                                                                                          |
|-----------------------------------------|-------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `backup`                                | Document and `StorageCluster` | The S3 store backups are written to (see [Backup and Recovery](../operations/data-protection/backup-recovery.md)).                                                                                                                                                   |
| `warningThreshold`, `criticalThreshold` | `StorageCluster`              | Capacity thresholds in percent: `capacity` for the used capacity and `provisionedCapacity` for the provisioned capacity. Above the critical used capacity, the cluster turns read-only. Above the critical provisioned capacity, volumes cannot be created or grown. |
| Service classes                         | `StorageCluster`              | The relative share of the cluster's I/O per class of volumes (see [Service Classes](../usage/service-classes.md)).                                                                                                                                                   |
| `maxConcurrentWorkerRestarts`           | `StorageCluster`              | How many workers the operator drains and restarts at once during maintenance.                                                                                                                                                                                        |

```yaml title="Capacity thresholds on the StorageCluster"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageCluster
metadata:
  name: simplyblock-cluster
  namespace: simplyblock
spec:
  warningThreshold:
    capacity: 85
    provisionedCapacity: 250
  criticalThreshold:
    capacity: 97
    provisionedCapacity: 500
```

For a large cluster, a critical capacity threshold of 99% is acceptable. For small clusters, below 50 TB, 97% leaves
more room. A provisioned capacity threshold of around 500% is typical for thin-provisioned volumes.

All fields are listed in the [Simplyblock Operator reference](../../reference/operator/index.md).
