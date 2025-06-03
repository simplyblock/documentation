---
title: Storage Plane
weight: 30200
---

## Fresh Cluster Cannot Be Activated

**Symptom:** After a fresh deployment, the cluster cannot be activated. The activation process hangs or fails, and the
storage nodes show `n/0` disks available in the disks column (`{{ cliname }} storage-node list`).

1. Shutdown all storage nodes: `{{ cliname }} storage-node shutdown --force`
2. Force remove all storage nodes: `{{ cliname }} storage-node remove --force`
3. Delete all storage nodes: `{{ cliname }} storage-node delete`
4. Re-add all storage nodes. The disks should become active.
5. Try to activate the cluster.

## Storage Node Health Check Shows Health=False

**Symptom:** The storage node health check returns _health=false_ (`{{ cliname }} storage-node list`).

1. First run `{{ cliname }} storage-node check`.
2. If the command keeps showing an unhealthy storage node, _suspend_, _shutdown_, and restart the storage node.

!!! danger
    Never shutdown or restart a storage node while the cluster is in **rebalancing** state. This can lead to potential
    I/O operation. This is independent of the cluster's high-availability status.<br/><br/ >
    Check the cluster status with any of the following commands:

    ```bash
    {{ cliname }} cluster list
    {{ cliname }} cluster get <cluster-id>
    {{ cliname }} cluster show <cluster-id>
    ```
