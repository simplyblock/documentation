---
title: "Volume Encryption"
description: "Encrypt simplyblock logical volumes at rest using the AES_XTS crypto bdev. Keys are managed by the cluster and can optionally be offloaded to an external KMS."
weight: 40000
---

Simplyblock supports encryption of logical volumes at rest, ensuring that sensitive data remains protected across the
distributed storage cluster. Internally, simplyblock uses the industry-proven
[crypto bdev](https://spdk.io/doc/bdev.html){:target="_blank" rel="noopener"} provided by SPDK, with an AES_XTS
variable-length block cipher.

Encryption is enabled per StorageClass, through the `encryption` parameter, and applies to every volume provisioned
from it. For a storage pool, it is normally stated once in `StoragePool.spec.volumeDefaults.enableEncryption`, which the
pool's StorageClass carries as `encryption`.

!!! warning
    Encryption must be specified at the time of volume creation. Existing logical volumes cannot be retroactively
    encrypted.

## Enabling Encryption for a Storage Pool

A pool whose volumes are all encrypted declares it in its volume defaults. The block is immutable once set, so the
setting belongs in the manifest that creates the pool.

```yaml title="Example of a StoragePool with encrypted volumes"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StoragePool
metadata:
  name: encrypted
  namespace: simplyblock
spec:
  clusterRef: production
  volumeDefaults:
    enableEncryption: true
```

## Enabling Encryption on a StorageClass

The StorageClass assigned to the pool sets the `encryption` parameter to `"true"`. Every PersistentVolumeClaim that
references the StorageClass is then provisioned as an encrypted volume.

```yaml title="Example of an encrypted StorageClass"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: my-encrypted-volumes
  labels:
    storage.simplyblock.io/namespace: simplyblock
    storage.simplyblock.io/cluster: production
    storage.simplyblock.io/pool: encrypted
provisioner: csi.simplyblock.io
parameters:
  cluster_id: <CLUSTER_UUID>
  pool_name: encrypted
  encryption: "true"
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

A PersistentVolumeClaim using this StorageClass is then encrypted automatically:

```yaml title="Encrypted PersistentVolumeClaim"
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-encrypted-volume-claim
spec:
  storageClassName: my-encrypted-volumes
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 200Gi
```

## Key Management

Encryption keys are generated and managed by the simplyblock cluster. No user-supplied keys, per-PVC Secrets, or
annotations are required to encrypt a volume.

!!! warning "Migration from earlier versions"
    Previous releases required a user-managed Kubernetes Secret (containing `crypto_key1` and `crypto_key2`) to be
    referenced from each PVC via the `simplyblock.io/secret-name` (or legacy `simplybk/secret-name`) annotation.
    That mechanism is **no longer used** for new volumes. Existing encrypted volumes provisioned with user-supplied
    keys continue to work, but new PVCs should not set those annotations.

## Hardening Key Storage with an External KMS

For environments that require stricter handling of key material (separation of duty between storage and key
custodians, regular rotation, or audit trails), the cluster can be configured to keep encryption keys in an external
HashiCorp Vault or OpenBao instance. The key store is set once per `StorageCluster`, in `spec.kms`, and applies to
every encrypted volume in that cluster.

```yaml title="Example of an external key store on a StorageCluster"
apiVersion: storage.simplyblock.io/v1alpha2
kind: StorageCluster
metadata:
  name: production
  namespace: simplyblock
spec:
  # ... other fields ...
  kms:
    vault:
      endpoint: https://vault.example.com:8200
```

The whole `kms` block is immutable, because switching the key store of a cluster that holds encrypted volumes is not
supported. The endpoint is refused when it resolves to a loopback or a link-local address.

See [Securing the Control Plane](../installation/security.md) for the full setup, or
[External Key Management](../../architecture/concepts/external-key-management.md) for the architectural background.
