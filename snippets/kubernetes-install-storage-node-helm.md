{% include 'prepare-nvme-tcp.md' %}

#### Collect Required Cluster Details

To install the simplyblock in Kubernetes, a Helm chart is provided. While it can be installed manually, the Helm chart
is strongly recommended.  The installation requires a few values to be available.

First, we need the unique cluster id. Note down the cluster UUID of the cluster to access.

```bash title="Retrieving the Cluster UUID"
sudo {{ cliname }} cluster list
```

An example of the output is below.

```plain title="Example output of a cluster listing"
[demo@demo ~]# {{ cliname }} cluster list
+--------------------------------------+-----------------------------------------------------------------+---------+-------+------------+---------------+-----+--------+
| UUID                                 | NQN                                                             | ha_type | tls   | mgmt nodes | storage nodes | Mod | Status |
+--------------------------------------+-----------------------------------------------------------------+---------+-------+------------+---------------+-----+--------+
| 4502977c-ae2d-4046-a8c5-ccc7fa78eb9a | nqn.2023-02.io.simplyblock:4502977c-ae2d-4046-a8c5-ccc7fa78eb9a | ha      | False | 1          | 4             | 1x1 | active |
+--------------------------------------+-----------------------------------------------------------------+---------+-------+------------+---------------+-----+--------+
```

In addition, we need the cluster secret. Note down the cluster secret.

```bash title="Retrieve the Cluster Secret"
{{ cliname }} cluster get-secret <CLUSTER_UUID>
```

Retrieving the cluster secret will look somewhat like that.

```plain title="Example output of retrieving a cluster secret"
[demo@demo ~]# {{ cliname }} cluster get-secret 4502977c-ae2d-4046-a8c5-ccc7fa78eb9a
oal4PVNbZ80uhLMah2Bs
```

Additionally, a storage pool is required. If a pool already exists, it can be reused. Otherwise, creating a storage
pool can be created as following:

```bash title="Create a Storage Pool"
{{ cliname }} pool add <POOL_NAME> <CLUSTER_UUID>
```

The last line of a successful storage pool creation returns the new pool id.

```plain title="Example output of creating a storage pool"
[demo@demo ~]# {{ cliname }} pool add test 4502977c-ae2d-4046-a8c5-ccc7fa78eb9a
2025-03-05 06:36:06,093: INFO: Adding pool
2025-03-05 06:36:06,098: INFO: {"cluster_id": "4502977c-ae2d-4046-a8c5-ccc7fa78eb9a", "event": "OBJ_CREATED", "object_name": "Pool", "message": "Pool created test", "caused_by": "cli"}
2025-03-05 06:36:06,100: INFO: Done
ad35b7bb-7703-4d38-884f-d8e56ffdafc6 # <- Pool Id
```

The last item necessary before deploying simplyblock is the control plane address. This is any of the API addresses of a
management node. Meaning, if the primary management node has the IP of `192.168.10.1`, the control plane address is
`http://192.168.0.1`. It is, however, recommended to front all management nodes with a load balancing proxy, such as
HAproxy. In the latter case, the load balancer URL would be the address of the control plane.

#### Installing the Helm Charts

Anyhow, deploying simplyblock using the provided helm chart comes down to providing the four necessary
values, adding the helm chart repository, and installing the driver. In addition to the storage nodes, this will also
install the Simplyblock CSI driver for seamless integration with the Kubernetes CSI persistent storage subsystem.

To enable Kubernetes to decide where to install storage nodes, the helm chart uses a Kubernetes node label. This can be
used to mark only specific nodes to act as storage nodes, or to use all nodes for the hyper-converged or hybrid setup. 

```bash title="Label the Kubernetes Worker Node"
kubectl label nodes <NODE_NAME> type=simplyblock-storage-plane
```

!!! warning
    The label must be applied to all nodes that operate as part of the storage plane.

After labeling the nodes, the Helm chart can be deployed.

```bash title="Install the helm chart"
CLUSTER_UUID="<UUID>"
CLUSTER_SECRET="<SECRET>"
CNTR_ADDR="<CONTROL-PLANE-ADDR>"
POOL_NAME="<POOL-NAME>"
helm repo add simplyblock-csi https://install.simplyblock.io/helm/csi
helm repo add simplyblock-controller https://install.simplyblock.io/helm/controller
helm repo update

# Install Simplyblock CSI Driver
helm install -n simplyblock \
    --create-namespace simplyblock \
    simplyblock-csi/spdk-csi \
    --set csiConfig.simplybk.uuid=<CLUSTER_UUID> \
    --set csiConfig.simplybk.ip=<CNTR_ADDR> \
    --set csiSecret.simplybk.secret=<CLUSTER_SECRET> \
    --set logicalVolume.pool_name=<POOL_NAME> \
    --set storagenode.create=true

# Install Simplyblock Storage Controller
helm install -n simplyblock \
    simplyblock-controller/sb-controller \
    --set storagenode.create=true
```

```plain title="Example output of the Simplyblock Kubernetes deployment"
demo@demo ~> export CLUSTER_UUID="4502977c-ae2d-4046-a8c5-ccc7fa78eb9a"
demo@demo ~> export CLUSTER_SECRET="oal4PVNbZ80uhLMah2Bs"
demo@demo ~> export CNTR_ADDR="http://192.168.10.1/"
demo@demo ~> export POOL_NAME="test"
demo@demo ~> helm repo add simplyblock-csi https://install.simplyblock.io/helm/csi
"simplyblock-csi" has been added to your repositories
demo@demo ~> helm repo add simplyblock-controller https://install.simplyblock.io/helm/controller
"simplyblock-controller" has been added to your repositories
demo@demo ~> helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "simplyblock-csi" chart repository
...Successfully got an update from the "simplyblock-controller" chart repository
Update Complete. ⎈Happy Helming!⎈
demo@demo ~> helm install -n simplyblock --create-namespace simplyblock simplyblock-csi/spdk-csi \
  --set csiConfig.simplybk.uuid=${CLUSTER_UUID} \
  --set csiConfig.simplybk.ip=${CNTR_ADDR} \
  --set csiSecret.simplybk.secret=${CLUSTER_SECRET} \
  --set logicalVolume.pool_name=${POOL_NAME}
NAME: simplyblock-csi
LAST DEPLOYED: Wed Mar  5 15:06:02 2025
NAMESPACE: simplyblock
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
The Simplyblock SPDK Driver is getting deployed to your cluster.

To check CSI SPDK Driver pods status, please run:

  kubectl --namespace=simplyblock get pods --selector="release=simplyblock-csi" --watch
demo@demo ~> kubectl --namespace=simplyblock get pods --selector="release=simplyblock-csi" --watch
NAME                   READY   STATUS    RESTARTS   AGE
spdkcsi-controller-0   6/6     Running   0          30s
spdkcsi-node-tzclt     2/2     Running   0          30s
```

As a last step, when the storage cluster nodes are deployed, it is recommended to apply CPU core isolation for highest
performance to the Kubernetes worker nodes that act as storage node hosts.

During the installation of the simplyblock controller, a configuration file with the system configuration has been
created. To apply core isolation to the Kubernetes worker, an SSH login to the worker node is required.

After logging in, _tuned_ must be installed if not already available. This can be installed via one of the following
commands:

=== "Red Hat / Alma / Rocky"

    ```bash
    yum install tuned
    ```

=== "Debian / Ubuntu"

    ```bash
    apt install tuned
    ```

Following the installation of _tuned_, the tuning profile file must be created. The following snippet automates the
creation based on the generated configuration file.

```bash title="Generate the core isolation tuning profile"
SIMPLYBLOCK_CONFIG="/var/simplyblock/sn_config_file"
pip install -y yq jq
ISOLATED=$(yq '.isolated_cores' ${SIMPLYBLOCK_CONFIG} | jq -r '. | $ join(",")'); echo "isolcpus=${ISOLATED}"
mkdir -p /etc/tuned/realtime
cat << EOF > /etc/tuned/realtimme/tuned.conf
[main]
include=latency-performance
[bootloader]
cmdline_add=isolcpus={$ISOLATED} nohz_full={$ISOLATED} rcu_nocbs={$ISOLATED}
EOF
```

Now the profile file must be applied and the worker node restarted.

!!! info
    Remember to drain potentially remaining services on the Kubernetes worker node before rebooting.

```bash title="Apply the profile and reboot"
tuned-adm profile realtime
reboot 
```

#### Changing the Number of Utilized CPU Cores

By default, simplyblock assumes that the whole host is available to it and will configure itself to use everything
but 20% of the host. In hyper-converged setups, this assumption is not true and the number of utilized CPU cores must
be adjusted.

To adjust the number of CPU cores, an SSH login to the Kubernetes worker node is required. After logging in, the
configuration file at _/var/simplyblock/sn_config_file_ must be updated.

```bash title="Open the configuration file in VI"
vi /var/simplyblock/sn_config_file
```

Inside the configuration file, the _cpu_mask_ value must be updated to represent the number and assignment of cores to
be used by simplyblock. To create the required CPU mask, the [CPU Mask Calculator](../../../reference/cpumask-calculator.md)
can be used. 

```json title="Updating the CPU Mask configuration"
{
    "nodes": [
        {
            "socket": 0,
            "cpu_mask": "0xfffbffc",
            "isolated": [
                2,
                3,
                4,
                5,
                ...
            ]
        }
    ]
}
```

After saving the file and exiting _vi_, the new configuration must be applied. For simplicity, this shell script at
[GitHub](https://github.com/simplyblock-io/simplyblock-csi/blob/master/scripts/config-gen-upgrade.sh) automates the
creation and submission of the Kubernetes job.

```bash title="Apply the configuration change"
curl -s -L https://raw.githubusercontent.com/simplyblock-io/simplyblock-csi/refs/heads/master/scripts/config-gen-upgrade.sh | bash
```
