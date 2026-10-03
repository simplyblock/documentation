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
- **Availability of dr-hub:** If the node of dr-hub fails, the pod is rescheduled to another node. The replica count can be raised with the `hub.replicas` Helm
  value.
- **Webhook availability:** dr-hub validates every DR object. While dr-hub is unavailable, no DR object (protection plan, DR path, protected application, recovery
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

No fixed hub sizes are defined. The following numbers are **initial recommendations**. The resource
requests are taken from the Helm chart and the bundled manifests. The per-node numbers are guidance and have to be
validated against the number of protected applications and sites.

| Component                                                          | Namespace                     | CPU request | Memory request | Memory limit     |
|--------------------------------------------------------------------|-------------------------------|-------------|----------------|------------------|
| OCM cluster-manager (registration-operator)                        | `open-cluster-management`     | 2m          | 16Mi           | none             |
| OCM hub controllers (registration, work, placement, addon-manager) | `open-cluster-management-hub` | OCM default | OCM default    | none             |
| Governance policy addon controller                                 | `open-cluster-management`     | 10m         | 64Mi           | 128Mi (CPU 500m) |
| Governance policy propagator                                       | `open-cluster-management`     | not set     | not set        | none             |
| ocm-controller                                                     | `open-cluster-management`     | 100m        | 256Mi          | 4Gi              |
| Ramen hub operator                                                 | `ramen-system`                | 100m        | 200Mi          | 300Mi (CPU 100m) |
| dr-hub                                                             | `dr-simplyblock`              | 50m         | 128Mi          | 512Mi            |
| DR console (UI)                                                    | -                             | -           | -              | -                |
| Prometheus                                                         | -                             | -           | -              | -                |

The requests of these components are small. The dominant consumers on a hub are the Kubernetes control plane itself
(API server and etcd) and a Prometheus instance if one runs on the hub.

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

| Component               | Version                                                                    |
|-------------------------|----------------------------------------------------------------------------|
| Open Cluster Management | 1.3.1                                                                      |
| Governance policy addon | 0.18.0                                                                     |
| Ramen                   | Pinned image digest                                                        |
| Velero (sites)          | 1.16.1, with velero-plugin-for-aws 1.12.0 and kubevirt-velero-plugin 0.8.0 |

On a hub that already runs Red Hat Advanced Cluster Management (ACM) and OpenShift Data Foundation (ODF) DR, the
bundled OCM and Ramen installation is disabled (`bootstrap.enabled: false`). Protection plans then reference an
existing Ramen S3 profile. See [Install the Hub](../disaster-recovery/install/hub.md).

## Site Cluster Requirements

Every site cluster must provide:

- **Simplyblock with CSI replication support:** The simplyblock CSI driver with support for csi-addons
  VolumeReplication (and VolumeGroupReplication when consistency groups are used).
- **Snapshot support:** The external snapshot controller with the VolumeSnapshot and VolumeGroupSnapshot CRDs. They
  are part of every simplyblock installation: the Simplyblock Operator Helm chart installs them by default
  (`snapshotcontroller.create`), independent of DR.
- **csi-addons:** The csi-addons controller and CRDs, which the simplyblock CSI driver uses for replication, fencing,
  and space reclamation. They are installed together with simplyblock storage, independent of DR.
- **Unique cluster name:** Every site joins the hub under a cluster name that is unique on the hub. The same name is
  used in the protection plans and must be reused when a site rejoins after a hub recovery.
- **Hub reachability:** Outbound HTTPS access to the hub API server (see [Networking](#networking)).
- **Optional KubeVirt:** KubeVirt or OpenShift Virtualization for protecting virtual machines.
- **Optional Multus network attachment for tests:** An isolated NetworkAttachmentDefinition without uplink for test
  bubbles of virtual machines with secondary networks.
- **Identical names on both sites, except VM networks:** The site mapper translates the Multus network attachments
  and guest addresses of virtual machines between the sites (see
  [Site Profiles and Mappings](../disaster-recovery/configuration/site-profiles.md)). Everything else recovers as
  captured: storage class names, zone names, and other classes that applications reference must exist with the same
  names on the target site.

The following components are installed on every site by the DR hub after the site joins, so they must not be
preinstalled in conflicting versions:

- **Recipe CRD and Ramen DR cluster operator.**
- **Velero:** Including the AWS and KubeVirt plugins.

Single components can be left out if they already exist on a site. The site stack also contains a snapshot
controller and csi-addons, which are not needed on a simplyblock site and are left out when the site joins. See
[Join Sites](../disaster-recovery/install/sites.md).

## S3 Buckets

A disaster recovery setup uses two kinds of S3 buckets. They hold different data, serve different recovery cases, and
are configured in different places. The storage-level backups of a simplyblock storage cluster, described in
[Backup and Recovery](../kubernetes/operations/data-protection/backup-recovery.md), are independent of DR.

| Bucket             | Content                                                                                                          | Used for                                                                                                                              | Configured in | Configured when |
|--------------------|------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|---------------|-----------------|
| DR metadata bucket | Kubernetes objects of protected applications, volume metadata, and the volume backups of the backup method types | Restoring the application objects on the target site during a failover, relocation, or test, and restoring volumes after a total loss |               |                 |
| Archive bucket     | Signed DR state bundles of the hub, and the reports of all recovery actions and tests                            | Rebuilding a lost hub, recovery after a cyberattack, and audit                                                                        |               |                 |

The buckets can be served by the same object store, but they should not be the same bucket. The archive bucket in
particular belongs in a location that survives the loss of the hub and of every site.

### DR Metadata Buckets

Every site of a protection plan names a DR metadata bucket. One bucket with one credential can serve all sites of all
plans, and this is the simplest setup. Separate buckets per site or per plan are possible as well. During a failover or
relocation, the Kubernetes objects of the application are restored from it on the target site, and tests read from it
as well. With a backup method type, the storage writes the backups of the site's primary volumes into the site's
store, so a plan with such a method declares its stores per site (`spec.s3Profiles`).

- **Configuration:** Declared per site in the protection plan (`spec.s3Profiles` with bucket, endpoint, region, and
  credential Secret), or referenced as an existing profile (`spec.s3Profile`). The credential Secret is created by the
  hub chart from `s3Credentials` and distributed to the sites by the hub, so the sites need no credentials of their
  own. See [Install the Hub](../disaster-recovery/install/hub.md)
  and [Protection Plans](../disaster-recovery/configuration/protection-plans.md#s3-profiles).
- **Reachability:** From the hub and from every site of the plan.
- **Location:** Outside the protected sites, or at least not only at one of them, since the bucket is needed after
  the loss of a site.

### Archive Bucket

The hub has one archive bucket. It holds the signed state bundles from which a lost hub is rebuilt, and the JSON and
PDF report of every finished recovery action and test. It is the bucket that must survive a cyberattack on the hub
and the sites, and therefore the one that needs object lock.

- **Configuration:** In the hub chart under `drConfig.spec.archive`, with its own credential Secret and the bundle
  signing key. See [Archive and State Bundle](../disaster-recovery/install/archive.md).
- **Reachability:** From the hub, and from the location where a lost hub is rebuilt.

### Simplyblock Backup Buckets

Simplyblock storage clusters back up volumes as incremental copy-on-write snapshots to S3, independent of DR (see
[Backup and Recovery](../kubernetes/operations/data-protection/backup-recovery.md)). The backup method types of a
protection plan use the same mechanism, but with the site's DR metadata store as the target and the interval and
retention of the method, so no separate bucket is needed for DR.

## Networking

Every connection between the hub and the sites is opened from the site to the hub. The hub
never opens a connection to a site and does not store a kubeconfig of any site.

| Direction                                                   | Source                                      | Destination                               | Port                         | Protocol | Purpose                                                                         |
|-------------------------------------------------------------|---------------------------------------------|-------------------------------------------|------------------------------|----------|---------------------------------------------------------------------------------|
| Within the hub cluster, between nodes                       | Hub API server                              | dr-hub webhook Service                    | 9443                         | HTTPS    | Admission webhooks for DR objects                                               |
| Within the hub cluster, between nodes                       | Prometheus                                  | dr-hub metrics                            | 8443                         | HTTPS    | DR metrics                                                                      |
| Within the hub cluster, between nodes                       | Kubelet (hub)                               | dr-hub                                    | 8081                         | HTTP     | Liveness and readiness probes                                                   |
| Between clusters: egress from each site, ingress to the hub | OCM klusterlet and addon agents (each site) | Hub API server                            | 6443 or 443                  | HTTPS    | Registration, status, and DR tasks                                              |
| Egress from the hub and every site                          | Hub and sites                               | DR metadata buckets                       | 443 (or the endpoint's port) | HTTPS    | Application objects, volume metadata, volume backups of the backup method types |
| Egress from the hub                                         | Hub                                         | Archive bucket                            | 443 (or the endpoint's port) | HTTPS    | State bundles and reports                                                       |
| Egress from the storage nodes of each site                  | Storage nodes                               | DR metadata buckets                       | 443 (or the endpoint's port) | HTTPS    | Volume backups of the backup method types                                       |
| Between clusters: site to site, both directions             | Storage nodes (each storage cluster)        | Storage nodes of the peer storage cluster | 4420-4499                    | NVMe/TCP | Storage-level replication                                                       |

No ingress into a site cluster is needed from the hub. A site only accepts inbound connections from the storage
nodes of its peer storage cluster, for replication.

Within the hub, the standard Kubernetes cluster networking applies. The port of the hub API server depends on the
distribution: 6443 for most distributions, 443 for many managed and hosted API endpoints.

For storage-level replication, the storage clusters of the sites need network connectivity between their storage
nodes, and between the storage nodes and the control plane they are attached to. The ports are listed in the network
port table of [Kubernetes Storage Plane Installation](../kubernetes/installation/k8s-storage-plane.md#networking). The
prerequisites of the replication relationship itself are described in
[Asynchronous Replication](../kubernetes/operations/data-protection/asynchronous-replication.md).

### Latency

Synchronous (metro) replication adds the round-trip time between the sites to every write. There is no hard
limit. As guidance, metro distances with a low single-digit millisecond round-trip time between the sites are
recommended. Asynchronous replication has no latency requirement, but the bandwidth must be sufficient to transfer the
changes of one scheduling interval within that interval.

### DNS, GSLB, and Load Balancers

After a failover or relocation, clients have to reach the application at its new site. In the current release, the
switch of DNS records, global server load balancing (GSLB), and virtual IP addresses is performed by external
postTargetReady hooks. See [Site Profiles](../disaster-recovery/configuration/site-profiles.md).

## Assigning Clusters to Sites

A site is assigned as a whole cluster. In a protection plan, every site names the Kubernetes cluster it runs on
(`spec.sites[].cluster`, the name under which the cluster joined the hub), and all nodes and storage of that cluster
belong to the site. With a separate cluster per site, which is the setup for asynchronous replication and for
backups, no node has to be labeled or tagged for DR.

```yaml title="Two sites, each a whole cluster"
spec:
  sites:
    - name: fra
      cluster: site-a
      region: eu-central
    - name: muc
      cluster: site-b
      region: eu-south
```

No label is set on the cluster or its nodes. The assignment is made in two steps, both by the DR administrator:

1. **Cluster name at join:** When the site cluster joins the hub, the spoke chart value `clusterName` sets the name
   under which it is registered on the hub (see [Join Sites](../disaster-recovery/install/sites.md)). The name is
   unique on the hub and must be reused when the site rejoins after a hub recovery.
2. **Site in the protection plan:** The protection plan maps each site name to one of those cluster names in
   `spec.sites[].cluster`. The DR hub reads the plan and treats everything that runs on that cluster as part of the
   site.

Within one protection plan, the relationship is one to one: a site is exactly one cluster, and a cluster is exactly
one site. The same cluster can take part in several protection plans, for example, as the source site of an async
plan with one partner and of a second plan with another partner.

The optional `zone` and `region` of a site are descriptive attributes of the whole site.

For a synchronous plan, the sites are the zones of one stretch cluster: every site names the same cluster and its own
zone, matched against the node label `topology.kubernetes.io/zone`, and dr-agent moves the applications between the
zones. See [Replication Types](../disaster-recovery/configuration/replication-types.md#synchronous-replication).

Independent of DR, the standard node labels `topology.kubernetes.io/zone` and `topology.kubernetes.io/region` are
still useful within a cluster, for example, for the topology-aware scheduling of workloads or for the failure domains
of a storage cluster (see [Failure Domains](../architecture/concepts/failure-domains.md)). They are not a DR
requirement.

### Stretched Storage Cluster

Synchronous (metro) replication uses a stretched simplyblock storage cluster, a dedicated cluster type that spans two
sites and presents the same volumes on both of them.

!!! info "Coming soon"
    The stretched storage cluster type is not available yet. Its deployment, including how its storage nodes are
    assigned to the two sites, will be described here once it is released.

## Checklist

- A separate hub cluster with at least three nodes is available (virtual machines, bare metal, or HyperShift).
- The hub runs Kubernetes 1.30 or later and signs `kubernetes.io/kube-apiserver-client` certificate requests (not
  Amazon EKS).
- The hub nodes meet the sizing recommendation, and etcd runs on fast local disks.
- Every site runs Kubernetes 1.30 or later and meets the simplyblock software and hardware requirements.
- The simplyblock CSI driver on every site supports csi-addons replication.
- Every site has a unique cluster name.
- Storage class names and zone names used by applications are identical on source and target sites. Network
  attachment definitions of virtual machines are either identical or bound to the same role in the site profiles.
- A DR metadata bucket and an archive bucket exist, each with its own credential, reachable from the hub and all
  sites.
- Versioning, object lock (compliance mode), and server-side encryption are enabled on the buckets.
- Write-only credentials are issued to the hub and sites, and a read-only restore credential and the bundle
  public key are stored offline.
- For a backup method type, the plan declares its stores per site, and the storage nodes of every site reach the
  site's store.
- Every site reaches the hub API server over HTTPS (6443 or 443). No inbound connection to the sites is needed.
- The storage clusters that replicate have network connectivity on the simplyblock storage ports.
- For metro DR, the round-trip time between the sites is in the low single-digit milliseconds.
- Every site of a protection plan names the cluster it runs on.
- A mirror registry is configured if the hub and sites have no internet access.
