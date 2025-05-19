---
title: "Find a Secondary Node"
weight: 20070
---

Simplyblock, in high-availability mode, creates two connections per logical volume: a primary and a secondary
connection.

The secondary connection will be used in case of issues or failures of the primary storage node which owns the logical
volume.

For debugging purposes, sometimes it is useful to find out which host is used as the secondary for a specific primary
storage node. This can be achieved using the command line tool `{{ variables.cliname }}` by asking for the details of
the primary storage node and grepping for the secondary id.

```bash title="Find secondary for a primary"
{{ variables.cliname }} storage-node get <NODE_ID> | grep secondary_node_id
```
