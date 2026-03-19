---
title: "NVMe-oF Connection Security"
weight: 30300
---

Simplyblock supports multiple security mechanisms for NVMe-over-Fabrics (NVMe-oF) connections between clients (hosts)
and storage nodes. These mechanisms control which hosts can access a volume and how connections are authenticated and
protected.

## Allowed Host Lists

By default, simplyblock volumes are accessible by any host that can reach the storage node's NVMe-oF subsystem. For
environments requiring access control, volumes can be configured with an **allowed host list** that restricts access
to specific host NQNs (NVMe Qualified Names).

### Creating a Volume with Allowed Hosts

When creating a volume, provide a JSON file listing the allowed host NQNs:

```json title="allowed-hosts.json"
[
  "nqn.2014-08.org.nvmexpress:uuid:app-server-1",
  "nqn.2014-08.org.nvmexpress:uuid:app-server-2"
]
```

```bash title="Create a volume with restricted host access"
{{ cliname }} volume add <POOL_ID> <VOLUME_NAME> <SIZE> --allowed-hosts allowed-hosts.json
```

When an allowed host list is specified, the underlying NVMe-oF subsystem is created with `allow_any_host=false`, and
only the listed hosts can establish connections.

### Adding and Removing Hosts

To add a host to an existing volume:

```bash title="Add a host to a volume"
{{ cliname }} volume add-host <VOLUME_ID> <HOST_NQN>
```

To remove a host:

```bash title="Remove a host from a volume"
{{ cliname }} volume remove-host <VOLUME_ID> <HOST_NQN>
```

Removing a host also cleans up any associated authentication keys on the storage nodes.

## DHCHAP Authentication

Simplyblock supports DH-HMAC-CHAP (DHCHAP) authentication for NVMe-oF connections. DHCHAP provides challenge-response
authentication between hosts and storage targets, preventing unauthorized access even if network isolation is
compromised.

### Unidirectional Authentication

In unidirectional mode, only the **host authenticates to the target** (storage node). The target challenges the host
to prove it possesses the correct key.

To enable unidirectional DHCHAP, provide security options when adding a host:

```json title="sec-options-uni.json"
{
  "dhchap_key": true
}
```

```bash title="Add a host with unidirectional DHCHAP"
{{ cliname }} volume add-host <VOLUME_ID> <HOST_NQN> --sec-options sec-options-uni.json
```

Simplyblock automatically generates a DHCHAP key in the standard `DHHC-1` format and registers it on the storage
nodes.

### Bidirectional Authentication

In bidirectional mode, **both host and target authenticate each other**. This provides mutual authentication, ensuring
the host is connecting to a legitimate storage target.

```json title="sec-options-bidi.json"
{
  "dhchap_key": true,
  "dhchap_ctrlr_key": true
}
```

```bash title="Add a host with bidirectional DHCHAP"
{{ cliname }} volume add-host <VOLUME_ID> <HOST_NQN> --sec-options sec-options-bidi.json
```

Two separate keys are generated:

- **`dhchap_key`**: Used by the host to authenticate to the target.
- **`dhchap_ctrlr_key`**: Used by the target to authenticate back to the host.

### Retrieving DHCHAP Secrets

To retrieve the DHCHAP credentials for a specific host (needed for configuring the client):

```bash title="Get host secrets"
{{ cliname }} volume get-secret <VOLUME_ID> <HOST_NQN>
```

This returns the `dhchap_key`, `dhchap_ctrlr_key`, and/or `psk` values for the host.

### Connecting with DHCHAP

When connecting to a volume that has DHCHAP authentication configured, the `volume connect` command automatically
includes the necessary authentication flags:

```bash title="Connect with DHCHAP authentication"
{{ cliname }} volume connect <VOLUME_ID> --host-nqn <HOST_NQN>
```

The generated `nvme connect` command will include `--dhchap-secret` and (for bidirectional) `--dhchap-ctrl-secret`
parameters.

!!! note
    The `--host-nqn` parameter is required when the volume has allowed hosts with security credentials.

### Cluster-Level DHCHAP Configuration

DHCHAP digest algorithms and Diffie-Hellman groups can be configured at cluster creation time:

```json title="host-sec.json"
{
  "params": {
    "dhchap_digests": ["sha256", "sha384", "sha512"],
    "dhchap_dhgroups": ["ffdhe2048", "ffdhe4096"]
  }
}
```

```bash title="Create a cluster with DHCHAP configuration"
{{ cliname }} cluster create --host-sec host-sec.json [other options]
```

**Supported digest algorithms:**

| Digest    | Description            |
|-----------|------------------------|
| `sha256`  | SHA-256 (default)      |
| `sha384`  | SHA-384                |
| `sha512`  | SHA-512                |

**Supported Diffie-Hellman groups:**

| DH Group      | Description                                   |
|---------------|-----------------------------------------------|
| `null`        | HMAC-CHAP only (no Diffie-Hellman exchange)   |
| `ffdhe2048`   | 2048-bit finite field DH                      |
| `ffdhe3072`   | 3072-bit finite field DH                      |
| `ffdhe4096`   | 4096-bit finite field DH                      |
| `ffdhe6144`   | 6144-bit finite field DH                      |
| `ffdhe8192`   | 8192-bit finite field DH                      |

When the DH group is set to `null`, authentication uses HMAC-CHAP without a Diffie-Hellman key exchange. All other
groups perform full DH-HMAC-CHAP with the specified group size.

### DHCHAP Key Format

DHCHAP keys follow the NVMe specification format:

```
DHHC-1:<hash_id>:<base64(key + crc32)>:
```

Where:

- `DHHC-1` is the key format identifier
- `<hash_id>` identifies the hash algorithm (`01` = SHA-256, `02` = SHA-384, `03` = SHA-512)
- The key material is 32 bytes with a 4-byte CRC32 checksum, base64-encoded

Keys are automatically generated by simplyblock and stored on each storage node in
`/etc/simplyblock/dhchap_keys/`. They are registered in the SPDK keyring for use during NVMe-oF authentication.

## TLS with Pre-Shared Key (PSK)

Simplyblock supports NVMe-oF TLS using pre-shared keys for in-flight encryption of data between hosts and storage
nodes. This provides confidentiality for data traversing the network.

### Enabling TLS with PSK

To create a volume host entry with TLS-PSK:

```json title="sec-options-tls.json"
{
  "psk": true
}
```

```bash title="Add a host with TLS-PSK"
{{ cliname }} volume add-host <VOLUME_ID> <HOST_NQN> --sec-options sec-options-tls.json
```

A 256-bit pre-shared key is automatically generated (hex-encoded, 64 characters).

### Connecting with TLS

When connecting to a volume with TLS-PSK configured, the `volume connect` command automatically appends the `--tls`
flag to the generated `nvme connect` command.

```bash title="Connect with TLS"
{{ cliname }} volume connect <VOLUME_ID> --host-nqn <HOST_NQN>
```

### Combining DHCHAP and TLS

DHCHAP authentication and TLS encryption can be used together for maximum security. This provides both mutual
authentication and in-flight encryption:

```json title="sec-options-full.json"
{
  "dhchap_key": true,
  "dhchap_ctrlr_key": true,
  "psk": true
}
```

```bash title="Add a host with full security"
{{ cliname }} volume add-host <VOLUME_ID> <HOST_NQN> --sec-options sec-options-full.json
```

### Creating a Volume with Security Options

Security options can also be specified at volume creation time along with the allowed host list:

```bash title="Create a secured volume"
{{ cliname }} volume add <POOL_ID> <VOLUME_NAME> <SIZE> --allowed-hosts allowed-hosts.json --sec-options sec-options-full.json
```

This creates the volume with restricted host access and automatically generates authentication keys for each listed
host.

## Security Best Practices

- **Use allowed host lists** for all production volumes to prevent unauthorized access.
- **Enable bidirectional DHCHAP** to protect against rogue storage targets (man-in-the-middle scenarios).
- **Enable TLS-PSK** when storage traffic traverses untrusted networks or shared infrastructure.
- **Combine all three** (allowed hosts + bidirectional DHCHAP + TLS) for defense in depth.
- **Store the `host-sec.json` and `sec-options.json` files securely** and do not commit them to version control.
- **Retrieve secrets on demand** using `volume get-secret` rather than storing them externally.

## Key Management

DHCHAP and PSK keys are managed automatically by simplyblock:

- **Generation:** Keys are generated using cryptographically secure random number generators.
- **Distribution:** Keys are written to each storage node hosting the volume and registered in the SPDK keyring.
- **Cleanup:** When a host is removed from a volume, all associated keys are removed from all storage nodes.
- **Deploy cleanup:** The deploy-cleaner process removes all DHCHAP key files from
  `/etc/simplyblock/dhchap_keys/` during cluster teardown.
