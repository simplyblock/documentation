---
title: "Install Control Plane"
weight: 32000
---

## Control Plane Installation

The first step when installing simplyblock on Plain Linux (Docker), is to install the control plane. The control plane manages one or more
storage clusters. If an existing control plane is available and the new cluster should be added to it, this section
can be skipped. 

Jump right to the [Storage Plane Installation](install-sp.md).

### Firewall Configuration (CP)

Simplyblock requires a number of TCP and UDP ports to be opened from certain networks. Additionally, it requires IPv6
to be disabled on management nodes.

The following is a list of all ports (TCP and UDP) required to operate as a management node. Attention is required, as
this list is for management nodes only. Storage nodes have a different port configuration.

{% include 'control-plane-network-port-table.md' %}

With the previously defined subnets, the following snippet disables IPv6 and configures the iptables automatically.

!!! danger
    The example assumes that you have an external firewall between the _admin_ network and the public internet!<br/>
    If this is not the case, ensure the correct source access for ports _22_ and _80_.

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
sudo iptables -A SIMPLYBLOCK -m state --state ESTABLISHED,RELATED -j RETURN
sudo iptables -A SIMPLYBLOCK -p tcp --dport 80 -j RETURN
sudo iptables -A SIMPLYBLOCK -p tcp --dport 2375 -s 192.168.10.0/24,10.10.10.0/24 -j RETURN
sudo iptables -A SIMPLYBLOCK -p tcp --dport 2377 -s 192.168.10.0/24,10.10.10.0/24 -j RETURN
sudo iptables -A SIMPLYBLOCK -p tcp --dport 4500 -s 192.168.10.0/24,10.10.10.0/24 -j RETURN
sudo iptables -A SIMPLYBLOCK -p udp --dport 4789 -s 192.168.10.0/24,10.10.10.0/24 -j RETURN
sudo iptables -A SIMPLYBLOCK -p tcp --dport 7946 -s 192.168.10.0/24,10.10.10.0/24 -j RETURN
sudo iptables -A SIMPLYBLOCK -p udp --dport 7946 -s 192.168.10.0/24,10.10.10.0/24 -j RETURN
sudo iptables -A SIMPLYBLOCK -p tcp --dport 9100 -s 192.168.10.0/24,10.10.10.0/24 -j RETURN
sudo iptables -A SIMPLYBLOCK -p tcp --dport 12201 -s 192.168.10.0/24,10.10.10.0/24 -j RETURN
sudo iptables -A SIMPLYBLOCK -p udp --dport 12201 -s 192.168.10.0/24,10.10.10.0/24 -j RETURN
sudo iptables -A SIMPLYBLOCK -p tcp --dport 12202 -s 192.168.10.0/24,10.10.10.0/24 -j RETURN
sudo iptables -A SIMPLYBLOCK -p tcp --dport 13201 -s 192.168.10.0/24,10.10.10.0/24 -j RETURN
sudo iptables -A SIMPLYBLOCK -p tcp --dport 13202 -s 192.168.10.0/24,10.10.10.0/24 -j RETURN
sudo iptables -A SIMPLYBLOCK -s 0.0.0.0/0 -j DROP
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

```bash title="Automatically check your configuration"
curl -s -L https://install.simplyblock.io/scripts/prerequisites-cp.sh | bash
```

If the check succeeds, it's time to set up the primary management node:

```bash title="Deploy the primary management node"
{{ cliname }} cluster create --ifname=<IF_NAME> --ha-type=ha
```

Some other important parameters include:

-```--enable-node-affinity```: as long as a node is not full (out of capacity), the first chunk 
  of data is always stored on the local node (the node to which the volume is attached). 
  This reduces network traffic and latency - accelerating particularly the read - but may lead to an
  inequal distribution of capacity within the cluster. Generally, using node affinity accelerates
  reads, but leads to higher variability in performance across nodes in the cluster.
  It is recommended on shared networks and networks below 100gb/s. 
-```--data-chunks-per-stripe, --parity-chunks-per-stripe```: those two parameters together make up
  the default erasure coding schema of the node (e.g. 1+1, 2+2, 4+2). Starting from R25.10, it is also
  possible to set individual schemas per volume, but this feature is still in alpha-stage.
-```--cap-warn, --cap-crit```: Warning and critical limits for overall cluster utilization. The warning
  limit will just cause issuance of warnings in the event log if exceeded, the "critical" limit will 
  place the cluster into read-only mode. For large clusters, 99% of "critical" limit is ok, for small
  clusters (less than 50TB) better use 97%. 
-```--prov-cap-warn, --prov-cap-crit```: Warning and critical limits for over-provisioning. Exceeding
  these limits will cause entries in the cluster log. If the critical limit is exceeded, 
  new volumes cannot be provisioned and volumes cannot be enlarged. A limit of 500% is typical.
-```--log-del-interval```: Number of days by which logs are retained. Log storage can grow significantly 
  and it is recommended to keep logs for not longer than one week.
-```--metrics-retention-period```: Number of days by which the io statistics and other metrics are retained.  
  The amount of data per day is significant, typically limit to a few days or a week.
-```--contact-point```: This is a webhook endpoint for alerting (critical events such as storage nodes becoming unreachable)
-```--fabric```: choose tcp, rdma or both. If both fabrics are chosen, volumes can connect to the cluster
  using both options (defined per volume or storage class), but the cluster internally uses rdma.
-```--qpair-count```: The amount of queue pairs (sockets) per volume for an initiator (host) to connect to the 
  target (server). More queue pairs per volume increase concurrency and volume performance, but require more
  server resources (ram, cpu) and thus limit the total amount of volumes per storage node. The default is 3. 
  If you need few, very performant volumes, increase the amount, if you need a large amount of less performant 
  volumes decrease it. More than 12 parallel connections have limited impact on overall performance. Also, the 
  host requires at least one core per queue pair.
* ```--name```: A human-readable name for the cluster

The output should look something like this:

```plain title="Example output of control plane deployment"
[root@vm11 ~]# {{ cliname }} cluster create --ifname=eth0 --ha-type=ha
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
[root@vm11 ~]# {{ cliname }} cluster get-secret 7bef076c-82b7-46a5-9f30-8c938b30e655
e8SQ1ElMm8Y9XIwyn8O0
```

### Secondary Management Nodes

A production cluster requires at least three management nodes in the control plane. Hence, additional management
nodes need to be added.

On the secondary nodes, the network requires the same configuration as on the primary. Executing the commands under
[Firewall Configuration (CP)](#firewall-configuration-cp) will get the node prepared.

Afterward, Python, Pip, and `{{ cliname }}` need to be installed.

```bash title="Deployment preparation"
sudo yum -y install python3-pip
pip install {{ cliname }} --upgrade
```

Finally, we deploy the management node software and join the control plane cluster.

```bash title="Secondary management node deployment"
{{ cliname }} mgmt add <CP_PRIMARY_IP> <CLUSTER_ID> <CLUSTER_SECRET> <IF_NAME>
```

Running against the primary management node in the control plane should create an output similar to the following
example:

```plain title="Example output joining a control plane cluster"
[demo@demo ~]# {{ cliname }} mgmt add 192.168.10.1 7bef076c-82b7-46a5-9f30-8c938b30e655 e8SQ1ElMm8Y9XIwyn8O0 eth0
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
