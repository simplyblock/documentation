---
title: "Accessing Graylog"
weight: 30049
---

Simplyblock's control plane includes a Prometheus, Grafana, and Graylog installation.

Graylog retrieves logs for all control plane and storage node services.

The standard retention period for metrics is 7 days. However, this can be changed when creating a cluster.

## How to access Graylog

Graylog can be accessed through all management node API. It is recommended to set up a load balancer with session
stickyness in front of the Graylog installation(s).

```plain title="Graylog URLs"
http://<MGMT_NODE_IP>/graylog
```

### Credentials

The Graylog installation uses the cluster secret as its password for the user _admin_. To retrieve the cluster secret,
the following command should be used:

```bash title="Get the cluster secret"
{{ cliname }} cluster get-secret <CLUSTER_ID>
```

**Credentials**<br/>
Username: **admin**<br/>
Password: **<CLUSTER_SECRET>**
