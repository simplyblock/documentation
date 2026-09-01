---
title: "Known Issues"
description: "Known Issues: is shown by lsblk. But when remounting the filesystem with the option to resize, it fails."
source: "https://docs.simplyblock.io/latest/important-notes/known-issues/"
---

# Known Issues

## Kubernetes

- Currently, it is not possible to resize a logical volume clone. The resize command does not fail and the new size
  is shown by `lsblk`. But when remounting the filesystem with the option to resize, it fails.
