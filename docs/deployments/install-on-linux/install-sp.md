---
title: "Install Storage Plane"
weight: 34000
---

## Storage Plane Installation

The installation of a storage plane requires a functioning control plane. If no control plane cluster is available yet,
it must be installed beforehand. Jump right to the [Control Plane Installation](install-cp.md).

The following examples assume two subnets are available. 

### Firewall Configuration (SP)

{% include 'iptables-setup-docker-swarm.md' %}

### Storage Node Installation

Now that the network is configured, the storage node software can be installed.

!!! info
    All storage nodes can be prepared at this point, as they are added to the cluster in the next step. Therefore, it
    is recommended to execute this step on all storage nodes before moving to the next step.

Simplyblock provides a command line interface called `{{ cliname }}`. It's built in Python and requires
Python 3 and Pip (the Python package manager) are installed on the machine. This can be achieved with `yum`.


```bash title="Install Python and Pip"
sudo yum -y install python3-pip
```

Afterward, the `{{ cliname }}` command line interface can be installed. Upgrading the CLI later on uses the
same command.

```bash title="Install Simplyblock CLI"
sudo pip install {{ cliname }} --upgrade
```

!!! recommendation
    Simplyblock recommends to only upgrade `{{ cliname }}` if a system upgrade is executed to prevent potential
    incompatibilities between the running simplyblock cluster and the version of `{{ cliname }}`.

At this point, a quick check with the simplyblock provided system check can reveal potential issues quickly.

```bash title="Automatically check your configuration"
curl -s -L https://install.simplyblock.io/scripts/prerequisites-sn.sh | bash
```

#### NVMe Device Preparation

{% include 'nvme-format.md' %}

#### Configuration and Deployment

The low-level format of the devices is required only once.

With all NVMe devices prepared, the storage node software can be deployed.

The actual deployment process happens in three steps:

- Creating the storage node configuration
- Deploy the first stage (the storage node API)
- Deploy the second stage (the actual storage node services). Remember that this step is performed from a control plane node.

The configuration process creates the configuration file, which contains all the assignments of NVMe devices, NICs, and
potentially available [NUMA nodes](../deployment-preparation/numa-considerations.md). By default, simplyblock
will configure one storage node per NUMA node.

```bash title="Configure the storage node"
sudo {{ cliname }} storage-node configure \
  --max-lvol <MAX_LOGICAL_VOLUMES> \
  --max-size <MAX_PROVISIONING_CAPACITY>
```

```plain title="Example output of storage node configure"
[demo@demo-3 ~]# sudo {{ cliname }} sn configure --nodes-per-socket=2 --max-lvol=50 --max-size=1T
2025-05-14 10:40:17,460: INFO: 0000:00:04.0 is already bound to nvme.
0000:00:1e.0
0000:00:1e.0
0000:00:1f.0
0000:00:1f.0
0000:00:1e.0
0000:00:1f.0
2025-05-14 10:40:17,841: INFO: JSON file successfully written to /etc/simplyblock/sn_config_file
2025-05-14 10:40:17,905: INFO: JSON file successfully written to /etc/simplyblock/system_info
True
```

A full set of the parameters for the `configure` subcommand can be found in the
[CLI reference](/reference/cli/storage-node.md#prepare-a-configuration-file-to-be-used-when-adding-the-storage-node). 

It is also possible to adjust the configuration file manually, e.g., to remove NVMe devices.
After the configuration has been created, the first stage deployment can be executed. 

```bash title="Deploy the storage node"
sudo {{ cliname }} storage-node deploy --ifname eth0
```

The output will look something like the following example:

```plain title="Example output of a storage node deployment"
[demo@demo-3 ~]# sudo {{ cliname }} storage-node deploy --ifname eth0
2025-02-26 13:35:06,991: INFO: NVMe SSD devices found on node:
2025-02-26 13:35:07,038: INFO: Installing dependencies...
2025-02-26 13:35:13,508: INFO: Node IP: 192.168.10.2
2025-02-26 13:35:13,623: INFO: Pulling image public.ecr.aws/simply-block/simplyblock:hmdi
2025-02-26 13:35:15,219: INFO: Recreating SNodeAPI container
2025-02-26 13:35:15,543: INFO: Pulling image public.ecr.aws/simply-block/ultra:main-latest
192.168.10.2:5000
```

On a successful deployment, the last line will provide the storage node's control channel address. This should be noted
for all storage nodes, as it is required in the next step to attach the storage node to the simplyblock storage cluster.

When all storage nodes are added, it's finally time to activate the storage plane.

### Attach the Storage Node to the Control Plane

When all storage nodes are prepared, they can be added to the storage cluster.

!!! Warning
    The following commands are executed from a management node. Attaching a storage node to a control plane is executed
    from a management node.

```bash title="Attaching a storage node to the storage plane"
sudo {{ cliname }} storage-node add-node <CLUSTER_ID> <SN_CTR_ADDR> <MGT_IF> \
  --partitions <NUM_OF_PARTITIONS> \
  --data-nics <DATA_IF>
```

If a separate NIC (e.g., BOND device) is used for storage traffic (no matter if in the cluster and between hosts and
cluster nodes), the `--data-nics` parameter must be specified. In R25.10, zero or one data NICs are supported. Zero data
NICs will utilize the management interface for all traffic.

!!! Info
    The number of partitions (_NUM_OF_PARTITIONS_) depends on the storage node setup. If a storage node has a
    separate journaling device (e.g., a SLC NVMe device), the value should be zero (_0_) to prevent the storage
    devices from being partitioned. This improves the performance and prevents device sharing between the journal and
    the actual data storage location. However, in most cases, a separate journaling device is not available or required
    and the value of `--partitions` has to be 1.

The output will look something like the following example:

```plain title="Example output of adding a storage node to the storage plane"
[demo@demo ~]# sudo {{ cliname }} storage-node add-node 7bef076c-82b7-46a5-9f30-8c938b30e655 192.168.10.2:5000 eth0 --number-of-devices 3 --data-nics eth1
2025-02-26 14:55:17,236: INFO: Adding Storage node: 192.168.10.2:5000
2025-02-26 14:55:17,340: INFO: Instance id: 0b0c825e-3d16-4d91-a237-51e55c6ffefe
2025-02-26 14:55:17,341: INFO: Instance cloud: None
2025-02-26 14:55:17,341: INFO: Instance type: None
2025-02-26 14:55:17,342: INFO: Instance privateIp: 192.168.10.2
2025-02-26 14:55:17,342: INFO: Instance public_ip: 192.168.10.2
2025-02-26 14:55:17,347: INFO: Node Memory info
2025-02-26 14:55:17,347: INFO: Total: 24.3 GB
2025-02-26 14:55:17,348: INFO: Free: 23.2 GB
2025-02-26 14:55:17,348: INFO: Minimum required huge pages memory is : 14.8 GB
2025-02-26 14:55:17,349: INFO: Joining docker swarm...
2025-02-26 14:55:21,060: INFO: Deploying SPDK
2025-02-26 14:55:31,969: INFO: adding alceml_2d1c235a-1f4d-44c7-9ac1-1db40e23a2c4
2025-02-26 14:55:32,010: INFO: creating subsystem nqn.2023-02.io.simplyblock:vm12:dev:2d1c235a-1f4d-44c7-9ac1-1db40e23a2c4
2025-02-26 14:55:32,022: INFO: adding listener for nqn.2023-02.io.simplyblock:vm12:dev:2d1c235a-1f4d-44c7-9ac1-1db40e23a2c4 on IP 10.10.10.2
2025-02-26 14:55:32,303: INFO: Connecting to remote devices
2025-02-26 14:55:32,321: INFO: Connecting to remote JMs
2025-02-26 14:55:32,342: INFO: Make other nodes connect to the new devices
2025-02-26 14:55:32,346: INFO: Setting node status to Active
2025-02-26 14:55:32,357: INFO: {"cluster_id": "3196b77c-e6ee-46c3-8291-736debfe2472", "event": "STATUS_CHANGE", "object_name": "StorageNode", "message": "Storage node status changed from: in_creation to: online", "caused_by": "monitor"}
2025-02-26 14:55:32,361: INFO: Sending event updates, node: 37b404b9-36aa-40b3-8b74-7f3af86bd5a5, status: online
2025-02-26 14:55:32,368: INFO: Sending to: 37b404b9-36aa-40b3-8b74-7f3af86bd5a5
2025-02-26 14:55:32,389: INFO: Connecting to remote devices
2025-02-26 14:55:32,442: WARNING: The cluster status is not active (unready), adding the node without distribs and lvstore
2025-02-26 14:55:32,443: INFO: Done
```

Repeat this process for all prepared storage nodes to add them to the storage plane.

### Activate the Storage Cluster

The last step, after all nodes are added to the storage cluster, is to activate the storage plane.

```bash title="Storage cluster activation"
sudo {{ cliname }} cluster activate <CLUSTER_ID>
```

The command output should look like this, and respond with a successful activation of the storage cluster

```plain title="Example output of a storage cluster activation"
[demo@demo ~]# {{ cliname }} cluster activate 7bef076c-82b7-46a5-9f30-8c938b30e655
2025-02-28 13:35:26,053: INFO: {"cluster_id": "7bef076c-82b7-46a5-9f30-8c938b30e655", "event": "STATUS_CHANGE", "object_name": "Cluster", "message": "Cluster status changed from unready to in_activation", "caused_by": "cli"}
2025-02-28 13:35:26,322: INFO: Connecting remote_jm_43560b0a-f966-405f-b27a-2c571a2bb4eb to 2f4dafb1-d610-42a7-9a53-13732459523e
2025-02-28 13:35:31,133: INFO: Connecting remote_jm_43560b0a-f966-405f-b27a-2c571a2bb4eb to b7db725a-96e2-40d1-b41b-738495d97093
2025-02-28 13:35:55,791: INFO: {"cluster_id": "7bef076c-82b7-46a5-9f30-8c938b30e655", "event": "STATUS_CHANGE", "object_name": "Cluster", "message": "Cluster status changed from in_activation to active", "caused_by": "cli"}
```
