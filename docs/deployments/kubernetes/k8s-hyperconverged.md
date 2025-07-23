---
title: "Hyper-Converged Setup"
weight: 50000
---

In the hyper-converged or hybrid deployment, csi driver (node-part) and storage nodes are at least partially co-located on the same hosts (k8s worker nodes). 

!!! info
    However, this does not mean that each worker node with the csi driver node-part has to become a storage node. This is  
    rather defined by a node label. Also, it is possible to add dedicated storage worker nodes to the same kubernetes cluster 
    for a hybrid deployment model. 

 As for the plain CSI driver installation, the control plane must be present and a storage cluster must have been created. 
The storage cluster will however not have any storage nodes attached yet.

## CSI Driver and Storage Node System Requirements

System requirements for CSI-only (node part) installation can be found [here](install-csi.md#csi-driver-system-requirements).
However, for nodes, which serve as storage nodes, the [following requirements](../deployment-planning/recommendations.md) apply. 

## Retrieving credentials and creating a pool

[see here](install-csi.md#getting-credentials) 

## Labeling Nodes

Before the helm chart is installed, it is required to label all nodes, which shall be added as storage nodes (it is possible to label additional nodes later on to add them to the storage cluster, but cluster expansion in an HA model always requires two nodes to be added in pairs).  

```bash title="Label the Kubernetes Worker Node"
kubectl label nodes <NODE_NAME> type=simplyblock-storage-plane
```

## Networking Configuration

Multiple ports are required to be opened on storage node hosts. ports used with the same source and target networks (vlans) will not require firewall settings. port openings may be required between control plane and storage network as those will be frequently on different vlans. 

| Service                     | Direction | Source / Target Network | Port(s)   | Protocol(s) |
|-----------------------------|-----------|-------------------------|-----------|-------------|
| ICMP                        | ingress   | control / storage       | -         | ICMP        |
| Storage node API            | ingress   | control / storage mgmt  | 5000      | TCP         |
| spdk-http-proxy             | ingress   | control / storage mgmt  | 8080-8180 | TCP         |
| hublvol-nvmf-subsys-port    | ingress   | storage / storage       | 9030-9059 | TCP         |
| internal-nvmf-subsys-port   | ingress   | storage / storage       | 9060-9099 | TCP         |
| lvol-nvmf-subsys-port       | ingress   | csi-node / storage      | 9100-9200 | TCP         |
| SSH                         | ingress   | admin / storage         | 22        | TCP         |
| FoundationDB                | egress    | storage mgmt / control  | 4500      | TCP         |
| Graylog                     | egress    | storage mgmt / control  | 12202     | TCP         |

## Installing CSI Driver and Storage Nodes via Helm

In the easiest version, compared to the [installation of the csi driver only](install-csi.md) the installation of a storage node via helm  requires only one one additional parameter  _--set storagenode.create=true_:

```bash title="Install the helm chart"
CLUSTER_UUID="<UUID>"
CLUSTER_SECRET="<SECRET>"
CNTR_ADDR="<CONTROL-PLANE-ADDR>"
POOL_NAME="<POOL-NAME>"
helm repo add simplyblock-csi https://install.simplyblock.io/helm/csi
helm repo add simplyblock-controller https://install.simplyblock.io/helm/controller
helm repo update

# Install Simplyblock CSI Driver and Storage Node API
helm install -n simplyblock \
    --create-namespace simplyblock \
    simplyblock-csi/spdk-csi \
    --set csiConfig.simplybk.uuid=<CLUSTER_UUID> \
    --set csiConfig.simplybk.ip=<CNTR_ADDR> \
    --set csiSecret.simplybk.secret=<CLUSTER_SECRET> \
    --set logicalVolume.pool_name=<POOL_NAME> \
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

There are a number of other helm parameters, which are very important for storage node deployment in hyper-converged mode. The most important ones are:

| Parameter                      | Description                                            | Default  | 
|--------------------------------|--------------------------------------------------------|----------|
| _storagenode.ifname_           | the interface name of the mgmt ifc (traffic btw.       | eth0     | 
|                                | storage nodes and control plane, see storage mgmt vlan |          |
|                                | above). HA ports and nw are required in prd, but can   |          |                        |                                | low bw (e.g. 1 gb/s).                                  |          |   |_storagenode.maxLogicalVolumes_ | Max. number of lvols allowed to connect to sn.         | 10       |                        |                                | Each lvol requires about 25MiB of RAM. Can be          |          |
|                                | changed later only on node restart.                    |          |
|_storagenode.maxSize_           | Maximum utilized storage capacity through this sn.     | 150g     | 
|                                | A conservative setting is the exp. cluster capacity.   |          |
|                                | This setting has significant impact on RAM demand:     |          |
|                                | 0.02% of maxSixe is required in add. RAM.              |          |
|_storagenode.isolateCores_      | isolation of cores used by simplyblock from other      | false    | 
|                                | processes and system, including IRQs, can significantly|          |
|                                | increase performance. core isolation requires worker   |          |
|                                | node reboot after deployment is completed. changes are |          |
|                                | performed via privileged container on OS-level (grub). |          |              
|_storagenode.dataNics_          | Optional. name of ifc for storage nw. (traffic inside  |          |
|                                | of storage cluster and btw. csi-nodes and storage nodes|          |
|                                | HA ports and nw are required for prd.                  |          |
|_storagenode.pciAllowed_        |                                                        |          |       
|_storagenode.pciBlocked_        |                                                        |          |       
|_storagenode.socketsToUse_      | Simplyblock is NUMA aware. If your worker node has     |    1     |
|                                | more than 1 socket, it is possible to deploy more      |          |
|                                | than one simplyblock storage node per host             |          |
|                                | (typically one per socket), depending on the           |          |
|                                | distribution of nvme and nic across sockets and the    |          |
|                                | resource demand of other workloads.                    |          |
|_storagenode.nodesPerSocket_    | It is possible to deploy 1 or 2                        |    1     |  
|                                | storage nodes per socket. 2 sense if one               |          |
|                                | each socket has a cpu with more than 32 cores.         |          | 
|_storagenode.coresPercentage_   | This is the percentage of total cores (vcpu), which    |          | 
|                                |will be reserved for the Simplyblock Storage            |          | 
|                                |Node Services. Make sure that the percentage            |          | 
|                                |leads to at least 8 vcpu per storage node.              |          | 
|                                |For example, if a host has 128 vcpu on two sockets      |          | 
|                                |(64 per socket) and socketsToUse=2 and nodesPerSocket=1,|          | 
|                                |you need to specify at least 13% (as 13%*64>8 and 8 is  |          | 
|                                |the minimum amount of vcpu required). Simplyblock       |          | 
|                                | does not use more than 32 vcpu per node efficiently.   |          | 


!!! warning
    The resources consumed by Simplyblock are dedicated and have to be aligned with resources required
    by other workloads. The minimum requirements are described [here](../deployment-planning/recommendations.md) and a sizing 
    guide (vcpu, ram) per storage node can be found [here](../deployment-planning/node-sizing.md). Minimum requirements as 
    well as vcpu sizing guidelines contain resources for the containers used by Simplyblock and a minimal system itself, but 
    no other user or system processes. 
    
!!! info
    The RAM requirement itself is split in between huge page memory and system memory. However, this is transparent for
    users, Simplyblock takes care of allocating, reserving and freeing huge pages as part of the overall ram it 
    uses. The total amount of ram required depends on the number of vcpu used, the number of active lvols (pvcs) and the
    utilized virtual storage on this node (this is not the storage provided on the node, but the storage connected to via 
    this node!).




