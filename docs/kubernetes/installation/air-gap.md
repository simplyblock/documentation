---
title: "Air Gap Installation"
description: "Air Gap Installation: Simplyblock can be installed in an air-gapped environment."
weight: 30300
---

Simplyblock can be installed in an air-gapped Kubernetes environment. The recommended entry point is the
`simplyblock-io/helm-deployer` image, which includes the required deployment tooling.

This deployer image, together with all other required simplyblock images, is available from the
[simplyblock-io organization on Quay](https://quay.io/organization/simplyblock-io){:target="_blank" rel="noopener"}.

This repository contains all required images. Synchronizing this repository with the local container repository
retrieves all required images by simplyblock to install control planes, storage planes, and the CSI driver.

How the container repository is synchronized with the local container repository depends on the solution used and is
outside the scope of this documentation. The documentation of the local container repository provides more
information.

The general installation instructions are similar to non-air-gapped installations, with the need to update the
container download locations to point to the local container repository.

## Images Deployed by the Operator

Besides the operator, the control plane (sbcli), and the storage plane (Ultra), whose tags follow the installed
release, the operator deploys the following images. All of them are synchronized to the local container repository:

```plain title="Images deployed by the operator"
quay.io/simplyblock-io/fdb-kubernetes-operator:v2.13.0
quay.io/simplyblock-io/fdb-kubernetes-monitor:7.3.63
quay.io/simplyblock-io/foundationdb-exporter:3.1.0
quay.io/simplyblock-io/minio:RELEASE.2024-01-16T16-07-38Z
quay.io/simplyblock-io/minio-client:RELEASE.2024-01-16T16-06-34Z
quay.io/simplyblock-io/snapshot-controller:v8.2.0
quay.io/simplyblock-io/cert-manager-controller:v1.16.2
quay.io/simplyblock-io/cert-manager-cainjector:v1.16.2
quay.io/simplyblock-io/cert-manager-webhook:v1.16.2
quay.io/simplyblock-io/cert-manager-acmesolver:v1.16.2
quay.io/simplyblock-io/local-path-provisioner:v0.0.30
quay.io/simplyblock-io/busybox:1.37.0
```

The add-on images (the snapshot controller, cert-manager, and the local path provisioner) are needed only for the
add-ons the operator installs. For OpenShift, the ImageSetConfiguration for `oc-mirror` is described in
[Air-Gapped Installation](openshift.md#air-gapped-installation).

## Local Container Repository

For an air-gapped installation, an air-gapped container repository installation is recommended. Tools such as
[JFrog Artifactory](https://jfrog.com/artifactory/){:target="_blank" rel="noopener"} or
[Sonatype Nexus](https://www.sonatype.com/products/sonatype-nexus-repository){:target="_blank" rel="noopener"} help with the setup and management of
container images in air-gapped environments.
