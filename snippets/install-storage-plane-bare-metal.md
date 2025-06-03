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

#### NVMe Device Preparation

Once the check is complete, the NVMe devices in each storage node can be prepared. To prevent data loss in case of a
sudden power outage, NVMe devices need to be formatted for a specific LBA format.

!!! danger
    Failing to format NVMe devices with the correct LBA format can lead to data loss or data corruption in the case
    of a sudden power outage or other loss of power.

The `lsblk` is the best way to find all NVMe devices attached to a system.

```plain title="Example output of lsblk"
[demo@demo-3 ~]# sudo lsblk
NAME        MAJ:MIN RM  SIZE RO TYPE MOUNTPOINTS
sda           8:0    0   30G  0 disk
├─sda1        8:1    0    1G  0 part /boot
└─sda2        8:2    0   29G  0 part
  ├─rl-root 253:0    0   26G  0 lvm  /
  └─rl-swap 253:1    0    3G  0 lvm  [SWAP]
nvme3n1     259:0    0  6.5G  0 disk
nvme2n1     259:1    0   70G  0 disk
nvme1n1     259:2    0   70G  0 disk
nvme0n1     259:3    0   70G  0 disk
```

In the example, we see four NVMe devices. Three devices of 70GiB and one device with 6.5GiB storage capacity.

To find the correct LBA format (_lbaf_) for each of the devices, the `nvme` CLI can be used.

```bash title="Show NVMe namespace information"
sudo nvme id-ns /dev/nvmeXnY
```

The output depends on the NVMe device itself, but looks something like this:

```plain title="Example output of NVMe namespace information"
[demo@demo-3 ~]# sudo nvme id-ns /dev/nvme0n1
NVME Identify Namespace 1:
...
lbaf  0 : ms:0   lbads:9  rp:0
lbaf  1 : ms:8   lbads:9  rp:0
lbaf  2 : ms:16  lbads:9  rp:0
lbaf  3 : ms:64  lbads:9  rp:0
lbaf  4 : ms:0   lbads:12 rp:0 (in use)
lbaf  5 : ms:8   lbads:12 rp:0
lbaf  6 : ms:16  lbads:12 rp:0
lbaf  7 : ms:64  lbads:12 rp:0
```

From this output, the required _lbaf_ configuration can be found. The necessary configuration has to have the following
values:

| Property | Value |
|----------|-------|
| ms       | 0     |
| lbads    | 12    |
| rp       | 0     |

In the example, the required LBA format is 4. If an NVMe device doesn't have that combination, any other _lbads=12_
combination will work. However, simplyblock recommends asking for the best available combination.

In our example, the device is already formatted with the correct _lbaf_ (see the "in use"). It is, however,
recommended to always format the device before use.

To format the drive, the `nvme` cli is used again.

```bash title="Formatting the NVMe device"
sudo nvme format --lbaf=<lbaf> --ses=0 /dev/nvmeXnY
```

The output of the command should give a successful response when executed similarly to the example below.

```plain title="Example output of NVMe device formatting"
[demo@demo-3 ~]# sudo nvme format --lbaf=4 --ses=0 /dev/nvme0n1
You are about to format nvme0n1, namespace 0x1.
WARNING: Format may irrevocably delete this device's data.
You have 10 seconds to press Ctrl-C to cancel this operation.

Use the force [--force] option to suppress this warning.
Sending format operation ...
Success formatting namespace:1
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
