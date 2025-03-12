---
title: "Encrypting"
weight: 40500
---

Simplyblock supports encryption of logical volumes (LVs) to protect data at rest, ensuring that sensitive
information remains secure across the distributed storage cluster. Encryption is applied during volume creation as
part of the storage class specification.

Encrypting Logical Volumes ensure that simplyblock storage meets data protection and compliance requirements,
safeguarding sensitive workloads without compromising performance.

!!! warning
    Encryption must be specified at the time of volume creation. Existing logical volumes cannot be retroactively
    encrypted.

## Encrypting Volumes with Simplyblock

Simplyblock supports the encryption of logical volumes. Internally, simplyblock utilizes the industry-proven
[crypto bdev](https://spdk.io/doc/bdev.html){:target="_blank" rel="noopener"} provided by SPDK to implement its encryption
functionality.

The encryption uses a AES_XTS variable length block cipher. This cipher requires two keys of 16 to 32 bytes each. The
keys need to have the same length, meaning, if one key is 32 bytes long, the other one has to be 32 bytes, too.

!!! recommendation
    Simplyblock strongly recommends two keys of 32 bytes.


## Generate Random Keys

Simplyblock does not provide an integrated way to generate encryption keys but recommends using the OpenSSL tool chain.
For Kubernetes, the encryption key needs to be provided as base64, hence it's encoded right away.

To generate the two keys, the following command is run twice. The result must be stored for later.

```bash title="Create en Encryption Key"
openssl rand -hex 32 | base64 -w0
```

## Create the Kubernetes Secret

Next up, a Kubernetes Secret is created, providing the just created two encryption keys.

```yaml title="Create a Kubernetes Secret Resource"
apiVersion: v1
kind: Secret
metadata:
  name: my-encryption-keys
data:
  crypto_key1: YzIzYzllY2I4MWJmYmY1ZDM5ZDA0NThjNWZlNzQwNjY2Y2RjZDViNWE4NTZkOTA5YmRmODFjM2UxM2FkZGU4Ngo=
  crypto_key2: ZmFhMGFlMzZkNmIyODdhMjYxMzZhYWI3ZTcwZDEwZjBmYWJlMzYzMDRjNTBjYTY5Nzk2ZGRlZGJiMDMwMGJmNwo=
```

The Kubernetes Secret can be used for one or more logical volumes. Using different encryption keys, multiple tenants
can be secured with an additional isolation layer against each other.

## StorageClass Configuration

A new Kubernetes StorageClass needs to be created, or an existing one needs to be configured. To use encryption on a
persistent volume claim level, the storage class has to be set for encryption.

```yaml title="Example StorageClass"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: my-encrypted-volumes
provisioner: csi.simplyblock.io
parameters:
  encryption: "True" # This is important!
  ... other parameters
reclaimPolicy: Delete
volumeBindingMode: Immediate
allowVolumeExpansion: true
```

## Create a PersistentVolumeClaim

When requesting a logical volume through a Kubernetes PersistentVolumeClaim, the storage class and the secret resources
have to be connected to the PVC. When picked up, simplyblock will automatically collect the keys and creates the logical
volumes as a fully encrypted logical volume.

```yaml title="Create an encrypting PersistentVolumeClaim"
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  annotations:
    simplybk/secret-name: my-encryption-keys # Encryption keys
  name: my-encrypted-volume-claim
spec:
  storageClassName: my-encrypted-volumes # StorageClass
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 200Gi
```
