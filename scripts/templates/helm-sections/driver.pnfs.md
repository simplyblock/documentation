## pNFS Metadata Server

The `driver.pnfs` block configures the pNFS metadata server, which serves ReadWriteMany volumes. One active metadata
server pod and its standby pods run per storage cluster, each on its own node with `/dev/kvm`. The number of standbys
is set by `driver.pnfs.mds.standbys` (0 to 4), which is commented out in the chart's `values.yaml`. Unset, the
driver's default of one standby applies. See [pNFS Volumes](../../kubernetes/usage/pnfs.md).
