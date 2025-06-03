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
{{ cliname }} cluster create
{{ cliname }} cluster list
```

```bash title="Sample output control plane creation"
[demo@demo ~]# sudo {{ cliname }} cluster create --ifname=ens18 --ha-type=ha
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
[demo@demo ~]# sudo {{ cliname }} cluster list
+--------------------------------------+-----------------------------------------------------------------+---------+-------+------------+---------------+-----+---------+
| UUID                                 | NQN                                                             | ha_type | tls   | mgmt nodes | storage nodes | Mod | Status  |
+--------------------------------------+-----------------------------------------------------------------+---------+-------+------------+---------------+-----+---------+
| 7bef076c-82b7-46a5-9f30-8c938b30e655 | nqn.2023-02.io.simplyblock:7bef076c-82b7-46a5-9f30-8c938b30e655 | ha      | False | 3          | 10             | 1x1 | unready |
+--------------------------------------+-----------------------------------------------------------------+---------+-------+------------+---------------+-----+---------+
```

### Get Cluster Secret
{{ cliname }} cluster get-secret <cluster_uuid>

```bash title="Example output get cluster secret"
[demo@demo ~]# sudo {{ cliname }} cluster get-secret 7bef076c-82b7-46a5-9f30-8c938b30e655
e8SQ1ElMm8Y9XIwyn8O0 # (1)
```

1. :light_bulb: This is the cluster secret: :octicons-arrow-down-24:<br/>e8SQ1ElMm8Y9XIwyn8O0

### Control Plane Secondaries

```bash title="Adding a management node to the control plane"
sudo yum -y install python3-pip
pip install {{ cliname }} --upgrade
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
sudo sysctl -w net.ipv6.conf.default.disable_ipv6=1
{{ cliname }} mgmt add 192.168.10.151 7bef076c-82b7-46a5-9f30-8c938b30e655 e8SQ1ElMm8Y9XIwyn8O0 ens18
{{ cliname }} mgmt add <CTR_PLANE_PRI_IP> <CLUSTER_ID> <CLUSTER_SECRET> <IF_NAME>
```

```plain title="Example output joining a control plane cluster"
[root@vm12 ~]# {{ cliname }} mgmt add 192.168.10.151 7bef076c-82b7-46a5-9f30-8c938b30e655 e8SQ1ElMm8Y9XIwyn8O0 ens18
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
- _loadbalancer:_ The subnet between the load balancer and the control plane
- _management:_ Valid IPs or IP ranges for direct management access

| Direction | Source or target nw | ports | protocol |
|-----------|---------------------|-------|----------|
| ingress   | management          | 80    | tcp      |
| ingress   | mgmt                | 3000  | tcp      |
| ingress   | mgmt                | 9000  | tcp      |
| egress    | all                 | all   | all      |

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

| Service     | Direction | Target Network | Port | Protocol(s) |
|-------------|-----------|----------------|------|-------------|
| All traffic | egress    | [0.0.0.0/0]    | ALL  | ALL         |

## Storage Plane

```bash title="Format the NVMe devices"
lsblk
nvme id-ns /dev/nvmeXnY
nvme format --lbaf=<lbaf> --ses=0 /dev/nvmeXnY
```

### Kubernetes Requirements

- Kubernetes v1.25 or higher
- Privileged container
