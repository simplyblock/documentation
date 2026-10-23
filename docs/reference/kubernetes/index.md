---
title: "Simplyblock Helm Chart"
description: "Overview of the simplyblock-operator Helm chart: what it renders per deployment profile, and example values files for the common deployment scenarios."
weight: 20100
---

The `simplyblock-operator` Helm chart installs the Simplyblock Operator, all simplyblock CRDs, the admission webhooks,
and the metrics API. On top of that, it renders the custom resources the operator acts on: `ControlPlane/simplyblock`,
`SimplyblockDriver/simplyblock`, and the first discovery run. From these, the control plane and the CSI driver are
installed by the operator. Storage clusters are not configured through the chart. They are created afterward with a
`ClusterDeploymentConfig`.

This page shows what the chart renders and how the values are combined for common deployments. Every value, with its
default, is listed in the [Simplyblock Helm Chart Values](helm-values.md) reference. The installation procedure is
described in [Install Simplyblock Operator](../../kubernetes/installation/k8s-control-plane.md).

## Deployment Profiles

The value `deployment.profile` decides which custom resources the chart renders. Any other value than the three below
fails the render.

| Profile      | Renders                                                                          | Used for                                                                                                                          |
|--------------|----------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| `standalone` | `ControlPlane` with a `local` source, `SimplyblockDriver`, and the discovery run | A cluster that hosts its own control plane. FoundationDB, the object store, and the management API are installed by the operator. |
| `managed`    | `ControlPlane` with a `managed` source and `SimplyblockDriver`                   | A cluster whose storage is registered with a control plane elsewhere. Nothing is installed for the control plane.                 |
| `empty`      | None of them                                                                     | An installation where the `ControlPlane` and the `SimplyblockDriver` are written by hand afterward.                               |

The source of a `ControlPlane` cannot be changed after installation. An upgrade to the `empty` profile is refused while
a `ControlPlane` or `SimplyblockDriver` created by the release still exists.

## What the Chart Renders

Besides the operator itself, the following objects are rendered when their values say so.

| Object                                   | Rendered when                                                  | Purpose                                                                                                        |
|------------------------------------------|----------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| `ControlPlane/simplyblock`               | `deployment.profile` is `standalone` or `managed`              | The control plane, installed locally or reached remotely.                                                      |
| `SimplyblockDriver/simplyblock`          | `deployment.profile` is `standalone` or `managed`              | The CSI driver, deployed from the `driver` block.                                                              |
| `OperatorOps` with the `Discover` action | `standalone` profile and `discovery.enabled` is `true`         | The first discovery run, which writes a draft `ClusterDeploymentConfig`.                                       |
| Secret `simplyblock-csi-secret-v2`       | `externallyManagedSecret.create` is `true`                     | Credentials of clusters the operator did not create, from `csiConfig`, `csiSecret`, and `multiCluster`.        |
| Block StorageClass                       | A pool is set in `csiConfig.simplybk.pool` or `multiCluster`   | A StorageClass for a cluster that has no `StoragePool` object to write one.                                    |
| cert-manager `ClusterIssuer`             | `tls.provider` is `cert-manager` with `createSelfSignedIssuer` | The self-signed issuer the chart mints its CA certificate from.                                                |
| Observability stack                      | `controlplane.observability.enabled` is `true`                 | Graylog, Grafana, Thanos, Fluent Bit, and the MongoDB and OpenSearch subcharts.                                |
| Prometheus                               | `prometheus.enabled` is `true`                                 | The instance the control plane pushes metrics to.                                                              |
| Reloader                                 | `reloader.enabled` is `true`                                   | Rolls the workloads that mount the FoundationDB cluster file when the coordinators move.                       |
| CSI snapshot controller                  | `snapshotcontroller.create` is `true`                          | The snapshot controller and the snapshot CRDs a cluster does not serve yet.                                    |
| CSI-Addons                               | `csiaddons.create` is `true`                                   | The CSI-Addons CRDs and controller.                                                                            |
| Control Center                           | `controlCenter.enabled` is `true`                              | The web console. See [Control Center](../../disaster-recovery/control-center.md).                              |
| Ramen operators                          | `ramen.hub.enabled` or `ramen.drCluster.enabled` is `true`     | The disaster recovery operators. See [Installing Disaster Recovery](../../disaster-recovery/install/index.md). |

The `tls`, `driver`, `discovery`, and `controlplane.observability.grafana.notifications` blocks are validated by the
chart's values schema. A key that is misspelled in one of them fails the render instead of being ignored.

## Example Values Files

Each example below is a values file that is passed to `helm install` or `helm upgrade` with `-f`. Values that are not
stated keep their defaults, so a file only carries what differs.

```bash title="Installing the chart with a values file"
helm install simplyblock-operator simplyblock/simplyblock-operator \
    --namespace simplyblock \
    --create-namespace \
    -f values.yaml
```

### Dedicated Control Plane Nodes

The control plane, the operator, and the log collector are pinned to labeled nodes with `controlplane.nodeSelector` and
`controlplane.tolerations`. FoundationDB can be confined further with its own selector. Confining it to a few workers
lets the remaining workers be added to the storage cluster in parallel. At least three workers are selected for the
`double` redundancy mode and five for `triple`.

```yaml title="Example of values placing the control plane on dedicated nodes (values.yaml)"
controlplane:
  nodeSelector:
    create: true
    key: node-role.kubernetes.io/simplyblock-control-plane
    value: ""
  tolerations:
    create: true
    list:
      - key: node-role.kubernetes.io/simplyblock-control-plane
        operator: Exists
        effect: NoSchedule
  storageclass:
    name: local-path
  foundationdb:
    redundancyMode: triple
    nodeSelector:
      storage.simplyblock.io/foundationdb: ""
```

The StorageClass in `controlplane.storageclass.name` backs the FoundationDB volumes. It should not be a simplyblock
StorageClass, because the storage cluster depends on the control plane.

### Narrowing the First Discovery Run

By default, the discovery run inspects every schedulable worker, and the run and its draft are placed in the release
namespace. The `discovery` block narrows the workers and devices before the draft is written. The values are copied into `spec.discover` of the rendered
`OperatorOps`. They take effect on the first installation only, because a finished run is not repeated on upgrade.

```yaml title="Example of values narrowing the first discovery run (values.yaml)"
discovery:
  name: production
  namespace: simplyblock-storage
  nodeSelector:
    node-role.kubernetes.io/simplyblock-storage: ""
  tolerations:
    - key: storage.simplyblock.io/dedicated
      operator: Equal
      value: "true"
      effect: NoSchedule
  deviceFilter:
    pcieDenyList:
      - "0000:00:1f.2"
    driveSizeRange: 1T-16T
```

The draft is named `discovered-production` and proposes the storage cluster `discovered-production-cluster`, so
`discovery.name` is limited to 18 characters. The namespace must exist. The tolerations are copied into the draft as
well, so the storage nodes tolerate the same taints. See
[Create a Storage Cluster](../../kubernetes/installation/k8s-storage-plane.md#discover-workers-and-devices).

### Managed Profile

A cluster without its own control plane registers its storage with a remote one. The Secrets named in the values hold
the bearer token and the CA certificate and are created in the release namespace beforehand.

```yaml title="Example of values for the managed profile (values.yaml)"
deployment:
  profile: managed
controlplane:
  managed:
    endpoint: https://cp.example.com
    credentialsSecretRef: cp-token
    caBundleSecretRef: cp-ca
    storageNodeImage: quay.io/simplyblock-io/simplyblock:26.4.0
prometheus:
  enabled: false
```

The `storageNodeImage` is the default image for storage clusters that do not set `spec.storageNodes.image`. A managed
cluster has no local control plane image to fall back to. Prometheus can be left out when the remote control plane
collects the metrics. See
[Connecting to an External Control Plane](../../kubernetes/installation/install-csi.md#installing-with-the-managed-profile).

### Operator Only

The `empty` profile installs the operator, its CRDs, and its webhooks, and nothing for it to act on. The `driver` and
`discovery` blocks are not read.

```yaml title="Example of values installing the operator only (values.yaml)"
deployment:
  profile: empty
```

### Transport Security

TLS is on by default and requires cert-manager or OpenShift. Mutual TLS is on by default as well, but its client
certificates are only issued by cert-manager. An existing cert-manager `ClusterIssuer` is used as shown in
[Securing the Control Plane](../../kubernetes/installation/security.md#enabling-mtls-with-an-existing-issuer).

With the `openshift` provider, the service CA of OpenShift issues the server certificates, and mutual TLS is turned
off. The values schema rejects the file otherwise.

```yaml title="Example of values for TLS on OpenShift (values.yaml)"
tls:
  enabled: true
  provider: openshift
  mutual_enabled: false
```

On a cluster with neither provider, TLS is turned off, and mutual TLS has to be turned off with it.

```yaml title="Example of values turning off TLS (values.yaml)"
tls:
  enabled: false
  mutual_enabled: false
```

### Observability and Alert Notifications

The observability stack is installed for the `standalone` profile. Graylog's retention is set when Graylog first starts
and is divided across its indices: 14 days over 7 indices rotates every 48 hours. A later change reaches only a new
installation.

```yaml title="Example of values enabling observability with Slack notifications (values.yaml)"
controlplane:
  storageclass:
    name: local-path
  observability:
    enabled: true
    graylog:
      retentionPeriod: 14d
      maxNumberIndex: "7"
    grafana:
      notifications:
        slack:
          enabled: true
          url: https://hooks.slack.com/services/T000/B000/XXXX
```

The notification credentials are rendered into a ConfigMap, so read access to the release namespace is read access to
them. Slack, Microsoft Teams, PagerDuty, Opsgenie, and a generic webhook are supported. See
[Alerts](../../kubernetes/operations/monitoring/alerts.md).

!!! warning
    The observability stack ships with default passwords (`controlplane.observability.secret`,
    `controlplane.observability.graylog.rootPasswordSha2`, and `controlplane.observability.graylog.passwordSecret`).
    They must be overridden in production.

### Control Center With an Ingress

The Control Center proxies the Kubernetes API with its own service account by default, so everyone who reaches it
shares its permissions. Authentication therefore belongs in front of the Ingress. The default Ingress annotations
enable NGINX basic authentication as a stop-gap. The NetworkPolicy restricts the console's egress, and its
`apiServerCidrs` are narrowed to the API server before it is enabled.

The basic authentication reads its users from the Secret `simplyblock-control-center-auth`, which is not created by
the chart. It is created in the release namespace beforehand, with an htpasswd file under the key `auth`. Without the
Secret, the Ingress answers every request with HTTP 503.

```bash title="Creating the basic authentication Secret for the Control Center Ingress"
htpasswd -c auth admin
kubectl create secret generic simplyblock-control-center-auth \
    --namespace simplyblock \
    --from-file=auth
```

```yaml title="Example of values exposing the Control Center (values.yaml)"
controlCenter:
  enabled: true
  image:
    tag: 26.4.0
  ingress:
    enabled: true
    className: nginx
    host: console.example.com
    tls:
      - hosts:
          - console.example.com
        secretName: console-tls
  networkPolicy:
    enabled: true
    apiServerCidrs:
      - 10.96.0.1/32
    ingressFromNamespaces:
      - ingress-nginx
```

The image tag is pinned, because an empty tag follows the chart's floating `appVersion`. See
[Control Center](../../disaster-recovery/control-center.md).

## Value Reference

The [Simplyblock Helm Chart Values](helm-values.md) reference lists every value of the chart, with its type, its
default, and a description. It is generated from the chart's `values.yaml`.
