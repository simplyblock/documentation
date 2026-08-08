---
title: "Encrypting a Logical Volume"
description: "Encrypting a Logical Volume: Simplyblock supports encryption of logical volumes (LVs) to protect data at rest, ensuring that sensitive information remains."
weight: 30500
---

Simplyblock supports encryption of logical volumes (LVs) to protect data at rest, ensuring that sensitive
information remains secure across the distributed storage cluster. Encryption is applied during volume creation using
the `{{ cliname }}` command line interface, and encrypted volumes are handled transparently during regular operation.

Encrypting Logical Volumes ensures that simplyblock storage meets data protection and compliance requirements,
safeguarding sensitive workloads without compromising performance.

!!! warning
    Encryption must be specified at the time of volume creation. Existing logical volumes cannot be retroactively
    encrypted.

## Prerequisites

- A running simplyblock cluster with encryption support enabled.
- `{{ cliname }}` installed and configured with access to the simplyblock management API.

## Encrypted Volumes in Simplyblock

Simplyblock supports the encryption of logical volumes. Internally, simplyblock utilizes the industry-proven
[crypto bdev](https://spdk.io/doc/bdev.html){:target="_blank" rel="noopener"} provided by SPDK to implement its encryption
functionality.

The encryption uses an AES_XTS variable-length block cipher.

The encryption keys are created and stored by the cluster's key management system (KMS) when the volume is
created. By default, simplyblock manages the keys internally. Alternatively, an external KMS (HashiCorp Vault or
OpenBao) can be configured at cluster creation time via `--hashicorp-vault-url`. See
[External Key Management](../../architecture/concepts/external-key-management.md) for the architecture.

!!! note
    Earlier releases required manually generated keys passed via `--crypto-key1` and `--crypto-key2`. These
    parameters are deprecated since 26.2 and cannot be used anymore. Key handling is fully KMS-based.

## Creating an Encrypted Logical Volume

To provision a new Logical Volume with encryption enabled:

```bash title="Create an encrypted logical volume"
{{ cliname }} volume add \
  --encrypt \
  <VOLUME_NAME> \
  <VOLUME_SIZE> \
  <POOL_NAME>
```

To see all available parameters when creating a logical volume, see [Provisioning](provisioning.md).

### Parameters

| Parameter   | Description                                      | Default |
|-------------|--------------------------------------------------|---------|
| `--encrypt` | Enables inline encryption on the logical volume. | false   |

## Verification

Check encryption status with:

```bash
{{ cliname }} volume get <VOLUME_UUID>
```

Look for the encryption field to confirm that encryption is active.
