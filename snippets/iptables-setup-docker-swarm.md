Simplyblock requires a number of TCP and UDP ports to be reachable from the control and the storage network. The
following table lists every port required for operation as a storage node.

{% include 'network-port-table-sn.md' %}

The following script opens those ports with `iptables`. No source address is enforced by it. Where a tighter rule
set is required, the sources given in the Hosts and the Network column are applied on top.

```bash title="Opening the storage node ports with iptables"
#!/usr/bin/env bash

iptables -A INPUT -p icmp -j ACCEPT
iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
iptables -A INPUT -p tcp --dport 4420:4499 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 4420:4499 -j ACCEPT
iptables -A INPUT -p tcp --dport 8080:9044 -j ACCEPT
```
