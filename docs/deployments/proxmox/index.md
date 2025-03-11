---
title: Proxmox Integration
weight: 20350
---

Simplyblock storage integrates easily with Proxmox installations.
After being deployed, VM and Container images can be deployed to Simplyblock logical volumes inherating all performance and reliability characteristics.
The volumes transparently managed in the background and provided on-demand on the hypervisor.

Note that the Proxmox integration is experimental at this point.
To get started, simply install the Proxmox integration package:

```bash
apt install ./simplyblock-proxmox.deb
```

Afterwards, you can add a Simplyblock-based storage provider:

```bash
pvesm add simplyblock <name> \
    --entrypoint=<control_plane_addr> \
    --cluster=<cluster_id> \
    --secret=<cluster_secret> \
    --pool=<storage_pool_name>
```

Done!
The hypervisor is now configured and can use the Simplyblock cluster as a storage backend.
