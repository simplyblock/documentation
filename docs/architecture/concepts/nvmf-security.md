---
title: "NVMe-oF Security"
description: "NVMe-oF security in simplyblock provides host access control, DH-HMAC-CHAP authentication, and TLS/PSK encryption for NVMe-oF connections."
weight: 30200
---

Simplyblock supports NVMe-oF transport security to protect data in transit and restrict access to storage subsystems.
Security is configured at two levels: cluster-wide settings define the authentication parameters, while pool-level
settings control which security keys are generated for volumes and their allowed hosts.

## Host Access Control

By default, NVMe-oF subsystems in simplyblock allow connections from any host (`allow_any_host=true`). When host access
control is enabled, only explicitly allowed host NQNs can connect to a volume's subsystem. Hosts are identified by their
NVMe Qualified Name (NQN), a unique identifier assigned to each NVMe-oF initiator.

Host access control is configured per volume at creation time or managed dynamically afterward. When a pool has security
options configured, every volume created in that pool automatically inherits those settings, and security keys are
auto-generated for each allowed host.

## DH-HMAC-CHAP Authentication

DH-HMAC-CHAP (Diffie-Hellman Hash-based Message Authentication Code Challenge-Handshake Authentication Protocol) is the
standard authentication mechanism for NVMe-oF, defined in the NVMe specification (TP8018). It provides mutual
authentication between the host (initiator) and the storage target (controller) without transmitting secrets in
cleartext.

Simplyblock supports:

- **Unidirectional authentication**: The target verifies the host identity using a shared `dhchap_key`.
- **Bidirectional (mutual) authentication**: Both host and target verify each other using a `dhchap_key` (host-to-target)
  and a `dhchap_ctrlr_key` (target-to-host).

Supported hash algorithms (digests): `sha256`, `sha384`, `sha512`

Supported Diffie-Hellman groups: `null`, `ffdhe2048`, `ffdhe3072`, `ffdhe4096`, `ffdhe6144`, `ffdhe8192`

DH-HMAC-CHAP keys are automatically generated in the NVMe TP8018 format (`DHHC-1:<hash_id>:<base64(key)>:`) when
a host is added to a volume in a pool with `dhchap_key` enabled in its security options.

## TLS/PSK Encryption

NVMe-oF connections can be encrypted using TLS 1.3 with Pre-Shared Keys (PSK). When TLS/PSK is enabled, all data
transferred between the host and the storage target is encrypted, providing confidentiality for data in transit.

PSK keys are automatically generated (256-bit random hex tokens) when a host is added to a volume in a pool with
`psk` enabled in its security options.

## Configuration Levels

NVMe-oF security is configured at two levels:

### Cluster Level

At cluster creation, DH-HMAC-CHAP parameters (digest algorithms and DH groups) are configured using a JSON
configuration file via the `--host-sec` flag. This defines the authentication behavior for all NVMe-oF connections
within the cluster.

```json title="Example: host-security-config.json"
{
  "params": {
    "dhchap_digests": ["sha256", "sha384"],
    "dhchap_dhgroups": ["ffdhe4096", "ffdhe2048"]
  }
}
```

### Pool Level

At pool creation, security options define which key types are generated for volumes in the pool. This is configured
using a JSON file via the `--sec-options` flag. Keys are automatically generated for each host added to a volume.

```json title="Example: sec-options.json"
{
  "dhchap_key": true,
  "dhchap_ctrlr_key": true,
  "psk": true
}
```

The available security option keys are:

| Key               | Description                                                              |
|-------------------|--------------------------------------------------------------------------|
| `dhchap_key`      | Generate a DH-HMAC-CHAP key for host authentication.                    |
| `dhchap_ctrlr_key`| Generate a DH-HMAC-CHAP controller key for mutual authentication. Requires `dhchap_key`. |
| `psk`             | Generate a TLS Pre-Shared Key for encrypted transport.                   |

## Host Management

Once a pool with security options is in place, hosts can be managed per volume:

- **Add a host**: `{{ cliname }} volume add-host <VOLUME_ID> <HOST_NQN>` — keys are auto-generated based on the pool's
  security options.
- **Remove a host**: `{{ cliname }} volume remove-host <VOLUME_ID> <HOST_NQN>`
- **Get credentials**: `{{ cliname }} volume get-secret <VOLUME_ID> <HOST_NQN>` — retrieves the generated keys for a
  specific host.

When connecting a volume with host access control, the `--host-nqn` flag must be provided:

```bash title="Connect Volume with Host NQN"
{{ cliname }} volume connect <VOLUME_ID> --host-nqn <HOST_NQN>
```

The connect command outputs the appropriate `nvme connect` command with the required authentication flags
(`--hostnqn`, `--dhchap-secret`, `--dhchap-ctrl-secret`, `--tls`) based on the host's configured keys.
