| Service              | Direction       | Hosts            | Network | Port(s)   | Protocol(s)             |
|----------------------|-----------------|------------------|---------|-----------|-------------------------|
| ICMP                 | ingress         | control          | Control | -         | ICMP                    |
| storage-node-api     | ingress         | control          | Control | 5000      | TCP                     |
| NVMf (client-target) | ingress         | client           | Storage | 4420-4499 | TCP, UDP <sup>(1)</sup> |
| NVMf (internal)      | ingress, egress | storage          | Storage | 4420-4499 | TCP, UDP <sup>(1)</sup> |
| storage-node-RPC     | ingress         | storage, control | Control | 8080-9044 | TCP                     |

<span style="font-size: 0.8em;">
<sup>1</sup> The NVMf port range carries both transports. NVMe-oF/TCP uses it over TCP, NVMe-oF/RDMA
over UDP. Only the protocol of the transport in use has to be opened.
</span>
