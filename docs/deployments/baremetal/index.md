---
title: "Plain Linux Initiators"
weight: 20200
---

Simplyblock storage can be attached over the network to Linux hosts which are not running Kubernetes, Proxmox or
OpenStack.

While no simplyblock components must be installed on these hosts, some OS-level configuration steps are required.
Those manual steps are typically taken care of by the CSI driver or Proxmox integration.

On plain Linux initiators, those steps have to be performed manually on each host that will connect simplyblock logical
volumes.

### Install NVMe Client Package

=== "RHEL / Alma / Rocky"

    ```bash
    sudo dnf install -y nvme-cli
    ```

=== "Debian / Ubuntu"

    ```bash
    sudo apt install -y nvme-cli
    ```

### Load the NVMe over Fabrics Kernel Modules

For NVMe over TCP and NVMe over RoCE:

{% include 'prepare-nvme-tcp.md' %}

### Create a Storage Pool

Before logical volumes can be created and connected, a storage pool is required. If a pool already exists, it can be
reused. Otherwise, creating a storage pool can be created on any control plane node as follows:

```bash title="Create a Storage Pool"
{{ cliname }} pool add <POOL_NAME> <CLUSTER_UUID>
```

The last line of a successful storage pool creation returns the new pool id.

```plain title="Example output of creating a storage pool"
[demo@demo ~]# {{ cliname }} pool add test 4502977c-ae2d-4046-a8c5-ccc7fa78eb9a
2025-03-05 06:36:06,093: INFO: Adding pool
2025-03-05 06:36:06,098: INFO: {"cluster_id": "4502977c-ae2d-4046-a8c5-ccc7fa78eb9a", "event": "OBJ_CREATED", "object_name": "Pool", "message": "Pool created test", "caused_by": "cli"}
2025-03-05 06:36:06,100: INFO: Done
ad35b7bb-7703-4d38-884f-d8e56ffdafc6 # <- Pool Id
```

### Create and Connect a Logical Volume

To create a new logical volume, the following command can be run on any control plane node.

```bash
{{ cliname }} volume add \
  --max-rw-iops <IOPS> \
  --max-r-mbytes <THROUGHPUT> \
  --max-w-mbytes <THROUGHPUT> \
  --ndcs <DATA CHUNKS IN STRIPE> \
  --npcs <PARITY CHUNKS IN STRIPE>
  --fabric {tcp, rdma}
  --lvol-priority-class <1-6>
  <VOLUME_NAME> \
  <VOLUME_SIZE> \
  <POOL_NAME>
```

!!! info
    The parameters `ndcs` and `npcs` define the erasure-coding schema (e.g., `--ndcs=4 --npcs=2`). The settings are
    optional. If not specified, the cluster default is chosen. Valid for `ndcs` are 1, 2, and 4, and for `npcs` 0,1,
    and 2. However, it must be considered that the number of cluster nodes must be equal to or larger than (`ndcs` +
    `npcs`).

    The parameter `--fabric` defines the fabric by which the volume is connected to the cluster. It is optional and the
    default is `tcp`. The fabric type `rdma` can only be chosen for hosts with an RDMA-capable NIC and for clusters that
    support RDMA. A priority class is optional as well and can be selected only if the cluster defines it. A cluster can
    define 0-6 priority classes. The default is 0.

```plain title="Example of creating a logical volume"
{{ cliname }} volume add --ndcs 2 --ndcs 1 --fabric tcp lvol01 1000G test  
```

In this example, a logical volume with the name `lvol01` and 1TB of thinly provisioned capacity is created in the pool
named `test`. The uuid of the logical volume is returned at the end of the operation.

For additional parameters, see [Add a new Logical Volume](../../reference/cli/volume.md#adds-a-new-logical-volume).

To connect a logical volume on the initiator (or Linux client), execute the following command on a any control plane
node. This command returns one or more connection commands to be executed on the client.

```bash
{{ cliname }} volume connect \
  <VOLUME_ID>
```

```plain title="Example of retrieving the connection strings of a logical volume"
{{ cliname }} volume connect a898b44d-d7ee-41bb-bc0a-989ad4711780

sudo nvme connect --reconnect-delay=2 --ctrl-loss-tmo=3600 --nr-io-queues=32 --keep-alive-tmo=5 --transport=tcp --traddr=10.10.20.2 --trsvcid=9101 --nqn=nqn.2023-02.io.simplyblock:fa66b0a0-477f-46be-8db5-b1e3a32d771a:lvol:a898b44d-d7ee-41bb-bc0a-989ad4711780
sudo nvme connect --reconnect-delay=2 --ctrl-loss-tmo=3600 --nr-io-queues=32 --keep-alive-tmo=5 --transport=tcp --traddr=10.10.20.3 --trsvcid=9101 --nqn=nqn.2023-02.io.simplyblock:fa66b0a0-477f-46be-8db5-b1e3a32d771a:lvol:a898b44d-d7ee-41bb-bc0a-989ad4711780
```

The output can be copy-pasted to the host to which the volumes should be attached.
