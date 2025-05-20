---
title: "Upgrading a Cluster"
weight: 10600
---

Simplyblock clusters consist of two independent parts: a control plane with management nodes, and a storage plane with
storage nodes. A single control plane can be used to manage for multiple storage planes.

The control plane and storage planes can be updated independently. It is, however, not recommended to run an upgraded
control plane without upgrading the storage planes.

!!! recommendation
    If multiple storage planes are connected to a single control plane, it is recommended to upgrade the control plane
    first.

Upgrading the control plane and storage cluster is an online operation and does not require downtime. Planning an
upgrade as part of a maintenance window is recommended, though.

## Upgrading a Control Plane

This section outlines the process of upgrading the control plane. An upgrade introduces new versions of the management
and monitoring services.

To upgrade a control plane, the following command must be executed:

```bash
sudo {{ variables.cliname }} cluster update <CLUSTER_ID> --cp-only=true --restart=true
```

After issuing the command, the individual management services will be upgraded and restarted on all management nodes. 

## Upgrading a Storage Plane

This section outlines the process of upgrading the storage plane, which is essential for maintaining data integrity,
performance, and compatibility with newer system components. A well-executed upgrade ensures continued reliability and
access to the latest features and fixes.

To upgrade a storage plane, the following command must be executed:

```bash
sudo {{ variables.cliname }} cluster update <CLUSTER_ID>
```
