---
title: "Known Issues"
weight: 20500
---

## Kubernetes
- Currently, it is not possible to resize a lvol clone. The resize command does not fail and the new size is shown by lsblk. But when remounting the filesystem with the option to resize, it fails.
- HA not working for Greylog (in case of a management node failure, greylog monitoring service will fail over, but recent system logs will be empty; historic logs remain on S3) - to be resolved with next patch

## AWS
- During VPC peering connection, all possible CIDRs from the request's VPC should be added to the route table. This can be more than one.

## Bare Metal
- At the moment, manually scanning for new devices isn't possible (adding to the nodes). As a workaround, a storage node restart will automatically detect newly added devices.

## Simplyblock
- Write IO errors after setting new cluster map (2+2, 2-3 nodes, 4-6 devices)
- 2+1: I/O interrupts with error when removing a node that was previously added
- 2+1: expansion migration completes with errors when there is a removed node in the cluster map
- I/O hanging and I/O errors on low memory (1+1, EBS); work-around: assign a minimum of 6G of huge page memory to a storage node
