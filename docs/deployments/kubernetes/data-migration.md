---
title: "Data Migration"
weight: 30300
---

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
