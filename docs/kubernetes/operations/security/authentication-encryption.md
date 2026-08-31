---
title: Host Authentication and Encryption
description: "Configure NVMe-oF host access control, DH-HMAC-CHAP authentication, and TLS/PSK encryption on Kubernetes through the StoragePool custom resource."
weight: 10710
---

Simplyblock supports NVMe-oF transport security to protect data in transit and restrict host access to storage
subsystems. This includes:

- **Host access control:** restrict which hosts (by NQN) can connect to a volume's NVMe-oF subsystem.
- **DH-HMAC-CHAP authentication:** mutual authentication between host and target using the NVMe standard
  authentication protocol (TP8018).
- **TLS/PSK encryption:** encrypt data in transit using TLS 1.3 with Pre-Shared Keys.

On Kubernetes, transport security is configured declaratively on the `StoragePool` custom resource and reconciled
by the Simplyblock Operator. No host NQN has to be registered and no key has to be provisioned by hand.

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

The keys are generated as soon as `dhchap` is set, but authentication is only enforced once `allowedNodes` is
non-empty.

## Reconciliation by the Operator

Once the storage pool is created, host registration and node scheduling are reconciled by the operator:

- Each node in `allowedNodes` is registered as an allowed host of the pool, under a deterministic NQN derived
  from that node's Kubernetes UID (`nqn.2014-08.io.simplyblock:uuid:<node-uid>`).
- Each allowed node is labeled `simplyblock.io/pool.<namespace>.<cluster>.<pool>: allowed`, and the generated
  `StorageClass` is restricted to that label through `allowedTopologies`. The first `Pod` to consume a
  `PersistentVolumeClaim` of this pool can therefore only be scheduled onto an allowed node.
- The same label is written into the `nodeAffinity` of the `PersistentVolume` when the volume is created, which
  restricts every later scheduling decision on the already-bound volume.
- The node's own NQN and the pool's DHCHAP secrets are presented by the CSI node plugin on connect, so no host
  NQN has to be supplied anywhere in the Kubernetes flow.

## Managing Allowed Nodes

`dhchap` is immutable, because the `parameters` and `allowedTopologies` of the generated `StorageClass` cannot
be patched in the Kubernetes API once it exists. `allowedNodes` stays mutable. Changing it relabels the nodes
and updates the pool's allowed hosts, and it never rewrites the `StorageClass`.

See the [Operator Reference](../../../reference/operator/reference.md) for the full `StoragePool` field list,
and [Storage Class](../../usage/storage-class.md) for the `dhchap_node_label` parameter this generates.

For a detailed explanation of the security mechanisms and configuration, see
[NVMe-oF Security](../../../architecture/concepts/nvmf-security.md). The equivalent flow for a plain Linux
installation is described in
[Host Authentication and Encryption ({{ cliname }})](../../../non-kubernetes/operations/security/authentication-encryption.md).
