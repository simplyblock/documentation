---
title: "Install Simplyblock Operator"
description: "Install the Simplyblock Operator with Helm. The operator installs the control plane and CSI driver from the ControlPlane and SimplyblockDriver resources."
weight: 30000
---

The Simplyblock Operator is deployed with a single Helm chart. The chart installs the operator, all simplyblock CRDs,
the admission webhooks, and the metrics API. It also creates two custom resources, `ControlPlane/simplyblock` and
`SimplyblockDriver/simplyblock`. From these, the operator installs the control plane (FoundationDB, the object store,
and the management API) and the CSI driver. Storage clusters are created afterward, see
[Create a Storage Cluster](k8s-storage-plane.md).

## Prerequisites

- **Kubernetes:** A cluster that meets the [Software Requirements](../../deployment-preparation/software-requirements.md).
- **Tools:** Helm 3 and `kubectl` configured with cluster-admin access.
- **Storage for FoundationDB:** A StorageClass for the FoundationDB persistent volumes of the control plane. It should not
  be a simplyblock StorageClass, because the control plane has to start before any simplyblock volume can be served.
- **Certificate issuer:** TLS is enabled by default and requires either
  [cert-manager](https://cert-manager.io/){:target="_blank" rel="noopener"} or, on OpenShift, the OpenShift service CA.
  Without either of them, TLS must be disabled explicitly with `tls.enabled=false`. See
  [Securing the Control Plane](security.md).

When deploying onto an OpenShift cluster, the environment-specific instructions in the [OpenShift](openshift.md) guide
must be followed first.

## Installing the Operator

```bash title="Install the Simplyblock Operator"
helm repo add simplyblock https://install.simplyblock.io/helm
helm repo update

helm install simplyblock-operator simplyblock/simplyblock-operator \
    --namespace simplyblock \
    --create-namespace
```

The chart refuses to render if TLS is enabled but no issuer is available. On a cluster with neither cert-manager nor
OpenShift, add `--set tls.enabled=false`.

The chart's values schema rejects unknown keys in several places, so a misspelled value fails the installation
instead of being ignored.

## Key Helm Values

| Value                                                        | Default                                       | Description                                                                                                                                                                                                                                            |
|--------------------------------------------------------------|-----------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `deployment.profile`                                         | `standalone`                                  | `standalone` installs a local control plane (`ControlPlane.spec.source.local`). `managed` connects to a control plane elsewhere (`spec.source.managed`) and installs none.                                                                             |
| `controlplane.managed.endpoint`                              |                                               | Base URL of the remote management API. Required for the `managed` profile.                                                                                                                                                                             |
| `controlplane.managed.credentialsSecretRef`                  |                                               | Secret with the bearer token for the remote control plane.                                                                                                                                                                                             |
| `controlplane.managed.caBundleSecretRef`                     |                                               | Secret with the CA certificate the remote endpoint is verified against.                                                                                                                                                                                |
| `image.simplyblock.repository`, `.tag`, `.pullPolicy`        | `quay.io/simplyblock-io/simplyblock`          | Control plane image, written to `ControlPlane.spec.source.local.image`. It is also the default storage node image.                                                                                                                                     |
| `image.operator.repository`, `.tag`                          | `quay.io/simplyblock-io/simplyblock-operator` | Operator image.                                                                                                                                                                                                                                        |
| `controlplane.foundationdb.redundancyMode`                   | `double`                                      | `double` runs 3 FoundationDB coordinators and tolerates one failure. `triple` runs 5 coordinators and tolerates two failures.                                                                                                                          |
| `controlplane.storageclass.name`                             |                                               | StorageClass for the FoundationDB volumes.                                                                                                                                                                                                             |
| `controlplane.nodeSelector.create`, `.key`, `.value`         | `false`                                       | Pins the control plane workloads to labeled nodes.                                                                                                                                                                                                     |
| `controlplane.tolerations.create`, `.list`                   | `false`                                       | Tolerations for the control plane workloads.                                                                                                                                                                                                           |
| `controlplane.observability.enabled`                         | `false`                                       | Installs the optional logging and dashboard stack. `standalone` profile only.                                                                                                                                                                          |
| `tls.enabled`                                                | `true`                                        | Encrypts control plane traffic with TLS.                                                                                                                                                                                                               |
| `tls.provider`                                               | `cert-manager`                                | `cert-manager` or `openshift`.                                                                                                                                                                                                                         |
| `tls.mutual_enabled`                                         | `true`                                        | Requires client certificates (mutual TLS). Only allowed with `tls.provider=cert-manager`.                                                                                                                                                              |
| `tls.cert-manager.createSelfSignedIssuer`, `.cluster-issuer` | `true`, `selfsigned`                          | The cert-manager `ClusterIssuer` the chart mints its CA from.                                                                                                                                                                                          |
| `driver.*`                                                   |                                               | Copied into the `SimplyblockDriver` resource: `driverName`, `image.*`, `controllerReplicas`, `nodeSelector`, `tolerations`, `controllerNodeSelector`, `controllerTolerations`, `enableVolumeSnapshots`, `enableServiceAccountAuth`, `sidecarImages.*`. |
| `controlplane.trustCSIServiceAccounts`                       | `false`                                       | Lets the control plane accept the CSI driver's service account tokens. Set together with `driver.enableServiceAccountAuth`.                                                                                                                            |
| `metricsAPI.enabled`                                         | `true`                                        | Serves the read-only metrics API `metrics.simplyblock.io/v1alpha2`.                                                                                                                                                                                    |
| `metricsAPI.prometheusURL`                                   | `http://simplyblock-prometheus:9090`          | Where the metrics API reads capacity samples from.                                                                                                                                                                                                     |
| `prometheus.enabled`                                         | `true`                                        | Installs the Prometheus instance the control plane pushes metrics to.                                                                                                                                                                                  |
| `reloader.enabled`                                           | `true`                                        | Rolls workloads that mount the FoundationDB cluster file when the coordinators move.                                                                                                                                                                   |
| `snapshotcontroller.create`                                  | `true`                                        | Installs the CSI snapshot controller.                                                                                                                                                                                                                  |
| `volumeMigration.legacy`                                     | `false`                                       | Re-enables the legacy `VolumeMigration` kind. Only needed while migrations raised against it drain after an upgrade.                                                                                                                                   |

The full list of values is documented in the [Simplyblock Helm Chart Reference](../../reference/kubernetes/index.md).

!!! warning "The driver name is immutable"
    `driver.driverName` (default `csi.simplyblock.io`) cannot be changed once the `SimplyblockDriver` exists. Every
    persistent volume records it, so changing it later orphans existing volumes.

## Waiting for the Control Plane and the CSI Driver

With the `standalone` profile, the operator installs FoundationDB first and starts the management API once the
database has reached quorum. The first installation therefore takes a few minutes.

```bash title="Wait for the control plane"
kubectl -n simplyblock get controlplane simplyblock -w

kubectl -n simplyblock wait controlplane simplyblock \
    --for=jsonpath='{.status.phase}'=Available --timeout=600s
```

The phase moves from `Installing` to `Available`. `Degraded` means the control plane answers while a component
behind it is short, and `status.components` lists which one. No storage resource is reconciled before the control
plane is `Available`.

Afterward, the CSI driver is deployed:

```bash title="Check the CSI driver"
kubectl -n simplyblock get simplyblockdriver simplyblock
```

The `SimplyblockDriver` phase is `Installing`, `Ready`, `Degraded`, or `Unavailable`. The columns `NODESREADY` and
`NODESTOTAL` show how many node plugins are running.

## Managed Profile

With `deployment.profile=managed`, the chart installs the operator and the CSI driver, but no control plane. The
`ControlPlane` resource points at a management API that runs elsewhere, and the operator only resolves and probes
that endpoint. Loopback and link-local endpoints are rejected. See
[Connecting to an External Control Plane](install-csi.md).

## Upgrading the Chart

`helm upgrade` does not update CRDs. Before upgrading the chart, apply the CRDs of the new chart version with a
server-side apply:

```bash title="Update the CRDs before a chart upgrade"
helm pull simplyblock/simplyblock-operator --untar
kubectl apply --server-side -f simplyblock-operator/crds/
helm upgrade simplyblock-operator simplyblock/simplyblock-operator -n simplyblock
```

## Uninstalling

The `ControlPlane` and `SimplyblockDriver` resources carry the annotation `helm.sh/resource-policy: keep`, so
`helm uninstall` leaves them in place. They must be deleted with `kubectl delete` while the operator is still running,
so that the operator can release their finalizers.

!!! warning
    Deleting a local `ControlPlane` deletes the FoundationDB database that holds every cluster definition, node
    registration, and volume record. Deleting the `SimplyblockDriver` removes the CSI driver, and attached volumes
    can no longer be detached.

## Next Steps

Once the control plane is `Available`, proceed to [Create a Storage Cluster](k8s-storage-plane.md).

For a complete reference of all CRD fields, see [Simplyblock Operator](../../reference/operator/index.md).
