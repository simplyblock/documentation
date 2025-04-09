---
title: Storage Plane
weight: 30200
---

## Fresh Cluster Cannot Be Activated

**Symptom:** After a fresh deployment, the cluster cannot be activated. The activation process hangs or fails and the
storage nodes show `n/0` disks available in the disks column (`{{ variables.cliname }} storage-node list`).

1. Shutdown all storage nodes: `{{ variables.cliname }} storage-node shutdown --force`
2. Force remove all storage nodes: `{{ variables.cliname }} storage-node remove --force`
3. Delete all storage nodes: `{{ variables.cliname }} storage-node delete`
4. Re-add all storage nodes. The disks should become active.
5. Try to activate the cluster.

## Storage Node Health Check Shows Health=False

**Symptom:** The storage node health check returns _health=false_ (`{{ variables.cliname }} storage-node list`).

1. First run `{{ variables.cliname }} storage-node check`.
2. If the command keeps showing an unhealthy storage node, _suspend_, _shutdown_, and restart the storage node.

!!! danger
    Never shutdown or restart a storage node while the cluster is in **rebalancing** state. This can lead to potential
    I/O operation. This is independent of the high-availability status of the cluster.<br/><br/>
    Check the cluster status with any of the following commands:

    ```bash
    {{ variables.cliname }} cluster list
    {{ variables.cliname }} cluster get <cluster-id>
    {{ variables.cliname }} cluster show <cluster-id>
    ```
