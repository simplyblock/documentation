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

## Upgrading cli

As a first step, you need to upgrade the cli on all nodes (control plane and storage plane):
```bash
sudo pip install {{ cliname }} --upgrade
```

## Upgrading a Control Plane

This section outlines the process of upgrading the control plane. An upgrade introduces new versions of the management
and monitoring services.

To upgrade a control plane, the following command must be executed:

```bash
sudo {{ cliname }} cluster update <CLUSTER_ID> --cp-only=true --restart=true
```

After issuing the command, the individual management services will be upgraded and restarted on all management nodes. 

## Upgrading a Storage Plane

Now to upgrade the storage plane, the following steps are performed for each of the storage nodes. First you run on the control plane:

```bash
sudo {{ cliname }} storage-node suspend <NODE_ID>
sudo {{ cliname }} storage-node shutdown <NODE_ID> 
```
If shutdown does not work, you may savely use:
```
sudo {{ cliname }} storage-node shutdown <NODE_ID> --force 
```
Make sure the node is really offline:
```
sudo {{ cliname }} storage-node list 
```

In the next step, you need to ssh into the storage node and run locally:
```
sudo {{ cliname }} storage-node deploy [--isolate-cores] --if-name <IFNAME>
```
From the control plane host again, restart the node then:
```
sudo {{ cliname }} storage-node restart <NODE-ID> 
```
Once the node is restarted, wait for 2 minutes and then continue with the next node.  


