---
title: "Accessing I/O Stats ({{ variables.cliname }})"
weight: 30300
---

Simplyblock's `{{ variables.cliname }}` tool provides the option to retrieve some extensive I/O statistics. Those
contain a number of relevant metrics of historic and current I/O activities per device, storage node, logical volume,
and cluster.

These metrics include:

- Read and write throughput (in MB/s)
- I/O operations per second (IOPS) for read, write, and unmap
- Total amount of bytes read and written
- Total number of I/O operations since the start of a node
- Latency ticks
- Average read, write, and unmap latency

## Accessing Cluster Statistics

To access cluster-wide statistics, use the following command:

```bash title="Accessing cluster-wide I/O statistics"
{{ variables.cliname }} cluster get-io-stats <CLUSTER_ID>
```

More information about the command is available in the
[CLI reference section](../../reference/cli/cluster.md#gets-a-clusters-io-statistics).

## Accessing Storage Node Statistics

To access the I/O statistics of a storage node (which includes all physical NVMe devices), use the following command:

```bash title="Accessing storage node I/O statistics"
{{ variables.cliname }} storage-node get-io-stats <NODE_ID>
```

More information about the command is available in the
[CLI reference section](../../reference/cli/storage-node.md#gets-storage-node-io-statistics).

To access the I/O statistics of a specific device in a storage node, use the following command:

```bash title="Accessing storage node device I/O statistics"
{{ variables.cliname }} storage-node get-io-stats-device <DEVICE_ID>
```

More information about the command is available in the
[CLI reference section](../../reference/cli/storage-node.md#gets-a-devices-io-statistics).

## Accessing Storage Pool Statistics

To access logical volume-specific statistics, use the following command:

```bash title="Accessing storage pool I/O statistics"
{{ variables.cliname }} storage-pool get-io-stats <POOL_ID>
```

More information about the command is available in the
[CLI reference section](../../reference/cli/storage-pool.md#gets-a-storage-pools-io-statistics).

## Accessing Logical Volume Statistics

To access logical volume-specific statistics, use the following command:

```bash title="Accessing logical volume I/O statistics"
{{ variables.cliname }} volume get-io-stats <VOLUME_ID>
```

More information about the command is available in the
[CLI reference section](../../reference/cli/volume.md#gets-a-logical-volumes-io-statistics).
