---
title: "Disaster Recovery Requirements"
description: "Requirements for simplyblock Disaster Recovery: hub cluster sizing, Kubernetes versions, site cluster prerequisites, S3 buckets, networking, and site labeling."
weight: 29980
---

Simplyblock Disaster Recovery (DR) consists of a hub cluster, which holds the DR configuration and drives every
action, and two or more site clusters, which run the applications and the simplyblock storage. This page lists the
requirements for the hub, the sites, the S3 object storage, and the network between them, as well as the node labels
that assign nodes to sites. A checklist at the end summarizes the preparation. The architectures that these
requirements apply to are described in [Deployment Architectures](deployment-architectures.md).

## Hub Cluster

The DR hub runs the Open Cluster Management (OCM) hub, the Ramen hub operator, and dr-hub. It is deployed on a
separate Kubernetes cluster, not on one of the site clusters, so that the loss of a site never takes the DR control
point with it.

!!! info "Coming soon"
    Once the hub deployment of the Simplyblock Operator and control plane is released, the same hub cluster can also
    host the centralized simplyblock storage management. See
    [Control Plane and Operator](../architecture/deployment-topologies/control-plane-and-operator.md).

### High Availability

The hub requires at least three nodes. Three nodes are needed for:

- **Control plane quorum:** The Kubernetes API server and etcd of the hub must survive the loss of one node.
- **Availability of dr-hub:** dr-hub runs as a leader-elected Deployment. If its node fails, the pod is rescheduled to
  another node, and a replacement leader takes over. The replica count can be raised with the `hub.replicas` Helm
  value.
- **Webhook availability:** dr-hub validates every DR object through admission webhooks with the failure policy
  `Fail`. While dr-hub is unavailable, no DR object (protection plan, DR path, protected application, recovery
  action, or test) can be created or changed.

While the hub is unavailable, protected applications keep running and replicating on the sites, but no DR action can
be started. A lost hub is rebuilt from its signed state bundle in S3. See
[Hub Recovery](../disaster-recovery/operations/hub-recovery.md).

### Deployment Options

The hub can be deployed on any infrastructure that meets the requirements on this page:

- **Virtual machines:** A three-node Kubernetes or OpenShift cluster on virtual machines is the most common choice.
  The hub does not serve storage and does not need NVMe devices.
- **Bare metal:** A small bare-metal cluster works in the same way.
- **Hosted control planes (HyperShift):** A hub that runs as a HyperShift hosted cluster is supported as a
  deployment option, as long as the requirements on this page are met, in particular, the signing of client
  certificate requests (see [Kubernetes Versions and Distributions](#kubernetes-versions-and-distributions)). The
  hosted API server must be reachable from all sites, and the node pool must provide at least three worker nodes.

### Sizing

The DR design does not define fixed hub sizes. The following numbers are **initial recommendations**. The resource
requests are taken from the Helm chart and the bundled manifests. The per-node numbers are guidance and have to be
validated against the number of protected applications and sites.

| Component                                                          | Namespace                     | CPU request | Memory request | Memory limit     | Source                                             |
|--------------------------------------------------------------------|-------------------------------|-------------|----------------|------------------|----------------------------------------------------|
| OCM cluster-manager (registration-operator)                        | `open-cluster-management`     | 2m          | 16Mi           | none             | Bundled manifest                                   |
| OCM hub controllers (registration, work, placement, addon-manager) | `open-cluster-management-hub` | OCM default | OCM default    | none             | ClusterManager with `resourceRequirement: Default` |
| Governance policy addon controller                                 | `open-cluster-management`     | 10m         | 64Mi           | 128Mi (CPU 500m) | Bundled manifest                                   |
| Governance policy propagator                                       | `open-cluster-management`     | not set     | not set        | none             | Bundled manifest                                   |
| ocm-controller                                                     | `open-cluster-management`     | 100m        | 256Mi          | 4Gi              | Bundled manifest                                   |
| Ramen hub operator                                                 | `ramen-system`                | 100m        | 200Mi          | 300Mi (CPU 100m) | Bundled manifest                                   |
| dr-hub                                                             | `dr-simplyblock`              | 50m         | 128Mi          | 512Mi            | Helm value `hub.resources`                         |
| DR console (UI)                                                    | -                             | -           | -              | -                | Not part of the hub chart                          |
| Prometheus                                                         | -                             | -           | -              | -                | Not bundled, an existing Prometheus scrapes dr-hub |

The requests of these components are small. The dominant consumers on a hub are the Kubernetes control plane itself
(API server and etcd), which serves all ManifestWorks, ManagedClusterViews, and DR objects, and a Prometheus instance
if one runs on the hub.

| Per-node sizing       | vCPU | RAM    | Local disk      |
|-----------------------|------|--------|-----------------|
| Minimum (DR-only hub) | 4    | 16 GiB | 100 GiB         |
| Recommended           | 8    | 32 GiB | 100 GiB or more |

The reference test hub used three nodes with 8 vCPU and 32 GiB each. On the sites, the dr-agent requests 20m CPU and
64Mi memory (limit 256Mi), in addition to Velero, the Ramen DR cluster operator, and the OCM agents.

### etcd

All DR state lives in the etcd of the hub. For etcd:

- **Fast local disks:** Use SSD or NVMe-backed local disks with low write latency for the etcd members.
- **Object size:** DR objects are kept below about 1.5 MB, the default etcd request size limit.
- **Retention:** Finished recovery actions and tests are kept for 90 days by default, and at least the last 10 per
  application, before they are pruned. With an S3 archive, older runs are pruned only once archived. The retention is
  configured in the `DRConfig` resource.

## Kubernetes Versions and Distributions

| Requirement             | Hub                                                           | Sites                                                                                                |
|-------------------------|---------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| Kubernetes version      | 1.30 or later                                                 | 1.30 or later, and the simplyblock requirements in [Software Requirements](software-requirements.md) |
| OpenShift               | Supported (primary target)                                    | Supported (primary target), including OpenShift Virtualization                                       |
| Upstream Kubernetes     | Supported, for example, RKE2, K3s, and kubeadm-based clusters | Supported, for example, RKE2, K3s, and kubeadm-based clusters                                        |
| Amazon EKS              | Not supported                                                 | Supported                                                                                            |
| Existing ACM or ODF hub | Supported with the bundled bootstrap disabled                 | -                                                                                                    |

Both Helm charts (hub and site) require Kubernetes 1.30 or later. Upstream Kubernetes with KubeVirt, Multus, and
MetalLB is supported for virtual machine workloads next to OpenShift Virtualization.

!!! warning "Amazon EKS cannot be the hub"
    OCM registers every site with a client certificate that the hub's API server signs
    (`kubernetes.io/kube-apiserver-client` certificate signing requests). The hub distribution must therefore sign
    these requests. Amazon EKS does not, so it cannot host the hub. Sites on Amazon EKS are supported.

The hub installs pinned versions of its dependencies. Installing never downloads anything, and all images can be
mirrored into a private registry with the `bootstrap.imageRegistry` Helm value.

| Component                    | Version                                                                    |
|------------------------------|----------------------------------------------------------------------------|
| Open Cluster Management      | 1.3.1                                                                      |
| Governance policy addon      | 0.18.0                                                                     |
| Ramen                        | Pinned image digest                                                        |
| External snapshotter (sites) | 8.6.0                                                                      |
| csi-addons (sites)           | 0.14.0                                                                     |
| Velero (sites)               | 1.16.1, with velero-plugin-for-aws 1.12.0 and kubevirt-velero-plugin 0.8.0 |

On a hub that already runs Red Hat Advanced Cluster Management (ACM) and OpenShift Data Foundation (ODF) DR, the
bundled OCM and Ramen installation is disabled (`bootstrap.enabled: false`). Protection plans then reference an
existing Ramen S3 profile. See [Install the Hub](../disaster-recovery/install/hub.md).

## Site Cluster Requirements

Every site cluster must provide:

- **Simplyblock with CSI replication support:** The simplyblock CSI driver with support for csi-addons
  VolumeReplication (and VolumeGroupReplication when consistency groups are used).
- **Unique cluster name:** Every site joins the hub under a cluster name that is unique on the hub. The same name is
  used in the protection plans and must be reused when a site rejoins after a hub recovery.
- **Hub reachability:** Outbound HTTPS access to the hub API server (see [Networking](#networking)).
- **Optional KubeVirt:** KubeVirt or OpenShift Virtualization for protecting virtual machines.
- **Optional Multus network attachment for tests:** An isolated NetworkAttachmentDefinition without uplink for test
  bubbles of virtual machines with secondary networks.
- **Identical names on both sites:** Applications recover exactly as captured. Network attachment definitions,
  storage class names, and zone names that applications reference must exist with the same names on the target site.

The following components are installed on every site by the DR hub after the site joins, so they must not be
preinstalled in conflicting versions:

- **Snapshot support:** External snapshotter with the snapshot CRDs and group snapshots.
- **Replication add-ons:** The csi-addons controller and CRDs for VolumeReplication, VolumeGroupReplication, and NetworkFence.
- **Recipe CRD and Ramen DR cluster operator.**
- **Velero:** Including the AWS and KubeVirt plugins.

Single components can be left out if they already exist on a site. See
[Join Sites](../disaster-recovery/install/sites.md).

## S3 Requirements for Disaster Recovery

Simplyblock DR stores application metadata, backups, reports, and hub state in S3. Any S3-compatible object store
can be used.

| Bucket                       | Content                                                                                           | Accessed by                                   |
|------------------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------|
| One or more buckets per site | Ramen metadata of protected volumes, Velero captures of Kubernetes objects, `snapshot-s3` backups | Hub and all sites                             |
| Archive bucket               | Action and test reports (JSON and PDF), signed hub state bundles                                  | Hub, and the restore tooling after a hub loss |

Every bucket needs:

- **Endpoint and region:** An S3-compatible endpoint (host and port) and a region.
- **Credentials:** AWS-style access keys (access key ID and secret access key), stored as Kubernetes Secrets.
- **Optional CA:** A CA certificate for endpoints with a private certificate authority.
- **Reachability:** The per-site buckets must be reachable from the hub and from all sites, and the archive bucket
  from the hub and from the location of a hub rebuild.

For ransomware resilience and a recoverable hub, the buckets should additionally use:

- **Versioning and object lock:** Enable versioning and object lock in compliance mode. The hub state bundles are
  protected with compliance-mode object lock for their retention period, and reports can be protected in the same
  way. The basic DR functions work without object lock, but recovering the hub after a ransomware attack needs it.
- **Server-side encryption:** Enable server-side encryption (SSE) on all buckets.
- **Separate credentials:** Use write-only credentials for the hub and for the sites, and keep a separate read-only
  restore credential offline, together with the public key that verifies the state bundles.
- **Separate location:** Place the archive bucket where it survives the loss of the hub and of every site.

The archive and bundle signing are configured in [Archive](../disaster-recovery/install/archive.md).

## S3 Requirements for Simplyblock Backups

Independent of DR, simplyblock backs up volumes at the storage level to S3 (see
[Backup and Recovery](../kubernetes/operations/data-protection/backup-recovery.md)). These backups are configured per
storage cluster in the `backup` section of the `StorageCluster`:

| Parameter         | Requirement                                                                                                                                                                                                  |
|-------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Endpoint          | `backup.endpoint`: any S3-compatible endpoint URL (Amazon S3, MinIO, or others). Loopback and link-local addresses are refused.                                                                              |
| Bucket and prefix | `backup.bucket` and optional `backup.prefix`. Several storage clusters can share a bucket with different prefixes. Backups of every cluster under the same bucket and prefix become visible to each of them. |
| Region            | `backup.region`, for endpoints that do not imply one.                                                                                                                                                        |
| Credentials       | `backup.credentialsSecretRef`: a Secret with `access_key_id` and `secret_access_key` in the namespace of the `StorageCluster`.                                                                               |
| Reachability      | The storage nodes of the cluster must reach the endpoint. For a cross-cluster restore, the storage nodes of the target cluster must also reach the bucket of the source cluster.                             |

## Networking

The hub and the sites communicate only through OCM, and every connection is opened from the site to the hub. The hub
never opens a connection to a site and does not store a kubeconfig of any site.

| Source                                      | Destination                               | Port                         | Protocol | Purpose                             |
|---------------------------------------------|-------------------------------------------|------------------------------|----------|-------------------------------------|
| Hub API server                              | dr-hub webhook Service                    | 9443                         | HTTPS    | Admission webhooks for DR objects   |
| Prometheus                                  | dr-hub metrics                            | 8443                         | HTTPS    | DR metrics                          |
| Kubelet (hub)                               | dr-hub                                    | 8081                         | HTTP     | Liveness and readiness probes       |
| OCM klusterlet and addon agents (each site) | Hub API server                            | 6443 or 443                  | HTTPS    | Registration, ManifestWorks, status |
| Sites and hub                               | S3 endpoints                              | 443 (or the endpoint's port) | HTTPS    | Metadata, backups, reports, bundles |
| Storage nodes (each storage cluster)        | Storage nodes of the peer storage cluster | 4420-4499                    | NVMe/TCP | Storage-level replication           |

Within the hub, the standard Kubernetes cluster networking applies. The port of the hub API server depends on the
distribution: 6443 for most distributions, 443 for many managed and hosted API endpoints.

For storage-level replication, the storage clusters of the sites need network connectivity between their storage
nodes, and between the storage nodes and the control plane they are attached to. The ports are listed in the network
port table of [Kubernetes Storage Plane Installation](../kubernetes/installation/k8s-storage-plane.md#networking). The
prerequisites of the replication relationship itself are described in
[Asynchronous Replication](../kubernetes/operations/data-protection/asynchronous-replication.md).

### Latency

Synchronous (metro) replication adds the round-trip time between the sites to every write. The DR design sets no
hard limit. As guidance, metro distances with a low single-digit millisecond round-trip time between the sites are
recommended. Asynchronous replication has no latency requirement, but the bandwidth must be sufficient to transfer the
changes of one scheduling interval within that interval.

### DNS, GSLB, and Load Balancers

After a failover or relocation, clients have to reach the application at its new site. In the current release, the
switch of DNS records, global server load balancing (GSLB), and virtual IP addresses is performed by external
postTargetReady hooks. See [Site Profiles](../disaster-recovery/configuration/site-profiles.md).

## Assigning Nodes to Sites

Sites and zones are identified by the standard Kubernetes topology labels on the nodes:

- **`topology.kubernetes.io/zone`:** The zone of a node, for example, a datacenter room or availability zone.
- **`topology.kubernetes.io/region`:** The region of a node, for example, a city or cloud region.

Cloud providers set these labels automatically. On premises, they are set by the administrator.

```bash title="Labeling a node with its zone and region"
kubectl label node worker-1.example.com \
    topology.kubernetes.io/zone=fra-a \
    topology.kubernetes.io/region=eu-central
```

In a protection plan, every site optionally records the `zone` and `region` of its nodes. A combination of cluster
and zone may appear only once in a plan.

### Stretched Storage Cluster

For a storage cluster stretched across two sites (metro DR), simplyblock must know which storage nodes belong to
which site, so that it places data chunks, journal copies, and failover paths across the sites. This is done with
failure domains. The deployment document of the storage cluster sets `spec.cluster.enableFailureDomains: true`, and
every node group names its `failureDomain`. A discovery run seeds the domain of each worker from its
`topology.kubernetes.io/zone` label, so labeling the storage workers per site before discovery yields a matching
draft.

```yaml title="Example of storage workers split across two sites with two failure domains each"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ClusterDeploymentConfig
metadata:
  name: simplyblock-deployment
  namespace: simplyblock
spec:
  approved: false
  cluster:
    name: simplyblock-cluster
    stripe:
      dataChunks: 2
      parityChunks: 2
    enableFailureDomains: true
  nodeSets:
    - name: site-a-1
      groups:
        - name: default
          failureDomain: site-a-1
          workers: [site-a-worker-1.example.com, site-a-worker-2.example.com]
          devices:
            nvme: ["0000:01:00.0", "0000:02:00.0"]
          journalManager:
            count: 4
    - name: site-a-2
      groups:
        - name: default
          failureDomain: site-a-2
          workers: [site-a-worker-3.example.com, site-a-worker-4.example.com]
          devices:
            nvme: ["0000:01:00.0", "0000:02:00.0"]
          journalManager:
            count: 4
    - name: site-b-1
      groups:
        - name: default
          failureDomain: site-b-1
          workers: [site-b-worker-1.example.com, site-b-worker-2.example.com]
          devices:
            nvme: ["0000:01:00.0", "0000:02:00.0"]
          journalManager:
            count: 4
    - name: site-b-2
      groups:
        - name: default
          failureDomain: site-b-2
          workers: [site-b-worker-3.example.com, site-b-worker-4.example.com]
          devices:
            nvme: ["0000:01:00.0", "0000:02:00.0"]
          journalManager:
            count: 4
```

To survive the loss of a whole site, the failure domains of one site must fit within the parity budget of the erasure
coding scheme. For example, with four failure domains (two per site) and two parity chunks (`1+2` or `2+2`), the loss
of two whole domains, and therefore of one site, is tolerated. The activation rules and the tolerance table are in
[Failure Domains](../architecture/concepts/failure-domains.md), and the configuration steps in
[Managing Failure Domains](../kubernetes/operations/cluster/failure-domains.md).

## Checklist

- A separate hub cluster with at least three nodes is available (virtual machines, bare metal, or HyperShift).
- The hub runs Kubernetes 1.30 or later and signs `kubernetes.io/kube-apiserver-client` certificate requests (not
  Amazon EKS).
- The hub nodes meet the sizing recommendation, and etcd runs on fast local disks.
- Every site runs Kubernetes 1.30 or later and meets the simplyblock software and hardware requirements.
- The simplyblock CSI driver on every site supports csi-addons replication.
- Every site has a unique cluster name.
- Network attachment definitions, storage class names, and zone names used by applications are identical on
  source and target sites.
- Per-site S3 buckets and an archive bucket exist, reachable from the hub and all sites, with credentials.
- Versioning, object lock (compliance mode), and server-side encryption are enabled on the buckets.
- Write-only credentials are issued to the hub and sites, and a read-only restore credential and the bundle
  public key are stored offline.
- The S3 backup target of each storage cluster is reachable from its storage nodes (for simplyblock backups).
- Every site reaches the hub API server over HTTPS (6443 or 443). No inbound connection to the sites is needed.
- The storage clusters that replicate have network connectivity on the simplyblock storage ports.
- For metro DR, the round-trip time between the sites is in the low single-digit milliseconds, and the storage
  workers are assigned to failure domains per site.
- Nodes carry `topology.kubernetes.io/zone` and `topology.kubernetes.io/region` labels.
- A mirror registry is configured if the hub and sites have no internet access.
