---
title: "Volume Encryption"
description: "Encrypt simplyblock logical volumes at rest using the AES_XTS crypto bdev. Keys are managed by the cluster and can optionally be offloaded to an external KMS."
weight: 40000
---

Simplyblock supports encryption of logical volumes at rest, ensuring that sensitive data remains protected across the
distributed storage cluster. Internally, simplyblock uses the industry-proven
[crypto bdev](https://spdk.io/doc/bdev.html){:target="_blank" rel="noopener"} provided by SPDK, with an AES_XTS
variable-length block cipher.

Encryption is enabled per StorageClass and applies to every volume provisioned from it.

!!! warning
    Encryption must be specified at the time of volume creation. Existing logical volumes cannot be retroactively
    encrypted.

## Enabling Encryption on a StorageClass

To enable encryption, set the `encryption` parameter on the StorageClass to `"True"`. Every PersistentVolumeClaim
that references the StorageClass is then provisioned as an encrypted volume.

```yaml title="Encrypted StorageClass"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: my-encrypted-volumes
provisioner: csi.simplyblock.io
parameters:
  encryption: "True"
  # ... other parameters
reclaimPolicy: Delete
volumeBindingMode: Immediate
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

For environments that require stricter handling of key material — separation of duty between storage and key
custodians, regular rotation, or audit trails — the cluster can be configured to keep encryption keys in an external
Hashicorp Vault or Openbao instance. The setup is configured once per `StorageCluster` and applies to every encrypted
volume in that cluster.

See [Securing the Control Plane: External KMS](security.md#external-key-management-kms) for the full setup, or
[External Key Management](../../architecture/concepts/external-key-management.md) for the architectural background.
