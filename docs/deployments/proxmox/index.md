---
title: Proxmox Integration
weight: 20350
---

```bash title="Install the Simplyblock Proxmox Integration"
apt install ./simplyblock-proxmox.deb
```

```bash title="Restart the Proxmox UI Daemon"
systemctl restart pvedaemon 
```

```bash title="Enable Simplyblock as a Storage Provider"
pvesm add simplyblock <name> \
    --entrypoint=<control_plane_addr> \
    --cluster=<cluster_id> \
    --secret=<cluster_secret> \
    --pool=<storage_pool_name>
```
