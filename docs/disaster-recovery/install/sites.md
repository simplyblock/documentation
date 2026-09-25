---
title: "Joining Site Clusters"
description: "Join site clusters to the DR hub with a bootstrap token and the dr-simplyblock-spoke chart, and verify the site stack the hub delivers."
weight: 10130
---

A site cluster is a Kubernetes cluster that runs protected applications or receives them after a failover. Each site
cluster joins the hub as an Open Cluster Management (OCM) managed cluster. After the join, the hub installs the DR
addons and the site stack on it without further manual steps.

The hub must be installed first, as described in [Installing the Hub](hub.md).

## Site Prerequisites

Before a site joins, the following must be in place on the site cluster:

- **Kubernetes:** A supported Kubernetes or OpenShift version, as listed in
  [Disaster Recovery Requirements](../../deployment-preparation/dr-requirements.md).
- **Simplyblock storage:** A simplyblock storage cluster with the Simplyblock Operator and the simplyblock CSI driver
  (see [Install Simplyblock CSI](../../kubernetes/installation/install-csi.md)). The CSI driver must support
  csi-addons VolumeReplication, and VolumeGroupReplication when consistency groups are enabled in the protection plan.
- **Protected StorageClasses:** The StorageClasses and VolumeSnapshotClasses to be protected carry a selectable label,
  for example, `simplyblock.io/replicated: "true"`. The protection plan selects the classes by this label (see
  [Labeling the StorageClasses](#labeling-the-storageclasses)).
- **Hub connectivity:** The site cluster can reach the hub API server. The hub never connects to the site.
- **Optional components:** KubeVirt for virtual machines, and Multus with an isolated
  NetworkAttachmentDefinition for test failovers of VMs with secondary networks.

The snapshot CRDs and controller, csi-addons, the Ramen Recipe CRD, and Velero do not have to be installed in
advance. They are part of the site stack.

## Creating a Join Token

A join token is created on the hub for each site. The token is valid for 24 hours by default (`--validity`):

```bash title="Creating a join token for site-a"
TOKEN=$(kubectl --context hub -n dr-simplyblock exec deploy/dr-hub -- \
  dr-bootstrap token --cluster site-a)
```

The spoke chart also needs the hub API server URL and its CA certificate:

```bash title="Reading the hub CA certificate"
HUB_CA=$(kubectl --context hub config view --raw --minify \
  -o jsonpath='{.clusters[0].cluster.certificate-authority-data}')
```

## Installing the Spoke Chart

The `dr-simplyblock-spoke` chart installs the OCM klusterlet and registers the site with the hub:

```bash title="Joining site-a to the hub"
helm --kube-context site-a install dr-simplyblock-spoke simplyblock/dr-simplyblock-spoke \
  --namespace dr-simplyblock --create-namespace \
  --set clusterName=site-a \
  --set hub.apiserver=https://hub.example.com:6443 \
  --set hub.token="$TOKEN" \
  --set hub.caData="$HUB_CA"
```

Clusters that join with a bootstrap token are approved automatically. No `clusteradm accept` step is needed.

| Value                   | Default                           | Description                                                                                                 |
|-------------------------|-----------------------------------|-------------------------------------------------------------------------------------------------------------|
| `clusterName`           | Required                          | Name the cluster registers under. It must be equal to `spec.sites[].cluster` in the protection plans.       |
| `hub.apiserver`         | Required                          | URL of the hub API server.                                                                                  |
| `hub.token`             | Required                          | Join token created with `dr-bootstrap token`.                                                               |
| `hub.caData`            | Required                          | Base64-encoded PEM CA certificate of the hub API server, as in a kubeconfig's `certificate-authority-data`. |
| `hub.publiclyTrustedCA` | `false`                           | Allows an empty `hub.caData` when the hub API server certificate is publicly trusted.                       |
| `images.registry`       | `quay.io/open-cluster-management` | Registry of the klusterlet images. Points to a mirror for air-gapped sites.                                 |
| `images.tag`            | `v1.3.1`                          | Tag of the klusterlet images.                                                                               |
| `stackOmit`             | `[]`                              | Site stack components the hub should not deliver to this cluster.                                           |

!!! warning
    The cluster name is permanent. It is the name of the OCM ManagedCluster, of the Ramen DRCluster, and of the site
    in every protection plan. After a hub loss, sites must rejoin under their old names.

## What the Hub Installs on a Site

When a cluster joins, `dr-hub` enables the following OCM addons on it:

- **Policy addons:** `governance-policy-framework` and `config-policy-controller`, used by Ramen to distribute the S3 credentials.
- **Work manager:** `work-manager`, required for ManagedClusterViews.
- **DR agent:** `dr-agent` in the `simplyblock-dr-agent` namespace. It reports the site status to the hub every 15
  seconds and runs hooks, probes, tests, and cleanups on the site.

It then delivers the site stack, one OCM ManifestWork `dr-stack-<component>` per component:

| Component               | Content                                                                                                                                        |
|-------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| `snapshotter`           | external-snapshotter v8.6.0 with volume group snapshots enabled.                                                                               |
| `csi-addons-crds`       | csi-addons v0.14.0 CRDs, including VolumeReplication, VolumeGroupReplication, and NetworkFence.                                                |
| `csi-addons-controller` | csi-addons v0.14.0 controller.                                                                                                                 |
| `recipe-crd`            | The Ramen Recipe CRD.                                                                                                                          |
| `velero`                | Velero v1.16.1 with velero-plugin-for-aws v1.12.0, kubevirt-velero-plugin v0.8.0, and Kopia. No default backup storage location is configured. |
| `olm-stubs`             | Stub CRDs for the OLM kinds that the Ramen DR cluster operator expects.                                                                        |
| `ramen-dr-cluster`      | The Ramen DR cluster operator.                                                                                                                 |
| `agent-velero-rbac`     | Permissions for `dr-agent` in the Velero namespace.                                                                                            |

The component list of a release is printed with `dr-bootstrap render spoke`:

```bash title="Listing the site stack components"
kubectl --context hub -n dr-simplyblock exec deploy/dr-hub -- dr-bootstrap render spoke
```

The stack ManifestWorks use the orphan delete option. Removing a site from DR does not delete the components from
the site cluster.

!!! note
    The ManifestWork that installs the Ramen DR cluster operator reports its OLM Subscription as not applied. This is
    expected, because the site does not run OLM.

## Opting Out of Site Stack Components

On a site that already runs some of the components, for example, Velero from OpenShift API for Data Protection
(OADP), the hub can be told not to deliver them:

- **Single components:** The spoke chart value `stackOmit` lists the components to skip. It is stored as the
  annotation `agent.open-cluster-management.io/dr-stack-omit` on the ManagedCluster.
- **Entire stack:** The label `dr.simplyblock.io/stack=false` on the ManagedCluster stops the hub from delivering any
  stack component to the site.

```bash title="Joining a site without the Velero component"
helm --kube-context site-b install dr-simplyblock-spoke simplyblock/dr-simplyblock-spoke \
  --namespace dr-simplyblock --create-namespace \
  --set clusterName=site-b \
  --set hub.apiserver=https://hub.example.com:6443 \
  --set hub.token="$TOKEN" \
  --set hub.caData="$HUB_CA" \
  --set 'stackOmit={velero}'
```

```bash title="Turning off the site stack for a managed cluster"
kubectl --context hub label managedcluster site-b dr.simplyblock.io/stack=false
```

Omitted components must be provided in compatible versions by other means.

## Labeling the StorageClasses

A protection plan picks the protected StorageClasses on every site with a label selector. Only the selection label is
set by the administrator. `dr-hub` adds the Ramen labels (`ramendr.openshift.io/storageid`,
`ramendr.openshift.io/replicationid`, and `ramendr.openshift.io/groupreplicationid`) and the plan label
`plan.dr.simplyblock.io/<plan>` itself.

```bash title="Labeling a simplyblock StorageClass and VolumeSnapshotClass for protection"
kubectl --context site-a label storageclass simplyblock-csi-sc simplyblock.io/replicated=true
kubectl --context site-a label volumesnapshotclass simplyblock-snap simplyblock.io/replicated=true
```

StorageClasses and VolumeSnapshotClasses with the same names must exist on every site of a plan, because an
application recovers exactly as captured (see [Site Profiles and Mappings](../configuration/site-profiles.md)). A
VolumeSnapshotClass is only labeled by `dr-hub` if its driver matches the provisioner of a selected StorageClass.

## Zones

A site usually corresponds to a whole cluster. If one cluster spans several topology zones, a site can also stand for
one zone of it, set with `spec.sites[].zone` in the protection plan. The zone must match the nodes'
`topology.kubernetes.io/zone` labels. Each combination of cluster and zone may appear only once per plan.

## Verifying the Join

On the hub, the managed cluster must be joined and available:

```bash title="Checking the managed clusters"
kubectl --context hub get managedclusters
```

```plain title="Example output of the managed cluster listing"
NAME          HUB ACCEPTED   MANAGED CLUSTER URLS   JOINED   AVAILABLE   AGE
site-a        true                                  True     True        12m
site-b        true                                  True     True        9m
```

The `dr-agent` addon must be available in the cluster's namespace:

```bash title="Checking the dr-agent addon of site-a"
kubectl --context hub -n site-a get managedclusteraddon dr-agent
```

Finally, the `DRConfig` status lists every site agent and the state of every site stack:

```bash title="Checking the site agents and site stacks"
kubectl --context hub get drconfig default -o jsonpath='{.status.agents}'
kubectl --context hub get drconfig default -o jsonpath='{.status.stack}'
```

Each entry of `status.agents` reports the cluster, whether the agent is available, its version, the Velero namespace,
and when it last reported. Each entry of `status.stack` reports whether all stack components are applied at the
current version, with a message if they are not.

## Next Steps

- [Configuration](../configuration/index.md)
- [Protection Plans](../configuration/protection-plans.md)
