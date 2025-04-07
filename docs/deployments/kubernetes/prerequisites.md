---
title: "Prerequisites"
weight: 30000
---

Before deploying simplyblock on a Kubernetes cluster, it is essential to ensure that the environment meets all necessary
infrastructure, software, and configuration requirements. Proper planning and preparation will help guarantee a smooth
installation, optimal performance, and long-term stability of the simplyblock storage system.

This section outlines the key hardware and software prerequisites, including supported Kubernetes versions, required
resources for management and storage nodes, necessary permissions, network configurations, and storage prerequisites.

Verifying these requirements before installation will help avoid compatibility issues and ensure that Simplyblock
integrates seamlessly with your Kubernetes deployment.

## Node Sizing

Simplyblock has certain requirements in terms of CPU, RAM, and storage. See the specific
[Node Sizing](../deployment-planning/node-sizing.md) documentation to learn more.

## Control Plane

Minimum 2 physical cores
Minimum 8GiB
35 GiB unused disk space
Supported Linux distribution
3 management nodes

```bash title="Create Management Cluster"
sbcli-pre cluster create
sbcli-pre cluster list
```

```bash title="Sample output control plane creation"
[demo@demo ~]# sudo sbcli-pre cluster create --ifname=ens18 --ha-type=ha
2025-02-26 12:37:06,097: INFO: Installing dependencies...
2025-02-26 12:37:13,338: INFO: Installing dependencies > Done
2025-02-26 12:37:13,358: INFO: Node IP: 192.168.10.151
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
7bef076c-82b7-46a5-9f30-8c938b30e655 # (1)
```

1.  :light_bulb: This is the cluster id: :octicons-arrow-down-24:<br/>7bef076c-82b7-46a5-9f30-8c938b30e655

Returns cluster-id


```plain title="Example output for listing available clusters"
[demo@demo ~]# sudo sbcli-pre cluster list
+--------------------------------------+-----------------------------------------------------------------+---------+-------+------------+---------------+-----+---------+
| UUID                                 | NQN                                                             | ha_type | tls   | mgmt nodes | storage nodes | Mod | Status  |
+--------------------------------------+-----------------------------------------------------------------+---------+-------+------------+---------------+-----+---------+
| 7bef076c-82b7-46a5-9f30-8c938b30e655 | nqn.2023-02.io.simplyblock:7bef076c-82b7-46a5-9f30-8c938b30e655 | ha      | False | 3          | 10             | 1x1 | unready |
+--------------------------------------+-----------------------------------------------------------------+---------+-------+------------+---------------+-----+---------+
```

### Get Cluster Secret
sbcli-pre cluster get-secret <cluster_uuid>

```bash title="Example output get cluster secret"
[demo@demo ~]# sudo sbcli-pre cluster get-secret 7bef076c-82b7-46a5-9f30-8c938b30e655
e8SQ1ElMm8Y9XIwyn8O0 # (1)
```

1. :light_bulb: This is the cluster secret: :octicons-arrow-down-24:<br/>e8SQ1ElMm8Y9XIwyn8O0

### Control Plane Secondaries

```bash title="Adding a management node to the control plane"
sudo yum -y install python3-pip
pip install sbcli-pre --upgrade
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
sudo sysctl -w net.ipv6.conf.default.disable_ipv6=1
sbcli mgmt add 192.168.10.151 7bef076c-82b7-46a5-9f30-8c938b30e655 e8SQ1ElMm8Y9XIwyn8O0 ens18
sbcli mgmt add <CTR_PLANE_PRI_IP> <CLUSTER_ID> <CLUSTER_SECRET> <IF_NAME>
```

```plain title="Example output joining a control plane cluster"
[root@vm12 ~]# sbcli mgmt add 192.168.10.151 7bef076c-82b7-46a5-9f30-8c938b30e655 e8SQ1ElMm8Y9XIwyn8O0 ens18
2025-02-26 12:40:17,815: INFO: Cluster found, NQN:nqn.2023-02.io.simplyblock:7bef076c-82b7-46a5-9f30-8c938b30e655
2025-02-26 12:40:17,816: INFO: Installing dependencies...
2025-02-26 12:40:25,606: INFO: Installing dependencies > Done
2025-02-26 12:40:25,626: INFO: Node IP: 192.168.10.152
2025-02-26 12:40:26,802: INFO: Joining docker swarm...
2025-02-26 12:40:27,719: INFO: Joining docker swarm > Done
2025-02-26 12:40:32,726: INFO: Adding management node object
2025-02-26 12:40:32,745: INFO: {"cluster_id": "7bef076c-82b7-46a5-9f30-8c938b30e655", "event": "OBJ_CREATED", "object_name": "MgmtNode", "message": "Management node added vm12", "caused_by": "cli"}
2025-02-26 12:40:32,752: INFO: Done
2025-02-26 12:40:32,755: INFO: Node joined the cluster
cdde125a-0bf3-4841-a6ef-a0b2f41b8245
```

### Network Configuration

#### Disable IPv6

```bash title="Permanently disable IPv6"
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
sudo sysctl -w net.ipv6.conf.default.disable_ipv6=1
```

Defined networks:

- _internal:_ The subnet for communication with the control plane
- _storage:_ The subnet for communication with and between the storage plane
- _loadbalancer:_ The subnet between the load balancer and control plane
- _management:_ Valid IPs or IP ranges for direct management access

| Direction | Source or target nw | ports | protocol |
|-----------|---------------------|-------|----------|
| ingress   | management          | 80    | tcp      |
| ingress   | mgmt                | 3000  | tcp      |
| ingress   | mgmt                | 9000  | tcp      |
| egress    | all                 | all   | all      |

<figure markdown>
| Service         | Direction | Source Network    | Port      | Protocol(s) |
|-----------------|-----------|-------------------|-----------|-------------|
| API (HTTPS)     | ingress   | loadbalancer      | 80        | TCP         |
| SSH             | ingress   | management        | 22        | TCP         |
| Grafana         | ingress   | loadbalancer      | 3000      | TCP         |
| Graylog         | ingress   | loadbalancer      | 9000      | TCP         |
| Docker Swarm    | ingress   | storage, internal | 2375      | TCP         |
| Docker Swarm    | ingress   | storage, internal | 2377      | TCP         |
| Docker Swarm    | ingress   | storage, internal | 4789      | UDP         |
| Docker Swarm    | ingress   | storage, internal | 7946      | TCP / UDP   |
| Graylog         | ingress   | storage, internal | 12201     | TCP / UDP   |
| FoundationDB    | ingress   | storage, internal | 4800      | TCP         |
| FoundationDB    | ingress   | storage           | 4500      | TCP         |
| Cluster Control | ingress   | storage           | 4420      | TCP         |
| Cluster Control | ingress   | storage           | 9090-9099 | TCP         |
<figcaption>Test</figcaption>
</figure>

| Service     | Direction | Target Network | Port | Protocol(s) |
|-------------|-----------|----------------|------|-------------|
| All traffic | egress    | [0.0.0.0/0]    | ALL  | ALL         |

## Storage Plane

```bash title="Format the NVMe devices"
lsblk
nvme id-ns /dev/nvmeXnY
nvme format --lbaf=<lbaf> --ses=0 /dev/nvmeXnY
```

### Deploy a Storage Node

```bash
sbcli -d sn deploy --ifname ens18
```

```plain title="Example output deploying storage node"
[demo@demo-sn-1 ~]# sbcli sn deploy --ifname ens18
2025-02-26 13:35:06,991: INFO: NVMe SSD devices found on node:
2025-02-26 13:35:07,038: INFO: Installing dependencies...
2025-02-26 13:35:13,508: INFO: Node IP: 192.168.10.153
2025-02-26 13:35:13,623: INFO: Pulling image public.ecr.aws/simply-block/simplyblock:hmdi
2025-02-26 13:35:15,219: INFO: Recreating SNodeAPI container
2025-02-26 13:35:15,543: INFO: Pulling image public.ecr.aws/simply-block/ultra:main-latest
192.168.10.153:5000
```

### Add Storage Node (from Management Node)

```plain title="Example output for adding a storage node"
[root@vm11 ~]# sbcli sn add-node 3196b77c-e6ee-46c3-8291-736debfe2472 192.168.10.152:5000 ens18 --max-lvol 100 --max-prov 5000 --number-of-devices 3 --partitions 0
2025-02-26 14:55:17,236: INFO: Adding Storage node: 192.168.10.152:5000
2025-02-26 14:55:17,340: INFO: Instance id: 0b0c825e-3d16-4d91-a237-51e55c6ffefe
2025-02-26 14:55:17,341: INFO: Instance cloud: None
2025-02-26 14:55:17,341: INFO: Instance type: None
2025-02-26 14:55:17,342: INFO: Instance privateIp: 192.168.10.152
2025-02-26 14:55:17,342: INFO: Instance public_ip: 192.168.10.152
2025-02-26 14:55:17,347: INFO: Node Memory info
2025-02-26 14:55:17,347: INFO: Total: 24.3 GB
2025-02-26 14:55:17,348: INFO: Free: 23.2 GB
2025-02-26 14:55:17,348: INFO: Minimum required huge pages memory is : 14.8 GB
2025-02-26 14:55:17,349: INFO: Joining docker swarm...
2025-02-26 14:55:21,060: INFO: Deploying SPDK
2025-02-26 14:55:31,969: INFO: adding alceml_2d1c235a-1f4d-44c7-9ac1-1db40e23a2c4
2025-02-26 14:55:32,010: INFO: creating subsystem nqn.2023-02.io.simplyblock:vm12:dev:2d1c235a-1f4d-44c7-9ac1-1db40e23a2c4
2025-02-26 14:55:32,022: INFO: adding listener for nqn.2023-02.io.simplyblock:vm12:dev:2d1c235a-1f4d-44c7-9ac1-1db40e23a2c4 on IP 192.168.10.152
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

- Kubernetes v1.25 or higher
- Privileged container


```plain title="Example output of a storage node listing"
[root@vm11 ~]# sbcli sn list
+--------------------------------------+----------+----------------+---------+-------+--------+--------+-----------+--------------------------------------+------------+----------------+
| UUID                                 | Hostname | Management IP  | Devices | LVols | Status | Health | Up time   | Cloud ID                             | Cloud Type | Ext IP         |
+--------------------------------------+----------+----------------+---------+-------+--------+--------+-----------+--------------------------------------+------------+----------------+
| 37b404b9-36aa-40b3-8b74-7f3af86bd5a5 | vm12     | 192.168.10.152 | 3/3     | 0     | online | True   | 1h 8m 11s | 0b0c825e-3d16-4d91-a237-51e55c6ffefe | None       | 192.168.10.152 |
| 1a5d4106-1bc8-4d68-91e5-ac6e93fb0549 | vm13     | 192.168.10.153 | 3/3     | 0     | online | True   | 45m 27s   | de45504a-d36b-42e6-996d-133ec79f4d47 | None       | 192.168.10.153 |
| 01b1caa0-b94a-4863-a735-832250faee61 | vm14     | 192.168.10.154 | 3/3     | 0     | online | True   | 43m 24s   | 1d20291f-3ca9-4aac-81e9-7d3e3e33e553 | None       | 192.168.10.154 |
+--------------------------------------+----------+----------------+---------+-------+--------+--------+-----------+--------------------------------------+------------+----------------+
```