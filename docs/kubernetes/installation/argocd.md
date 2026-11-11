---
title: "Argo CD"
description: "Deploy simplyblock with Argo CD: the Application for the operator chart, the approved storage plane, and the values that differ from Helm."
weight: 30350
---

Simplyblock is deployed with Argo CD from one `Application` that installs the Helm chart, which brings up the
operator, the control plane, and the CSI driver. The storage plane is not synced from Git: a discovery run writes it
as a draft `ClusterDeploymentConfig`, which is reviewed and approved in the cluster. Everything the operator creates
is outside the `Application`, and Argo CD does not track it.

On OpenShift, the operator is installed through OperatorHub instead, as described in [OpenShift](openshift.md). The
`OperatorGroup` and the `Subscription` shown there are synced by an `Application` like any other manifest.

## Prerequisites

- **Argo CD:** Tested with version 3.5, with access to `https://install.simplyblock.io/helm`.
- **Kubernetes:** A cluster that meets the [Software Requirements](../../deployment-preparation/software-requirements.md).

cert-manager, the FoundationDB CRDs, the CSI snapshot controller, and a local-path provisioner do not have to be
installed first. The `ControlPlane` installs the ones the cluster lacks, as set by
`controlplane.local.prerequisites` (see [Install the Control Plane](k8s-control-plane.md#key-helm-values)).

## Operator and Control Plane

```yaml title="Application for the operator chart (simplyblock-application.yaml)"
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: simplyblock
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://install.simplyblock.io/helm
    chart: simplyblock-operator
    targetRevision: <chart-version>
    helm:
      releaseName: simplyblock-operator
  destination:
    server: https://kubernetes.default.svc
    namespace: simplyblock
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

```bash title="Creating the Application"
kubectl apply -f simplyblock-application.yaml
kubectl -n simplyblock get controlplane -w
```

### TLS on a Cluster Without cert-manager

TLS is enabled by default and issued by cert-manager. On a cluster that does not serve `cert-manager.io/v1` yet, the
chart renders without its cert-manager objects, and the operator issues its webhook certificate itself. Once the
`ControlPlane` has installed cert-manager, the next Argo CD refresh renders the chart's `Certificate` resources and
the operator's webhook configuration, and the automated sync applies them. The `Application` reports `OutOfSync` in
between, for up to one refresh interval (three minutes by default).

With `controlplane.local.prerequisites.installCertManager: false`, or with the `managed` profile, nothing installs
cert-manager, and the chart refuses to render until it is served.

### Development Images

The chart in the `main` branch of the operator repository references images that are not published to `quay.io`. An
`Application` that syncs the chart from Git instead of from the Helm repository sets the development images
explicitly:

```yaml title="Values for the chart from the main branch"
image:
  operator:
    repository: docker.io/simplyblock/simplyblock-operator
    tag: main
  simplyblock:
    repository: docker.io/simplyblock/simplyblock
    tag: main
driver:
  image:
    repository: docker.io/simplyblock/spdkcsi
    tag: main
```

## Storage Plane

On a fresh installation, the chart raises the discovery run `initial-discovery`, and the operator writes its result as
the draft `ClusterDeploymentConfig` `discovered-initial-discovery`. Further runs are requested with an `OperatorOps`
resource and the action `Discover` (see [Create a Storage Cluster](k8s-storage-plane.md#discover-workers-and-devices)).

The draft is inert until it is approved. It is reviewed and approved with `kubectl`:

```bash title="Reviewing and approving the draft"
kubectl -n simplyblock get clusterdeploymentconfig discovered-initial-discovery -o yaml
kubectl -n simplyblock patch clusterdeploymentconfig discovered-initial-discovery \
    --type merge -p '{"spec":{"approved":true}}'
```

The operator expands the approved document into a `StorageCluster` and its `StorageNodeSet`. Neither the draft nor
the objects it expands into belong to the `Application`, so `selfHeal` and `prune` do not touch them. Approval
cannot be withdrawn.

## Operations

`OperatorOps`, `StorageClusterOps`, `StorageNodeSetOps`, `ReplicationOps`, and the other `*Ops` resources are
imperative requests.
They are applied with `kubectl` and not committed to a path that an `Application` syncs with `selfHeal`, since a
completed request that Argo CD re-creates is a new request.

The chart's CRDs are installed from its `crds/` directory, which Argo CD applies on the first sync and on every sync
after that. A chart upgrade through Argo CD updates them, unlike a `helm upgrade`.

## Verification

```bash title="Checking the deployment"
kubectl -n argocd get applications
kubectl -n simplyblock get controlplane,clusterdeploymentconfig,storagecluster
```

The `Application` reports `Synced` and `Healthy`, the `ControlPlane` reports `Available`, and the `StorageCluster`
reports `Online`.
