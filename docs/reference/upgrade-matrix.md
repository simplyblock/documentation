---
title: "Upgrade Matrix"
description: "Upgrade Matrix: Simplyblock supports in-place upgrades of existing clusters. However, not all versions can be upgraded straight to the latest versions."
weight: 20150
---

Simplyblock supports in-place upgrades of existing clusters. However, not all versions can be upgraded straight to
the latest versions. Hence, some upgrades may include multiple steps.

## How to Use This Matrix

Use the matrix as follows:

- **Requested Version** is the target version to run.
- **Installed Version** lists versions that can directly upgrade to the requested version.

If the currently installed version is not listed in the row for the target version, an upgrade to a listed
intermediate version has to come first.

## Upgrade Rules

- Only listed source-to-target paths are supported as direct upgrades.
- If a direct path is not listed, perform a multi-step upgrade via supported intermediate versions.
- Validate every intermediate step before continuing to the next target.

## Pre-Upgrade Checklist

Before starting an upgrade:

1. Confirm cluster health is stable (no critical alerts or degraded nodes).
2. Take and validate backups or snapshots according to the recovery policy.
3. Ensure enough capacity and maintenance window for the full upgrade path.
4. Review release notes and known issues for both source and target versions.

## Supported Upgrade Paths

| Requested Version | Installed Version (Directly Supported) | Intermediate Step Required |
|-------------------|----------------------------------------|----------------------------|
| 25.10.2           | 25.7.6, 25.7.7                         | No                         |
| 25.10.3           | 25.7.6, 25.7.7                         | No                         |
| 25.10.4           | 25.10.3                                | No                         |
| 25.10.5           | 25.10.4, 25.10.4.2                     | No                         |
| 26.2              | 26.1, 25.10.5                          | No                         |

## Examples

- Installed `25.10.4` -> target `25.10.5`: direct upgrade is supported.
- Installed `25.7.6` -> target `25.10.5`: direct upgrade is not listed. Upgrade first to `25.10.2` or `25.10.3`,
  then continue through `25.10.4` to `25.10.5`.
- Installed version is not present in any row: move first to the nearest listed supported source version before
  targeting later releases.

## Rollback and Failure Handling

If an upgrade step fails:

1. Stop and do not continue to the next version step.
2. Investigate the failure and restore service health first.
3. Use the validated backup/snapshot rollback procedure if required.
4. Retry only after confirming the failed step prerequisites are met.

## Related References

- [Release Notes](../release-notes/index.md)
- [Troubleshooting](troubleshooting/index.md)
