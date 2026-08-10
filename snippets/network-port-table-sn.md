| Service              | Direction       | Hosts            | Network | Port(s)                         | Protocol(s) |
|----------------------|-----------------|------------------|---------|---------------------------------|-------------|
| ICMP                 | ingress         | control          | Control | -                               | ICMP        |
| storage-node-api     | ingress         | control          | Control | 5000                            | TCP         |
| NVMf (client-target) | ingress         | client           | Storage | 4420-4499                       | TCP         |
| NVMf (internal)      | ingress, egress | storage          | Storage | 4420-4499                       | TCP         |
| storage-node-RPC     | ingress         | storage, control | Control | 8080-9044                       | TCP         |
