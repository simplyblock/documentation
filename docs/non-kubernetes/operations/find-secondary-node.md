---
title: "Finding the Secondary Node"
description: "Finding the Secondary Node: Simplyblock, in high-availability mode, creates two connections per logical volume: a primary and a secondary connection."
weight: 20070
---

Simplyblock, in high-availability mode, creates two connections per logical volume: a primary and a secondary
connection.

The secondary connection will be used in case of issues or failures of the primary storage node which owns the logical
volume.

## When to Use This

Checking the secondary node is useful when:

- validating HA placement after cluster changes,
- investigating failover behavior,
- troubleshooting node-level performance or availability issues.

## Primary vs Secondary Node

In HA mode, logical volume ownership and replication state span primary and secondary storage nodes. The primary node
typically serves active ownership, while the secondary node is part of failover readiness and recovery.

## Prerequisites

Before running the check:

- Ensure `{{ cliname }}` is configured and can access the control plane.
- Ensure the primary storage node ID is known.
- Ensure cluster and storage-node state is reachable.

## Find the Secondary Node ID

For debugging purposes, find which host is used as secondary for a specific primary storage node by querying
storage-node details and filtering for the secondary field:

```bash title="Find secondary for a primary"
{{ cliname }} storage-node get <NODE_ID> | grep secondary_node_id
```

## Interpret the Output

- If `secondary_node_id` is present and populated, that value is the paired secondary node.
- If the field is missing or empty, possible reasons include:
  - non-HA configuration,
  - transitional state during migration/rebalancing,
  - unavailable metadata due to API or cluster issues.

## Validate the Secondary Node

After obtaining the secondary node ID, verify that node is healthy:

```bash title="Inspect the secondary node"
{{ cliname }} storage-node get <SECONDARY_NODE_ID>
```

```bash title="List storage nodes for status cross-check"
{{ cliname }} storage-node list --cluster-id=<CLUSTER_ID>
```

## Troubleshooting

- If no secondary is reported, verify the affected logical volumes are configured for HA.
- If the secondary node appears offline or degraded, investigate node health and recent events first.
- If values appear stale, re-run the query after short intervals while checking cluster health.

## Related References

- [Cluster Health](monitoring/cluster-health.md)
- [Logical Volume Conditions](monitoring/lvol-conditions.md)
- [Migrating a Storage Node](migrating-storage-node.md)
- [Replacing a Storage Node](replacing-storage-node.md)
