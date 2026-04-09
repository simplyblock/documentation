---
title: "Security"
description: "Security is a core pillar of the simplyblock platform, designed to protect data across every layer of the storage stack."
weight: 20200
---

Security is a core pillar of the simplyblock platform, designed to protect data across every layer of the storage
stack. From encryption at rest to NVMe-oF transport security, multi-tenant isolation, and secure communications,
simplyblock provides robust, enterprise-grade features that help meet stringent compliance and data protection
requirements. Security is enforced by design, ensuring your workloads and sensitive data remain protected against
internal and external threats.

## NVMe-oF Transport Security

Simplyblock supports NVMe-oF transport security to protect data in transit and restrict host access to storage
subsystems. This includes:

- **Host access control** — restrict which hosts (by NQN) can connect to a volume's NVMe-oF subsystem.
- **DH-HMAC-CHAP authentication** — mutual authentication between host and target using the NVMe standard
  authentication protocol (TP8018).
- **TLS/PSK encryption** — encrypt data in transit using TLS 1.3 with Pre-Shared Keys.

NVMe-oF security is configured at two levels:

1. **Cluster level** — define DH-HMAC-CHAP digest algorithms and DH groups at cluster creation using
   `--host-sec=<config.json>`.
2. **Pool level** — define which security key types to auto-generate for volumes in a pool using
   `--sec-options=<config.json>`.

Once configured, hosts are managed per volume using the following commands:

```bash title="Manage Allowed Hosts per Volume"
# Add an allowed host (keys are auto-generated based on pool security options)
{{ cliname }} volume add-host <VOLUME_ID> <HOST_NQN>

# Remove an allowed host
{{ cliname }} volume remove-host <VOLUME_ID> <HOST_NQN>

# Retrieve the generated credentials for a host
{{ cliname }} volume get-secret <VOLUME_ID> <HOST_NQN>
```

When connecting a volume with host access control enabled, the `--host-nqn` flag is required:

```bash title="Connect Volume with Host NQN"
{{ cliname }} volume connect <VOLUME_ID> --host-nqn <HOST_NQN>
```

For a detailed explanation of the security mechanisms and configuration, see
[NVMe-oF Security](../../architecture/concepts/nvmf-security.md).
