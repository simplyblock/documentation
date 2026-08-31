---
title: Host Authentication and Encryption
description: "Host access control and DH-HMAC-CHAP authentication for the NVMe-oF transport on Kubernetes, configured on a StoragePool and reconciled by the operator."
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

Security is configured per storage pool and is disabled by default. It is enabled by setting `dhchap` on the
`StoragePool` and listing the worker nodes that are allowed to connect to the pool in `allowedNodes`.

```yaml title="Example of a StoragePool with DHCHAP enabled for two worker nodes"
apiVersion: storage.simplyblock.io/v1alpha1
kind: StoragePool
metadata:
  name: pool-a
  namespace: simplyblock
spec:
  clusterName: cluster-a
  dhchap: true
  allowedNodes:
    - worker-1
    - worker-2
```

The DH-HMAC-CHAP keys of the pool are generated as soon as `dhchap` is set. Authentication is only enforced once
`allowedNodes` is non-empty.

Both fields belong into the manifest that creates the pool. The `StorageClass` generated for the pool is only
restricted to the allowed nodes when `dhchap` is `true` and `allowedNodes` is non-empty at the moment the class is
created, and `parameters` and `allowedTopologies` cannot be patched afterward. A pool created with `dhchap: true` and
an empty `allowedNodes` therefore keeps an unrestricted `StorageClass` for the rest of its life, even once nodes are
added to the list. Recreating the pool is the only way to correct this.

## Reconciliation by the Operator

Once the storage pool is created, host registration and node scheduling are reconciled by the operator:

- **Allowed hosts:** each node in `allowedNodes` is registered as an allowed host of the pool, under a deterministic
  NQN derived from that node's Kubernetes UID (`nqn.2014-08.io.simplyblock:uuid:<node-uid>`).
- **Node labels:** each allowed node is labeled `simplyblock.io/pool.<namespace>.<cluster>.<pool>: allowed`, and the
  label is removed again from every node that leaves the list.
- **First scheduling decision:** the generated `StorageClass` is restricted to that label through `allowedTopologies`,
  so the first `Pod` to consume a `PersistentVolumeClaim` of this pool can only be scheduled onto an allowed node.
- **Every later scheduling decision:** the same label is written into the `nodeAffinity` of the `PersistentVolume`
  when the volume is created, which restricts every scheduling decision on the already-bound volume, including a
  restart, a recreate, and a drain.
- **Host NQN:** the node's own NQN and the pool's DHCHAP secrets are presented by the CSI node plugin on connect, so
  no host NQN has to be supplied anywhere in the Kubernetes flow.

## Managing Allowed Nodes

`dhchap` is immutable, because the `parameters` and `allowedTopologies` of the generated `StorageClass` cannot be
patched in the Kubernetes API once it exists. `allowedNodes` stays mutable. Changing it relabels the nodes and updates
the pool's allowed hosts, and it never rewrites the `StorageClass`.

A node removed from `allowedNodes` loses its label, and its NQN is removed from the allowed hosts of the pool and of
every volume in it. The node is rejected on its next connect attempt. A volume already connected on that node is not
disconnected by the removal.

## Verifying the Configuration

`status.allowedNodes` carries the node names last registered on the control plane. A difference to `spec.allowedNodes`
means the pool has not converged yet.

```bash title="Reading the allowed nodes registered for a storage pool"
kubectl get storagepool pool-a -n simplyblock \
    -o jsonpath='{.status.allowedNodes}'
```

The nodes carrying the pool's label are listed through a label selector. The result has to match `status.allowedNodes`.

```bash title="Listing the nodes labeled as allowed for a storage pool"
kubectl get nodes \
    -l simplyblock.io/pool.simplyblock.cluster-a.pool-a=allowed
```

Whether the generated `StorageClass` restricts scheduling at all is visible in its `allowedTopologies`. An empty result
means the class was created while `allowedNodes` was empty.

```bash title="Checking the topology restriction of the generated storage class"
kubectl get storageclass simplyblock-simplyblock-cluster-a-pool-a \
    -o jsonpath='{.allowedTopologies}'
```

## Pods on a Disallowed Node

`allowedTopologies` and the `nodeAffinity` of the `PersistentVolume` keep a `Pod` off a node outside `allowedNodes`.
If one lands there regardless, no `nvme connect` is ever built. `NodeStageVolume` derives the host NQN of its own node
and requests the connection information from the control plane, which rejects the unknown NQN with an HTTP `404`. The
`Pod` stays unscheduled with a `FailedMount` event.

```plain title="Example of a FailedMount event on a node outside the allowed nodes"
MountVolume.MountDevice failed for volume "pvc-...": rpc error: code = Internal
desc = failed to fetch connection: GET 404: Host NQN
nqn.2014-08.io.simplyblock:uuid:<node-uid> not found in allowed hosts for volume <lvol-id>
```

The node is either missing from `allowedNodes` or the pool has not converged yet. Both are checked as described in
[Verifying the Configuration](#verifying-the-configuration).

See the [Operator Reference](../../../reference/operator/reference.md) for the full `StoragePool` field list, and
[Storage Class](../../usage/storage-class.md) for the `dhchap_node_label` parameter this generates.

For a detailed explanation of the security mechanisms and configuration, see
[NVMe-oF Security](../../../architecture/concepts/nvmf-security.md). The equivalent flow for a plain Linux
installation is described in
[Host Authentication and Encryption ({{ cliname }})](../../../non-kubernetes/operations/security/authentication-encryption.md).
