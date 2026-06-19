| Service              | Direction       | Hosts            | Network | Port(s)                          | Protocol(s) |
|----------------------|-----------------|------------------|---------|----------------------------------|-------------|
| ICMP                 | ingress         | control          | Control | -                                | ICMP        |
| spdk-http-proxy      | ingress, egress | storage, control | Control | 5000                             | TCP         |
| nvmf (client-target) | egress          | client           | Storage | 4420-4499                        | TCP         |
| nvmf (internal)      | ingress, egress | storage          | Storage | 4420-4499                        | TCP         |
| FoundationDB         | ingress         | control          | Control | 4500                             | TCP         |
| Control plane API    | egress          | control          | Control | 80                               | TCP         |
| Control plane RPC    | ingress, egress | storage, control | Control | 8080-9044                        | TCP         |
| Monitoring Stack     | ingress, egress | control          | Control | 12202, 13301, 13302, 9200, 9090  | TCP         |
