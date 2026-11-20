---
title: "Unified DataStore"
description: "simplyblock Unified DataStore runs simplyblock on LUNs of an FC, iSCSI, or NVMe-oF storage array that simplyblock provisions and fails over itself."
weight: 10115
---

{{experimental}}

A Unified DataStore runs a simplyblock cluster on LUNs of an existing storage array, with the array integrated into
the control plane. Every LUN is created, presented to several hosts, grown, cut off, and deleted by simplyblock
through an array plug-in. The array protects the data with its RAID, and simplyblock protects the access to it: when
a storage node fails, its LUN is taken over by a standby node within seconds, without a rebuild. On top of the LUNs,
the full simplyblock feature set is available, including Kubernetes-native volumes, snapshots and clones, QoS,
encryption, replication, and disaster recovery.

Arrays of Pure Storage, NetApp, Dell, HPE, IBM, Hitachi, Huawei, and Infinidat are supported, as well as Amazon EBS
volumes with Multi-Attach.

| Page                                                | Content                                                                                               |
|-----------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| [Architecture](architecture.md)                     | Components, LUN lifecycle, ownership of LUNs, LUN takeover after a node failure, and credentials      |
| [Deployment Preparation](deployment-preparation.md) | Supported arrays, array account, host connectivity, credential sources, and sizing                    |
| [Deployment on Kubernetes](deployment.md)           | Storing the array login, discovery with the array stated up front, review, approval, and provisioning |
| [Operations](operations.md)                         | Array registration, login rotation, capacity growth, node failures, node removal, and teardown        |
| [Array Plug-ins](array-plugins.md)                  | Every plug-in with its protocols, LUN sizes, login fields, and options                                |

A cluster on LUNs that are created and presented by the storage administrator instead is described in
[Storage Arrays](../architecture/concepts/storage-arrays.md).
