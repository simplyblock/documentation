---
title: "Accessing Graylog"
weight: 30049
---

Simplyblock's control plane include a Prometheus, Grafana, and Graylog installation.

Graylog retrieves logs for all control plane and storage nodes services.

The standard retention period for metrics is 7 days. This, however, can be changed while creating a cluster.

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
{{ variables.cliname }} cluster get-secret <CLUSTER_ID>
```

**Credentials**<br/>
Username: **admin**<br/>
Password: **<CLUSTER_SECRET>**
