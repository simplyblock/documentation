---
title: "Upgrading a Cluster"
description: "Upgrading a Cluster: Simplyblock clusters consist of two independent parts: a control plane with management nodes, and a storage plane with storage nodes."
weight: 10600
---

Simplyblock clusters consist of two independent parts: a control plane with management nodes, and a storage plane with
storage nodes. A single control plane can be used to manage multiple storage planes.

The control plane and storage planes can be updated independently. It is, however, not recommended to run an upgraded
control plane without upgrading the storage planes.

!!! recommendation
    If multiple storage planes are connected to a single control plane, it is recommended to upgrade the control plane
    first.

Upgrading the control plane and storage cluster is currently not an online operation and requires downtime. Planning an
upgrade as part of a maintenance window is recommended. This is expected to become an online operation in a future
release.

## Upgrading the CLI

Before starting a cluster upgrade, all storage and control plane nodes must update the CLI ({{ cliname }}).

This can be achieved using the same command used during the initial installation. It is important, though, to provide
the `--upgrade` parameter to pip to ensure the upgrade is performed.

```bash title="Upgrade {{ cliname }} via pip"
sudo pip install {{ cliname }} --upgrade
```

## Upgrading a Control Plane

This section outlines the process of upgrading the control plane. An upgrade introduces new versions of the management
and monitoring services.

To upgrade a control plane, the following command must be executed:

```bash title="Upgrade Control Plane"
sudo {{ cliname }} cluster update <CLUSTER_ID> --cp-only true
```

After issuing the command, the individual management services will be upgraded and restarted on all management nodes.

## Upgrading a Storage Plane

To upgrade the storage plane, perform the following steps for each storage node. From the control plane, issue the
following commands.

!!! warning
    Ensure not all storage nodes are offline at the same time. Storage nodes must be updated in a round-robin fashion. In
    between, it is important to wait until the cluster is in `ACTIVE` state again and finished with the `REBALANCING` task.

```bash title="Suspend and Shut Down Storage Node"
sudo {{ cliname }} storage-node suspend <NODE_ID>
sudo {{ cliname }} storage-node shutdown <NODE_ID> 
```

If the shutdown does not complete by itself, you may safely force a shutdown using the `--force` parameter.

```bash title="Force Shut Down Storage Node"
sudo {{ cliname }} storage-node shutdown <NODE_ID> --force 
```

Ensure the node has become offline before continuing.

```bash title="Verify Storage Node Offline State"
sudo {{ cliname }} storage-node list 
```

Next, a redeployment must be executed on the storage node itself. To do so, SSH into the storage node and run the
following command.

```bash title="Redeploy Storage Node"
sudo {{ cliname }} storage-node deploy
```

Finally, the new storage node deployment can be restarted from the control plane.

```bash title="Restart Upgraded Storage Node"
sudo {{ cliname }} --dev storage-node restart <NODE-ID> \
    --spdk-image <UPGRADE SPDK IMAGE>
```

!!! note
    You can find the upgrade SPDK image in the `env_var` file on the storage node at:
    
    ```plain
    /usr/local/lib/python3.9/site-packages/simplyblock_core/env_var
    ```

Once the node is restarted, wait until the cluster stabilizes. Depending on the capacity of a storage node, this can
take a few minutes.
The status of the cluster can be checked via the cluster listing or listing the tasks and checking their progress.

```bash title="Verify Cluster Stabilization"
sudo {{ cliname }} cluster list
sudo {{ cliname }} cluster list-tasks <CLUSTER_ID>
```
