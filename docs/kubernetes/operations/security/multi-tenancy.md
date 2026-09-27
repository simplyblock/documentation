---
title: "Multi-Tenancy"
description: "Isolate tenants on Kubernetes with one StorageCluster per namespace, StoragePools as tenancy units, and the RBAC aggregate roles."
weight: 10720
---

Simplyblock is designed to support secure and efficient multi-tenancy, enabling multiple independent tenants to share
the same physical infrastructure without compromising data isolation, performance guarantees, or security. On
Kubernetes, tenancy is built from three pieces: a namespace per storage cluster, a `StoragePool` per tenant inside a
cluster, and standard Kubernetes RBAC on top of both.

## One StorageCluster per Namespace

A namespace holds at most one `StorageCluster`, which a validating webhook enforces. Every object that belongs to the
cluster lives in the same namespace: its `StorageNode`, `StorageDevice`, and `StoragePool` objects, its backup
policies and backups, and all operations on them. A `StoragePool` whose `clusterRef` names a cluster outside its own
namespace is rejected.

This turns "administrator of cluster `production`" into "administrator of the namespace where `StorageCluster`
`production` lives," which is a problem Kubernetes RBAC already solves. The recommended layout is one namespace per
storage cluster.

## Storage Pools as Tenancy Units

Inside a cluster, the `StoragePool` is the tenancy unit. A pool carries three groups of settings:

- **`limits`:** the budget of the pool as a whole: `capacity`, `maxVolumeSize`, `iops`, and `throughput` (`read`,
  `write`, `readWrite`, in MB/s). The limits are mutable.
- **`volumeDefaults`:** what every volume of the pool is created with: per-volume `iops` and `throughput`, the
  `filesystem`, compression, encryption, replication, `enableDHCHAP`, and more. The block is immutable once set,
  because it is carried into StorageClass parameters, which Kubernetes does not allow to change.
- **`allowedNodes`:** the Kubernetes nodes allowed to connect to the pool's volumes (see
  [Host Authentication and Encryption](authentication-encryption.md)).

```yaml title="Example of a StoragePool for one tenant"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StoragePool
metadata:
  name: tenant-a
  namespace: simplyblock
spec:
  clusterRef: production
  limits:
    capacity: 10T
    maxVolumeSize: 2T
    iops: 200000
    throughput:
      readWrite: 4096
  volumeDefaults:
    iops: 20000
    throughput:
      readWrite: 512
    filesystem: xfs
    enableEncryption: true
```

In this example, the pool may use 10 TB and 200,000 IOPS in total, and each volume defaults to 20,000 IOPS, so ten busy
volumes saturate the pool. All volumes of the tenant count toward the pool's capacity.

A tenant's workloads reach the pool through a StorageClass assigned to it, which is authored for every pool but the
cluster's default pool (see [Storage Class](../../usage/storage-class.md)). The capacity of each pool is readable
through the `StoragePoolMetrics` resource (`kubectl get spm`), see
[Capacity Metrics API](../monitoring/index.md#capacity-metrics-api).

### Logical Volume Isolation

If a tenant is expected to have only one volume or strong isolation between volumes is required, each logical volume
can be seen as fully isolated at the storage layer. Access to volumes is tightly controlled, and each volume is only
exposed to the hosts explicitly granted access.

## Access Control with Kubernetes RBAC

The Simplyblock Operator delegates user authorization entirely to Kubernetes RBAC. It installs two ClusterRoles that
aggregate into the built-in roles:

| Operator ClusterRole            | Aggregates into | Grants on `StorageCluster` and `StoragePool`                  |
|---------------------------------|-----------------|---------------------------------------------------------------|
| `simplyblock-aggregate-to-view` | `view`          | `get`, `list`, `watch` (including `status`)                   |
| `simplyblock-aggregate-to-edit` | `edit`, `admin` | `get`, `list`, `watch`, `create`, `update`, `patch`, `delete` |

A third ClusterRole, `simplyblock-metrics-aggregate-to-view`, aggregates `get` and `list` on the five capacity metrics
resources of `metrics.simplyblock.io` into `view`.

Anyone bound to the built-in `view`, `edit`, or `admin` role in a namespace therefore gets the corresponding access to
the `StorageCluster` and the `StoragePool` objects of that namespace. For example, to make `alice` an administrator of
the cluster in namespace `cluster-prod`:

```bash title="Granting namespace admin rights on a storage cluster"
kubectl create rolebinding alice-admin \
    --clusterrole=admin \
    --user=alice \
    --namespace=cluster-prod
```

!!! note
    The aggregate roles cover `StorageCluster` and `StoragePool` only. Access to the operation kinds (for example,
    `StorageClusterOps`, `StorageNodeOps`, and `PersistentVolumeOps`) and to the other simplyblock kinds is granted
    with explicit Roles or ClusterRoles.

### Per-Resource Scoping

For finer-grained delegation, for example, administration of one `StorageCluster` only, a Role with `resourceNames` is
written:

```yaml title="Example of a Role scoped to one StorageCluster"
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: prod-cluster-admin
  namespace: cluster-prod
rules:
- apiGroups: ["storage.simplyblock.io"]
  resources: ["storageclusters"]
  resourceNames: ["prod"]
  verbs: ["get", "update", "patch", "delete"]
- apiGroups: ["storage.simplyblock.io"]
  resources: ["storageclusters/status"]
  resourceNames: ["prod"]
  verbs: ["get"]
```

`resourceNames` only filters the verbs that target a named object (`get`, `update`, `patch`, `delete`). It is ignored
for `list`, `watch`, and `create`, so enumerating the clusters requires a separate binding, for example, to the `view`
role. This is a property of Kubernetes RBAC, not of the operator.

## Quality of Service

To prevent noisy neighbor effects and ensure fair resource allocation, simplyblock supports per-volume Quality of
Service (QoS) limits in addition to the pool limits. Per-volume limits are set through the pool's `volumeDefaults`,
the StorageClass, or PVC annotations, as described in [Defining Quality of Service](../../usage/quality-of-service.md).

## NVMe-oF Transport Security

To enforce tenant isolation at the transport layer, simplyblock supports NVMe-oF host access control and DH-HMAC-CHAP
authentication per storage pool. By restricting which host NQNs can connect to a volume's subsystem and requiring
authenticated connections, tenants are cryptographically isolated at the network level. Security keys are generated
per storage pool, so tenants in different pools have distinct credentials.

See [Host Authentication and Encryption](authentication-encryption.md) for the configuration, and
[NVMe-oF Security](../../../architecture/concepts/nvmf-security.md) for the background.

## Encryption and Data Security

Volume data can be encrypted at rest with AES-based cryptographic algorithms. Encryption is applied at the volume
level, so tenant data remains secure and inaccessible to other users, even at the physical storage layer. It is
switched on for a whole pool through `volumeDefaults.enableEncryption`, or per StorageClass, as described in
[Volume Encryption](../../usage/volume-encryption.md).
