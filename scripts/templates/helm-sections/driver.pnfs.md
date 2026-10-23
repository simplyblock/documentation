## pNFS Metadata Server

The `driver.pnfs` block configures the pNFS metadata server, which serves ReadWriteMany volumes. One metadata server
pod runs per storage cluster, on a node with `/dev/kvm`. See [pNFS Volumes](../../kubernetes/usage/pnfs.md).
