---
title: "External Key Management"
description: "Data-at-rest encryption with external key management systems, enabling separation of duty, rotation, and audit."
weight: 30220
---

Volume encryption protects data at rest by ciphering every block written to a logical volume. To encrypt data, the
cipher itself needs a key. However, the question of *where that key lives and who controls it* is the responsibility of
the key management layer.

By default, simplyblock manages encryption keys internally. For environments with stricter security policies, such as
regulated environments or any deployment that separates storage and security duties, where the team operating the
storage cluster must not be in possession of the long-lived key material, the key-encryption keys can be offloaded to an
external Key Management Service (KMS).

Simplyblock supports storing keys in external KMS solutions. Currently supported KMS backends are:
- [HashiCorp Vault](https://www.vaultproject.io/){:target="_blank" rel="noopener"}
- [OpenBao](https://openbao.org/){:target="_blank" rel="noopener"}

## Two-Layer Key Model

When an external KMS is configured, simplyblock applies a two-layer key model:

- **Unseal Keys** are generated once and presented at the time of the KMS setup (for example, HashCorp Vault).
  Typically, a certain number of all the unseal keys are required to unseal the KMS (e.g., 3 of 5 keys). These keys
  should be stored in separate secure locations.
- **Data Encryption Keys (DEKs)** are generated per volume and used to encrypt the at-rest data blocks of that volume.
  These keys are short-lived in cluster memory and never stored in plaintext at rest. The wrapped DEKs are stored inside
  the external KMS.
- **Key Encryption Keys (KEKs)** live inside the KMS. The cluster asks the KMS to wrap each DEK on creation and to
  unwrap it when the volume is brought online. The KEKs never leave the KMS.

## Authentication and Trust

The KMS authenticates simplyblock components using a client certificate issued by the
`simplyblock-certificate-authority-issuer` ClusterIssuer, which the operator creates as part of its mTLS setup.
Because the KMS depends on this CA, [mTLS](../../deployments/kubernetes/security.md#transport-layer-security-mutual-tls-mtls)
must be configured on the control plane before an external KMS can be wired up.

Operationally, this means the KMS team and the storage team share only the CA bundle and an agreed-upon DNS-name for
the simplyblock client. No static passwords or long-lived tokens must be exchanged.

For the setup steps, see [Securing the Control Plane: External KMS](../../deployments/kubernetes/security.md#external-key-management-kms).
