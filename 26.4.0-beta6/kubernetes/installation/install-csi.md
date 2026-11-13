---
title: "Connecting to an External Control Plane"
description: "Use the managed profile of the Simplyblock Operator to consume simplyblock storage from a control plane outside the Kubernetes cluster."
source: "https://docs.simplyblock.io/latest/kubernetes/installation/install-csi/"
---

# Connecting to an External Control Plane

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
- The NVMe/TCP initiator, described below.

### NVMe/TCP Initiator on Client Nodes

A node that runs application pods using simplyblock storage attaches its volumes over NVMe/TCP. Its kernel needs the
`nvme-tcp` module and native [NVMe over Fabrics multipathing](../../important-notes/terminology.md#multipathing)
(`CONFIG_NVME_MULTIPATH`). A node image that provides both, for example, Ubuntu, meets the requirement. The
platform guides ([Amazon EKS](eks.md#node-images), [GKE](gke.md#node-images)) give the node-image form for each.

!!! note "Storage and control plane nodes are not affected"
    This applies only to client nodes, the nodes that mount volumes. Storage nodes and control plane nodes do not need
    the host `nvme-tcp` module: the storage engine runs in user space, and the connections between storage nodes do not
    use the NVMe initiator of the host kernel.

Native multipathing is a property of the kernel build, and is checked on the host:

```bash title="Checking for native NVMe multipathing"
cat /sys/module/nvme_core/parameters/multipath
```

The answer must be `Y`. The tested kernels are listed in
[Supported Linux Kernels](../../reference/supported-linux-kernels.md).

The `nvme-tcp` module is often absent from a default cloud image. The Ubuntu AWS kernel ships it in the package
`linux-modules-extra-<KERNEL_VERSION>`, which the images do not install. Without the module the CSI node plugin does not
start on that node: its pod is in `CrashLoopBackOff`, the `SimplyblockDriver` reports `Degraded`, and a pod that mounts
a simplyblock volume on that node stays in `ContainerCreating`. A `Warning` event with the reason
`NVMeTCPInitiatorMissing` on the node plugin pod names the missing module and, on an Ubuntu kernel, the package to
install. After the module is loaded, the plugin starts on its next restart, and deleting the node plugin pod starts it
at once.

```bash title="Finding the node plugin pods that do not start"
kubectl get pods -n <NAMESPACE> -o wide | grep csi-node
kubectl describe pod -n <NAMESPACE> <CSI_NODE_POD>
```

The package is installed, the module loaded, and the load persisted across reboots, before the node joins the cluster:

```bash title="Installing the NVMe/TCP initiator"
apt-get install -y linux-modules-extra-$(uname -r)   # Ubuntu
echo nvme-tcp > /etc/modules-load.d/nvme-tcp.conf
modprobe nvme-tcp
```

RHEL 9 and its derivatives ship the module in `kernel-modules-core`, which is always installed, so only the load is
persisted there. Baking these steps into the node image or the node
group's bootstrap configuration gives every new node the module before it joins the cluster.

## Exposing the Management API of the Storage Cluster

The consumer cluster reaches the storage cluster's Management API over the network, so the Management API has to be
exposed outside the storage cluster, such as through an ingress controller or a load balancer. The exposed
endpoint must meet two conditions:

- **Its certificate is trusted by the consumer cluster.** The Management API's own certificate names only its
  in-cluster Service, so the exposed endpoint serves a certificate for its external hostname. With the installation
  below, the CSI driver verifies that certificate against the system trust store of its image, so a publicly
  trusted certificate is required.
- **It satisfies the Management API's mutual TLS, when that is on.** With `tls.mutual_enabled` set on the storage
  cluster, which is the default, the Management API accepts only clients that present a certificate issued by the
  storage cluster's CA. The exposing component then connects to it with such a client certificate, as described below.
  With mutual TLS off, the exposing component connects without a client certificate.

The endpoint answers with `204` once it is reachable:

```bash title="Check the exposed Management API"
curl -sS -o /dev/null -w '%{http_code}\n' https://storage-api.example.com/api/v2/_meta/ready
```

### Presenting a Client Certificate to the Management API

This applies only while mutual TLS is on in the storage cluster. The exposing component terminates the consumer
cluster's TLS connection and opens its own HTTPS connection to the Management API, on which it presents a client
certificate issued by the storage cluster's CA. TLS passthrough does not work here, because the consumer cluster has
no certificate from that CA.

```plain title="The two TLS connections"
consumer cluster                          storage cluster
┌────────────────────┐   hop 1   ┌──────────────────────────┐   hop 2   ┌─────────────────────────┐
│ CSI driver,        │ ───────▶  │ ingress (Traefik, nginx) │ ───────▶  │ simplyblock-webappapi   │
│ operator           │  HTTPS    │                          │  HTTPS +  │ :5000 (mutual TLS)      │
└────────────────────┘           └──────────────────────────┘  client   └─────────────────────────┘
                                                               cert
```

- **Hop 1, from the consumer cluster to the ingress:** ordinary HTTPS. The ingress presents its publicly trusted
  certificate, and the consumer cluster presents none. The consumer cluster authenticates to the Management API with
  the storage cluster's cluster secret, which the CSI driver sends with every request and the ingress passes on.
- **Hop 2, from the ingress to the Management API:** HTTPS with mutual TLS. The ingress presents the client
  certificate below, and verifies the Management API against the storage cluster's CA.

The client certificate stays in the storage cluster: only the ingress reads it, and the consumer cluster never needs
it.

!!! warning
    Behind the ingress, mutual TLS no longer identifies the remote caller. Any client that reaches the exposed
    endpoint is passed on with the ingress's certificate, and access to the Management API rests on the cluster
    secret. Where possible, restrict the exposed endpoint to the networks of the consumer clusters.

The client certificate is issued in the storage cluster by cert-manager, which also renews it:

```yaml title="Client certificate for the exposing component (storage cluster)"
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: webappapi-ingress-client
  namespace: simplyblock
spec:
  commonName: webappapi-ingress-client
  secretName: webappapi-ingress-client-tls
  usages: [digital signature, key encipherment, client auth]
  issuerRef:
    kind: ClusterIssuer
    name: simplyblock-certificate-authority-issuer
```

The exposing component is then configured to connect to the Service `simplyblock-webappapi` on port 5000 over HTTPS,
with these settings for its connection to the backend:

| Setting            | Value                                                               |
|--------------------|---------------------------------------------------------------------|
| Client certificate | The Secret `webappapi-ingress-client-tls` (`tls.crt` and `tls.key`) |
| Trusted CA         | The Secret `simplyblock-ca-bundle-tls` (`ca.crt`)                   |
| Server name        | `simplyblock-webappapi.simplyblock.svc`                             |

Where these settings are made depends on the ingress controller. Traefik takes them in a `ServersTransport`
(`certificatesSecrets`, `rootCAs`, and `serverName`) referenced by the route's service. ingress-nginx takes them in
the annotations `nginx.ingress.kubernetes.io/backend-protocol: HTTPS`, `proxy-ssl-secret`, `proxy-ssl-verify`, and
`proxy-ssl-name`. Other proxies and load balancers configure them as upstream or backend TLS.

## Collecting the Storage Cluster Details

The consumer cluster needs the storage cluster's ID, its cluster secret, and the name of a storage pool. All three
are read in the storage cluster:

```bash title="Read the cluster ID, the cluster secret, and the pool name (storage cluster)"
kubectl -n simplyblock get secret simplyblock-csi-secret-v2 \
    -o jsonpath='{.data.secret\.json}' | base64 -d

kubectl -n simplyblock get storagepool
```

The first command prints `cluster_id` and `cluster_secret`. The cluster secret is a credential and is best kept in a
secret store, such as Sealed Secrets or External Secrets, rather than in a Git repository.

Every worker of the consumer cluster that runs pods with simplyblock volumes must reach the storage nodes'
data-network addresses on the NVMe/TCP ports (4420 and up):

```bash title="Check NVMe/TCP access from a consumer worker"
nvme discover -t tcp -a <STORAGE-NODE-DATA-IP> -s <PORT>
```

## Installing With the Managed Profile

```bash title="Install the operator and CSI driver with the managed profile (consumer cluster)"
helm repo add simplyblock https://install.simplyblock.io/helm
helm repo update

helm install simplyblock-operator simplyblock/simplyblock-operator \
    --namespace simplyblock --create-namespace \
    --set deployment.profile=managed \
    --set controlplane.managed.endpoint=https://storage-api.example.com \
    --set tls.enabled=false \
    --set tls.mutual_enabled=false \
    --set externallyManagedSecret.create=true \
    --set csiConfig.simplybk.uuid=<CLUSTER-ID> \
    --set csiConfig.simplybk.ip=https://storage-api.example.com \
    --set csiSecret.simplybk.secret=<CLUSTER-SECRET>
```

| Helm value                                         | Purpose                                                                                                       |
|----------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| `deployment.profile=managed`                       | Installs the operator and the CSI driver, and no control plane.                                               |
| `controlplane.managed.endpoint`                    | The Management API of the storage cluster, as exposed by the ingress.                                         |
| `tls.enabled`, `tls.mutual_enabled`                | The CSI driver verifies the ingress certificate against the system trust store instead of a cluster-local CA. |
| `externallyManagedSecret.create`                   | Writes the Secret `simplyblock-csi-secret-v2`, from which the CSI driver reads the storage cluster.           |
| `csiConfig.simplybk.uuid`, `csiConfig.simplybk.ip` | The storage cluster's ID and the endpoint of its Management API.                                              |
| `csiSecret.simplybk.secret`                        | The storage cluster's cluster secret.                                                                         |

If cert-manager runs in a namespace other than `cert-manager`, `tls.cert-manager.namespace` names it.

Two optional Secrets in the operator's namespace can be named for the `ControlPlane` connection:

- **Credentials Secret** (`controlplane.managed.credentialsSecretRef`): holds the bearer token for the Management
  API under the key `token` or `secret`. Without it, no token is sent.
- **CA bundle Secret** (`controlplane.managed.caBundleSecretRef`): holds the CA certificate the endpoint is
  verified against under the key `ca.crt` or `tls.crt`. Without it, the system trust store is used, which is the
  right choice for a publicly trusted ingress certificate.

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
      endpoint: "https://storage-api.example.com"
```

The operator installs nothing for the control plane. It resolves and probes the endpoint and reports the result:

```bash title="Check the control plane connection and the CSI driver"
kubectl -n simplyblock get controlplane simplyblock
kubectl -n simplyblock get simplyblockdriver simplyblock
```

The `ControlPlane` reaches the phase `Available` once the endpoint answers, and the `SimplyblockDriver` reaches
`Ready` once every node plugin runs. An unreachable endpoint is reported with the event `EndpointUnreachable`.
`ControlPlaneOps` actions are rejected for a managed control plane, because the operator owns none of its workloads.
The source (`local` or `managed`) cannot be changed after installation.

The `prometheus.enabled` value can be set to `false` if the remote control plane collects the metrics itself.

## Creating a Storage Class and a Test Volume

```yaml title="StorageClass for the remote storage cluster"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: simplyblock
provisioner: csi.simplyblock.io
parameters:
  cluster_id: "<CLUSTER-ID>"
  pool_name: "<POOL-NAME>"
  csi.storage.k8s.io/fstype: xfs
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

```yaml title="Test volume and pod"
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: simplyblock-test
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: simplyblock
  resources:
    requests:
      storage: 1Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: simplyblock-test
spec:
  containers:
    - name: test
      image: busybox:1.36
      command: [sh, -c, "echo hello > /data/f && cat /data/f && sleep 3600"]
      volumeMounts:
        - name: data
          mountPath: /data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: simplyblock-test
```

The claim reaches `Bound`, and `kubectl logs simplyblock-test` prints `hello`.

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
`simplyblock-csi-secret-v2`, which the CSI driver reads. A consumer cluster that only uses a remote storage cluster
has no `StorageCluster`, and the Secret is written from the Helm values described in
[Installing With the Managed Profile](#installing-with-the-managed-profile).

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
