---
title: "Defining Quality of Service"
weight: 30600
---

Simplyblock allows Quality of Service (QoS) limits to be applied to logical volumes (LVs) to control performance by
defining maximum IOPS and throughput. QoS settings can be configured during volume creation or adjusted on an
active Logical Volume using the `sbcli` command line interface.

Configuring QoS allows simplyblock logical volumes to deliver predictable performance by limiting resource consumption
and ensuring balanced workload distribution across the storage cluster.

## Setting QoS During Volume Creation

QoS can be applied when creating a new logical volume:

```sh
sbcli volume create \
  --max-rw-iops MAX_RW_IOPS 3500 \
  --max-rw-mbytes MAX_RW_MBYTES 125 \
  <VOLUME_NAME> \
  <VOLUME_SIZE> \
  <POOL_NAME>
```

### Parameters

| Parameter                     | Description                                         | Default |
|-------------------------------|-----------------------------------------------------|---------|
| --max-rw-iops MAX_RW_IOPS     | Maximum IO operations per second.                   | 0       |
| --max-rw-mbytes MAX_RW_MBYTES | Maximum read/write throughput.                      | 0       |
| --max-r-mbytes MAX_R_MBYTES   | Maximum read throughout.                            | 0       |
| --max-w-mbytes MAX_W_MBYTES   | Maximum write throughput.                           | 0       |

To see all available parameters when creating a logical volume, see [Provisioning](provisioning.md).

## Changing QoS on an Active Logical Volume

QoS settings can also be updated on an existing logical volume:

```sh
sbcli volume qos-set \
  --max-rw-iops MAX_RW_IOPS 5000 \
  --max-rw-mbytes MAX_RW_MBYTES 250 \
  <VOLUME_UUID>
```

## Verification

To check the current QoS settings:

```sh
sbcli volume get <VOLUME_UUID>
```

Review the output for the active QoS configuration.
