---
title: "Unified DataStore"
description: "How simplyblock creates, presents, fences, and takes over the LUNs of an FC, iSCSI, or NVMe-oF storage array through array plug-ins."
weight: 30655
---

{{experimental}}

A Unified DataStore is a simplyblock cluster whose data lives on LUNs of an external storage array, with the array
integrated into the control plane. The LUNs are created, presented to the hosts, grown, cut off, and deleted by
simplyblock itself, through an array plug-in. Every LUN is presented to more than one host. When the storage node
serving a LUN fails, the LUN is taken over by a standby node within seconds, and no data has to be rebuilt.

Arrays of Pure Storage, NetApp, Dell, HPE, IBM, Hitachi, Huawei, and Infinidat are supported, as well as Amazon EBS
volumes with Multi-Attach (see [Array Plug-ins](../../reference/array-plugins.md)). On top of the LUNs, the full
simplyblock feature set is available: Kubernetes-native volumes, snapshots and clones, QoS, encryption,
replication, and disaster recovery. The array protects the data, and simplyblock protects the access to it.

## How It Works

```plain title="Storage stack of a Unified DataStore"
Kubernetes workloads
        │  NVMe/TCP or NVMe/RoCE
Simplyblock storage nodes  (1+0, thin provisioning, snapshots, replication)
        │  one data LUN per node, presented to its standby nodes as well
LUNs on the storage array  (FC, iSCSI, NVMe-oF; RAID in the array)
        ▲
        │  management API (HTTPS)
Simplyblock control plane  (array plug-in: create, map, grow, fence, delete)
```

The cluster is created in multi-attach mode and runs `1+0`: every volume is spread across the data LUNs of all
storage nodes, and no parity is kept, because every LUN is already protected by the RAID of the array. Each storage
node owns exactly one data LUN. Its journal is kept on a LUN of its own, which can be placed in a faster pool of the
array and is mapped to that node only, or on a local disk or partition of the host (see
[Journal](../../deployment-preparation/unified-datastore.md#journal)).

Every host reaches its LUNs over several paths. SCSI LUNs over FC or iSCSI are used through device-mapper multipath
maps, and NVMe-oF LUNs through the native NVMe multipathing of the Linux kernel. The loss of a path is handled below
simplyblock, and the loss of all paths of a host like the failure of its storage node.

The fault tolerance (`1` or `2`) states how many storage-node failures the cluster survives. A node's LUN is presented
to the node itself and to as many standby nodes as the fault tolerance: its secondary, and with a fault tolerance of
`2` also its tertiary. Only one of them serves the LUN at a time. All other nodes reach it over NVMe-oF, through a
controller that does not depend on which host currently exports the LUN.

## Components

| Component            | Runs in               | Task                                                                                                                                 |
|----------------------|-----------------------|--------------------------------------------------------------------------------------------------------------------------------------|
| Array plug-in        | Control plane         | Creates, maps, unmaps, grows, and deletes LUNs and host objects through the management API of one array family                       |
| Credential store     | Control plane and KMS | Holds the array login wrapped by the cluster's key management service, or a reference to a secret in Vault or a KMIP server          |
| LUN lifecycle        | Control plane         | Creates a node's LUN when the node is added, presents it to the standby nodes, grows all LUNs together, and releases or deletes them |
| LUN watchdog         | Control plane         | Probes every node that serves a LUN twice per second and starts the takeover of a lost node's LUNs                                   |
| LUN takeover         | Control plane         | Fences the lost node, reopens its LUN on a standby node, and adds the new path to every node                                         |
| Storage node agent   | Every host            | Reports the host's iSCSI, FC, and NVMe initiators and rescans the host for newly presented LUNs                                      |
| Simplyblock Operator | Kubernetes            | Registers the array from the `StorageCluster` and holds node additions until the registration succeeded                              |

## LUN Lifecycle

Every LUN of a Unified DataStore is created by simplyblock. LUNs created by anybody else are never touched.

| Event                    | What happens on the array                                                                                                                                         |
|--------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Array registration       | The plug-in connects with the login and reads the array's capabilities. Nothing is saved when the connection or the login fails.                                  |
| Storage node addition    | The host is registered on the array with its initiators. A LUN of the configured size is created and mapped to it. The host is rescanned until the LUN appears.   |
| LVS role assignment      | The LUN is mapped to the node's secondary and, with a fault tolerance of `2`, its tertiary. A node that loses a role loses the mapping, unless it serves the LUN. |
| Capacity growth          | All LUNs are grown by the same factor on the array. Every host is rescanned until it sees the new size, and the devices are grown online.                         |
| Storage node failure     | The node is fenced from its LUN, and the LUN is taken over by a standby node (see [Node Failure and LUN Takeover](#node-failure-and-lun-takeover)).               |
| Storage node removal     | The node's LUN is unmapped from every host. The LUN is kept.                                                                                                      |
| Storage cluster deletion | Every LUN created for the cluster is unmapped and deleted.                                                                                                        |

### Ownership of LUNs

A LUN is named `sb-<cluster hash><LUN hash>` on the array, which identifies both the cluster and the storage node it
was created for. Most arrays carry no free-form tags, so the name is how ownership is recorded. Every operation of the
plug-in checks it first, and a LUN of another cluster, or one created outside simplyblock, is refused. Before a LUN is
grown, mapped, or deleted, its WWN or NGUID is also compared with the one recorded at its creation.

Host objects are named `sb-<hostname>`, shortened with a hash suffix where the array limits names to fewer
characters. LUNs are only grown, never shrunk.

## Node Failure and LUN Takeover

With `1+0`, every volume has data on every LUN, so a lost LUN stops the I/O of all volumes until the LUN is served
again. The takeover is therefore started by its own fast detection rather than by the regular node monitoring.

1. **Detection:** Every node that serves a LUN is probed every 0.5 seconds. A node is lost at once when its agent
   reports that the storage-plane process is not running, and after 2 seconds when neither the storage plane nor the
   agent answers. A node whose storage plane answers slowly but runs is not taken over.
2. **Fencing:** The lost node is cut off from the LUN first. Its host may still have writes queued in its multipath
   layer, and if they landed later they would overwrite newer data. The fence is an NVMe or SCSI persistent
   reservation taken over by the standby where the plug-in supports reservations, and otherwise an unmap of the LUN
   at the array. The takeover does not continue without the fence.
3. **Standby selection:** The LUN's secondary is chosen, otherwise its tertiary. It must be online, see the LUN, and
   find the simplyblock signature in its first block. These checks only read from the LUN.
4. **Reopening:** The LUN's data device is opened on the standby without being formatted, and exported under the
   same NVMe-oF subsystem and namespace identity as before.
5. **New path:** The standby's export is added as a new path to the LUN's controller on every node, where the held
   I/O resumes. The failed node's path is removed.

While no path is available, the nodes hold the LUN's I/O for up to 150 seconds instead of failing it. A takeover gives
up after 90 seconds, and the LUN is marked unavailable. On the test systems, the I/O of a takeover started by the fast
detection paused for a few seconds.

A takeover is not started while more nodes of the cluster fail their probes than the fault tolerance allows, or while
no other node has answered recently. In both cases, the control plane itself may be the one that is cut off.

When the failed node returns, it is not given its LUN back. It becomes a standby of it, and the LUN stays with the
node that took it over.

## Credentials

The array login is never stored in the clear in the cluster database. Three sources are accepted:

- **Managed:** The login is given once, at registration. It is encrypted with the cluster's credentials key in the
  [key management service](external-key-management.md) (HashiCorp Vault Transit, OpenBao, or KMIP) and bound to the
  array and its endpoint. A login encrypted for one endpoint is refused for any other, so an endpoint changed in the
  database cannot redirect it.
- **Vault KV:** The login stays in a HashiCorp Vault or OpenBao KV v2 secret. Only its location is stored, and it is
  read when the control plane connects to the array.
- **KMIP secret:** The login stays in a secret-data object of a KMIP server. Only its identifier is stored.

A cluster without an external key management service can only use managed credentials after an explicit opt-in,
because its local key store keeps them effectively unencrypted.

## Thin Provisioning on Two Levels

Thin provisioning applies twice: simplyblock allocates volume capacity only when it is written, and the array
allocates LUN capacity only when simplyblock writes to it. This allows large LUNs at no upfront cost. Two effects
are considered:

- **Space is not returned to the array:** Simplyblock reuses capacity freed by deleted volumes and snapshots for new
  data, but it does not release it to the array. The array's allocation of a LUN grows up to the highest capacity
  simplyblock has used on it.
- **The array pool can run out first:** Simplyblock sees the full size of the LUNs. If the array's thin pool is
  smaller, it can fill up while simplyblock still reports free capacity. Writes then fail on all LUNs at once, which
  takes the cluster offline. The pool of the array is therefore monitored, or sized for the full LUN capacity.

## Division of Responsibilities

| Function                                   | Array                         | Simplyblock                                   |
|--------------------------------------------|-------------------------------|-----------------------------------------------|
| Protection against drive failures          | Yes, with RAID                | Not used (`1+0`)                              |
| Protection against host or path loss       | Presents each LUN to standbys | Yes, by LUN takeover                          |
| LUN provisioning and host mapping          | Executes                      | Decides and drives, through the array plug-in |
| Thin provisioning                          | Yes, for the LUNs             | Yes, for the volumes                          |
| Snapshots, clones, and copy-on-write       | Not used                      | Yes                                           |
| Replication, backup, and disaster recovery | Not used                      | Yes                                           |
| Encryption                                 | Optional                      | Yes, per volume                               |
| QoS                                        | Not used                      | Yes, per volume, pool, and service class      |

The array is a shared failure domain: its outage stops the whole cluster. Array snapshots and array replication are
not consistent across the LUNs of all nodes and cannot be used to restore a cluster.

## Limitations

- **Path failover:** A multipath map of a SCSI LUN completes a path failover, or fails its I/O, within 60 seconds,
  because a storage node gives up on a LUN I/O after 60 seconds (see
  [Multipathing](../../deployment-preparation/unified-datastore.md#multipathing)).
- **Protocols:** The protocols a plug-in supports are listed in the [array plug-in reference](../../reference/array-plugins.md).
  Several plug-ins support FC and iSCSI only.
- **Capacity:** Capacity is added by growing all LUNs together or by adding storage nodes. A single LUN is never grown
  alone.
- **Validation:** The array plug-ins are experimental. Their API usage is checked against each vendor's own client
  libraries, and validation against the arrays themselves is in progress.
