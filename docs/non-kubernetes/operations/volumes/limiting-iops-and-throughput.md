---
title: "Quality of Service Limits"
description: "Quality of Service Limits: IOPS, read, write, and combined throughput limits can be applied at the storage pool level or per logical volume."
weight: 10440
---

Quality of Service (QoS) limits — IOPS, read throughput, write throughput, and combined read+write throughput —
can be set at the storage pool level or on individual logical volumes.

**Pool-level QoS** caps the aggregate throughput of all volumes in the pool. Individual volumes are not
guaranteed a share; the pool limit is a shared ceiling.

**Volume-level QoS** caps each volume independently.

!!! warning "Mutually exclusive"
    Pool-level and volume-level QoS cannot be used together for the same volume. If a pool has QoS settings,
    none of its volumes may have their own QoS settings, and vice versa. The system rejects the conflicting
    assignment.

## Pool-Level QoS

### Setting Pool QoS at Creation

Pass the QoS flags when creating the pool:

```bash title="Create a pool with QoS limits"
{{ cliname }} storage-pool add <POOL_NAME> <CLUSTER_ID> \
    --max-rw-iops 5000 \
    --max-rw-mbytes 50 \
    --max-r-mbytes 35 \
    --max-w-mbytes 15
```

#### Pinning QoS Volumes to a Storage Node

All volumes in a pool with QoS limits must reside on the same storage node. When you set QoS on a pool, the
system selects a storage node automatically. To choose a specific node, pass `--qos-host`:

```bash title="Create a QoS pool pinned to a specific storage node"
{{ cliname }} storage-pool add <POOL_NAME> <CLUSTER_ID> \
    --max-rw-iops 5000 \
    --qos-host <NODE_ID>
```

`--qos-host` is only valid together with at least one QoS parameter (`--max-rw-iops`, `--max-rw-mbytes`,
`--max-r-mbytes`, or `--max-w-mbytes`). Using it on a pool with no QoS settings is an error.

### Updating Pool QoS

Pool QoS limits can only be **increased** after creation. Passing a value lower than the current limit is
rejected. To remove a limit entirely, pass `0`:

```bash title="Increase pool QoS limits"
{{ cliname }} storage-pool set <POOL_ID> \
    --max-rw-iops 10000 \
    --max-rw-mbytes 100 \
    --max-r-mbytes 70 \
    --max-w-mbytes 30
```

```bash title="Remove all pool QoS limits"
{{ cliname }} storage-pool set <POOL_ID> \
    --max-rw-iops 0 \
    --max-rw-mbytes 0 \
    --max-r-mbytes 0 \
    --max-w-mbytes 0
```

## Volume-Level QoS

### Setting Volume QoS at Creation

```bash title="Create a volume with QoS limits"
{{ cliname }} volume add <VOLUME_NAME> 100G <POOL_ID> \
    --max-rw-iops 5000 \
    --max-rw-mbytes 50 \
    --max-r-mbytes 35 \
    --max-w-mbytes 15
```

### Updating Volume QoS

QoS can be changed on an active volume at any time:

```bash title="Update QoS on an existing volume"
{{ cliname }} volume qos-set <VOLUME_ID> \
    --max-rw-iops 10000 \
    --max-rw-mbytes 100 \
    --max-r-mbytes 70 \
    --max-w-mbytes 30
```

## QoS Parameters

All parameters are optional. A value of `0` means no limit.

| Parameter          | Description                         |
|--------------------|-------------------------------------|
| `--max-rw-iops`    | Maximum combined read+write IOPS    |
| `--max-rw-mbytes`  | Maximum combined read+write MB/s    |
| `--max-r-mbytes`   | Maximum read throughput (MB/s)      |
| `--max-w-mbytes`   | Maximum write throughput (MB/s)     |

When `--max-rw-mbytes` is set, `--max-r-mbytes` and `--max-w-mbytes` must each be less than or equal to it.

!!! note "Kubernetes"
    In Kubernetes, StorageClass-level QoS settings are not allowed if the referenced pool already has QoS
    limits. See [Storage Class](../../../kubernetes/usage/storage-class.md) and
    [Defining Quality of Service](../../../kubernetes/usage/quality-of-service.md) for the Kubernetes flow.
