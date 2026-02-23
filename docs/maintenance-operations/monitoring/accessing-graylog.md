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

The Graylog installation uses the cluster secret as its password for the user _admin_.

Depending on the selected installation method for the simplyblock control plane, there are two ways to retrieve the
Graylog password.

If the simplyblock control plane is installed outside Kubernetes, to retrieve the cluster secret, the following
commands should be used:

```bash title="Get the cluster uuid"
{{ cliname }} cluster list
```

```bash title="Get the cluster secret"
{{ cliname }} cluster get-secret <CLUSTER_ID>
```

When installed inside Kubernetes, the Graylog password can be retrieved using `kubectl` as follows:

```bash title="Retrieve the Graylog password"
kubectl get secret -n simplyblock simplyblock-graylog``-secret \
    -o jsonpath="{.data.GRAYLOG_PASSWORD_SECRET}" | base64 --decode
```

The resulting password can be used to log in to Graylog.

```plain title="Example output for Graylog password"
[root@demo ~]# kubectl get secret -n simplyblock simplyblock-graylog-secret \
    -o jsonpath="{.data.GRAYLOG_PASSWORD_SECRET}" | base64 --decode
is6SP2EdWg0NdmVGv6CEp5h87d7g9sdassem4t9pouMqDQnHwXMSomas1qcbKSt5yISr8eBHv4Y7Dbswhyz84Ut0TW6kqsiPs
```

**Credentials**<br/>
Username: `admin`<br/>
Password: `<PASSWORD>`
