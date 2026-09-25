---
title: Host Authentication and Encryption
description: "Host access control and DH-HMAC-CHAP authentication for NVMe-oF on Kubernetes, configured on a StoragePool and its StorageClass."
weight: 10710
---

Simplyblock protects the NVMe-oF transport between a worker node and a storage node with host access control and
DH-HMAC-CHAP authentication. Only a host registered as an allowed host of a storage pool can connect to the NVMe-oF
subsystem of a volume in that pool, and every connection is authenticated in both directions with the NVMe standard
authentication protocol (TP8018).

On Kubernetes, both are configured declaratively on the `StoragePool` custom resource and reconciled by the
Simplyblock Operator. No host NQN has to be registered, and no key has to be provisioned by hand.

!!! note "Transport encryption and volume encryption"
    TLS/PSK encryption of the NVMe-oF transport is not exposed through the `StoragePool`. Encryption of the volume
    data at rest is an unrelated, per-volume feature and is described in
    [Volume Encryption](../../usage/volume-encryption.md).

## Enable Host Authentication and Encryption

Security is configured per storage pool and is disabled by default. It is enabled by setting
`volumeDefaults.enableDHCHAP` on the `StoragePool` and listing the Kubernetes worker nodes that are allowed to connect
to the pool's volumes in `allowedNodes`. The pool belongs to the `StorageCluster` named in `clusterRef`, in the same
namespace.

```yaml title="Example of a StoragePool with DHCHAP enabled for two worker nodes (pool-a.yaml)"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StoragePool
metadata:
  name: pool-a
  namespace: simplyblock
spec:
  clusterRef: production
  allowedNodes:
    - worker-1
    - worker-2
  volumeDefaults:
    enableDHCHAP: true
```

```bash title="Creating the storage pool"
kubectl apply -f pool-a.yaml
```

Authentication is only enforced once `allowedNodes` is non-empty. `volumeDefaults` is immutable once set, so
`enableDHCHAP` belongs in the manifest that creates the pool. `allowedNodes` stays mutable.

The default pool that is created with a cluster (`<cluster>-default`) carries no DHCHAP setting. DHCHAP is therefore
configured on an additional pool, together with a StorageClass assigned to it.

## StorageClass of a DHCHAP Pool

Volumes of a DHCHAP pool have to be scheduled onto allowed nodes only. This is expressed through the StorageClass
parameter `dhchap_node_selector`, which names the node label the operator puts on every allowed node of the pool:

```plain title="Node label of the allowed nodes of a pool"
storage.simplyblock.io/storage-pool.<POOL_UUID>=allowed
```

The pool UUID is known once the pool is `Ready`:

```bash title="Reading the UUID of the storage pool"
kubectl get storagepool pool-a -n simplyblock -o jsonpath='{.status.uuid}'
```

The operator only writes a StorageClass for a cluster's default pool. For any other pool, the StorageClass is authored
and assigned to the pool by the three labels described in [Storage Class](../../usage/storage-class.md). For a DHCHAP
pool it also carries `dhchap_node_selector`:

```yaml title="Example of a StorageClass for the DHCHAP pool (pool-a-class.yaml)"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: pool-a
  labels:
    storage.simplyblock.io/namespace: simplyblock
    storage.simplyblock.io/cluster: production
    storage.simplyblock.io/pool: pool-a
provisioner: csi.simplyblock.io
parameters:
  cluster_id: <CLUSTER_UUID>
  pool_name: pool-a
  dhchap_node_selector: storage.simplyblock.io/storage-pool.<POOL_UUID>
  csi.storage.k8s.io/fstype: xfs
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

The cluster UUID is held in `StorageCluster.status.uuid`. StorageClass parameters cannot be changed after creation, so
the class is created once the pool UUID is known.

## Reconciliation by the Operator

Once the storage pool is created, host registration and node scheduling are reconciled by the operator:

- **Allowed hosts:** each node in `allowedNodes` is registered as an allowed host of the pool, under a deterministic
  NQN derived from that node's Kubernetes UID (`nqn.2014-08.io.simplyblock:uuid:<node-uid>`).
- **Node labels:** each allowed node is labeled `storage.simplyblock.io/storage-pool.<POOL_UUID>=allowed`, and the
  label is removed again from every node that leaves the list.
- **Scheduling:** for a StorageClass with `dhchap_node_selector`, the CSI driver writes the same label into the
  `nodeAffinity` of every `PersistentVolume` it creates. Every scheduling decision on the volume, including the first
  one, a restart, a recreate, and a drain, is restricted to allowed nodes.
- **Host NQN:** the node's own NQN and the pool's DHCHAP secrets are presented by the CSI node plugin on connect, so
  no host NQN has to be supplied anywhere in the Kubernetes flow.

A name in `allowedNodes` that resolves to no Kubernetes node is ignored and kept in the spec, with an
`AllowedNodeMissing` event. The node returns to the pool when it comes back under the same name.

## Managing Allowed Nodes

`allowedNodes` is mutable. Changing it relabels the nodes and updates the pool's allowed hosts, and it never touches a
StorageClass.

A node removed from `allowedNodes` loses its label, and its NQN is removed from the allowed hosts of the pool. The node
is rejected on its next connect attempt. A volume already connected on that node is not disconnected by the removal.

## Verifying the Configuration

`status.allowedNodes` carries the node names the operator resolved and registered. A difference to
`spec.allowedNodes` means a listed node does not exist, or the pool has not converged yet.

```bash title="Reading the allowed nodes registered for a storage pool"
kubectl get storagepool pool-a -n simplyblock \
    -o jsonpath='{.status.allowedNodes}'
```

The nodes carrying the pool's label are listed through a label selector. The result has to match `status.allowedNodes`.

```bash title="Listing the nodes labeled as allowed for a storage pool"
kubectl get nodes \
    -l "storage.simplyblock.io/storage-pool.$(kubectl get sp pool-a -n simplyblock -o jsonpath='{.status.uuid}')=allowed"
```

Whether a volume is restricted to the allowed nodes is visible in the `nodeAffinity` of its PersistentVolume. An empty
result means its StorageClass carries no `dhchap_node_selector`.

```bash title="Checking the node affinity of a volume"
kubectl get pv <pv-name> -o jsonpath='{.spec.nodeAffinity}'
```

## Pods on a Disallowed Node

The `nodeAffinity` of the `PersistentVolume` keeps a `Pod` off a node outside `allowedNodes`. If one lands there
regardless, no `nvme connect` is ever built. `NodeStageVolume` derives the host NQN of its own node and requests the
connection information from the control plane, which rejects the unknown NQN with an HTTP `404`. The `Pod` stays
unscheduled with a `FailedMount` event.

```plain title="Example of a FailedMount event on a node outside the allowed nodes"
MountVolume.MountDevice failed for volume "pvc-...": rpc error: code = Internal
desc = failed to fetch connection: GET 404: Host NQN
nqn.2014-08.io.simplyblock:uuid:<node-uid> not found in allowed hosts for volume <lvol-id>
```

The node is either missing from `allowedNodes` or the pool has not converged yet. Both are checked as described in
[Verifying the Configuration](#verifying-the-configuration).

See the [Operator Reference](../../../reference/operator/reference.md) for the full `StoragePool` field list, and
[Storage Class](../../usage/storage-class.md) for the `dhchap_node_selector` parameter.

For a detailed explanation of the security mechanisms and configuration, see
[NVMe-oF Security](../../../architecture/concepts/nvmf-security.md).
