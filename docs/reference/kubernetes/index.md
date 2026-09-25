---
title: "Simplyblock Helm Chart Reference"
description: "Reference of every value of the simplyblock-operator Helm chart, with its default and a short description, grouped by top-level key."
weight: 20100
---

The `simplyblock-operator` Helm chart installs the Simplyblock Operator, all simplyblock CRDs, the admission webhooks,
and the metrics API. It also renders two custom resources, `ControlPlane/simplyblock` and
`SimplyblockDriver/simplyblock`. From these, the operator installs the control plane (for the `standalone` profile)
and the CSI driver. Storage clusters are not configured through the chart. They are created afterward with a
`ClusterDeploymentConfig`.

This reference lists every value in the chart's `values.yaml`, with its default, grouped by top-level key. For the
installation procedure and the most commonly set values, see
[Install Simplyblock Operator](../../kubernetes/installation/k8s-control-plane.md).

An empty default means that the value is unset. Some blocks (`tls`, `driver`, and
`controlplane.observability.grafana.notifications`) are validated by the chart's values schema and reject unknown
keys. Values marked "Not read by the chart templates" are present in `values.yaml` but have no effect in this chart
version.

## Images

The `image` block sets the images of the workloads the chart renders directly. The CSI driver image is set with
`driver.image` instead.

!!! warning
    Overriding the pinned images can leave the deployment unusable. Change them only when requested by simplyblock.

| Value                                       | Default                                         | Description                                                                                                         |
|---------------------------------------------|-------------------------------------------------|---------------------------------------------------------------------------------------------------------------------|
| `image.simplyblock.repository`              | `quay.io/simplyblock-io/simplyblock`            | Control plane image, written to `ControlPlane.spec.source.local.image`. It is also the default storage node image.  |
| `image.simplyblock.tag`                     | `26.2.6-PRE`                                    | Control plane image tag.                                                                                            |
| `image.simplyblock.pullPolicy`              | `Always`                                        | Control plane image pull policy.                                                                                    |
| `image.operator.repository`                 | `quay.io/simplyblock-io/simplyblock-operator`   | Simplyblock Operator image.                                                                                         |
| `image.operator.tag`                        | `v26.2.6`                                       | Simplyblock Operator image tag.                                                                                     |
| `image.operator.pullPolicy`                 | `Always`                                        | Simplyblock Operator image pull policy.                                                                             |
| `image.rebalancer.repository`               | `quay.io/simplyblock-io/simplyblock-rebalancer` | Rebalancer image.                                                                                                   |
| `image.rebalancer.tag`                      | `""`                                            | Rebalancer image tag. Empty follows `image.operator.tag`, which keeps the rebalancer in lockstep with the operator. |
| `image.numaResource.repository`             | `quay.io/simplyblock-io/numa-resource-plugin`   | NUMA resource plugin image.                                                                                         |
| `image.numaResource.tag`                    | `latest`                                        | NUMA resource plugin image tag.                                                                                     |
| `image.numaResource.pullPolicy`             | `Always`                                        | NUMA resource plugin image pull policy.                                                                             |
| `image.csiSnapshotterController.repository` | `quay.io/simplyblock-io/snapshot-controller`    | CSI snapshot controller image, used when `snapshotcontroller.create` is `true`.                                     |
| `image.csiSnapshotterController.tag`        | `v8.2.0`                                        | CSI snapshot controller image tag.                                                                                  |
| `image.csiSnapshotterController.pullPolicy` | `Always`                                        | CSI snapshot controller image pull policy.                                                                          |
| `image.storageNode.repository`              | `quay.io/simplyblock-io/storage-node-handler`   | Storage node handler image. Not read by the chart templates.                                                        |
| `image.storageNode.tag`                     | `v0.1.9`                                        | Storage node handler image tag. Not read by the chart templates.                                                    |
| `image.storageNode.pullPolicy`              | `Always`                                        | Storage node handler image pull policy. Not read by the chart templates.                                            |

## Deployment Profile

The `deployment` block selects what the chart renders into `ControlPlane/simplyblock`.

| Value                | Default      | Description                                                                                                                                                                                                                                                                                               |
|----------------------|--------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `deployment.profile` | `standalone` | `standalone` hosts the control plane in this cluster (`spec.source.local`), and the operator installs FoundationDB, the object store, and the management API. `managed` registers the storage with a control plane elsewhere (`spec.source.managed`) and installs none. Any other value fails the render. |

## CSI Driver

The `driver` block is copied into `SimplyblockDriver/simplyblock`, from which the operator deploys the CSI node and
controller plugins, their RBAC, and the CSIDriver registration. An empty field takes the version shipped with the
operator release. The block rejects unknown keys.

| Value                                      | Default              | Description                                                                                                                                                 |
|--------------------------------------------|----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `driver.driverName`                        | `csi.simplyblock.io` | CSI driver name that StorageClasses provision with. Immutable once the `SimplyblockDriver` exists, and changing it orphans every existing PersistentVolume. |
| `driver.image.repository`                  | `""`                 | CSI plugin image repository. Empty uses the image shipped with the operator release. When set, `driver.image.tag` is required.                              |
| `driver.image.tag`                         | `""`                 | CSI plugin image tag.                                                                                                                                       |
| `driver.image.pullPolicy`                  | `Always`             | CSI plugin image pull policy (`Always`, `IfNotPresent`, or `Never`).                                                                                        |
| `driver.controllerReplicas`                | `1`                  | Number of CSI controller plugin instances. Minimum `1`.                                                                                                     |
| `driver.nodeSelector`                      | `{}`                 | Node selector for the CSI node plugin. Empty runs it on every schedulable worker.                                                                           |
| `driver.tolerations`                       | `[]`                 | Tolerations for the CSI node plugin.                                                                                                                        |
| `driver.controllerNodeSelector`            | `{}`                 | Node selector for the CSI controller plugin.                                                                                                                |
| `driver.controllerTolerations`             | `[]`                 | Tolerations for the CSI controller plugin.                                                                                                                  |
| `driver.enableVolumeSnapshots`             | `true`               | Deploys snapshot support for `driverName`: the VolumeSnapshotClass, and the snapshot CRDs and controller where the cluster serves neither.                  |
| `driver.enableServiceAccountAuth`          | `false`              | Authenticates both plugins to the management API with their pod service account token instead of the static cluster secret.                                 |
| `driver.sidecarImages.provisioner`         | `""`                 | Override for the CSI provisioner sidecar, as a full `repository:tag` reference from a simplyblock registry.                                                 |
| `driver.sidecarImages.attacher`            | `""`                 | Override for the CSI attacher sidecar.                                                                                                                      |
| `driver.sidecarImages.resizer`             | `""`                 | Override for the CSI resizer sidecar.                                                                                                                       |
| `driver.sidecarImages.snapshotter`         | `""`                 | Override for the CSI snapshotter sidecar.                                                                                                                   |
| `driver.sidecarImages.healthMonitor`       | `""`                 | Override for the CSI external health monitor sidecar.                                                                                                       |
| `driver.sidecarImages.nodeDriverRegistrar` | `""`                 | Override for the CSI node driver registrar sidecar.                                                                                                         |

## Control Plane

The `controlplane` block configures the control plane that `ControlPlane/simplyblock` describes, and the workloads the
chart renders around it.

| Value                                                                 | Default                                            | Description                                                                                                                                                                                  |
|-----------------------------------------------------------------------|----------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `controlplane.managed.endpoint`                                       | `""`                                               | Base URL of the remote management API. Required for `deployment.profile=managed`. Loopback and link-local addresses are rejected.                                                            |
| `controlplane.managed.credentialsSecretRef`                           | `""`                                               | Secret in the release namespace holding the bearer token under `token` or `secret`. Empty sends no token.                                                                                    |
| `controlplane.managed.caBundleSecretRef`                              | `""`                                               | Secret holding the CA the endpoint is verified against, under `ca.crt` or `tls.crt`. Empty uses the system trust store.                                                                      |
| `controlplane.trustCSIServiceAccounts`                                | `false`                                            | Accepts the service account tokens of the CSI driver instead of the static cluster secret. Meant to be set together with `driver.enableServiceAccountAuth`. Not read by the chart templates. |
| `controlplane.tolerations.create`                                     | `false`                                            | Adds the tolerations in `controlplane.tolerations.list` to the control plane, the operator, and the log collector.                                                                           |
| `controlplane.tolerations.list`                                       | (see `values.yaml`)                                | Toleration list (`operator`, `effect`, `key`, `value`).                                                                                                                                      |
| `controlplane.nodeSelector.create`                                    | `false`                                            | Pins the control plane, the operator, and the log collector to nodes carrying the label below.                                                                                               |
| `controlplane.nodeSelector.key`                                       |                                                    | Node label key.                                                                                                                                                                              |
| `controlplane.nodeSelector.value`                                     |                                                    | Node label value.                                                                                                                                                                            |
| `controlplane.storageclass.name`                                      |                                                    | StorageClass for the FoundationDB volumes and the observability database. Should not be a simplyblock StorageClass.                                                                          |
| `controlplane.storageclass.allowedTopologyZones`                      | `[]`                                               | Zones the `local-hostpath` StorageClass is restricted to.                                                                                                                                    |
| `controlplane.ports.lvolNvmfPortStart`                                | `9110`                                             | First NVMe-oF port for logical volumes. Not read by the chart templates.                                                                                                                     |
| `controlplane.foundationdb.redundancyMode`                            | `double`                                           | `double` runs 3 FoundationDB coordinators and tolerates one failure. `triple` runs 5 and tolerates two.                                                                                      |
| `controlplane.foundationdb.exporter.enabled`                          | `true`                                             | Adds the Prometheus scrape job and the Grafana dashboard for the FoundationDB exporter.                                                                                                      |
| `controlplane.foundationdb.enabled`                                   | `true`                                             | FoundationDB switch. The operator installs FoundationDB for the `standalone` profile regardless. Not read by the chart templates.                                                            |
| `controlplane.foundationdb.multiAZ`                                   | `false`                                            | Multi-zone FoundationDB layout. Not read by the chart templates.                                                                                                                             |
| `controlplane.foundationdb.nodeSelector`                              | `{}`                                               | Node selector for dedicated FoundationDB nodes. Not read by the chart templates.                                                                                                             |
| `controlplane.foundationdb.image.operator.repository`                 | `quay.io/simplyblock-io/fdb-kubernetes-operator`   | FoundationDB operator image. Not read by the chart templates.                                                                                                                                |
| `controlplane.foundationdb.image.operator.tag`                        | `v2.13.0`                                          | FoundationDB operator image tag. Not read by the chart templates.                                                                                                                            |
| `controlplane.foundationdb.image.monitor.repository`                  | `quay.io/simplyblock-io/fdb-kubernetes-monitor`    | FoundationDB monitor image. Not read by the chart templates.                                                                                                                                 |
| `controlplane.foundationdb.image.monitor.tag`                         | `7.3.63`                                           | FoundationDB monitor image tag. Not read by the chart templates.                                                                                                                             |
| `controlplane.foundationdb.image.mainContainer.baseImage`             | `quay.io/simplyblock-io/fdb-kubernetes-monitor`    | FoundationDB main container base image. Not read by the chart templates.                                                                                                                     |
| `controlplane.foundationdb.exporter.image.repository`                 | `aikoven/foundationdb-exporter`                    | FoundationDB exporter image. Not read by the chart templates.                                                                                                                                |
| `controlplane.foundationdb.exporter.image.tag`                        | `3.1.0`                                            | FoundationDB exporter image tag. Not read by the chart templates.                                                                                                                            |
| `controlplane.foundationdb.exporter.resources.requests.cpu`           | `50m`                                              | FoundationDB exporter CPU request. Not read by the chart templates.                                                                                                                          |
| `controlplane.foundationdb.exporter.resources.requests.memory`        | `64Mi`                                             | FoundationDB exporter memory request. Not read by the chart templates.                                                                                                                       |
| `controlplane.foundationdb.exporter.resources.limits.cpu`             | `200m`                                             | FoundationDB exporter CPU limit. Not read by the chart templates.                                                                                                                            |
| `controlplane.foundationdb.exporter.resources.limits.memory`          | `128Mi`                                            | FoundationDB exporter memory limit. Not read by the chart templates.                                                                                                                         |
| `controlplane.csiHostpathDriver.enabled`                              | `false`                                            | Installs the CSI hostpath driver and its `local-hostpath` StorageClass, for example, to back the control plane volumes on a cluster without other storage.                                   |
| `controlplane.csiHostpathDriver.image.csiProvisioner.repository`      | `quay.io/simplyblock-io/csi-provisioner`           | CSI provisioner image of the hostpath driver.                                                                                                                                                |
| `controlplane.csiHostpathDriver.image.csiProvisioner.tag`             | `v6.0.0`                                           | CSI provisioner image tag.                                                                                                                                                                   |
| `controlplane.csiHostpathDriver.image.csiResizer.repository`          | `quay.io/simplyblock-io/csi-resizer`               | CSI resizer image of the hostpath driver.                                                                                                                                                    |
| `controlplane.csiHostpathDriver.image.csiResizer.tag`                 | `v2.0.0`                                           | CSI resizer image tag.                                                                                                                                                                       |
| `controlplane.csiHostpathDriver.image.nodeDriverRegistrar.repository` | `quay.io/simplyblock-io/csi-node-driver-registrar` | CSI node driver registrar image of the hostpath driver.                                                                                                                                      |
| `controlplane.csiHostpathDriver.image.nodeDriverRegistrar.tag`        | `v2.12.0`                                          | CSI node driver registrar image tag.                                                                                                                                                         |
| `controlplane.csiHostpathDriver.image.hostpathPlugin.repository`      | `quay.io/simplyblock-io/hostpathplugin`            | Hostpath plugin image.                                                                                                                                                                       |
| `controlplane.csiHostpathDriver.image.hostpathPlugin.tag`             | `v1.15.0`                                          | Hostpath plugin image tag.                                                                                                                                                                   |
| `controlplane.csiHostpathDriver.image.livenessProbe.repository`       | `quay.io/simplyblock-io/livenessprobe`             | Liveness probe image of the hostpath driver.                                                                                                                                                 |
| `controlplane.csiHostpathDriver.image.livenessProbe.tag`              | `v2.15.0`                                          | Liveness probe image tag.                                                                                                                                                                    |

## Observability

The `controlplane.observability` block installs the optional logging, metrics, and dashboard stack (Graylog, OpenSearch,
MongoDB, Grafana, Thanos, and Fluent Bit). It is intended for the `standalone` profile.

| Value                                                 | Default                               | Description                                                                                                                                              |
|-------------------------------------------------------|---------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|
| `controlplane.observability.enabled`                  | `false`                               | Installs the observability stack, including the MongoDB and OpenSearch subcharts.                                                                        |
| `controlplane.observability.secret`                   | `sWbpOgba1bKnCfcPkVQi`                | Password of the observability stack (Grafana admin, Graylog MongoDB user). Must be overridden in production.                                             |
| `controlplane.observability.logParser`                | `cri`                                 | Fluent Bit parser for container logs. `cri` is correct for containerd and CRI-O. `docker` is only for dockershim clusters (Kubernetes 1.23 and earlier). |
| `controlplane.observability.deletionInterval`         | `3d`                                  | Retention interval of collected data. Not read by the chart templates.                                                                                   |
| `controlplane.observability.level`                    | `DEBUG`                               | Log level. Not read by the chart templates.                                                                                                              |
| `controlplane.observability.graylog.repository`       | `quay.io/simplyblock-io/graylog`      | Graylog image.                                                                                                                                           |
| `controlplane.observability.graylog.tag`              | `5.0`                                 | Graylog image tag.                                                                                                                                       |
| `controlplane.observability.graylog.rootPasswordSha2` | (shipped default, see `values.yaml`)  | SHA-256 hash of the Graylog root password. Must be overridden in production.                                                                             |
| `controlplane.observability.graylog.passwordSecret`   | (shipped default, see `values.yaml`)  | Graylog password secret (pepper). Must be overridden in production.                                                                                      |
| `controlplane.observability.graylog.maxNumberIndex`   | `3`                                   | Maximum number of Graylog indices kept.                                                                                                                  |
| `controlplane.observability.grafana.repository`       | `quay.io/simplyblock-io/grafana`      | Grafana image.                                                                                                                                           |
| `controlplane.observability.grafana.tag`              | `10.0.12`                             | Grafana image tag.                                                                                                                                       |
| `controlplane.observability.grafana.endpoint`         | `""`                                  | External Grafana endpoint reported to the control plane.                                                                                                 |
| `controlplane.observability.thanos.repository`        | `quay.io/simplyblock-io/thanos`       | Thanos image.                                                                                                                                            |
| `controlplane.observability.thanos.tag`               | `v0.31.0`                             | Thanos image tag.                                                                                                                                        |
| `controlplane.observability.fluentbit.repository`     | `quay.io/simplyblock-io/fluent-bit`   | Fluent Bit image.                                                                                                                                        |
| `controlplane.observability.fluentbit.tag`            | `1.8.11`                              | Fluent Bit image tag.                                                                                                                                    |
| `controlplane.observability.fluentbit.pullPolicy`     | `IfNotPresent`                        | Fluent Bit image pull policy.                                                                                                                            |
| `controlplane.observability.minio.repository`         | `quay.io/simplyblock-io/minio`        | MinIO image. Not read by the chart templates.                                                                                                            |
| `controlplane.observability.minio.tag`                | `RELEASE.2024-01-16T16-07-38Z`        | MinIO image tag. Not read by the chart templates.                                                                                                        |
| `controlplane.observability.minio.pullPolicy`         | `IfNotPresent`                        | MinIO image pull policy. Not read by the chart templates.                                                                                                |
| `controlplane.observability.minio.mcRepository`       | `quay.io/simplyblock-io/minio-client` | MinIO client image. Not read by the chart templates.                                                                                                     |
| `controlplane.observability.minio.mcTag`              | `RELEASE.2024-01-16T16-06-34Z`        | MinIO client image tag. Not read by the chart templates.                                                                                                 |
| `controlplane.observability.minio.bucket`             | `thanos`                              | Object store bucket for Thanos. Not read by the chart templates.                                                                                         |
| `controlplane.observability.minio.accessKey`          | `minioadmin`                          | MinIO access key. Not read by the chart templates.                                                                                                       |
| `controlplane.observability.minio.secretKey`          | `minioadmin`                          | MinIO secret key. Not read by the chart templates.                                                                                                       |
| `controlplane.observability.minio.storageSize`        | `50Gi`                                | MinIO volume size. Not read by the chart templates.                                                                                                      |
| `controlplane.observability.minio.storageClass`       |                                       | MinIO StorageClass. Not read by the chart templates.                                                                                                     |

## Alert Notifications

The `controlplane.observability.grafana.notifications` block provisions receivers into the `grafana-alerts` contact
point. Every enabled channel is notified for every simplyblock alert. With none enabled, no contact point and no
notification policy are provisioned. The credentials are rendered into the `simplyblock-grafana-alerting` ConfigMap, so
read access to the release namespace is read access to them. The block rejects unknown keys.

| Value                                                                               | Default                              | Description                                                                                     |
|-------------------------------------------------------------------------------------|--------------------------------------|-------------------------------------------------------------------------------------------------|
| `controlplane.observability.grafana.notifications.slack.enabled`                    | `false`                              | Enables the Slack receiver.                                                                     |
| `controlplane.observability.grafana.notifications.slack.url`                        | `""`                                 | Incoming webhook URL of the Slack channel.                                                      |
| `controlplane.observability.grafana.notifications.teams.enabled`                    | `false`                              | Enables the Microsoft Teams receiver.                                                           |
| `controlplane.observability.grafana.notifications.teams.url`                        | `""`                                 | Incoming webhook or workflow URL.                                                               |
| `controlplane.observability.grafana.notifications.pagerduty.enabled`                | `false`                              | Enables the PagerDuty receiver.                                                                 |
| `controlplane.observability.grafana.notifications.pagerduty.integrationKey`         | `""`                                 | Integration key of an Events API v2 service.                                                    |
| `controlplane.observability.grafana.notifications.pagerduty.severity`               | `critical`                           | Event severity: `info`, `warning`, `error`, or `critical`.                                      |
| `controlplane.observability.grafana.notifications.pagerduty.class`                  | `""`                                 | Optional event class. Accepts a Grafana notification template.                                  |
| `controlplane.observability.grafana.notifications.pagerduty.component`              | `""`                                 | Optional event component. Accepts a Grafana notification template.                              |
| `controlplane.observability.grafana.notifications.pagerduty.group`                  | `""`                                 | Optional event group. Accepts a Grafana notification template.                                  |
| `controlplane.observability.grafana.notifications.opsgenie.enabled`                 | `false`                              | Enables the Opsgenie receiver.                                                                  |
| `controlplane.observability.grafana.notifications.opsgenie.apiKey`                  | `""`                                 | Opsgenie API key.                                                                               |
| `controlplane.observability.grafana.notifications.opsgenie.apiUrl`                  | `https://api.opsgenie.com/v2/alerts` | Opsgenie alerts API. EU accounts use `https://api.eu.opsgenie.com/v2/alerts`.                   |
| `controlplane.observability.grafana.notifications.opsgenie.autoClose`               | `true`                               | Closes the Opsgenie alert when the Grafana alert resolves.                                      |
| `controlplane.observability.grafana.notifications.opsgenie.overridePriority`        | `false`                              | Derives the Opsgenie priority from an `og_priority` alert label.                                |
| `controlplane.observability.grafana.notifications.opsgenie.sendTagsAs`              | `tags`                               | How alert labels are carried over: `tags`, `details`, or `both`.                                |
| `controlplane.observability.grafana.notifications.webhook.enabled`                  | `false`                              | Enables the generic webhook receiver, which is sent the Grafana alert JSON payload unmodified.  |
| `controlplane.observability.grafana.notifications.webhook.url`                      | `""`                                 | Webhook URL.                                                                                    |
| `controlplane.observability.grafana.notifications.webhook.httpMethod`               | `POST`                               | `POST` or `PUT`.                                                                                |
| `controlplane.observability.grafana.notifications.webhook.username`                 | `""`                                 | Basic authentication user name. Basic authentication is omitted when empty.                     |
| `controlplane.observability.grafana.notifications.webhook.password`                 | `""`                                 | Basic authentication password.                                                                  |
| `controlplane.observability.grafana.notifications.webhook.authorizationScheme`      | `""`                                 | Authorization header scheme (for example, `Bearer`), as an alternative to basic authentication. |
| `controlplane.observability.grafana.notifications.webhook.authorizationCredentials` | `""`                                 | Authorization header credentials.                                                               |
| `controlplane.observability.grafana.notifications.webhook.maxAlerts`                | `0`                                  | Maximum number of alerts per notification. `0` sends all of them.                               |

## Transport Security

The `tls` block is copied into the `tls` blocks of `ControlPlane/simplyblock` and `SimplyblockDriver/simplyblock`. The
block rejects unknown keys. See [Securing the Control Plane](../../kubernetes/installation/security.md).

| Value                                     | Default        | Description                                                                                                                                                                         |
|-------------------------------------------|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `tls.enabled`                             | `true`         | Encrypts control plane traffic with TLS. The render fails when the selected provider is unavailable, so a cluster with neither cert-manager nor OpenShift sets this to `false`.     |
| `tls.provider`                            | `cert-manager` | Certificate provider: `cert-manager` or `openshift`.                                                                                                                                |
| `tls.mutual_enabled`                      | `true`         | Requires client certificates (mutual TLS) and issues them for the operator, the CSI plugins, Prometheus, and the FoundationDB peers. Only allowed with `tls.provider=cert-manager`. |
| `tls.cert-manager.createSelfSignedIssuer` | `true`         | Creates a self-signed ClusterIssuer named by `cluster-issuer`. `false` uses an existing issuer.                                                                                     |
| `tls.cert-manager.cluster-issuer`         | `selfsigned`   | ClusterIssuer the chart mints its CA certificate from.                                                                                                                              |
| `tls.cert-manager.namespace`              | `cert-manager` | Namespace cert-manager runs in. The chart places its CA Secret there so the ClusterIssuer can read it.                                                                              |

## CSI Link

The `csiLink` block configures the endpoint the CSI node and controller pods dial on the operator, so the operator can
query node storage state.

| Value                 | Default                | Description                                                                                                                                     |
|-----------------------|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| `csiLink.port`        | `9500`                 | Port the operator listens on, and the port of its Service.                                                                                      |
| `csiLink.certSecret`  | `""`                   | Secret with the serving certificate of the link (`tls.crt`, `tls.key`), whose SANs must cover `serviceName`. Empty serves the link without TLS. |
| `csiLink.serviceName` | `simplyblock-csi-link` | Service name the CSI pods dial and verify the certificate against.                                                                              |
| `csiLink.audience`    | `simplyblock-csi-link` | Audience of the projected service account tokens the CSI pods present.                                                                          |

## Metrics API

The `metricsAPI` block configures the aggregated API `metrics.simplyblock.io/v1alpha2`, which serves
`LogicalVolumeMetrics` (`kubectl get lvm`) and `StorageDeviceMetrics` (`kubectl get sdm`).

| Value                      | Default                              | Description                                                                                                     |
|----------------------------|--------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| `metricsAPI.enabled`       | `true`                               | Serves the metrics API. `false` removes the APIService, its Service, and the delegated authentication bindings. |
| `metricsAPI.port`          | `6443`                               | Container port the Kubernetes API server is proxied to.                                                         |
| `metricsAPI.prometheusURL` | `http://simplyblock-prometheus:9090` | Prometheus the capacity samples are read from. Empty serves provisioned sizes only.                             |

## Volume Migration

The `volumeMigration` block selects the kind volume moves are raised with.

| Value                    | Default | Description                                                                                                                                           |
|--------------------------|---------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| `volumeMigration.legacy` | `false` | Re-enables the legacy `VolumeMigration` kind instead of `PersistentVolumeOps`. Only needed while migrations raised against it drain after an upgrade. |

## CSI Credentials

The `externallyManagedSecret`, `csiConfig`, `csiSecret`, and `multiCluster` values render the
`simplyblock-csi-secret-v2` Secret with cluster credentials for the CSI driver. The operator maintains the credentials
of the clusters it creates, so these values are only needed for clusters it does not create.

| Value                            | Default             | Description                                                                                                                                                          |
|----------------------------------|---------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `externallyManagedSecret.create` | `true`              | Renders the Secret. The template tests the `externallyManagedSecret` block itself, so the Secret is rendered whenever the block is present, regardless of this flag. |
| `csiConfig.simplybk.uuid`        |                     | UUID of the simplyblock cluster. The Secret carries credentials only when this and `csiSecret.simplybk.secret` are set.                                              |
| `csiConfig.simplybk.ip`          |                     | Management API endpoint. Empty uses the in-cluster `simplyblock-webappapi` service.                                                                                  |
| `csiSecret.simplybk.secret`      |                     | Cluster secret.                                                                                                                                                      |
| `multiCluster.enable`            | `false`             | Writes one entry per item in `multiCluster.clusters` instead of the single cluster above.                                                                            |
| `multiCluster.clusters`          | (see `values.yaml`) | List of `cluster_id`, `secret`, and `workers`. `cluster_id` and `secret` are required per entry.                                                                     |

## Snapshots, RBAC, and Annotations

These top-level values toggle supporting resources.

| Value                       | Default | Description                                                                                                               |
|-----------------------------|---------|---------------------------------------------------------------------------------------------------------------------------|
| `snapshotcontroller.create` | `true`  | Installs the CSI snapshot controller, its RBAC, and the volume group snapshot CRDs where the cluster does not serve them. |
| `rbac.create`               | `true`  | Creates the service account and RBAC of the node probe jobs.                                                              |
| `serviceAccount.create`     | `true`  | Service account switch. Not read by the chart templates.                                                                  |
| `podAnnotations`            | `{}`    | Annotations for all pods. Not read by the chart templates.                                                                |
| `simplyBlockAnnotations`    | `{}`    | Annotations for simplyblock DaemonSets, Deployments, and StatefulSets. Not read by the chart templates.                   |
| `operator.openShiftCluster` | `true`  | OpenShift switch. Not read by the chart templates.                                                                        |

## Prometheus

The `prometheus` block is passed to the upstream `prometheus` chart (version 25.18.0). The instance stores the metrics
the control plane pushes and ships them to Thanos. Values not listed here take the upstream defaults.

| Value                                                    | Default                                             | Description                                                                                                        |
|----------------------------------------------------------|-----------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| `prometheus.enabled`                                     | `true`                                              | Installs the Prometheus subchart. A `managed` deployment that reports to its remote control plane can turn it off. |
| `prometheus.simplyblock.prometheusURL`                   | `simplyblock-prometheus`                            | Prometheus service name. Not read by the chart templates.                                                          |
| `prometheus.simplyblock.prometheusPORT`                  | `9090`                                              | Prometheus service port. Not read by the chart templates.                                                          |
| `prometheus.server.image.repository`                     | `quay.io/simplyblock-io/prometheus`                 | Prometheus image.                                                                                                  |
| `prometheus.server.image.tag`                            | `v2.51.0`                                           | Prometheus image tag.                                                                                              |
| `prometheus.server.fullnameOverride`                     | `simplyblock-prometheus`                            | Name of the Prometheus server resources.                                                                           |
| `prometheus.server.name`                                 | `simplyblock-prometheus`                            | Prometheus server name.                                                                                            |
| `prometheus.server.enabled`                              | `true`                                              | Deploys the Prometheus server.                                                                                     |
| `prometheus.server.statefulSet.enabled`                  | `true`                                              | Runs the server as a StatefulSet.                                                                                  |
| `prometheus.server.replicaCount`                         | `1`                                                 | Number of Prometheus replicas.                                                                                     |
| `prometheus.server.nodeSelector`                         | `{}`                                                | Node selector for the Prometheus server.                                                                           |
| `prometheus.server.tolerations`                          | `[]`                                                | Tolerations for the Prometheus server.                                                                             |
| `prometheus.server.affinity`                             | (see `values.yaml`)                                 | Pod anti-affinity that spreads replicas across hosts.                                                              |
| `prometheus.server.podLabels`                            | (see `values.yaml`)                                 | Pod labels of the Prometheus server.                                                                               |
| `prometheus.server.podAnnotations`                       | (see `values.yaml`)                                 | Pod annotations (log collection and Reloader triggers).                                                            |
| `prometheus.server.service.servicePort`                  | `9090`                                              | Service port.                                                                                                      |
| `prometheus.server.service.type`                         | `ClusterIP`                                         | Service type.                                                                                                      |
| `prometheus.server.service.gRPC.enabled`                 | `true`                                              | Exposes the Thanos sidecar gRPC port on the Service.                                                               |
| `prometheus.server.service.gRPC.servicePort`             | `10901`                                             | gRPC service port.                                                                                                 |
| `prometheus.server.service.additionalPorts`              | (see `values.yaml`)                                 | Additional Service ports (Thanos HTTP on `10902`).                                                                 |
| `prometheus.server.securityContext.fsGroup`              | `65534`                                             | File system group of the server pod.                                                                               |
| `prometheus.server.persistentVolume.enabled`             | `true`                                              | Stores the time series on a persistent volume.                                                                     |
| `prometheus.server.persistentVolume.size`                | `20Gi`                                              | Size of the Prometheus volume.                                                                                     |
| `prometheus.server.persistentVolume.storageClass`        |                                                     | StorageClass of the Prometheus volume. Empty uses the cluster default.                                             |
| `prometheus.server.extraArgs`                            | (see `values.yaml`)                                 | TSDB block durations (`2h`), as required by the Thanos sidecar.                                                    |
| `prometheus.server.sidecarContainers`                    | (see `values.yaml`)                                 | Thanos sidecar container that uploads blocks to the object store.                                                  |
| `prometheus.server.resources.requests.cpu`               | `100m`                                              | Prometheus CPU request.                                                                                            |
| `prometheus.server.resources.requests.memory`            | `512Mi`                                             | Prometheus memory request.                                                                                         |
| `prometheus.server.resources.limits.cpu`                 | `500m`                                              | Prometheus CPU limit.                                                                                              |
| `prometheus.server.resources.limits.memory`              | `1Gi`                                               | Prometheus memory limit.                                                                                           |
| `prometheus.server.configPath`                           | `/etc/simplyblock-config/prometheus.yml`            | Path of the simplyblock Prometheus configuration.                                                                  |
| `prometheus.server.extraVolumes`                         | (see `values.yaml`)                                 | Volumes for the Prometheus configuration, the object store configuration, and the TLS client and CA certificates.  |
| `prometheus.server.extraVolumeMounts`                    | (see `values.yaml`)                                 | Mounts of the volumes above.                                                                                       |
| `prometheus.alertmanager.enabled`                        | `false`                                             | Deploys Alertmanager.                                                                                              |
| `prometheus.prometheus-pushgateway.enabled`              | `false`                                             | Deploys the Pushgateway.                                                                                           |
| `prometheus.prometheus-node-exporter.enabled`            | `false`                                             | Deploys the node exporter.                                                                                         |
| `prometheus.kube-state-metrics.enabled`                  | `false`                                             | Deploys kube-state-metrics.                                                                                        |
| `prometheus.configmapReload.prometheus.image.repository` | `quay.io/simplyblock-io/prometheus-config-reloader` | Configuration reloader image.                                                                                      |
| `prometheus.configmapReload.prometheus.image.tag`        | `v0.72.0`                                           | Configuration reloader image tag.                                                                                  |
| `prometheus.defaultBackend.enabled`                      | `false`                                             | Deploys the default backend.                                                                                       |
| `prometheus.defaultBackend.name`                         | `defaultbackend`                                    | Default backend name.                                                                                              |
| `prometheus.defaultBackend.image.registry`               | `quay.io/simplyblock-io`                            | Default backend image registry.                                                                                    |
| `prometheus.defaultBackend.image.image`                  | `defaultbackend-amd64`                              | Default backend image.                                                                                             |
| `prometheus.defaultBackend.image.tag`                    | `1.5`                                               | Default backend image tag.                                                                                         |

## Reloader

The `reloader` block is passed to the upstream Stakater `reloader` chart (version 1.3.0).

| Value                                       | Default                           | Description                                                                                                                                         |
|---------------------------------------------|-----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| `reloader.enabled`                          | `true`                            | Rolls the workloads mounting the FoundationDB cluster file when the coordinators move. With `false`, they pick up the change on their next restart. |
| `reloader.nameOverride`                     | `simplyblock-reloader`            | Name override.                                                                                                                                      |
| `reloader.fullnameOverride`                 | `simplyblock-reloader`            | Full name override.                                                                                                                                 |
| `reloader.reloader.deployment.image.name`   | `quay.io/simplyblock-io/reloader` | Reloader image.                                                                                                                                     |
| `reloader.reloader.deployment.image.tag`    | `v1.3.0`                          | Reloader image tag.                                                                                                                                 |
| `reloader.reloader.deployment.nodeSelector` | `{}`                              | Node selector for Reloader.                                                                                                                         |
| `reloader.reloader.deployment.tolerations`  | `[]`                              | Tolerations for Reloader.                                                                                                                           |

## MongoDB

The `mongodb-kubernetes` block is passed to the upstream `mongodb-kubernetes` chart (version 1.4.0), which is installed
with `controlplane.observability.enabled` and runs the Graylog database.

| Value                                            | Default                  | Description                                          |
|--------------------------------------------------|--------------------------|------------------------------------------------------|
| `mongodb-kubernetes.name`                        | `simplyblock-mongodb`    | Name of the MongoDB operator.                        |
| `mongodb-kubernetes.deployment_name`             | `simplyblock-mongodb`    | Deployment name of the MongoDB operator.             |
| `mongodb-kubernetes.resources.requests.cpu`      | `100m`                   | CPU request.                                         |
| `mongodb-kubernetes.resources.requests.memory`   | `300Mi`                  | Memory request.                                      |
| `mongodb-kubernetes.resources.limits.cpu`        | `250m`                   | CPU limit.                                           |
| `mongodb-kubernetes.resources.limits.memory`     | `1Gi`                    | Memory limit.                                        |
| `mongodb-kubernetes.community.mongodb.repo`      | `quay.io/simplyblock-io` | MongoDB image repository.                            |
| `mongodb-kubernetes.community.mongodb.imageType` | `ubi8`                   | MongoDB image type.                                  |
| `mongodb-kubernetes.community.agent.name`        | `mongodb-agent`          | MongoDB agent image name.                            |
| `mongodb-kubernetes.community.agent.version`     | `108.0.2.8729-1`         | MongoDB agent version.                               |
| `mongodb-kubernetes.community.registry.agent`    | `quay.io/simplyblock-io` | MongoDB agent registry.                              |
| `mongodb-kubernetes.registry.operator`           | `quay.io/simplyblock-io` | Operator image registry.                             |
| `mongodb-kubernetes.registry.agent`              | `quay.io/simplyblock-io` | Agent image registry.                                |
| `mongodb-kubernetes.registry.readinessProbe`     | `quay.io/simplyblock-io` | Readiness probe image registry.                      |
| `mongodb-kubernetes.registry.versionUpgradeHook` | `quay.io/simplyblock-io` | Version upgrade hook image registry.                 |
| `mongodb-kubernetes.nodeSelector`                | `{}`                     | Node selector.                                       |
| `mongodb-kubernetes.tolerations`                 | `[]`                     | Tolerations.                                         |
| `mongodb-kubernetes.affinity`                    | (see `values.yaml`)      | Pod anti-affinity that spreads members across hosts. |

## OpenSearch

The `opensearch` block is passed to the upstream `opensearch` chart (version 2.9.0), which is installed with
`controlplane.observability.enabled` and stores the Graylog log data.

| Value                                  | Default                             | Description                                                                                |
|----------------------------------------|-------------------------------------|--------------------------------------------------------------------------------------------|
| `opensearch.fullnameOverride`          | `simplyblock-opensearch`            | Name of the OpenSearch resources.                                                          |
| `opensearch.singleNode`                | `true`                              | Runs OpenSearch as a single node.                                                          |
| `opensearch.replicas`                  | `1`                                 | Number of OpenSearch replicas.                                                             |
| `opensearch.nodeSelector`              | `{}`                                | Node selector.                                                                             |
| `opensearch.tolerations`               | `[]`                                | Tolerations.                                                                               |
| `opensearch.antiAffinity`              | `hard`                              | Pod anti-affinity mode.                                                                    |
| `opensearch.persistence.enabled`       | `true`                              | Stores the data on a persistent volume.                                                    |
| `opensearch.persistence.image`         | `quay.io/simplyblock-io/busybox`    | Image of the volume permission init container.                                             |
| `opensearch.persistence.storageClass`  |                                     | StorageClass of the data volume. Empty uses the cluster default.                           |
| `opensearch.persistence.size`          | `40Gi`                              | Size of the data volume.                                                                   |
| `opensearch.image.repository`          | `quay.io/simplyblock-io/opensearch` | OpenSearch image.                                                                          |
| `opensearch.image.tag`                 | `""`                                | OpenSearch image tag. Empty uses the chart app version.                                    |
| `opensearch.resources.requests.cpu`    | `100m`                              | CPU request.                                                                               |
| `opensearch.resources.requests.memory` | `512Mi`                             | Memory request.                                                                            |
| `opensearch.resources.limits.cpu`      | `500m`                              | CPU limit.                                                                                 |
| `opensearch.resources.limits.memory`   | `3Gi`                               | Memory limit.                                                                              |
| `opensearch.extraEnvs`                 | (see `values.yaml`)                 | Environment settings (memory lock, no automatic index creation, security plugin disabled). |
| `opensearch.securityConfig.enabled`    | `false`                             | Enables the OpenSearch security configuration.                                             |
