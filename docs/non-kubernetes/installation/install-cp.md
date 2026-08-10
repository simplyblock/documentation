---
title: "Install Control Plane"
description: "Install Control Plane: The first step when installing simplyblock on plain Linux (Docker), is to install the control plane."
weight: 32000
---

### Prerequisites

Before starting the deployment, make sure that the following prerequisites as described in the
[hardware prerequisites](../../deployment-preparation/hardware-requirements.md) and
[software prerequisites](../../deployment-preparation/software-requirements.md) section are met.

## Control Plane Installation

The first step when installing simplyblock on plain Linux (Docker) is to install the control plane. The control
plane manages one or more storage clusters. If an existing control plane is available and the new cluster should be
added to it, this section can be skipped.

In this case, the following section can be skipped to [Storage Plane Installation](install-sp.md).

### Firewall Configuration (CP)

Simplyblock requires a number of TCP and UDP ports to be opened from certain networks.

The following is a list of all ports (TCP and UDP) required to operate as a management node. Attention is required, as
this list is for management nodes only. Storage nodes have a different port configuration.

{% include 'network-port-table.md' %}

With the previously defined subnets, the following snippet configures the iptables automatically.


```bash title="Network Configuration"
#!/bin/bash

# ICMP ingress
iptables -A INPUT -p icmp -j ACCEPT

# storage-node-api — TCP 5000, ingress + egress
iptables -A INPUT  -p tcp --dport 5000 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 5000 -j ACCEPT

# NVMf — TCP 4420-4499, ingress + egress
iptables -A INPUT  -p tcp --dport 4420:4499 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 4420:4499 -j ACCEPT

# FoundationDB — TCP 4500, ingress
iptables -A INPUT -p tcp --dport 4500 -j ACCEPT

# Control plane API — TCP 80, egress
iptables -A OUTPUT -p tcp --dport 80 -j ACCEPT

# Control plane RPC — TCP 8080-9044, ingress + egress
iptables -A INPUT  -p tcp --dport 8080:9044 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 8080:9044 -j ACCEPT

# Monitoring Stack — optional
# iptables -A INPUT  -p tcp -m multiport --dports 12202,13301,13302,9200,9090 -j ACCEPT
# iptables -A OUTPUT -p tcp -m multiport --dports 12202,13301,13302,9200,9090 -j ACCEPT
```

### Management Node Installation

Now that the network is configured, the management node software can be installed.

Simplyblock provides a command line interface called `{{ cliname }}`. It's built in Python and requires
Python 3 and Pip (the Python package manager) installed on the machine. This can be achieved with `yum`.

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

```bash title="Automatically check the configuration"
curl -s -L https://install.simplyblock.io/scripts/prerequisites-cp.sh | bash
```

If the check succeeds, it's time to set up the primary management node:

```bash title="Deploy the primary management node"
{{ cliname }} cluster create --ifname=<IF_NAME>
```

Important cluster deployment options can be found in the [Cluster Deployment Options](../../deployment-preparation/cluster-deployment-options.md).

The output should look something like this:

```plain title="Example output of control plane deployment"
[root@demo ~]# {{ cliname }} cluster create --ifname=eth0 --ha-type=ha
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

```bash title="Get the cluster secret"
{{ cliname }} cluster get-secret <CLUSTER_ID>
```

```plain title="Example output get cluster secret"
[root@demo ~]# {{ cliname }} cluster get-secret 7bef076c-82b7-46a5-9f30-8c938b30e655
e8SQ1ElMm8Y9XIwyn8O0
```

### Secondary Management Nodes

A production cluster requires at least three management nodes in the control plane. Hence, additional management
nodes need to be added.

On the secondary nodes, the network requires the same configuration as on the primary. Executing the commands under
[Firewall Configuration (CP)](#firewall-configuration-cp) will get the node prepared.

!!! important "Highly Available Control Plane"
    When simplyblock is deployed with an HA control plane, an external load balancer is required to distribute
    requests of the storage plane to active control plane nodes. This is required to ensure that the control plane
    is not a single point of failure when one or more management nodes are down.

Afterward, Python, Pip, and `{{ cliname }}` need to be installed.

```bash title="Deployment preparation"
sudo yum -y install python3-pip
pip install {{ cliname }} --upgrade
```

Finally, the management node software is deployed and joins the control plane cluster.

```bash title="Secondary management node deployment"
{{ cliname }} mgmt add <CP_PRIMARY_IP> <CLUSTER_ID> <CLUSTER_SECRET>
```

Running against the primary management node in the control plane should create an output similar to the following
example:

```plain title="Example output joining a control plane cluster"
[demo@demo ~]# {{ cliname }} mgmt add 192.168.10.1 7bef076c-82b7-46a5-9f30-8c938b30e655 e8SQ1ElMm8Y9XIwyn8O0
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
