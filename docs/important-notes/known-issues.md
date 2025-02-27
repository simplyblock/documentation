---
title: "Known Issues"
weight: 20500
---

## Kubernetes

- Currently, it is not possible to resize a logical volume clone. The resize command does not fail and the new size 
  is shown by `lsblk`. But when remounting the filesystem with the option to resize, it fails.
- High-availability is not working for Graylog. In case of a management node failure, the Graylog monitoring service
  will fail over, but recent system logs will be empty. However, historic logs remain on S3. This issue is to be
  resolved with the next patch.

## AWS

- During a VPC peering connection, all possible CIDRs from the request's VPC should be added to the route table.
  Be aware, that there might be more than one CIDR to be added.

## Bare Metal

- At the moment, manually scanning for new devices isn't possible (when adding to the nodes). As a workaround, a
  storage node restart should be performed. This will automatically detect all newly added devices.

## Simplyblock

- Write IO errors after setting new cluster map (2+2, 2-3 nodes, 4-6 devices)
- 2+1: I/O interruption with error when removing a node that was previously added
- 2+1: Expansion migration completes with errors when there is a removed node in the cluster map
- I/O hangs and I/O errors on low memory (1+1, EBS). As a work-around assign a minimum of 6G of huge page memory to a
  storage node
