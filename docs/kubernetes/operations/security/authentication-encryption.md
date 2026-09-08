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

Both fields belong in the manifest that creates the pool. The `StorageClass` generated for the pool only carries
`dhchap_node_label` when `dhchap` is `true` and `allowedNodes` is non-empty at the moment the class is created, and
`parameters` cannot be patched afterward. A pool created with `dhchap: true` and an empty `allowedNodes` therefore
keeps an unrestricted `StorageClass` for the rest of its life, even once nodes are added to the list. Recreating the
pool is the only way to correct this.

## Reconciliation by the Operator

Once the storage pool is created, host registration and node scheduling are reconciled by the operator:

- **Allowed hosts:** each node in `allowedNodes` is registered as an allowed host of the pool, under a deterministic
  NQN derived from that node's Kubernetes UID (`nqn.2014-08.io.simplyblock:uuid:<node-uid>`).
- **Node labels:** each allowed node is labeled `simplyblock.io/pool.<namespace>.<cluster>.<pool>=allowed`, and the
  label is removed again from every node that leaves the list.
- **Volume placement:** the same label is written into the `nodeAffinity` of the `PersistentVolume` when the volume is
  created, which is what restricts the volume to the allowed nodes.
- **First scheduling decision:** the first `Pod` to consume a `PersistentVolumeClaim` of this pool is placed before
  its volume exists, so it may be assigned to any node. The scheduler then rejects that assignment against the new
  volume's `nodeAffinity` (`node affinity doesn't match node`) without binding the `Pod`, and reschedules it onto an
  allowed node. A one-off `FailedScheduling` event during this hand-off is expected and self-correcting.
- **Every later scheduling decision:** the volume now exists, so its `nodeAffinity` filters candidate nodes from the
  first attempt, including on a restart, a recreate, and a drain.
- **Host NQN:** the node's own NQN and the pool's DHCHAP secrets are presented by the CSI node plugin on connect, so
  no host NQN has to be supplied anywhere in the Kubernetes flow.

## Managing Allowed Nodes

`dhchap` is immutable, because the `parameters` of the generated `StorageClass` cannot be patched in the Kubernetes
API once it exists. `allowedNodes` stays mutable. Changing it relabels the nodes and updates the pool's allowed hosts,
and it never rewrites the `StorageClass`.

A node removed from `allowedNodes` loses its label, and its NQN is removed from the allowed hosts of the pool and of
every volume in it. The node is rejected on its next connect attempt. A volume already connected on that node is not
disconnected by the removal.

## Enforcement Through a Custom Storage Class

The restriction reaches a volume through the `dhchap_node_label` parameter, whose value the CSI driver writes into the
`nodeAffinity` of every `PersistentVolume` it provisions from the class. It applies when a node mounts the volume, not
when the claim is bound, and the operator always sets it on the class it generates.

!!! warning "A custom storage class without `dhchap_node_label` is not enforced"

    A `StorageClass` that names a DHCHAP pool in `pool_name` but omits `dhchap_node_label` provisions volumes with no
    `nodeAffinity`, so no node restriction applies at all, even though the pool reports DHCHAP as enabled. A `Pod`
    outside `allowedNodes` is scheduled and its volume is attached, and only the connection is refused, as described
    in [Pods on a Disallowed Node](#pods-on-a-disallowed-node).

### The Value to Set

The parameter takes the label **key** the operator writes onto the pool's allowed nodes. It is not a node name, and
it is not the label's value. The driver always matches the fixed value `allowed`. The key is derived from the pool:

```plain title="Format of the dhchap_node_label value"
simplyblock.io/pool.<namespace>.<storageCluster CR name>.<pool name>
```

| Segment                    | Source                                                                             |
|----------------------------|------------------------------------------------------------------------------------|
| `<namespace>`              | the namespace of the `StoragePool`, which is also its `StorageCluster`'s namespace |
| `<storageCluster CR name>` | `StoragePool.spec.clusterName`, the name of the `StorageCluster` CR, not its UUID  |
| `<pool name>`              | `StoragePool.metadata.name`, the CR name, not the pool's `status.uuid`             |

For the `pool-a` example above, created in namespace `simplyblock` against `StorageCluster` `cluster-a`, the key is
`simplyblock.io/pool.simplyblock.cluster-a.pool-a`:

```yaml title="Custom StorageClass for a DHCHAP pool"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: custom-dhchap-sc
provisioner: csi.simplyblock.io
volumeBindingMode: WaitForFirstConsumer
parameters:
  cluster_id: <STORAGE_CLUSTER_UUID>
  pool_name: pool-a
  dhchap_node_label: simplyblock.io/pool.simplyblock.cluster-a.pool-a
```

Rather than deriving the key, it can be read off the cluster. Either from an allowed node:

```bash title="Read the key from an allowed node"
kubectl get node <ALLOWED_NODE> -o jsonpath='{.metadata.labels}' \
  | tr ',' '\n' | grep 'simplyblock.io/pool\.'
```

Or from the `StorageClass` the operator already generated for the same pool, which is the authoritative value:

```bash title="Read the key from the generated StorageClass"
kubectl get storageclass simplyblock-<namespace>-<storageCluster CR name>-<pool name> \
  -o jsonpath='{.parameters.dhchap_node_label}'
```

!!! note "A wrong key is silently unsatisfiable"

    The key is not validated against the pool. A `StorageClass` carrying a key no node holds still provisions
    volumes, but their `nodeAffinity` matches nothing, so every `Pod` consuming one stays `Pending` with
    `didn't match PersistentVolume's node affinity`. Reading the key off the cluster avoids the typo.

## Worker Node Kernel Requirements

Every node in `allowedNodes` needs a kernel built for DH-HMAC-CHAP. A newer kernel is not automatically a supported
one, and [NVMe-oF Security](../../../architecture/concepts/nvmf-security.md) lists the option per kernel version. A
node is checked through the CSI node plugin `Pod` running on it, which mounts the host's `/dev`:

```bash title="Checking a worker node for DH-HMAC-CHAP support"
kubectl exec -n simplyblock <CSI_NODE_POD> -c csi-node -- cat /dev/nvme-fabrics | grep -o dhchap_secret
```

Without the option, the volume is attached normally and only the mount fails, with `option "dhchap_secret" ignored`
in the `FailedMount` event of a `Pod` left in `ContainerCreating`. Such a node is either left out of `allowedNodes`,
or booted with a kernel that carries the option.

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

Whether the generated `StorageClass` restricts scheduling at all is visible in its `dhchap_node_label` parameter. An
empty result means the class was created while `allowedNodes` was empty.

```bash title="Checking the node restriction of the generated storage class"
kubectl get storageclass simplyblock-simplyblock-cluster-a-pool-a \
    -o jsonpath='{.parameters.dhchap_node_label}'
```

## Pods on a Disallowed Node

The `nodeAffinity` of the `PersistentVolume` keeps a `Pod` off a node outside `allowedNodes`. If one lands there
regardless (pinned there by a `nodeSelector`, for instance), no `nvme connect` is ever built. `NodeStageVolume` derives the host NQN of its own node
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
