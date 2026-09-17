---
title: "NVMe over Fabrics Security"
description: "NVMe-oF security in simplyblock provides host access control and DH-HMAC-CHAP authentication for NVMe-oF connections, configured at the storage pool level."
weight: 30200
---

Simplyblock supports NVMe-oF transport security to protect data in transit and restrict access to storage subsystems.
Security is enabled at the storage pool level and cannot be changed after the pool is created. Turning it on for a
storage pool applies to all volumes created in that pool. Host access control and per-host security keys are then
managed per pool, and the changes propagate automatically to all volumes in the pool. There is no cluster-level
security configuration.

## Host Access Control

By default, NVMe-oF subsystems in simplyblock allow connections from any host (`allow_any_host=true`). When host
access control is enabled, only explicitly allowed host NQNs can connect to a volume's subsystem. Hosts are
identified by their NVMe Qualified Name (NQN), a unique identifier assigned to each NVMe-oF initiator.

Host access control is enabled at pool creation time. Every volume created in a DHCHAP-enabled pool automatically
inherits the pool's allowed hosts list, and security keys are auto-generated for each registered host.

## DH-HMAC-CHAP Authentication

DH-HMAC-CHAP (Diffie-Hellman Hash-based Message Authentication Code Challenge-Handshake Authentication Protocol) is the
standard authentication mechanism for NVMe-oF, defined in the NVMe specification (TP8018). It provides mutual
authentication between the host (initiator) and the storage target (controller) without transmitting secrets in
cleartext.

Simplyblock supports:

- **Unidirectional authentication:** The target verifies the host identity using a shared `dhchap_key`.
- **Bidirectional (mutual) authentication:** Both host and target verify each other using a `dhchap_key` (host-to-target)
  and a `dhchap_ctrlr_key` (target-to-host).

When using pool-level DHCHAP (`--dhchap` flag), both keys are always auto-generated, meaning bidirectional
(mutual) authentication is enabled by default. There is no option to enable unidirectional authentication at
the pool level.

Simplyblock uses a fixed DH-HMAC-CHAP configuration:

- Hash algorithms offered and negotiated: `sha256`, `sha384`, `sha512`.
- Diffie-Hellman group: `ffdhe2048`.

DH-HMAC-CHAP keys are automatically generated in the NVMe TP8018 format (`DHHC-1:<hash_id>:<base64(key)>:`) when
a host is added to a pool.

## TLS/PSK Encryption

NVMe-oF connections can be encrypted using TLS 1.3 with Pre-Shared Keys (PSK). When TLS/PSK is enabled, all data
transferred between the host and the storage target is encrypted, providing confidentiality for data in transit.

PSK keys are automatically generated (256-bit random hex tokens) when a host is added to a volume in a pool with
`psk` enabled in its security options.

## Configuration Levels

NVMe-oF security is configured at the storage pool level. It is **not** configured at the cluster level — a storage
cluster itself carries no security settings.

### Pool Level

Security is enabled at pool creation time with the `--dhchap` flag. This setting is immutable; recreating the pool
is the only way to change it.

By default, all security options are disabled. With `--dhchap`, the following are enabled for every volume in the
pool:

- Bidirectional DH-HMAC-CHAP authentication (both `dhchap_key` and `dhchap_ctrlr_key` are auto-generated).
- Host access control (`allow_any_host` is set to `false`).

```bash title="Create a pool with DH-HMAC-CHAP authentication"
{{ cliname }} storage-pool add <POOL_NAME> <CLUSTER_ID> --dhchap
```

## Host Management

Once a DHCHAP-enabled pool exists, hosts are managed at the pool level:

```bash title="Add an allowed host to the pool"
{{ cliname }} storage-pool add-host <POOL_ID> <HOST_NQN>
```

```bash title="Remove an allowed host from the pool"
{{ cliname }} storage-pool remove-host <POOL_ID> <HOST_NQN>
```

Adding a host propagates immediately: the NQN and its auto-generated DHCHAP keys are registered on all volumes
currently in the pool. Any volume created in the pool afterward also includes the registered hosts.

Removing a host propagates immediately: the NQN is removed from all volumes in the pool. A volume that is currently
connected on that host is not forcibly disconnected, but the next connection attempt is rejected.

## Connecting a Volume

When connecting a volume in a DHCHAP-enabled pool, the `--host-nqn` flag must be provided:

```bash title="Connect volume with host NQN"
{{ cliname }} volume connect <VOLUME_ID> --host-nqn <HOST_NQN>
```

The connect command outputs the appropriate `nvme connect` command with the required authentication flags
based on the host's configured keys:

```bash title="Example nvme connect command with DHCHAP keys"
nvme connect -t tcp -a 192.168.1.100 -s 4420 \
    -n nqn.2023-02.io.simplyblock:lvol:abc123 \
    --hostnqn=nqn.2023-02.io.example:host-1 \
    --dhchap-secret=DHHC-1:01:<base64-key>: \
    --dhchap-ctrl-secret=DHHC-1:01:<base64-key>: \
    --ctrl-loss-tmo=-1
```

`--dhchap-secret` and `--dhchap-ctrl-secret` are included only when the volume belongs to a DHCHAP-enabled pool
and the specified host NQN is in the pool's allowed hosts list. Without `--host-nqn`, the connect command returns a
plain connection string without authentication parameters.

## Clone Security Behavior

When a clone is created from a DHCHAP-protected volume, it receives independent security settings. A clone inherits
the pool's `allowed_hosts` list at the time of creation. However, its host access control is managed independently
from the parent volume — adding or removing hosts on the parent does not affect existing clones, and vice versa.
