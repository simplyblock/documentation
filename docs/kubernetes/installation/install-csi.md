---
title: "Connecting to an External Control Plane"
description: "Use the managed profile of the Simplyblock Operator to consume simplyblock storage from a control plane outside the Kubernetes cluster."
weight: 30200
---

The simplyblock CSI driver is deployed and managed by the Simplyblock Operator through the `SimplyblockDriver`
resource. The separate CSI Helm chart used by earlier releases is replaced by the operator chart. For a Kubernetes
cluster that does not host its own control plane, the operator chart is installed with the **managed** profile. The
chart then installs the operator and the CSI driver, and the `ControlPlane` resource points at a management API that
runs elsewhere.

!!! note
    For Kubernetes-native deployments where the control plane runs in the same cluster, use the default `standalone`
    profile described in [Install Simplyblock Operator](k8s-control-plane.md).

## CSI Driver System Requirements

The CSI driver consists of two parts:

- **Controller plugin:** Communicates with the control plane through the Management API. Runs as a StatefulSet.
- **Node plugin:** Attaches and mounts volumes. Runs as a DaemonSet on every node with pods that use simplyblock
  storage.

The workers that run the node plugin must satisfy the following requirements:

- [Linux Distributions and Versions](../../reference/supported-linux-distributions.md)
- [Linux Kernel Versions](../../reference/supported-linux-kernels.md)

## Preparing the Credentials

The managed profile needs the base URL of the remote Management API. The endpoint must not be a loopback or link-local
address. Two optional Secrets in the operator's namespace complete the connection:

- **Credentials Secret:** Holds the bearer token for the Management API under the key `token` or `secret`. Without
  it, no token is sent.
- **CA bundle Secret:** Holds the CA certificate the endpoint is verified against under the key `ca.crt` or `tls.crt`.
  Without it, the system trust store is used.

```bash title="Create the Secrets for the managed control plane"
kubectl create namespace simplyblock

kubectl -n simplyblock create secret generic cp-token \
    --from-literal=token='<MANAGEMENT-API-TOKEN>'

kubectl -n simplyblock create secret generic cp-ca \
    --from-file=ca.crt=./control-plane-ca.crt
```

A named Secret that does not exist or cannot be used is reported as an error.

## Installing With the Managed Profile

```bash title="Install the operator and CSI driver with the managed profile"
helm repo add simplyblock https://install.simplyblock.io/helm
helm repo update

helm install simplyblock-operator simplyblock/simplyblock-operator \
    --namespace simplyblock \
    --set deployment.profile=managed \
    --set controlplane.managed.endpoint=https://cp.example.com \
    --set controlplane.managed.credentialsSecretRef=cp-token \
    --set controlplane.managed.caBundleSecretRef=cp-ca
```

The chart renders the `ControlPlane` resource with a `managed` source:

```yaml title="ControlPlane with a managed source"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ControlPlane
metadata:
  name: simplyblock
  namespace: simplyblock
spec:
  source:
    managed:
      endpoint: "https://cp.example.com"
      credentialsSecretRef:
        name: cp-token
      caBundleSecretRef:
        name: cp-ca
```

The operator installs nothing for the control plane. It resolves and probes the endpoint and reports the result:

```bash title="Check the control plane connection and the CSI driver"
kubectl -n simplyblock get controlplane simplyblock
kubectl -n simplyblock get simplyblockdriver simplyblock
```

The `ControlPlane` reaches the phase `Available` once the endpoint answers. An unreachable endpoint is reported with
the event `EndpointUnreachable`. `ControlPlaneOps` actions are rejected for a managed control plane, because the
operator owns none of its workloads. The source (`local` or `managed`) cannot be changed after installation.

The TLS settings of the CSI driver come from the `tls.*` Helm values, see [Securing the Control Plane](security.md). The
`prometheus.enabled` value can be set to `false` if the remote control plane collects the metrics itself.

## Configuring the CSI Driver

The Helm values under `driver.*` are copied into the `SimplyblockDriver` resource. The most important fields are:

| Field                                             | Default              | Description                                                                                                                                                                   |
|---------------------------------------------------|----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `driverName`                                      | `csi.simplyblock.io` | The CSI driver name. Immutable.                                                                                                                                               |
| `image`                                           | Operator release     | The plugin image. Empty uses the image shipped with the operator release.                                                                                                     |
| `controllerReplicas`                              | `1`                  | Number of controller plugin instances.                                                                                                                                        |
| `nodeSelector`, `tolerations`                     |                      | Placement of the node plugin. Empty runs it on every schedulable worker.                                                                                                      |
| `controllerNodeSelector`, `controllerTolerations` |                      | Placement of the controller plugin.                                                                                                                                           |
| `enableVolumeSnapshots`                           | `true`               | Installs the VolumeSnapshotClass, and the snapshot CRDs and controller where the cluster serves none.                                                                         |
| `enableServiceAccountAuth`                        | `false`              | Authenticates the plugins with their service account tokens instead of the static cluster secret. The control plane must trust them (`controlplane.trustCSIServiceAccounts`). |
| `sidecarImages`                                   | Operator release     | Overrides for the six CSI sidecar images.                                                                                                                                     |

## Storage Clusters Behind the Managed Control Plane

Storage clusters are described by `StorageCluster` resources in the Kubernetes cluster, regardless of where the
control plane runs. A storage cluster whose storage nodes run in this Kubernetes cluster is created from an approved
`ClusterDeploymentConfig`, exactly as described in [Create a Storage Cluster](k8s-storage-plane.md).

For every `StorageCluster`, the operator writes the cluster ID, the endpoint, and the cluster secret into the Secret
`simplyblock-csi-secret-v2`, which the CSI driver reads. The Secret is maintained by the operator and does not need to
be edited manually.

## Multi-Cluster Storage Classes

The CSI driver can serve several simplyblock clusters at once. Which cluster a volume is provisioned on is selected by
the StorageClass parameters.

### Cluster ID-Based Selection

Each StorageClass names one cluster with `cluster_id` (the cluster's `status.uuid`). This is ideal for setups where
workloads are directed to specific clusters.

```yaml title="Example of cluster ID-based selection"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: simplyblock-cluster1
provisioner: csi.simplyblock.io
parameters:
  cluster_id: "<cluster-uuid-1>"
  pool_name: "<pool-name>"
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

### Zone-Aware Selection

A single StorageClass selects the cluster based on the Kubernetes zone the workload is scheduled in. The parameter
`zone_cluster_map` maps each zone to a cluster ID, and `allowedTopologies` restricts provisioning to those zones.

```yaml title="Example of zone-aware selection"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: simplyblock-zonal
provisioner: csi.simplyblock.io
parameters:
  zone_cluster_map: |
    {"us-east-1a":"<cluster-uuid-1>","us-east-1b":"<cluster-uuid-2>"}
  pool_name: "<pool-name>"
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
allowedTopologies:
  - matchLabelExpressions:
      - key: topology.kubernetes.io/zone
        values:
          - us-east-1a
          - us-east-1b
```

### Region-Aware Selection

The same approach works with regions. The parameter `region_cluster_map` maps each region to a cluster ID.

```yaml title="Example of region-aware selection"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: simplyblock-regional
provisioner: csi.simplyblock.io
parameters:
  region_cluster_map: |
    {"us-east-1":"<cluster-uuid-a>","us-west-2":"<cluster-uuid-b>"}
  pool_name: "<pool-name>"
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
allowedTopologies:
  - matchLabelExpressions:
      - key: topology.kubernetes.io/region
        values:
          - us-east-1
          - us-west-2
```

!!! tip
    The keys of `zone_cluster_map` and `region_cluster_map` must match the zone and region labels on the Kubernetes
    nodes (typically `topology.kubernetes.io/zone` and `topology.kubernetes.io/region`). Every referenced cluster ID
    must have an entry in `simplyblock-csi-secret-v2`.

For the full list of StorageClass parameters, see [Storage Class](../usage/storage-class.md).
