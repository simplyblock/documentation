---
title: "Deploy with Linux Block Devices"
description: "Deploying a simplyblock cluster on Linux block devices: cluster creation in lblk mode, device selection by name or serial, and node addition."
weight: 35000
---

{{ experimental }}

This page describes deploying a storage plane on Linux block devices instead of NVMe PCIe devices. It
follows the standard [storage plane installation](install-sp.md) flow; only the differing steps are
described here. Background on the device mode, the eligibility rules, and the device identity is
found under [Linux Block Devices (lblk)](../../architecture/concepts/linux-block-devices.md).

!!! warning
    Linux block device support is experimental. It is intended for evaluation, for test environments,
    and for deployments where NVMe devices are unavailable, such as cloud instances with attached
    volumes only. For production-grade performance, local NVMe devices are recommended.

## Cluster Creation

The device mode is a cluster-global, deploy-time choice made when the cluster is created on the
control plane:

```bash title="Creating a cluster in lblk device mode"
sudo {{ cliname }} cluster create --device-mode lblk
```

`--device-mode` accepts `nvme` (the default) and `lblk`. It cannot be changed after creation, and all
storage nodes of the cluster follow it.

!!! important
    All control plane and storage node services must run a software version that supports the `lblk`
    device mode before a cluster is created with it.

## Storage Node Configuration

On each storage node, devices are selected at `storage-node configure` time with the `--lblk` flag
and an optional device selector:

```bash title="Configuring a storage node with all eligible block devices"
sudo {{ cliname }} storage-node configure --lblk --max-lvol <MAX_LOGICAL_VOLUMES>
```

Without a selector, every eligible disk on the host is used. Eligible means a whole, unmounted,
unheld, and unpartitioned disk that is not the root disk (see the
[eligibility rules](../../architecture/concepts/linux-block-devices.md#device-eligibility)).

Devices can be selected explicitly by name or by serial number. The three selectors are mutually
exclusive:

```bash title="Selecting block devices by name"
sudo {{ cliname }} storage-node configure --lblk --blk-names sdb,sdc --max-lvol 50
```

```bash title="Selecting all eligible block devices except some"
sudo {{ cliname }} storage-node configure --lblk --blk-names-exclude sda --max-lvol 50
```

```bash title="Selecting block devices by serial number or WWN"
sudo {{ cliname }} storage-node configure --lblk --blk-serials S3EVNX0M602707,S3EVNX0M602708 --max-lvol 50
```

A requested device that is busy — mounted, held, or otherwise ineligible — is an error: the
configuration fails rather than silently skipping the device.

The resulting configuration file (`/etc/simplyblock/sn_config_file`) stores the selected devices with
their name, serial, stable by-id path, size, and NUMA assignment. As in NVMe mode, the file can be
reviewed and manually edited before deployment, for example to remove a device from the selection.

### Partitioned Devices

A device carrying a partition table is not eligible by default. To reuse such a device, it is marked
eligible with `--force` at configuration time:

```bash title="Including a partitioned block device in the selection"
sudo {{ cliname }} storage-node configure --lblk --blk-names sdb --force --max-lvol 50
```

The actual wipe happens later, at node addition, and must be requested there explicitly with
`--force-format`. Until then, no data is touched.

## Storage Node Deployment and Addition

Node deployment is unchanged:

```bash title="Deploying the storage node"
sudo {{ cliname }} storage-node deploy --ifname eth0
```

Adding the node to the cluster from a control plane node is unchanged as well, with one additional
flag: if partitioned devices were force-included at configuration time, `--force-format` instructs
the node addition to wipe partition tables and filesystem signatures (`wipefs`) from those devices:

```bash title="Adding the storage node while wiping partitioned devices"
sudo {{ cliname }} storage-node add-node --force-format <CLUSTER_ID> <NODE_IP>:5000 eth0
```

!!! danger
    `--force-format` irreversibly destroys any data on the affected devices. The device selection in
    the node configuration has to be verified before the node is added.

During node addition, each selected device is wrapped in an SPDK AIO bdev. No kernel driver unbinding
takes place — the devices stay visible to the host OS but must not be used by anything else. The
smallest device becomes the journal device, as in NVMe mode with journal-on-device deployments.

Everything after node addition — cluster activation, pool creation, volume provisioning, and client
connection — is identical to an NVMe-mode cluster.

## Verification

After activation, the devices are listed like NVMe devices, showing the device path instead of a PCIe
address:

```bash title="Listing the storage devices of a node"
sudo {{ cliname }} storage-node list-devices <NODE_ID>
```

On the host, `lsblk` continues to show the devices, since they remain kernel-owned, and the SPDK
process exposes one `aio_<serial>` base bdev per device.
