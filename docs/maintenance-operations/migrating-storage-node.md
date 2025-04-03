---
title: "Migrating a Storage Node"
weight: 20000
---

Simplyblock storage clusters are designed as always on. That means that a storage node migration is an online operation
which doesn't require explicit maintenance windows or storage downtime.

## Storage Node Migration

Migrating a storage node is a three-step process. First, the new storage node will be pre-deployed, then the old node
will be restarted with the new node address, and finally, the new storage node will become the primary storage node.

!!! warning
    Between each process step, it is required to wait for storage node migration tasks to complete. Otherwise, there
    may be impact to the system's performance or worse, may lead to data loss.

As part of the process, the existing storage node id will be moved to the new host machine. All logical volumes
allocated on the old storage node will be moved to the new storage node and automatically be reconnected.

### First-Stage Storage Node Deployment

To install the first stage of a storage node, the installation guide according to the selected environment should be
followed.

The process will diverge after the initial deployment command `sbcli storage-node deploy` has been executed. If the
command finishes successfully, resume from the next section of this page.

- [Kubernetes](../deployments/kubernetes/install-simplyblock/index.md)
- [Bare Metal or Virtualized Linux](../deployments/baremetal/index.md)
- [AWS EC2](../deployments/aws-ec2/index.md)

### Restart Old Storage Node

To start the migration process of logical volumes, the old storage node needs to be restarted with the new storage
node's API address.

In this example, it is assumed the new storage node's IP address to be _192.168.10.100_. The IP address must be changed
according to the real-world setup.

!!! danger
    Providing the wrong IP address can lead to service interruption and data loss.

To restart the node, the following command must be run:

```bash title="Restarting a storage node to initiate the migration"
sbcli storage-node restart <NODE_ID> --node-addr=<NEW_NODE_IP>:5000
```

!!! warning
    The parameter `--node-addr` expects the API endpoint of the new storage node. This API is reachable on port _5000_.
    It must be ensured that the given parameter is the new IP address and the port, separated by a colon.

```plain title="Example output of the node restart"
<missing>
```

### Make new Storage Node Primary

After the migration has successfully finished, the new storage node must be made the primary storage node for the owned
set of logical volumes.

This can be initiated using the following command:

```bash title="Make the new storage node the primary"
sbcli storage-node make-primary <NODE_ID>
```

Following is the example output.

```plain title="Example output of primary change"
<missing>
```

At this point the old storage node is automatically removed from the cluster and the storage node id is taken over by
the new storage node. Any operation on the old storage node, such as an OS reinstall, can be safely executed.
