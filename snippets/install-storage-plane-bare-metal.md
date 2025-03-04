## Storage Plane Installation

The installation of a storage plane requires a functioning control plane. If no control plane cluster is available yet,
it must be installed beforehand. Jump right to the [Control Plane Installation](#control-plane-installation).

The following examples assume two subnets to be available. These subnets are defined as shown in
[Network Preparation](#network-preparation).

### Firewall Configuration (SP)

Simplyblock requires a number of TCP and UDP ports to be opened from certain networks. Additionally, it requires IPv6
to be disabled on management nodes.

Following is a list of all ports (TCP and UDP) required for operation as a storage node. Attention is required, as this
list is for storage nodes only. Management nodes have a different port configuration. See the
[Firewall Configuration](#firewall-configuration-cp) section for the control plane.

--8<-- "storage-plane-network-port-table.md"

With the previously defined subnets, the following snippet disables IPv6 and configures the iptables automatically.

!!! danger
    The example assumes that you have an external firewall between the _admin_ network and the public internet!<br/>
    If this is not the case, ensure the correct source access for port _22_.

```plain title="Network Configuration"
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
sudo sysctl -w net.ipv6.conf.default.disable_ipv6=1

# Clean up
sudo iptables -F SIMPLYBLOCK
sudo iptables -D DOCKER-FORWARD -j SIMPLYBLOCK
sudo iptables -X SIMPLYBLOCK
# Setup
sudo iptables -N SIMPLYBLOCK
sudo iptables -I DOCKER-FORWARD 1 -j SIMPLYBLOCK
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A SIMPLYBLOCK -p tcp --dport 2375 -s 192.168.10.0/24,10.10.10.0/24 -j RETURN
sudo iptables -A SIMPLYBLOCK -p tcp --dport 2377 -s 192.168.10.0/24,10.10.10.0/24 -j RETURN
sudo iptables -A SIMPLYBLOCK -p tcp --dport 4420 -s 10.10.10.0/24 -j RETURN
sudo iptables -A SIMPLYBLOCK -p udp --dport 4789 -s 192.168.10.0/24,10.10.10.0/24 -j RETURN
sudo iptables -A SIMPLYBLOCK -p tcp --dport 5000 -s 192.168.10.0/24 -j RETURN
sudo iptables -A SIMPLYBLOCK -p tcp --dport 7946 -s 192.168.10.0/24,10.10.10.0/24 -j RETURN
sudo iptables -A SIMPLYBLOCK -p udp --dport 7946 -s 192.168.10.0/24,10.10.10.0/24 -j RETURN
sudo iptables -A SIMPLYBLOCK -p tcp --dport 8080:8890 -s 192.168.10.0/24,10.10.10.0/24 -j RETURN
sudo iptables -A SIMPLYBLOCK -p tcp --dport 9090-9900 -s 192.168.10.0/24,10.10.10.0/24 -j RETURN
sudo iptables -A SIMPLYBLOCK -s 0.0.0.0/0 -j DROP
```

### Storage Node Installation

Now that the network is configured, the storage node software can be installed.

!!! info
    All storage nodes can be prepared at this point, as they are added to the cluster in the next step. Therefore, it
    is recommended to execute this step on all storage nodes, before moving to the next step.

Simplyblock provides a command line interface called `sbcli`. It's built in Python and required Python 3 and Pip
(the Python package manager) installed on the machine. This can be achieved with `yum`.


```bash title="Install Python and Pip"
sudo yum -y install python3-pip
```

Afterward, the `sbcli` command line interface can be installed. Upgrading the CLI later on, uses the same command.

```bash title="Install Simplyblock CLI"
sudo pip install sbcli --upgrade
```

!!! recommendation
    Simplyblock recommends to only upgrade `sbcli` if a system upgrade is executed to prevent potential
    incompatibilities between the running simplyblock cluster and the version of `sbcli`.

At this point, a quick check with the simplyblock provided system check can reveal potential issues quickly.

```bash title="Automatically check your configuration"
curl -L https://sblk.xyz/prerequisites | bash
```

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

To find the correct LBA format (_lbaf_) for each of the devices, the `nvme` cli can be used.

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

In the example, the required LBA format is 4. If a NVMe device doesn't have that combination, any other lbads=12
combination will work. However, simplyblock recommends to ask for the best available combination.

In our example, the device is already formatted with the correct _lbaf_ (see the "in use"). It is, however,
recommended to always format the device before use.

To format the drive, the `nvme` cli is used again.

```bash title="Formatting the NVMe device"
sudo nvme format --lbaf=<lbaf> --ses=0 /dev/nvmeXnY
```

The output of the command should give a successful response when executing similar to the below example.

```plain title="Example output of NVMe device formatting"
[demo@demo-3 ~]# sudo nvme format --lbaf=4 --ses=0 /dev/nvme0n1
You are about to format nvme0n1, namespace 0x1.
WARNING: Format may irrevocably delete this device's data.
You have 10 seconds to press Ctrl-C to cancel this operation.

Use the force [--force] option to suppress this warning.
Sending format operation ...
Success formatting namespace:1
```

With all NVMe devices prepared, the storage node software can be deployed.

```bash title="Deploy the storage node"
sudo sbcli sn deploy --ifname eth0
```

The output will look something like the following example:

```plain title="Example output of a storage node deployment"
[demo@demo-3 ~]# sudo sbcli sn deploy --ifname eth0
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

### Secondary Node Installation

A secondary node is a storage node without additional storage disks to contribute to the distributed storage pool.
Apart from that, it is the same as a normal storage node.

However, due to the missing storage devices, preparing a secondary node on requires deploying the storage node
software.

```bash title="Deploy the secondary node"
sudo sbcli sn deploy --ifname eth0
```

The output will look something like the following example:

```plain title="Example output of a secondary node deployment"
[demo@demo-4 ~]# sudo sbcli sn deploy --ifname eth0
2025-02-26 13:35:06,991: INFO: NVMe SSD devices found on node:
2025-02-26 13:35:07,038: INFO: Installing dependencies...
2025-02-26 13:35:13,508: INFO: Node IP: 192.168.10.4
2025-02-26 13:35:13,623: INFO: Pulling image public.ecr.aws/simply-block/simplyblock:hmdi
2025-02-26 13:35:15,219: INFO: Recreating SNodeAPI container
2025-02-26 13:35:15,543: INFO: Pulling image public.ecr.aws/simply-block/ultra:main-latest
192.168.10.4:5000
```

On a successful deployment, the last line will provide the secondary node's control channel address. This should be
noted, as it is required in the next step to attach the secondary node to the simplyblock storage cluster.

### Attach the Storage Node to the Control Plane

When all storage nodes are prepared, they can be added to the storage cluster.

!!! warning
    The following command are executed from a management node. Attaching a storage node to a control plane is executed
    from a management node.

```bash title="Attaching a storage node to the storage plane"
sudo sbcli sn add-node <CLUSTER_ID> <SN_CTR_ADDR> <MGT_IF> \
  --max-lvol <MAX_LOGICAL_VOLUMES> \
  --max-prov <MAX_PROVISIONING_CAPACITY> \
  --number-of-devices <NUM_STOR_NVME> \
  --partitions <NUM_OF_PARTITIONS> \
  --data-nics <DATA_IF>
```

!!! info
    The number of partitions (_&lt;NUM_OF_PARTITIONS&gt;_) depends on the storage node setup. If a storage node has a
    separate journaling device (which is strongly recommended), the value should be zero (_0_) to prevent the storage
    devices to be partitioned. This improves the performance and prevents device sharing between the journal and
    actual data storage location.

The output will look something like the following example:

```plain title="Example output of adding a storage node to the storage plane"
[demo@demo ~]# sudo sbcli sn add-node 7bef076c-82b7-46a5-9f30-8c938b30e655 192.168.10.2:5000 eth0 --max-lvol 50 --max-prov 500g --number-of-devices 3 --partitions 0 --data-nics eth1
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

### Attach the Secondary Node to the Control Plane

Afterward, the secondary node needs to be added to the cluster.

```bash title="Attaching a secondary node to the storage plane"
sudo sbcli sn add-node <CLUSTER_ID> <SN_CTR_ADDR> <MGT_IF> \
  --data-nics <DATA_IF>
  --is-secondary-node
```

The output will look something like the following example:

```plain title="Example output of a secondary node to the storage plane"
[demo@demo ~]# sudo sbcli sn add-node 7bef076c-82b7-46a5-9f30-8c938b30e655 192.168.10.5:5000 ens18 --data-nics=ens16 --is-secondary-node
2025-02-28 13:34:57,877: INFO: Adding Storage node: 192.168.10.115:5000
2025-02-28 13:34:57,952: INFO: Node found: vm5
2025-02-28 13:34:57,953: INFO: Instance id: 5d679365-1361-40b0-bac0-3de949057bbc
2025-02-28 13:34:57,953: INFO: Instance cloud: None
2025-02-28 13:34:57,954: INFO: Instance type: None
2025-02-28 13:34:57,954: INFO: Instance privateIp: 192.168.10.5
2025-02-28 13:34:57,955: INFO: Instance public_ip: 192.168.10.5
2025-02-28 13:34:57,977: WARNING: Unsupported instance-type None for deployment
2025-02-28 13:34:57,977: INFO: Node Memory info
...
025-02-28 13:35:08,068: INFO: Connecting to remote devices
2025-02-28 13:35:08,111: INFO: Connecting to node 2f4dafb1-d610-42a7-9a53-13732459523e
2025-02-28 13:35:08,111: INFO: bdev found remote_alceml_378cf3b5-1959-4415-87bf-392fa1bbed6c_qosn1
2025-02-28 13:35:08,112: INFO: bdev found remote_alceml_c4c4011a-8f82-4c9d-8349-b4023a20b87c_qosn1
2025-02-28 13:35:08,112: INFO: bdev found remote_alceml_d27388b9-bbd8-4e82-8880-d8811aa45383_qosn1
2025-02-28 13:35:08,113: INFO: Connecting to node b7db725a-96e2-40d1-b41b-738495d97093
2025-02-28 13:35:08,113: INFO: bdev found remote_alceml_7f5ade89-53c6-440b-9614-ec24db3afbd9_qosn1
2025-02-28 13:35:08,114: INFO: bdev found remote_alceml_8d160125-f095-43ae-9781-16d841ae9719_qosn1
2025-02-28 13:35:08,114: INFO: bdev found remote_alceml_b0691372-1a4b-4fa9-a805-c2c1f311541c_qosn1
2025-02-28 13:35:08,114: INFO: Connecting to node 43560b0a-f966-405f-b27a-2c571a2bb4eb
2025-02-28 13:35:08,115: INFO: bdev found remote_alceml_29e74188-5efa-47d9-9282-84b4e46b77db_qosn1
2025-02-28 13:35:08,115: INFO: bdev found remote_alceml_a1efcbbf-328c-4f86-859f-fcfceae1c7a8_qosn1
2025-02-28 13:35:08,116: INFO: bdev found remote_alceml_cf2d3d24-e244-4a45-a71d-6383db07806f_qosn1
2025-02-28 13:35:08,274: WARNING: The cluster status is not active (unready), adding the node without distribs and lvstore
2025-02-28 13:35:08,274: INFO: Done
```

On a successful response, it's finally time to activate the storage plane.

### Activate the Storage Cluster

The last step after all nodes are added to the storage cluster, the storage plane can be activated.

```bash title="Storage cluster activation"
sudo sbcli cluster activate <CLUSTER_ID>
```

The command output should look like this and respond with a successful activation of the storage cluster

```plain title="Example output of a storage cluster activation"
[demo@demo ~]# sbcli cluster activate 7bef076c-82b7-46a5-9f30-8c938b30e655
2025-02-28 13:35:26,053: INFO: {"cluster_id": "7bef076c-82b7-46a5-9f30-8c938b30e655", "event": "STATUS_CHANGE", "object_name": "Cluster", "message": "Cluster status changed from unready to in_activation", "caused_by": "cli"}
2025-02-28 13:35:26,322: INFO: Connecting remote_jm_43560b0a-f966-405f-b27a-2c571a2bb4eb to 2f4dafb1-d610-42a7-9a53-13732459523e
2025-02-28 13:35:31,133: INFO: Connecting remote_jm_43560b0a-f966-405f-b27a-2c571a2bb4eb to b7db725a-96e2-40d1-b41b-738495d97093
2025-02-28 13:35:55,791: INFO: {"cluster_id": "7bef076c-82b7-46a5-9f30-8c938b30e655", "event": "STATUS_CHANGE", "object_name": "Cluster", "message": "Cluster status changed from in_activation to active", "caused_by": "cli"}
2025-02-28 13:35:55,794: INFO: Cluster activated successfully
```

Now that the cluster is ready, it is time to install the [Kubernetes CSI Driver](install-simplyblock-csi.md) or learn
how to use the simplyblock storage cluster to
[manually provision logical volumes](../../usage/baremetal/provisioning.md).
