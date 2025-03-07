| Service                     | Direction | Source / Target Network | Port      | Protocol(s) |
|-----------------------------|-----------|-------------------------|-----------|-------------|
| ICMP                        | ingress   | control                 | -         | ICMP        |
| Cluster API                 | ingress   | storage, control, admin | 80        | TCP         |
| SSH                         | ingress   | storage, control, admin | 22        | TCP         |
| Graylog                     | ingress   | storage, control        | 12201     | TCP / UDP   |
| Graylog                     | ingress   | storage, control        | 12202     | TCP         |
| Graylog                     | ingress   | storage, control        | 13201     | TCP         |
| Graylog                     | ingress   | storage, control        | 13202     | TCP         |
| Docker Daemon Remote Access | ingress   | storage, control        | 2375      | TCP         |
| Docker Swarm Remote Access  | ingress   | storage, control        | 2377      | TCP         |
| Docker Overlay Network      | ingress   | storage, control        | 4789      | UDP         |
| Docker Network Discovery    | ingress   | storage, control        | 7946      | TCP / UDP   |
| FoundationDB                | ingress   | storage, control        | 4500      | TCP         |
| Prometheus                  | ingress   | storage, control        | 9100      | TCP         |
|                             |           |                         |           |             |
| Cluster Control             | egress    | storage, control        | 8080-8890 | TCP         |
| spdk-http-proxy             | egress    | storage, control        | 5000      | TCP         |
| Docker Daemon Remote Access | egress    | storage, control        | 2375      | TCP         |
| Docker Swarm Remote Access  | egress    | storage, control        | 2377      | TCP         |
| Docker Overlay Network      | egress    | storage, control        | 4789      | UDP         |
| Docker Network Discovery    | egress    | storage, control        | 7946      | TCP / UDP   |
