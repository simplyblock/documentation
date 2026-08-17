---
title: Host Authentication and Encryption
description: "Simplyblock provides host access control, DH-HMAC-CHAP authentication, and TLS/PSK encryption for NVMe-oF connections."
weight: 30110
---

Simplyblock supports NVMe-oF transport security to protect data in transit and restrict host access to storage
subsystems. This includes:

- **Host access control:** restrict which hosts (by NQN) can connect to a volume's NVMe-oF subsystem.
- **DH-HMAC-CHAP authentication:** mutual authentication between host and target using the NVMe standard
  authentication protocol (TP8018).
- **TLS/PSK encryption:** encrypt data in transit using TLS 1.3 with Pre-Shared Keys.

## Enable Host Authentication and Encryption

At cluster creation time, required security keys are automatically generated. No additional configuration is required.
Adding allowed hosts to a storage pool automatically provisions the required security keys.

However, host authentication and transport layer encryption can be configured at a storage pool level. That means, when
a storage pool is created, security can be enabled for that pool. By default, host authentication and encryption are
disabled.

```bash title="Enable Host Authentication and Encryption"
{{ cliname }} storage-pool add <POOL_ID> --dhchap
```

## Managed Allowed Hosts for Host Authentication

Once an encryption-enabled storage pool is configured, hosts can be managed using the following commands:

```bash title="Manage Allowed Hosts per Volume"
# Add an allowed host
{{ cliname }} storage-pool add-host <POOL_ID> <HOST_NQN>

# Remove an allowed host
{{ cliname }} storage-pool remove-host <POOL_ID> <HOST_NQN>
```

## Connecting a Volume with Host Access Control and Encryption

When connecting a volume with host access control enabled, the `--host-nqn` flag is required:

```bash title="Connect Volume with Host NQN"
{{ cliname }} volume connect <VOLUME_ID> --host-nqn <HOST_NQN>
```

For a detailed explanation of the security mechanisms and configuration, see
[NVMe-oF Security](../../../architecture/concepts/nvmf-security.md).

## Configuring DHCHAP via the StoragePool CRD

On Kubernetes deployments managed by the simplyblock operator, DHCHAP and host access control are configured
declaratively on the `StoragePool` custom resource instead of via `{{ cliname }}` directly:

```yaml title="Enable DHCHAP and restrict a pool to specific Kubernetes nodes"
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

The operator reconciles this into everything the CLI-based flow above does manually:

- Registers each node in `allowedNodes` as an allowed host, using a deterministic NQN derived from that
  node's Kubernetes UID (`nqn.2014-08.io.simplyblock:uuid:<node-uid>`) — no manual `--host-nqn` bookkeeping.
- Labels each allowed node and creates a StorageClass restricted to those nodes (`allowedTopologies`), so a
  Pod using this pool's PersistentVolumeClaim can only ever be scheduled onto an allowed node.
- The CSI node plugin on each node automatically presents that node's own NQN and DHCHAP secret when
  connecting — no `--host-nqn` needs to be supplied anywhere in the Kubernetes flow.

`dhchap` and `allowedNodes` are immutable once set, the same as `StorageClassParameters`. See the
[Operator Reference](../../../reference/operator/reference.md) for the full `StoragePool` field list, and
[Storage Class](../../usage/storage-class.md) for the `dhchap_node_label` parameter this generates.
