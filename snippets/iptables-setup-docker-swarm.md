Simplyblock requires a number of TCP and UDP ports to be opened from certain networks. Following is a list of all
ports (TCP and UDP) required for operation as a storage node.

!!! note
    The NVMf port range is used twice. It is TCP for NVMe-oF/TCP and UDP for NVMe-oF/RDMA.

{% include 'network-port-table-sn.md' %}

The following script opens those ports with `iptables`.

```bash title="Configuration script for iptables"
#!/usr/bin/env bash

iptables -A INPUT -p icmp -j ACCEPT
iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
iptables -A INPUT -p tcp --dport 4420:4499 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 4420:4499 -j ACCEPT
iptables -A INPUT -p tcp --dport 8080:9044 -j ACCEPT
```
