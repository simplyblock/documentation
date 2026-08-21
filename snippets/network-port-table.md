| Service                         | Direction       | Hosts            | Network | Port(s)                         | Protocol(s)             |
|---------------------------------|-----------------|------------------|---------|---------------------------------|-------------------------|
| ICMP                            | egress          | control          | Control | -                               | ICMP                    |
| storage-node-api                | egress          | storage          | Control | 5000                            | TCP                     |
| NVMf (client-target)            | egress          | client           | Storage | 4420-4499                       | TCP, UDP <sup>(1)</sup> |
| FoundationDB                    | ingress, egress | control          | Control | 4500                            | TCP                     |
| control-plane-API               | ingress         | control          | Control | 80                              | TCP                     |
| storage-node-RPC                | ingress, egress | storage, control | Control | 8080-9044                       | TCP                     |
| Monitoring Stack <sup>(2)</sup> | ingress, egress | control          | Control | 12202, 13301, 13302, 9200, 9090 | TCP                     |

<span style="font-size: 0.8em;">
<sup>1</sup> The NVMf port range carries both transports. NVMe-oF/TCP uses it over TCP, NVMe-oF/RDMA
over UDP. Only the protocol of the transport(s) in use has to be opened.<br>
<sup>2</sup> The monitoring stack is optional. Its ports only have to be opened where it is deployed.
</span>
