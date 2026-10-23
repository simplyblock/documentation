---
title: "Simplyblock Helm Chart Values"
description: "Generated reference of every value of the simplyblock-operator Helm chart, with its type and default, grouped by top-level key."
weight: 20101
---

<!--
This file is generated. Do not edit it by hand.
Run scripts/helm-reference-gen.sh from the documentation repository.
-->

This page lists every value of the `simplyblock-operator` Helm chart, version `26.3.0`, as it appears in
the chart's `values.yaml`. What the chart renders, and example values files for common deployments, are described in
[Simplyblock Helm Chart](index.md).


## Cluster Domain

The DNS domain of the Kubernetes cluster. Every in-cluster address and certificate name the chart and the operator
build, and the FoundationDB cluster file, use it. It only needs to be changed on a cluster set up with a domain other
than `cluster.local`.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `clusterDnsDomain` | string | `"cluster.local"` |  |

## Images

The `image` block sets the images of the workloads the chart renders directly. The CSI driver image is set with
`driver.image` instead.

!!! warning
    Overriding the pinned images can leave the deployment unusable. Change them only when requested by simplyblock.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `image.csiSnapshotterController.repository` | string | `"quay.io/simplyblock-io/snapshot-controller"` |  |
| `image.csiSnapshotterController.tag` | string | `"v8.2.0"` |  |
| `image.csiSnapshotterController.pullPolicy` | string | `"Always"` |  |
| `image.csiAddonsController.repository` | string | `"quay.io/csiaddons/k8s-controller"` |  |
| `image.csiAddonsController.tag` | string | `"v0.15.0"` |  |
| `image.csiAddonsController.pullPolicy` | string | `"Always"` |  |
| `image.simplyblock.repository` | string | `"quay.io/simplyblock-io/simplyblock"` |  |
| `image.simplyblock.tag` | string | `"main"` |  |
| `image.simplyblock.pullPolicy` | string | `"Always"` |  |
| `image.operator.repository` | string | `"quay.io/simplyblock-io/simplyblock-operator"` |  |
| `image.operator.tag` | string | `"main"` |  |
| `image.operator.pullPolicy` | string | `"Always"` |  |
| `image.rebalancer.repository` | string | `"quay.io/simplyblock-io/simplyblock-rebalancer"` |  |
| `image.rebalancer.tag` | string | `""` |  |
| `image.numaResource.repository` | string | `"quay.io/simplyblock-io/numa-resource-plugin"` |  |
| `image.numaResource.tag` | string | `"latest"` |  |
| `image.numaResource.pullPolicy` | string | `"Always"` |  |

## Supporting Resources

These top-level values toggle the supporting resources the chart installs next to the operator: the CSI snapshot
controller, the CSI-Addons controller, and their CRDs where the cluster does not serve them yet.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `rbac.create` | bool | `true` |  |
| `snapshotcontroller.create` | bool | `true` |  |
| `csiaddons.create` | bool | `false` |  |

## CSI Credentials

The `externallyManagedSecret`, `csiConfig`, `csiSecret`, and `multiCluster` values render the
`simplyblock-csi-secret-v2` Secret with cluster credentials for the CSI driver. The credentials of the clusters the
operator creates are maintained by the operator, so these values are only needed for clusters it does not create. A
pool named in `csiConfig` or `multiCluster` also gets a block StorageClass, because no `StoragePool` exists for such a
cluster to write one.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `externallyManagedSecret.create` | bool | `true` |  |
| `csiConfig.simplybk.uuid` | string | `nil` |  |
| `csiConfig.simplybk.ip` | string | `nil` |  |
| `csiConfig.simplybk.pool` | string | `nil` |  |
| `csiConfig.simplybk.storageClassName` | string | `nil` |  |
| `csiSecret.simplybk.secret` | string | `nil` |  |
| `multiCluster.enable` | bool | `false` |  |
| `multiCluster.clusters[0].cluster_id` | string | `nil` |  |
| `multiCluster.clusters[0].secret` | string | `nil` |  |
| `multiCluster.clusters[0].workers` | string | `nil` |  |
| `multiCluster.clusters[0].pool` | string | `nil` |  |
| `multiCluster.clusters[0].storageClassName` | string | `nil` |  |

## Deployment Profile

The `deployment` block selects which of the control plane, the CSI driver, and the first discovery run the chart
renders. See [Deployment Profiles](index.md#deployment-profiles).

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `deployment.profile` | string | `"standalone"` |  |

## Discovery

The `discovery` block configures the first discovery run, rendered for the `standalone` profile as an `OperatorOps`
with the `Discover` action. The run inspects the workers and writes a `ClusterDeploymentConfig` in `Draft`. Nothing is
deployed until the draft is approved. A finished run is not repeated on upgrade, so a changed value has no effect after
the first installation. See
[Narrowing the First Discovery Run](index.md#narrowing-the-first-discovery-run).

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `discovery.enabled` | bool | `true` |  |
| `discovery.name` | string | `"initial-discovery"` |  |
| `discovery.namespace` | string | `""` |  |
| `discovery.nodeSelector` | object | `{}` |  |
| `discovery.tolerations` | list | `[]` |  |
| `discovery.enableControlPlaneNodes` | bool | `false` |  |
| `discovery.enableLogicalBlockDevices` | bool | `false` |  |
| `discovery.enablePartitionedDevices` | bool | `true` |  |
| `discovery.forceJournalDevice` | bool | `false` |  |
| `discovery.deviceFilter.blockAllowList` | list | `[]` |  |
| `discovery.deviceFilter.blockDenyList` | list | `[]` |  |
| `discovery.deviceFilter.pcieAllowList` | list | `[]` |  |
| `discovery.deviceFilter.pcieDenyList` | list | `[]` |  |
| `discovery.deviceFilter.pcieModel` | string | `""` |  |
| `discovery.deviceFilter.driveSizeRange` | string | `""` |  |
| `discovery.draft.name` | string | `""` |  |
| `discovery.draft.images.spdk` | string | `""` |  |
| `discovery.draft.images.spdkProxy` | string | `""` |  |
| `discovery.draft.cluster.name` | string | `""` |  |
| `discovery.draft.cluster.stripe` | object | `{}` |  |
| `discovery.draft.cluster.enableChecksumValidation` | bool | `nil` |  |
| `discovery.draft.cluster.enableAtomicity4K` | bool | `nil` |  |

## CSI Driver

The `driver` block is copied into `SimplyblockDriver/simplyblock`. From it, the CSI node and controller plugins, their
RBAC, and the CSIDriver registration are deployed by the operator. An empty field takes the version shipped with the
operator release.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `driver.driverName` | string | `"csi.simplyblock.io"` |  |
| `driver.image.repository` | string | `""` |  |
| `driver.image.tag` | string | `""` |  |
| `driver.image.pullPolicy` | string | `"Always"` |  |
| `driver.controllerReplicas` | int | `1` |  |
| `driver.nodeSelector` | object | `{}` |  |
| `driver.tolerations` | list | `[]` |  |
| `driver.controllerNodeSelector` | object | `{}` |  |
| `driver.controllerTolerations` | list | `[]` |  |
| `driver.enableVolumeSnapshots` | bool | `true` |  |
| `driver.enableServiceAccountAuth` | bool | `false` |  |
| `driver.sidecarImages.provisioner` | string | `""` |  |
| `driver.sidecarImages.attacher` | string | `""` |  |
| `driver.sidecarImages.resizer` | string | `""` |  |
| `driver.sidecarImages.snapshotter` | string | `""` |  |
| `driver.sidecarImages.healthMonitor` | string | `""` |  |
| `driver.sidecarImages.nodeDriverRegistrar` | string | `""` |  |
| `driver.sidecarImages.csiAddons` | string | `""` |  |

## pNFS Metadata Server

The `driver.pnfs` block configures the pNFS metadata server, which serves ReadWriteMany volumes. One metadata server
pod runs per storage cluster, on a node with `/dev/kvm`. See [pNFS Volumes](../../kubernetes/usage/pnfs.md).

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `driver.pnfs.mds.enabled` | bool | `true` |  |
| `driver.pnfs.mds.nodeSelector` | object | `{}` |  |
| `driver.pnfs.mds.tolerations` | list | `[]` |  |
| `driver.pnfs.mds.resources` | object | `{}` |  |
| `driver.pnfs.mds.stateSize` | string | `""` |  |
| `driver.pnfs.mds.dataNetwork.subnet` | string | `""` |  |
| `driver.pnfs.mds.dataNetwork.rangeStart` | string | `""` |  |
| `driver.pnfs.mds.dataNetwork.rangeEnd` | string | `""` |  |

## Control Plane

The `controlplane` block configures the control plane that `ControlPlane/simplyblock` describes, and the placement of
the workloads the chart renders around it. The `local` values apply to the `standalone` profile, the `managed` values
to the `managed` profile.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `controlplane.local.adminTokenSecretRef` | string | `""` |  |
| `controlplane.managed.endpoint` | string | `""` |  |
| `controlplane.managed.credentialsSecretRef` | string | `""` |  |
| `controlplane.managed.caBundleSecretRef` | string | `""` |  |
| `controlplane.managed.storageNodeImage` | string | `""` |  |
| `controlplane.tolerations.create` | bool | `false` |  |
| `controlplane.tolerations.list[0].operator` | string | `"Exists"` |  |
| `controlplane.tolerations.list[0].effect` | string | `nil` |  |
| `controlplane.tolerations.list[0].key` | string | `nil` |  |
| `controlplane.tolerations.list[0].value` | string | `nil` |  |
| `controlplane.nodeSelector.create` | bool | `false` |  |
| `controlplane.nodeSelector.key` | string | `nil` |  |
| `controlplane.nodeSelector.value` | string | `nil` |  |
| `controlplane.storageclass.name` | string | `nil` |  |

## Observability

The `controlplane.observability` block installs the optional logging, metrics, and dashboard stack: Graylog, Grafana,
Thanos, Fluent Bit, and the MongoDB and OpenSearch subcharts. It is intended for the `standalone` profile. See
[Observability and Alert Notifications](index.md#observability-and-alert-notifications).

!!! warning
    The observability stack ships with default passwords. They must be overridden in production.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `controlplane.observability.enabled` | bool | `false` |  |
| `controlplane.observability.secret` | string | (shipped default, see `values.yaml`) |  |
| `controlplane.observability.mongodb.installCRDs` | bool | `true` |  |
| `controlplane.observability.logParser` | string | `"cri"` |  |
| `controlplane.observability.graylog.repository` | string | `"quay.io/simplyblock-io/graylog"` |  |
| `controlplane.observability.graylog.tag` | string | `"5.0"` |  |
| `controlplane.observability.graylog.pullPolicy` | string | `"Always"` |  |
| `controlplane.observability.graylog.rootPasswordSha2` | string | (shipped default, see `values.yaml`) |  |
| `controlplane.observability.graylog.passwordSecret` | string | (shipped default, see `values.yaml`) |  |
| `controlplane.observability.graylog.maxNumberIndex` | string | `"3"` |  |
| `controlplane.observability.graylog.retentionPeriod` | string | `"7d"` |  |
| `controlplane.observability.grafana.repository` | string | `"quay.io/simplyblock-io/grafana"` |  |
| `controlplane.observability.grafana.tag` | string | `"10.0.12"` |  |
| `controlplane.observability.grafana.pullPolicy` | string | `"IfNotPresent"` |  |
| `controlplane.observability.grafana.endpoint` | string | `""` |  |
| `controlplane.observability.thanos.repository` | string | `"quay.io/simplyblock-io/thanos"` |  |
| `controlplane.observability.thanos.tag` | string | `"v0.31.0"` |  |
| `controlplane.observability.thanos.pullPolicy` | string | `"IfNotPresent"` |  |
| `controlplane.observability.fluentbit.repository` | string | `"quay.io/simplyblock-io/fluent-bit"` |  |
| `controlplane.observability.fluentbit.tag` | string | `"1.8.11"` |  |
| `controlplane.observability.fluentbit.pullPolicy` | string | `"IfNotPresent"` |  |

## Alert Notifications

The `controlplane.observability.grafana.notifications` block provisions receivers into the `grafana-alerts` contact
point. Every enabled channel is notified for every simplyblock alert. With none enabled, no contact point and no
notification policy are provisioned. The credentials are rendered into the `simplyblock-grafana-alerting` ConfigMap, so
read access to the release namespace is read access to them.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `controlplane.observability.grafana.notifications.slack.enabled` | bool | `false` |  |
| `controlplane.observability.grafana.notifications.slack.url` | string | `""` |  |
| `controlplane.observability.grafana.notifications.teams.enabled` | bool | `false` |  |
| `controlplane.observability.grafana.notifications.teams.url` | string | `""` |  |
| `controlplane.observability.grafana.notifications.pagerduty.enabled` | bool | `false` |  |
| `controlplane.observability.grafana.notifications.pagerduty.integrationKey` | string | `""` |  |
| `controlplane.observability.grafana.notifications.pagerduty.severity` | string | `"critical"` |  |
| `controlplane.observability.grafana.notifications.pagerduty.class` | string | `""` |  |
| `controlplane.observability.grafana.notifications.pagerduty.component` | string | `""` |  |
| `controlplane.observability.grafana.notifications.pagerduty.group` | string | `""` |  |
| `controlplane.observability.grafana.notifications.opsgenie.enabled` | bool | `false` |  |
| `controlplane.observability.grafana.notifications.opsgenie.apiKey` | string | `""` |  |
| `controlplane.observability.grafana.notifications.opsgenie.apiUrl` | string | `"https://api.opsgenie.com/v2/alerts"` |  |
| `controlplane.observability.grafana.notifications.opsgenie.autoClose` | bool | `true` |  |
| `controlplane.observability.grafana.notifications.opsgenie.overridePriority` | bool | `false` |  |
| `controlplane.observability.grafana.notifications.opsgenie.sendTagsAs` | string | `"tags"` |  |
| `controlplane.observability.grafana.notifications.webhook.enabled` | bool | `false` |  |
| `controlplane.observability.grafana.notifications.webhook.url` | string | `""` |  |
| `controlplane.observability.grafana.notifications.webhook.httpMethod` | string | `"POST"` |  |
| `controlplane.observability.grafana.notifications.webhook.username` | string | `""` |  |
| `controlplane.observability.grafana.notifications.webhook.password` | string | `""` |  |
| `controlplane.observability.grafana.notifications.webhook.authorizationScheme` | string | `""` |  |
| `controlplane.observability.grafana.notifications.webhook.authorizationCredentials` | string | `""` |  |
| `controlplane.observability.grafana.notifications.webhook.maxAlerts` | int | `0` |  |

## FoundationDB

The `controlplane.foundationdb` block configures the FoundationDB cluster that stores the control plane state of the
`standalone` profile. See [Dedicated Control Plane Nodes](index.md#dedicated-control-plane-nodes).

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `controlplane.foundationdb.installCRDs` | bool | `true` |  |
| `controlplane.foundationdb.redundancyMode` | string | `"double"` |  |
| `controlplane.foundationdb.nodeSelector` | object | `{}` |  |
| `controlplane.foundationdb.tolerations` | list | `[]` |  |
| `controlplane.foundationdb.exporter.enabled` | bool | `true` |  |

## Volume Migration

The `volumeMigration` block selects the kind volume moves are raised with. Volume moves are raised when the
rebalancer moves a volume off a busy node, when a node is drained, and when a claim is pinned to another node.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `volumeMigration.legacy` | bool | `false` |  |

## CSI Link

The `csiLink` block configures the endpoint the CSI node and controller pods dial on the operator. Through it, the
operator queries the storage state of a node without anything listening on the node.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `csiLink.port` | int | `9500` |  |
| `csiLink.certSecret` | string | `""` |  |
| `csiLink.serviceName` | string | `"simplyblock-csi-link"` |  |
| `csiLink.audience` | string | `"simplyblock-csi-link"` |  |

## Metrics API

The `metricsAPI` block configures the aggregated API `metrics.simplyblock.io/v1alpha2`. It serves capacity readings of
storage clusters, storage nodes, storage pools, storage devices, and logical volumes, computed on demand and never
stored. See [Capacity Metrics API](../../kubernetes/operations/monitoring/index.md#capacity-metrics-api).

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `metricsAPI.enabled` | bool | `true` |  |
| `metricsAPI.port` | int | `6443` |  |
| `metricsAPI.prometheusURL` | string | `"http://simplyblock-prometheus:9090"` |  |

## MongoDB

The `mongodb-kubernetes` block is passed to the upstream `mongodb-kubernetes` chart, which is installed with
`controlplane.observability.enabled` and runs the Graylog database.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `mongodb-kubernetes.name` | string | `"simplyblock-mongodb"` |  |
| `mongodb-kubernetes.deployment_name` | string | `"simplyblock-mongodb"` |  |
| `mongodb-kubernetes.resources.requests.cpu` | string | `"100m"` |  |
| `mongodb-kubernetes.resources.requests.memory` | string | `"300Mi"` |  |
| `mongodb-kubernetes.resources.limits.cpu` | string | `"250m"` |  |
| `mongodb-kubernetes.resources.limits.memory` | string | `"1Gi"` |  |
| `mongodb-kubernetes.community.mongodb.repo` | string | `"quay.io/simplyblock-io"` |  |
| `mongodb-kubernetes.community.mongodb.imageType` | string | `"ubi8"` |  |
| `mongodb-kubernetes.community.agent.name` | string | `"mongodb-agent"` |  |
| `mongodb-kubernetes.community.agent.version` | string | `"108.0.2.8729-1"` |  |
| `mongodb-kubernetes.community.registry.agent` | string | `"quay.io/simplyblock-io"` |  |
| `mongodb-kubernetes.registry.operator` | string | `"quay.io/simplyblock-io"` |  |
| `mongodb-kubernetes.registry.agent` | string | `"quay.io/simplyblock-io"` |  |
| `mongodb-kubernetes.registry.readinessProbe` | string | `"quay.io/simplyblock-io"` |  |
| `mongodb-kubernetes.registry.versionUpgradeHook` | string | `"quay.io/simplyblock-io"` |  |
| `mongodb-kubernetes.nodeSelector` | object | `{}` |  |
| `mongodb-kubernetes.tolerations` | list | `[]` |  |
| `mongodb-kubernetes.affinity.podAntiAffinity.requiredDuringSchedulingIgnoredDuringExecution[0].labelSelector.matchExpressions[0].key` | string | `"app.kubernetes.io/component"` |  |
| `mongodb-kubernetes.affinity.podAntiAffinity.requiredDuringSchedulingIgnoredDuringExecution[0].labelSelector.matchExpressions[0].operator` | string | `"In"` |  |
| `mongodb-kubernetes.affinity.podAntiAffinity.requiredDuringSchedulingIgnoredDuringExecution[0].labelSelector.matchExpressions[0].values[0]` | string | `"mongodb"` |  |
| `mongodb-kubernetes.affinity.podAntiAffinity.requiredDuringSchedulingIgnoredDuringExecution[0].topologyKey` | string | `"kubernetes.io/hostname"` |  |

## OpenSearch

The `opensearch` block is passed to the upstream `opensearch` chart, which is installed with
`controlplane.observability.enabled` and stores the Graylog log data.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `opensearch.fullnameOverride` | string | `"simplyblock-opensearch"` |  |
| `opensearch.singleNode` | bool | `true` |  |
| `opensearch.replicas` | int | `1` |  |
| `opensearch.nodeSelector` | object | `{}` |  |
| `opensearch.tolerations` | list | `[]` |  |
| `opensearch.antiAffinity` | string | `"hard"` |  |
| `opensearch.persistence.enabled` | bool | `true` |  |
| `opensearch.persistence.image` | string | `"quay.io/simplyblock-io/busybox"` |  |
| `opensearch.persistence.storageClass` | string | `nil` |  |
| `opensearch.persistence.size` | string | `"40Gi"` |  |
| `opensearch.image.repository` | string | `"quay.io/simplyblock-io/opensearch"` |  |
| `opensearch.image.tag` | string | `""` |  |
| `opensearch.resources.requests.cpu` | string | `"100m"` |  |
| `opensearch.resources.requests.memory` | string | `"512Mi"` |  |
| `opensearch.resources.limits.cpu` | string | `"500m"` |  |
| `opensearch.resources.limits.memory` | string | `"3Gi"` |  |
| `opensearch.extraEnvs[0].name` | string | `"bootstrap.memory_lock"` |  |
| `opensearch.extraEnvs[0].value` | string | `"true"` |  |
| `opensearch.extraEnvs[1].name` | string | `"action.auto_create_index"` |  |
| `opensearch.extraEnvs[1].value` | string | `"false"` |  |
| `opensearch.extraEnvs[2].name` | string | `"plugins.security.ssl.http.enabled"` |  |
| `opensearch.extraEnvs[2].value` | string | `"false"` |  |
| `opensearch.extraEnvs[3].name` | string | `"plugins.security.disabled"` |  |
| `opensearch.extraEnvs[3].value` | string | `"true"` |  |
| `opensearch.securityConfig.enabled` | bool | `false` |  |

## Reloader

The `reloader` block is passed to the upstream Stakater `reloader` chart. Reloader rolls the workloads that mount the
FoundationDB cluster file when the coordinators move.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `reloader.enabled` | bool | `true` |  |
| `reloader.nameOverride` | string | `"simplyblock-reloader"` |  |
| `reloader.fullnameOverride` | string | `"simplyblock-reloader"` |  |
| `reloader.reloader.deployment.image.name` | string | `"quay.io/simplyblock-io/reloader"` |  |
| `reloader.reloader.deployment.image.tag` | string | `"v1.3.0"` |  |
| `reloader.reloader.deployment.pod.annotations.log-collector/enabled` | string | `"true"` |  |
| `reloader.reloader.deployment.nodeSelector` | object | `{}` |  |
| `reloader.reloader.deployment.tolerations` | list | `[]` |  |

## Prometheus

The `prometheus` block is passed to the upstream `prometheus` chart. The instance stores the metrics the control plane
pushes and ships them to Thanos. Values not listed here take the upstream defaults.

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `prometheus.enabled` | bool | `true` |  |
| `prometheus.simplyblock.prometheusURL` | string | `"simplyblock-prometheus"` |  |
| `prometheus.simplyblock.prometheusPORT` | int | `9090` |  |
| `prometheus.server.image.repository` | string | `"quay.io/simplyblock-io/prometheus"` |  |
| `prometheus.server.image.tag` | string | `"v2.51.0"` |  |
| `prometheus.server.fullnameOverride` | string | `"simplyblock-prometheus"` |  |
| `prometheus.server.enabled` | bool | `true` |  |
| `prometheus.server.statefulSet.enabled` | bool | `true` |  |
| `prometheus.server.name` | string | `"simplyblock-prometheus"` |  |
| `prometheus.server.replicaCount` | int | `1` |  |
| `prometheus.server.podLabels.app` | string | `"simplyblock-prometheus"` |  |
| `prometheus.server.podAnnotations.log-collector/enabled` | string | `"true"` |  |
| `prometheus.server.podAnnotations."reloader.stakater.com/auto"` | string | `"true"` |  |
| `prometheus.server.podAnnotations."reloader.stakater.com/configmap"` | string | `"simplyblock-prometheus-config"` |  |
| `prometheus.server.nodeSelector` | object | `{}` |  |
| `prometheus.server.tolerations` | list | `[]` |  |
| `prometheus.server.affinity.podAntiAffinity.requiredDuringSchedulingIgnoredDuringExecution[0].labelSelector.matchExpressions[0].key` | string | `"app.kubernetes.io/component"` |  |
| `prometheus.server.affinity.podAntiAffinity.requiredDuringSchedulingIgnoredDuringExecution[0].labelSelector.matchExpressions[0].operator` | string | `"In"` |  |
| `prometheus.server.affinity.podAntiAffinity.requiredDuringSchedulingIgnoredDuringExecution[0].labelSelector.matchExpressions[0].values[0]` | string | `"simplyblock-prometheus"` |  |
| `prometheus.server.affinity.podAntiAffinity.requiredDuringSchedulingIgnoredDuringExecution[0].topologyKey` | string | `"kubernetes.io/hostname"` |  |
| `prometheus.server.service.servicePort` | int | `9090` |  |
| `prometheus.server.service.type` | string | `"ClusterIP"` |  |
| `prometheus.server.service.gRPC.enabled` | bool | `true` |  |
| `prometheus.server.service.gRPC.servicePort` | int | `10901` |  |
| `prometheus.server.service.additionalPorts[0].name` | string | `"http-thanos"` |  |
| `prometheus.server.service.additionalPorts[0].port` | int | `10902` |  |
| `prometheus.server.service.additionalPorts[0].targetPort` | int | `10902` |  |
| `prometheus.server.service.additionalPorts[0].protocol` | string | `"TCP"` |  |
| `prometheus.server.securityContext.fsGroup` | int | `65534` |  |
| `prometheus.server.persistentVolume.enabled` | bool | `true` |  |
| `prometheus.server.persistentVolume.size` | string | `"20Gi"` |  |
| `prometheus.server.persistentVolume.storageClass` | string | `nil` |  |
| `prometheus.server.extraArgs."storage.tsdb.min-block-duration"` | string | `"2h"` |  |
| `prometheus.server.extraArgs."storage.tsdb.max-block-duration"` | string | `"2h"` |  |
| `prometheus.server.sidecarContainers.thanos-sidecar.image` | string | `"quay.io/simplyblock-io/thanos:v0.31.0"` |  |
| `prometheus.server.sidecarContainers.thanos-sidecar.args[0]` | string | `"sidecar"` |  |
| `prometheus.server.sidecarContainers.thanos-sidecar.args[1]` | string | `"--tsdb.path=/prometheus"` |  |
| `prometheus.server.sidecarContainers.thanos-sidecar.args[2]` | string | `"--prometheus.url=http://localhost:9090"` |  |
| `prometheus.server.sidecarContainers.thanos-sidecar.args[3]` | string | `"--objstore.config-file=/etc/thanos/objstore.yml"` |  |
| `prometheus.server.sidecarContainers.thanos-sidecar.ports[0].name` | string | `"grpc"` |  |
| `prometheus.server.sidecarContainers.thanos-sidecar.ports[0].containerPort` | int | `10901` |  |
| `prometheus.server.sidecarContainers.thanos-sidecar.ports[1].name` | string | `"http"` |  |
| `prometheus.server.sidecarContainers.thanos-sidecar.ports[1].containerPort` | int | `10902` |  |
| `prometheus.server.sidecarContainers.thanos-sidecar.volumeMounts[0].name` | string | `"storage-volume"` |  |
| `prometheus.server.sidecarContainers.thanos-sidecar.volumeMounts[0].mountPath` | string | `"/prometheus"` |  |
| `prometheus.server.sidecarContainers.thanos-sidecar.volumeMounts[1].name` | string | `"objstore-config"` |  |
| `prometheus.server.sidecarContainers.thanos-sidecar.volumeMounts[1].mountPath` | string | `"/etc/thanos"` |  |
| `prometheus.server.sidecarContainers.thanos-sidecar.resources.requests.cpu` | string | `"100m"` |  |
| `prometheus.server.sidecarContainers.thanos-sidecar.resources.requests.memory` | string | `"256Mi"` |  |
| `prometheus.server.sidecarContainers.thanos-sidecar.resources.limits.cpu` | string | `"250m"` |  |
| `prometheus.server.sidecarContainers.thanos-sidecar.resources.limits.memory` | string | `"1Gi"` |  |
| `prometheus.server.resources.requests.cpu` | string | `"100m"` |  |
| `prometheus.server.resources.requests.memory` | string | `"512Mi"` |  |
| `prometheus.server.resources.limits.cpu` | string | `"500m"` |  |
| `prometheus.server.resources.limits.memory` | string | `"1Gi"` |  |
| `prometheus.server.configPath` | string | `"/etc/simplyblock-config/prometheus.yml"` |  |
| `prometheus.server.extraVolumes[0].name` | string | `"simplyblock-prometheus-config"` |  |
| `prometheus.server.extraVolumes[0].configMap.name` | string | `"simplyblock-prometheus-config"` |  |
| `prometheus.server.extraVolumes[1].name` | string | `"objstore-config"` |  |
| `prometheus.server.extraVolumes[1].configMap.name` | string | `"simplyblock-objstore-config"` |  |
| `prometheus.server.extraVolumes[2].name` | string | `"prometheus-client-tls"` |  |
| `prometheus.server.extraVolumes[2].secret.secretName` | string | `"simplyblock-prometheus-client-tls"` |  |
| `prometheus.server.extraVolumes[2].secret.optional` | bool | `true` |  |
| `prometheus.server.extraVolumes[3].name` | string | `"prometheus-ca-tls"` |  |
| `prometheus.server.extraVolumes[3].secret.secretName` | string | `"simplyblock-ca-bundle-tls"` |  |
| `prometheus.server.extraVolumes[3].secret.optional` | bool | `true` |  |
| `prometheus.server.extraVolumeMounts[0].name` | string | `"simplyblock-prometheus-config"` |  |
| `prometheus.server.extraVolumeMounts[0].mountPath` | string | `"/etc/simplyblock-config"` |  |
| `prometheus.server.extraVolumeMounts[1].name` | string | `"prometheus-client-tls"` |  |
| `prometheus.server.extraVolumeMounts[1].mountPath` | string | `"/etc/prometheus/certs"` |  |
| `prometheus.server.extraVolumeMounts[1].readOnly` | bool | `true` |  |
| `prometheus.server.extraVolumeMounts[2].name` | string | `"prometheus-ca-tls"` |  |
| `prometheus.server.extraVolumeMounts[2].mountPath` | string | `"/etc/prometheus/ca"` |  |
| `prometheus.server.extraVolumeMounts[2].readOnly` | bool | `true` |  |
| `prometheus.alertmanager.enabled` | bool | `false` |  |
| `prometheus.prometheus-pushgateway.enabled` | bool | `false` |  |
| `prometheus.prometheus-node-exporter.enabled` | bool | `false` |  |
| `prometheus.kube-state-metrics.enabled` | bool | `false` |  |
| `prometheus.configmapReload.prometheus.image.repository` | string | `"quay.io/simplyblock-io/prometheus-config-reloader"` |  |
| `prometheus.configmapReload.prometheus.image.tag` | string | `"v0.72.0"` |  |
| `prometheus.defaultBackend.enabled` | bool | `false` |  |
| `prometheus.defaultBackend.name` | string | `"defaultbackend"` |  |
| `prometheus.defaultBackend.image.registry` | string | `"quay.io/simplyblock-io"` |  |
| `prometheus.defaultBackend.image.image` | string | `"defaultbackend-amd64"` |  |
| `prometheus.defaultBackend.image.tag` | string | `"1.5"` |  |

## Control Center

The `controlCenter` block deploys the Control Center web console. The console proxies the Kubernetes API, so
authentication has to be put in front of it before it is exposed. See
[Control Center With an Ingress](index.md#control-center-with-an-ingress).

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `controlCenter.enabled` | bool | `false` |  |
| `controlCenter.nameOverride` | string | `""` |  |
| `controlCenter.fullnameOverride` | string | `""` |  |
| `controlCenter.image.registry` | string | `""` |  |
| `controlCenter.image.repository` | string | `"simplyblock-io/control-center"` |  |
| `controlCenter.image.tag` | string | `""` |  |
| `controlCenter.image.pullPolicy` | string | `"IfNotPresent"` |  |
| `controlCenter.imagePullSecrets` | list | `[]` |  |
| `controlCenter.replicas` | int | `2` |  |
| `controlCenter.mode` | string | `"full"` |  |
| `controlCenter.drNamespace` | string | `"ramen-ops"` |  |
| `controlCenter.drHubNamespace` | string | `"dr-simplyblock"` |  |
| `controlCenter.authMode` | string | `"serviceaccount"` |  |
| `controlCenter.tokenRefreshSeconds` | int | `600` |  |
| `controlCenter.kubernetesApi` | string | `"https://kubernetes.default.svc"` |  |
| `controlCenter.kubernetesApiHost` | string | `"kubernetes.default.svc"` |  |
| `controlCenter.kubernetesApiCaFile` | string | `"/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"` |  |
| `controlCenter.operatorUrl` | string | `""` |  |
| `controlCenter.helmUrl` | string | `""` |  |
| `controlCenter.prometheusUrl` | string | `""` |  |
| `controlCenter.controlPlane.enabled` | bool | `true` |  |
| `controlCenter.controlPlane.url` | string | `""` |  |
| `controlCenter.controlPlane.trustServiceAccount` | bool | `true` |  |
| `controlCenter.controlPlane.tokenSecret` | string | `""` |  |
| `controlCenter.logStore.enabled` | bool | `true` |  |
| `controlCenter.logStore.url` | string | `""` |  |
| `controlCenter.logStore.user` | string | `"admin"` |  |
| `controlCenter.logStore.passwordSecret` | string | `""` |  |
| `controlCenter.logStore.passwordKey` | string | `""` |  |
| `controlCenter.logStore.tokenSecret` | string | `""` |  |
| `controlCenter.rbac.create` | bool | `true` |  |
| `controlCenter.rbac.hubLabelling` | bool | `false` |  |
| `controlCenter.service.type` | string | `"ClusterIP"` |  |
| `controlCenter.service.port` | int | `80` |  |
| `controlCenter.ingress.enabled` | bool | `false` |  |
| `controlCenter.ingress.className` | string | `"nginx"` |  |
| `controlCenter.ingress.host` | string | `""` |  |
| `controlCenter.ingress.annotations."nginx.ingress.kubernetes.io/auth-type"` | string | `"basic"` |  |
| `controlCenter.ingress.annotations."nginx.ingress.kubernetes.io/auth-secret"` | string | `"simplyblock-control-center-auth"` |  |
| `controlCenter.ingress.annotations."nginx.ingress.kubernetes.io/auth-realm"` | string | `"simplyblock Control Center"` |  |
| `controlCenter.ingress.annotations."nginx.ingress.kubernetes.io/proxy-body-size"` | string | `"2m"` |  |
| `controlCenter.ingress.annotations."nginx.ingress.kubernetes.io/proxy-read-timeout"` | string | `"3600"` |  |
| `controlCenter.ingress.tls` | list | `[]` |  |
| `controlCenter.networkPolicy.enabled` | bool | `false` |  |
| `controlCenter.networkPolicy.apiServerCidrs[0]` | string | `"10.0.0.0/8"` |  |
| `controlCenter.networkPolicy.apiServerCidrs[1]` | string | `"172.16.0.0/12"` |  |
| `controlCenter.networkPolicy.apiServerCidrs[2]` | string | `"192.168.0.0/16"` |  |
| `controlCenter.networkPolicy.ingressFromNamespaces` | list | `[]` |  |
| `controlCenter.mock.enabled` | bool | `false` |  |
| `controlCenter.mock.image.registry` | string | `""` |  |
| `controlCenter.mock.image.repository` | string | `"simplyblock-io/control-center-mock"` |  |
| `controlCenter.mock.image.tag` | string | `""` |  |
| `controlCenter.mock.image.pullPolicy` | string | `"IfNotPresent"` |  |
| `controlCenter.mock.dataset` | string | `"auto"` |  |
| `controlCenter.mock.seed` | int | `0` |  |
| `controlCenter.mock.simInterval` | string | `"4s"` |  |
| `controlCenter.mock.failRate` | float | `0.1` |  |
| `controlCenter.mock.resources.requests.cpu` | string | `"10m"` |  |
| `controlCenter.mock.resources.requests.memory` | string | `"32Mi"` |  |
| `controlCenter.mock.resources.limits.cpu` | string | `"200m"` |  |
| `controlCenter.mock.resources.limits.memory` | string | `"256Mi"` |  |
| `controlCenter.resources.requests.cpu` | string | `"20m"` |  |
| `controlCenter.resources.requests.memory` | string | `"48Mi"` |  |
| `controlCenter.resources.limits.cpu` | string | `"500m"` |  |
| `controlCenter.resources.limits.memory` | string | `"192Mi"` |  |
| `controlCenter.nodeSelector` | object | `{}` |  |
| `controlCenter.tolerations` | list | `[]` |  |
| `controlCenter.podAnnotations` | object | `{}` |  |

## Ramen

The `ramen` block installs the upstream Ramen disaster recovery operators. The hub operator runs on the management
cluster and requires Open Cluster Management. The DR cluster operator runs on each managed cluster that holds protected
volumes. Both are off by default. See [Installing Disaster Recovery](../../disaster-recovery/install/index.md).

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `ramen.image.repository` | string | `"quay.io/ramendr/ramen-operator"` |  |
| `ramen.image.tag` | string | `"v0.1.0-rc1"` |  |
| `ramen.image.pullPolicy` | string | `"IfNotPresent"` |  |
| `ramen.namespace` | string | `"ramen-system"` |  |
| `ramen.createNamespace` | bool | `true` |  |
| `ramen.installCRDs` | bool | `true` |  |
| `ramen.s3StoreProfiles` | list | `[]` |  |
| `ramen.hub.enabled` | bool | `false` |  |
| `ramen.hub.replicas` | int | `1` |  |
| `ramen.hub.config` | object | `{}` |  |
| `ramen.hub.resources.requests.cpu` | string | `"100m"` |  |
| `ramen.hub.resources.requests.memory` | string | `"200Mi"` |  |
| `ramen.hub.resources.limits.cpu` | string | `"100m"` |  |
| `ramen.hub.resources.limits.memory` | string | `"300Mi"` |  |
| `ramen.drCluster.enabled` | bool | `false` |  |
| `ramen.drCluster.replicas` | int | `1` |  |
| `ramen.drCluster.config` | object | `{}` |  |
| `ramen.drCluster.resources.requests.cpu` | string | `"100m"` |  |
| `ramen.drCluster.resources.requests.memory` | string | `"200Mi"` |  |
| `ramen.drCluster.resources.limits.cpu` | string | `"100m"` |  |
| `ramen.drCluster.resources.limits.memory` | string | `"300Mi"` |  |
| `ramen.nodeSelector` | object | `{}` |  |
| `ramen.tolerations` | list | `[]` |  |

## Transport Security

The `tls` block is copied into the `tls` blocks of `ControlPlane/simplyblock` and `SimplyblockDriver/simplyblock`. TLS
requires cert-manager or OpenShift. Mutual TLS is only allowed with cert-manager, so both the `openshift` provider and
turning TLS off require `tls.mutual_enabled: false`. See
[Securing the Control Plane](../../kubernetes/installation/security.md).

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `tls.enabled` | bool | `true` |  |
| `tls.provider` | string | `"cert-manager"` |  |
| `tls.cert-manager.createSelfSignedIssuer` | bool | `true` |  |
| `tls.cert-manager.cluster-issuer` | string | `"selfsigned"` |  |
| `tls.cert-manager.namespace` | string | `"cert-manager"` |  |
| `tls.mutual_enabled` | bool | `true` |  |
