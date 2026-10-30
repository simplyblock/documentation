---
title: "OpenShift"
description: "Install simplyblock on OpenShift: grant the privileged SCC, choose the TLS provider, and set the OpenShift environment of the deployment config."
weight: 40100
---

When installing simplyblock on OpenShift, the process is very similar to Kubernetes, with a few key differences.
OpenShift requires explicitly granting the privileged Security Context Constraint (SCC) to service accounts to enable
storage and SPDK operations, it provides its own certificate service for TLS, and the storage nodes apply their host
configuration through OpenShift MachineConfig objects.

!!! info
    In OpenShift deployments, not all worker nodes must host storage components.
    The `ClusterDeploymentConfig` lists the workers that participate in the storage cluster.
    Storage workloads can be isolated on dedicated worker nodes or node pools.

## Prerequisites

Ensure the OpenShift cluster is operational and that administrator privileges are available.

Before deploying simplyblock components, grant the required SCC permissions:

```bash title="Grant SCC permissions"
oc create namespace simplyblock

oc adm policy add-scc-to-group privileged system:serviceaccounts:simplyblock
oc adm policy add-scc-to-group anyuid system:serviceaccounts:simplyblock

oc label namespace simplyblock \
  pod-security.kubernetes.io/enforce=privileged \
  pod-security.kubernetes.io/audit=privileged \
  pod-security.kubernetes.io/warn=privileged
```

This step is mandatory to allow SPDK and storage-related containers to run with the privileges required for NVMe device
access.

## TLS on OpenShift

TLS is enabled by default. On OpenShift, two certificate providers are available:

- **OpenShift service CA (`tls.provider=openshift`):** Uses the certificates OpenShift issues for services. It
  provides one-way TLS only, so `tls.mutual_enabled` must be set to `false`.
- **Cert-manager (`tls.provider=cert-manager`):** Required for mutual TLS and for an external KMS.
  [cert-manager](https://cert-manager.io/){:target="_blank" rel="noopener"} must be installed first.

```bash title="Install the operator with the OpenShift service CA"
helm install simplyblock-operator simplyblock/simplyblock-operator \
    --namespace simplyblock \
    --set tls.provider=openshift \
    --set tls.mutual_enabled=false
```

For details, see [Securing the Control Plane](security.md).

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

## Installation of Simplyblock

The Simplyblock Operator is installed with the Helm chart or through the OpenShift OperatorHub, since
simplyblock-operator is published in Red Hat's certified-operators catalog. Storage nodes, storage pools, and the CSI
driver are deployed the same way regardless of which install method is used.

=== "Helm"
    To install the simplyblock components on OpenShift, follow the instructions to
    [install the Simplyblock Operator](k8s-control-plane.md) and to [create a storage
    cluster](k8s-storage-plane.md).

=== "OperatorHub"
    {{ experimental }}

    The operator is installed from OperatorHub in the OpenShift web console. Only the `AllNamespaces` install mode
    is supported, so the operator is installed into the `openshift-operators` namespace and reconciles resources
    across the whole cluster. The container images referenced by the bundle are pulled from
    `quay.io/simplyblock-io`, so no Red Hat entitlement or pull secret is required.

    The same subscription is created directly with the following manifest:

    ```yaml title="Example of a Subscription for the Simplyblock Operator (simplyblock-subscription.yaml)"
    apiVersion: operators.coreos.com/v1alpha1
    kind: Subscription
    metadata:
      name: simplyblock-operator
      namespace: openshift-operators
    spec:
      channel: alpha
      name: simplyblock-operator
      source: certified-operators
      sourceNamespace: openshift-marketplace
    ```

    ```bash title="Creating the subscription"
    oc apply -f simplyblock-subscription.yaml
    ```

    Wait until the ClusterServiceVersion reports `Succeeded`:

    ```bash title="Waiting for the operator"
    oc -n openshift-operators get csv -w
    ```

    The operator is running now, but it has no control plane, no CSI driver, and no storage nodes yet. The steps
    below create them. Every resource goes into the namespace the operator was installed into, which is
    `openshift-operators` for an OperatorHub install, because the operator only reads its own namespace.

    !!! warning
        The SCC and Pod Security commands in [Prerequisites](#prerequisites) name the namespace `simplyblock`.
        For an OperatorHub install, run them for `openshift-operators` instead, or the storage and discovery pods
        are rejected.

    **1. Install the FoundationDB custom resource definitions**

    The operator starts the FoundationDB operator itself, but the FoundationDB custom resource definitions (CRDs)
    are not part of the OperatorHub bundle. A Helm install ships them. Without them, the control plane never
    progresses and the operator log repeats `apply FoundationDBCluster ... the server could not find the requested
    resource`. Apply them once per cluster, before the `ControlPlane`:

    ```bash title="Installing the FoundationDB CRDs"
    FDB=v2.13.0
    BASE=https://raw.githubusercontent.com/FoundationDB/fdb-kubernetes-operator/$FDB/config/crd/bases
    oc apply --server-side \
      -f $BASE/apps.foundationdb.org_foundationdbclusters.yaml \
      -f $BASE/apps.foundationdb.org_foundationdbbackups.yaml \
      -f $BASE/apps.foundationdb.org_foundationdbrestores.yaml
    ```

    `--server-side` is required: the `FoundationDBCluster` definition is larger than the annotation limit of a
    client-side apply. Use the same release the operator deploys (`v2.13.0`). If the cluster already runs its own
    FoundationDB operator, skip this step.

    **2. Create the control plane**

    ```yaml title="controlplane.yaml"
    apiVersion: storage.simplyblock.io/v1alpha2
    kind: ControlPlane
    metadata:
      name: simplyblock
      namespace: openshift-operators
    spec:
      source:
        local:
          image: quay.io/simplyblock-io/simplyblock:26.4.0-beta1
          foundationDB:
            replicas: 3
          tls:
            enableTLS: false
            enableMutualTLS: false
    ```

    The name has to be `simplyblock`, because the operator ignores any other. `replicas: 3` is the `double` redundancy
    mode. Use `5` for `triple`. To serve the management API over TLS, see [Security](security.md).

    ```bash title="Creating the control plane"
    oc apply -f controlplane.yaml
    oc -n openshift-operators get controlplane simplyblock -w
    ```

    The control plane takes several minutes: the FoundationDB pods start first, then the management API, task
    runner, and monitoring. Continue when the phase is `Available` and every pod in the namespace is `Running`.

    **3. Create the CSI driver**

    ```yaml title="driver.yaml"
    apiVersion: storage.simplyblock.io/v1alpha2
    kind: SimplyblockDriver
    metadata:
      name: simplyblock
      namespace: openshift-operators
    spec:
      driverName: csi.simplyblock.io
    ```

    ```bash title="Creating the CSI driver"
    oc apply -f driver.yaml
    ```

    The driver pods wait for a secret that only exists once the storage cluster in step 5 is created, so the driver
    shows `Unavailable` until then.

    **4. Discover the workers and devices**

    ```yaml title="discover.yaml"
    apiVersion: storage.simplyblock.io/v1alpha2
    kind: OperatorOps
    metadata:
      name: discover-now
      namespace: openshift-operators
    spec:
      action: Discover
    ```

    ```bash title="Running the discovery"
    oc apply -f discover.yaml
    oc -n openshift-operators get operatorops discover-now -w
    ```

    The run probes every schedulable worker and ends `Succeeded`. It writes a draft `ClusterDeploymentConfig` named
    `discovered-discover-now`. Nothing is deployed from a draft. To limit the run to labeled workers or to certain
    devices, see [Create a Storage Cluster](k8s-storage-plane.md).

    **5. Review and approve the draft**

    ```bash title="Reviewing the draft"
    oc -n openshift-operators get clusterdeploymentconfig discovered-discover-now -o yaml
    ```

    Check that `nodeSets[].groups[].workers`, `devices`, and the data and management interfaces name the machines
    and disks that simplyblock may take. Devices listed here are formatted. Approving the draft deploys it:

    ```bash title="Approving the draft"
    oc -n openshift-operators patch clusterdeploymentconfig discovered-discover-now \
      --type=merge -p '{"spec":{"approved":true}}'
    ```

    **6. Check that the storage nodes come up**

    ```bash title="Watching the storage nodes"
    oc -n openshift-operators get storagecluster,storagenode
    oc -n openshift-operators get simplyblockdriver
    ```

    The storage cluster moves through `Creating` and `Provisioning`. Each storage node goes from `Provisioning` to
    `Online`, and the driver becomes `Ready` once the cluster exists. The nodes come up one after another, so allow
    several minutes. When every node is `Online`, continue with [Create a Storage
    Cluster](k8s-storage-plane.md) to create a storage pool and a first volume.
