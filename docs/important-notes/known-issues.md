---
title: "Known Issues"
weight: 20500
---
## Kubernetes

- Currently, it is not possible to resize a logical volume clone. The resize command does not fail and the new size 
  is shown by `lsblk`. But when remounting the filesystem with the option to resize, it fails.


