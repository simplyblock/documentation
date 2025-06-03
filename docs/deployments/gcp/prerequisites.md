---
title: "Prerequisites"
weight: 30000
---

When installing simplyblock control planes and storage planes, a number of prerequisites are important to understand.

Simplyblock uses Docker Swarm for the control plane cluster. In case of a bare metal or virtualized installation, it
will also use Docker Swarm for the storage plane. Hence, Docker has to be installed.

Furthermore, simplyblock requires installing the `{{ cliname }}` command line tool. This tool is written in
Python. Therefore, Python (3.5 or later) has to be installed. Likewise, pip, the Python package manager, has to be
installed with version 20 or later.

To install `{{ cliname }}` run:

```bash
sudo pip install {{ cliname }} --upgrade
```

## Node Sizing

Simplyblock has certain requirements in terms of CPU, RAM, and storage. See the specific
[Node Sizing](../deployment-planning/node-sizing.md) documentation to learn more.

### Node Instance Type

Simplyblock recommends pre-tested and verified instance types. Those instance types are:

- i3en.6xlarge
- i4i.8xlarge

## Network Configuration

Simplyblock requires a number of network ports to be available from different networks. The configuration of the
required network ports are provided in the [installation documentation](install-simplyblock.md).

Additionally, IPv6 must be disabled on all nodes running simplyblock.

```bash
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
sudo sysctl -w net.ipv6.conf.default.disable_ipv6=1
```

### Google Compute Engine Networks
Specifically for GCP, simplyblock strongly advises using individual networks for the control plane and storage plane.

For access to the Cluster Management API, simplyblock recommends using an GCP load balancer as a front instead of
making the API available directly.

### Network Ports for Control Plane

{% include 'control-plane-network-port-table.md' %}

### Network Ports for Storage Plane

{% include 'storage-plane-network-port-table.md' %}

## Storage Configuration

Simplyblock has certain requirements in terms of storage. While the most important facts are provided in the
installation section, here are things to consider.

### Root Volume

The volume mounted as the root directory has to provide at least **35GiB** of free capacity. More free space is
recommended, especially for control plane nodes, which collect logs and the cluster state.

### NVMe Devices

NVMe devices used for simplyblock should **ALWAYS** be formatted using the `nvme` command line tool before adding them
to a simplyblock storage node. Failing to do so can negatively impact storage performance and lead to data corruption
or even data loss in case of a sudden power outage.

The `lsblk` is the best way to find all NVMe devices attached to a system.

```plain title="Example output of lsblk"
[demo@demo ~]# sudo lsblk
NAME        MAJ:MIN RM  SIZE RO TYPE MOUNTPOINTS
sda           8:0    0   30G  0 disk
├─sda1        8:1    0    1G  0 part /boot
└─sda2        8:2    0   29G  0 part
  ├─rl-root 253:0    0   26G  0 lvm  /
  └─rl-swap 253:1    0    3G  0 lvm  [SWAP]
nvme3n1     259:0    0  6.5G  0 disk
nvme2n1     259:1    0   70G  0 disk
nvme1n1     259:2    0   70G  0 disk
nvme0n1     259:3    0   70G  0 disk
```

In the example, we see four NVMe devices. Three devices of 70GiB and one device with 6.5GiB storage capacity.

To find the correct LBA format (_lbaf_) for each of the devices, the `nvme` CLI can be used.

```bash title="Show NVMe namespace information"
sudo nvme id-ns /dev/nvmeXnY
```

The output depends on the NVMe device itself, but looks something like this:

```plain title="Example output of NVMe namespace information"
[demo@demo ~]# sudo nvme id-ns /dev/nvme0n1
NVME Identify Namespace 1:
...
lbaf  0 : ms:0   lbads:9  rp:0
lbaf  1 : ms:8   lbads:9  rp:0
lbaf  2 : ms:16  lbads:9  rp:0
lbaf  3 : ms:64  lbads:9  rp:0
lbaf  4 : ms:0   lbads:12 rp:0 (in use)
lbaf  5 : ms:8   lbads:12 rp:0
lbaf  6 : ms:16  lbads:12 rp:0
lbaf  7 : ms:64  lbads:12 rp:0
```

From this output, the required _lbaf_ configuration can be found. The necessary configuration has to have the following
values:

| Property | Value |
|----------|-------|
| ms       | 0     |
| lbads    | 12    |
| rp       | 0     |

In the example, the required LBA format is 4. If a NVMe device doesn't have that combination, any other _lbads=12_
combination will work. However, simplyblock recommends asking for the best available combination.

In our example, the device is already formatted with the correct _lbaf_ (see the "in use"). It is, however,
recommended to always format the device before use.

To format the drive, the `nvme` CLI is used again.

```bash title="Formatting the NVMe device"
sudo nvme format --lbaf=<lbaf> --ses=0 /dev/nvmeXnY
```

The command output should give a successful response when executed similarly to the example below.

```plain title="Example output of NVMe device formatting"
[demo@demo ~]# sudo nvme format --lbaf=4 --ses=0 /dev/nvme0n1
You are about to format nvme0n1, namespace 0x1.
WARNING: Format may irrevocably delete this device's data.
You have 10 seconds to press Ctrl-C to cancel this operation.

Use the force [--force] option to suppress this warning.
Sending format operation ...
Success formatting namespace:1
```
