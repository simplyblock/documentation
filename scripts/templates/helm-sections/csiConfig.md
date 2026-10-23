## CSI Credentials

The `externallyManagedSecret`, `csiConfig`, `csiSecret`, and `multiCluster` values render the
`simplyblock-csi-secret-v2` Secret with cluster credentials for the CSI driver. The credentials of the clusters the
operator creates are maintained by the operator, so these values are only needed for clusters it does not create. A
pool named in `csiConfig` or `multiCluster` also gets a block StorageClass, because no `StoragePool` exists for such a
cluster to write one.
