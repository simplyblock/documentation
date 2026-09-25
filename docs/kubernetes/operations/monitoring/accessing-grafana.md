---
title: "Accessing Grafana"
description: "Enable the Grafana dashboards of a simplyblock control plane on Kubernetes, reach them through a port-forward, and retrieve the admin password."
weight: 10640
---

The observability stack of a local simplyblock control plane includes Prometheus, Grafana, and Graylog. Grafana
retrieves metric data from Prometheus, including capacity, I/O statistics, and the cluster event log, and it delivers
the [alerts](alerts.md) of the cluster.

The stack is optional. It is installed with a local control plane (the `standalone` deployment profile) when the Helm
value `controlplane.observability.enabled` is `true`, which is not the default.

```bash title="Enabling the observability stack"
helm upgrade simplyblock-operator simplyblock/simplyblock-operator \
  -n simplyblock --reuse-values \
  --set controlplane.observability.enabled=true
```

## How to Access Grafana

Grafana is served by the `simplyblock-grafana` Service on port 3000 in the namespace of the control plane. For a quick
look, the Service is forwarded to the local machine:

```bash title="Forwarding the Grafana Service"
kubectl -n simplyblock port-forward svc/simplyblock-grafana 3000:3000
```

Grafana is then reachable at `http://localhost:3000`. For permanent access, the Service is exposed through the ingress
controller or load balancer of the Kubernetes cluster. A load balancer in front of several Grafana replicas should use
session stickiness.

### Credentials

The admin password of Grafana is held in the `simplyblock-grafana-secrets` Secret and is set through the Helm value
`controlplane.observability.secret`. It is retrieved with `kubectl`:

```bash title="Retrieving the Grafana password"
kubectl get secret -n simplyblock simplyblock-grafana-secrets \
    -o jsonpath="{.data.MONITORING_SECRET}" | base64 --decode
```

```plain title="Example output for Grafana password"
sWbpOgbe3bKnCfcnfaDi
```

**Credentials**<br/>
Username: `admin`<br/>
Password: `<PASSWORD>`

!!! warning
    The chart ships a default value for `controlplane.observability.secret`. It should be replaced with a unique
    password on every installation.

## Grafana Dashboards

The following dashboards are provisioned:

- Cluster
- Storage node
- Device
- Logical Volume
- Storage Pool
- FoundationDB

Dashboard widgets are designed to be self-explanatory.

By default, each dashboard contains data for all objects (for example, all devices) in a cluster. It is, however,
possible to filter them by particular objects (for example, devices, storage nodes, or logical volumes) and to change
the timescale and window.

Dashboards include physical and logical capacity utilization dynamics, IOPS, I/O throughput, and latency dynamics (all
separate for read, write, and unmap).

For capacity readings without Grafana, see [Capacity Metrics API](index.md#capacity-metrics-api).
