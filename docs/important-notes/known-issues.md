---
title: "Known Issues"
weight: 20500
---

## Kubernetes

- Currently, it is not possible to resize a logical volume clone. The resize command does not fail and the new size 
  is shown by `lsblk`. But when remounting the filesystem with the option to resize, it fails.

## AWS

- During a VPC peering connection, all possible CIDRs from the request's VPC should be added to the route table.
  Be aware that there might be more than one CIDR to be added.

## Control Plane

- Log data is not transferred in case of the graylog failover, and recent system logs will be empty.
- API times out if the selected history of I/O statistics is too long
  
## Storage Plane 

- Currently, the erasure coding schemas with n>1 (e.g., 2+1, 2+2, 4+1) are not power-fail-safe as parity inconsistencies can be found in rare cases.
We are working with maximum effort to resolve this issue.
- During background deletion of large volumes, if the storage node at which the deleted volume resides goes offline or becomes unreachable before the delete completes, possible storage garbage may be left.
- The node removal currently does not migrate logical volumes. Remove nodes only if they are entirely empty. Otherwise, restart existing nodes on new instances or fail individual NVMe devices to phase out old hardware. 
- The fail-back on the restart of a primary node can cause I/O to hang for a few seconds. 
