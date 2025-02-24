---
title: "CLI"
weight: 20000
---


Simplyblock provides a feature-rich CLI (command line interface) client to manage all aspects of the storage cluster.

```bash
usage: sbcli [-h] [-d]
             {storage-node,sn,cluster,lvol,mgmt,pool,snapshot,caching-node,cn}
             ...

positional arguments:
  {storage-node,sn,cluster,lvol,mgmt,pool,snapshot,caching-node,cn}
    storage-node (sn)   Storage node commands
    cluster             Cluster commands
    lvol                LVol commands
    mgmt                Management node commands
    pool                Pool commands
    snapshot            Snapshot commands
    caching-node (cn)   Caching client node commands

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           Print debug messages

```


## Storage Node Commands


```bash
usage: sbcli storage-node [-h]
                          {deploy,deploy-cleaner,add-node,delete,remove,list,get,restart,shutdown,suspend,resume,get-io-stats,get-capacity,list-devices,device-testing-mode,get-device,reset-device,restart-device,add-device,remove-device,get-capacity-device,get-io-stats-device,port-list,port-io-stats,check,check-device,info,info-spdk}
                          ...

positional arguments:
  {deploy,deploy-cleaner,add-node,delete,remove,list,get,restart,shutdown,suspend,resume,get-io-stats,get-capacity,list-devices,device-testing-mode,get-device,reset-device,restart-device,add-device,remove-device,get-capacity-device,get-io-stats-device,port-list,port-io-stats,check,check-device,info,info-spdk}
    deploy              Deploy local services for remote ops (local run)
    deploy-cleaner      clean local deploy (local run)
    add-node            Add storage node by ip
    delete              Delete storage node obj
    remove              Remove storage node
    list                List storage nodes
    get                 Get storage node info
    restart             Restart a storage node
    shutdown            Shutdown a storage node
    suspend             Suspend a storage node
    resume              Resume a storage node
    get-io-stats        Get node IO statistics
    get-capacity        Get node capacity statistics
    list-devices        List storage devices
    device-testing-mode
                        Set device testing mode
    get-device          Get storage device by id
    reset-device        Reset storage device
    restart-device      Restart storage device
    add-device          Add a new storage device
    remove-device       Remove a storage device
    get-capacity-device
                        Get device capacity
    get-io-stats-device
                        Get device IO statistics
    port-list           Get Data interfaces list for a node
    port-io-stats       Get Data interfaces IO stats
    check               Health check storage node
    check-device        Health check device
    info                Get node information
    info-spdk           Get SPDK memory information

optional arguments:
  -h, --help            show this help message and exit

```


### Deploy Local Services for Remote Ops (execute locally)


```bash
usage: sbcli storage-node deploy [-h] [--ifname IFNAME]

optional arguments:
  -h, --help       show this help message and exit
  --ifname IFNAME  Management interface name, default: eth0

```


### Clean local deploy (local run)


```bash
usage: sbcli storage-node deploy-cleaner [-h]

optional arguments:
  -h, --help  show this help message and exit

```


### Add Storage Node by IP


```bash
usage: sbcli storage-node add-node [-h] [--partitions PARTITIONS]
                                   [--jm-percent JM_PERCENT]
                                   [--data-nics DATA_NICS [DATA_NICS ...]]
                                   [--cpu-mask SPDK_CPU_MASK]
                                   [--memory SPDK_MEM]
                                   [--spdk-image SPDK_IMAGE] [--spdk-debug]
                                   [--iobuf_small_pool_count SMALL_POOL_COUNT]
                                   [--iobuf_large_pool_count LARGE_POOL_COUNT]
                                   [--iobuf_small_bufsize SMALL_BUFSIZE]
                                   [--iobuf_large_bufsize LARGE_BUFSIZE]
                                   cluster_id node_ip ifname

positional arguments:
  cluster_id            UUID of the cluster to which the node will belong
  node_ip               IP of storage node to add
  ifname                Management interface name

optional arguments:
  -h, --help            show this help message and exit
  --partitions PARTITIONS
                        Number of partitions to create per device
  --jm-percent JM_PERCENT
                        Number in percent to use for JM from each device
  --data-nics DATA_NICS [DATA_NICS ...]
                        Data interface names
  --cpu-mask SPDK_CPU_MASK
                        SPDK app CPU mask, default is all cores found
  --memory SPDK_MEM     SPDK huge memory allocation, default is 4G
  --spdk-image SPDK_IMAGE
                        SPDK image uri
  --spdk-debug          Enable spdk debug logs
  --iobuf_small_pool_count SMALL_POOL_COUNT
                        bdev_set_options param
  --iobuf_large_pool_count LARGE_POOL_COUNT
                        bdev_set_options param
  --iobuf_small_bufsize SMALL_BUFSIZE
                        bdev_set_options param
  --iobuf_large_bufsize LARGE_BUFSIZE
                        bdev_set_options param

```


### Delete Storage Node Object


```bash
usage: sbcli storage-node delete [-h] node_id

positional arguments:
  node_id     UUID of storage node

optional arguments:
  -h, --help  show this help message and exit

```


### Remove Storage Node


```bash
usage: sbcli storage-node remove [-h] [--force-remove] [--force-migrate]
                                 node_id

positional arguments:
  node_id          UUID of storage node

optional arguments:
  -h, --help       show this help message and exit
  --force-remove   Force remove all LVols and snapshots
  --force-migrate  Force migrate All LVols to other nodes

```


### List Storage Nodes


```bash
usage: sbcli storage-node list [-h] [--cluster-id CLUSTER_ID] [--json]

optional arguments:
  -h, --help            show this help message and exit
  --cluster-id CLUSTER_ID
                        id of the cluster for which nodes are listed
  --json                Print outputs in json format

```


### Get Storage Node Info


```bash
usage: sbcli storage-node get [-h] id

positional arguments:
  id          UUID of storage node

optional arguments:
  -h, --help  show this help message and exit

```


### Restart Storage Node
All functions and device drivers will be reset. During restart, the node does not accept IO. In a high-availability setup, this will not impact operations

```bash
usage: sbcli storage-node restart [-h] [--cpu-mask SPDK_CPU_MASK]
                                  [--memory SPDK_MEM]
                                  [--spdk-image SPDK_IMAGE] [--spdk-debug]
                                  [--iobuf_small_pool_count SMALL_POOL_COUNT]
                                  [--iobuf_large_pool_count LARGE_POOL_COUNT]
                                  [--iobuf_small_bufsize SMALL_BUFSIZE]
                                  [--iobuf_large_bufsize LARGE_BUFSIZE]
                                  node_id

positional arguments:
  node_id               UUID of storage node

optional arguments:
  -h, --help            show this help message and exit
  --cpu-mask SPDK_CPU_MASK
                        SPDK app CPU mask, default is all cores found
  --memory SPDK_MEM     SPDK huge memory allocation, default is 4G
  --spdk-image SPDK_IMAGE
                        SPDK image uri
  --spdk-debug          Enable spdk debug logs
  --iobuf_small_pool_count SMALL_POOL_COUNT
                        bdev_set_options param
  --iobuf_large_pool_count LARGE_POOL_COUNT
                        bdev_set_options param
  --iobuf_small_bufsize SMALL_BUFSIZE
                        bdev_set_options param
  --iobuf_large_bufsize LARGE_BUFSIZE
                        bdev_set_options param

```


### Shutdown Storage Node
Once the command is issued, the node will stop accepting IO,but IO, which was previously received, will still be processed. In a high-availability setup, this will not impact operations.

```bash
usage: sbcli storage-node shutdown [-h] [--force] node_id

positional arguments:
  node_id     UUID of storage node

optional arguments:
  -h, --help  show this help message and exit
  --force     Force node shutdown

```


### Suspend Storage Node
The node will stop accepting new IO, but will finish processing any IO, which has been received already.

```bash
usage: sbcli storage-node suspend [-h] [--force] node_id

positional arguments:
  node_id     UUID of storage node

optional arguments:
  -h, --help  show this help message and exit
  --force     Force node suspend

```


### Resume Storage Node


```bash
usage: sbcli storage-node resume [-h] node_id

positional arguments:
  node_id     UUID of storage node

optional arguments:
  -h, --help  show this help message and exit

```


### Get Node IO Statistics


```bash
usage: sbcli storage-node get-io-stats [-h] [--history HISTORY] node_id

positional arguments:
  node_id            Node ID

optional arguments:
  -h, --help         show this help message and exit
  --history HISTORY  list history records -one for every 15 minutes- for XX
                     days and YY hours -up to 10 days in total-, format:
                     XXdYYh

```


### Get Node Capacity Statistics


```bash
usage: sbcli storage-node get-capacity [-h] [--history HISTORY] node_id

positional arguments:
  node_id            Node ID

optional arguments:
  -h, --help         show this help message and exit
  --history HISTORY  list history records -one for every 15 minutes- for XX
                     days and YY hours -up to 10 days in total-, format:
                     XXdYYh

```


### List Storage Devices


```bash
usage: sbcli storage-node list-devices [-h] [-s {node-seq,dev-seq,serial}]
                                       [--json]
                                       node_id

positional arguments:
  node_id               the node's UUID

optional arguments:
  -h, --help            show this help message and exit
  -s {node-seq,dev-seq,serial}, --sort {node-seq,dev-seq,serial}
                        Sort the outputs
  --json                Print outputs in json format

```


### Set Device Testing Mode


```bash
usage: sbcli storage-node device-testing-mode [-h]
                                              device_id
                                              {full_pass_through,io_error_on_read,io_error_on_write,io_error_on_unmap,io_error_on_all,discard_io_all,hotplug_removal}

positional arguments:
  device_id             Device UUID
  {full_pass_through,io_error_on_read,io_error_on_write,io_error_on_unmap,io_error_on_all,discard_io_all,hotplug_removal}
                        Testing mode

optional arguments:
  -h, --help            show this help message and exit

```


### Get Storage Device by Id


```bash
usage: sbcli storage-node get-device [-h] device_id

positional arguments:
  device_id   the devices's UUID

optional arguments:
  -h, --help  show this help message and exit

```


### Reset Storage Device
Hardware device reset. Resetting the device can return the device from an unavailable into online state, if successful

```bash
usage: sbcli storage-node reset-device [-h] device_id

positional arguments:
  device_id   the devices's UUID

optional arguments:
  -h, --help  show this help message and exit

```


### Restart Storage Device
a previously removed or unavailable device may be returned into online state. If the device is not physically present, accessible or healthy, it will flip back into unavailable state again.

```bash
usage: sbcli storage-node restart-device [-h] id

positional arguments:
  id          the devices's UUID

optional arguments:
  -h, --help  show this help message and exit

```


### Add new Storage Device
Adding a device will include a previously detected device (currently in "new" state) into cluster and will launch and auto-rebalancing background process in which some cluster capacity is re-distributed to this newly added device.

```bash
usage: sbcli storage-node add-device [-h]

optional arguments:
  -h, --help  show this help message and exit

```


### Remove Storage Device
The device will become unavailable, independently if it was physically removed from the server. This function can be used if auto-detection of removal did not work or if the device must be maintained otherwise while remaining inserted into the server.

```bash
usage: sbcli storage-node remove-device [-h] [--force] device_id

positional arguments:
  device_id   Storage device ID

optional arguments:
  -h, --help  show this help message and exit
  --force     Force device remove

```


### Get Device Capacity


```bash
usage: sbcli storage-node get-capacity-device [-h] [--history HISTORY]
                                              device_id

positional arguments:
  device_id          Storage device ID

optional arguments:
  -h, --help         show this help message and exit
  --history HISTORY  list history records -one for every 15 minutes- for XX
                     days and YY hours -up to 10 days in total-, format:
                     XXdYYh

```


### Get Device IO Statistics


```bash
usage: sbcli storage-node get-io-stats-device [-h] [--history HISTORY]
                                              device_id

positional arguments:
  device_id          Storage device ID

optional arguments:
  -h, --help         show this help message and exit
  --history HISTORY  list history records -one for every 15 minutes- for XX
                     days and YY hours -up to 10 days in total-, format:
                     XXdYYh

```


### List Node Data Interfaces List


```bash
usage: sbcli storage-node port-list [-h] node_id

positional arguments:
  node_id     Storage node ID

optional arguments:
  -h, --help  show this help message and exit

```


### Get Sata Interfaces IO Stats


```bash
usage: sbcli storage-node port-io-stats [-h] [--history HISTORY] port_id

positional arguments:
  port_id            Data port ID

optional arguments:
  -h, --help         show this help message and exit
  --history HISTORY  list history records -one for every 15 minutes- for XX
                     days and YY hours -up to 10 days in total, format: XXdYYh

```


### Check Storage Node Health


```bash
usage: sbcli storage-node check [-h] id

positional arguments:
  id          UUID of storage node

optional arguments:
  -h, --help  show this help message and exit

```


### Check Device Health


```bash
usage: sbcli storage-node check-device [-h] id

positional arguments:
  id          device UUID

optional arguments:
  -h, --help  show this help message and exit

```


### Get Mode Information


```bash
usage: sbcli storage-node info [-h] id

positional arguments:
  id          Node UUID

optional arguments:
  -h, --help  show this help message and exit

```


### Get SPDK Memory Information


```bash
usage: sbcli storage-node info-spdk [-h] id

positional arguments:
  id          Node UUID

optional arguments:
  -h, --help  show this help message and exit

```


## Cluster Commands


```bash
usage: sbcli cluster [-h]
                     {create,add,list,status,get,suspend,unsuspend,get-capacity,get-io-stats,get-logs,get-secret,upd-secret,check,update,graceful-shutdown,graceful-startup,list-tasks,delete}
                     ...

positional arguments:
  {create,add,list,status,get,suspend,unsuspend,get-capacity,get-io-stats,get-logs,get-secret,upd-secret,check,update,graceful-shutdown,graceful-startup,list-tasks,delete}
    create              Create an new cluster with this node as mgmt (local
                        run)
    add                 Add new cluster
    list                Show clusters list
    status              Show cluster status
    get                 Show cluster info
    suspend             Suspend cluster
    unsuspend           Unsuspend cluster
    get-capacity        Get cluster capacity
    get-io-stats        Get cluster IO statistics
    get-logs            Returns cluster status logs
    get-secret          Get cluster secret
    upd-secret          Updates the cluster secret
    check               Health check cluster
    update              Update cluster mgmt services
    graceful-shutdown   Graceful shutdown of storage nodes
    graceful-startup    Graceful startup of storage nodes
    list-tasks          List tasks by cluster ID
    delete              Delete Cluster

optional arguments:
  -h, --help            show this help message and exit

```


### Create new Cluster attached to this Management Node (execute locally)


```bash
usage: sbcli cluster create [-h] [--blk_size {512,4096}]
                            [--page_size PAGE_SIZE] [--CLI_PASS CLI_PASS]
                            [--cap-warn CAP_WARN] [--cap-crit CAP_CRIT]
                            [--prov-cap-warn PROV_CAP_WARN]
                            [--prov-cap-crit PROV_CAP_CRIT] [--ifname IFNAME]
                            [--log-del-interval LOG_DEL_INTERVAL]
                            [--metrics-retention-period METRICS_RETENTION_PERIOD]

optional arguments:
  -h, --help            show this help message and exit
  --blk_size {512,4096}
                        The block size in bytes
  --page_size PAGE_SIZE
                        The size of a data page in bytes
  --CLI_PASS CLI_PASS   Password for CLI SSH connection
  --cap-warn CAP_WARN   Capacity warning level in percent, default=80
  --cap-crit CAP_CRIT   Capacity critical level in percent, default=90
  --prov-cap-warn PROV_CAP_WARN
                        Capacity warning level in percent, default=180
  --prov-cap-crit PROV_CAP_CRIT
                        Capacity critical level in percent, default=190
  --ifname IFNAME       Management interface name, default: eth0
  --log-del-interval LOG_DEL_INTERVAL
                        graylog deletion interval, default: 7d
  --metrics-retention-period METRICS_RETENTION_PERIOD
                        retention period for prometheus metrics, default: 7d

```


### Add new Cluster


```bash
usage: sbcli cluster add [-h] [--blk_size {512,4096}] [--page_size PAGE_SIZE]
                         [--cap-warn CAP_WARN] [--cap-crit CAP_CRIT]
                         [--prov-cap-warn PROV_CAP_WARN]
                         [--prov-cap-crit PROV_CAP_CRIT]

optional arguments:
  -h, --help            show this help message and exit
  --blk_size {512,4096}
                        The block size in bytes
  --page_size PAGE_SIZE
                        The size of a data page in bytes
  --cap-warn CAP_WARN   Capacity warning level in percent, default=80
  --cap-crit CAP_CRIT   Capacity critical level in percent, default=90
  --prov-cap-warn PROV_CAP_WARN
                        Capacity warning level in percent, default=180
  --prov-cap-crit PROV_CAP_CRIT
                        Capacity critical level in percent, default=190

```


### Show Clusters List


```bash
usage: sbcli cluster list [-h]

optional arguments:
  -h, --help  show this help message and exit

```


### Show Cluster Status


```bash
usage: sbcli cluster status [-h] cluster_id

positional arguments:
  cluster_id  the cluster UUID

optional arguments:
  -h, --help  show this help message and exit

```


### Show Cluster Info


```bash
usage: sbcli cluster get [-h] id

positional arguments:
  id          the cluster UUID

optional arguments:
  -h, --help  show this help message and exit

```


### Suspend Cluster


```bash
usage: sbcli cluster suspend [-h] cluster_id

positional arguments:
  cluster_id  the cluster UUID

optional arguments:
  -h, --help  show this help message and exit

```


### Unsuspend Cluster


```bash
usage: sbcli cluster unsuspend [-h] cluster_id

positional arguments:
  cluster_id  the cluster UUID

optional arguments:
  -h, --help  show this help message and exit

```


### Get Cluster Capacity


```bash
usage: sbcli cluster get-capacity [-h] [--json] [--history HISTORY] cluster_id

positional arguments:
  cluster_id         the cluster UUID

optional arguments:
  -h, --help         show this help message and exit
  --json             Print json output
  --history HISTORY  (XXdYYh), list history records (one for every 15 minutes)
                     for XX days and YY hours (up to 10 days in total).

```


### Get Cluster IO Statistics


```bash
usage: sbcli cluster get-io-stats [-h] [--records RECORDS] [--history HISTORY]
                                  cluster_id

positional arguments:
  cluster_id         the cluster UUID

optional arguments:
  -h, --help         show this help message and exit
  --records RECORDS  Number of records, default: 20
  --history HISTORY  (XXdYYh), list history records (one for every 15 minutes)
                     for XX days and YY hours (up to 10 days in total).

```


### Get Cluster Status Logs


```bash
usage: sbcli cluster get-logs [-h] cluster_id

positional arguments:
  cluster_id  cluster uuid

optional arguments:
  -h, --help  show this help message and exit

```


### Get Cluster Secret


```bash
usage: sbcli cluster get-secret [-h] cluster_id

positional arguments:
  cluster_id  cluster uuid

optional arguments:
  -h, --help  show this help message and exit

```


### Updates Cluster Secret


```bash
usage: sbcli cluster upd-secret [-h] cluster_id secret

positional arguments:
  cluster_id  cluster uuid
  secret      new 20 characters password

optional arguments:
  -h, --help  show this help message and exit

```


### Check Cluster Health


```bash
usage: sbcli cluster check [-h] id

positional arguments:
  id          cluster UUID

optional arguments:
  -h, --help  show this help message and exit

```


### Update Cluster Management Services


```bash
usage: sbcli cluster update [-h] id

positional arguments:
  id          cluster UUID

optional arguments:
  -h, --help  show this help message and exit

```


### Graceful Shutdown of Storage Nodes


```bash
usage: sbcli cluster graceful-shutdown [-h] id

positional arguments:
  id          cluster UUID

optional arguments:
  -h, --help  show this help message and exit

```


### Graceful Startup of Storage Nodes


```bash
usage: sbcli cluster graceful-startup [-h] id

positional arguments:
  id          cluster UUID

optional arguments:
  -h, --help  show this help message and exit

```


### List Tasks by Cluster Id


```bash
usage: sbcli cluster list-tasks [-h] cluster_id

positional arguments:
  cluster_id  UUID of the cluster

optional arguments:
  -h, --help  show this help message and exit

```


### Delete cluster
This is only possible, if no storage nodes and pools are attached to the cluster

```bash
usage: sbcli cluster delete [-h] id

positional arguments:
  id          cluster UUID

optional arguments:
  -h, --help  show this help message and exit

```


## Logical Volume Commands


```bash
usage: sbcli lvol [-h]
                  {add,qos-set,list,list-mem,get,delete,connect,resize,create-snapshot,clone,move,get-capacity,get-io-stats,send-cluster-map,get-cluster-map,check}
                  ...

positional arguments:
  {add,qos-set,list,list-mem,get,delete,connect,resize,create-snapshot,clone,move,get-capacity,get-io-stats,send-cluster-map,get-cluster-map,check}
    add                 Add a new logical volume
    qos-set             Change qos settings for an active logical volume
    list                List LVols
    list-mem            Get the size and max_size of the lvol
    get                 Get LVol details
    delete              Delete LVol
    connect             Get lvol connection strings
    resize              Resize LVol
    create-snapshot     Create snapshot from LVol
    clone               create LVol based on a snapshot
    move                Moves a full copy of the logical volume between nodes
    get-capacity        Get LVol capacity
    get-io-stats        Get LVol IO statistics
    send-cluster-map    send cluster map
    get-cluster-map     get cluster map
    check               Health check LVol

optional arguments:
  -h, --help            show this help message and exit

```


### Add new Logical Volume


```bash
usage: sbcli lvol add [-h] [--snapshot] [--max-size MAX_SIZE]
                      [--host-id HOST_ID] [--ha-type {single,ha,default}]
                      [--encrypt] [--crypto-key1 CRYPTO_KEY1]
                      [--crypto-key2 CRYPTO_KEY2] [--max-rw-iops MAX_RW_IOPS]
                      [--max-rw-mbytes MAX_RW_MBYTES]
                      [--max-r-mbytes MAX_R_MBYTES]
                      [--max-w-mbytes MAX_W_MBYTES] [--distr-vuid DISTR_VUID]
                      [--distr-ndcs DISTR_NDCS] [--distr-npcs DISTR_NPCS]
                      [--distr-bs DISTR_BS] [--distr-chunk-bs DISTR_CHUNK_BS]
                      name size pool

positional arguments:
  name                  LVol name or id
  size                  LVol size: 10M, 10G, 10(bytes)
  pool                  Pool UUID or name

optional arguments:
  -h, --help            show this help message and exit
  --snapshot, -s        Make LVol with snapshot capability, default is False
  --max-size MAX_SIZE   LVol max size
  --host-id HOST_ID     Primary storage node UUID or Hostname
  --ha-type {single,ha,default}
                        LVol HA type (single, ha), default is cluster HA type
  --encrypt             Use inline data encryption and de-cryption on the
                        logical volume
  --crypto-key1 CRYPTO_KEY1
                        the hex value of key1 to be used for lvol encryption
  --crypto-key2 CRYPTO_KEY2
                        the hex value of key2 to be used for lvol encryption
  --max-rw-iops MAX_RW_IOPS
                        Maximum Read Write IO Per Second
  --max-rw-mbytes MAX_RW_MBYTES
                        Maximum Read Write Mega Bytes Per Second
  --max-r-mbytes MAX_R_MBYTES
                        Maximum Read Mega Bytes Per Second
  --max-w-mbytes MAX_W_MBYTES
                        Maximum Write Mega Bytes Per Second
  --distr-vuid DISTR_VUID
                        (Dev) set vuid manually, default: random (1-99999)
  --distr-ndcs DISTR_NDCS
                        (Dev) set ndcs manually, default: 4
  --distr-npcs DISTR_NPCS
                        (Dev) set npcs manually, default: 1
  --distr-bs DISTR_BS   (Dev) distrb bdev block size, default: 4096
  --distr-chunk-bs DISTR_CHUNK_BS
                        (Dev) distrb bdev chunk block size, default: 4096

```


### Change QOS Settings for an Active Logical Volume


```bash
usage: sbcli lvol qos-set [-h] [--max-rw-iops MAX_RW_IOPS]
                          [--max-rw-mbytes MAX_RW_MBYTES]
                          [--max-r-mbytes MAX_R_MBYTES]
                          [--max-w-mbytes MAX_W_MBYTES]
                          id

positional arguments:
  id                    LVol id

optional arguments:
  -h, --help            show this help message and exit
  --max-rw-iops MAX_RW_IOPS
                        Maximum Read Write IO Per Second
  --max-rw-mbytes MAX_RW_MBYTES
                        Maximum Read Write Mega Bytes Per Second
  --max-r-mbytes MAX_R_MBYTES
                        Maximum Read Mega Bytes Per Second
  --max-w-mbytes MAX_W_MBYTES
                        Maximum Write Mega Bytes Per Second

```


### List Logical Volumes


```bash
usage: sbcli lvol list [-h] [--cluster-id CLUSTER_ID] [--pool POOL] [--json]

optional arguments:
  -h, --help            show this help message and exit
  --cluster-id CLUSTER_ID
                        List LVols in particular cluster
  --pool POOL           List LVols in particular Pool ID or name
  --json                Print outputs in json format

```


### Get the Size and Maximum Size of the Logical Volume


```bash
usage: sbcli lvol list-mem [-h] [--json] [--csv]

optional arguments:
  -h, --help  show this help message and exit
  --json      Print outputs in json format
  --csv       Print outputs in csv format

```


### Get Logical Volume Details


```bash
usage: sbcli lvol get [-h] [--json] id

positional arguments:
  id          LVol id or name

optional arguments:
  -h, --help  show this help message and exit
  --json      Print outputs in json format

```


### Delete Logical Volume
This is only possible, if no more snapshots and non-inflated clones of the volume exist. The volume must be suspended before it can be deleted.

```bash
usage: sbcli lvol delete [-h] [--force] id [id ...]

positional arguments:
  id          LVol id or ids

optional arguments:
  -h, --help  show this help message and exit
  --force     Force delete LVol from the cluster

```


### Get Logical Volume Connection Strings
Multiple connections to the cluster are always available for multipath and high-availability.

```bash
usage: sbcli lvol connect [-h] id

positional arguments:
  id          LVol id

optional arguments:
  -h, --help  show this help message and exit

```


### Resize Logical Volume
The logical volume cannot exceed the maximum size for logical volumes or exceed total remaining provisioned space in pool. It cannot drop below the current utilization.

```bash
usage: sbcli lvol resize [-h] id size

positional arguments:
  id          LVol id
  size        New LVol size size: 10M, 10G, 10(bytes)

optional arguments:
  -h, --help  show this help message and exit

```


### Create Snapshot from Logical Volume


```bash
usage: sbcli lvol create-snapshot [-h] id name

positional arguments:
  id          LVol id
  name        snapshot name

optional arguments:
  -h, --help  show this help message and exit

```


### Create Logical Volume from Snapshot


```bash
usage: sbcli lvol clone [-h] [--resize RESIZE] snapshot_id clone_name

positional arguments:
  snapshot_id      snapshot UUID
  clone_name       clone name

optional arguments:
  -h, --help       show this help message and exit
  --resize RESIZE  New LVol size: 10M, 10G, 10(bytes)

```


### Moves a Full Copy of the Logical Volume between Nodes


```bash
usage: sbcli lvol move [-h] [--force] id node_id

positional arguments:
  id          LVol UUID
  node_id     Destination Node UUID

optional arguments:
  -h, --help  show this help message and exit
  --force     Force LVol delete from source node

```


### Get Logical Volume Capacity


```bash
usage: sbcli lvol get-capacity [-h] [--history HISTORY] id

positional arguments:
  id                 LVol id

optional arguments:
  -h, --help         show this help message and exit
  --history HISTORY  (XXdYYh), list history records (one for every 15 minutes)
                     for XX days and YY hours (up to 10 days in total).

```


### Get Logical Volume IO Statistics


```bash
usage: sbcli lvol get-io-stats [-h] [--history HISTORY] id

positional arguments:
  id                 LVol id

optional arguments:
  -h, --help         show this help message and exit
  --history HISTORY  (XXdYYh), list history records (one for every 15 minutes)
                     for XX days and YY hours (up to 10 days in total).

```


### Send Cluster Map


```bash
usage: sbcli lvol send-cluster-map [-h] id

positional arguments:
  id          LVol id

optional arguments:
  -h, --help  show this help message and exit

```


### Get Cluster Map


```bash
usage: sbcli lvol get-cluster-map [-h] id

positional arguments:
  id          LVol id

optional arguments:
  -h, --help  show this help message and exit

```


### Check Logical Volume Health


```bash
usage: sbcli lvol check [-h] id

positional arguments:
  id          UUID of LVol

optional arguments:
  -h, --help  show this help message and exit

```


## Management Node Commands


```bash
usage: sbcli mgmt [-h] {add,list,remove} ...

positional arguments:
  {add,list,remove}
    add              Add Management node to the cluster (local run)
    list             List Management nodes
    remove           Remove Management node

optional arguments:
  -h, --help         show this help message and exit

```


### Add Management Node to Cluster (execute locally)


```bash
usage: sbcli mgmt add [-h] cluster_ip cluster_id ifname

positional arguments:
  cluster_ip  the cluster IP address
  cluster_id  the cluster UUID
  ifname      Management interface name

optional arguments:
  -h, --help  show this help message and exit

```


### List Management Nodes


```bash
usage: sbcli mgmt list [-h] [--json]

optional arguments:
  -h, --help  show this help message and exit
  --json      Print outputs in json format

```


### Remove Management Node


```bash
usage: sbcli mgmt remove [-h] id

positional arguments:
  id          Mgmt node uuid

optional arguments:
  -h, --help  show this help message and exit

```


## Pool Commands


```bash
usage: sbcli pool [-h]
                  {add,set,list,get,delete,enable,disable,get-secret,upd-secret,get-capacity,get-io-stats}
                  ...

positional arguments:
  {add,set,list,get,delete,enable,disable,get-secret,upd-secret,get-capacity,get-io-stats}
    add                 Add a new Pool
    set                 Set pool attributes
    list                List pools
    get                 get pool details
    delete              Delete Pool
    enable              Set pool status to Active
    disable             Set pool status to Inactive.
    get-secret          Get pool secret
    upd-secret          Updates pool secret
    get-capacity        Get pool capacity
    get-io-stats        Get pool IO statistics

optional arguments:
  -h, --help            show this help message and exit

```


### Add new Pool


```bash
usage: sbcli pool add [-h] [--pool-max POOL_MAX] [--lvol-max LVOL_MAX]
                      [--max-rw-iops MAX_RW_IOPS]
                      [--max-rw-mbytes MAX_RW_MBYTES]
                      [--max-r-mbytes MAX_R_MBYTES]
                      [--max-w-mbytes MAX_W_MBYTES] [--has-secret]
                      name cluster_id

positional arguments:
  name                  Pool name
  cluster_id            Cluster UUID

optional arguments:
  -h, --help            show this help message and exit
  --pool-max POOL_MAX   Pool maximum size: 20M, 20G, 0(default)
  --lvol-max LVOL_MAX   LVol maximum size: 20M, 20G, 0(default)
  --max-rw-iops MAX_RW_IOPS
                        Maximum Read Write IO Per Second
  --max-rw-mbytes MAX_RW_MBYTES
                        Maximum Read Write Mega Bytes Per Second
  --max-r-mbytes MAX_R_MBYTES
                        Maximum Read Mega Bytes Per Second
  --max-w-mbytes MAX_W_MBYTES
                        Maximum Write Mega Bytes Per Second
  --has-secret          Pool is created with a secret (all further API
                        interactions with the pool and logical volumes in the
                        pool require this secret)

```


### Set Pool Attributes


```bash
usage: sbcli pool set [-h] [--pool-max POOL_MAX] [--lvol-max LVOL_MAX]
                      [--max-rw-iops MAX_RW_IOPS]
                      [--max-rw-mbytes MAX_RW_MBYTES]
                      [--max-r-mbytes MAX_R_MBYTES]
                      [--max-w-mbytes MAX_W_MBYTES]
                      id

positional arguments:
  id                    Pool UUID

optional arguments:
  -h, --help            show this help message and exit
  --pool-max POOL_MAX   Pool maximum size: 20M, 20G
  --lvol-max LVOL_MAX   LVol maximum size: 20M, 20G
  --max-rw-iops MAX_RW_IOPS
                        Maximum Read Write IO Per Second
  --max-rw-mbytes MAX_RW_MBYTES
                        Maximum Read Write Mega Bytes Per Second
  --max-r-mbytes MAX_R_MBYTES
                        Maximum Read Mega Bytes Per Second
  --max-w-mbytes MAX_W_MBYTES
                        Maximum Write Mega Bytes Per Second

```


### List Pools


```bash
usage: sbcli pool list [-h] [--json] [--cluster-id CLUSTER_ID]

optional arguments:
  -h, --help            show this help message and exit
  --json                Print outputs in json format
  --cluster-id CLUSTER_ID
                        ID of the cluster

```


### Get Pool Details


```bash
usage: sbcli pool get [-h] [--json] id

positional arguments:
  id          pool uuid

optional arguments:
  -h, --help  show this help message and exit
  --json      Print outputs in json format

```


### Delete Pool
It is only possible to delete a pool if it is empty (no provisioned logical volumes contained).

```bash
usage: sbcli pool delete [-h] id

positional arguments:
  id          pool uuid

optional arguments:
  -h, --help  show this help message and exit

```


### Set Pool Status to Active


```bash
usage: sbcli pool enable [-h] pool_id

positional arguments:
  pool_id     pool uuid

optional arguments:
  -h, --help  show this help message and exit

```


### Set Pool Status to Inactive.


```bash
usage: sbcli pool disable [-h] pool_id

positional arguments:
  pool_id     pool uuid

optional arguments:
  -h, --help  show this help message and exit

```


### Get Pool Secret


```bash
usage: sbcli pool get-secret [-h] pool_id

positional arguments:
  pool_id     pool uuid

optional arguments:
  -h, --help  show this help message and exit

```


### Updates Pool Secret


```bash
usage: sbcli pool upd-secret [-h] pool_id secret

positional arguments:
  pool_id     pool uuid
  secret      new 20 characters password

optional arguments:
  -h, --help  show this help message and exit

```


### Get Pool Capacity


```bash
usage: sbcli pool get-capacity [-h] pool_id

positional arguments:
  pool_id     pool uuid

optional arguments:
  -h, --help  show this help message and exit

```


### Get Pool IO Statistics


```bash
usage: sbcli pool get-io-stats [-h] [--history HISTORY] id

positional arguments:
  id                 Pool id

optional arguments:
  -h, --help         show this help message and exit
  --history HISTORY  (XXdYYh), list history records (one for every 15 minutes)
                     for XX days and YY hours (up to 10 days in total).

```


## Snapshot Commands


```bash
usage: sbcli snapshot [-h] {add,list,delete,clone} ...

positional arguments:
  {add,list,delete,clone}
    add                 Create new snapshot
    list                List snapshots
    delete              Delete a snapshot
    clone               Create LVol from snapshot

optional arguments:
  -h, --help            show this help message and exit

```


### Create new Snapshot


```bash
usage: sbcli snapshot add [-h] id name

positional arguments:
  id          LVol UUID
  name        snapshot name

optional arguments:
  -h, --help  show this help message and exit

```


### List Snapshots


```bash
usage: sbcli snapshot list [-h]

optional arguments:
  -h, --help  show this help message and exit

```


### Delete a Snapshot


```bash
usage: sbcli snapshot delete [-h] id

positional arguments:
  id          snapshot UUID

optional arguments:
  -h, --help  show this help message and exit

```


### Create lvol from snapshot


```bash
usage: sbcli snapshot clone [-h] [--resize RESIZE] id lvol_name

positional arguments:
  id               snapshot UUID
  lvol_name        LVol name

optional arguments:
  -h, --help       show this help message and exit
  --resize RESIZE  New LVol size: 10M, 10G, 10(bytes)

```


## Caching Client Node Commands


```bash
usage: sbcli caching-node [-h]
                          {deploy,add-node,list,list-lvols,remove,connect,disconnect,recreate}
                          ...

positional arguments:
  {deploy,add-node,list,list-lvols,remove,connect,disconnect,recreate}
    deploy              Deploy caching node on this machine (local exec)
    add-node            Add new Caching node to the cluster
    list                List Caching nodes
    list-lvols          List connected lvols
    remove              Remove Caching node from the cluster
    connect             Connect to LVol
    disconnect          Disconnect LVol from Caching node
    recreate            recreate Caching node bdevs

optional arguments:
  -h, --help            show this help message and exit

```


### Deploy Caching Node on this Machine (execute locally)


```bash
usage: sbcli caching-node deploy [-h] [--ifname IFNAME]

optional arguments:
  -h, --help       show this help message and exit
  --ifname IFNAME  Management interface name, default: eth0

```


### Add new Caching Node to Cluster


```bash
usage: sbcli caching-node add-node [-h] [--cpu-mask SPDK_CPU_MASK]
                                   [--memory SPDK_MEM]
                                   [--spdk-image SPDK_IMAGE]
                                   [--namespace NAMESPACE]
                                   cluster_id node_ip ifname

positional arguments:
  cluster_id            UUID of the cluster to which the node will belong
  node_ip               IP of caching node to add
  ifname                Management interface name

optional arguments:
  -h, --help            show this help message and exit
  --cpu-mask SPDK_CPU_MASK
                        SPDK app CPU mask, default is all cores found
  --memory SPDK_MEM     SPDK huge memory allocation, default is Max hugepages
                        available
  --spdk-image SPDK_IMAGE
                        SPDK image uri
  --namespace NAMESPACE
                        k8s namespace to deploy on

```


### List Caching Nodes


```bash
usage: sbcli caching-node list [-h]

optional arguments:
  -h, --help  show this help message and exit

```


### List Connected Logical Volumes


```bash
usage: sbcli caching-node list-lvols [-h] id

positional arguments:
  id          Caching Node UUID

optional arguments:
  -h, --help  show this help message and exit

```


### Remove Caching Node from Cluster


```bash
usage: sbcli caching-node remove [-h] [--force] id

positional arguments:
  id          Caching Node UUID

optional arguments:
  -h, --help  show this help message and exit
  --force     Force remove

```


### Connect to Logical Volume


```bash
usage: sbcli caching-node connect [-h] node_id lvol_id

positional arguments:
  node_id     Caching node UUID
  lvol_id     LVol UUID

optional arguments:
  -h, --help  show this help message and exit

```


### Disconnect Logical Volume From Caching Node


```bash
usage: sbcli caching-node disconnect [-h] node_id lvol_id

positional arguments:
  node_id     Caching node UUID
  lvol_id     LVol UUID

optional arguments:
  -h, --help  show this help message and exit

```


### Recreate a Caching Node bdevs


```bash
usage: sbcli caching-node recreate [-h] node_id

positional arguments:
  node_id     Caching node UUID

optional arguments:
  -h, --help  show this help message and exit

```
