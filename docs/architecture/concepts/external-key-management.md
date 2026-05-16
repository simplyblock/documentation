---
title: "External Key Management"
description: "An external KMS keeps the keys that protect simplyblock volume encryption material outside the storage cluster, enabling separation of duty, rotation, and audit."
weight: 30220
---

Volume encryption protects data at rest by ciphering every block written to a logical volume. The cipher itself
needs a key; the question of *where that key lives and who controls it* is the responsibility of the key management
layer.

By default, simplyblock manages encryption keys internally. For environments where the team operating the storage
cluster should not also be in possession of the long-lived key material — common in regulated environments and any
deployment that separates storage and security duties — the key-encryption keys can be offloaded to an external Key
Management Service (KMS). Simplyblock supports [Hashicorp Vault](https://www.vaultproject.io/){:target="_blank" rel="noopener"}
and [Openbao](https://openbao.org/){:target="_blank" rel="noopener"} as KMS backends.

## Two-Layer Key Model

When an external KMS is configured, simplyblock applies a two-layer model:

- **Data Encryption Keys (DEKs)** are generated per volume and used to encrypt the blocks of that volume. They are
  short-lived in cluster memory and never stored in plaintext at rest.
- **Key Encryption Keys (KEKs)** live in the KMS. The cluster asks the KMS to wrap each DEK on creation and to unwrap
  it when the volume is brought online. The KEKs never leave the KMS.

Compromise of the cluster does not compromise the KEKs; compromise of the KMS does not directly expose any specific
volume's data, because DEKs are wrapped against the KEK rather than stored alongside it.

## Authentication and Trust

The KMS authenticates simplyblock components using a client certificate issued by the
`simplyblock-certificate-authority-issuer` ClusterIssuer, which the operator creates as part of its mTLS setup.
Because the KMS depends on this CA, [control-plane mTLS](../../deployments/kubernetes/security.md#transport-layer-security-mtls)
must be configured before an external KMS can be wired up.

Operationally, this means the KMS team and the storage team share only the CA bundle and an agreed-upon DNS name for
the simplyblock client — no static passwords or long-lived tokens are exchanged.

For the setup steps, see [Securing the Control Plane: External KMS](../../deployments/kubernetes/security.md#external-key-management-kms).
