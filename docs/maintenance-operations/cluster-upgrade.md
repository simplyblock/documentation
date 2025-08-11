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

Upgrading the control plane and storage cluster is currently not an online operation and requires downtime. Planning an
upgrade as part of a maintenance window is recommended. They should be an online operation from next release.

## Upgrading the CLI

Before starting a cluster upgrade, all storage and control plane nodes must update the CLI ({{ cliname }}).

This can be achieved using the same command used during the intial installation. It is important, though, to provide
the `--upgrade` parameter to pip to ensure an upgrade to happen.

```bash
sudo pip install {{ cliname }} --upgrade
```

## Upgrading a Control Plane

This section outlines the process of upgrading the control plane. An upgrade introduces new versions of the management
and monitoring services.

To upgrade a control plane, the following command must be executed:

```bash
sudo {{ cliname }} cluster update <CLUSTER_ID> --cp-only true
```

After issuing the command, the individual management services will be upgraded and restarted on all management nodes. 

## Upgrading a Storage Plane

Now to upgrade the storage plane, the following steps are performed for each of the storage nodes. From the control plane, 
issue the following commands.

!!! warning
    Ensure not all storage nodes are offline at the same time. Storage nodes must be updated in a round-robin fashion. In
    between, it is important to wait until the cluster has stabilized again and potential rebalancing operations have
    finished before starting to upgrade the next storage node.

```bash
sudo {{ cliname }} storage-node suspend <NODE_ID>
sudo {{ cliname }} storage-node shutdown <NODE_ID> 
```

If the shutdown doesn't work by itself, you may savely force a shutdown using the `--force` parameter.

```bash
sudo {{ cliname }} storage-node shutdown <NODE_ID> --force 
```

Ensure the node has become offline before continuing.

```bash
sudo {{ cliname }} storage-node list 
```

Next up, on the storage node itself, a redployment must be executed. To achieve that, ssh into the storage node and run the following command.

```bash
sudo {{ cliname }} storage-node deploy
```

Finally, the new storage node deployment can be restarted from the control plane.

```bash
sudo {{ cliname }} --dev storage-node restart <NODE-ID> --spdk-image <UPGRADE SPDK IMAGE>
```

!!! note
    One can find the upgrade spdk image from env_var file on storage node, location: /usr/local/lib/python3.9/site-packages/simplyblock_core/env_var

Once the node is restarted, wait until the cluster is stabilized. Depending on the capacity of a storage node, this can take a few minutes.
The status of the cluster can be checked via the cluster listing or listing the tasks and checkking their progress.

```bash
sudo {{ cliname }} cluster list
sudo {{ cliname }} cluster list-tasks <CLUSTER_ID>
```


