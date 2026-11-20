---
title: "Unified DataStore"
description: "Prepare a storage array and its hosts for a simplyblock Unified DataStore: supported arrays, array account, host connectivity, credentials, and sizing."
weight: 29990
---

{{experimental}}

A Unified DataStore runs a simplyblock cluster on LUNs that simplyblock creates on an external storage array (see
[Unified DataStore](../architecture/concepts/unified-datastore.md) for the architecture). The array, its management access,
and the hosts' storage connectivity are prepared before the deployment. This page lists what has to be in place.

## Supported Storage Arrays

Each array family is driven by its own array plug-in. The plug-in key is what a deployment names.

| Plug-in key           | Arrays                                        | Protocols                               |
|-----------------------|-----------------------------------------------|-----------------------------------------|
| `pure-flasharray`     | Pure Storage FlashArray //X, //C, //XL, //E   | FC, iSCSI, NVMe/TCP, NVMe/RoCE, NVMe/FC |
| `netapp-ontap`        | NetApp AFF, FAS, and ASA (not ASA r2)         | FC, iSCSI, NVMe/TCP, NVMe/FC            |
| `dell-powerstore`     | Dell PowerStore                               | FC, iSCSI, NVMe/TCP, NVMe/FC            |
| `dell-powermax`       | Dell PowerMax                                 | FC, iSCSI, NVMe/TCP                     |
| `dell-powerflex`      | Dell PowerFlex 3.6 and 4.x                    | PowerFlex SDC                           |
| `hpe-wsapi`           | HPE Alletra Storage MP B10000, Primera, 3PAR  | FC, iSCSI                               |
| `hpe-nimble`          | HPE Alletra 5000 and 6000, Nimble             | FC, iSCSI                               |
| `ibm-flashsystem`     | IBM FlashSystem, Storage Virtualize, SVC      | FC, iSCSI, NVMe/TCP, NVMe/RoCE          |
| `hitachi-vsp`         | Hitachi VSP One Block, VSP E series, VSP 5000 | FC, iSCSI                               |
| `huawei-dorado`       | Huawei OceanStor Dorado                       | FC, iSCSI                               |
| `infinidat-infinibox` | Infinidat InfiniBox                           | FC, iSCSI                               |
| `aws-ebs`             | Amazon EBS io2 and io1 with Multi-Attach      | NVMe (Nitro instances)                  |

The options and the login fields of every plug-in are listed in the
[array plug-in reference](../reference/array-plugins.md).

## Array Preparation

- **Storage pool:** A pool (or the array's equivalent, such as an SVM, a CPG, or a storage resource pool) is set
  aside for the cluster's LUNs. Its name or id is given to the plug-in as an option.
- **RAID and thin provisioning:** The pool is RAID-protected, since the cluster keeps no parity of its own. Thin LUNs
  are recommended. The pool must be sized for the full capacity of all LUNs, or be monitored with an alert well before
  it fills up, because a full pool fails the writes of all LUNs at once.
- **Data services:** Array snapshots, array replication, and array-side deduplication are not used for the cluster's
  LUNs. Volumes encrypted by simplyblock do not deduplicate or compress on the array.
- **Ports:** For FC and iSCSI, the target ports the hosts reach are known. Where a plug-in maps through named port
  groups or host groups (`dell-powermax`, `hitachi-vsp`), they are given as options.

### Array Account

A dedicated account on the array is used by simplyblock. It needs permission to create, grow, and delete volumes in
the pool, to create and modify host objects, and to map and unmap volumes. Where the array scopes accounts, the
account is limited to the pool or the storage virtual machine of the cluster, for example, an SVM-scoped account with
the `vsadmin` role on NetApp ONTAP, or a user with the `storage_admin` role and its API token on Pure Storage
FlashArray.

### Management Access

The control plane reaches the array's management API over HTTPS. Its endpoint, for example,
`https://pure01.example.com`, must be reachable from the control-plane hosts. An array certificate that no public
certificate authority signed is given as a CA bundle at registration. TLS verification stays on outside of test
environments.

## Host Preparation

Every host that runs a storage node needs a working storage connection to the array before the cluster is deployed,
because the LUNs are presented to it while nodes are added. The LUNs are mapped and the host is rescanned by
simplyblock. Logging in to the array's targets and configuring the zoning are not.

| Protocol                     | Host preparation                                                                                                                                               |
|------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| iSCSI                        | A unique initiator name in `/etc/iscsi/initiatorname.iscsi`, and sessions logged in to the array's portals (one per path), set to log in automatically at boot |
| FC                           | HBA ports zoned to the array's target ports                                                                                                                    |
| NVMe/TCP, NVMe/RoCE, NVMe/FC | A unique host NQN in `/etc/nvme/hostnqn`, and connections to the array's NVMe subsystems or discovery controller that are restored at boot                     |
| PowerFlex SDC                | The PowerFlex SDC installed and connected to the PowerFlex system                                                                                              |

Host NQNs and iSCSI initiator names must be unique per host. Hosts cloned from one image often share them, and the
array then cannot tell the hosts apart.

### Multipathing

Every host reaches its LUNs over several paths. NVMe-oF LUNs are used with the native NVMe multipathing of the Linux
kernel. SCSI LUNs over FC or iSCSI are used through device-mapper multipath: every path of a LUN is a SCSI disk of the
host, and the map `multipathd` builds over them is the device the storage node uses. The paths below a map are never
used on their own, and a LUN reached over a single path is used as that path's disk. A multipath map is served by the
io_uring I/O engine of the storage node, because the Linux AIO interface cannot submit I/O to device-mapper multipath
devices.

`multipathd` is configured for the array as its vendor recommends, with two requirements:

- **Maps for the cluster's LUNs:** `multipathd` builds a map for every LUN of the cluster, for example, with
  `find_multipaths yes`. The array's LUNs are not blacklisted.
- **Failing within 60 seconds:** A map whose paths are all gone fails its I/O within 60 seconds rather than queueing
  it without limit. A storage node gives up on a LUN I/O after 60 seconds, so a map that queues longer stalls the node
  instead of failing over. The product of `polling_interval` and `no_path_retry` is kept below 60 seconds, and
  `no_path_retry queue` is not used.

```plain title="Example of the multipath settings for the cluster's LUNs in /etc/multipath.conf"
defaults {
    find_multipaths yes
    polling_interval 5
}
overrides {
    no_path_retry 6
}
```

Settings in `overrides` take precedence over the built-in defaults of the array's device entry, some of which queue
I/O for longer.

### Journal

Every storage node keeps a journal of its own, which is written before its data and is never shared with another
node. Its placement is chosen per cluster in `spec.multiAttach.array.journal`:

| Placement       | Where the journal is kept                                                                                         | Host requirement                                  |
|-----------------|-------------------------------------------------------------------------------------------------------------------|---------------------------------------------------|
| `LUN` (default) | A LUN of its own, created on the array when the node is added, next to its data LUN, and mapped to that node only | None: no local device is used                     |
| `Local`         | A local disk or partition of the worker, used whole                                                               | One free local disk or partition per storage node |

With `LUN`, the journal LUNs can be created in a pool of their own. Every write of a volume passes through the journal
first, so a pool of higher performance or priority than the data pool shortens the write latency. A dedicated pool
is set up on the array beforehand, or an existing pool is named. It is given in `journal.options` with the plug-in
option that places the data LUNs in `options`. Options not named in `journal.options` are taken from `options`.
Without such an option, a journal LUN is created where the data LUNs are.

| Plug-in                                  | Option placing the journal LUNs                                  |
|------------------------------------------|------------------------------------------------------------------|
| `netapp-ontap`                           | `aggregates`                                                     |
| `dell-powerstore`                        | `appliance_id`                                                   |
| `dell-powermax`                          | `srp`                                                            |
| `dell-powerflex`                         | `storage_pool_id` (and `protection_domain_id`)                   |
| `hpe-wsapi`                              | `cpg`                                                            |
| `hpe-nimble`                             | `pool`, and `performance_policy` for a policy of higher priority |
| `ibm-flashsystem`, `infinidat-infinibox` | `pool`                                                           |
| `hitachi-vsp`                            | `pool_id`                                                        |
| `huawei-dorado`                          | `storage_pool`                                                   |
| `aws-ebs`                                | `volume_type` and `iops`, for journal volumes with more IOPS     |
| `pure-flasharray`                        | None: the array has one pool, and journal LUNs are created in it |

The plug-in options are described in the [array plug-in reference](../reference/array-plugins.md).

```yaml title="Example of journal LUNs in a pool of their own on IBM FlashSystem"
spec:
  multiAttach:
    array:
      plugin: ibm-flashsystem
      options:
        pool: capacity
      journal:
        placement: LUN
        size: 64Gi
        options:
          pool: latency
```

A journal LUN is never presented to standby nodes and is not fenced: when a node fails, its journal is not needed for
the takeover of its data LUN. Its size defaults to 3% of `lunSize`, at least 2 GiB, rounded up to whole GiB.

With `Local`, a fast local NVMe disk or a partition of one is preferred. Its size is about 3% of the node's LUN size,
at least 2 GiB.

A journal on a partition of the node's data LUN is not offered. The data LUN is presented to standby nodes and taken
over by them as a whole, and it is grown as a whole, neither of which a partition of it allows.

A placement chosen later applies to storage nodes added afterward. Existing nodes keep their journals.

## Credentials

The array login is kept in one of three places, chosen per cluster:

| Source       | Where the login is kept                                                                      | Requirement                                                      |
|--------------|----------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| `Secret`     | A Kubernetes Secret, encrypted by the cluster's key management service once it is registered | An external key management service, or the explicit local opt-in |
| `VaultKV`    | A HashiCorp Vault or OpenBao KV v2 secret, read when the control plane connects to the array | The cluster's key management service is Vault or OpenBao         |
| `KMIPSecret` | A secret-data object of a KMIP server, read when the control plane connects to the array     | The cluster's key management service is KMIP                     |

`VaultKV` and `KMIPSecret` keep the login out of Kubernetes entirely. A Vault KV secret holds one key per login field.
A KMIP object holds the login fields as a JSON object, or a single value such as an API token, which is then named
with the reference's `field`. The key management service itself is set up as described in
[OpenBao KMS](../kubernetes/installation/openbao-kms.md) or [KMIP KMS](../kubernetes/installation/kmip-kms.md).

## Sizing

| Item                  | Rule                                                                                                                                                                      |
|-----------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Storage nodes         | At least the fault tolerance plus one, on as many workers: 2 for a fault tolerance of `1`, 3 for `2`                                                                      |
| LUNs                  | One data LUN per storage node, all of the same size                                                                                                                       |
| LUN size              | Large thin LUNs sized for the expected growth. All LUNs are grown together later.                                                                                         |
| Presentations per LUN | The fault tolerance plus one hosts. The array must allow that many hosts per LUN (`aws-ebs`: at most 16).                                                                 |
| Array pool            | The full capacity of all LUNs, or an alert on the pool's usage                                                                                                            |
| Journal               | `LUN`: one LUN per storage node, 3% of the LUN size, at least 2 GiB, optionally in a faster pool. `Local`: one local disk or partition per storage node of the same size. |

## Checklist

- The array plug-in for the array is listed in [Supported Storage Arrays](#supported-storage-arrays).
- A pool and a dedicated array account with the permissions above exist.
- The management endpoint is reachable from the control plane, and its CA bundle is at hand if needed.
- Every host has a unique initiator for the chosen protocol and a working connection to the array.
- The journal placement is chosen: with `LUN`, the pool for the journal LUNs exists; with `Local`, every host has one
  free local disk or partition per storage node.
- The key management service and the credential source are chosen, and the login is stored there.
