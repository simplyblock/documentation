
```bash
helm install -n simplyblock-csi \
    --create-namespace simplyblock-csi \
    simplyblock-csi/spdk-csi \
    --set csiConfig.simplybk.uuid=<CLUSTER_ID> \
    --set csiConfig.simplybk.ip=<CLUSTER_MGMT_ADDR> \
    --set csiSecret.simplybk.secret=<CLUSTER_SECRET> \
    --set logicalVolume.pool_name=<POOL_NAME> \
    --set storagenode.create=true
```
