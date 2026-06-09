Simplyblock generally requires NVMe devices with support for 4K block size. This is the case for almost all Enterprise-grade NVMe devices, 
nevertheless it is recommended to ensure support before deployment. 

Alternatively, devices supporting only 512 bytes blocks can be used, if they provide 4K write atomiticy or 4K torn write protection. 
The only devices with 512 bytes block size, which are known to support 4K torn write protection, are the NVMe devices used by AWS. 

Devices must not contain active mount points under Linux. Simplyblock fails to claim devices with active mount points. 
Partitions must be removed from devices. Simplyblock can only claim unpartitioned devices. Simplyblock removes partitions during
the optional formatting process in the deployment.

!!! warning
    Simplyblock optionally performs a low-level format of selected devices during the deployment process. 
    This erases all data on the devices without recovery option!
    
Use `lsblk` to identify available NVMe devices without active mount points.

```plain title="Example output of lsblk"
[demo@demo-3 ~]# sudo lsblk
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

In the example, we see four NVMe devices. Three devices of 70GiB and one device with 6.5GiB storage capacity
with no active mount points and no partitions.

To find the correct LBA format (_lbaf_) for each of the devices, the `nvme` CLI can be used.

```bash title="Show NVMe namespace information"
sudo nvme id-ns /dev/nvmeXnY
```

The output depends on the NVMe device itself, but looks something like this:

```plain title="Example output of NVMe namespace information"
[demo@demo-3 ~]# sudo nvme id-ns /dev/nvme0n1
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

From this output, the required _lbaf_ configuration can be found. lbads must be 12. Simplyblock will choose lbads: 12 with ms>0 if available, as 
this significantly improves performance, if DIF (data integrity checking) is used. If only ms:0 is available, it will be used as a fallback option.




!!! warning
    This operation needs to be repeated for each NVMe device that will be handled by simplyblock.
