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

## Grafana Dashboards

All dashboards are stored in per-cluster folders. Each cluster contains the following dashboards entries:

- Cluster
- Storage node
- Device
- Logical Volume
- Storage Pool

Dashboard widgets are designed to be self-explanatory.

Per default, each of those dashboards contain data for all objects (e.g. all devices) in a cluster. It is, however,
possible to filter them by particular objects (e.g. devices, storage nodes or logical volumes) and to change the
timescale and window.

Dashboards include physical and logical capacity utilization dynamics, IOPS, I/O throughput, and latency dynamics (all
separate for read, write and unmap). While all data of the event log is currently stored in Prometheus, they aren't
used at the time of writing.
