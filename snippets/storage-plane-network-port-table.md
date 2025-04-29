| Service                     | Direction | Source / Target Network | Port(s)   | Protocol(s) |
|-----------------------------|-----------|-------------------------|-----------|-------------|
| ICMP                        | ingress   | control                 | -         | ICMP        |
| bdts                        | ingress   | storage                 | 4420      | TCP         |
| Cluster Control             | ingress   | control                 | 5000      | TCP         |
| spdk-http-proxy             | ingress   | storage, control        | 8080-8890 | TCP         |
| hub-lvol                    | ingress   | storage, control        | 9060-9099 | TCP         |
| lvol-proxy                  | ingress   | storage, control        | 9100-9900 | TCP         |
| SSH                         | ingress   | storage, control, admin | 22        | TCP         |
| Docker Daemon Remote Access | ingress   | storage, control        | 2375      | TCP         |
| Docker Swarm Remote Access  | ingress   | storage, control        | 2377      | TCP         |
| Docker Overlay Network      | ingress   | storage, control        | 4789      | UDP         |
| Docker Network Discovery    | ingress   | storage, control        | 7946      | TCP / UDP   |
|                             |           |                         |           |             |
| FoundationDB                | egress    | storage                 | 4500      | TCP         |
| Docker Daemon Remote Access | egress    | storage, control        | 2375      | TCP         |
| Docker Swarm Remote Access  | egress    | storage, control        | 2377      | TCP         |
| Docker Overlay Network      | egress    | storage, control        | 4789      | UDP         |
| Docker Network Discovery    | egress    | storage, control        | 7946      | TCP / UDP   |
| Graylog                     | egress    | control                 | 12202     | TCP         |
