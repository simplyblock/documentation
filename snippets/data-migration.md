
When migrating existing data to simplyblock, the process can be performed at the block level or the file system
level, depending on the source system and migration requirements. Because Simplyblock provides logical Volumes (LVs)
as virtual block devices, data can be migrated using standard block device cloning tools such as `dd`, as well
as file-based tools like `rsync` after the block device has been formatted.

Therefore, sata migration to simplyblock is a straightforward process using common block-level and file-level tools.
For full disk cloning, `dd` and similar utilities are effective. For selective file migrations, `rsync` provides
flexibility and reliability. Proper planning and validation of available storage capacity are essential to ensure
successful and complete data transfers.

## Block-Level Migration Using `dd`

A block-level copy duplicates the entire content of a source block device, including partition tables, file systems, and
data. This method is ideal when migrating entire disks or volumes.

```sh
dd if=/dev/source-device of=/dev/simplyblock-device bs=4M status=progress
```

- `if=` specifies the input (source) device.
- `of=` specifies the output (Simplyblock Logical Volume) device.
- `bs=4M` sets the block size for efficiency.
- `status=progress` provides real-time progress updates.

!!! info
    Ensure that the simplyblock logical volume is at least as large as the source device to prevent data loss.

## Alternative Block-Level Cloning Tools

Other block-level tools such as `Clonezilla`, `partclone`, or `dcfldd` may also be used for disk duplication, depending
on the specific environment and desired features like compression or network transfer.

## File-Level Migration Using `rsync`

For scenarios where only file contents need to be migrated (for example, after creating a new file system on a
simplyblock logical volume), `rsync` is a reliable tool.

1. First, format the Simplyblock Logical Volume:
   ```bash
   mkfs.ext4 /dev/simplyblock-device
   ```

2. Mount the Logical Volume:
   ```bash
   mount /dev/simplyblock-device /mnt/simplyblock
   ```

3. Use `rsync` to copy files from the source directory:
   ```bash
   rsync -avh --progress /source/data/ /mnt/simplyblock/
   ```

    - `-a` preserves permissions, timestamps, and symbolic links.
    - `-v` provides verbose output.
    - `-h` makes output human-readable.
    - `--progress` shows transfer progress.

## Minimal-Downtime Migration Strategy

An alternative, but more complex solution enables minimal downtime. This option utilizes the Linux `dm` (Device Mapper)
subsystem.

Using the Device Mapper, the current and new block devices will be moved into a RAID-1 and synchronized (re-silvered)
in the background.  This solution requires two minimal downtimes to create and remount the devices.

!!! warning
    This method is quite involved, requires a lot of steps and can lead to data loss in case of wrong commands or
    parameters. It should only be used by advanced users that understand the danger of the commands below.<br/><br/>
    Furthermore, this migration method **MUST NOT** be used for boot devices!

In this walkthrough, we assume the new simplyblock logical volume is already connected to the system.

### Preparation

To successfully execute this data migration, a few values are required. First of all, the two device names of the
currently used and new device need to be collected.

This can be done by executing the command `lsblk` to list all attached block devices.

```bash
lsblk
```

In this example, _sda_ is the boot device which hosts the operating system, while _sdb_ is the currently used block
device and _nvme0n1_ is the newly attached simplyblock logical volume. The latter two should be noted down.

!!! danger
    It is important to understand the difference between the currently used and the new device. Using them in the wrong
    order in the following steps will cause any or all data to be lost!

```plain
[root@demo ~]# lsblk
NAME                      MAJ:MIN RM  SIZE RO TYPE  MOUNTPOINTS
sda                         8:0    0   25G  0 disk
├─sda1                      8:1    0    1G  0 part  /boot/efi
├─sda2                      8:2    0    2G  0 part  /boot
└─sda3                      8:3    0 21.9G  0 part
  └─ubuntu--vg-ubuntu--lv 252:0    0   11G  0 lvm   /
sdb                         8:16   0   25G  0 disk
└─sdb1                      8:17   0   25G  0 part  /data/pg
sr0                        11:0    1 57.4M  0 rom
nvme0n1                   259:0    0   25G  0 disk
```

Next up the cluster size of the current device is required. The value must be set on the RAID to-be-created. It needs
to be noted down.

```bash
tune2fs -l /dev/sdb1 | grep -i 'block size'
```

In this example, the block size is 4 KiB (4096 bytes).

```plain
[root@demo ~]# tune2fs -l /dev/sdb1 | grep -i 'block size'
Block size:               4096
```

Last, it is important to ensure that the new target device is at least as large or larger than the current device.
`lsblk` can be used again to get the required numbers.

```bash
lsblk -b
```

In this example, both devices are the same size, _26843545600_ bytes in total disk capacity.

```plain
[root@demo ~]# lsblk -b
NAME                      MAJ:MIN RM        SIZE RO TYPE  MOUNTPOINTS
sda                         8:0    0 26843545600  0 disk
├─sda1                      8:1    0  1127219200  0 part  /boot/efi
├─sda2                      8:2    0  2147483648  0 part  /boot
└─sda3                      8:3    0 23566745600  0 part
  └─ubuntu--vg-ubuntu--lv 252:0    0 11781799936  0 lvm   /
sdb                         8:16   0 26843545600  0 disk
└─sdb1                      8:17   0 26843513344  0 part  /data/pg
sr0                        11:0    1    60225536  0 rom
nvme0n1                   259:0    0 26843545600  0 disk
```

### Device Mapper RAID Setup

!!! danger
    From here on out, mistakes can cause any or all data to be lost!<br/>
    It is strongly recommended to only go further, if ensured that the values above are correct and after a full data
    backup is created. It is also recommended to test the backup before continuing. A failure to do so can cause issues
    in case it cannot be replayed.

Now, it's time to create the temporary RAID for disk synchronization. Anything beyond this point is dangerous.

!!! warning
    Any service accessing the current block device or any of its partitions need to be shutdown and the block device
    and its partitions need to be unmounted. It is required for the device to not be busy.<br/><br/>
    ```bash title="Example of PostgreSQL shutdown and partition unmount"
    service postgresql stop
    umount /data/pg
    ```

```bash
mdadm --build --chunk=<CHUNK_SIZE> --level=1 \
    --raid-devices=2 --bitmap=none \
    <RAID_NAME> <CURRENT_DEVICE_FILE> missing
```

In this example, the RAID is created using the _/dev/sdb_ device file and _4096_ as the chunk size. The newly created
RAID is called _migration_. The RAID-level is 1 (meaning, RAID-1) and it includes 2 devices. The _missing_ at the end
of the command is required to tell the device mapper that the second device of the RAID is missing for now. It will be
added later.

```plain
[root@demo ~]# mdadm --build --chunk=4096 --level=1 --raid-devices=2 --bitmap=none migration /dev/sdb missing
mdadm: array /dev/md/migration built and started.
```

To ensure the that the RAID was created successfully, all device files with _/dev/md*_ can be listed. In this case,
_/dev/md127_ is the actual RAID device, while _/dev/md/migration_ is the device mapper file.

```plain
[root@demo ~]# ls /dev/md*
/dev/md127  /dev/md127p1

/dev/md:
migration  migration1
```

After the RAID device name is confirmed, the new RAID device can be mounted. In this example, the original block device
was partitioned. Hence, the RAID device also has one partition _/dev/md127p1_. This is what needs to be mounted to the
same mount point as the original disk before, _/data/pg_ in this example.

```plain
[root@demo ~]# mount /dev/md127p1 /data/pg/
```

!!! info
    All services that require access to the data can be started again. The RAID itself is still in a degraded state, but
    it provides the same data security as the original device.

Now the second, new device must be added to the RAID setup to start the re-silvering (data synchronization) process.
This is again done using `mdadm` tool.

```bash
mdadm <RAID_DEVICE_MAPPER_FILE> --add <NEW_DEVICE_FILE>
```

In the example, we add _/dev/nvme0n1_ (the simplyblock logical volume) to the RAID named "migration".

```plain
[root@demo ~]# mdadm /dev/md/migration --add /dev/nvme0n1
mdadm: added /dev/nvme0n1
```

After the device was added to the RAID setup, a background process is automatically started to synchronize the newly
added device to the first device in the setup. This process is called re-silvering.

!!! info
    While the devices are synchronized, the read and write performance may be impacted due to the additional I/O
    operations of the synchronization process. However, the process runs on a very low priority and shouldn't impact
    the live operation too extensively.<br/><br/>
    **For AWS users:** if the migration uses an Amazon EBS volume as the source, ensure enough IOPS to cover live
    operation and migration.

The synchronization process status can be monitored using one of two commands:

```bash
mdadm -D <RAID_DEVICE_FILE>
cat /proc/mdstat
```

```plain
[root@demo ~]#mdadm -D /dev/md127
/dev/md127:
           Version :
     Creation Time : Sat Mar 15 17:24:17 2025
        Raid Level : raid1
        Array Size : 26214400 (25.00 GiB 26.84 GB)
     Used Dev Size : 26214400 (25.00 GiB 26.84 GB)
      Raid Devices : 2
     Total Devices : 2

             State : clean, degraded, recovering
    Active Devices : 1
   Working Devices : 2
    Failed Devices : 0
     Spare Devices : 1

Consistency Policy : resync

    Rebuild Status : 98% complete

    Number   Major   Minor   RaidDevice State
       0       8       16        0      active sync   /dev/sdb
       2     259        0        1      spare rebuilding   /dev/nvme0n1
```

```plain
[root@localhost ~]# cat /proc/mdstat 
Personalities : [raid1] 
md0 : active raid1 sdb[1] nvme0n1[0]
      10484664 blocks super 1.2 [2/2] [UU]
      [========>............]  resync = 42.3% (4440832/10484664) finish=0.4min speed=201856K/sec
      
unused devices: <none>
```

### After the Synchronization is done

Eventually, the synchronization finishes. At this point, the two devices (original and new) are kept in sync by the
device mapper system.

```plain
[root@localhost ~]# mdadm -D /dev/md127
/dev/md127:
           Version :
     Creation Time : Sat Mar 15 17:24:17 2025
        Raid Level : raid1
        Array Size : 26214400 (25.00 GiB 26.84 GB)
     Used Dev Size : 26214400 (25.00 GiB 26.84 GB)
      Raid Devices : 2
     Total Devices : 2

             State : clean
    Active Devices : 2
   Working Devices : 2
    Failed Devices : 0
     Spare Devices : 0

Consistency Policy : resync

    Number   Major   Minor   RaidDevice State
       0       8       16        0      active sync   /dev/sdb
       2     259        0        1      active sync   /dev/nvme0n1
```

To fully switch to the new simplyblock logical volume, a second minimal downtime is required.

The RAID device needs to unmounted and the device mapper stopped.

```bash
umount <MOUNT_POINT>
mdadm --stop <DEVICE_MAPPER_FILE>
```

In this example _/data/pg_ and _/dev/md/migration_ are used.

```plain
[root@localhost ~]# umount /data/pg/
[root@localhost ~]# mdadm --stop /dev/md/migration
mdadm: stopped /dev/md/migration
```

Now, the system should be restarted. If a system reboot takes too long and is out of the scope of the available
maintenance window, a re-read of the partition tables can be forced.

```bash
blockdev --rereadpt <NEW_DEVICE_FILE>
```

After re-reading the partition table of a device, the partition should be recognized and visible.

```plain
[root@localhost ~]# blockdev --rereadpt /dev/nvme0n1
[root@localhost ~]# ls /dev/nvme0n1p1
/dev/nvme0n1p1
```

As a last step, the partition must be mounted to the same mount point as the RAID device before. If the mount is
successful, the services can be started again.

```plain
[root@localhost ~]# mount /dev/nvme0n1p1 /data/pg/
[root@localhost ~]# service postgresql start
```

