---
title: "Reconnecting Logical Volume"
weight: 20080
---

After outages of storage nodes, primary and secondary NVMe over Fabrics connections may need to be re-established. With
integrations such as simplyblock's Kubernetes CSI driver and the Proxmox integration, this is automatically handled.

With plain Linux clients, the connections have to be reconnected manually. This is especially important when a storage
node is unavailable for more than 60 seconds (by default).

## Reconnect a Missing NVMe Controller

To reconnect the NVMe controllers for the logical volume, the normal _nvme connect_ commands are executed again. This
will immediately reconnect missing controllers and connection paths.

```bash title="Retrieve connection strings"
{cliname} volume connect <VOLUME_ID>
```

```plain title="Example output for connection string retrieval"
[demo@demo ~]# {cliname} volume connect 82e587c5-4a94-42a1-86e5-a5b8a6a75fc4
sudo nvme connect --reconnect-delay=2 --ctrl-loss-tmo=60 --nr-io-queues=6 --keep-alive-tmo=5 --transport=tcp --traddr=192.168.10.112 --trsvcid=9100 --nqn=nqn.2023-02.io.simplyblock:0f2c4cb0-a71c-4830-bcff-11112f0ee51a:lvol:82e587c5-4a94-42a1-86e5-a5b8a6a75fc4
sudo nvme connect --reconnect-delay=2 --ctrl-loss-tmo=60 --nr-io-queues=6 --keep-alive-tmo=5 --transport=tcp --traddr=192.168.10.113 --trsvcid=9100 --nqn=nqn.2023-02.io.simplyblock:0f2c4cb0-a71c-4830-bcff-11112f0ee51a:lvol:82e587c5-4a94-42a1-86e5-a5b8a6a75fc4
```

## Increase Loss Timeout

Alternatively, depending on the environment, it is possible to increase the timeout after which Linux assumes the
NVMe controller to be lost and stops with reconnection attempts.

To increase the timeout, the parameter _--ctrl-loss-tmo_ can be increased. The value is the number of seconds until
the Linux kernel stops the reconnection attempt and removes the controller from the list of valid multipath routes.
