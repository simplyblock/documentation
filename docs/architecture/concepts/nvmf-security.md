---
title: "NVMe over Fabrics Security"
description: "NVMe-oF security in simplyblock provides host access control, DH-HMAC-CHAP authentication, and TLS/PSK encryption for NVMe-oF connections."
weight: 30200
---

Simplyblock supports NVMe-oF transport security to protect data in transit and restrict access to storage subsystems.
Security is enabled at a storage pool level. Turning it on for a storage pool applies to all volume created in that
specific storage pool. Host access control and the per-host security keys are then managed per volume. There is no
cluster-level security configuration. The DH-HMAC-CHAP parameters are fixed and cannot be set when creating a cluster.

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

When using pool-level DHCHAP (`--dhchap` flag), both keys are always auto-generated, meaning bidirectional
(mutual) authentication is enabled by default. There is no option to enable unidirectional authentication at
the pool level.

Simplyblock uses a fixed DH-HMAC-CHAP configuration. The following settings are used:

- Hash algorithms (digests) offered to and negotiated by the host: `sha256`, `sha384`, `sha512`.
- Diffie-Hellman group: `ffdhe2048`.

DH-HMAC-CHAP keys are automatically generated in the NVMe TP8018 format (`DHHC-1:<hash_id>:<base64(key)>:`) when
a host is added to a volume in a pool with `dhchap_key` enabled in its security options.

## TLS/PSK Encryption

NVMe-oF connections can be encrypted using TLS 1.3 with Pre-Shared Keys (PSK). When TLS/PSK is enabled, all data
transferred between the host and the storage target is encrypted, providing confidentiality for data in transit.

PSK keys are automatically generated (256-bit random hex tokens) when a host is added to a volume in a pool with
`psk` enabled in its security options.

## Configuration Levels

NVMe-oF security is configured at the storage pool level and managed per volume/host. It is **not** configured at the cluster
level. In simplyblock, a storage cluster itself carries no security settings.

### Pool Level

At pool creation time, host authentication and encryption can be enabled using a single parameter `--dhchap`.

By default, all security options are disabled. If the parameter is present at pool creation, the following is
enabled:

- Bidirectional DH-HMAC-CHAP Authentication (both `dhchap_key` and `dhchap_ctrlr_key` are auto-generated)
- Host access control (`allow_any_host` is set to `false` for all volumes in the pool)

```bash title="Create Pool with DH-HMAC-CHAP Authentication"
{{ cliname }} storage-pool add <POOL_NAME> --dhchap
```

## Host Management

Once a pool with security options is in place, hosts can be managed per storage pool:

- **Add a host**: `{{ cliname }} storage-pool add-host <POOL_ID> <HOST_NQN>` — keys are auto-generated based on the pool's
  security options.
- **Remove a host**: `{{ cliname }} storage-pool remove-host <POOL_ID> <HOST_NQN>`

## Connecting a Volume

When connecting a volume with host access control, the `--host-nqn` flag must be provided:

```bash title="Connect Volume with Host NQN"
{{ cliname }} volume connect <VOLUME_ID> --host-nqn <HOST_NQN>
```

The connect command outputs the appropriate `nvme connect` command with the required authentication flags
based on the host's configured keys:

```bash title="Example Output"
nvme connect -t tcp -a 192.168.1.100 -s 4420 \
  -n nqn.2023-02.io.simplyblock:lvol:abc123 \
  --hostnqn=nqn.2023-02.io.example:host-1 \
  --dhchap-secret=DHHC-1:01:<base64-key>: \
  --dhchap-ctrl-secret=DHHC-1:01:<base64-key>: \
  --ctrl-loss-tmo=-1
```

The `--dhchap-secret` and `--dhchap-ctrl-secret` flags are included only when the volume belongs to a
DHCHAP-enabled pool and the specified host NQN is in the pool's allowed hosts list. Without `--host-nqn`,
the connect command returns a plain connection string without authentication parameters.

## Clone Security Behavior

When a clone is created from a DHCHAP-protected volume, it receives independent security settings. 
A clone is treated as a new volume and inherits the pool’s `allowed_hosts` list at the time of creation. 
However, its host access control is managed independently from the parent volume. Adding or removing hosts 
on the parent volume does not affect existing clones, and adding or removing hosts on a clone does not 
affect the parent volume.
