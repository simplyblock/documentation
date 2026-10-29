---
title: "EKS"
description: "Install simplyblock on EKS with tainted node groups: place the control plane and the CSI driver, and point the discovery at the storage node group."
weight: 40050
---

On EKS, the installation follows the general procedure of [installing the Simplyblock Operator](k8s-control-plane.md)
and [creating a storage cluster](k8s-storage-plane.md). The differences come from the dedicated, tainted node groups
described in [EKS](../../deployment-preparation/eks.md): every simplyblock component has to be placed
onto its node group and has to tolerate its taint.

The examples on this page use the following labels and taints. They are examples and are replaced with the ones of the
actual node groups.

| Node Group    | Label                  | Taint                                              |
|---------------|------------------------|----------------------------------------------------|
| Control plane | `sb-role=controlplane` | `simplyblock.io/role=controlplane:NoSchedule`      |
| Storage       | `sb-role=storage-a`    | `storage.simplyblock.io/dedicated=true:NoSchedule` |
| Clients       | `sb-role=client`       | `simplyblock.io/role=client:NoSchedule`            |

## Helm Values

The placement is stated in the Helm values. The Simplyblock Operator and the CSI controller run on the untainted system
node group and need no placement.

```yaml title="Helm values for EKS (values-eks.yaml)"
controlplane:
  # StorageClass of the FoundationDB volumes; EKS has no default StorageClass.
  storageclass:
    name: ebs-gp3
  nodeSelector:
    create: true
    key: sb-role
    value: controlplane
  tolerations:
    create: true
    list:
      - key: simplyblock.io/role
        operator: Equal
        value: controlplane
        effect: NoSchedule

prometheus:
  server:
    persistentVolume:
      storageClass: ebs-gp3
    nodeSelector:
      sb-role: controlplane
    tolerations:
      - key: simplyblock.io/role
        operator: Equal
        value: controlplane
        effect: NoSchedule

driver:
  # The CSI node plugin must run on the tainted client nodes.
  tolerations:
    - operator: Exists

# The initial discovery run, restricted to the storage node group.
discovery:
  enabled: true
  name: cluster-a
  nodeSelector:
    sb-role: storage-a
  tolerations:
    - key: storage.simplyblock.io/dedicated
      operator: Equal
      value: "true"
      effect: NoSchedule
```

```bash title="Installing the operator with the EKS values"
helm install simplyblock-operator simplyblock/simplyblock-operator \
    -n simplyblock --create-namespace -f values-eks.yaml
```

`controlplane.nodeSelector` and `controlplane.tolerations` place every control plane workload, including the
FoundationDB processes, onto the control plane node group. Prometheus is installed by its own subchart and is placed
with its own values.

The persistent volume claim template of Prometheus cannot be changed after the first installation. A release that was
installed without `prometheus.server.persistentVolume.storageClass` keeps a pending claim, which only a deletion of
the Prometheus StatefulSet and its claim clears.

## Referring to the Taint During the Storage Cluster Deployment

A storage cluster is created from a discovery run, which writes a draft `ClusterDeploymentConfig`. The probe pods of
the run are pinned to their nodes, which bypasses the scheduler but not the taints. A run that does not tolerate the
taint of the storage node group therefore finds no workers.

The taint is stated once, in the tolerations of the discovery run. The run carries them into the draft
(`spec.cluster.tolerations`), and from there they reach the storage node DaemonSet of the cluster.

### The First Storage Cluster

The initial discovery run is configured with the Helm values `discovery.nodeSelector` and `discovery.tolerations`
shown above. After the control plane becomes `Available`, the operator raises the run and writes the draft
`discovered-<discovery.name>`.

```bash title="Following the initial discovery"
kubectl -n simplyblock get operatorops cluster-a -w
kubectl -n simplyblock get clusterdeploymentconfig
```

### Additional Storage Clusters

Every further storage cluster gets its own node group and its own discovery run, an `OperatorOps` resource with the
action `Discover`.

```yaml title="Discovery run for a second storage node group (discover-cluster-b.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: OperatorOps
metadata:
  name: discover-cluster-b
  namespace: simplyblock
spec:
  action: Discover
  discover:
    configName: cluster-b
    nodeSelector:
      sb-role: storage-b
    tolerations:
      - key: storage.simplyblock.io/dedicated
        operator: Equal
        value: "true"
        effect: NoSchedule
```

```bash title="Running the discovery"
kubectl apply -f discover-cluster-b.yaml
kubectl -n simplyblock get operatorops discover-cluster-b -w
```

### Reviewing and Approving the Draft

The draft lists the workers of the storage node group, their NVMe instance storage, and the tolerations of the run.

```yaml title="Excerpt of a draft written for a tainted storage node group"
spec:
  approved: false
  cluster:
    tolerations:
      - effect: NoSchedule
        key: storage.simplyblock.io/dedicated
        operator: Equal
        value: "true"
  nodeSets:
    - groups:
        - devices:
            nvme:
              - 0000:00:1f.0
          workers:
            - ip-192-168-20-206.ec2.internal
            - ip-192-168-4-223.ec2.internal
            - ip-192-168-8-222.ec2.internal
```

The boot disk of an EKS node is an EBS volume and does not appear in the draft. After the review, the draft is
approved, and the operator creates the storage cluster.

```bash title="Approving the draft"
kubectl -n simplyblock patch clusterdeploymentconfig discovered-cluster-a \
    --type=merge -p '{"spec":{"approved":true}}'
```

The review, the approval, and the verification of the cluster are described in detail in
[Create a Storage Cluster](k8s-storage-plane.md#review-the-draft).

## Verifying the Placement

```bash title="Checking where the simplyblock pods run"
kubectl -n simplyblock get pods -o wide
```

The FoundationDB, API, task, and monitoring pods run on the control plane nodes, the storage node pods run on the
storage nodes, and a CSI node plugin pod runs on every client node.

On the client nodes, the volumes are attached with native NVMe multipathing. How to check it is described in
[Node Images](../../deployment-preparation/eks.md#node-images).
