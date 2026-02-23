---
title: "Stopping and Manually Restarting a Storage Node"
weight: 10700
---

There are a few reasons to manually restart a storage node:

- After a storage node became unavailable, the auto-restart did not work
- A cluster upgrade
- A planned storage node maintenance

!!! critical
    There is an auto-restart functionality, which restarts a storage node in case the monitoring service detects
    an issue with that specific node. This can be the case if one of the containers exited, after a reboot 
    of the host, or because of an internal node error which causes the management interface to become 
    unresponsive. The auto-restart functionality retries multiple times. It will **not** work in one of 
    the following cases:
    
    - The cluster is suspended (e.g. two or more storage nodes are offline)
    - The RPC interface is responsive and the container is up, but the storage node has another health issue
    - The host or docker service are not available or hanging (e.g. network issue) 
    - Too many retries (e.g. because there is a problem with the lvolstore recovering for some of the logical volimes)
    
    In these cases, a manual restart is required.

## Shutdown of Storage Nodes

!!! warning
    Nodes can only be restarted from `offline` state!
    
    It is important to ensure that the cluster is not in `degraded` state and all other nodes are `online` 
    before shutting down a storage node for maintainance or upgrades! Otherwise loss of availability - io interrupt - may occur!

Suspending a storage node and then shutting it down: 

```bash title="Shutdown storage node"
{{ cliname }} storage-node suspend <NODE_ID> 
{{ cliname }} storage-node shutdown <NODE_ID> 
```   

If that does not work, it is ok to forcefully shutdown the storage node.

```bash title="Shutdown storage node forcefully"
{{ cliname }} storage-node shutdown <NODE_ID> --force
```
### Storage Node in Offline State

It is very important to notice that with a storage node in state `offline`, the cluster is in a `degraded` state.
Write and read performance can be impacted, and if another node goes offline, I/O will be interrupted.
Therefore, it is recommended to keep nodes in `offline` state as short as possible!

If a longer maintenance window (hours to weeks) is required, it is recommended to migrate 
the storage node to another host for the time being. This alternative host can be without NVMe devices.
Node migration is entirely automated. Later the storage node can be migrated back to its original host.

### Restarting a Storage Node

A storage node can be restarted using the following command:

```bash title="Restarting storage node"
{{ cliname }} storage-node restart <NODE_ID> 
```    

In the rare case the restart may hang. If this is the case, it is ok to forcefully shutdown and forcefully
restart the storage node:

```bash title="Restarting storage node"
{{ cliname }} storage-node restart <NODE_ID> --force 
```   

### Restarting Docker Service

!!! warning
    This applies to disaggregated storage nodes under Docker (only non-Kubernetes setups) only. 
  
If there is a problem with the entire Docker service on a host, the Docker service may require a restart. 
In such a case, auto-restart will not be able to automatically self-heal the storage node. This happens because the
container responsible for self-healing and auto-restarting (SNodeAPI) itself does not respond anymore.

```bash title="Restarting docker service"
sudo systemctl restart docker --force
```  

After restarting the Docker service, the auto-restart will start to self-heal the storage node after a short delay.
A manual restart of the storage node is not required.
