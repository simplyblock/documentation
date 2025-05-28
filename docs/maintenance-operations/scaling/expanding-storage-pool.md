---
title: "Expanding a Storage Pool"
weight: 30000
---

Simplyblock is designed as on always-on a storage system. Therefore, expanding a storage pool is an online operation and
does not require a maintenance window or system downtime.

When expanding a storage pool, its capacity will be extended, offering an extended quota of the overall storage cluster. 

## Storage Pool Expansion

To expand a storage pool, the `{{ cliname }}` command line interface:

```bash title="Expanding the storage pool"
{{ cliname }} storage-pool set <POOL_ID> --pool-max=<NEW_SIZE>
```

The value of _NEW_SIZE_ must be given as `20G`, `20T`, etc.

All valid parameters can be found in the 
[Storage Pool CLI Reference](../../reference/cli/storage-pool.md#sets-a-storage-pools-attributes). 
