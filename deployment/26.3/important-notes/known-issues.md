---
title: "Known Issues"
description: "Known Issues: is shown by lsblk. But when remounting the filesystem with the option to resize, it fails."
source: "https://docs.simplyblock.io/latest/important-notes/known-issues/"
---

# Known Issues

- Currently, it is not possible to resize a logical volume clone. The resize command does not fail and the new size is
  shown by `lsblk`. But when remounting the filesystem with the option to resize, it fails.
- A full FTT1/FTT2 network outage can create a situation where surviving nodes lose access to last journal records. This
  can cause loss of IO availability until at least one node is restarted.
- Node Removal currently only works with online nodes.
