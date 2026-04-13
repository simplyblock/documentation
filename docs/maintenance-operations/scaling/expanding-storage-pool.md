---
title: "Expanding a Storage Pool"
description: "Expanding a Storage Pool: Simplyblock is designed as on always-on a storage system."
weight: 30000
---

Simplyblock is designed as on always-on a storage system. Therefore, expanding a storage pool is an online operation and
does not require a maintenance window or system downtime.

When expanding a storage pool, its capacity will be extended, offering an extended quota of the overall storage cluster. 

## What Pool Expansion Changes

Expanding a storage pool updates the configured pool capacity limit (`pool-max`) and increases the quota available to
logical volumes in that pool.

This operation does not add physical storage devices by itself. Physical capacity changes (for example, adding storage
nodes or devices) are separate scaling operations.

## Prerequisites

Before expanding a pool:

- Ensure the target cluster is healthy and reachable.
- Ensure you have operator permissions to modify pool settings.
- Identify the correct storage pool ID.
- Confirm the target size aligns with cluster capacity and policy.

## Pre-Change Checks

Verify current pool state and limits before applying changes:

```bash title="List storage pools"
{{ cliname }} storage-pool list --cluster-id=<CLUSTER_ID>
```

```bash title="Inspect current pool settings"
{{ cliname }} storage-pool get <POOL_ID>
```

## Perform the Expansion

To expand a storage pool, use the `{{ cliname }}` command line interface:

```bash title="Expanding the storage pool"
{{ cliname }} storage-pool set <POOL_ID> --pool-max=<NEW_SIZE>
```

The value of _NEW_SIZE_ must be given as `20G`, `20T`, etc.

Examples:

- `--pool-max=500G`
- `--pool-max=2T`
- `--pool-max=10T`

## Verification

After applying the change, confirm the new pool limit:

```bash title="Verify the updated pool limit"
{{ cliname }} storage-pool get <POOL_ID>
```

Also verify that:

- The updated size is reflected in the pool output.
- Cluster health remains stable.
- No new capacity or pool-related alerts are raised.

## Troubleshooting

If expansion does not behave as expected:

- Verify `POOL_ID` points to the intended pool.
- Verify `_NEW_SIZE_` format (for example `500G`, `2T`).
- Re-run `storage-pool get` to confirm whether the change was persisted.
- If monitoring values lag, allow a short interval for metrics refresh and re-check.

## Operational Best Practices

- Keep alert thresholds aligned with updated capacity policy.
- Record pool capacity changes in your operational change history.

## Related References

- [Cluster Health](../monitoring/cluster-health.md)
- [Alerting](../monitoring/alerts.md)
- [Accessing I/O Stats ({{ cliname }})](../monitoring/io-stats.md)
- [Storage Pool CLI Reference](../../reference/cli/storage-pool.md)
