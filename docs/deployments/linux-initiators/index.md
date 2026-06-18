---
title: "Plain Linux Initiators"
description: "Plain Linux Initiators: Simplyblock storage can be attached over the network to Linux hosts which are not running Kubernetes, Proxmox or OpenStack."
weight: 20200
---

Simplyblock storage can be attached over the network to Linux hosts that are not running Kubernetes, Proxmox, or
OpenStack.

While no simplyblock components need to be installed on these hosts, some OS-level configuration steps are required.
Those manual steps are typically taken care of by the CSI driver or Proxmox integration.

On plain Linux initiators, those steps must be performed manually on each host that will connect simplyblock logical
volumes.

### Prerequisites

Before starting the deployment, make sure that the prerequisites described in the
[hardware prerequisites](../deployment-preparation/hardware-requirements.md) and
[software prerequisites](../deployment-preparation/software-requirements.md) sections are met.

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
reused. Otherwise, a storage pool can be created on any control plane node as follows:

```bash title="Create a Storage Pool"
{{ cliname }} storage-pool add <POOL_NAME> <CLUSTER_UUID>
```

To enable NVMe-oF security for all volumes in the pool, provide the `--dhchap` flag.

```bash title="Create a Storage Pool with NVMe-oF Security"
{{ cliname }} storage-pool add <POOL_NAME> <CLUSTER_UUID> --dhchap
```

For more information, see [NVMe-oF Security](../../architecture/concepts/nvmf-security.md).

The last line of a successful storage pool creation returns the new pool ID.

```plain title="Example output of creating a storage pool"
[demo@demo ~]# {{ cliname }} storage-pool add test 4502977c-ae2d-4046-a8c5-ccc7fa78eb9a
2025-03-05 06:36:06,093: INFO: Adding pool
2025-03-05 06:36:06,098: INFO: {"cluster_id": "4502977c-ae2d-4046-a8c5-ccc7fa78eb9a", "event": "OBJ_CREATED", "object_name": "Pool", "message": "Pool created test", "caused_by": "cli"}
2025-03-05 06:36:06,100: INFO: Done
ad35b7bb-7703-4d38-884f-d8e56ffdafc6 # <- Pool Id
```

### Create and Connect a Logical Volume

To create a new logical volume, the following command can be run on any control plane node.

```bash title="Create a Logical Volume"
{{ cliname }} volume add \
  --max-rw-iops <IOPS> \
  --max-r-mbytes <THROUGHPUT> \
  --max-w-mbytes <THROUGHPUT> \
  --fabric {tcp, rdma} \
  --lvol-priority-class <1-6> \
  <VOLUME_NAME> \
  <VOLUME_SIZE> \
  <POOL_NAME>
```

!!! info
    The erasure-coding schema (the number of data and parity chunks per stripe) is not configured per volume. It is a
    cluster-level setting defined once during a cluster created. Configuration happens via the `--data-chunks-per-stripe` and
    `--parity-chunks-per-stripe` options of the cluster deployment.

    All volumes inherit the cluster's erasure-coding schema. For details on the available schemas and how to choose one, see
    [Erasure Coding Scheme](../deployment-preparation/erasure-coding-scheme.md) and
    [Cluster Deployment Options](../cluster-deployment-options.md).

    The parameter `--fabric` defines the fabric by which the volume is connected to the cluster. It is optional and the
    default is `tcp`. The fabric type `rdma` can only be chosen for hosts with an RDMA-capable NIC and for clusters that
    support RDMA. A priority class is optional as well and can be selected only if the cluster defines it. A cluster can
    define 0-6 priority classes. The default is 0.

```plain title="Example of creating a logical volume"
{{ cliname }} volume add \
  --fabric tcp lvol01 1000G test  
```

In this example, a logical volume named `lvol01` with 1 TB of thinly provisioned capacity is created in the pool
named `test`. The UUID of the logical volume is returned at the end of the operation.

For additional parameters, see [the CLI reference](../../reference/cli/index.md).

To connect a logical volume on the initiator (or Linux client), execute the following command on any control plane
node. This command returns one or more connection commands to be executed on the client.

```bash title="Get Volume Connection Commands"
{{ cliname }} volume connect \
  <VOLUME_ID>
```

If the volume has host access control enabled (allowed hosts configured), the `--host-nqn` flag is required:

```bash title="Get Volume Connection Command with Host NQN"
{{ cliname }} volume connect \
  <VOLUME_ID> --host-nqn <HOST_NQN>
```

The output will include the required authentication flags (`--hostnqn`, `--dhchap-secret`, `--dhchap-ctrl-secret`,
`--tls`) based on the host's security credentials. For more information, see
[NVMe-oF Security](../../architecture/concepts/nvmf-security.md).

```plain title="Example of retrieving the connection strings of a logical volume"
{{ cliname }} volume connect a898b44d-d7ee-41bb-bc0a-989ad4711780

sudo nvme connect --reconnect-delay=2 --ctrl-loss-tmo=3600 \
  --nr-io-queues=32 --keep-alive-tmo=5 --transport=tcp \
  --traddr=10.10.20.2 --trsvcid=9101 \
  --nqn=nqn.2023-02.io.simplyblock:fa66b0a0-477f-46be-8db5-b1e3a32d771a:lvol:a898b44d-d7ee-41bb-bc0a-989ad4711780
sudo nvme connect --reconnect-delay=2 --ctrl-loss-tmo=3600 \
  --nr-io-queues=32 --keep-alive-tmo=5 --transport=tcp \
  --traddr=10.10.20.3 --trsvcid=9101 \
  --nqn=nqn.2023-02.io.simplyblock:fa66b0a0-477f-46be-8db5-b1e3a32d771a:lvol:a898b44d-d7ee-41bb-bc0a-989ad4711780
```

The output can be copied and pasted to the host to which the volumes should be attached.
