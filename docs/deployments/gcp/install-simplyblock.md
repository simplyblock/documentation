---
title: "Install Simplyblock Storage Cluster"
weight: 30100
---

<!-- include: install intro -->
{% include 'bare-metal-intro.md' %}

!!! warning
    Simplyblock strongly recommends setting up individual networks for the storage plane and control plane traffic.  

## Google Kubernetes Engine (GKE)

!!! info
    If simplyblock is to be installed into Google Kubernetes Engine (GKE), the [Kubernetes documentation](../kubernetes/index.md) section
    has the necessary step-by-step guide.

<!-- include: install control plane documentation -->
{% include 'install-control-plane.md' %}

## Storage Plane Installation

The installation of a storage plane requires a functioning control plane. If no control plane cluster is available yet,
it must be installed beforehand. Jump right to the [Control Plane Installation](#control-plane-installation).

The following examples assume two subnets are available. These subnets are defined as shown in
[Network Preparation](#network-preparation).

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

{% include 'prepare-nvme-tcp.md' %}

#### Configuration and Deployment

With all NVMe devices prepared and the NVMe/TCP driver loaded, the storage node software can be deployed.

The actual deployment process happens in three steps:
- Creating the storage node configuration
- Deploy the first stage (the storage node API)
- Deploy the second stage (add the storage node to the cluster), happening from a management node

The configuration process creates the configuration file, which contains all the assignments of NVMe devices, NICs, and
potentially available [NUMA nodes](/deployments/deployment-planning/numa-considerations.md). By default, simplyblock
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

A full set of the parameters for the configure subcommand can be found in the
[CLI reference](/reference/cli/storage-node.md#prepare-a-configuration-file-to-be-used-when-adding-the-storage-node). 

After the configuration has been created, the first stage deployment can be executed 

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
2025-02-28 13:35:55,794: INFO: Cluster activated successfully
```

Now that the cluster is ready, it is time to install the [Kubernetes CSI Driver](install-simplyblock-csi.md) or learn
how to use the simplyblock storage cluster to
[manually provision logical volumes](../../usage/baremetal/provisioning.md).
