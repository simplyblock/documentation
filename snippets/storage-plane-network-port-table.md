| Service                     | Direction | Source / Target Network | Port(s)   | Protocol(s) |
|-----------------------------|-----------|-------------------------|-----------|-------------|
| ICMP                        | ingress   | control                 | -         | ICMP        |
| Storage node API            | ingress   | storage                 | 5000      | TCP         |
| spdk-firewall-proxy         | ingress   | storage                 | 5001      | TCP         |
| spdk-http-proxy             | ingress   | storage, control        | 8080-8180 | TCP         |
| hublvol-nvmf-subsys-port    | ingress   | storage, control        | 9030-9059 | TCP         |
| internal-nvmf-subsys-port   | ingress   | storage, control        | 9060-9099 | TCP         |
| lvol-nvmf-subsys-port       | ingress   | storage, control        | 9100-9200 | TCP         |
| SSH                         | ingress   | storage, control, admin | 22        | TCP         |
| Docker Daemon Remote Access | ingress   | storage, control        | 2375      | TCP         |
| Docker Swarm Remote Access  | ingress   | storage, control        | 2377      | TCP         |
| Docker Overlay Network      | ingress   | storage, control        | 4789      | UDP         |
| Docker Network Discovery    | ingress   | storage, control        | 7946      | TCP / UDP   |
| Greylog                     | ingress   | control                 | 12202     | TCP         |
|                             |           |                         |           |             |
| FoundationDB                | egress    | storage                 | 4500      | TCP         |
| Docker Daemon Remote Access | egress    | storage, control        | 2375      | TCP         |
| Docker Swarm Remote Access  | egress    | storage, control        | 2377      | TCP         |
| Docker Overlay Network      | egress    | storage, control        | 4789      | UDP         |
| Docker Network Discovery    | egress    | storage, control        | 7946      | TCP / UDP   |
| Greylog                     | egress    | control                 | 12202     | TCP         |
