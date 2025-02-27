---
title: "Huge Pages Calculator"
weight: 20400
---

Calculating the correct minimum size of huge pages reserved for simplyblock isn't an easy task. Therefore, simplyblock
provides the following calculator.

The calculator provides the number of 2 MiB sized huge pages.

--8<-- "huge-pages-calculator.md"

The resulting number can be used for temporary allocation of huge pages or to persist and pre-allocate them during
system boot-up.

```bash title="Temporary allocation"
sudo sysctl vm.nr_hugepages=4096
```

```plain title="Persisted allocation"
GRUB_CMDLINE_LINUX="${GRUB_CMDLINE_LINUX} default_hugepagesz=2MB hugepagesz=2MB hugepages=4096"
```

```bash title="Persist the configuration change"
sudo grub2-mkconfig -o /boot/efi/EFI/redhat/grub.cfg
```
