---
title: "Argo CD"
description: "Deploy simplyblock with Argo CD: one Application for the operator chart and the control plane, a second one for the storage plane, and the values that differ from a Helm install."
weight: 30350
---

Simplyblock is deployed with Argo CD from two `Application` resources. The first one installs the Helm chart, which
brings up the operator, the control plane, and the CSI driver. The second one syncs the storage plane: an approved
`ClusterDeploymentConfig` kept in a Git repository. Everything else is created by the operator, and Argo CD does not
track it.

On OpenShift, the operator is installed through OperatorHub instead, as described in [OpenShift](openshift.md). The
`OperatorGroup` and the `Subscription` shown there are synced by an `Application` like any other manifest.

## Prerequisites

- **Argo CD:** Tested with version 3.5, with access to `https://install.simplyblock.io/helm` and to the Git repository
  that holds the storage plane.
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
      valuesObject:
        discovery:
          enabled: false
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

`discovery.enabled: false` keeps the chart from raising the discovery run. The storage plane is declared in Git, so a
draft waiting in the cluster has no reader. A cluster whose workers and devices are not known yet keeps the default
for its first sync and copies the draft into Git, as described below.

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

The storage plane is one approved `ClusterDeploymentConfig` per cluster. Its workers, interfaces, and device
addresses come from a discovery run. On a first installation, the discovery run is raised by the chart (with
`discovery.enabled` left at its default) or written by hand as an `OperatorOps` (see
[Create a Storage Cluster](k8s-storage-plane.md#discover-workers-and-devices)). The draft it produces is reviewed,
committed to Git under a name of its own with `approved: true`, and the draft in the cluster is deleted:

```bash title="Copying the draft"
kubectl -n simplyblock get clusterdeploymentconfig discovered-initial-discovery -o yaml
kubectl -n simplyblock delete clusterdeploymentconfig discovered-initial-discovery
```

```yaml title="Storage plane in Git (storage/clusterdeploymentconfig.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ClusterDeploymentConfig
metadata:
  name: simplyblock-storage
  namespace: simplyblock
spec:
  approved: true
  environment: K3s
  hostOS:
    distro: rocky
    family: RedHat
  cluster:
    name: simplyblock-cluster
    clusterMode: Standard
    enableDriveFormat: true
    maxSubsystemCount: 30
    vcpuCount: 5
    network:
      spdkOnHostNetwork: true
    stripe:
      dataChunks: 1
      parityChunks: 1
  nodeSets:
    - name: storage
      groups:
        - name: nvme
          mgmtInterface: eth0
          dataInterfaces:
            - eth1
          devices:
            nvme:
              - "0000:00:02.0"
              - "0000:00:03.0"
          workers:
            - worker-1
            - worker-2
            - worker-3
```

```yaml title="Application for the storage plane (storage-application.yaml)"
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: simplyblock-storage
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://git.example.com/platform/gitops.git
    targetRevision: main
    path: simplyblock/storage
  destination:
    server: https://kubernetes.default.svc
    namespace: simplyblock
  syncPolicy:
    automated:
      prune: false
      selfHeal: true
    syncOptions:
      - SkipDryRunOnMissingResource=true
    retry:
      limit: 10
      backoff:
        duration: 30s
        maxDuration: 5m
```

`prune: false` keeps a `ClusterDeploymentConfig` that was removed from Git in the cluster. Deleting the storage plane
stays a deliberate `kubectl delete`. `SkipDryRunOnMissingResource` and the retry cover a storage `Application` that
syncs before the operator chart has installed the CRDs.

The operator expands the document into a `StorageCluster` and its `StorageNodeSet`. Approval cannot be withdrawn, and
the cluster template is spent on that first expansion. Workers are added to an existing cluster with a further
`ClusterDeploymentConfig` that names it in `spec.clusterRef`, committed to the same path.

## Operations

`StorageClusterOps`, `StorageNodeSetOps`, `ReplicationOps`, and the other `*Ops` resources are imperative requests.
They are applied with `kubectl` and not committed to a path that an `Application` syncs with `selfHeal`, since a
completed request that Argo CD re-creates is a new request.

The chart's CRDs are installed from its `crds/` directory, which Argo CD applies on the first sync and on every sync
after that. A chart upgrade through Argo CD updates them, unlike a `helm upgrade`.

## Verification

```bash title="Checking the deployment"
kubectl -n argocd get applications
kubectl -n simplyblock get controlplane,clusterdeploymentconfig,storagecluster
```

Both `Application` resources report `Synced` and `Healthy`, the `ControlPlane` reports `Available`, and the
`StorageCluster` reports `Online`.
