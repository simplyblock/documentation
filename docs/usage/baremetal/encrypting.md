---
title: "Encrypting a Logical Volume"
weight: 30500
---

Simplyblock supports encryption of logical volumes (LVs) to protect data at rest, ensuring that sensitive
information remains secure across the distributed storage cluster. Encryption is applied during volume creation using
the `{{ variables.cliname }}` command line interface, and encrypted volumes are handled transparently during regular operation.

Encrypting Logical Volumes ensures that simplyblock storage meets data protection and compliance requirements,
safeguarding sensitive workloads without compromising performance.

!!! warning
    Encryption must be specified at the time of volume creation. Existing logical volumes cannot be retroactively
    encrypted.

## Prerequisites

- A running simplyblock cluster with encryption support enabled.
- `{{ variables.cliname }}` installed and configured with access to the Simplyblock management API.

## Encrypted Volumes in Simplyblock

Simplyblock supports the encryption of logical volumes. Internally, simplyblock utilizes the industry-proven
[crypto bdev](https://spdk.io/doc/bdev.html){:target="_blank" rel="noopener"} provided by SPDK to implement its encryption
functionality.

The encryption uses an AES_XTS variable-length block cipher. This cipher requires two keys of 16 to 32 bytes each. The
keys need to have the same length, meaning that if one key is 32 bytes long, the other one has to be 32 bytes, too.

!!! recommendation
    Simplyblock strongly recommends two keys of 32 bytes.

## Generate Random Keys

Simplyblock does not provide an integrated way to generate encryption keys, but recommends using the OpenSSL tool chain.

To generate the two keys, the following command is run twice. The result must be stored for later.

```bash title="Create an Encryption Key"
openssl rand -hex 32
```

## Creating an Encrypted Logical Volume

To provision a new Logical Volume with encryption enabled:

```bash
{{ variables.cliname }} volume add \
  --encrypt \
  --crypto-key1 <HEX_KEY_1> \
  --crypto-key2 <HEX_KEY_2> \
  <VOLUME_NAME> \
  <VOLUME_SIZE> \
  <POOL_NAME>
```

To see all available parameters when creating a logical volume, see [Provisioning](provisioning.md).

### Parameters

| Parameter                     | Description                                      | Default |
|-------------------------------|--------------------------------------------------|---------|
| --encrypt                     | Enables inline encryption on the logical volume. | false   |
| --crypto-key1 CRYPTO_KEY1     | The hex value of the first encryption key.       |         |
| --crypto-key2 CRYPTO_KEY2     | The hex value of the second encryption key.      |         |

## Verification

Check encryption status with:

```bash
{{ variables.cliname }} volume get <VOLUME_UUID>
```

Look for the encryption field to confirm that encryption is active.
