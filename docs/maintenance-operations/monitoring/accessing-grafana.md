---
title: "Accessing Grafana"
weight: 30000
---

Simplyblock's control plane includes a Prometheus, Grafana, and Graylog installation.

Grafana retrieves metric data from Prometheus, including capacity, I/O statistics, and the cluster event log.
Additionally, Grafana is used for alerting via Slack or email.

The standard retention period for metrics is 7 days. However, this can be changed when creating a cluster.

## How to access Grafana

Grafana can be accessed through all management node API. It is recommended to set up a load balancer with session
stickyness in front of the Grafana installation(s).

```plain title="Grafana URLs"
http://<MGMT_NODE_IP>/grafana
```

To retrieve the endpoint address from the cluster itself, use the following command:

```bash title="Retrieving the Grafana endpoint"
{{ cliname }} cluster get <CLUSTER_ID> | grep grafana_endpoint
```

### Credentials

The Grafana installation uses the cluster secret as its password for the user _admin_.

Depending on the selected installation method for the simplyblock control plane, there are two ways to retrieve the
Grafana password.

If the simplyblock control plane is installed outside Kubernetes, to retrieve the cluster secret, the following
commands should be used:

```bash title="Get the cluster uuid"
{{ cliname }} cluster list
```

```bash title="Get the cluster secret"
{{ cliname }} cluster get-secret <CLUSTER_ID>
```

When installed inside Kubernetes, the Grafana password can be retrieved using `kubectl` as follows:

```bash title="Retrieve the Grafana password"
kubectl get secret -n simplyblock simplyblock-grafana-secrets \
    -o jsonpath="{.data.MONITORING_SECRET}" | base64 --decode
```

The resulting password can be used to log in to Grafana.

```plain title="Example output for Grafana password"
[root@demo ~]# kubectl get secret -n simplyblock simplyblock-grafana-secrets \
    -o jsonpath="{.data.MONITORING_SECRET}" | base64 --decode
sWbpOgbe3bKnCfcnfaDi
```

**Credentials**<br/>
Username: `admin`<br/>
Password: `<PASSWORD>`

## Grafana Dashboards

All dashboards are stored in per-cluster folders. Each cluster contains the following dashboard entries:

- Cluster
- Storage node
- Device
- Logical Volume
- Storage Pool
- Storage Plane node(s) system monitoring
- Control Plane node(s) system monitoring

Dashboard widgets are designed to be self-explanatory.

By default, each dashboard contains data for all objects (e.g., all devices) in a cluster. It is, however, possible to
filter them by particular objects (e.g., devices, storage nodes, or logical volumes) and to change the timescale and
window.

Dashboards include physical and logical capacity utilization dynamics, IOPS, I/O throughput, and latency dynamics (all
separate for read, write, and unmap). While all data from the event log is currently stored in Prometheus, they weren't
used at the time of writing.
