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


## `clusterDnsDomain`

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `clusterDnsDomain` | string | `"cluster.local"` |  |

## `image`

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

## `rbac`

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `rbac.create` | bool | `true` |  |

## `snapshotcontroller`

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `snapshotcontroller.create` | bool | `true` |  |

## `csiaddons`

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `csiaddons.create` | bool | `false` |  |

## `externallyManagedSecret`

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `externallyManagedSecret.create` | bool | `true` |  |

## `spdkdev`

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `spdkdev.create` | bool | `false` |  |

## `csiConfig`

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `csiConfig.simplybk.uuid` | string | `nil` |  |
| `csiConfig.simplybk.ip` | string | `nil` |  |
| `csiConfig.simplybk.pool` | string | `nil` |  |
| `csiConfig.simplybk.storageClassName` | string | `nil` |  |

## `csiSecret`

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `csiSecret.simplybk.secret` | string | (shipped default, see `values.yaml`) |  |

## `podAnnotations`

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `podAnnotations` | object | `{}` |  |

## `simplyBlockAnnotations`

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `simplyBlockAnnotations` | object | `{}` |  |

## `multiCluster`

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `multiCluster.enable` | bool | `false` |  |
| `multiCluster.clusters[0].cluster_id` | string | `nil` |  |
| `multiCluster.clusters[0].secret` | string | (shipped default, see `values.yaml`) |  |
| `multiCluster.clusters[0].workers` | string | `nil` |  |
| `multiCluster.clusters[0].pool` | string | `nil` |  |
| `multiCluster.clusters[0].storageClassName` | string | `nil` |  |

## `deployment`

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `deployment.profile` | string | `"standalone"` |  |

## `discovery`

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
| `discovery.draft.cluster.enableChecksumValidation` | string | `nil` |  |
| `discovery.draft.cluster.enableAtomicity4K` | string | `nil` |  |

## `driver`

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
| `driver.pnfs.mds.enabled` | bool | `true` |  |
| `driver.pnfs.mds.nodeSelector` | object | `{}` |  |
| `driver.pnfs.mds.tolerations` | list | `[]` |  |
| `driver.pnfs.mds.resources` | object | `{}` |  |
| `driver.pnfs.mds.stateSize` | string | `""` |  |
| `driver.pnfs.mds.dataNetwork.subnet` | string | `""` |  |
| `driver.pnfs.mds.dataNetwork.rangeStart` | string | `""` |  |
| `driver.pnfs.mds.dataNetwork.rangeEnd` | string | `""` |  |

## `controlplane`

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `controlplane.local.adminTokenSecretRef` | string | `""` |  |
| `controlplane.managed.endpoint` | string | `""` |  |
| `controlplane.managed.credentialsSecretRef` | string | `""` |  |
| `controlplane.managed.caBundleSecretRef` | string | `""` |  |
| `controlplane.managed.storageNodeImage` | string | `""` |  |
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
| `controlplane.observability.thanos.repository` | string | `"quay.io/simplyblock-io/thanos"` |  |
| `controlplane.observability.thanos.tag` | string | `"v0.31.0"` |  |
| `controlplane.observability.thanos.pullPolicy` | string | `"IfNotPresent"` |  |
| `controlplane.observability.minio.repository` | string | `"quay.io/simplyblock-io/minio"` |  |
| `controlplane.observability.minio.tag` | string | `"RELEASE.2024-01-16T16-07-38Z"` |  |
| `controlplane.observability.minio.pullPolicy` | string | `"IfNotPresent"` |  |
| `controlplane.observability.minio.mcRepository` | string | `"quay.io/simplyblock-io/minio-client"` |  |
| `controlplane.observability.minio.mcTag` | string | `"RELEASE.2024-01-16T16-06-34Z"` |  |
| `controlplane.observability.minio.bucket` | string | `"thanos"` |  |
| `controlplane.observability.minio.accessKey` | string | `"minioadmin"` |  |
| `controlplane.observability.minio.secretKey` | string | (shipped default, see `values.yaml`) |  |
| `controlplane.observability.minio.storageSize` | string | `"50Gi"` |  |
| `controlplane.observability.minio.storageClass` | string | `nil` |  |
| `controlplane.observability.fluentbit.repository` | string | `"quay.io/simplyblock-io/fluent-bit"` |  |
| `controlplane.observability.fluentbit.tag` | string | `"1.8.11"` |  |
| `controlplane.observability.fluentbit.pullPolicy` | string | `"IfNotPresent"` |  |
| `controlplane.tolerations.create` | bool | `false` |  |
| `controlplane.tolerations.list[0].operator` | string | `"Exists"` |  |
| `controlplane.tolerations.list[0].effect` | string | `nil` |  |
| `controlplane.tolerations.list[0].key` | string | `nil` |  |
| `controlplane.tolerations.list[0].value` | string | `nil` |  |
| `controlplane.nodeSelector.create` | bool | `false` |  |
| `controlplane.nodeSelector.key` | string | `nil` |  |
| `controlplane.nodeSelector.value` | string | `nil` |  |
| `controlplane.storageclass.name` | string | `nil` |  |
| `controlplane.storageclass.allowedTopologyZones` | list | `[]` |  |
| `controlplane.foundationdb.installCRDs` | bool | `true` |  |
| `controlplane.foundationdb.redundancyMode` | string | `"double"` |  |
| `controlplane.foundationdb.nodeSelector` | object | `{}` |  |
| `controlplane.foundationdb.tolerations` | list | `[]` |  |
| `controlplane.foundationdb.image.operator.repository` | string | `"quay.io/simplyblock-io/fdb-kubernetes-operator"` |  |
| `controlplane.foundationdb.image.operator.tag` | string | `"v2.13.0"` |  |
| `controlplane.foundationdb.image.monitor.repository` | string | `"quay.io/simplyblock-io/fdb-kubernetes-monitor"` |  |
| `controlplane.foundationdb.image.monitor.tag` | string | `"7.3.63"` |  |
| `controlplane.foundationdb.image.mainContainer.baseImage` | string | `"quay.io/simplyblock-io/fdb-kubernetes-monitor"` |  |
| `controlplane.foundationdb.exporter.enabled` | bool | `true` |  |

## `volumeMigration`

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `volumeMigration.legacy` | bool | `false` |  |

## `csiLink`

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `csiLink.port` | int | `9500` |  |
| `csiLink.certSecret` | string | `""` |  |
| `csiLink.serviceName` | string | `"simplyblock-csi-link"` |  |
| `csiLink.audience` | string | `"simplyblock-csi-link"` |  |

## `metricsAPI`

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `metricsAPI.enabled` | bool | `true` |  |
| `metricsAPI.port` | int | `6443` |  |
| `metricsAPI.prometheusURL` | string | `"http://simplyblock-prometheus:9090"` |  |

## `mongodb-kubernetes`

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

## `opensearch`

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

## `reloader`

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

## `prometheus`

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

## `controlCenter`

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

## `ramen`

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

## `tls`

| Value | Type | Default | Description |
|-------|------|---------|-------------|
| `tls.enabled` | bool | `true` |  |
| `tls.provider` | string | `"cert-manager"` |  |
| `tls.cert-manager.createSelfSignedIssuer` | bool | `true` |  |
| `tls.cert-manager.cluster-issuer` | string | `"selfsigned"` |  |
| `tls.cert-manager.namespace` | string | `"cert-manager"` |  |
| `tls.mutual_enabled` | bool | `true` |  |
