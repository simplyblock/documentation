---
title: "OpenShift"
description: "Install simplyblock on OpenShift through OperatorHub: SCC grants, the subscription, the control plane, the storage cluster, and the CSI driver."
weight: 40100
---

On OpenShift, simplyblock is installed through OperatorHub. The operator is subscribed to once, and everything else
is created from custom resources: the `ControlPlane`, the `SimplyblockDriver`, a discovery run, and the
`ClusterDeploymentConfig` it drafts. The cluster add-ons the control plane depends on are detected and, where
missing, installed by the operator itself.

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

**3. Create the CSI driver**

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

The driver's TLS follows the control plane's unless `spec.tls` sets it. With the default mutual TLS through
cert-manager, the driver issues the client certificates its plugins present to the control plane. Until the storage
cluster exists, the driver reports `Unavailable`, because its plugins wait for a Secret that only exists once the
storage cluster in step 5 is created.

**4. Discover the workers and devices**

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
Control-plane nodes are left out unless the run is set up for them, as described in
[Storage Nodes on Control-Plane Nodes](#storage-nodes-on-control-plane-nodes).

Devices that carry a partition table are not reported. A device whose table is stale, such as one left by an earlier
simplyblock cluster, is reported once `spec.discover.enablePartitionedDevices` is set to `true`.

**5. Review and approve the draft**

```bash title="Reviewing the draft"
oc -n simplyblock get clusterdeploymentconfig discovered-discover-now -o yaml
```

The workers in `nodeSets[].groups[].workers`, the `devices`, and the data and management interfaces have to name
the machines and disks that simplyblock may take. Devices listed here are formatted. Approving the draft deploys it:

```bash title="Approving the draft"
oc -n simplyblock patch clusterdeploymentconfig discovered-discover-now \
  --type=merge -p '{"spec":{"approved":true}}'
```

**6. Check that the storage nodes come up**

```bash title="Watching the storage nodes"
oc -n simplyblock get storagecluster,storagenode,storagepool
oc -n simplyblock get simplyblockdriver
```

The storage cluster moves through `Creating`, `Provisioning`, and `Activating` to `Online`. Each storage node goes
from `Provisioning` to `Online`, and the driver becomes `Ready` once its node and controller plugins run. The nodes
come up one after another, so several minutes are to be expected. The expansion creates a storage pool and a
StorageClass for it, named `simplyblock-<namespace>-<cluster>`, from which volumes are provisioned.

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

### Machine Configuration of a Failed Deployment

The pool `storage-<cluster>` is named after the first six characters of the cluster's UUID. It comes with the
MachineConfig `storage-mc-<cluster>` and the KubeletConfig `storage-kubelet-<cluster>`. When a deployment is removed
(see [Cleaning Up a Failed Deployment](k8s-storage-plane.md#cleaning-up-a-failed-deployment)), with either the
resource cleanup or the full cleanup, these stay behind. A
node still selected by an old pool cannot join the pool of the next deployment, because a node belongs to at most one
custom pool.

```bash title="Finding the machine configuration of earlier deployments"
oc get mcp | grep storage-
oc get machineconfig | grep storage-
oc get kubeletconfig | grep storage-
```

A pool is first emptied, so that its nodes return to their original pool, and then deleted together with its
MachineConfig and KubeletConfig. Nodes that return to their original pool reboot once:

```bash title="Removing the machine configuration of a failed deployment"
POOL=storage-36beed    # as listed above

oc patch mcp $POOL --type=merge -p '{"spec":{"nodeSelector":{"matchExpressions":[{"key":"kubernetes.io/hostname","operator":"In","values":["retired-empty-storage-pool"]}]}}}'
oc get mcp -w          # wait until the original pools report UPDATED=True

oc delete kubeletconfig storage-kubelet-${POOL#storage-}
oc delete machineconfig storage-mc-${POOL#storage-}
oc delete mcp $POOL
```

## Storage Nodes on Control-Plane Nodes

Discovery leaves control-plane nodes out by default, because they run the API server and etcd. On a compact
cluster, or where the control-plane nodes carry the NVMe devices, they can host storage nodes as well. Four things
are needed for that.

**1. Discovery must tolerate the control-plane taints.** Control-plane nodes carry the taint
`node-role.kubernetes.io/master:NoSchedule`. A probe is not run on a node whose taint the run does not tolerate, and
the node is reported with a `WorkerDeclined` event. The tolerations of the run are also written into the draft, as
`spec.cluster.tolerations`, so that the storage node DaemonSet can schedule onto the same nodes.

**2. Discovery must be told to include control-plane nodes.** Even when their taints are tolerated, control-plane
nodes are declined until `spec.discover.enableControlPlaneNodes` is set. An included node is reported with a
`ControlPlaneNodeIncluded` event.

```yaml title="discover-control-plane.yaml"
apiVersion: storage.simplyblock.io/v1alpha2
kind: OperatorOps
metadata:
  name: discover-now
  namespace: simplyblock
spec:
  action: Discover
  discover:
    enableControlPlaneNodes: true
    tolerations:
      - key: node-role.kubernetes.io/master
        operator: Exists
        effect: NoSchedule
      - key: node-role.kubernetes.io/control-plane
        operator: Exists
        effect: NoSchedule
```

When the operator is installed with Helm, the discovery run the chart creates takes the same settings as values:

```bash title="Helm values for a discovery that includes control-plane nodes"
--set discovery.enableControlPlaneNodes=true \
--set-json 'discovery.tolerations=[{"key":"node-role.kubernetes.io/master","operator":"Exists","effect":"NoSchedule"},{"key":"node-role.kubernetes.io/control-plane","operator":"Exists","effect":"NoSchedule"}]'
```

A run does not overwrite a draft that already exists. To repeat a run under the same name, the `OperatorOps` and its
draft `discovered-<name>` are deleted first.

**3. Every node needs the same data interface.** Discovery determines the data networks of the fleet and declines a
node that holds no interface on them, with a `DeviceDeclined` event such as `declined by data network because it
holds no data interface on 10.10.10.0/24`. A draft is also rejected when its groups name different data interfaces,
because one DaemonSet serves every storage node of a cluster. Control-plane nodes often lack the dedicated storage
NIC the workers have. There are two ways to resolve this:

- Give each control-plane node an address on the data network, on an interface with the same name as on the
  workers. Discovery then includes the nodes on its own.
- Carry the data traffic over the OpenShift node network instead. Every group of the draft then names `br-ex` as
  its data interface, the workers included. Storage traffic then shares the network of the cluster's management and
  pod traffic.

For the second way, the draft is edited before it is approved. The workers' group is switched to `br-ex`, and a
group is added for the control-plane nodes with the devices discovery reported for them:

```bash title="Adding the control-plane nodes to a draft with br-ex as data interface"
oc -n simplyblock patch clusterdeploymentconfig discovered-discover-now --type=json -p '[
  {"op":"replace","path":"/spec/nodeSets/0/groups/0/dataInterfaces","value":["br-ex"]},
  {"op":"add","path":"/spec/nodeSets/0/groups/-","value":{
    "name":"control-plane",
    "failureDomain":"default",
    "mgmtInterface":"br-ex",
    "dataInterfaces":["br-ex"],
    "devices":{"nvme":["0000:00:02.0","0000:00:03.0","0000:00:04.0","0000:00:05.0"]},
    "workers":["master-1","master-2","master-3"]}}]'

oc -n simplyblock get clusterdeploymentconfig discovered-discover-now -o jsonpath='{.status.message}'
```

The draft is ready to approve when its status reports that the document is valid and waiting for `spec.approved`.
The devices of every node are listed in the probe report that discovery stores in the ConfigMap
`sb-nodeprobe-<run>-<node>-<hash>`. If the draft comes from a run without the control-plane tolerations, they are
added to `spec.cluster.tolerations` by hand.

**4. A dedicated journal device is chosen at the cluster level.** Discovery proposes a dedicated journal device
only when every node hands over exactly one device smaller than its others. Otherwise, each device carries a journal
partition. A dedicated journal device is requested in the draft:

```yaml title="Dedicating the smallest device of each node to the journal"
spec:
  cluster:
    enableJournalDevice: true
```

`enableJournalDevice` dedicates the smallest NVMe device of every storage node in the cluster to the journal. It
applies to all nodes, workers and control-plane nodes alike, costs one device of capacity per node, and cannot be
changed once the cluster exists. The journal device is listed in the group's `devices` with the other devices. In
discovery, `spec.discover.forceJournalDevice` (Helm value `discovery.forceJournalDevice`) asks for the same where
the smallest device is not unique. It only acts on the nodes the run includes.

### Machine Configuration of Control-Plane Nodes

Control-plane nodes cannot leave the `master` MachineConfigPool, so they are not moved into `storage-<cluster>`.
The operator instead creates the KubeletConfig `storage-kubelet-<cluster>-master`, which selects the `master` pool.
It applies to every node of that pool, including control-plane nodes that host no storage node. The
MachineConfig Operator applies it by draining and rebooting the control-plane nodes one at a time, so the API server
is briefly less redundant while the pool updates:

```bash title="Watching the control-plane pool update"
oc get mcp master -w
```

The per-group `reservedSystemCPU` of the draft is the CPU set held back from SPDK for the system, as a core list such
as `0,1`. On OpenShift it reaches the kubelet through the KubeletConfig of the pool, so all groups whose nodes share
the `master` pool state the same value. It is set before the draft is approved, because changing it later rolls the
`master` pool again.

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
