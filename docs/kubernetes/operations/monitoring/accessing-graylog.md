---
title: "Accessing Graylog"
description: "Reach the Graylog log search of a simplyblock control plane on Kubernetes through a port-forward and retrieve its admin password."
weight: 10650
---

The observability stack of a local simplyblock control plane includes Prometheus, Grafana, and Graylog. Graylog
collects the logs of all control plane and storage node services. Like Grafana, it is installed when the Helm value
`controlplane.observability.enabled` is `true` (see [Accessing Grafana](accessing-grafana.md)).

## How to Access Graylog

Graylog is served by the `simplyblock-graylog` Service on port 9000 in the namespace of the control plane. For a quick
look, the Service is forwarded to the local machine:

```bash title="Forwarding the Graylog Service"
kubectl -n simplyblock port-forward svc/simplyblock-graylog 9000:9000
```

Graylog is then reachable at `http://localhost:9000`. For permanent access, the Service is exposed through the ingress
controller or load balancer of the Kubernetes cluster, with session stickiness when several replicas are served.

### Credentials

Graylog is logged in to as the user _admin_. Its password is the monitoring secret of the control plane, the same
password Grafana uses, which is held in the `simplyblock-grafana-secrets` Secret:

```bash title="Retrieving the Graylog password"
kubectl get secret -n simplyblock simplyblock-grafana-secrets \
    -o jsonpath="{.data.MONITORING_SECRET}" | base64 --decode
```

Graylog itself checks the SHA-256 hash of that password, which is stored as `GRAYLOG_ROOT_PASSWORD_SHA2` in the
`simplyblock-graylog-secret` Secret. The `GRAYLOG_PASSWORD_SECRET` key of the same Secret is the internal secret Graylog
uses to secure stored user passwords, not a login password.

**Credentials**<br/>
Username: `admin`<br/>
Password: `<PASSWORD>`

!!! warning
    The chart ships default values for `controlplane.observability.secret`,
    `controlplane.observability.graylog.rootPasswordSha2`, and `controlplane.observability.graylog.passwordSecret`.
    All three should be replaced on every installation, and `rootPasswordSha2` has to stay the SHA-256 hash of the
    monitoring secret.
