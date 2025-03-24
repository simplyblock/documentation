---
title: "Replacing a Storage Node"
weight: 30200
---

A simplyblock storage cluster is designed to be always up. Hence, operations such as extending a cluster or
replacing a storage node are online operations and don't require a system downtime. However, there are a few
things to keep in mind when replacing a storage node.

## Starting the new Storage Node

It is always recommended to start the new storage node before removing the old one, even if the remaining
cluster has enough storage available to absorb the additional (temporary) storage requirement.

Every operation that changes the cluster topology comes with a set of migration tasks, moving data across
the cluster to ensure equal usage distribution.

If a storage node failed and cannot be recovered, adding a new storage node is perfectly fine, though.

To start a new storage node, follow the storage node installation according to your chosen set up:

- [Kubernetes](../../deployments/kubernetes/install-simplyblock/index.md)
- [Bare Metal Linux](../../deployments/baremetal/index.md)
- [AWS EC2](../../deployments/aws-ec2/index.md)

## Remove the old Storage Node

To remove the old storage node, use the `sbcli` command line tool. 

```bash title="Remove a storage node"
sbcli storage-node remove <NODE_ID>
```

Wait until the operation has successfully finished. Afterward, the storage node is removed from the cluster.

This can be checked again with the `sbcli` command line tool.

```bash title="List storage nodes"
sbcli storage-node list --cluster-id=<CLUSTER_ID>
```
