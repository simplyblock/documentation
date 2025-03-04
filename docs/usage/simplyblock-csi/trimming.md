---
title: "Trimming a Filesystem"
weight: 40800
---

Filesystem trimming is the process of informing the underlying storage system about unused blocks, allowing simplyblock
to reclaim and optimize storage space. This is particularly important when using thin-provisioned Logical Volumes (LVs)
in Simplyblock, as it helps maintain efficient resource utilization and reduces unnecessary storage consumption over
time.

## When to Trim

Trimming should be performed:

- After large file deletions.
- As part of regular maintenance to keep storage optimized.
- Following data migration or cleanup tasks.

## Perform a Trim

Trimming must be executed within the filesystem inside the mounted volume. The specific command depends on the
filesystem type. Below are common examples:

```bash title="Trimming an ext4 filesystem"
fstrim -v /mount/point
```

```bash title="Trimming an xfs filesystem"
xfs_fsr -v /mount/point
```
