---
title: "Provisioning a Logical Volume"
description: "Provisioning a Logical Volume: A logical volume (LV) in simplyblock can be provisioned using the command line interface."
weight: 30000
---

A logical volume (LV) in simplyblock can be provisioned using the `{{ cliname }}` command line interface.
This allows administrators to create virtual NVMe block devices backed by simplyblock’s distributed storage, enabling
high-performance and fault-tolerant storage for workloads.

## Prerequisites

- A running simplyblock cluster with healthy management and storage nodes.
- `{{ cliname }}` installed and configured with access to the simplyblock management API.

## Provisioning a New Logical Volume

To create a new logical volume:

```bash
{{ cliname }} volume add \
  --max-rw-iops <IOPS> \
  --max-r-mbytes <THROUGHPUT> \
  --max-w-mbytes <THROUGHPUT> \
  <VOLUME_NAME> \
  <VOLUME_SIZE> \
  <POOL_NAME>
```

### Available Parameters

| Parameter                       | Description                                                     | Default |
|---------------------------------|-----------------------------------------------------------------|---------|
| `--snapshot`, `-s`              | Enables snapshot capability on the logical volume.              | false   |
| `--max-size`                    | Maximum size of the logical volume.                             | 1000T   |
| `--ha-type {single,ha,default}` | High-availability mode of the logical volume.                   | default |
| `--encrypt`                     | Enables inline encryption on the logical volume.                | false   |
| `--max-rw-iops <IOPS>`          | Maximum I/O operations per second.                              | 0       |
| `--max-rw-mbytes <MBYTES>`      | Maximum read/write throughput.                                  | 0       |
| `--max-r-mbytes <MBYTES>`       | Maximum read throughput.                                        | 0       |
| `--max-w-mbytes <MBYTES>`       | Maximum write throughput.                                       | 0       |
| `--replicate`                   | Enables snapshot-based asynchronous replication for the volume. | false   |

The encryption keys of a volume created with `--encrypt` are managed by the cluster's key management system. See
[Encrypting a Logical Volume](encrypting.md).

Host access restrictions (allowed host NQNs) are configured on the storage pool with
`{{ cliname }} storage-pool add-host` and `{{ cliname }} storage-pool remove-host`, not per volume.

## Verification

After creation, the Logical Volume can be listed and verified:

```bash
{{ cliname }} volume list
```

Details of the volume can be retrieved using:

```bash
{{ cliname }} volume get <VOLUME_UUID>
```
