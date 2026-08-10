| Service              | Direction       | Hosts            | Network | Port(s)                         | Protocol(s) |
|----------------------|-----------------|------------------|---------|---------------------------------|-------------|
| ICMP                 | egress          | control          | Control | -                               | ICMP        |
| storage-node-api     | egress          | storage          | Control | 5000                            | TCP         |
| NVMf (client-target) | egress          | client           | Storage | 4420-4499                       | TCP         |
| FoundationDB         | ingress, egress | control          | Control | 4500                            | TCP         |
| control-plane-API    | ingress         | control          | Control | 80                              | TCP         |
| storage-node-RPC     | ingress, egress | storage, control | Control | 8080-9044                       | TCP         |
| Monitoring Stack     | ingress, egress | control          | Control | 12202, 13301, 13302, 9200, 9090 | TCP         |
