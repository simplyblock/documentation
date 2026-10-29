---
title: "What is Simplyblock?"
description: "Simplyblock is a distributed, NVMe-native storage platform for Kubernetes, which serves block, shared file, and object storage with predictable low latency."
weight: 20000
---

Simplyblock is a high-performance, distributed storage platform for cloud-native environments. It pools the
storage devices of many servers into one storage cluster and serves logical volumes over NVMe over Fabrics
(NVMe/TCP or NVMe/RoCE). On the same clusters, it also provides shared file storage through pNFS and, soon as a
beta, S3-compatible object storage. On Kubernetes, the Simplyblock Operator deploys and manages the platform, and
workloads consume storage through the simplyblock CSI driver. Integrations for Proxmox and OpenStack are available as
well.

## What Makes Simplyblock Special?

- **NVMe from end to end:** All storage access uses NVMe and NVMe over Fabrics: on the storage nodes, from the hosts
  to the cluster, and between the storage nodes. Besides NVMe devices, Linux block devices, such as SAS or SATA SSDs,
  partitions, and cloud volumes, can be used as storage.
- **User-space data plane:** The data plane runs entirely in user space, without interrupts, locks, or data copies,
  on dedicated CPU cores and per NUMA socket. The hot data path never involves the Linux kernel.
- **Distributed data placement:** Data is spread in small chunks across all devices and nodes, which keeps the load
  balanced and lets performance grow almost linearly with the cluster.
- **Advanced QoS:** Besides IOPS and throughput caps, service classes guarantee groups of volumes their share of
  the cluster's performance.
- **High availability:** Distributed erasure coding, NVMe multipathing with automatic failover, and failure domains
  keep volumes available through device, node, and rack failures.
- **Block, file, and object:** Block volumes, shared file storage (`ReadWriteMany`) through pNFS, and S3-compatible
  object storage (coming soon as a beta) run on the same NVMe-oF infrastructure and share all data services.
- **Data services:** Thin provisioning, instant snapshots and clones, compression and deduplication, encryption with
  end-to-end key management through an external KMS, policy-based backups to S3, live migration between clusters,
  and policy-based replication between clusters.
- **Kubernetes-native operations:** Clusters, nodes, devices, pools, and operations, such as restarts, upgrades, and
  migrations, are declared as custom resources and run by the Simplyblock Operator.
- **Deployment flexibility:** Storage nodes run **hyper-converged** on the application workers, **disaggregated** on
  dedicated workers, or in a **hybrid** mix of both, on bare metal or virtual machines, in public clouds or on
  premises, on x86-64 and ARM64 CPUs.

## Customer Benefits Across Industries

Simplyblock offers tailored advantages to various sectors:

- **Financial Services:** Enhances data management by boosting performance, strengthening security, and optimizing cloud
  storage costs.

- **Media and Gaming:** Improves storage performance, reduces costs, and streamlines data management, facilitating
  efficient handling of large media files and gaming data.

- **Technology and SaaS Companies:** Provides cost savings and performance enhancements, simplifying storage management
  and improving application performance without significant infrastructure changes.

- **Telecommunications:** Offers ultra-low-latency access to data, enhances security, and simplifies complex storage
  infrastructures, aiding in the efficient management of customer records and network telemetry.

- **Blockchain and Cryptocurrency:** Delivers cost efficiency, enhanced performance, scalability, and robust data
  security, addressing the unique storage demands of blockchain networks.
