Simplyblock is built upon the NVMe over Fabrics standard and uses NVMe over TCP (NVMe/TCP) by default.

While the driver is part of the Linux kernel with kernel versions 5.x and later, it is not enabled by default. Hence,
when using simplyblock, the driver needs to be loaded.

```bash title="Loading the NVMe/TCP driver"
modprobe nvme-tcp
```

When loading the NVMe/TCP driver, the NVMe over Fabrics driver automatically get loaded to, as the former depends on its
provided foundations.

It is possible to check for successful loading of both drivers with the following command:

```bash title="Checking the drivers being loaded"
lsmod | grep 'nvme_'
```

The response should list the drivers as _nvme_tcp_ and _nvme_fabrics_ as seen in the following example:

```plain title="Example output of the driver listing"
[demo@demo ~]# lsmod | grep 'nvme_'
nvme_tcp               57344  0
nvme_keyring           16384  1 nvme_tcp
nvme_fabrics           45056  1 nvme_tcp
nvme_core             237568  3 nvme_tcp,nvme,nvme_fabrics
nvme_auth              28672  1 nvme_core
t10_pi                 20480  2 sd_mod,nvme_core
```

To make the driver loading persistent and survive system reboots, it has to be configured to be loaded at system startup
time. This can be achieved by either adding it to _/etc/modules_ (Debian / Ubuntu) or creating a config file under
_/etc/modules-load.d/_ (Red Hat / Alma / Rocky).

=== "Red Hat / Alma / Rocky"

    ```bash
    echo "nvme-tcp" | sudo tee -a /etc/modules-load.d/nvme-tcp.conf
    ```

=== "Debian / Ubuntu"

    ```bash
    echo "nvme-tcp" | sudo tee -a /etc/modules
    ```

After rebooting the system, the driver should be loaded automatically. It can be checked again via the above provided
`lsmod` command.
