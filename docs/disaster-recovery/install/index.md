---
title: "Install"
description: "Installation flow of simplyblock Disaster Recovery: the hub cluster, the archive, the state bundle, the site clusters, and the components each of them runs."
weight: 10100
---

Simplyblock Disaster Recovery (component name `dr-simplyblock`) is installed with two Helm charts. The
`dr-simplyblock-hub` chart turns a Kubernetes cluster into the DR hub, and the `dr-simplyblock-spoke` chart joins each
site cluster to that hub. Everything else, including Open Cluster Management (OCM), the Ramen operators, Velero, and
the csi-addons controllers, is installed by `dr-simplyblock` itself.

## Installation Flow

The installation follows the same order on every deployment:

1. **Prerequisites:** The hub and site clusters, the S3 buckets, and the network paths described in
   [Disaster Recovery Requirements](../../deployment-preparation/dr-requirements.md) are in place. Each site runs a
   simplyblock storage cluster with the simplyblock CSI driver.
2. **Hub:** The `dr-simplyblock-hub` chart installs OCM, the Ramen hub operator, and `dr-hub` on the hub cluster. See
   [Installing the Hub](hub.md).
3. **Archive and state bundle:** An S3 archive for reports and a signed DR state bundle are configured, so that the
   hub itself can be rebuilt after a disaster. See [Archive and State Bundle](archive.md).
4. **Sites:** Each site cluster joins the hub with a bootstrap token and the `dr-simplyblock-spoke` chart. The hub
   then delivers the site stack to it. See [Joining Site Clusters](sites.md).
5. **Verification:** The managed clusters report `Joined` and `Available`, the `dr-agent` addon is available on every
   site, and the `DRConfig` status lists every site agent and site stack.

Once the installation is complete, protection is configured with protection plans, DR paths, and protected
applications, as described in [Configuration](../configuration/index.md).

## Components per Cluster

The hub cluster runs the control components. Site clusters only run agents and the data-path components. The hub
never holds a kubeconfig of a site cluster: all communication runs through OCM, with the site clusters connecting to
the hub API server.

| Component                                                                                | Hub | Site         | Version                  |
|------------------------------------------------------------------------------------------|-----|--------------|--------------------------|
| `dr-hub` (controllers, admission webhooks, report archiver, state bundler)               | Yes | No           | Chart version            |
| OCM cluster manager                                                                      | Yes | No           | 1.3.1                    |
| OCM governance-policy addon                                                              | Yes | Addon agents | v0.18.0                  |
| OCM `ocm-controller` (ManagedClusterView, work-manager addon)                            | Yes | Addon agent  | Bundled                  |
| Ramen hub operator                                                                       | Yes | No           | Pinned by digest         |
| OCM klusterlet (registration and work agents)                                            | No  | Yes          | 1.3.1                    |
| `dr-agent` (OCM addon, namespace `simplyblock-dr-agent`)                                 | No  | Yes          | Chart version            |
| Ramen DR cluster operator                                                                | No  | Yes          | Pinned by digest         |
| external-snapshotter (with volume group snapshots)                                       | No  | Yes          | v8.6.0                   |
| csi-addons CRDs and controller (VolumeReplication, VolumeGroupReplication, NetworkFence) | No  | Yes          | v0.14.0                  |
| Ramen Recipe CRD                                                                         | No  | Yes          | Pinned                   |
| Velero with velero-plugin-for-aws and kubevirt-velero-plugin                             | No  | Yes          | v1.16.1, v1.12.0, v0.8.0 |
| Simplyblock storage, Simplyblock Operator, and CSI driver                                | No  | Yes          | Installed separately     |

The exact versions of a release can be printed from the hub image:

```bash title="Listing the pinned component versions"
kubectl -n dr-simplyblock exec deploy/dr-hub -- dr-bootstrap render versions
```

The site stack is delivered by the hub as OCM ManifestWorks. The individual components can be left out on a site
that already runs them, as described in [Opting Out of Site Stack Components](sites.md#opting-out-of-site-stack-components).

## Air-Gapped Installation

All manifests of the bootstrapped components are embedded in the `dr-simplyblock` image. Installing never downloads
anything, neither manifests nor charts. Only container images are pulled.

For an air-gapped installation, the images are mirrored into a local registry, and the charts point to it:

- **Hub images:** `image.registry` of the hub chart points to the mirror of `quay.io/simplyblock-io`.
- **Bootstrapped images:** `bootstrap.imageRegistry` of the hub chart makes every bootstrapped component (OCM, Ramen,
  the site stack) pull from the mirror. It is stored in `DRConfig.spec.bootstrap.imageRegistry`.
- **Klusterlet images:** `images.registry` of the spoke chart points to the mirror of
  `quay.io/open-cluster-management`.

General guidance on mirroring images is available in [Air-Gapped Installation](../../deployment-preparation/air-gap/index.md).

## Installing on an Existing ACM or ODF Hub

On a hub where OCM and Ramen are already installed, for example, by Red Hat Advanced Cluster Management (ACM) or
OpenShift Data Foundation (ODF), the bootstrap is turned off with `bootstrap.enabled=false`. In this mode:

- **No bootstrap:** The chart installs neither OCM nor Ramen, and `dr-hub` does not deliver the site stack.
- **Ramen configuration:** `dr-hub` does not manage the Ramen hub configuration (`DRConfig.spec.ramen.managed` is
  `false`). Protection plans must reference an existing Ramen S3 profile with `spec.s3Profile` instead of declaring
  per-site stores with `spec.s3Profiles`.
- **Addon rollout:** The `dr-agent` addon is rolled out by `agent.installStrategy`, either manually (a
  `ManagedClusterAddOn` named `dr-agent` in each cluster namespace) or through OCM Placements.

## Pages in This Section

- [Installing the Hub](hub.md)
- [Archive and State Bundle](archive.md)
- [Joining Site Clusters](sites.md)
