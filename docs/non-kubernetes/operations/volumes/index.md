---
title: "Volumes"
description: "Operate simplyblock logical volumes outside Kubernetes: migrate one between storage nodes, reconnect it, reclaim blocks, and limit its IOPS and throughput."
weight: 10300
---

The lifecycle of a logical volume, from provisioning to deletion, is covered under [Usage](../../usage/index.md). This
section covers what is operated on an existing volume: moving it between storage nodes, re-establishing its NVMe-oF
connections, reclaiming the blocks its filesystem no longer uses, and capping the performance it may consume.

| Topic                                                        | Purpose                                                                     |
|--------------------------------------------------------------|-----------------------------------------------------------------------------|
| [Volume Migration](volume-migration.md)                      | Moving a logical volume between storage nodes while it stays online.        |
| [Reconnecting Logical Volume](reconnect-nvme-device.md)      | Re-establishing the NVMe-oF connections of a volume after a node outage.    |
| [Trimming a Filesystem](trimming.md)                         | Reclaiming the unused blocks of a thin-provisioned logical volume.          |
| [Quality of Service Limits](limiting-iops-and-throughput.md) | Capping the IOPS and the throughput of a volume or a storage pool.          |
| [QoS Service Classes](qos-service-classes.md)                | Assigning volumes to a service class to guarantee its share of the cluster. |
