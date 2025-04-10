---
title: "Install Simplyblock CSI"
weight: 30200
---

Simplyblock provides a seamless integration with Kubernetes through its Kubernetes CSI driver.

--8<-- "prepare-nvme-tcp.md"

To install the Simplyblock CSI Driver, a helm chart is provided. While it can be installed manually, the helm chart is
strongly recommended. If a manual installation is preferred, see the
[CSI Driver Repository](https://github.com/simplyblock-io/simplyblock-csi/blob/master/docs/install-simplyblock-csi-driver.md){:target="_blank" rel="noopener"}. 

Either way, the installation requires a few values to be available.

First we need the unique cluster id. Note down the cluster uuid of the cluster to access.

```bash title="Retrieving the Cluster UUID"
sudo {{ variables.cliname }} cluster list
```

An example of the output is below.

```plain title="Example output of a cluster listing"
[demo@demo ~]# {{ variables.cliname }} cluster list
+--------------------------------------+-----------------------------------------------------------------+---------+-------+------------+---------------+-----+--------+
| UUID                                 | NQN                                                             | ha_type | tls   | mgmt nodes | storage nodes | Mod | Status |
+--------------------------------------+-----------------------------------------------------------------+---------+-------+------------+---------------+-----+--------+
| 4502977c-ae2d-4046-a8c5-ccc7fa78eb9a | nqn.2023-02.io.simplyblock:4502977c-ae2d-4046-a8c5-ccc7fa78eb9a | ha      | False | 1          | 4             | 1x1 | active |
+--------------------------------------+-----------------------------------------------------------------+---------+-------+------------+---------------+-----+--------+
```

In addition, we need the cluster secret. Note down the cluster secret.

```bash title="Retrieve the Cluster Secret"
{{ variables.cliname }} cluster get-secret <CLUSTER_UUID>
```

Retrieving the cluster secret will look somewhat like that.

```plain title="Example output of retrieving a cluster secret"
[demo@demo ~]# {{ variables.cliname }} cluster get-secret 4502977c-ae2d-4046-a8c5-ccc7fa78eb9a
oal4PVNbZ80uhLMah2Bs
```

Additionally, a storage pool is required. If a pool already exists, it can be reused. Otherwise, creating a storage
pool can be created as following:

```bash title="Create a Storage Pool"
{{ variables.cliname }} pool add <POOL_NAME> <CLUSTER_UUID>
```

The last line of a successful storage pool creation returns the new pool id.

```plain title="Example output of creating a storage pool"
[demo@demo ~]# {{ variables.cliname }} pool add test 4502977c-ae2d-4046-a8c5-ccc7fa78eb9a
2025-03-05 06:36:06,093: INFO: Adding pool
2025-03-05 06:36:06,098: INFO: {"cluster_id": "4502977c-ae2d-4046-a8c5-ccc7fa78eb9a", "event": "OBJ_CREATED", "object_name": "Pool", "message": "Pool created test", "caused_by": "cli"}
2025-03-05 06:36:06,100: INFO: Done
ad35b7bb-7703-4d38-884f-d8e56ffdafc6 # <- Pool Id
```

The last item necessary before deploying the CSI driver is the control plane address. On a standard bare metal or
virtualized installation it is any of the API addresses. Meaning, if the primary management node has the IP of
`192.168.10.1`, the control plane address is `http://192.168.0.1`. It is, however, recommended to front all management
nodes, with a load balancing proxy, such as HAproxy. In the latter case, the load balancer URL would be the address of
the control plane.

Anyhow, deploying the Simplyblock CSI Driver using the provided helm chart comes down to providing the four necessary
values, adding the helm chart repository, and installing the driver.

```bash title="Install Simplyblock's CSI Driver"
CLUSTER_UUID="<UUID>"
CLUSTER_SECRET="<SECRET>"
CNTR_ADDR="<CONTROL-PLANE-ADDR>"
POOL_NAME="<POOL-NAME>"
helm repo add simplyblock-csi https://install.simplyblock.io/helm
helm repo update
helm install -n simplyblock-csi --create-namespace simplyblock-csi simplyblock-csi/spdk-csi \
    --set csiConfig.simplybk.uuid=${CLUSTER_UUID} \
    --set csiConfig.simplybk.ip=${CNTR_ADDR} \
    --set csiSecret.simplybk.secret=${CLUSTER_SECRET} \
    --set logicalVolume.pool_name=${POOL_NAME}
```

```plain title="Example output of the CSI driver deployment"
demo@demo ~> export CLUSTER_UUID="4502977c-ae2d-4046-a8c5-ccc7fa78eb9a"
demo@demo ~> export CLUSTER_SECRET="oal4PVNbZ80uhLMah2Bs"
demo@demo ~> export CNTR_ADDR="http://192.168.10.1/"
demo@demo ~> export POOL_NAME="test"
demo@demo ~> helm repo add simplyblock-csi https://install.simplyblock.io/helm
"simplyblock-csi" has been added to your repositories
demo@demo ~> helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "simplyblock-csi" chart repository
...Successfully got an update from the "kasten" chart repository
Update Complete. ⎈Happy Helming!⎈
demo@demo ~> helm install -n simplyblock-csi --create-namespace simplyblock-csi simplyblock-csi/spdk-csi \
  --set csiConfig.simplybk.uuid=${CLUSTER_UUID} \
  --set csiConfig.simplybk.ip=${CNTR_ADDR} \
  --set csiSecret.simplybk.secret=${CLUSTER_SECRET} \
  --set logicalVolume.pool_name=${POOL_NAME}
NAME: simplyblock-csi
LAST DEPLOYED: Wed Mar  5 15:06:02 2025
NAMESPACE: simplyblock-csi
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
The Simplyblock SPDK Driver is getting deployed to your cluster.

To check CSI SPDK Driver pods status, please run:

  kubectl --namespace=simplyblock-csi get pods --selector="release=simplyblock-csi" --watch
demo@demo ~> kubectl --namespace=simplyblock-csi get pods --selector="release=simplyblock-csi" --watch
NAME                   READY   STATUS    RESTARTS   AGE
spdkcsi-controller-0   6/6     Running   0          30s
spdkcsi-node-tzclt     2/2     Running   0          30s
```
