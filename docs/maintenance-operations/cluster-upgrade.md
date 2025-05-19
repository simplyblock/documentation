---
title: "Upgrading a Cluster"
weight: 10600
---

Simplyblock clusters consist of two independent parts: a control plane with management nodes, and a storage plane with
storage nodes. A single control plane can be used to manage for multiple storage planes.

The control plane and storage planes can be updated independently. It is, however, not recommended to run an upgraded
control plane without upgrading the storage planes.

## Upgrading a Control Plane

If multiple storage planes are connected to a single control plane, it is recommended to upgrade the control plane
first.

To upgrade a control plane, the following command must be executed:

```bash
sudo {{ variables.cliname }} cluster update <CLUSTER_ID> --cp-only=true --restart=true
```

After issuing the command, the individual management services will be upgraded and restarted on all management nodes. 

## Upgrading a Storage Plane

!!! info
    If multiple storage planes are connected to a single control plane, it is recommended to upgrade the control plane
    first.

To upgrade a storage plane, the following command must be executed:

```bash
sudo {{ variables.cliname }} cluster update <CLUSTER_ID>
```
