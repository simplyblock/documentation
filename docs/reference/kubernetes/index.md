---
title: "Kubernetes Helm Chart Parameters"
weight: 20100
---

Simplyblock provides a Helm chart to install one or more components into Kubernetes. Available components are the CSI
driver, storage nodes, and caching nodes.

This reference provides an overview of all available parameters that can be set on the Helm chart during installation
or upgrade.

## CSI Parameters

Commonly configured CSI driver parameters:

| Parameter                           | Description                                                                                  | Default                                                     |
|-------------------------------------|----------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| `csiConfig.simplybk.uuid`           | Sets the simplyblock cluster id on which the volumes are provisioned.                        | ``                                                          | 
| `csiConfig.simplybk.ip`             | Sets the HTTP(S) API Gateway endpoint connected to the management node.                      | `https://o5ls1ykzbb.execute-api.eu-central-1.amazonaws.com` | 
| `csiSecret.simplybk.secret`         | Sets the cluster secret associated with the cluster.                                         | ``                                                          | 
| `logicalVolume.encryption`          | Specifies whether logical volumes should be encrypted.                                       | `False`                                                     | 
| `csiSecret.simplybkPvc.crypto_key1` | Sets the first encryption key.                                                               | ``                                                          | 
| `csiSecret.simplybkPvc.crypto_key2` | Sets the second encryption key.                                                              | ``                                                          | 
| `logicalVolume.pool_name`           | Sets the storage pool name where logical volumes are created. This storage pool needs exist. | `testing1`                                                  | 
| `logicalVolume.qos_rw_iops`         | Sets the maximum read-write IOPS. Zero means unlimited.                                      | `0`                                                         | 
| `logicalVolume.qos_rw_mbytes`       | Sets the maximum read-write Mbps. Zero means unlimited.                                      | `0`                                                         | 
| `logicalVolume.qos_r_mbytes`        | Sets the maximum read Mbps. Zero means unlimited.                                            | `0`                                                         | 
| `logicalVolume.qos_w_mbytes`        | Sets the maximum write Mbps. Zero means unlimited.                                           | `0`                                                         | 
| `logicalVolume.numDataChunks`       | Sets the number of Erasure coding schema parameter k (distributed raid).                     | `1`                                                         | 
| `logicalVolume.numParityChunks`     | Sets the number of Erasure coding schema parameter n (distributed raid).                     | `1`                                                         | 
| `logicalVolume.lvol_priority_class` | Sets the logical volume priority class.                                                      | `0`                                                         | 
| `storageclass.create`               | Specifies whether to create a StorageClass.                                                  | `true`                                                      | 
| `snapshotclass.create`              | Specifies whether to create a SnapshotClass.                                                 | `true`                                                      | 
| `snapshotcontroller.create`         | Specifies whether to create a snapshot controller and CRD for snapshot support it.           | `true`                                                      | 

Additional, uncommonly configured CSI driver parameters:

| Parameter                           | Description                                                                                             | Default              |
|-------------------------------------|---------------------------------------------------------------------------------------------------------|----------------------|
| `driverName`                        | Sets an alternative driver name.                                                                        | `csi.simplyblock.io` |
| `serviceAccount.create`             | Specifies whether to create service account for spdkcsi-controller.                                     | `true`               |
| `rbac.create`                       | Specifies whether to create RBAC permissions for the spdkcsi-controller.                                | `true`               |
| `controller.replicas`               | Sets the replica number of the spdkcsi-controller.                                                      | `1`                  |
| `serviceAccount.create`             | Specifies whether to create service account for the csi controller.                                     | `true`               |
| `rbac.create`                       | Specifies whether to create RBAC permissions for the csi controller.                                    | `true`               |
| `controller.replicas`               | Sets the replica number of the csi controller.                                                          | `1`                  |
| `controller.tolerations.create`     | Specifies whether to create tolerations for the csi controller.                                         | `false`              | 
| `controller.tolerations.effect`     | Sets the effect of tolerations on the csi controller.                                                   | `<empty>`            | 
| `controller.tolerations.key`        | Sets the key of tolerations for the csi controller.                                                     | `<empty>`            | 
| `controller.tolerations.operator`   | Sets the operator for the csi controller tolerations.                                                   | `Exists`             | 
| `controller.tolerations.value`      | Sets the value of tolerations for the csi controller.                                                   | `<empty>`            | 
| `controller.nodeSelector.create`    | Specifies whether to create nodeSelector for the csi controller.                                        | `false`              | 
| `controller.nodeSelector.key`       | Sets the key of nodeSelector for the csi controller.                                                    | `<empty>`            | 
| `controller.nodeSelector.value`     | Sets the value of nodeSelector for the csi controller.                                                  | `<empty>`            | 
| `externallyManagedConfigmap.create` | Specifies whether a externallyManagedConfigmap should be created.                                       | `true`               | 
| `externallyManagedSecret.create`    | Specifies whether a externallyManagedSecret should be created.                                          | `true`               | 
| `podAnnotations`                    | Annotations to apply to all pods in the chart.                                                          | `{}`                 | 
| `simplyBlockAnnotations`            | Annotations to apply to simplyblock Kubernetes resources like DaemonSets, Deployments, or StatefulSets. | `{}`                 | 
| `node.tolerations.create`           | Specifies whether to create tolerations for the CSI driver node.                                        | `false`              | 
| `node.tolerations.effect`           | Sets the effect of tolerations on the CSI driver node.                                                  | `<empty>`            | 
| `node.tolerations.key`              | Sets the key of tolerations for the CSI driver node.                                                    | `<empty>`            | 
| `node.tolerations.operator`         | Sets the operator for the csi node tolerations.                                                         | `Exists`             | 
| `node.tolerations.value`            | Sets the value of tolerations for the CSI driver node.                                                  | `<empty>`            | 
| `node.nodeSelector.create`          | Specifies whether to create nodeSelector for the CSI driver node.                                       | `false`              | 
| `node.nodeSelector.key`             | Sets the key of nodeSelector for the CSI driver node.                                                   | `<empty>`            | 
| `node.nodeSelector.value`           | Sets the value of nodeSelector for the CSI driver node.                                                 | `<empty>`            | 

## Storage Node Parameters

| Parameter                                        | Description                                                                                 | Default                             |
|--------------------------------------------------|---------------------------------------------------------------------------------------------|-------------------------------------|
| `storagenode.daemonsets[0].name`                 | Sets the name of the storage node DaemonSet.                                                | `storage-node-ds`                   | 
| `storagenode.daemonsets[0].appLabel`             | Sets the label applied to the storage node DaemonSet for identification.                    | `storage-node`                      | 
| `storagenode.daemonsets[0].nodeSelector.key`     | Sets the key used in the nodeSelector to constrain which nodes the DaemonSet should run on. | `type`                              | 
| `storagenode.daemonsets[0].nodeSelector.value`   | Sets the value for the nodeSelector key to match against specific nodes.                    | `simplyblock-storage-plane`         | 
| `storagenode.daemonsets[0].tolerations.create`   | Specifies whether to create tolerations for the storage node.                               | `false`                             | 
| `storagenode.daemonsets[0].tolerations.effect`   | Sets the effect of tolerations on the storage node.                                         | `<empty>`                           | 
| `storagenode.daemonsets[0].tolerations.key`      | Sets the key of tolerations for the storage node.                                           | `<empty>`                           | 
| `storagenode.daemonsets[0].tolerations.operator` | Sets the operator for the storage node tolerations.                                         | `Exists`                            | 
| `storagenode.daemonsets[0].tolerations.value`    | Sets the value of tolerations for the storage node.                                         | `<empty>`                           | 
| `storagenode.daemonsets[1].name`                 | Sets the name of the restart storage node DaemonSet.                                        | `storage-node-ds-restart`           | 
| `storagenode.daemonsets[1].appLabel`             | Sets the label applied to the restart storage node DaemonSet for identification.            | `storage-node-restart`              | 
| `storagenode.daemonsets[1].nodeSelector.key`     | Sets the key used in the nodeSelector to constrain which nodes the DaemonSet should run on. | `type`                              | 
| `storagenode.daemonsets[1].nodeSelector.value`   | Sets the value for the nodeSelector key to match against specific nodes.                    | `simplyblock-storage-plane-restart` | 
| `storagenode.daemonsets[1].tolerations.create`   | Specifies whether to create tolerations for the restart storage node.                       | `false`                             | 
| `storagenode.daemonsets[1].tolerations.effect`   | Sets the effect of tolerations on the restart storage node.                                 | `<empty>`                           | 
| `storagenode.daemonsets[1].tolerations.key`      | Sets the key of tolerations for the restart storage node.                                   | `<empty>`                           | 
| `storagenode.daemonsets[1].tolerations.operator` | Sets the operator for the restart storage node tolerations.                                 | `Exists`                            | 
| `storagenode.daemonsets[1].tolerations.value`    | Sets the value of tolerations for the restart storage node.                                 | `<empty>`                           | 
| `storagenode.create`                             | Specifies whether to create storage node on kubernetes worker node.                         | `false`                             | 
| `storagenode.ifname`                             | Sets the default interface to be used for binding the storage node to host interface.       | `eth0`                              | 
| `storagenode.maxLogicalVolumes`                  | Sets the default maximum number of logical volumes per storage node.                        | `10`                                | 
| `storagenode.maxSnapshots`                       | Sets the default maximum number of snapshot per storage node.                               | `10`                                | 
| `storagenode.maxSize`                            | Sets the max provisioning size of all storage nodes.                                        | `150g`                              | 
| `storagenode.numPartitions`                      | Sets the number of partitions to create per device.                                         | `1`                                 | 
| `storagenode.numDevices`                         | Sets the number of devices per storage node.                                                | `1`                                 | 
| `storagenode.numDistribs`                        | Sets the number of distribs per storage node.                                               | `2`                                 | 
| `storagenode.isolateCores`                       | Enables automatic core isolation.                                                           | `false`                             | 
| `storagenode.dataNics`                           | Sets the data interface names.                                                              | `<empty>`                           | 
| `storagenode.pciAllowed`                         | Sets the list of allowed NVMe PCIe addresses.                                               | `<empty>`                           | 
| `storagenode.pciBlocked`                         | Sets the list of blocked NVMe PCIe addresses.                                               | `<empty>`                           | 
| `storagenode.socketsToUse`                       | Sets the list of sockets to use.                                                            | `<empty>`                           | 
| `storagenode.nodesPerSocket`                     | Sets the number of nodes to use per socket.                                                 | `<empty>`                           | 

## Caching Node Parameters

| Parameter                          | Description                                                                                 | Default             |
|------------------------------------|---------------------------------------------------------------------------------------------|---------------------|
| `cachingnode.tolerations.create`   | Specifies whether to create tolerations for the caching node.                               | `false`             | 
| `cachingnode.tolerations.effect`   | Sets the effect of tolerations on caching nodes.                                            | `<empty>`           | 
| `cachingnode.tolerations.key`      | Sets the tolerations key for caching nodes.                                                 | `<empty>`           | 
| `cachingnode.tolerations.operator` | Sets the operator for caching node tolerations.                                             | `Exists`            | 
| `cachingnode.tolerations.value`    | Sets the value of tolerations for caching nodes.                                            | `<empty>`           | 
| `cachingnode.create`               | Specifies whether to create caching nodes on Kubernetes worker nodes.                       | `false`             | 
| `cachingnode.nodeSelector.key`     | Sets the key used in the nodeSelector to constrain which nodes the DaemonSet should run on. | `type`              | 
| `cachingnode.nodeSelector.value`   | Sets the value for the nodeSelector key to match against specific nodes.                    | `simplyblock-cache` | 
| `cachingnode.ifname`               | Sets the default interface to be used for binding the caching node to host interface.       | `eth0`              | 
| `cachingnode.cpuMask`              | Sets the CPU mask for the spdk app to use for caching node.                                 | `<empty>`           | 
| `cachingnode.spdkMem`              | Sets the amount of hugepages memory to allocate for caching node.                           | `<empty>`           | 
| `cachingnode.multipathing`         | Specifies whether to enable multipathing for logical volume connections.                    | `true`              | 

## Image Overrides

!!! danger
    Overriding pinned image tags can result in an unusable state.
    The following parameters should only be used after an explicit request from simplyblock.  

| Parameter                              | Description                                               | Default                                                                 |
|----------------------------------------|-----------------------------------------------------------|-------------------------------------------------------------------------|
| `image.csi.repository`                 | Simplyblock CSI driver image.                             | `simplyblock/spdkcsi`                                                   |
| `image.csi.tag`                        | Simplyblock CSI driver image tag.                         | `v0.1.0`                                                                |
| `image.csi.pullPolicy`                 | Simplyblock CSI driver image pull policy.                 | `Always`                                                                |
| `image.csiProvisioner.repository`      | CSI provisioner image.                                    | `registry.k8s.io/sig-storage/csi-provisioner`                           |
| `image.csiProvisioner.tag`             | CSI provisioner image tag.                                | `v4.0.1`                                                                |
| `image.csiProvisioner.pullPolicy`      | CSI provisioner image pull policy.                        | `Always`                                                                |
| `image.csiAttacher.repository`         | CSI attacher image.                                       | `gcr.io/k8s-staging-sig-storage/csi-attacher`                           |
| `image.csiAttacher.tag`                | CSI attacher image tag.                                   | `v4.5.1`                                                                |
| `image.csiAttacher.pullPolicy`         | CSI attacher image pull policy.                           | `Always`                                                                |
| `image.nodeDriverRegistrar.repository` | CSI node driver registrar image.                          | `registry.k8s.io/sig-storage/csi-node-driver-registrar`                 |
| `image.nodeDriverRegistrar.tag`        | CSI node driver registrar image tag.                      | `v2.10.1`                                                               |
| `image.nodeDriverRegistrar.pullPolicy` | CSI node driver registrar image pull policy.              | `Always`                                                                |
| `image.csiSnapshotter.repository`      | CSI snapshotter image.                                    | `registry.k8s.io/sig-storage/csi-snapshotter`                           |
| `image.csiSnapshotter.tag`             | CSI snapshotter image tag.                                | `v7.0.2`                                                                |
| `image.csiSnapshotter.pullPolicy`      | CSI snapshotter image pull policy.                        | `Always`                                                                |
| `image.csiResizer.repository`          | CSI resizer image.                                        | `gcr.io/k8s-staging-sig-storage/csi-resizer`                            |
| `image.csiResizer.tag`                 | CSI resizer image tag.                                    | `v1.10.1`                                                               |
| `image.csiResizer.pullPolicy`          | CSI resizer image pull policy.                            | `Always`                                                                |
| `image.csiHealthMonitor.repository`    | CSI external health-monitor controller image.             | `gcr.io/k8s-staging-sig-storage/csi-external-health-monitor-controller` |
| `image.csiHealthMonitor.tag`           | CSI external health-monitor controller image tag.         | `v0.11.0`                                                               |
| `image.csiHealthMonitor.pullPolicy`    | CSI external health-monitor controller image pull policy. | `Always`                                                                |
| `image.simplyblock.repository`         | Simplyblock management image.                             | `simplyblock/simplyblock`                                               |
| `image.simplyblock.tag`                | Simplyblock management image tag.                         | `R25.5-Hotfix`                                                          |
| `image.simplyblock.pullPolicy`         | Simplyblock management image pull policy.                 | `Always`                                                                |
| `image.storageNode.repository`         | Simplyblock storage-node controller image.                | `simplyblock/simplyblock`                                               |
| `image.storageNode.tag`                | Simplyblock storage-node controller image tag.            | `v0.1.0`                                                                |
| `image.storageNode.pullPolicy`         | Simplyblock storage-node controller image pull policy.    | `Always`                                                                |
| `image.cachingNode.repository`         | Simplyblock caching-node controller image.                | `simplyblock/simplyblock`                                               |
| `image.cachingNode.tag`                | Simplyblock caching-node controller image tag.            | `v0.1.0`                                                                |
| `image.cachingNode.pullPolicy`         | Simplyblock caching-node controller image pull policy.    | `Always`                                                                |
| `image.mgmtAPI.repository`             | Simplyblock management api image.                         | `python`                                                                |
| `image.mgmtAPI.tag`                    | Simplyblock management api image tag.                     | `3.10`                                                                  |
| `image.mgmtAPI.pullPolicy`             | Simplyblock management api image pull policy.             | `Always`                                                                |
