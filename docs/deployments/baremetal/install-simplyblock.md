---
title: "Install Simplyblock Storage Cluster"
weight: 30100
---

Installing simplyblock for production, requires a few components to be installed, as well as a couple of configurations
to secure the network, ensure the performance and data protection in the case of hardware or software failures.

Simplyblock provides a test script to automatically check your system's configuration. While it may not catch all
edge cases, it can help to streamline the configuration check. This script can be run multiple times during the
preparation phase to find missing configuration during the process.

```bash title="Automatically check your configuration"
curl -L https://sblk.xyz/prerequisites | bash
```

## Network Preparation

Simplyblock recommends two individual network interfaces, one for the control plane and one for the storage plane.
Hence, in the following installation description, we assume two separated subnets. To install simplyblock in your
environment, you may have to adopt these commands to match your configuration.

| Network interface | Network definition | Abbreviation | Subnet          |
|-------------------|--------------------|--------------|-----------------|
| eth0              | Control Plane      | control      | 192.168.10.0/24 |
| eth1              | Storage Plane      | storage      | 10.10.10.0/24   |

!!! danger
    Simplyblock requires a fully redundant network interconnect, implemented via a solution such as LACP or Static
    LAG. Failing to provide that may cause data corruption or data loss in case of network issues. For more information
    see the [Network Considerations](../../deployments/deployment-planning/network-considerations.md)
    section.

## Control Plane Installation

The first step when installing simplyblock, is to install the control plane. The control plane manages one or more
storage clusters. If an existing control plane is available and the new cluster should be added to it, this section
can be skipped. Jump right to the [Storage Plane Installation](#storage-plane-installation).

### Firewall Configuration (CP)

Simplyblock requires a number of TCP and UDP ports to be opened from certain networks. Additionally, it requires IPv6
to be disabled on management nodes.

Following is a list of all ports (TCP and UDP) required for operation as a management node. Attention is required, as
this list is for management nodes only. Storage nodes have a different port configuration. See the
[Firewall Configuration](#firewall-configuration-sp) section for the storage plane.

| Service                     | Direction | Source / Target Network | Port  | Protocol(s) |
|-----------------------------|-----------|-------------------------|-------|-------------|
| Cluster API                 | ingress   | storage, control, admin | 80    | TCP         |
| SSH                         | ingress   | storage, control, admin | 22    | TCP         |
| Graylog                     | ingress   | storage, control        | 12201 | TCP / UDP   |
| Graylog                     | ingress   | storage, control        | 12202 | TCP         |
| Graylog                     | ingress   | storage, control        | 13201 | TCP         |
| Graylog                     | ingress   | storage, control        | 13202 | TCP         |
| Docker Daemon Remote Access | ingress   | storage, control        | 2375  | TCP         |
| Docker Swarm Remote Access  | ingress   | storage, control        | 2377  | TCP         |
| Docker Overlay Network      | ingress   | storage, control        | 4789  | UDP         |
| Docker Network Discovery    | ingress   | storage, control        | 7946  | TCP / UDP   |
| FoundationDB                | ingress   | storage, control        | 4500  | TCP         |
| Prometheus                  | ingress   | storage, control        | 9100  | TCP         |
|                             |           |                         |       |             |
| Cluster Control             | egress    | storage, control        | 8080  | TCP         |
| spdk-http-proxy             | egress    | storage, control        | 5000  | TCP         |
| Docker Daemon Remote Access | egress    | storage, control        | 2375  | TCP         |
| Docker Swarm Remote Access  | egress    | storage, control        | 2377  | TCP         |
| Docker Overlay Network      | egress    | storage, control        | 4789  | UDP         |
| Docker Network Discovery    | egress    | storage, control        | 7946  | TCP / UDP   |

With the previously defined subnets, the following snippet disables IPv6 and configures the iptables automatically.

```plain title="Network Configuration"
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
sudo sysctl -w net.ipv6.conf.default.disable_ipv6=1

sudo iptables -F
sudo iptables -X
sudo iptables -N CONTROL_AND_STORAGE
sudo iptables -A CONTROL_AND_STORAGE -s 192.168.10.0/24 -j ACCEPT
sudo iptables -A CONTROL_AND_STORAGE -s 10.10.10.0/24 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 2375 -j CONTROL_AND_STORAGE
sudo iptables -A INPUT -p tcp --dport 2377 -j CONTROL_AND_STORAGE
sudo iptables -A INPUT -p tcp --dport 4500 -j CONTROL_AND_STORAGE
sudo iptables -A INPUT -p udp --dport 4789 -j CONTROL_AND_STORAGE
sudo iptables -A INPUT -p tcp --dport 7946 -j CONTROL_AND_STORAGE
sudo iptables -A INPUT -p udp --dport 7946 -j CONTROL_AND_STORAGE
sudo iptables -A INPUT -p tcp --dport 9100 -j CONTROL_AND_STORAGE
sudo iptables -A INPUT -p tcp --dport 12201 -j CONTROL_AND_STORAGE
sudo iptables -A INPUT -p udp --dport 12201 -j CONTROL_AND_STORAGE
sudo iptables -A INPUT -p tcp --dport 12202 -j CONTROL_AND_STORAGE
sudo iptables -A INPUT -p tcp --dport 13201 -j CONTROL_AND_STORAGE
sudo iptables -A INPUT -p tcp --dport 13202 -j CONTROL_AND_STORAGE
sudo iptables -P INPUT DROP
```

### Management Node Installation

Now that the network is configured, the management node software can be installed.

Simplyblock provides a command line interface called `sbcli`. It's built in Python and required Python 3 and Pip (the
Python package manager) installed on the machine. This can be achieved with `yum`.

```bash title="Install Python and Pip"
sudo yum -y install python3-pip
```

Afterward, the `sbcli` command line interface can be installed. Upgrading the CLI later on, uses the same command.

```bash title="Install Simplyblock CLI"
sudo pip install sbcli --upgrade
```

!!! tip "Recommendation"
    Simplyblock recommends to only upgrade `sbcli` if a system upgrade is executed to prevent potential
    incompatibilities between the running simplyblock cluster and the version of `sbcli`.

At this point, a quick check with the simplyblock provided system check can reveal potential issues quickly.

```bash title="Automatically check your configuration"
curl -L https://sblk.xyz/prerequisites | bash
```

If the check succeeds, it's time to set up the primary management node: 

```bash title="Deploy the primary management node"
sbcli cluster create --ifname=<IF_NAME> -ha-type=ha
```

The output should look something like this:

```plain title="Example output control plane creation"
[root@vm11 ~]# sbcli cluster create --ifname=eth0 --ha-type=ha
2025-02-26 12:37:06,097: INFO: Installing dependencies...
2025-02-26 12:37:13,338: INFO: Installing dependencies > Done
2025-02-26 12:37:13,358: INFO: Node IP: 192.168.10.1
2025-02-26 12:37:13,510: INFO: Configuring docker swarm...
2025-02-26 12:37:14,199: INFO: Configuring docker swarm > Done
2025-02-26 12:37:14,200: INFO: Adding new cluster object
File moved to /usr/local/lib/python3.9/site-packages/simplyblock_core/scripts/alerting/alert_resources.yaml successfully.
2025-02-26 12:37:14,269: INFO: Deploying swarm stack ...
2025-02-26 12:38:52,601: INFO: Deploying swarm stack > Done
2025-02-26 12:38:52,604: INFO: deploying swarm stack succeeded
2025-02-26 12:38:52,605: INFO: Configuring DB...
2025-02-26 12:39:06,003: INFO: Configuring DB > Done
2025-02-26 12:39:06,106: INFO: Settings updated for existing indices.
2025-02-26 12:39:06,147: INFO: Template created for future indices.
2025-02-26 12:39:06,505: INFO: {"cluster_id": "7bef076c-82b7-46a5-9f30-8c938b30e655", "event": "OBJ_CREATED", "object_name": "Cluster", "message": "Cluster created 7bef076c-82b7-46a5-9f30-8c938b30e655", "caused_by": "cli"}
2025-02-26 12:39:06,529: INFO: {"cluster_id": "7bef076c-82b7-46a5-9f30-8c938b30e655", "event": "OBJ_CREATED", "object_name": "MgmtNode", "message": "Management node added vm11", "caused_by": "cli"}
2025-02-26 12:39:06,533: INFO: Done
2025-02-26 12:39:06,535: INFO: New Cluster has been created
2025-02-26 12:39:06,535: INFO: 7bef076c-82b7-46a5-9f30-8c938b30e655
7bef076c-82b7-46a5-9f30-8c938b30e655
```

If the deployment was successful, the last line returns the cluster id. This should be noted down. It's required in
further steps of the installation.

Additionally to the cluster id, the cluster secret is required in many further steps. The following command can be used
to retrieve it.

```bash title=""
sbcli cluster get-secret <CLUSTER_ID>
```

```plain title="Example output get cluster secret"
[root@vm11 ~]# sbcli cluster get-secret 7bef076c-82b7-46a5-9f30-8c938b30e655
e8SQ1ElMm8Y9XIwyn8O0
```

### Secondary Management Nodes

A production cluster, requires at least three management nodes in the control plane. Hence, additional management
nodes need to be added.

On the secondary nodes, the network requires the same configuration as on the primary. Executing the commands under
[Firewall Configuration (CP)](#firewall-configuration-cp) will get the node prepared.

Afterward, Python, Pip, and `sbcli` need to be installed.

```bash title="Deployment preparation"
sudo yum -y install python3-pip
pip install sbcli --upgrade
```

Finally, we deploy the management node software and join the control plane cluster.

```bash title="Secondary management node deployment"
sbcli mgmt add <CP_PRIMARY_IP> <CLUSTER_ID> <CLUSTER_SECRET> <IF_NAME>
```

Running against the primary management node in the control plane should create an output similar to the following
example:

```plain title="Example output joining a control plane cluster"
[root@vm12 ~]# sbcli-dev mgmt add 192.168.10.1 7bef076c-82b7-46a5-9f30-8c938b30e655 e8SQ1ElMm8Y9XIwyn8O0 eth0
2025-02-26 12:40:17,815: INFO: Cluster found, NQN:nqn.2023-02.io.simplyblock:7bef076c-82b7-46a5-9f30-8c938b30e655
2025-02-26 12:40:17,816: INFO: Installing dependencies...
2025-02-26 12:40:25,606: INFO: Installing dependencies > Done
2025-02-26 12:40:25,626: INFO: Node IP: 192.168.10.2
2025-02-26 12:40:26,802: INFO: Joining docker swarm...
2025-02-26 12:40:27,719: INFO: Joining docker swarm > Done
2025-02-26 12:40:32,726: INFO: Adding management node object
2025-02-26 12:40:32,745: INFO: {"cluster_id": "7bef076c-82b7-46a5-9f30-8c938b30e655", "event": "OBJ_CREATED", "object_name": "MgmtNode", "message": "Management node added vm12", "caused_by": "cli"}
2025-02-26 12:40:32,752: INFO: Done
2025-02-26 12:40:32,755: INFO: Node joined the cluster
cdde125a-0bf3-4841-a6ef-a0b2f41b8245
```

From here, additional management nodes can be added to the control plane cluster. If the control plane cluster is ready,
the storage plane can be installed.

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

| Service                     | Direction | Source / Target Network | Port  | Protocol(s) |
|-----------------------------|-----------|-------------------------|-------|-------------|
| bdts                        | ingress   | storage                 | 4420  | TCP         |
| Cluster Control             | ingress   | control                 | 5000  | TCP         |
| spdk-http-proxy             | ingress   | storage, control        | 8080  | TCP         |
| SSH                         | ingress   | storage, control, admin | 22    | TCP         |
| Docker Daemon Remote Access | ingress   | storage, control        | 2375  | TCP         |
| Docker Swarm Remote Access  | ingress   | storage, control        | 2377  | TCP         |
| Docker Overlay Network      | ingress   | storage, control        | 4789  | UDP         |
| Docker Network Discovery    | ingress   | storage, control        | 7946  | TCP / UDP   |
|                             |           |                         |       |             |
| FoundationDB                | egress    | storage                 | 4500  | TCP         |
| Docker Daemon Remote Access | egress    | storage, control        | 2375  | TCP         |
| Docker Swarm Remote Access  | egress    | storage, control        | 2377  | TCP         |
| Docker Overlay Network      | egress    | storage, control        | 4789  | UDP         |
| Docker Network Discovery    | egress    | storage, control        | 7946  | TCP / UDP   |
| Graylog                     | egress    | control                 | 12202 | TCP         |

With the previously defined subnets, the following snippet disables IPv6 and configures the iptables automatically.

```bash title="Network Configuration"
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
sudo sysctl -w net.ipv6.conf.default.disable_ipv6=1

sudo iptables -F
sudo iptables -X
sudo iptables -N CONTROL_AND_STORAGE
sudo iptables -A CONTROL_AND_STORAGE -s 192.168.10.0/24 -j ACCEPT
sudo iptables -A CONTROL_AND_STORAGE -s 10.10.10.0/24 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 2375 -j CONTROL_AND_STORAGE
sudo iptables -A INPUT -p tcp --dport 2377 -j CONTROL_AND_STORAGE
sudo iptables -A INPUT -p tcp --dport 4420 -s 10.10.10.0/24 -j ACCEPT
sudo iptables -A INPUT -p udp --dport 4789 -j CONTROL_AND_STORAGE
sudo iptables -A INPUT -p tcp --dport 5000 -s 192.168.10.0/24 -j ACCEPT
sudo iptables -A INPUT -p udp --dport 7946 -j CONTROL_AND_STORAGE
sudo iptables -A INPUT -p udp --dport 7946 -j CONTROL_AND_STORAGE
sudo iptables -A INPUT -p tcp --dport 8080 -j CONTROL_AND_STORAGE
sudo iptables -A INPUT -p tcp --dport 7946 -s 10.10.10.0/24 -j ACCEPT
sudo iptables -P INPUT DROP
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

!!! tip "Recommendation"
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
[demo@demo ~]# sudo lsblk
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
[demo@demo ~]# sudo nvme id-ns /dev/nvme0n1
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
nvme format --lbaf=<lbaf> --ses=0 /dev/nvmeXnY
```

The output of the command should give a successful response when executing similar to the below example.

```plain title="Example output of NVMe device formatting"
[demo@demo ~]# sudo nvme format --lbaf=4 --ses=0 /dev/nvme0n1
You are about to format nvme0n1, namespace 0x1.
WARNING: Format may irrevocably delete this device's data.
You have 10 seconds to press Ctrl-C to cancel this operation.

Use the force [--force] option to suppress this warning.
Sending format operation ...
Success formatting namespace:1
```

With all NVMe devices prepared, the storage node software can be deployed.

```bash title="Deploy the storage node"
sbcli -d sn deploy --ifname eth0
```

The output will look something like the following example:

```plain title="Example output of a storage node deployment"
[root@vm13 ~]# sbcli -d sn deploy --ifname eth0
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

### Attach the Storage Node to the Control Plane

When all storage nodes are prepared, they can be added to the storage cluster.

!!! warning
    The following command are executed from a management node. Attaching a storage node to a control plane is executed
    from a management node.

```
sbcli -d sn add-node <CLUSTER_ID> <SN_CTR_ADDR> <MGT_IF> \
  --max-lvol 50 \
  --max-prov 500g \
  --number-of-devices <NUM_STOR_NVME> \
  --partitions 0 \
  --data-nics <DATA_IF>
```

```plain title="Example output of adding a node to the control plane"
sbcli -d sn add-node 7bef076c-82b7-46a5-9f30-8c938b30e655 192.168.10.2:5000 eth0 --max-lvol 50 --max-prov 500g --number-of-devices 3 --partitions 0 --data-nics eth1
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