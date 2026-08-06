---
title: "Volume Migration"
description: "Migrate a logical volume between storage nodes with the simplyblock CLI: pre-create, client connect, continue, monitor, and cancel."
weight: 20040
---

Simplyblock can move a logical volume — including its snapshots — from one storage node to another while the
volume stays online. I/O is only frozen for the brief moment needed to transfer the final delta at the end of the
migration.

This page describes the CLI-driven migration between nodes of the **same cluster**. For moving volumes between
**clusters**, see [Asynchronous Replication](asynchronous-replication.md), which provides a
replication-based cross-cluster migration. In Kubernetes environments, migrations are managed declaratively
through the `VolumeMigration` resource; see
[Volume Migration on Kubernetes](../../kubernetes/operations/volume-migration.md).

## How a Migration Works

A migration is a two-step operation with a client action in between:

1. `volume migrate` **pre-creates** the target: the NVMe-oF subsystem for the volume is created on the target
   node with the same NQN as on the source, with all listeners in the ANA state `inaccessible`. The command
   returns a migration ID and the NVMe connect strings for the new target paths.
2. The operator runs the returned `nvme connect` commands **on the client**. The new paths join the client's
   native NVMe multipath for the volume; because they are `inaccessible`, they carry no I/O yet.
3. `volume migrate-continue` starts the data transfer. The snapshot chain is copied oldest-first, the live delta
   is progressively shrunk with intermediate snapshots, and the final delta is transferred under a short I/O
   freeze. At cutover, the ANA states flip: the target paths become active and the source paths become
   inaccessible. The client follows automatically, without a disconnect.

!!! warning
    A pre-created migration must be continued within **five minutes**. If `migrate-continue` is not run in time,
    the migration is automatically cancelled and the target resources are released.

## Starting a Migration

```bash title="Step 1: Pre-create the migration"
{{ cliname }} volume migrate <VOLUME_ID> <TARGET_NODE_ID>
```

The output contains the migration ID and one connect command per target path (one per data interface of the
target node):

```bash title="Step 2: Connect the client to the target paths"
# Run the connect commands returned by 'volume migrate' on the client host.
sudo nvme connect --transport=tcp --traddr=<TARGET_IP> --trsvcid=<PORT> --nqn=<NQN> ...
```

!!! important
    On nodes with multiple data interfaces, connect **all** returned target paths. A path that is not connected
    is simply unused after the cutover, reducing the redundancy of the volume.

```bash title="Step 3: Start the data transfer"
{{ cliname }} volume migrate-continue <MIGRATION_ID>
```

`migrate-continue` accepts `--max-retries <N>` (default 10) and `--deadline <SECONDS>` (default 14400; `0`
disables the deadline).

If the volume has host authentication configured (DH-HMAC-CHAP), pass the client's host NQN to the pre-create
step with `--host-nqn <NQN>`.

## Monitoring

```bash title="List migrations"
{{ cliname }} volume migrate-list [--cluster-id <CLUSTER_ID>] [--json]
```

The list shows source and target node, the current phase, status, snapshot progress (migrated/planned), the retry
counter, and the last error, if any.

| Phase | Meaning |
|-------|---------|
| `pre_created` | Target subsystem exists, waiting for `migrate-continue`. |
| `snap_copy` | The snapshot chain is being copied to the target. |
| `lvol_migrate` | The final delta is being transferred. This is the only phase with a (short) I/O freeze. |
| `cleanup_source` | Data has moved; source-side objects are being removed. |
| `cleanup_target` | Rollback after a failure or cancellation: target-side objects are being removed. |
| `completed` | The migration has finished. |

A volume that is part of an active migration shows the migration ID in the `migrating` field of
`{{ cliname }} volume get <VOLUME_ID>`.

## Cancelling a Migration

```bash title="Cancel a migration"
{{ cliname }} volume migrate-cancel <MIGRATION_ID>
```

A migration cancelled in the `pre_created` phase is torn down immediately. In later phases, the cancellation is
picked up asynchronously by the migration runner, which rolls the target back (`cleanup_target`); it may take a
few seconds to reflect in `migrate-list`. Data on the source remains intact and authoritative until the final
cutover, so a migration can be cancelled at any phase before `cleanup_source`.

## Migrating Shared Subsystems (Batch Migration)

Volumes that share one NVMe-oF subsystem (namespaced volumes) can only be migrated together. Pass `--batch` with
any member volume; simplyblock migrates all volumes of the subsystem as one coordinated group and returns a
migration group ID, which is then used with `--batch` on the other commands:

```bash title="Migrate all volumes of a shared subsystem"
{{ cliname }} volume migrate <ANY_MEMBER_VOLUME_ID> <TARGET_NODE_ID> --batch
{{ cliname }} volume migrate-continue <GROUP_ID> --batch
{{ cliname }} volume migrate-group-list [--cluster-id <CLUSTER_ID>]
{{ cliname }} volume migrate-cancel <GROUP_ID> --batch
```

Attempting to migrate a single member of a shared subsystem without `--batch` is rejected.

## Preconditions and Constraints

A migration is admitted only if:

- The cluster is active and not currently rebalancing (no device migration or post-restart rebalancing tasks are
  running).
- The volume is online; the target node is online and different from the source node; the source node is online
  or suspended.
- The volume has no other active migration. Re-running `volume migrate` with the same volume and target returns
  the existing migration ID; a different target requires cancelling the existing migration first.

Additional operational constraints while a migration is active:

- **Snapshots of volumes on the source node cannot be created** until the migration completes.
- New volumes cannot be attached to a subsystem that has an active migration.
- The erasure coding scheme of the volume is preserved; it is not re-negotiated on the target.
- Simplyblock does not pre-check the free capacity of the target node. Ensure the target has enough capacity for
  the volume and its snapshots before starting the migration.

## Draining a Node

Volume migration is the building block for emptying a node before removing it from the cluster
(`{{ cliname }} storage-node remove` requires the node to host no volumes or snapshots). Migrate all volumes off
the node first, then remove it.
