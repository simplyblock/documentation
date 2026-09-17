---
title: Host Authentication and Encryption
description: "Simplyblock provides host access control and DH-HMAC-CHAP authentication for NVMe-oF connections, configured at the storage pool level."
weight: 10710
---

Simplyblock protects the NVMe-oF transport between a host and a storage node with host access control and
DH-HMAC-CHAP authentication. Only a host registered as an allowed host of a storage pool can connect to the NVMe-oF
subsystem of a volume in that pool, and every connection is authenticated in both directions with the NVMe standard
authentication protocol (TP8018).

Security is enabled per storage pool at creation time and cannot be changed afterward. All volumes in a DHCHAP-enabled
pool inherit host access control automatically.

!!! note "Transport encryption"
    TLS/PSK encryption of the NVMe-oF transport is not currently exposed through the CLI. Volume encryption at rest
    is a separate, per-volume feature described in the volume encryption documentation.

## Step 1: Create a Pool with DHCHAP Enabled

Pass `--dhchap` when creating the storage pool:

```bash title="Create a storage pool with DH-HMAC-CHAP enabled"
{{ cliname }} storage-pool add <POOL_NAME> <CLUSTER_ID> --dhchap
```

This enables bidirectional (mutual) DH-HMAC-CHAP authentication for the pool. Both a host key
(`dhchap_key`) and a controller key (`dhchap_ctrlr_key`) are auto-generated. `--dhchap` is immutable — it
cannot be toggled on an existing pool.

Pool-level QoS can be combined with DHCHAP at creation time:

```bash title="Pool with DHCHAP and QoS limits"
{{ cliname }} storage-pool add <POOL_NAME> <CLUSTER_ID> \
    --dhchap \
    --max-rw-iops 10000 --max-rw-mbytes 200
```

## Step 2: Register Allowed Hosts

Register every host initiator that needs to connect to volumes in this pool. Each host is identified by its NVMe
Qualified Name (NQN):

```bash title="Add an allowed host to the pool"
{{ cliname }} storage-pool add-host <POOL_ID> <HOST_NQN>
```

Registration propagates immediately: the host NQN and its auto-generated DHCHAP keys are added to all volumes
currently in the pool, and any volume created afterward will also include it.

```bash title="Remove an allowed host from the pool"
{{ cliname }} storage-pool remove-host <POOL_ID> <HOST_NQN>
```

Removing a host revokes access for that NQN across all volumes in the pool. A volume that is currently connected
on that host is not forcibly disconnected, but the next connection attempt is rejected.

## Step 3: Create Volumes

Volumes in a DHCHAP-enabled pool inherit host access control automatically. No extra flags are needed:

```bash title="Create a volume in a DHCHAP-enabled pool"
{{ cliname }} volume add <VOLUME_NAME> <SIZE> <POOL_ID>
```

The volume only accepts connections from hosts in the pool's allowed hosts list. Its DHCHAP keys are generated
from the pool's key material.

## Step 4: Connect a Volume

When connecting to a volume in a DHCHAP-enabled pool, pass `--host-nqn` with the initiator's NQN. The connect
command returns a ready-to-run `nvme connect` command that includes the DHCHAP keys for that host:

```bash title="Get the NVMe connection string for a volume"
{{ cliname }} volume connect <VOLUME_ID> --host-nqn <HOST_NQN>
```

Example output:

```bash title="nvme connect command with DHCHAP keys"
nvme connect -t tcp -a 192.168.1.100 -s 4420 \
    -n nqn.2023-02.io.simplyblock:lvol:abc123 \
    --hostnqn=nqn.2023-02.io.example:host-1 \
    --dhchap-secret=DHHC-1:01:<base64-key>: \
    --dhchap-ctrl-secret=DHHC-1:01:<base64-key>: \
    --ctrl-loss-tmo=-1
```

`--dhchap-secret` and `--dhchap-ctrl-secret` are included only when the host NQN is in the pool's allowed
hosts list. A host not in the list receives a `404` from the control plane and cannot connect.

## Verifying the Configuration

List the allowed hosts registered for a pool:

```bash title="Show allowed hosts for a pool"
{{ cliname }} storage-pool get <POOL_ID>
```

The `allowed_hosts` field lists the NQNs currently registered. A difference between this list and the hosts
you expect means the pool has not finished propagating yet.

For a detailed explanation of the security mechanisms, key formats, and clone behavior, see
[NVMe-oF Security](../../../architecture/concepts/nvmf-security.md).
