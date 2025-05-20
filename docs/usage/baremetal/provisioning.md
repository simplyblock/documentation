---
title: "Provisioning a Logical Volume"
weight: 30000
---

A logical volume (LV) in simplyblock can be provisioned using the `{{ variables.cliname }}` command line interface. 
This allows administrators to create virtual NVMe block devices backed by simplyblock’s distributed storage, enabling 
high-performance and fault-tolerant storage for workloads.

## Prerequisites

- A running simplyblock cluster with healthy management and storage nodes.
- `{{ variables.cliname }}` installed and configured with access to the simplyblock management API.

## Provisioning a New Logical Volume

To create a new logical volume:

```bash
{{ variables.cliname }} volume add \
  --max-rw-iops <IOPS> \
  --max-r-mbytes <THROUGHPUT> \
  --max-w-mbytes <THROUGHPUT> \
  <VOLUME_NAME> \
  <VOLUME_SIZE> \
  <POOL_NAME>
```

### Available Parameters

| Parameter                     | Description                                        | Default |
|-------------------------------|----------------------------------------------------|---------|
| --snapshot, -s                | Enables snapshot capability on the logical volume. | false   |
| --max-size                    | Maximum size of the logical volume.                | 0       |
| --ha-type {single,ha,default} | High availability mode of the logical volume.      | ha      |
| --encrypt                     | Enables inline encryption on the logical volume.   | false   |
| --crypto-key1 CRYPTO_KEY1     | The hex value of the first encryption key.         |         |
| --crypto-key2 CRYPTO_KEY2     | The hex value of the second encryption key.        |         |
| --max-rw-iops MAX_RW_IOPS     | Maximum IO operations per second.                  | 0       |
| --max-rw-mbytes MAX_RW_MBYTES | Maximum read/write throughput.                     | 0       |
| --max-r-mbytes MAX_R_MBYTES   | Maximum read throughout.                           | 0       |
| --max-w-mbytes MAX_W_MBYTES   | Maximum write throughput.                          | 0       |

## Verification

After creation, the Logical Volume can be listed and verified:

```bash
{{ variables.cliname }} volume list
```

Details of the volume can be retrieved using:

```bash
{{ variables.cliname }} volume get <VOLUME_UUID>
```
