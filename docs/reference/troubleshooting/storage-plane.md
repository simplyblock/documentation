---
title: Storage Plane
description: "Storage Plane: Symptom: After a fresh deployment, the cluster cannot be activated."
weight: 30200
---

## Fresh Cluster Cannot Be Activated

**Symptom:** After a fresh deployment, the cluster cannot be activated. The activation process hangs or fails, and the
storage nodes show `n/0` disks available in the disks column (`{{ cliname }} storage-node list`).

1. Remove all storage nodes: `{{ cliname }} storage-node remove <NODE_ID>`. The node must be online or
   suspended; the removal shuts the node down itself. (`--force-remove` does not force a removal — it only
   cancels active tasks of the node.)
2. Delete all storage nodes: `{{ cliname }} storage-node delete <NODE_ID>`
3. Re-add all storage nodes. The disks should become active.
4. Try to activate the cluster.

## Storage Node Health Check Shows Health=False

**Symptom:** The storage node health check returns _health=false_ (`{{ cliname }} storage-node list`).

1. First run `{{ cliname }} storage-node check <NODE_ID>`.
2. If the command keeps showing an unhealthy storage node, _shutdown_ and _restart_ the storage node.

!!! danger
    Never shutdown or restart a storage node while the cluster is in **degraded** state. This can lead to potential
    I/O operation. This is independent of the cluster's high-availability status.<br/><br/ >
    Check the cluster status with any of the following commands:

    ```bash
    {{ cliname }} cluster list
    {{ cliname }} cluster get <cluster-id>
    {{ cliname }} cluster show <cluster-id>
    ```
