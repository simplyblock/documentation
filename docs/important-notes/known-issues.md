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

- In a highly available control plane cluster, Graylog currently runs only on the primary (first) node. Availability
  is lost in case of an outage of the primary control plane node.
  
## Storage Plane 

- During background deletion of large volumes, if the storage node at which the deleted volume resides goes offline
  or becomes unreachable before the delete completes, possible storage garbage may be left.


