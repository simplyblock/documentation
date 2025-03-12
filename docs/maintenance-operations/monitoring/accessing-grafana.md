---
title: "Accessing Grafana"
weight: 30000
---

Simplyblock's control plane include a Prometheus and Grafana installation.

Grafana retrieves metric data from Prometheus, including capacity, io statistics, the cluster event log. Additionally,
Grafana is used for alerting via Slack or email.

The standard retention period for metrics is 7 days. This, however, can be changed while creating a cluster.

## How to access Grafana

Grafana can be accessed through all management nodes via port 3000. It is recommended to set up a load balancer with
session stickyness in front of the Grafana installation(s).

```plain title="Grafana URLs"
http://<MGMT_NODE_IP>:3000
```

To retrieve the endpoint address from the cluster itself, use the following command:

```bash title="Retrieving the Grafana endpoint"
sbcli cluster get <CLUSTER_ID> | grep grafana_endpoint
```

### Credentials

The Grafana installation uses the cluster secret as its password for the user _admin_. To retrieve the cluster secret,
the following command should be used:

```bash title="Get the cluster secret"
sbcli cluster get-secret <CLUSTER_ID>
```

**Credentials**<br/>
Username: **admin**<br/>
Password: **<CLUSTER_SECRET>**
