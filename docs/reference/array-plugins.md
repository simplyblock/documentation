---
title: "Array Plug-ins"
description: "Reference of the simplyblock array plug-ins for Unified DataStores: supported arrays, protocols, LUN sizes, login fields, and plug-in options."
weight: 20170
---

{{experimental}}

An array plug-in connects a [Unified DataStore](../architecture/concepts/unified-datastore.md) to one family of storage
arrays. It is chosen by its key when the array is registered, and its options and login fields are given with it.
This page lists the plug-ins, what they need, and what they create on the array.

## Common Behavior

Every plug-in creates one LUN per storage node, named `sb-<cluster hash><LUN hash>`, and one host object per host,
named `sb-<hostname>`. Names longer than the array allows are shortened with a hash suffix. A plug-in acts only on
LUNs whose name carries the cluster's hash, and it compares a LUN's WWN or NGUID with the one recorded at creation
before it grows, maps, or deletes the LUN. LUNs are only grown, never shrunk.

Every request goes over HTTPS with certificate verification. A session the array expires or rejects is opened again
once before the request fails. Requests that only read are retried on connection errors and on the answers `502`,
`503`, and `504`.

## Common Options

These options apply to every plug-in except `aws-ebs`. In a `StorageCluster`, `protocol` and the CA bundle are fields
of their own (`array.protocol`, `array.caBundle`), and every other option is given under `array.options` as a string.
A string option is read as the type of its default: `true` or `false` (also `yes`, `no`, `on`, `off`, `1`, and `0`),
a number, a comma-separated list, or a JSON object where it starts with a brace.

| Option       | Default | Meaning                                                                                                                                 |
|--------------|---------|-----------------------------------------------------------------------------------------------------------------------------------------|
| `protocol`   | -       | `iscsi`, `fc`, `nvme-tcp`, `nvme-rdma`, `nvme-fc`, or `sdc`. Required. The hosts are registered with their initiators of this protocol. |
| `ca_bundle`  | -       | The PEM certificate the management endpoint is verified against                                                                         |
| `verify_tls` | `true`  | `false` turns certificate verification off, for test environments only                                                                  |
| `timeout_s`  | `60`    | The timeout of a single request to the management API, in seconds                                                                       |

## Supported Systems

| Plug-in key           | Protocols                               | Size granularity | Minimum LUN size | Login fields           |
|-----------------------|-----------------------------------------|------------------|------------------|------------------------|
| `pure-flasharray`     | FC, iSCSI, NVMe/TCP, NVMe/RoCE, NVMe/FC | 512 B            | 1 MiB            | `api_token`            |
| `netapp-ontap`        | FC, iSCSI, NVMe/TCP, NVMe/FC            | 4 KiB            | 1 MiB            | `password`, `username` |
| `dell-powerstore`     | FC, iSCSI, NVMe/TCP, NVMe/FC            | 8 KiB            | 1 MiB            | `password`, `username` |
| `dell-powermax`       | FC, iSCSI, NVMe/TCP                     | 1.875 MiB        | 1.875 MiB        | `password`, `username` |
| `dell-powerflex`      | PowerFlex SDC                           | 8 GiB            | 8 GiB            | `password`, `username` |
| `hpe-wsapi`           | FC, iSCSI                               | 256 MiB          | 256 MiB          | `password`, `username` |
| `hpe-nimble`          | FC, iSCSI                               | 1 MiB            | 1 MiB            | `password`, `username` |
| `ibm-flashsystem`     | FC, iSCSI, NVMe/TCP, NVMe/RoCE          | 512 B            | 1 MiB            | `password`, `username` |
| `hitachi-vsp`         | FC, iSCSI                               | 1 MiB            | 64 MiB           | `password`, `username` |
| `huawei-dorado`       | FC, iSCSI                               | 1 MiB            | 1 MiB            | `password`, `username` |
| `infinidat-infinibox` | FC, iSCSI                               | 1 MiB            | 1 MiB            | `password`, `username` |

### Pure Storage FlashArray (`pure-flasharray`)

The plug-in uses the FlashArray REST API 2.x (Purity//FA 6 and later) and logs in with the API token of an array user. Volumes are created in the array's default container, and host objects carry the hosts' IQNs, WWPNs, or NQNs. A deleted volume is destroyed and stays recoverable for the array's eradication delay, unless `eradicate` is set. Every protocol of the array is supported, and NVMe hosts see the volume's NGUID.

| Option        | Required | Default | Meaning                                                                                                   |
|---------------|----------|---------|-----------------------------------------------------------------------------------------------------------|
| `eradicate`   | No       | `false` | Eradicates deleted volumes at once instead of leaving them recoverable for the array's eradication delay. |
| `api_version` | No       | -       | Pins the REST 2.x version, for example, `2.21`. Unset, the newest version both sides support is used.     |

### NetApp ONTAP (`netapp-ontap`)

The plug-in uses the ONTAP REST API of ONTAP 9 (AFF, FAS, ASA, and Lenovo ThinkSystem DM) and logs in with an account of the storage VM. Every LUN gets a thin FlexVol of its own, without snapshot reserve or snapshot policy. Hosts become initiator groups for SCSI and hosts of an NVMe subsystem for NVMe. ASA r2 systems, which have no FlexVols, are refused. A deleted FlexVol stays in ONTAP's volume recovery queue unless `skip_recovery_queue` is set.

| Option                     | Required | Default | Meaning                                                                                                                     |
|----------------------------|----------|---------|-----------------------------------------------------------------------------------------------------------------------------|
| `svm`                      | Yes      | -       | The storage VM that owns the cluster's volumes, initiator groups, and NVMe subsystems.                                      |
| `protocol_family`          | No       | `scsi`  | `scsi` (LUNs) or `nvme` (namespaces). Derived from the protocol and only checked when stated.                               |
| `aggregates`               | No       | -       | Aggregates for new FlexVols, comma-separated. With several, the one with the most free space is used. Unset, ONTAP chooses. |
| `volume_per_lun`           | No       | `true`  | Creates one FlexVol per LUN or namespace.                                                                                   |
| `flexvol`                  | No       | -       | An existing FlexVol for all LUNs or namespaces. Required when `volume_per_lun` is `false`.                                  |
| `space_guarantee`          | No       | `none`  | The FlexVol space guarantee: `none` (thin) or `volume`.                                                                     |
| `snapshot_reserve_percent` | No       | `0`     | The FlexVol snapshot reserve, 0 to 90.                                                                                      |
| `snapshot_policy`          | No       | `none`  | The FlexVol snapshot policy.                                                                                                |
| `flexvol_headroom_percent` | No       | `5`     | How much larger a FlexVol is than its LUN or namespace, for metadata.                                                       |
| `os_type`                  | No       | `linux` | The `os_type` of LUNs, namespaces, initiator groups, and subsystems.                                                        |
| `namespace_block_size`     | No       | `4096`  | The block size of NVMe namespaces: `512` or `4096`.                                                                         |
| `job_timeout_s`            | No       | `300`   | Seconds to wait for an asynchronous ONTAP job.                                                                              |
| `skip_recovery_queue`      | No       | `false` | Deletes FlexVols with `force=true`, so that they do not stay in the volume recovery queue and keep using space.             |

### Dell PowerStore (`dell-powerstore`)

The plug-in uses the PowerStore REST API (PowerStoreOS 3 and 4). Hosts are created with the hosts' initiators and the `os_type` option, and volumes are attached to them directly. NVMe/TCP and NVMe/FC hosts are registered with their host NQN.

| Option         | Required | Default | Meaning                                                                                                          |
|----------------|----------|---------|------------------------------------------------------------------------------------------------------------------|
| `os_type`      | No       | `Linux` | The `os_type` of the host objects simplyblock creates.                                                           |
| `appliance_id` | No       | -       | Creates volumes on this appliance of a multi-appliance cluster, for example, `A1`. Unset, the array places them. |

### Dell PowerMax (`dell-powermax`)

The plug-in uses the Unisphere for PowerMax REST API 10. Every LUN gets a storage group of its own in the configured storage resource pool, and every mapping becomes a masking view of that storage group, the host's initiator group, and a port group. The port group is required to map LUNs and is given per protocol where the hosts use several. NVMe hosts are registered with their host NQN and host ID, which is derived from a host NQN of the form `nqn.2014-08.org.nvmexpress:uuid:<UUID>`.

| Option          | Required | Default | Meaning                                                                                                                               |
|-----------------|----------|---------|---------------------------------------------------------------------------------------------------------------------------------------|
| `symmetrix_id`  | Yes      | -       | The 12-digit serial of the array, for example, `000197900123`.                                                                        |
| `srp`           | No       | `SRP_1` | The storage resource pool of new storage groups.                                                                                      |
| `service_level` | No       | -       | The service level of new storage groups, for example, `Diamond`. Unset, none.                                                         |
| `port_group`    | No       | -       | The port group of masking views: one name, or a JSON object from protocol (`iscsi`, `fc`, `nvme-tcp`) to name. Needed to map volumes. |
| `api_version`   | No       | `100`   | The Unisphere REST version in the URL: `100` for 10.0, `101` for 10.1, and so on.                                                     |
| `async_jobs`    | No       | `false` | Runs changes as Unisphere jobs and polls them. Recommended for large arrays, where synchronous calls time out.                        |
| `job_timeout_s` | No       | `600`   | Seconds to wait for an asynchronous job.                                                                                              |

### Dell PowerFlex (`dell-powerflex`)

The plug-in uses the PowerFlex REST gateway of PowerFlex 3.6 and 4.x. LUNs are PowerFlex volumes in the configured storage pool and are presented through the PowerFlex SDC, which has to run on every host. A host is its SDC, identified by the SDC's GUID, and the SDC registers itself with the PowerFlex system. Volume sizes are multiples of 8 GiB. Volumes are mapped with multiple mappings allowed, so that the standby nodes can be given access.

| Option                 | Required | Default | Meaning                                                                                                                                       |
|------------------------|----------|---------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| `storage_pool_id`      | Yes      | -       | The id of the storage pool new volumes are created in.                                                                                        |
| `protection_domain_id` | No       | -       | The protection domain of the storage pool, where the gateway asks for it.                                                                     |
| `auth`                 | No       | `auto`  | `auto`, `token` (3.x), or `oauth` (4.x). `auto` logs in through `/api/login` and picks basic or bearer authentication by the gateway version. |
| `sdc_naming`           | No       | `claim` | `claim` names unnamed SDCs after their host and treats an SDC named differently as another host's. `ignore` never reads or writes SDC names.  |

### HPE Alletra MP / Primera / 3PAR (`hpe-wsapi`)

The plug-in uses the WSAPI of HPE Alletra Storage MP B10000, Primera, and 3PAR. Volumes are created in the configured CPG, thin or with data reduction, in steps of 256 MiB. Hosts carry iSCSI names or FC WWPNs, and mappings are VLUNs. Names are limited to 31 characters.

| Option         | Required | Default | Meaning                                                                                              |
|----------------|----------|---------|------------------------------------------------------------------------------------------------------|
| `cpg`          | Yes      | -       | The Common Provisioning Group new volumes are created in.                                            |
| `provisioning` | No       | `tpvv`  | `tpvv` (thin) or `reduce` (thin with deduplication and compression, on Primera and Alletra MP only). |
| `persona`      | No       | `2`     | The host persona of new hosts. `2` is Generic-ALUA.                                                  |

### HPE Alletra 5000/6000 / Nimble (`hpe-nimble`)

The plug-in uses the NimbleOS REST API of HPE Alletra 5000 and 6000 and Nimble arrays. The endpoint includes the API port, for example, `https://nimble01.example.com:5392`. Hosts become initiator groups, and mappings become access control records. A volume is taken offline before it is deleted. Hosts see the volume by its EUI-64 identifier.

| Option               | Required | Default | Meaning                                                               |
|----------------------|----------|---------|-----------------------------------------------------------------------|
| `pool`               | No       | -       | The pool new volumes are created in. Unset, the array's default pool. |
| `performance_policy` | No       | -       | The performance policy of new volumes. Unset, the array's default.    |
| `job_timeout_s`      | No       | `300`   | Seconds to wait for an asynchronous job.                              |

### IBM FlashSystem / Storage Virtualize (`ibm-flashsystem`)

The plug-in uses the REST API of IBM Storage Virtualize (FlashSystem and SAN Volume Controller) on port 7443. Volumes are created in the configured pool, thin by default. A host is created with one kind of port, and further ports are added to it. NVMe hosts are created with the protocol of their transport.

| Option                | Required | Default | Meaning                                                                                            |
|-----------------------|----------|---------|----------------------------------------------------------------------------------------------------|
| `pool`                | Yes      | -       | The storage pool (MDisk group), by name or id, of new volumes.                                     |
| `thin`                | No       | `true`  | Creates thin-provisioned volumes. In a data reduction pool, these are thin DRP volumes.            |
| `io_group`            | No       | -       | The I/O group that owns new volumes. Unset, the array chooses.                                     |
| `rest_root`           | No       | `/rest` | The REST path root. `/rest/v1` on code levels that refuse `/rest`.                                 |
| `nvme_protocol_value` | No       | -       | Overrides the `mkhost -protocol` value of NVMe hosts. Unset, `tcpnvme` or `rdmanvme` by transport. |

### Hitachi VSP (`hitachi-vsp`)

The plug-in uses the Configuration Manager REST API of Hitachi VSP One Block, VSP E series, and VSP 5000, either embedded in the storage system or through an Ops Center API Configuration Manager server (`storage_device_id`). Volumes are DP volumes (LDEVs) in the configured pool, labeled with their name. Every host gets a host group on each of the configured target ports of its protocol. Configuration changes run as asynchronous jobs, and some models need the resource-group lock (`use_lock`).

| Option              | Required | Default      | Meaning                                                                                                                                                                |
|---------------------|----------|--------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `pool_id`           | Yes      | -            | The number of the DP pool new volumes are created in.                                                                                                                  |
| `ports`             | Yes      | -            | The target ports hosts are presented on, comma-separated, for example, `CL1-A,CL2-A`. A host uses the ports of its protocol.                                           |
| `storage_device_id` | No       | -            | The `storageDeviceId`, for example, `886000123456`, when the endpoint is an Ops Center API Configuration Manager server. Unset for the API embedded in the controller. |
| `ldev_range`        | No       | -            | Restricts new LDEV numbers, and volume lookups, to `start-end`.                                                                                                        |
| `host_mode`         | No       | `LINUX/IRIX` | The host mode of new host groups.                                                                                                                                      |
| `host_mode_options` | No       | -            | The host mode option numbers of new host groups.                                                                                                                       |
| `job_timeout_s`     | No       | `300`        | Seconds to wait for an asynchronous job.                                                                                                                               |
| `use_lock`          | No       | `false`      | Takes the resource-group lock around configuration changes, which some models need.                                                                                    |
| `lock_wait_s`       | No       | `30`         | Seconds to wait for the resource-group lock.                                                                                                                           |

### Huawei OceanStor Dorado (`huawei-dorado`)

The plug-in uses the DeviceManager REST API of OceanStor Dorado V6 and OceanStor 6. LUNs are created thin in the configured storage pool. Every host gets a host group, a LUN group, and a mapping view of its own, and LUNs are mapped by adding them to the host's LUN group. Names are limited to 31 characters.

| Option         | Required | Default | Meaning                                                      |
|----------------|----------|---------|--------------------------------------------------------------|
| `storage_pool` | Yes      | -       | The storage pool new LUNs are created in.                    |
| `scope`        | No       | `0`     | The login scope: `0` for a local user, `1` for an LDAP user. |

### Infinidat InfiniBox (`infinidat-infinibox`)

The plug-in uses the InfiniBox REST API (InfiniBox 7). Volumes are created in the configured pool, thin by default, and mapped to host objects that carry the hosts' iSCSI names or FC WWPNs. Operations the array asks to confirm are confirmed by the plug-in.

| Option     | Required | Default | Meaning                                                  |
|------------|----------|---------|----------------------------------------------------------|
| `pool`     | Yes      | -       | The pool new volumes are created in.                     |
| `provtype` | No       | `THIN`  | The provisioning type of new volumes: `THIN` or `THICK`. |


### Amazon EBS (`aws-ebs`)

The plug-in creates EBS `io2` or `io1` volumes with Multi-Attach enabled and attaches them to the EC2 instances of
the storage nodes. All instances are Nitro instances in the one availability zone of the cluster, and a volume can be
attached to at most 16 instances. A host is identified by its EC2 instance id, which the storage node agent reads from
the instance metadata service. Every volume is tagged with the cluster's id, and volumes without that tag are never
touched. A failed node is fenced with an NVMe persistent reservation, followed by a forced detach of its volume.

The login is optional: without it, the instance role of the control plane is used. The login fields are
`aws_access_key_id`, `aws_secret_access_key`, and `aws_session_token`. The endpoint is left empty, or names a VPC
endpoint of EC2.

| Option                | Required | Default   | Meaning                                                         |
|-----------------------|----------|-----------|-----------------------------------------------------------------|
| `az`                  | Yes      | -         | The availability zone of the cluster, for example, `us-east-1a` |
| `region`              | No       | From `az` | The region, when it differs from the availability zone's        |
| `volume_type`         | No       | `io2`     | `io2` or `io1`                                                  |
| `iops`                | No       | `3000`    | The provisioned IOPS of every volume                            |
| `encrypted`           | No       | `true`    | Encrypts the volumes with EBS encryption                        |
| `kms_key_id`          | No       | -         | The AWS KMS key of the EBS encryption                           |
| `poll_interval`       | No       | `2`       | Seconds between status checks of a volume                       |
| `fence_poll_interval` | No       | `0.2`     | Seconds between status checks of a forced detach                |
| `timeout`             | No       | `300`     | Seconds to wait for a volume operation                          |

## Validation Status

The array plug-ins are experimental. The API usage of each plug-in is checked against the vendor's own client
libraries, Kubernetes CSI drivers, and Ansible collections, and is covered by tests against a simulation of each
array's API. Validation against the arrays themselves is in progress, and a plug-in is promoted from experimental once
it has passed it.
