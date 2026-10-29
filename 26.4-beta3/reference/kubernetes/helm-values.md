---
title: "Simplyblock Helm Chart Values"
description: "Generated reference of every value of the simplyblock-operator Helm chart, with its type and default, grouped by top-level key."
source: "https://docs.simplyblock.io/latest/reference/kubernetes/helm-values/"
---

# Simplyblock Helm Chart Values

<!--
This file is generated. Do not edit it by hand.
Run scripts/helm-reference-gen.sh from the documentation repository.
-->

This page lists every value of the `simplyblock-operator` Helm chart, version `26.3.0`, as it appears in
the chart's `values.yaml`. What the chart renders, and example values files for common deployments, are described in
[Simplyblock Helm Chart](index.md).


## Images

The `image` block sets the images of the workloads the chart renders directly. The CSI driver image is set with
`driver.image` instead.

!!! warning
    Overriding the pinned images can leave the deployment unusable. Change them only when requested by simplyblock.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `image.csiSnapshotterController.repository` | string | `"quay.io/simplyblock-io/snapshot-controller"` | CSI snapshot controller image, used when `snapshotcontroller.create` is `true`. |
| `image.csiSnapshotterController.tag` | string | `"v8.2.0"` | CSI snapshot controller image tag. |
| `image.csiSnapshotterController.pullPolicy` | string | `"Always"` | CSI snapshot controller image pull policy. One of `Always`, `IfNotPresent`, or `Never`. |
| `image.csiAddonsController.repository` | string | `"quay.io/csiaddons/k8s-controller"` | CSI-Addons controller image, used when `csiaddons.create` is `true`. |
| `image.csiAddonsController.tag` | string | `"v0.15.0"` | CSI-Addons controller image tag. |
| `image.csiAddonsController.pullPolicy` | string | `"Always"` | CSI-Addons controller image pull policy. One of `Always`, `IfNotPresent`, or `Never`. |
| `image.simplyblock.repository` | string | `"quay.io/simplyblock-io/simplyblock"` | Control plane image, written to `ControlPlane.spec.source.local.image`. It is also the default storage node image. |
| `image.simplyblock.tag` | string | `"main"` | Control plane image tag. |
| `image.simplyblock.pullPolicy` | string | `"Always"` | Control plane image pull policy. One of `Always`, `IfNotPresent`, or `Never`. |
| `image.operator.repository` | string | `"quay.io/simplyblock-io/simplyblock-operator"` | Simplyblock Operator image. |
| `image.operator.tag` | string | `"main"` | Simplyblock Operator image tag. |
| `image.operator.pullPolicy` | string | `"Always"` | Simplyblock Operator image pull policy. One of `Always`, `IfNotPresent`, or `Never`. |
| `image.rebalancer.repository` | string | `""` | Rebalancer image repository. Empty runs the rebalancer from the operator's registry, which keeps the two in lockstep. |
| `image.rebalancer.tag` | string | `""` | Rebalancer image tag. Empty uses `image.operator.tag`. |
| `image.numaResource.repository` | string | `"quay.io/simplyblock-io/numa-resource-plugin"` | NUMA resource plugin image. |
| `image.numaResource.tag` | string | `"latest"` | NUMA resource plugin image tag. |
| `image.numaResource.pullPolicy` | string | `"Always"` | NUMA resource plugin image pull policy. One of `Always`, `IfNotPresent`, or `Never`. |

## Supporting Resources

These top-level values toggle the supporting resources the chart installs next to the operator: the CSI snapshot
controller, the CSI-Addons controller, and their CRDs where the cluster does not serve them yet.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `rbac.create` | bool | `true` | RBAC switch. Not read by the chart templates. |
| `snapshotcontroller.create` | bool | `true` | Installs the CSI snapshot controller, its RBAC, and the volume group snapshot CRDs where the cluster does not serve them. |
| `csiaddons.create` | bool | `false` | Installs the CSI-Addons CRDs (`VolumeReplication` and related kinds) and the CSI-Addons controller. |

## CSI Credentials

The `externallyManagedSecret`, `csiConfig`, `csiSecret`, and `multiCluster` values render the
`simplyblock-csi-secret-v2` Secret with cluster credentials for the CSI driver. The credentials of the clusters the
operator creates are maintained by the operator, so these values are only needed for clusters it does not create. A
pool named in `csiConfig` or `multiCluster` also gets a block StorageClass, because no `StoragePool` exists for such a
cluster to write one.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `externallyManagedSecret.create` | bool | `true` | Renders the Secret. The Secret is rendered whenever the `externallyManagedSecret` block is present, regardless of this flag. |
| `csiConfig.simplybk.uuid` | string | `nil` | UUID of the simplyblock cluster. The Secret carries credentials only when this and `csiSecret.simplybk.secret` are set. |
| `csiConfig.simplybk.ip` | string | `nil` | Management API endpoint. Empty uses the in-cluster `simplyblock-webappapi` service. |
| `csiConfig.simplybk.pool` | string | `nil` | Storage pool the volumes on this cluster are created in. When set, the chart renders a block StorageClass for the cluster and pool. |
| `csiConfig.simplybk.storageClassName` | string | `nil` | Name of the StorageClass rendered for `csiConfig.simplybk.pool`. Empty uses `simplyblock-<pool>`. |
| `csiSecret.simplybk.secret` | string | `nil` | Cluster secret. |
| `multiCluster.enable` | bool | `false` | Writes one entry per item in `multiCluster.clusters` instead of the single cluster above. |
| `multiCluster.clusters` | list | (see `values.yaml`) | Storage clusters the CSI driver connects to, when `multiCluster.enable` is `true`. Each entry has `cluster_id`, `secret`, `workers`, `pool`, and `storageClassName`, with the same meaning as the matching `csiConfig` and `csiSecret` values. |

## Deployment Profile

The `deployment` block selects which of the control plane, the CSI driver, and the first discovery run the chart
renders. See [Deployment Profiles](index.md#deployment-profiles).

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `deployment.profile` | string | `"standalone"` | Selects what the chart renders. `standalone` hosts the control plane in this cluster, and FoundationDB, the object store, and the management API are installed by the operator. `managed` registers the storage with a control plane elsewhere, named by `controlplane.managed`, and installs none. `empty` installs only the operator, its CRDs, and its webhooks. The `ControlPlane` and `SimplyblockDriver` are then written by hand. One of `standalone`, `managed`, or `empty`. |

## Discovery

The `discovery` block configures the first discovery run, rendered for the `standalone` profile as an `OperatorOps`
with the `Discover` action. The run inspects the workers and writes a `ClusterDeploymentConfig` in `Draft`. Nothing is
deployed until the draft is approved. A finished run is not repeated on upgrade, so a changed value has no effect after
the first installation. See
[Narrowing the First Discovery Run](index.md#narrowing-the-first-discovery-run).

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `discovery.enabled` | bool | `true` | Renders an `OperatorOps` with the `Discover` action on a fresh `standalone` install. The run inspects the workers and writes a `ClusterDeploymentConfig` in `Draft`. Nothing is deployed until the draft is approved. A finished run is not repeated on upgrade, so another run needs a new `OperatorOps`. With `false`, the `ClusterDeploymentConfig` is written by hand. |
| `discovery.name` | string | `"initial-discovery"` | Name of the discovery run, at most 18 characters. The draft is named `discovered-<name>`, and its storage cluster `discovered-<name>-cluster`. |
| `discovery.namespace` | string | `""` | Namespace of the discovery run and the draft. Approving the draft builds the storage cluster in the same namespace. The namespace must exist. Empty uses the release namespace. |
| `discovery.nodeSelector` | object | `{}` | Labels selecting the workers the discovery run inspects. All entries must match. Empty inspects every schedulable worker. |
| `discovery.tolerations` | list | `[]` | Tolerations of the discovery probe pods. They are copied into the draft, so the storage nodes tolerate the same taints. |
| `discovery.enableControlPlaneNodes` | bool | `false` | Lets the discovery run inspect Kubernetes control plane nodes. Required on a single-node cluster. |
| `discovery.enableLogicalBlockDevices` | bool | `false` | Scans logical block devices instead of NVMe devices. A cluster uses one class of device, so this selects the class rather than adding one. |
| `discovery.enablePartitionedDevices` | bool | `true` | Reports devices that carry a partition table. Devices that are mounted, in use, or carry swap stay excluded. |
| `discovery.forceJournalDevice` | bool | `false` | Dedicates one of several equal-sized disks as the journal device. Without it, an NVMe cluster carves journal partitions out of every device, and a discovery run over logical block devices fails. The draft notes which disk was taken. |
| `discovery.networkAttachment.management` | string | `""` | NetworkAttachmentDefinition, in the discovery namespace, that the storage nodes' management traffic is attached through. Empty keeps host networking. Alone, it carries data traffic as well. |
| `discovery.networkAttachment.data` | string | `""` | NetworkAttachmentDefinition, in the discovery namespace, that the storage nodes' data traffic is attached through. Requires `management`. |
| `discovery.deviceFilter.blockAllowList` | list | `[]` | Block devices to include, such as `/dev/nvme0n1`. Requires `discovery.enableLogicalBlockDevices`. An allow list that matches nothing produces an empty draft. |
| `discovery.deviceFilter.blockDenyList` | list | `[]` | Block devices to exclude, such as the boot disk `/dev/sda`. Requires `discovery.enableLogicalBlockDevices`. |
| `discovery.deviceFilter.pcieAllowList` | list | `[]` | NVMe devices to include, by PCI address. |
| `discovery.deviceFilter.pcieDenyList` | list | `[]` | NVMe devices to exclude, by PCI address. |
| `discovery.deviceFilter.pcieModel` | string | `""` | Includes only NVMe devices whose PCI model string matches. |
| `discovery.deviceFilter.driveSizeRange` | string | `""` | Size range a device must fall in, for example, `1T-16T`. Applies to either device class. |
| `discovery.draft` | object | (see `values.yaml`) | Not used. Accepted so that values files of earlier releases still install. Edit the draft before approving it instead. |

## CSI Driver

The `driver` block is copied into `SimplyblockDriver/simplyblock`. From it, the CSI node and controller plugins, their
RBAC, and the CSIDriver registration are deployed by the operator. An empty field takes the version shipped with the
operator release.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `driver.driverName` | string | `"csi.simplyblock.io"` | CSI driver name that StorageClasses provision with. Immutable once the `SimplyblockDriver` exists, and changing it orphans every existing PersistentVolume. |
| `driver.image.repository` | string | `""` | CSI plugin image repository. Empty uses the image shipped with the operator release. When set, `driver.image.tag` is required. |
| `driver.image.tag` | string | `""` | CSI plugin image tag. |
| `driver.image.pullPolicy` | string | `"Always"` | CSI plugin image pull policy. One of `Always`, `Never`, or `IfNotPresent`. |
| `driver.controllerReplicas` | int | `1` | Number of CSI controller plugin instances. Minimum `1`. |
| `driver.nodeSelector` | object | `{}` | Node selector for the CSI node plugin. Empty runs it on every schedulable worker. |
| `driver.tolerations` | list | `[]` | Tolerations for the CSI node plugin. |
| `driver.controllerNodeSelector` | object | `{}` | Node selector for the CSI controller plugin. |
| `driver.controllerTolerations` | list | `[]` | Tolerations for the CSI controller plugin. |
| `driver.enableVolumeSnapshots` | bool | `true` | Deploys snapshot support for `driverName`: the VolumeSnapshotClass, and the snapshot CRDs and controller where the cluster serves neither. |
| `driver.enableServiceAccountAuth` | bool | `false` | Authenticates both plugins to the management API with their pod service account token instead of the static cluster secret. |
| `driver.sidecarImages.provisioner` | string | `""` | Override for the CSI provisioner sidecar, as a full `repository:tag` reference from a simplyblock registry. |
| `driver.sidecarImages.attacher` | string | `""` | Override for the CSI attacher sidecar. |
| `driver.sidecarImages.resizer` | string | `""` | Override for the CSI resizer sidecar. |
| `driver.sidecarImages.snapshotter` | string | `""` | Override for the CSI snapshotter sidecar. |
| `driver.sidecarImages.healthMonitor` | string | `""` | Override for the CSI external health monitor sidecar. |
| `driver.sidecarImages.nodeDriverRegistrar` | string | `""` | Override for the CSI node driver registrar sidecar. |
| `driver.sidecarImages.csiAddons` | string | `""` | CSI-Addons sidecar image. |

## pNFS Metadata Server

The `driver.pnfs` block configures the pNFS metadata server, which serves ReadWriteMany volumes. One metadata server
pod runs per storage cluster, on a node with `/dev/kvm`. See [pNFS Volumes](../../kubernetes/usage/pnfs.md).

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `driver.pnfs.mds.enabled` | bool | `true` | Runs the pNFS metadata server, one pod per storage cluster, which serves ReadWriteMany volumes. It requires a node with `/dev/kvm`. With `false`, pNFS volumes stay `Pending`. |
| `driver.pnfs.mds.nodeSelector` | object | `{}` | Node selector of the metadata server, merged with the KVM-capable label the pod always requires. |
| `driver.pnfs.mds.tolerations` | list | `[]` | Tolerations of the metadata server. |
| `driver.pnfs.mds.resources` | object | `{}` | Resource requests and limits of the metadata server. Empty uses limits of 2 CPUs and 2Gi of memory. |
| `driver.pnfs.mds.stateSize` | string | `""` | Size of the metadata server's state disk, which holds the NFS client recovery database. Empty uses `1Gi`. |
| `driver.pnfs.mds.dataNetwork.subnet` | string | `""` | Storage data network subnet the metadata server is attached to, through a Multus macvlan. Set together with `rangeStart` and `rangeEnd`. Empty uses the pod network. |
| `driver.pnfs.mds.dataNetwork.rangeStart` | string | `""` | First address the metadata server may use on the storage data network. The range must not overlap with other addresses in use. |
| `driver.pnfs.mds.dataNetwork.rangeEnd` | string | `""` | Last address the metadata server may use on the storage data network. |

## Control Plane

The `controlplane` block configures the control plane that `ControlPlane/simplyblock` describes, and the placement of
the workloads the chart renders around it. The `local` values apply to the `standalone` profile, the `managed` values
to the `managed` profile.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `controlplane.local.adminTokenSecretRef` | string | `""` | Secret holding a static admin bearer token, under `token`, that this control plane accepts. A remote cluster with the `managed` profile names the same token in `controlplane.managed.credentialsSecretRef`. Empty grants no additional credential. |
| `controlplane.managed.endpoint` | string | `""` | Base URL of the remote management API. Required for `deployment.profile=managed`. Loopback and link-local addresses are rejected. |
| `controlplane.managed.credentialsSecretRef` | string | `""` | Secret in the release namespace holding the bearer token under `token` or `secret`. Empty sends no token. |
| `controlplane.managed.caBundleSecretRef` | string | `""` | Secret holding the CA the endpoint is verified against, under `ca.crt` or `tls.crt`. Empty uses the system trust store. |
| `controlplane.managed.storageNodeImage` | string | `""` | Default storage node image for storage clusters whose `spec.storageNodes.image` is unset. Required in practice for the `managed` profile. |
| `controlplane.tolerations.create` | bool | `false` | Adds the tolerations in `controlplane.tolerations.list` to the control plane, the operator, and the log collector. |
| `controlplane.tolerations.list` | list | (see `values.yaml`) | Tolerations of the control plane pods, when `controlplane.tolerations.create` is `true`. |
| `controlplane.nodeSelector.create` | bool | `false` | Pins the control plane, the operator, and the log collector to nodes carrying the label below. |
| `controlplane.nodeSelector.key` | string | `nil` | Node label key. |
| `controlplane.nodeSelector.value` | string | `nil` | Node label value. |
| `controlplane.storageclass.name` | string | `nil` | StorageClass for the FoundationDB volumes and the observability database. Should not be a simplyblock StorageClass. |

## Observability

The `controlplane.observability` block installs the optional logging, metrics, and dashboard stack: Graylog, Grafana,
Thanos, Fluent Bit, and the MongoDB and OpenSearch subcharts. It is intended for the `standalone` profile. See
[Observability and Alert Notifications](index.md#observability-and-alert-notifications).

!!! warning
    The observability stack ships with default passwords. They must be overridden in production.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `controlplane.observability.enabled` | bool | `false` | Installs the observability stack, including the MongoDB and OpenSearch subcharts. |
| `controlplane.observability.secret` | string | (shipped default, see `values.yaml`) | Password of the observability stack (Grafana admin, Graylog MongoDB user). Must be overridden in production. |
| `controlplane.observability.mongodb.installCRDs` | bool | `true` | Installs the `MongoDBCommunity` CRD that Graylog requires. Turn it off only when the CRD is installed separately. |
| `controlplane.observability.logParser` | string | `"cri"` | Fluent Bit parser for container logs. `cri` is correct for containerd and CRI-O. `docker` is only for dockershim clusters (Kubernetes 1.23 and earlier). One of `cri` or `docker`. |
| `controlplane.observability.graylog.repository` | string | `"quay.io/simplyblock-io/graylog"` | Graylog image. |
| `controlplane.observability.graylog.tag` | string | `"5.0"` | Graylog image tag. |
| `controlplane.observability.graylog.pullPolicy` | string | `"Always"` | Graylog image pull policy. One of `Always`, `IfNotPresent`, or `Never`. |
| `controlplane.observability.graylog.rootPasswordSha2` | string | (shipped default, see `values.yaml`) | SHA-256 hash of the Graylog root password. Must be overridden in production. |
| `controlplane.observability.graylog.passwordSecret` | string | (shipped default, see `values.yaml`) | Graylog password secret (pepper). Must be overridden in production. |
| `controlplane.observability.graylog.maxNumberIndex` | string | `"3"` | Number of Graylog indices kept. The oldest is deleted when a new one starts. Applies only when Graylog first starts. |
| `controlplane.observability.graylog.retentionPeriod` | string | `"7d"` | How long Graylog keeps logs, as a count followed by `h`, `d`, or `w`. The period is divided across `maxNumberIndex` indices: `7d` over 3 indices rotates every 56 hours. Applies only when Graylog first starts. A later change reaches only a new installation. |
| `controlplane.observability.grafana.repository` | string | `"quay.io/simplyblock-io/grafana"` | Grafana image. |
| `controlplane.observability.grafana.tag` | string | `"10.0.12"` | Grafana image tag. |
| `controlplane.observability.grafana.pullPolicy` | string | `"IfNotPresent"` | Grafana image pull policy. One of `Always`, `IfNotPresent`, or `Never`. |
| `controlplane.observability.grafana.endpoint` | string | `""` | External Grafana endpoint reported to the control plane. |
| `controlplane.observability.thanos.repository` | string | `"quay.io/simplyblock-io/thanos"` | Thanos image. |
| `controlplane.observability.thanos.tag` | string | `"v0.31.0"` | Thanos image tag. |
| `controlplane.observability.thanos.pullPolicy` | string | `"IfNotPresent"` | Thanos image pull policy. One of `Always`, `IfNotPresent`, or `Never`. |
| `controlplane.observability.fluentbit.repository` | string | `"quay.io/simplyblock-io/fluent-bit"` | Fluent Bit image. |
| `controlplane.observability.fluentbit.tag` | string | `"1.8.11"` | Fluent Bit image tag. |
| `controlplane.observability.fluentbit.pullPolicy` | string | `"IfNotPresent"` | Fluent Bit image pull policy. One of `Always`, `IfNotPresent`, or `Never`. |

## Alert Notifications

The `controlplane.observability.grafana.notifications` block provisions receivers into the `grafana-alerts` contact
point. Every enabled channel is notified for every simplyblock alert. With none enabled, no contact point and no
notification policy are provisioned. The credentials are rendered into the `simplyblock-grafana-alerting` ConfigMap, so
read access to the release namespace is read access to them.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `controlplane.observability.grafana.notifications.slack.enabled` | bool | `false` | Enables the Slack receiver. |
| `controlplane.observability.grafana.notifications.slack.url` | string | `""` | Incoming webhook URL of the Slack channel. |
| `controlplane.observability.grafana.notifications.teams.enabled` | bool | `false` | Enables the Microsoft Teams receiver. |
| `controlplane.observability.grafana.notifications.teams.url` | string | `""` | Incoming webhook or workflow URL. |
| `controlplane.observability.grafana.notifications.pagerduty.enabled` | bool | `false` | Enables the PagerDuty receiver. |
| `controlplane.observability.grafana.notifications.pagerduty.integrationKey` | string | `""` | Integration key of an Events API v2 service. |
| `controlplane.observability.grafana.notifications.pagerduty.severity` | string | `"critical"` | Event severity. One of `info`, `warning`, `error`, or `critical`. |
| `controlplane.observability.grafana.notifications.pagerduty.class` | string | `""` | Optional event class. Accepts a Grafana notification template. |
| `controlplane.observability.grafana.notifications.pagerduty.component` | string | `""` | Optional event component. Accepts a Grafana notification template. |
| `controlplane.observability.grafana.notifications.pagerduty.group` | string | `""` | Optional event group. Accepts a Grafana notification template. |
| `controlplane.observability.grafana.notifications.opsgenie.enabled` | bool | `false` | Enables the Opsgenie receiver. |
| `controlplane.observability.grafana.notifications.opsgenie.apiKey` | string | `""` | Opsgenie API key. |
| `controlplane.observability.grafana.notifications.opsgenie.apiUrl` | string | `"https://api.opsgenie.com/v2/alerts"` | Opsgenie alerts API. EU accounts use `https://api.eu.opsgenie.com/v2/alerts`. |
| `controlplane.observability.grafana.notifications.opsgenie.autoClose` | bool | `true` | Closes the Opsgenie alert when the Grafana alert resolves. |
| `controlplane.observability.grafana.notifications.opsgenie.overridePriority` | bool | `false` | Derives the Opsgenie priority from an `og_priority` alert label. |
| `controlplane.observability.grafana.notifications.opsgenie.sendTagsAs` | string | `"tags"` | How alert labels are carried over to Opsgenie. One of `tags`, `details`, or `both`. |
| `controlplane.observability.grafana.notifications.webhook.enabled` | bool | `false` | Enables the generic webhook receiver, which is sent the Grafana alert JSON payload unmodified. |
| `controlplane.observability.grafana.notifications.webhook.url` | string | `""` | Webhook URL. |
| `controlplane.observability.grafana.notifications.webhook.httpMethod` | string | `"POST"` | HTTP method of the webhook request. One of `POST` or `PUT`. |
| `controlplane.observability.grafana.notifications.webhook.username` | string | `""` | Basic authentication user name. Basic authentication is omitted when empty. |
| `controlplane.observability.grafana.notifications.webhook.password` | string | `""` | Basic authentication password. |
| `controlplane.observability.grafana.notifications.webhook.authorizationScheme` | string | `""` | Authorization header scheme (for example, `Bearer`), as an alternative to basic authentication. |
| `controlplane.observability.grafana.notifications.webhook.authorizationCredentials` | string | `""` | Authorization header credentials. |
| `controlplane.observability.grafana.notifications.webhook.maxAlerts` | int | `0` | Maximum number of alerts per notification. `0` sends all of them. |

## FoundationDB

The `controlplane.foundationdb` block configures the FoundationDB cluster that stores the control plane state of the
`standalone` profile. See [Dedicated Control Plane Nodes](index.md#dedicated-control-plane-nodes).

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `controlplane.foundationdb.installCRDs` | bool | `true` | Installs the FoundationDB CRDs. Turn it off only when the CRDs are installed separately. |
| `controlplane.foundationdb.redundancyMode` | string | `"double"` | `double` runs 3 FoundationDB coordinators and tolerates one failure. `triple` runs 5 and tolerates two. One of `double` or `triple`. |
| `controlplane.foundationdb.nodeSelector` | object | `{}` | Workers the FoundationDB processes run on. Confining them to a few workers lets the other workers be added in parallel during expansion. Select at least three workers for `double` and five for `triple`. Empty places them with the rest of the control plane. |
| `controlplane.foundationdb.tolerations` | list | `[]` | Tolerations of the FoundationDB processes. When set, they replace `controlplane.tolerations` for FoundationDB. Empty uses `controlplane.tolerations`. |
| `controlplane.foundationdb.exporter.enabled` | bool | `true` | Adds the Prometheus scrape job and the Grafana dashboard for the FoundationDB exporter. |

## Volume Migration

The `volumeMigration` block selects the kind volume moves are raised with. Volume moves are raised when the
rebalancer moves a volume off a busy node, when a node is drained, and when a claim is pinned to another node.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `volumeMigration.legacy` | bool | `false` | Re-enables the legacy `VolumeMigration` kind instead of `PersistentVolumeOps`. Only needed while migrations raised against it drain after an upgrade. |

## CSI Link

The `csiLink` block configures the endpoint the CSI node and controller pods dial on the operator. Through it, the
operator queries the storage state of a node without anything listening on the node.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `csiLink.port` | int | `9500` | Port the operator listens on, and the port of its Service. |
| `csiLink.certSecret` | string | `""` | Secret with a serving certificate (`tls.crt`, `tls.key`) used instead of the one the chart issues. Its SANs must cover `serviceName`, and it must be signed by the CA the CSI pods mount. Requires `tls.enabled`. Empty uses the issued certificate. With TLS disabled, the link is plaintext. |
| `csiLink.serviceName` | string | `"simplyblock-csi-link"` | Service name the CSI pods dial and verify the certificate against. |
| `csiLink.audience` | string | `"simplyblock-csi-link"` | Audience of the projected service account tokens the CSI pods present. |

## Metrics API

The `metricsAPI` block configures the aggregated API `metrics.simplyblock.io/v1alpha2`. It serves capacity readings of
storage clusters, storage nodes, storage pools, storage devices, and logical volumes, computed on demand and never
stored. See [Capacity Metrics API](../../kubernetes/operations/monitoring/index.md#capacity-metrics-api).

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `metricsAPI.enabled` | bool | `true` | Serves the metrics API. `false` removes the APIService, its Service, and the delegated authentication bindings. |
| `metricsAPI.port` | int | `6443` | Container port the Kubernetes API server is proxied to. |
| `metricsAPI.prometheusURL` | string | `"http://simplyblock-prometheus:9090"` | Prometheus the capacity samples are read from. Empty serves provisioned sizes only. |

## MongoDB

The `mongodb-kubernetes` block is passed to the upstream `mongodb-kubernetes` chart, which is installed with
`controlplane.observability.enabled` and runs the Graylog database.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `mongodb-kubernetes.name` | string | `"simplyblock-mongodb"` | Name of the MongoDB operator. |
| `mongodb-kubernetes.deployment_name` | string | `"simplyblock-mongodb"` | Deployment name of the MongoDB operator. |
| `mongodb-kubernetes.resources.requests.cpu` | string | `"100m"` | CPU request. |
| `mongodb-kubernetes.resources.requests.memory` | string | `"300Mi"` | Memory request. |
| `mongodb-kubernetes.resources.limits.cpu` | string | `"250m"` | CPU limit. |
| `mongodb-kubernetes.resources.limits.memory` | string | `"1Gi"` | Memory limit. |
| `mongodb-kubernetes.community.mongodb.repo` | string | `"quay.io/simplyblock-io"` | MongoDB image repository. |
| `mongodb-kubernetes.community.mongodb.imageType` | string | `"ubi8"` | MongoDB image type. |
| `mongodb-kubernetes.community.agent.name` | string | `"mongodb-agent"` | MongoDB agent image name. |
| `mongodb-kubernetes.community.agent.version` | string | `"108.0.2.8729-1"` | MongoDB agent version. |
| `mongodb-kubernetes.community.registry.agent` | string | `"quay.io/simplyblock-io"` | MongoDB agent registry. |
| `mongodb-kubernetes.registry.operator` | string | `"quay.io/simplyblock-io"` | Operator image registry. |
| `mongodb-kubernetes.registry.agent` | string | `"quay.io/simplyblock-io"` | Agent image registry. |
| `mongodb-kubernetes.registry.readinessProbe` | string | `"quay.io/simplyblock-io"` | Readiness probe image registry. |
| `mongodb-kubernetes.registry.versionUpgradeHook` | string | `"quay.io/simplyblock-io"` | Version upgrade hook image registry. |
| `mongodb-kubernetes.nodeSelector` | object | `{}` | Node selector. |
| `mongodb-kubernetes.tolerations` | list | `[]` | Tolerations. |
| `mongodb-kubernetes.affinity` | object | (see `values.yaml`) | Affinity of the MongoDB pods. The default spreads them across nodes. |

## OpenSearch

The `opensearch` block is passed to the upstream `opensearch` chart, which is installed with
`controlplane.observability.enabled` and stores the Graylog log data.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `opensearch.fullnameOverride` | string | `"simplyblock-opensearch"` | Name of the OpenSearch resources. |
| `opensearch.singleNode` | bool | `true` | Runs OpenSearch as a single node. |
| `opensearch.replicas` | int | `1` | Number of OpenSearch replicas. |
| `opensearch.nodeSelector` | object | `{}` | Node selector. |
| `opensearch.tolerations` | list | `[]` | Tolerations. |
| `opensearch.antiAffinity` | string | `"hard"` | Pod anti-affinity mode. |
| `opensearch.persistence.enabled` | bool | `true` | Stores the data on a persistent volume. |
| `opensearch.persistence.image` | string | `"quay.io/simplyblock-io/busybox"` | Image of the volume permission init container. |
| `opensearch.persistence.storageClass` | string | `nil` | StorageClass of the data volume. Empty uses the cluster default. |
| `opensearch.persistence.size` | string | `"40Gi"` | Size of the data volume. |
| `opensearch.image.repository` | string | `"quay.io/simplyblock-io/opensearch"` | OpenSearch image. |
| `opensearch.image.tag` | string | `""` | OpenSearch image tag. Empty uses the chart app version. |
| `opensearch.resources.requests.cpu` | string | `"100m"` | CPU request. |
| `opensearch.resources.requests.memory` | string | `"512Mi"` | Memory request. |
| `opensearch.resources.limits.cpu` | string | `"500m"` | CPU limit. |
| `opensearch.resources.limits.memory` | string | `"3Gi"` | Memory limit. |
| `opensearch.extraEnvs` | list | (see `values.yaml`) | Additional OpenSearch environment variables. The defaults lock memory, disable automatic index creation, and turn off the OpenSearch security plugin. |
| `opensearch.securityConfig.enabled` | bool | `false` | Enables the OpenSearch security configuration. |

## Reloader

The `reloader` block is passed to the upstream Stakater `reloader` chart. Reloader rolls the workloads that mount the
FoundationDB cluster file when the coordinators move.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `reloader.enabled` | bool | `true` | Rolls the workloads mounting the FoundationDB cluster file when the coordinators move. With `false`, they pick up the change on their next restart. |
| `reloader.nameOverride` | string | `"simplyblock-reloader"` | Name override. |
| `reloader.fullnameOverride` | string | `"simplyblock-reloader"` | Full name override. |
| `reloader.reloader.deployment.image.name` | string | `"quay.io/simplyblock-io/reloader"` | Reloader image. |
| `reloader.reloader.deployment.image.tag` | string | `"v1.3.0"` | Reloader image tag. |
| `reloader.reloader.deployment.pod.annotations` | object | `{"log-collector/enabled":"true"}` | Reloader pod annotations. The default ships the pod logs to Graylog. |
| `reloader.reloader.deployment.nodeSelector` | object | `{}` | Node selector for Reloader. |
| `reloader.reloader.deployment.tolerations` | list | `[]` | Tolerations for Reloader. |

## Prometheus

The `prometheus` block is passed to the upstream `prometheus` chart. The instance stores the metrics the control plane
pushes and ships them to Thanos. Values not listed here take the upstream defaults.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `prometheus.enabled` | bool | `true` | Installs the Prometheus subchart. A `managed` deployment that reports to its remote control plane can turn it off. |
| `prometheus.simplyblock.prometheusURL` | string | `"simplyblock-prometheus"` | Prometheus service name the Control Center queries when `controlCenter.prometheusUrl` is empty. |
| `prometheus.simplyblock.prometheusPORT` | int | `9090` | Prometheus service port the Control Center queries when `controlCenter.prometheusUrl` is empty. |
| `prometheus.server.image.repository` | string | `"quay.io/simplyblock-io/prometheus"` | Prometheus image. |
| `prometheus.server.image.tag` | string | `"v2.51.0"` | Prometheus image tag. |
| `prometheus.server.fullnameOverride` | string | `"simplyblock-prometheus"` | Name of the Prometheus server resources. |
| `prometheus.server.enabled` | bool | `true` | Deploys the Prometheus server. |
| `prometheus.server.statefulSet.enabled` | bool | `true` | Runs the server as a StatefulSet. |
| `prometheus.server.name` | string | `"simplyblock-prometheus"` | Prometheus server name. |
| `prometheus.server.replicaCount` | int | `1` | Number of Prometheus replicas. |
| `prometheus.server.podLabels` | object | `{"app":"simplyblock-prometheus"}` | Prometheus pod labels. |
| `prometheus.server.podAnnotations` | object | (see `values.yaml`) | Prometheus pod annotations, for log collection and Reloader triggers. |
| `prometheus.server.nodeSelector` | object | `{}` | Node selector for the Prometheus server. |
| `prometheus.server.tolerations` | list | `[]` | Tolerations for the Prometheus server. |
| `prometheus.server.affinity` | object | (see `values.yaml`) | Affinity of the Prometheus pods. The default spreads them across nodes. |
| `prometheus.server.service.servicePort` | int | `9090` | Service port. |
| `prometheus.server.service.type` | string | `"ClusterIP"` | Service type. |
| `prometheus.server.service.gRPC.enabled` | bool | `true` | Exposes the Thanos sidecar gRPC port on the Service. |
| `prometheus.server.service.gRPC.servicePort` | int | `10901` | gRPC service port. |
| `prometheus.server.service.additionalPorts` | list | (see `values.yaml`) | Additional Service ports. The default exposes the Thanos sidecar HTTP port `10902`. |
| `prometheus.server.securityContext.fsGroup` | int | `65534` | File system group of the server pod. |
| `prometheus.server.persistentVolume.enabled` | bool | `true` | Stores the time series on a persistent volume. |
| `prometheus.server.persistentVolume.size` | string | `"20Gi"` | Size of the Prometheus volume. |
| `prometheus.server.persistentVolume.storageClass` | string | `nil` | StorageClass of the Prometheus volume. Empty uses the cluster default. |
| `prometheus.server.extraArgs` | object | (see `values.yaml`) | Additional Prometheus arguments. The default sets a 2-hour block duration for the Thanos sidecar. |
| `prometheus.server.sidecarContainers` | object | (see `values.yaml`) | Sidecar containers of the Prometheus pod. The default runs the Thanos sidecar, which uploads blocks to the object store. |
| `prometheus.server.resources.requests.cpu` | string | `"100m"` | Prometheus CPU request. |
| `prometheus.server.resources.requests.memory` | string | `"512Mi"` | Prometheus memory request. |
| `prometheus.server.resources.limits.cpu` | string | `"500m"` | Prometheus CPU limit. |
| `prometheus.server.resources.limits.memory` | string | `"1Gi"` | Prometheus memory limit. |
| `prometheus.server.configPath` | string | `"/etc/simplyblock-config/prometheus.yml"` | Path of the simplyblock Prometheus configuration. |
| `prometheus.server.extraVolumes` | list | (see `values.yaml`) | Additional volumes of the Prometheus pod: the scrape configuration, the object store configuration, and the TLS client certificate and CA. |
| `prometheus.server.extraVolumeMounts` | list | (see `values.yaml`) | Mounts of `prometheus.server.extraVolumes`. |
| `prometheus.alertmanager.enabled` | bool | `false` | Deploys Alertmanager. |
| `prometheus.prometheus-pushgateway.enabled` | bool | `false` | Deploys the Pushgateway. |
| `prometheus.prometheus-node-exporter.enabled` | bool | `false` | Deploys the node exporter. |
| `prometheus.kube-state-metrics.enabled` | bool | `false` | Deploys kube-state-metrics. |
| `prometheus.configmapReload.prometheus.image.repository` | string | `"quay.io/simplyblock-io/prometheus-config-reloader"` | Configuration reloader image. |
| `prometheus.configmapReload.prometheus.image.tag` | string | `"v0.72.0"` | Configuration reloader image tag. |
| `prometheus.defaultBackend.enabled` | bool | `false` | Deploys the default backend. |
| `prometheus.defaultBackend.name` | string | `"defaultbackend"` | Default backend name. |
| `prometheus.defaultBackend.image.registry` | string | `"quay.io/simplyblock-io"` | Default backend image registry. |
| `prometheus.defaultBackend.image.image` | string | `"defaultbackend-amd64"` | Default backend image. |
| `prometheus.defaultBackend.image.tag` | string | `"1.5"` | Default backend image tag. |

## Control Center

The `controlCenter` block deploys the Control Center web console. The console proxies the Kubernetes API, so
authentication has to be put in front of it before it is exposed. See
[Control Center With an Ingress](index.md#control-center-with-an-ingress).

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `controlCenter.enabled` | bool | `false` | Deploys the Control Center web console. It proxies the Kubernetes API, so put authentication in front of it before exposing it. |
| `controlCenter.nameOverride` | string | `""` | Overrides the name part of the Control Center objects. |
| `controlCenter.fullnameOverride` | string | `""` | Overrides the full name of the Control Center objects. Empty uses `<release>-control-center`. |
| `controlCenter.image.registry` | string | `""` | Control Center image registry. Empty uses `quay.io`. |
| `controlCenter.image.repository` | string | `"simplyblock-io/control-center"` | Control Center image repository. |
| `controlCenter.image.tag` | string | `""` | Control Center image tag. Empty uses the chart's `appVersion`. Pin a released tag in production. |
| `controlCenter.image.pullPolicy` | string | `"IfNotPresent"` | Control Center image pull policy. One of `Always`, `IfNotPresent`, or `Never`. |
| `controlCenter.imagePullSecrets` | list | `[]` | Image pull secrets of the Control Center pods. |
| `controlCenter.replicas` | int | `2` | Number of Control Center replicas. |
| `controlCenter.mode` | string | `"full"` | `full` runs the storage console, including the disaster recovery section. `dr` runs the disaster recovery console only. One of `full` or `dr`. |
| `controlCenter.drNamespace` | string | `"ramen-ops"` | Ramen operations namespace on the disaster recovery hub. |
| `controlCenter.drHubNamespace` | string | `"dr-simplyblock"` | Namespace of the disaster recovery hub release. |
| `controlCenter.authMode` | string | `"serviceaccount"` | `serviceaccount` proxies requests with the console's own service account, so everyone who reaches the console shares its permissions. `passthrough` passes on the user's bearer token, so each user's own RBAC applies. It requires an authentication proxy that injects the token. One of `serviceaccount` or `passthrough`. |
| `controlCenter.tokenRefreshSeconds` | int | `600` | Interval, in seconds, at which the service account token is reread. |
| `controlCenter.kubernetesApi` | string | `"https://kubernetes.default.svc"` | Kubernetes API server URL. |
| `controlCenter.kubernetesApiHost` | string | `"kubernetes.default.svc"` | Host name presented to the Kubernetes API server. It must be on the server certificate. Change it together with `kubernetesApi`. |
| `controlCenter.kubernetesApiCaFile` | string | `"/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"` | CA file the Kubernetes API server is verified against. |
| `controlCenter.operatorUrl` | string | `""` | Simplyblock Operator API URL. Empty uses the operator of this release. |
| `controlCenter.helmUrl` | string | `""` | Helm API URL. Empty uses the default of this release. |
| `controlCenter.prometheusUrl` | string | `""` | Prometheus URL. Empty uses the Prometheus of this release. |
| `controlCenter.controlPlane.enabled` | bool | `true` | Gives the console read-only access to the control plane API. |
| `controlCenter.controlPlane.url` | string | `""` | Control plane API URL. Empty uses the management API of this release for the `standalone` profile. |
| `controlCenter.controlPlane.trustServiceAccount` | bool | `true` | Adds the console's service account to the control plane admin accounts, in `serviceaccount` mode. |
| `controlCenter.controlPlane.tokenSecret` | string | `""` | Secret holding a static control plane admin token, under `token`. It takes precedence over `trustServiceAccount`. |
| `controlCenter.logStore.enabled` | bool | `true` | Lets the Logs view search Graylog. Without it, the view shows a pod's live log. |
| `controlCenter.logStore.url` | string | `""` | Graylog URL. Empty uses the Graylog of this release when observability is enabled. |
| `controlCenter.logStore.user` | string | `"admin"` | Graylog user name. |
| `controlCenter.logStore.passwordSecret` | string | `""` | Secret holding the Graylog password. Empty uses the observability stack's own secret. |
| `controlCenter.logStore.passwordKey` | string | `""` | Key of the password in `passwordSecret`. |
| `controlCenter.logStore.tokenSecret` | string | `""` | Secret holding a Graylog access token, under `token`. It takes precedence over the password. |
| `controlCenter.rbac.create` | bool | `true` | Creates the console's RBAC rules. Required in `serviceaccount` mode. Set it to `false` only with `passthrough`. |
| `controlCenter.rbac.hubLabelling` | bool | `false` | Lets the console label StorageClasses, nodes, PersistentVolumeClaims, and workloads of the hub for disaster recovery. This grants `patch` on those kinds. |
| `controlCenter.service.type` | string | `"ClusterIP"` | Service type of the console. |
| `controlCenter.service.port` | int | `80` | Service port of the console. |
| `controlCenter.ingress.enabled` | bool | `false` | Creates an Ingress for the console. |
| `controlCenter.ingress.className` | string | `"nginx"` | Ingress class name. |
| `controlCenter.ingress.host` | string | `""` | Host name of the Ingress. |
| `controlCenter.ingress.annotations` | object | (see `values.yaml`) | Ingress annotations. The default enables NGINX basic authentication. Replace it with the annotations of an OIDC or OAuth2 proxy. |
| `controlCenter.ingress.tls` | list | `[]` | TLS configuration of the Ingress. |
| `controlCenter.networkPolicy.enabled` | bool | `false` | Restricts the console's egress to its upstreams and DNS. Narrow `apiServerCidrs` before enabling it. |
| `controlCenter.networkPolicy.apiServerCidrs` | list | `["10.0.0.0/8","172.16.0.0/12","192.168.0.0/16"]` | CIDRs of the Kubernetes API server. The defaults cover all private ranges. |
| `controlCenter.networkPolicy.ingressFromNamespaces` | list | `[]` | Namespaces allowed to reach the console, in addition to the release namespace, such as the Ingress controller's namespace. |
| `controlCenter.mock` | object | (see `values.yaml`) | Runs the console against a simulated cluster, for UI tests and demos only. Never enable it in production. |
| `controlCenter.resources` | object | (see `values.yaml`) | Resource requests and limits of the console. |
| `controlCenter.nodeSelector` | object | `{}` | Node selector of the console. |
| `controlCenter.tolerations` | list | `[]` | Tolerations of the console. |
| `controlCenter.podAnnotations` | object | `{}` | Pod annotations of the console. |

## Ramen

The `ramen` block installs the upstream Ramen disaster recovery operators. The hub operator runs on the management
cluster and requires Open Cluster Management. The DR cluster operator runs on each managed cluster that holds protected
volumes. Both are off by default. See [Installing Disaster Recovery](../../disaster-recovery/install/index.md).

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `ramen.image.repository` | string | `"quay.io/ramendr/ramen-operator"` | Ramen operator image. |
| `ramen.image.tag` | string | `"v0.1.0-rc1"` | Ramen operator image tag. |
| `ramen.image.pullPolicy` | string | `"IfNotPresent"` | Ramen operator image pull policy. One of `Always`, `IfNotPresent`, or `Never`. |
| `ramen.namespace` | string | `"ramen-system"` | Namespace of the Ramen objects. |
| `ramen.createNamespace` | bool | `true` | Creates `ramen.namespace`. Set it to `false` when the namespace exists. |
| `ramen.installCRDs` | bool | `true` | Installs the Ramen CRDs of the enabled operators. Set it to `false` where Ramen is already installed, for example, by Red Hat Advanced Cluster Management or OpenShift Data Foundation. The CRDs are kept on uninstall. |
| `ramen.s3StoreProfiles` | list | `[]` | S3 store profiles that Ramen keeps cluster data in for failover, in the Ramen `s3StoreProfiles` format. |
| `ramen.hub.enabled` | bool | `false` | Runs the Ramen hub operator, on the management cluster. It requires Open Cluster Management. |
| `ramen.hub.replicas` | int | `1` | Number of hub operator replicas. |
| `ramen.hub.config` | object | `{}` | Ramen configuration of the hub operator, merged over the Ramen defaults. |
| `ramen.hub.resources` | object | (see `values.yaml`) | Resource requests and limits of the hub operator. |
| `ramen.drCluster.enabled` | bool | `false` | Runs the Ramen DR cluster operator, on a managed cluster that holds protected volumes. |
| `ramen.drCluster.replicas` | int | `1` | Number of DR cluster operator replicas. |
| `ramen.drCluster.config` | object | `{}` | Ramen configuration of the DR cluster operator, merged over the Ramen defaults. |
| `ramen.drCluster.resources` | object | (see `values.yaml`) | Resource requests and limits of the DR cluster operator. |
| `ramen.nodeSelector` | object | `{}` | Node selector of the Ramen operators. |
| `ramen.tolerations` | list | `[]` | Tolerations of the Ramen operators. |

## Transport Security

The `tls` block is copied into the `tls` blocks of `ControlPlane/simplyblock` and `SimplyblockDriver/simplyblock`. TLS
requires cert-manager or OpenShift. Mutual TLS is only allowed with cert-manager, so both the `openshift` provider and
turning TLS off require `tls.mutual_enabled: false`. See
[Securing the Control Plane](../../kubernetes/installation/security.md).

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `tls.enabled` | bool | `true` | Encrypts control plane traffic with TLS. The render fails when the selected provider is unavailable, so a cluster with neither cert-manager nor OpenShift sets this to `false`. |
| `tls.provider` | string | `"cert-manager"` | Certificate provider. The `openshift` provider requires `tls.mutual_enabled: false`. One of `openshift` or `cert-manager`. |
| `tls.cert-manager.createSelfSignedIssuer` | bool | `true` | Creates a self-signed ClusterIssuer named by `cluster-issuer`. `false` uses an existing issuer. |
| `tls.cert-manager.cluster-issuer` | string | `"selfsigned"` | ClusterIssuer the chart mints its CA certificate from. |
| `tls.cert-manager.namespace` | string | `"cert-manager"` | Namespace cert-manager runs in. The chart places its CA Secret there so the ClusterIssuer can read it. |
| `tls.mutual_enabled` | bool | `true` | Requires client certificates (mutual TLS) and issues them for the operator, the CSI plugins, Prometheus, and the FoundationDB peers. Only allowed with `tls.provider=cert-manager`. |
