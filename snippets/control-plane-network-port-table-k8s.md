| Service                     | Direction | Source / Target Network | Port      | Protocol(s) |
|-----------------------------|-----------|-------------------------|-----------|-------------|
| ICMP                        | ingress   | control                 | -         | ICMP        |
| Cluster API                 | ingress   | storage, control, admin | 80        | TCP         |
| FoundationDB                | ingress   | storage, control        | 4500      | TCP         |                                   |           |             |
| Cluster Control             | egress    | storage, control        | 8080-8890 | TCP         |
| spdk-http-proxy             | egress    | storage, control        | 5000      | TCP         |
| spdk-firewall-proxy         | egress    | storage, control        | 5001      | TCP         |
