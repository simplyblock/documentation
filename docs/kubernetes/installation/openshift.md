---
title: "OpenShift"
description: "Install simplyblock on OpenShift through OperatorHub: SCC grants, the subscription, the control plane, the storage cluster, and the CSI driver."
weight: 40100
---

On OpenShift, simplyblock is installed through OperatorHub. The operator is subscribed to once, and everything else
is created from custom resources: the `ControlPlane`, a discovery run, the `ClusterDeploymentConfig` it drafts, and
the `SimplyblockDriver`. The cluster add-ons the control plane depends on are detected and, where missing, installed
by the operator itself.

OpenShift differs from other Kubernetes distributions in three ways that matter here: the privileged Security Context
Constraint (SCC) has to be granted to the namespace explicitly, it ships its own snapshot controller, and the storage
nodes apply their host configuration through MachineConfig objects.

!!! info
    In OpenShift deployments, not all worker nodes must host storage components.
    The `ClusterDeploymentConfig` lists the workers that participate in the storage cluster.
    Storage workloads can be isolated on dedicated worker nodes or node pools.

## Prerequisites

The OpenShift cluster has to be operational, and administrator privileges are required.

The operator and every simplyblock workload run in the `simplyblock` namespace. The namespace is created and granted
the required SCC permissions before the operator is installed:

```bash title="Grant SCC permissions"
oc create namespace simplyblock

oc adm policy add-scc-to-group privileged system:serviceaccounts:simplyblock
oc adm policy add-scc-to-group anyuid system:serviceaccounts:simplyblock

oc label namespace simplyblock \
  pod-security.kubernetes.io/enforce=privileged \
  pod-security.kubernetes.io/audit=privileged \
  pod-security.kubernetes.io/warn=privileged
```

This step is mandatory. SPDK and the storage containers need the privileges for NVMe device access, and the
local-path provisioner the operator installs for the control plane's volumes runs in the same namespace and needs
them for its host directories.

## Installation of Simplyblock

**1. Install the operator**

The operator is published in Red Hat's certified-operators catalog. It supports the `AllNamespaces` install mode
only, and it reads its custom resources from the namespace it runs in, so it is installed into `simplyblock` with an
`OperatorGroup` of its own:

```yaml title="Subscription for the Simplyblock Operator (simplyblock-subscription.yaml)"
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: simplyblock
  namespace: simplyblock
spec: {}
---
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: simplyblock-operator
  namespace: simplyblock
spec:
  channel: alpha
  name: simplyblock-operator
  source: certified-operators
  sourceNamespace: openshift-marketplace
```

```bash title="Subscribing to the operator"
oc apply -f simplyblock-subscription.yaml
oc -n simplyblock get csv -w
```

The operator runs once the ClusterServiceVersion reports `Succeeded`. The container images the bundle references are
pulled from `quay.io/simplyblock-io`, so no Red Hat entitlement or pull secret is required.

**2. Create the control plane**

```yaml title="controlplane.yaml"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ControlPlane
metadata:
  name: simplyblock
  namespace: simplyblock
spec:
  source:
    local:
      image: quay.io/simplyblock-io/simplyblock:26.4.0-beta1
```

```bash title="Creating the control plane"
oc apply -f controlplane.yaml
oc -n simplyblock get controlplane simplyblock -w
```

The name has to be `simplyblock`, because the operator ignores any other. Before the first installation step, the
operator installs the add-ons described in [Prerequisite Add-ons](#prerequisite-add-ons) that the cluster lacks. The
FoundationDB pods start next, then the management API, the task runner, and monitoring, which takes several minutes.
Mutual TLS through cert-manager is on by default, as described in [TLS on OpenShift](#tls-on-openshift).

**3. Discover the workers and devices**

```yaml title="discover.yaml"
apiVersion: storage.simplyblock.io/v1alpha2
kind: OperatorOps
metadata:
  name: discover-now
  namespace: simplyblock
spec:
  action: Discover
```

```bash title="Running the discovery"
oc apply -f discover.yaml
oc -n simplyblock get operatorops discover-now -w
```

The run probes every schedulable worker and ends `Succeeded`. It writes a draft `ClusterDeploymentConfig` named
`discovered-discover-now`. Nothing is deployed from a draft. To limit the run to labeled workers or to certain
devices, see [Create a Storage Cluster](k8s-storage-plane.md).

Devices that carry a partition table are not reported. A device whose table is stale, such as one left by an earlier
simplyblock cluster, is reported once `spec.discover.enablePartitionedDevices` is set to `true`.

**4. Review and approve the draft**

```bash title="Reviewing the draft"
oc -n simplyblock get clusterdeploymentconfig discovered-discover-now -o yaml
```

The workers in `nodeSets[].groups[].workers`, the `devices`, and the data and management interfaces have to name
the machines and disks that simplyblock may take. Devices listed here are formatted. Approving the draft deploys it:

```bash title="Approving the draft"
oc -n simplyblock patch clusterdeploymentconfig discovered-discover-now \
  --type=merge -p '{"spec":{"approved":true}}'
```

**5. Check that the storage nodes come up**

```bash title="Watching the storage nodes"
oc -n simplyblock get storagecluster,storagenode,storagepool
```

The storage cluster moves through `Creating`, `Provisioning`, and `Activating` to `Online`. Each storage node goes
from `Provisioning` to `Online`. The nodes come up one after another, so several minutes are to be expected. The
expansion creates a storage pool and a StorageClass for it, named `simplyblock-<namespace>-<cluster>`, from which volumes are provisioned.

**6. Create the CSI driver**

```yaml title="driver.yaml"
apiVersion: storage.simplyblock.io/v1alpha2
kind: SimplyblockDriver
metadata:
  name: simplyblock
  namespace: simplyblock
spec:
  driverName: csi.simplyblock.io
  enableVolumeSnapshots: true
```

```bash title="Creating the CSI driver"
oc apply -f driver.yaml
```

The driver is created once the storage cluster is `Online`, because its plugins mount the
`simplyblock-csi-secret-v2` Secret that the storage cluster writes. The driver's TLS follows the control plane's
unless `spec.tls` sets it. With the default mutual TLS through cert-manager, the driver issues the client
certificates its plugins present to the control plane.

```bash title="Watching the CSI driver"
oc -n simplyblock get simplyblockdriver
```

The driver becomes `Ready` once its node and controller plugins run.

## Prerequisite Add-ons

The control plane depends on four cluster add-ons. Each is detected before the installation starts, and installed
from manifests built into the operator only when it is missing:

| Add-on                           | Detected by                                                 | Required when                                              |
|----------------------------------|-------------------------------------------------------------|------------------------------------------------------------|
| FoundationDB CRDs (v2.13.0)      | `apps.foundationdb.org/v1beta2` is served                   | always                                                     |
| cert-manager (v1.16.2)           | `cert-manager.io/v1` is served                              | TLS is on and issued by cert-manager                       |
| local-path-provisioner (v0.0.30) | a StorageClass uses the `rancher.io/local-path` provisioner | `spec.source.local.foundationDB.storageClassName` is empty |
| CSI snapshot controller (v8.2.0) | `snapshot.storage.k8s.io/v1` is served                      | always, without holding the control plane                  |

OpenShift ships its own snapshot controller, so the operator does not install one there.

An add-on that is already present is left as it is. Every object the operator installs carries the label
`storage.simplyblock.io/installed-prerequisite`, and no owner reference: add-ons are cluster-wide, other workloads
come to depend on them, and they are not removed with the `ControlPlane`. After an operator upgrade, an add-on the
operator installed is re-applied from the newer manifest, except cert-manager, whose upgrades go one minor version
at a time. An outdated cert-manager is reported with a `PrerequisiteOutdated` event instead.

local-path-provisioner is installed into the `simplyblock` namespace, where the SCC and Pod Security grants from
[Prerequisites](#prerequisites) cover its privileged helper pods. Its StorageClass becomes the default only when the
cluster has no default class. A local-path volume lives on one node's disk without a quota, so production clusters
set `spec.source.local.foundationDB.storageClassName` to a class of their own, which also skips the local-path
install.

Each install can be turned off. An add-on whose flag is `false` is only checked, and the installation holds with a
message naming it until it is installed separately:

```yaml title="ControlPlane with the add-ons installed separately (excerpt)"
spec:
  source:
    local:
      prerequisites:
        installFoundationDBCRDs: false
        installCertManager: false
        installLocalPathProvisioner: false
        installSnapshotController: false
```

## TLS on OpenShift

TLS and mutual TLS are on by default, and cert-manager issues the certificates. When cert-manager is missing, the
operator installs it and creates the issuer chain the control plane's certificates are signed from: a self-signed
root, the certificate authority, the `simplyblock-certificate-authority-issuer` ClusterIssuer, and the client
certificate the operator itself presents. An existing `simplyblock-certificate-authority-issuer` is left as it is.

cert-manager is the provider for an OperatorHub installation. The OpenShift service CA (`provider: OpenShift`)
provides one-way TLS only, and it relies on objects that only the Helm chart creates.

TLS cannot be changed once the `ControlPlane` exists. For details, see [Securing the Control Plane](security.md).

## Air-Gapped Installation

The add-on manifests are built into the operator, so no manifest is downloaded at install time. The images are not:
`oc-mirror` copies the images the bundle lists (the operator, the control plane, the storage node, and the
rebalancer) but not the images the operator deploys for the NUMA resource plugin, the control plane, and the
add-ons. Those are added to the ImageSetConfiguration as additional images:

```yaml title="Additional images for an air-gapped installation (ImageSetConfiguration excerpt)"
mirror:
  additionalImages:
    - name: quay.io/simplyblock-io/fdb-kubernetes-operator:v2.13.0
    - name: quay.io/simplyblock-io/fdb-kubernetes-monitor:7.3.63
    - name: quay.io/simplyblock-io/minio:RELEASE.2024-01-16T16-07-38Z
    - name: quay.io/simplyblock-io/minio-client:RELEASE.2024-01-16T16-06-34Z
    - name: quay.io/simplyblock-io/snapshot-controller:v8.2.0
    - name: quay.io/jetstack/cert-manager-controller:v1.16.2
    - name: quay.io/jetstack/cert-manager-cainjector:v1.16.2
    - name: quay.io/jetstack/cert-manager-webhook:v1.16.2
    - name: quay.io/jetstack/cert-manager-acmesolver:v1.16.2
    - name: docker.io/rancher/local-path-provisioner:v0.0.30
    - name: docker.io/library/busybox:1.37.0
```

The NUMA resource plugin image is set per release. The exact reference is the value of `SB_NUMA_PLUGIN_IMAGE` in
the operator's ClusterServiceVersion, and it is added to `additionalImages` as well:

```bash title="Reading the NUMA resource plugin image"
oc get csv -n simplyblock -l operators.coreos.com/simplyblock-operator.simplyblock \
  -o jsonpath='{.items[0].spec.install.spec.deployments[0].spec.template.spec.containers[0].env[?(@.name=="SB_NUMA_PLUGIN_IMAGE")].value}'
```

The add-on images are needed only for the add-ons the operator installs. The snapshot controller is never
installed on OpenShift, and cert-manager is installed only where the cluster runs none.

The operator pulls every one of these images by digest, except the FoundationDB monitor image: the FoundationDB
operator appends the version tag to it. On OpenShift, the ImageDigestMirrorSet generated by `oc-mirror` therefore
covers all of them once they are mirrored, and the monitor image needs an ImageTagMirrorSet entry for
`quay.io/simplyblock-io/fdb-kubernetes-monitor`.

Without mirror sets, the operator rewrites the registry of every image it deploys, keeping each image's path, tag,
and digest, when `SB_IMAGE_MIRROR_REGISTRY` is set in its environment:

```yaml title="Subscription with a mirror registry (excerpt)"
spec:
  config:
    env:
      - name: SB_IMAGE_MIRROR_REGISTRY
        value: registry.example.com:5000
```

## OpenShift Environment

The `ClusterDeploymentConfig` that describes the storage cluster must name the environment `OpenShift`. Discovery
detects the distribution and writes it into the draft, but it should be checked during the review:

```yaml title="ClusterDeploymentConfig for OpenShift (excerpt)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: ClusterDeploymentConfig
metadata:
  name: simplyblock-deployment
  namespace: simplyblock
spec:
  approved: false
  environment: OpenShift
  cluster:
    name: simplyblock-cluster
    maxSubsystemCount: 50
    vcpuCount: 8
    minHugePagesSize: "100G"
    stripe:
      dataChunks: 1
      parityChunks: 1
    fabricType: tcp
  nodeSets:
    - name: rack-a
      groups:
        - name: default
          workers: [worker-node-1, worker-node-2, worker-node-3]
          mgmtInterface: br-ex
          dataInterfaces: [br-ex]
          devices:
            nvme: ["0000:01:00.0", "0000:02:00.0"]
```

With `environment: OpenShift`, the expansion sets the `openshift` block, `enableCpuTopology`, and
`enableKubeletConfiguration` on `StorageCluster.spec.storageNodes`. Adding a storage node creates a
MachineConfigPool of its own, `storage-<cluster>`, and moves the node into it. A node belongs to exactly one custom
pool, so whatever machine configuration its previous pool carried is lost unless that pool's role is named in
`spec.storageNodes.openshift.machineConfigPool` for the new one to select as well. It defaults to `worker`, the role
every pool already selects, which makes it a no-op for a fleet whose workers are ordinary workers.

## Uninstallation

Uninstalling the operator through OperatorHub removes the operator and its RBAC, but neither the simplyblock custom
resources nor the add-ons it installed. The storage clusters, the `SimplyblockDriver`, and the `ControlPlane` are
deleted first, while the operator still runs to clear their finalizers. After the operator is uninstalled, the
add-ons it installed are found by their label:

```bash title="Listing the add-ons the operator installed"
oc get crd,clusterrole,clusterrolebinding,storageclass,clusterissuer \
  -l storage.simplyblock.io/installed-prerequisite
oc get deployment,serviceaccount,role,rolebinding,certificate -A \
  -l storage.simplyblock.io/installed-prerequisite
```

Deleting local-path-provisioner stops new local-path volumes for every workload that uses its StorageClass, and
deleting cert-manager breaks every other certificate it issues, so both are removed only when nothing else depends
on them.

## Installation with Helm

The operator can also be installed with the Helm chart. With Helm, the SCC commands in
[Prerequisites](#prerequisites) apply unchanged, and the instructions to [install the
operator](k8s-control-plane.md) and to [create a storage cluster](k8s-storage-plane.md) are followed as on any other
Kubernetes distribution. The chart supports the OpenShift service CA as a TLS provider:

```bash title="Installing the operator with Helm and the OpenShift service CA"
helm install simplyblock-operator simplyblock/simplyblock-operator \
    --namespace simplyblock \
    --set tls.provider=openshift \
    --set tls.mutual_enabled=false
```
