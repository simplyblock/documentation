---
title: "External Key Management"
description: "How simplyblock encrypts data at rest against an external key management system, and what separation of duty, key rotation, and audit that buys."
source: "https://docs.simplyblock.io/latest/architecture/concepts/external-key-management/"
---

# External Key Management

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

- **Unseal Keys** are generated once and presented at the time of the KMS setup (for example, HashiCorp Vault).
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
Because the KMS depends on this CA, [mTLS](../../kubernetes/installation/security.md#transport-layer-security-mutual-tls-mtls)
must be configured on the control plane before an external KMS can be wired up.

Operationally, this means the KMS team and the storage team share only the CA bundle and an agreed-upon DNS-name for
the simplyblock client. No static passwords or long-lived tokens must be exchanged.

## Where the KMS Runs

A volume of the cluster is only usable once its DEK has been unwrapped, which makes the KMS a dependency of the data
path. The KMS must therefore not store its own state on the cluster it holds the keys for. Such a deployment
deadlocks on a cold start: the KMS waits for its data volume, and that volume waits for the KMS to unwrap its key.
The state cannot be recovered from inside the cluster, so the KMS is placed on storage that is available before
simplyblock is.

For the setup steps, see [Securing the Control Plane: External KMS](../../kubernetes/installation/security.md#external-key-management-kms).
A worked deployment of an instance is in [Deploying OpenBao as a KMS](../../tutorials/openbao-kms.md).
